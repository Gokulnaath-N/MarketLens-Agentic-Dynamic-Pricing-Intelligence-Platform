"""Aggregate transaction observations to canonical regular time-series demand grain."""

from __future__ import annotations

from typing import List, Optional
import pandas as pd

from marketlens.data.contracts import validate_demand_series_df
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.data.aggregation")


def aggregate_to_demand_series(
    canonical_sales: pd.DataFrame,
    freq: str = "W-MON",
    min_active_periods: int = 12,
    top_n_products: Optional[int] = None,
) -> pd.DataFrame:
    """Aggregate individual sales observations into a regular time-indexed demand table.

    Args:
        canonical_sales: Canonical sales DataFrame (output of canonicalize_uci_transactions).
        freq: Pandas offset alias ('W-MON' for weekly on Mondays, 'D' for daily).
        min_active_periods: Minimum distinct active periods required to keep a product.
        top_n_products: Optional limit to top N highest volume products for model training.

    Returns:
        Regularized demand series DataFrame matching DemandSeriesRecord schema.
    """
    logger.info(f"Aggregating {len(canonical_sales):,} sales records to grain '{freq}'...")

    df = canonical_sales.copy()
    # Floor timestamp to period start (Mondays for weekly grain)
    if "W" in freq.upper():
        df["period_start"] = df["timestamp"].dt.to_period("W").dt.start_time
    elif "D" in freq.upper():
        df["period_start"] = df["timestamp"].dt.floor("D")
    else:
        df["period_start"] = df["timestamp"].dt.to_period(freq).dt.start_time

    # 1. Product activity filter
    product_periods = df.groupby("product_id")["period_start"].nunique()
    eligible_products = product_periods[product_periods >= min_active_periods].index

    logger.info(
        f"Filtered products: {len(eligible_products):,} / {len(product_periods):,} "
        f"products have >= {min_active_periods} active periods."
    )

    if top_n_products is not None and top_n_products > 0:
        vol = df[df["product_id"].isin(eligible_products)].groupby("product_id")["quantity_sold"].sum()
        top_skus = vol.sort_values(ascending=False).head(top_n_products).index
        eligible_products = eligible_products.intersection(top_skus)
        logger.info(f"Selected top {len(eligible_products)} products by volume.")

    df = df[df["product_id"].isin(eligible_products)].copy()

    # 2. Groupby aggregation
    agg_df = (
        df.groupby(["product_id", "period_start"])
        .apply(
            lambda g: pd.Series(
                {
                    "units_sold": float(g["quantity_sold"].sum()),
                    "total_revenue": float(g["revenue"].sum()),
                    "transaction_count": int(len(g)),
                    "mean_unit_price": (
                        float(g["revenue"].sum() / g["quantity_sold"].sum())
                        if g["quantity_sold"].sum() > 0
                        else float(g["unit_price"].mean())
                    ),
                    "source_dataset": g["source_dataset"].iloc[0],
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )

    # 3. Regularize grid (fill missing dates between global min & max)
    logger.info("Regularizing time grid across eligible products...")
    all_periods = pd.date_range(
        start=agg_df["period_start"].min(),
        end=agg_df["period_start"].max(),
        freq=freq,
    )

    regularized_rows = []
    for pid, group in agg_df.groupby("product_id"):
        group = group.set_index("period_start").reindex(all_periods)
        group["product_id"] = pid
        group["source_dataset"] = group["source_dataset"].ffill().bfill()
        # Quality flag
        is_missing = group["units_sold"].isna()
        group["data_quality_flags"] = is_missing.apply(
            lambda m: ["zero_imputed"] if m else ["observed"]
        )
        # Impute zeros for unobserved periods
        group["units_sold"] = group["units_sold"].fillna(0.0)
        group["total_revenue"] = group["total_revenue"].fillna(0.0)
        group["transaction_count"] = group["transaction_count"].fillna(0).astype(int)
        # Price forward fill then back fill
        group["mean_unit_price"] = group["mean_unit_price"].ffill().bfill()

        group = group.reset_index().rename(columns={"index": "period_start"})
        regularized_rows.append(group)

    result_df = pd.concat(regularized_rows, ignore_index=True)
    result_df = result_df.sort_values(["product_id", "period_start"]).reset_index(drop=True)

    validate_demand_series_df(result_df)
    logger.info(
        f"Aggregation complete: {len(result_df):,} rows across {result_df['product_id'].nunique()} products. "
        f"Periods span from {result_df['period_start'].min()} to {result_df['period_start'].max()}."
    )
    return result_df
