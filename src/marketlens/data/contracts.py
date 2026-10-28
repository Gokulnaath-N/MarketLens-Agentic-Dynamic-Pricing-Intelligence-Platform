"""Canonical data schemas, contracts, and vectorized validation routines."""

from __future__ import annotations

from typing import Any, List, Optional
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class ProductRecord(BaseModel):
    """Canonical representation of a retail product / SKU."""

    model_config = ConfigDict(extra="ignore")

    product_id: str = Field(description="Namespaced canonical ID, e.g. 'uci_85048'")
    source_dataset: str
    source_product_id: str
    product_name: Optional[str] = None
    category: Optional[str] = None
    currency: str = "GBP"


class CanonicalSalesRecord(BaseModel):
    """Canonical single-event sales transaction line."""

    model_config = ConfigDict(extra="ignore")

    observation_id: str
    product_id: str
    timestamp: str
    quantity_sold: int
    unit_price: float
    revenue: float
    currency: str = "GBP"
    source_dataset: str
    data_status: str = "real_source"


class DemandSeriesRecord(BaseModel):
    """Time-indexed demand record aggregated to canonical time grain."""

    model_config = ConfigDict(extra="ignore")

    product_id: str
    period_start: str
    units_sold: float
    mean_unit_price: float
    transaction_count: int
    total_revenue: float
    source_dataset: str
    data_quality_flags: List[str] = Field(default_factory=list)


class ContractValidationError(Exception):
    """Raised when tabular data violates canonical contracts."""

    pass


def validate_canonical_sales_df(df: pd.DataFrame) -> None:
    """Vectorized validation for canonical transaction dataframe.

    Args:
        df: DataFrame conforming to CanonicalSalesRecord schema.

    Raises:
        ContractValidationError: If columns are missing or types/ranges are invalid.
    """
    required_columns = {
        "observation_id",
        "product_id",
        "timestamp",
        "quantity_sold",
        "unit_price",
        "revenue",
        "currency",
        "source_dataset",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ContractValidationError(f"Missing required canonical columns: {sorted(missing)}")

    # Range validations
    if (df["quantity_sold"] <= 0).any():
        neg_count = (df["quantity_sold"] <= 0).sum()
        raise ContractValidationError(
            f"Canonical sales records must contain strictly positive quantities. Found {neg_count} non-positive rows."
        )

    if (df["unit_price"] <= 0).any():
        non_pos_price = (df["unit_price"] <= 0).sum()
        raise ContractValidationError(
            f"Canonical sales records must contain positive unit prices. Found {non_pos_price} non-positive rows."
        )

    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        raise ContractValidationError("Column 'timestamp' must be datetime dtype.")


def validate_demand_series_df(df: pd.DataFrame) -> None:
    """Vectorized validation for aggregated demand time series.

    Args:
        df: DataFrame conforming to DemandSeriesRecord schema.

    Raises:
        ContractValidationError: On schema or constraint breach.
    """
    required_columns = {
        "product_id",
        "period_start",
        "units_sold",
        "mean_unit_price",
        "transaction_count",
        "total_revenue",
        "source_dataset",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ContractValidationError(f"Missing required demand series columns: {sorted(missing)}")

    if not pd.api.types.is_datetime64_any_dtype(df["period_start"]):
        raise ContractValidationError("Column 'period_start' must be datetime dtype.")

    if (df["units_sold"] < 0).any():
        raise ContractValidationError("Aggregated 'units_sold' cannot be negative.")

    if (df["mean_unit_price"] < 0).any():
        raise ContractValidationError("Aggregated 'mean_unit_price' cannot be negative.")
