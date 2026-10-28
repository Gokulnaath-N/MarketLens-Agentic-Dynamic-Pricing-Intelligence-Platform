"""Integration test executing the complete forecasting pipeline on an offline fixture."""

from __future__ import annotations

import pandas as pd
import pytest

from marketlens.data.aggregation import aggregate_to_demand_series
from marketlens.data.canonicalize import canonicalize_uci_transactions
from marketlens.data.cleaning import clean_uci_transactions
from marketlens.data.split import chronological_split
from marketlens.features.temporal import build_temporal_features
from marketlens.forecasting.evaluate import train_and_evaluate_models


@pytest.fixture
def synthetic_transaction_fixture() -> pd.DataFrame:
    """Generate 20 weeks of synthetic multi-SKU retail transactions."""
    rows = []
    dates = pd.date_range("2026-01-05", periods=20, freq="W-MON")
    for d_idx, d in enumerate(dates):
        for sku_idx in ["SKU_ALPHA", "SKU_BETA"]:
            # Valid purchase
            rows.append(
                {
                    "Invoice": f"INV_{d_idx}_{sku_idx}",
                    "StockCode": sku_idx,
                    "Description": f"Product {sku_idx}",
                    "Quantity": 10 + (d_idx % 5) * 2,
                    "InvoiceDate": d + pd.Timedelta(hours=10),
                    "Price": 12.50,
                }
            )
        # Add 1 cancellation invoice
        rows.append(
            {
                "Invoice": f"C_INV_{d_idx}",
                "StockCode": "SKU_ALPHA",
                "Description": "Product SKU_ALPHA",
                "Quantity": -2,
                "InvoiceDate": d + pd.Timedelta(hours=11),
                "Price": 12.50,
            }
        )
    return pd.DataFrame(rows)


def test_end_to_end_forecasting_pipeline_offline(synthetic_transaction_fixture: pd.DataFrame):
    """End-to-end integration test: clean -> canonicalize -> aggregate -> features -> split -> train -> evaluate."""
    # 1. Cleaning
    clean_df, audit = clean_uci_transactions(synthetic_transaction_fixture)
    assert audit["exclusion_breakdown"]["cancellations_and_returns_rows"] == 20
    assert (clean_df["Quantity"] > 0).all()

    # 2. Canonicalize
    sales_df, catalog_df = canonicalize_uci_transactions(clean_df)
    assert len(sales_df) == 40 # 20 weeks * 2 valid SKUs
    assert len(catalog_df) == 2

    # 3. Aggregate
    demand_df = aggregate_to_demand_series(sales_df, freq="W-MON", min_active_periods=10)
    assert demand_df["product_id"].nunique() == 2
    assert len(demand_df) == 40

    # 4. Temporal Features
    features_df = build_temporal_features(demand_df, horizon=1, lags=[1, 2], rolling_windows=[4])
    assert "target_lag_1" in features_df.columns
    assert "rolling_mean_4" in features_df.columns

    # 5. Chronological Split
    train_df, val_df, test_df, meta = chronological_split(
        features_df,
        time_col="period_start",
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
    )
    assert train_df["period_start"].max() < test_df["period_start"].min()

    feature_cols = ["target_lag_1", "target_lag_2", "rolling_mean_4", "price_lag_1", "cal_month"]

    # 6. Model Training & Evaluation
    metrics_df, preds_df, trained_models = train_and_evaluate_models(
        train_df=train_df,
        test_df=test_df,
        feature_cols=feature_cols,
        target_col="units_sold",
    )

    assert len(metrics_df) == 4 # Naive, MA, Ridge, Random Forest
    assert "naive_last_observed" in metrics_df["model_name"].values
    assert "random_forest" in metrics_df["model_name"].values
    assert not preds_df.empty
    assert (preds_df["predicted_units"] >= 0.0).all()
