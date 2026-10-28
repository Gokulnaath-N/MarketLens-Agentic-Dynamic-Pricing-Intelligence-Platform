"""Unit tests for transaction cleaning, cancellation handling, and exclusion auditing."""

from __future__ import annotations

import pandas as pd
import pytest

from marketlens.data.cleaning import clean_uci_transactions


@pytest.fixture
def raw_sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Invoice": ["489434", "C489435", "489436", "489436", "489437", "489438", "489439"],
            "StockCode": ["85048", "85048", "79323P", "79323P", "POST", "21232", "22041"],
            "Description": [
                "15CM CHRISTMAS GLASS BALL",
                "15CM CHRISTMAS GLASS BALL",
                "PINK CHERRY LIGHTS",
                "PINK CHERRY LIGHTS", # Duplicate
                "POSTAGE",
                "STRAWBERRY CERAMIC TRINKET BOX",
                "DAMAGED ITEM",
            ],
            "Quantity": [12, -12, 10, 10, 1, 5, -2],
            "InvoiceDate": [
                "2009-12-01 07:45:00",
                "2009-12-01 07:46:00", # Cancellation
                "2009-12-01 09:00:00",
                "2009-12-01 09:00:00", # Duplicate
                "2009-12-01 10:00:00", # Postage
                "2009-12-01 11:00:00", # Valid
                "2009-12-01 12:00:00", # Negative qty
            ],
            "Price": [6.95, 6.95, 6.75, 6.75, 18.00, 1.25, 0.00],
            "Customer ID": [13085.0, 13085.0, 13078.0, 13078.0, 13078.0, 14527.0, None],
            "Country": ["United Kingdom"] * 7,
        }
    )


class TestTransactionCleaning:
    """Tests governance-compliant data cleaning and exclusion audits."""

    def test_cancellation_invoices_excluded(self, raw_sample_df: pd.DataFrame):
        clean_df, audit = clean_uci_transactions(raw_sample_df)
        assert not (clean_df["Invoice"].str.startswith("C")).any()
        assert (clean_df["Quantity"] > 0).all()
        assert audit["exclusion_breakdown"]["cancellations_and_returns_rows"] == 2 # C489435 and negative qty

    def test_admin_non_product_skus_excluded(self, raw_sample_df: pd.DataFrame):
        clean_df, audit = clean_uci_transactions(raw_sample_df)
        assert "POST" not in clean_df["StockCode"].values
        assert audit["exclusion_breakdown"]["administrative_non_product_skus"] >= 1

    def test_zero_price_rows_excluded(self, raw_sample_df: pd.DataFrame):
        clean_df, audit = clean_uci_transactions(raw_sample_df)
        assert (clean_df["Price"] > 0).all()

    def test_exact_duplicates_removed(self, raw_sample_df: pd.DataFrame):
        clean_df, audit = clean_uci_transactions(raw_sample_df)
        # Should only retain 1 row of the duplicated 489436 / 79323P
        assert len(clean_df[clean_df["StockCode"] == "79323P"]) == 1
        assert audit["exclusion_breakdown"]["exact_duplicate_rows"] == 1

    def test_clean_df_retains_valid_rows(self, raw_sample_df: pd.DataFrame):
        clean_df, audit = clean_uci_transactions(raw_sample_df)
        # Exactly 3 valid rows: 489434 (85048), 489436 (79323P), 489438 (21232)
        assert len(clean_df) == 3
        assert audit["final_clean_sales_rows"] == 3
        assert audit["total_excluded_rows"] == 4
