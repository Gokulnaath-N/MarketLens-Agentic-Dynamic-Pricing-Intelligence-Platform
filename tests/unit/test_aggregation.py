"""Unit tests for time-series demand aggregation and grid regularization."""

from __future__ import annotations

import pandas as pd
import pytest

from marketlens.data.aggregation import aggregate_to_demand_series
from marketlens.data.contracts import validate_demand_series_df


@pytest.fixture
def canonical_multi_week_sales() -> pd.DataFrame:
    # 3 weeks of transactions for product A, 1 week for product B
    return pd.DataFrame(
        {
            "observation_id": [f"obs_{i}" for i in range(5)],
            "product_id": ["uci_SKU_A", "uci_SKU_A", "uci_SKU_A", "uci_SKU_A", "uci_SKU_B"],
            "timestamp": pd.to_datetime(
                [
                    "2026-01-05 10:00:00", # Week 1 Monday
                    "2026-01-06 14:00:00", # Week 1 Tuesday
                    "2026-01-19 09:00:00", # Week 3 Monday (Week 2 is unobserved!)
                    "2026-01-26 11:00:00", # Week 4 Monday
                    "2026-01-05 12:00:00", # Week 1
                ]
            ),
            "quantity_sold": [10, 5, 20, 15, 8],
            "unit_price": [10.0, 10.0, 12.0, 12.0, 25.0],
            "revenue": [100.0, 50.0, 240.0, 180.0, 200.0],
            "currency": ["GBP"] * 5,
            "source_dataset": ["uci_online_retail_ii"] * 5,
            "data_status": ["real_source"] * 5,
        }
    )


class TestDemandAggregation:
    """Tests regular time-indexed demand aggregation."""

    def test_aggregation_aggregates_units_and_regularizes_gaps(
        self, canonical_multi_week_sales: pd.DataFrame
    ):
        demand_df = aggregate_to_demand_series(
            canonical_sales=canonical_multi_week_sales,
            freq="W-MON",
            min_active_periods=3, # Keeps SKU_A, filters SKU_B (1 period)
        )

        assert demand_df["product_id"].nunique() == 1
        assert "uci_SKU_A" in demand_df["product_id"].values

        # SKU_A was active Week 1 (Jan 5), Week 3 (Jan 19), Week 4 (Jan 26)
        # Week 2 (Jan 12) must be zero-imputed!
        assert len(demand_df) == 4
        validate_demand_series_df(demand_df)

        week1 = demand_df[demand_df["period_start"] == pd.Timestamp("2026-01-05")].iloc[0]
        assert week1["units_sold"] == 15.0 # 10 + 5
        assert week1["transaction_count"] == 2
        assert "observed" in week1["data_quality_flags"]

        # Week 2 gap check
        week2 = demand_df[demand_df["period_start"] == pd.Timestamp("2026-01-12")].iloc[0]
        assert week2["units_sold"] == 0.0
        assert week2["total_revenue"] == 0.0
        assert week2["transaction_count"] == 0
        assert "zero_imputed" in week2["data_quality_flags"]
        # Mean unit price forward filled from week 1 (10.0)
        assert week2["mean_unit_price"] == 10.0
