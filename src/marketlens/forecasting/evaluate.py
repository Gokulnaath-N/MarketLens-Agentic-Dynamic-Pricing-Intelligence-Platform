"""Evaluation engine comparing candidate forecasting models on identical test windows."""

from __future__ import annotations

from typing import Dict, List, Tuple
import pandas as pd

from marketlens.forecasting.baselines import (
    BaseForecaster,
    MovingAverageForecaster,
    NaiveLastObservedForecaster,
    RandomForestDemandForecaster,
    RidgeRegressionForecaster,
)
from marketlens.forecasting.metrics import compute_forecasting_metrics
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.forecasting.evaluate")


def get_default_models(random_seed: int = 42) -> Dict[str, BaseForecaster]:
    """Return dictionary of baseline and conventional ML models for evaluation."""
    return {
        "naive_last_observed": NaiveLastObservedForecaster(lag_col="target_lag_1"),
        "moving_average_4w": MovingAverageForecaster(rolling_col="rolling_mean_4"),
        "ridge_regression": RidgeRegressionForecaster(alpha=10.0),
        "random_forest": RandomForestDemandForecaster(n_estimators=100, max_depth=8, random_state=random_seed),
    }


def train_and_evaluate_models(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = "units_sold",
    models: Dict[str, BaseForecaster] | None = None,
    random_seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, BaseForecaster]]:
    """Train all models on train_df and evaluate against test_df on identical observations.

    Args:
        train_df: Training DataFrame with features and target.
        test_df: Held-out test DataFrame with identical feature columns.
        feature_cols: List of feature column names available at prediction time.
        target_col: Column name of demand target.
        models: Optional dictionary of {model_name: model_instance}.
        random_seed: Random seed for model reproducibility.

    Returns:
        Tuple of (metrics_summary_df, detailed_predictions_df, trained_models_dict).
    """
    candidate_models = models or get_default_models(random_seed=random_seed)
    y_test_actual = test_df[target_col].values
    y_train_actual = train_df[target_col].values

    metrics_records = []
    prediction_frames = []
    trained_models = {}

    logger.info(
        f"Evaluating {len(candidate_models)} models on {len(test_df):,} test periods across "
        f"{test_df['product_id'].nunique()} products..."
    )

    for name, model in candidate_models.items():
        logger.info(f"Training model '{name}'...")
        model.fit(train_df, target_col=target_col, feature_cols=feature_cols)
        trained_models[name] = model

        preds = model.predict(test_df, feature_cols=feature_cols)
        metrics = compute_forecasting_metrics(y_true=y_test_actual, y_pred=preds, y_train=y_train_actual)
        metrics["model_name"] = name
        metrics_records.append(metrics)

        # Build prediction record
        pred_sub = pd.DataFrame(
            {
                "product_id": test_df["product_id"].values,
                "period_start": test_df["period_start"].values,
                "actual_units": y_test_actual,
                "predicted_units": preds,
                "model_name": name,
            }
        )
        prediction_frames.append(pred_sub)

    metrics_df = pd.DataFrame(metrics_records)
    # Order columns: model_name, mae, rmse, wape, mase, r2
    metrics_df = metrics_df[["model_name", "mae", "rmse", "wape", "mase", "r2"]].sort_values("mae").reset_index(drop=True)
    all_predictions_df = pd.concat(prediction_frames, ignore_index=True)

    logger.info("Evaluation complete. Model comparison:\n" + metrics_df.to_string(index=False))
    return metrics_df, all_predictions_df, trained_models
