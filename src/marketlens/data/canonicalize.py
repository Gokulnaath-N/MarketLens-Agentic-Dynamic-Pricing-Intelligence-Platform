"""Map clean raw transaction observations to canonical schemas."""

from __future__ import annotations

from typing import Tuple
import pandas as pd

from marketlens.data.contracts import validate_canonical_sales_df
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.data.canonicalize")


def canonicalize_uci_transactions(clean_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Transform cleaned UCI transactions into canonical sales observations and product catalog.

    Args:
        clean_df: DataFrame output from clean_uci_transactions.

    Returns:
        Tuple of (canonical_sales_df, product_catalog_df).
    """
    logger.info(f"Canonicalizing {len(clean_df):,} cleaned sales transactions...")

    # Assign stable namespaced product identifier
    product_series = "uci_" + clean_df["StockCode"].astype(str)

    canonical_sales = pd.DataFrame(
        {
            "observation_id": (
                "uci_"
                + clean_df["Invoice"].astype(str)
                + "_"
                + clean_df["StockCode"].astype(str)
                + "_"
                + clean_df.index.astype(str)
            ),
            "product_id": product_series,
            "timestamp": clean_df["InvoiceDate"],
            "quantity_sold": clean_df["Quantity"].astype(int),
            "unit_price": clean_df["Price"].astype(float),
            "revenue": (clean_df["Quantity"] * clean_df["Price"]).astype(float),
            "currency": "GBP",
            "source_dataset": "uci_online_retail_ii",
            "data_status": "real_source",
        }
    )

    # Validate against canonical sales contract
    validate_canonical_sales_df(canonical_sales)

    # Build unique product catalog with most common description
    logger.info("Extracting unique product catalog entries...")
    desc_clean = clean_df[["StockCode", "Description"]].dropna()
    # Find most common description per StockCode
    top_descriptions = (
        desc_clean.groupby(["StockCode", "Description"])
        .size()
        .reset_index(name="count")
        .sort_values(["StockCode", "count"], ascending=[True, False])
        .drop_duplicates(subset=["StockCode"])
        .set_index("StockCode")["Description"]
        .to_dict()
    )

    unique_skus = clean_df["StockCode"].unique()
    product_catalog = pd.DataFrame(
        {
            "product_id": ["uci_" + sku for sku in unique_skus],
            "source_dataset": "uci_online_retail_ii",
            "source_product_id": unique_skus,
            "product_name": [top_descriptions.get(sku, None) for sku in unique_skus],
            "category": None, # UCI does not supply explicit taxonomy categories
            "currency": "GBP",
        }
    )

    logger.info(
        f"Canonicalization complete: {len(canonical_sales):,} sales observations, "
        f"{len(product_catalog):,} unique canonical products."
    )
    return canonical_sales, product_catalog
