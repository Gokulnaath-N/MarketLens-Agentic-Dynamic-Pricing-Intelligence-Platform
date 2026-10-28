"""Integration tests for Phase 5 feature ablation pipeline."""

import pytest
import pandas as pd
from marketlens.experiments.ablation import FeatureAblationRunner
from marketlens.experiments.schemas import ExperimentStatus


def test_ablation_pipeline_end_to_end(tmp_path):
    """Verify end-to-end execution of the ablation pipeline across multiple products."""
    dates = pd.date_range("2024-01-01", periods=30, freq="W-MON")
    rows = []
    for pid in ["SKU-A", "SKU-B"]:
        for i, d in enumerate(dates):
            rows.append({
                "product_id": pid,
                "period_start": d,
                "units_sold": float(20 + i * 2),
                "mean_unit_price": 5.0,
            })
    df = pd.DataFrame(rows)

    cfg = {
        "experiment": {
            "name": "integration_test_ablation",
            "tracking_dir": str(tmp_path / "phase5_artifacts"),
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
            "baseline": ["target_lag_1", "target_lag_2", "rolling_mean_4", "price_lag_1", "cal_month"],
            "review_intelligence": ["review_count_30d", "mean_sentiment_30d"],
            "competitor_intelligence": ["competitor_count_7d", "min_competitor_price_7d"],
        },
        "models": {
            "primary_ablation_model": "ridge_regression",
        },
        "pricing_evaluation": {
            "enabled": True,
        },
    }

    runner = FeatureAblationRunner(config=cfg)
    manifest, comparison_df = runner.run_ablation(df=df, allow_synthetic_simulation=False)

    # 1. Assertions on manifest structure
    assert manifest.run_id.startswith("ablation_integration_test_ablation_")
    assert len(manifest.train_range) == 2
    assert len(manifest.test_range) == 2
    assert manifest.shared_cohort_test_rows > 0

    # 2. Assertions on E0 Baseline
    e0_result = manifest.variant_results["E0_baseline"]
    assert e0_result.status == ExperimentStatus.COMPLETED
    assert e0_result.test_rows > 0
    assert e0_result.metrics.mae > 0.0
    assert e0_result.metrics.rmse > 0.0

    # 3. Assertions on E1-E3
    assert manifest.variant_results["E1_reviews"].status == ExperimentStatus.NOT_RUN
    assert manifest.variant_results["E2_competitors"].status == ExperimentStatus.NOT_RUN
    assert manifest.variant_results["E3_both"].status == ExperimentStatus.NOT_RUN

    # 4. Assertions on DataFrame comparison table
    assert len(comparison_df) == 4
    assert "variant" in comparison_df.columns
    assert "status" in comparison_df.columns
    assert "mae" in comparison_df.columns
    assert "delta_mae" in comparison_df.columns
