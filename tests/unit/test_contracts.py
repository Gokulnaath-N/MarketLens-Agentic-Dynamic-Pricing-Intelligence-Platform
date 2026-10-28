"""Unit tests for canonical data contracts and vectorized schema validators."""

from __future__ import annotations

import pandas as pd
import pytest

from marketlens.data.contracts import (
    CanonicalSalesRecord,
    ContractValidationError,
    DemandSeriesRecord,
    ProductRecord,
    validate_canonical_sales_df,
    validate_demand_series_df,
)


@pytest.fixture
def valid_sales_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "observation_id": ["uci_INV001_1001_0", "uci_INV002_1002_1"],
            "product_id": ["uci_1001", "uci_1002"],
            "timestamp": pd.to_datetime(["2026-01-01 10:00:00", "2026-01-02 11:00:00"]),
            "quantity_sold": [10, 5],
            "unit_price": [15.5, 20.0],
            "revenue": [155.0, 100.0],
            "currency": ["GBP", "GBP"],
            "source_dataset": ["uci_online_retail_ii", "uci_online_retail_ii"],
            "data_status": ["real_source", "real_source"],
        }
    )


class TestCanonicalContracts:
    """Tests Pydantic models and vectorized DataFrame validation."""

    def test_product_record_creation(self):
        prod = ProductRecord(
            product_id="uci_85048",
            source_dataset="uci_online_retail_ii",
            source_product_id="85048",
            product_name="Christmas Glass Ball",
        )
        assert prod.product_id == "uci_85048"
        assert prod.currency == "GBP"

    def test_canonical_sales_record_creation(self):
        rec = CanonicalSalesRecord(
            observation_id="obs_001",
            product_id="uci_85048",
            timestamp="2026-01-01T10:00:00",
            quantity_sold=10,
            unit_price=5.99,
            revenue=59.9,
            source_dataset="uci_online_retail_ii",
        )
        assert rec.quantity_sold == 10
        assert rec.revenue == 59.9

    def test_validate_canonical_sales_df_passes_valid(self, valid_sales_df: pd.DataFrame):
        # Should execute without raising
        validate_canonical_sales_df(valid_sales_df)

    def test_validate_canonical_sales_df_missing_column_raises(self, valid_sales_df: pd.DataFrame):
        invalid_df = valid_sales_df.drop(columns=["quantity_sold"])
        with pytest.raises(ContractValidationError, match="Missing required canonical columns"):
            validate_canonical_sales_df(invalid_df)

    def test_validate_canonical_sales_df_non_positive_quantity_raises(self, valid_sales_df: pd.DataFrame):
        invalid_df = valid_sales_df.copy()
        invalid_df.loc[0, "quantity_sold"] = -5
        with pytest.raises(ContractValidationError, match="strictly positive quantities"):
            validate_canonical_sales_df(invalid_df)

    def test_validate_canonical_sales_df_zero_price_raises(self, valid_sales_df: pd.DataFrame):
        invalid_df = valid_sales_df.copy()
        invalid_df.loc[0, "unit_price"] = 0.0
        with pytest.raises(ContractValidationError, match="positive unit prices"):
            validate_canonical_sales_df(invalid_df)

    def test_validate_demand_series_df_negative_units_raises(self):
        df = pd.DataFrame(
            {
                "product_id": ["uci_1001"],
                "period_start": pd.to_datetime(["2026-01-01"]),
                "units_sold": [-10.0],
                "mean_unit_price": [5.0],
                "transaction_count": [1],
                "total_revenue": [50.0],
                "source_dataset": ["uci_online_retail_ii"],
            }
        )
        with pytest.raises(ContractValidationError, match="cannot be negative"):
            validate_demand_series_df(df)
