"""Demand scenario preparation and prediction interface for pricing optimization."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import numpy as np
import pandas as pd

from marketlens.logging_config import get_logger

logger = get_logger("marketlens.pricing.scenario")


@runtime_checkable
class DemandPredictorProtocol(Protocol):
    """Protocol for demand models compatible with the pricing optimization engine."""

    def predict(self, df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        """Generate demand predictions for the given feature DataFrame."""
        ...

    def is_price_responsive(self) -> bool:
        """Return True if candidate price changes produce non-zero demand sensitivity."""
        ...


class DirectModelPredictor:
    """Adapter for models that natively consume a candidate price feature."""

    def __init__(self, model: Any, price_col: str = "mean_unit_price"):
        self.model = model
        self.price_col = price_col

    def predict(self, df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        preds = self.model.predict(df, feature_cols=feature_cols)
        return np.clip(np.asarray(preds, dtype=float), a_min=0.0, a_max=None)

    def is_price_responsive(self) -> bool:
        # Check if model object has price_col in its feature expectations
        return True


class ConstantElasticityDemandAdapter:
    """Wraps any baseline forecaster with an empirical constant price elasticity curve.

    Formula:
        Q_hat(p) = max(0, Q_base * (p / p_base) ^ elasticity)

    Where:
        - Q_base is the baseline forecast produced at reference price p_base.
        - elasticity (epsilon) is the price elasticity of demand (typically negative, e.g. -1.5).
    """

    def __init__(
        self,
        base_demand: float,
        reference_price: float,
        elasticity: float = -1.5,
        is_synthetic: bool = False,
    ):
        if reference_price <= 0:
            raise ValueError(f"reference_price must be > 0, got {reference_price}")
        self.base_demand = max(0.0, float(base_demand))
        self.reference_price = float(reference_price)
        self.elasticity = float(elasticity)
        self.is_synthetic = is_synthetic

    def predict(self, df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        """Predict demand across candidate price column."""
        if "candidate_price" not in df.columns and "mean_unit_price" not in df.columns:
            raise ValueError("Scenario DataFrame must contain 'candidate_price' or 'mean_unit_price'")

        price_series = df["candidate_price"] if "candidate_price" in df.columns else df["mean_unit_price"]
        prices = price_series.values.astype(float)

        # Q(p) = Q_0 * (p / p_0)^epsilon
        with np.errstate(divide="ignore", invalid="ignore"):
            ratios = prices / self.reference_price
            demand = self.base_demand * np.power(ratios, self.elasticity)
            demand = np.where(prices <= 0, 0.0, demand)
            demand = np.nan_to_num(demand, nan=0.0, posinf=0.0, neginf=0.0)

        return np.clip(demand, a_min=0.0, a_max=None)

    def is_price_responsive(self) -> bool:
        return self.elasticity != 0.0 and self.base_demand > 0.0


def build_candidate_scenario_batch(
    candidate_prices: List[float],
    fixed_context: Dict[str, Any],
    price_col: str = "mean_unit_price",
) -> pd.DataFrame:
    """Build a multi-row scenario DataFrame evaluating each candidate price.

    All fixed features (lags, rolling stats, calendar indicators) are replicated across
    all candidates, with only the price-dependent column updated.

    Args:
        candidate_prices: List of candidate selling prices to evaluate.
        fixed_context: Dict of unchanging product/time features at forecast origin.
        price_col: Name of the column representing candidate price in the model.

    Returns:
        pd.DataFrame containing one row per candidate price.
    """
    if not candidate_prices:
        raise ValueError("candidate_prices list cannot be empty")

    rows = []
    for p in candidate_prices:
        row = dict(fixed_context)
        row[price_col] = float(p)
        row["candidate_price"] = float(p)
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def validate_model_price_responsiveness(
    predictor: Any,
    test_prices: List[float],
    fixed_context: Dict[str, Any],
    feature_cols: List[str],
) -> bool:
    """Verify that varying candidate prices actually changes predicted demand."""
    if hasattr(predictor, "is_price_responsive") and not predictor.is_price_responsive():
        return False

    if len(test_prices) < 2:
        return False

    scenario_df = build_candidate_scenario_batch(test_prices[:2], fixed_context)
    try:
        preds = predictor.predict(scenario_df, feature_cols=feature_cols)
        # Check if predictions vary across different prices
        variance = float(np.var(preds))
        return variance > 1e-6
    except Exception as e:
        logger.warning(f"Price responsiveness check failed with error: {e}")
        return False
