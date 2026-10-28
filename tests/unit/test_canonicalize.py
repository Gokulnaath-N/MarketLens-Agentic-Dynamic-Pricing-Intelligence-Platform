"""Unit tests for canonical mapping and product catalog extraction."""

from __future__ import annotations

import pandas as pd
import pytest

from marketlens.data.canonicalize import canonicalize_uci_transactions
from marketlens.data.contracts import validate_canonical_sales_df


@pytest.fixture
def clean_sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Invoice": ["489434", "489436"],
            "StockCode": ["85048", "79323P"],
            "Description": ["CHRISTMAS GLASS BALL", "PINK CHERRY LIGHTS"],
            "Quantity": [12, 10],
            "InvoiceDate": pd.to_datetime(["2009-12-01 07:45:00", "2009-12-01 09:00:00"]),
            "Price": [6.95, 6.75],
        }
    )


class TestCanonicalization:
    """Tests transformation into canonical sales and product catalog schemas."""

    def test_canonicalize_produces_valid_sales(self, clean_sample_df: pd.DataFrame):
        canonical_sales, catalog = canonicalize_uci_transactions(clean_sample_df)

        assert len(canonical_sales) == 2
        assert "uci_85048" in canonical_sales["product_id"].values
        assert "uci_79323P" in canonical_sales["product_id"].values
        assert canonical_sales["currency"].iloc[0] == "GBP"

        # Validate against canonical contract
        validate_canonical_sales_df(canonical_sales)

    def test_product_catalog_extraction(self, clean_sample_df: pd.DataFrame):
        _, catalog = canonicalize_uci_transactions(clean_sample_df)

        assert len(catalog) == 2
        assert "uci_85048" in catalog["product_id"].values
        assert catalog.loc[catalog["product_id"] == "uci_85048", "product_name"].iloc[0] == "CHRISTMAS GLASS BALL"
