"""Unit tests for Phase 5 experiment metrics, pricing evaluation, and artifact saving."""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from marketlens.experiments.ablation import FeatureAblationRunner
from marketlens.experiments.schemas import MetricResult


def test_metric_result_delta_computation():
    """Verify signed metric deltas: negative delta represents forecast accuracy improvement."""
    e0 = MetricResult(mae=10.0, rmse=15.0, wape=0.20, mase=1.5, r2=0.50)
    e1_mae = 8.5  # Improvement of 1.5 units
    e1_rmse = 13.0

    delta_mae = e1_mae - e0.mae
    pct_delta_mae = (delta_mae / e0.mae) * 100.0

    assert delta_mae == -1.5  # Negative = improvement
    assert pct_delta_mae == -15.0


def test_ablation_artifacts_persisted(tmp_path):
    """Verify that ablation runner creates and persists expected artifact files."""
    dates = pd.date_range("2025-01-06", periods=20, freq="W-MON")
    df = pd.DataFrame({
        "product_id": "SKU-TEST-1",
        "period_start": dates,
        "units_sold": [10.0 + i for i in range(20)],
        "mean_unit_price": [2.50] * 20,
    })

    cfg = {
        "experiment": {
            "name": "test_exp",
            "tracking_dir": str(tmp_path / "artifacts"),
            "random_seed": 42,
        },
        "data": {
            "target_column": "units_sold",
            "time_column": "period_start",
            "product_id_column": "product_id",
            "price_column": "mean_unit_price",
            "forecast_horizon": 1,
        },
        "splits": {
            "train_ratio": 0.70,
            "validation_ratio": 0.15,
            "test_ratio": 0.15,
        },
        "feature_groups": {
            "baseline": ["target_lag_1", "rolling_mean_4", "price_lag_1", "cal_month"],
            "review_intelligence": ["review_count_30d", "mean_sentiment_30d"],
            "competitor_intelligence": ["competitor_count_7d", "min_competitor_price_7d"],
        },
        "models": {
            "primary_ablation_model": "random_forest",
        },
        "pricing_evaluation": {
            "enabled": True,
        },
    }

    runner = FeatureAblationRunner(config=cfg)
    manifest, comp_df = runner.run_ablation(df=df, allow_synthetic_simulation=False)

    tracking_dir = Path(cfg["experiment"]["tracking_dir"])
    assert (tracking_dir / "ablation_metrics.csv").exists()
    assert (tracking_dir / "ablation_metrics.json").exists()
    assert (tracking_dir / "ablation_run_manifest.json").exists()
    assert (tracking_dir / "ablation_predictions.parquet").exists()

    # Check that E0 pricing evaluation was recorded
    e0_rec = manifest.variant_results["E0_baseline"].pricing_recommendation
    assert e0_rec is not None
    assert "recommended_price" in e0_rec
    assert "expected_revenue" in e0_rec
