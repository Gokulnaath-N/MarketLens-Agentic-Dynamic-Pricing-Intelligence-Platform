"""Source-specific data cleaning for UCI Online Retail II transactions."""

from __future__ import annotations

from typing import Any, Dict, Tuple
import pandas as pd

from marketlens.logging_config import get_logger

logger = get_logger("marketlens.data.cleaning")

# Known non-product administrative / freight / manual adjustment codes in UCI
NON_PRODUCT_CODES = {
    "POST",
    "D",
    "M",
    "BANK CHARGES",
    "PADS",
    "DOT",
    "CRUK",
    "TEST",
    "ADJUST",
    "ADJUST2",
    "AMAZONFEE",
    "SP1002",
}


def clean_uci_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean UCI Online Retail II transactions according to strict data governance rules.

    Transformations:
    1. Parse and standardize column names.
    2. Identify and isolate cancellations (invoices starting with 'C' and negative quantities).
    3. Exclude non-product administrative codes ('POST', 'M', 'BANK CHARGES', etc.).
    4. Exclude zero and negative price adjustments.
    5. Deduplicate exact matching transaction lines.
    6. Ensure valid timestamps and positive demand quantities.

    Args:
        df: Raw DataFrame loaded from UCI workbook.

    Returns:
        Tuple of (clean_df, audit_metrics_dict).
    """
    initial_rows = len(df)
    logger.info(f"Beginning cleaning pipeline on {initial_rows:,} raw transaction lines...")

    # Standardize column names
    col_map = {c: c.strip() for c in df.columns}
    df = df.rename(columns=col_map)

    # 1. Check missing identifiers
    missing_stock = df["StockCode"].isna().sum()
    missing_date = df["InvoiceDate"].isna().sum()
    df = df.dropna(subset=["StockCode", "InvoiceDate"]).copy()

    # Convert types
    df["Invoice"] = df["Invoice"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # Drop unparseable dates or quantities
    invalid_records = df["InvoiceDate"].isna() | df["Quantity"].isna() | df["Price"].isna()
    df = df[~invalid_records].copy()

    # 2. Identify cancellations and returns
    is_cancellation = df["Invoice"].str.startswith("C", na=False) | (df["Quantity"] < 0)
    cancellation_rows = int(is_cancellation.sum())
    cancellation_units = int(df.loc[is_cancellation, "Quantity"].sum())

    # Exclude cancellations for primary gross positive sales demand baseline
    df_sales = df[~is_cancellation].copy()

    # 3. Identify and exclude non-product SKU codes
    stock_upper = df_sales["StockCode"].str.upper()
    is_admin_code = stock_upper.isin(NON_PRODUCT_CODES) | stock_upper.str.contains("TEST", na=False)
    admin_rows = int(is_admin_code.sum())
    df_sales = df_sales[~is_admin_code].copy()

    # 4. Filter zero or negative selling prices
    is_non_positive_price = df_sales["Price"] <= 0
    non_positive_price_rows = int(is_non_positive_price.sum())
    df_sales = df_sales[~is_non_positive_price].copy()

    # 5. Deduplicate exact duplicate transaction records
    dup_mask = df_sales.duplicated(
        subset=["Invoice", "StockCode", "InvoiceDate", "Quantity", "Price"],
        keep="first",
    )
    duplicate_rows = int(dup_mask.sum())
    df_sales = df_sales[~dup_mask].copy()

    final_rows = len(df_sales)
    excluded_rows = initial_rows - final_rows

    audit: Dict[str, Any] = {
        "initial_rows": initial_rows,
        "final_clean_sales_rows": final_rows,
        "total_excluded_rows": excluded_rows,
        "exclusion_breakdown": {
            "missing_identifier_or_date": int(missing_stock + missing_date),
            "cancellations_and_returns_rows": cancellation_rows,
            "cancellation_net_units": cancellation_units,
            "administrative_non_product_skus": admin_rows,
            "zero_or_negative_price_rows": non_positive_price_rows,
            "exact_duplicate_rows": duplicate_rows,
        },
        "retention_rate_pct": round((final_rows / initial_rows) * 100.0, 2) if initial_rows > 0 else 0.0,
    }

    logger.info(
        f"Cleaning complete: retained {final_rows:,} rows ({audit['retention_rate_pct']}%), "
        f"excluded {excluded_rows:,} rows (Cancellations: {cancellation_rows:,}, Duplicates: {duplicate_rows:,})."
    )
    return df_sales, audit
