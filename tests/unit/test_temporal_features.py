"""Unit tests for leakage-safe temporal feature engineering and anti-leakage verification."""

from __future__ import annotations

import pandas as pd
import pytest

from marketlens.features.temporal import build_temporal_features, verify_no_future_leakage


@pytest.fixture
def sample_demand_series() -> pd.DataFrame:
    dates = pd.date_range("2026-01-05", periods=10, freq="W-MON")
    return pd.DataFrame(
        {
            "product_id": ["uci_SKU_A"] * 10,
            "period_start": dates,
            "units_sold": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
            "mean_unit_price": [5.0] * 10,
            "transaction_count": [1] * 10,
            "total_revenue": [50.0] * 10,
            "source_dataset": ["uci_online_retail_ii"] * 10,
        }
    )


class TestTemporalFeatures:
    """Tests feature calculation and strict temporal leakage prevention."""

    def test_lags_and_rolling_features_shifted_by_horizon(self, sample_demand_series: pd.DataFrame):
        features_df = build_temporal_features(
            sample_demand_series,
            horizon=1,
            lags=[1, 2],
            rolling_windows=[4],
        )

        # Horizon = 1:
        # At row 0: lag_1 must be NaN (no prior period)
        assert pd.isna(features_df.loc[0, "target_lag_1"])

        # At row 1 (date = 2026-01-12): lag_1 must be row 0's units_sold (10.0)
        assert features_df.loc[1, "target_lag_1"] == 10.0

        # At row 2: lag_1 is row 1's target (20.0), lag_2 is row 0's target (10.0)
        assert features_df.loc[2, "target_lag_1"] == 20.0
        assert features_df.loc[2, "target_lag_2"] == 10.0

        # Rolling mean at row 4 must only use rows 0, 1, 2, 3 (not row 4 target!)
        # targets: [10, 20, 30, 40] -> mean = 25.0
        assert features_df.loc[4, "rolling_mean_4"] == 25.0

    def test_future_leakage_verification_passes(self, sample_demand_series: pd.DataFrame):
        """Verify that altering future target values does not alter past features."""
        passed = verify_no_future_leakage(
            sample_demand_series,
            feature_builder_fn=lambda df: build_temporal_features(df, horizon=1),
        )
        assert passed is True
