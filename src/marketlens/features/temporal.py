"""Leakage-safe temporal and price feature engineering for demand time series."""

from __future__ import annotations

from typing import List, Optional
import numpy as np
import pandas as pd

from marketlens.logging_config import get_logger

logger = get_logger("marketlens.features.temporal")


def build_temporal_features(
    demand_df: pd.DataFrame,
    target_col: str = "units_sold",
    price_col: str = "mean_unit_price",
    time_col: str = "period_start",
    product_id_col: str = "product_id",
    horizon: int = 1,
    lags: Optional[List[int]] = None,
    rolling_windows: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Generate strictly past-only lag, rolling, calendar, and price features per product.

    Leakage Prevention Principle:
    For a forecast horizon h (e.g. h=1):
    Target to predict at period t is y_t.
    The forecast origin is at t - h (e.g. t - 1).
    Therefore, all features available at forecast origin must be shifted by at least h periods:
    - lag_1 represents the target at (t - h).
    - lag_2 represents the target at (t - h - 1).
    - rolling features over prior k periods must be strictly shifted by h periods.

    Args:
        demand_df: Clean demand series DataFrame sorted by product and time.
        target_col: Column name of demand target.
        price_col: Column name of unit selling price.
        time_col: Column name of period start timestamp.
        product_id_col: Column name of product identifier.
        horizon: Forecast horizon steps ahead (default 1).
        lags: List of lag steps to compute (e.g. [1, 2, 4]).
        rolling_windows: Windows for rolling means/stds (e.g. [4, 8]).

    Returns:
        DataFrame with feature columns appended, containing no lookahead leakage.
    """
    df = demand_df.copy()
    df = df.sort_values([product_id_col, time_col]).reset_index(drop=True)

    lag_steps = lags or [1, 2, 4]
    windows = rolling_windows or [4, 8]

    feature_dfs = []
    for pid, group in df.groupby(product_id_col):
        group = group.copy()
        target_s = group[target_col]
        price_s = group[price_col]

        # 1. Target Lags (shifted by horizon)
        for l in lag_steps:
            effective_shift = (l - 1) + horizon
            group[f"target_lag_{l}"] = target_s.shift(effective_shift)

        # 2. Price Lags
        group["price_lag_1"] = price_s.shift(horizon)

        # 3. Rolling Statistics (strictly shifted by horizon before window computation)
        for w in windows:
            shifted_target = target_s.shift(horizon)
            group[f"rolling_mean_{w}"] = shifted_target.rolling(window=w, min_periods=1).mean()
            group[f"rolling_std_{w}"] = shifted_target.rolling(window=w, min_periods=2).std().fillna(0.0)

            shifted_price = price_s.shift(horizon)
            group[f"price_rolling_mean_{w}"] = shifted_price.rolling(window=w, min_periods=1).mean()

        feature_dfs.append(group)

    result_df = pd.concat(feature_dfs, ignore_index=True)

    # 4. Calendar Features (strictly from the period timestamp)
    timestamps = result_df[time_col]
    result_df["cal_month"] = timestamps.dt.month
    result_df["cal_quarter"] = timestamps.dt.quarter
    result_df["cal_week_of_year"] = timestamps.dt.isocalendar().week.astype(int)

    # Sine/Cosine cyclical month encoding
    result_df["sin_month"] = np.sin(2 * np.pi * result_df["cal_month"] / 12.0)
    result_df["cos_month"] = np.cos(2 * np.pi * result_df["cal_month"] / 12.0)

    logger.info(
        f"Generated {len(lag_steps) + len(windows)*2 + 6} temporal/price/calendar features. "
        f"Horizon: {horizon} step(s)."
    )
    return result_df


def verify_no_future_leakage(
    df: pd.DataFrame,
    feature_builder_fn,
    target_col: str = "units_sold",
    time_col: str = "period_start",
    product_id_col: str = "product_id",
) -> bool:
    """Rigorous leakage test: verifies that perturbing future target values does not alter past features.

    Returns:
        True if all past features remain identical after future perturbation.
    """
    df_base = feature_builder_fn(df)

    # Modify future targets (last 2 periods for each product)
    df_perturbed = df.copy()
    latest_dates = df_perturbed.groupby(product_id_col)[time_col].nlargest(2).values
    df_perturbed.loc[df_perturbed[time_col].isin(latest_dates), target_col] += 999999.0

    df_perturbed_features = feature_builder_fn(df_perturbed)

    # Compare features on all periods except the perturbed dates
    unperturbed_mask = ~df_base[time_col].isin(latest_dates)
    feature_cols = [c for c in df_base.columns if "lag" in c or "rolling" in c]

    diff = (
        df_base.loc[unperturbed_mask, feature_cols]
        - df_perturbed_features.loc[unperturbed_mask, feature_cols]
    ).abs().max().max()

    return bool(diff < 1e-6)
