"""Unit tests for Phase 5 feature ablation registry and variant dispatching."""

from datetime import datetime, timedelta, timezone
import pytest
import pandas as pd

from marketlens.agents.schemas import (
    CompetitorObservation,
    ExtractionMethod,
    ReviewInsightOutput,
    SentimentLabel,
)
from marketlens.experiments.ablation import FeatureAblationRunner
from marketlens.experiments.schemas import ExperimentStatus, ExperimentVariant


@pytest.fixture
def sample_demand_df():
    """Create a minimal synthetic demand dataframe for unit testing."""
    dates = pd.date_range("2025-01-06", periods=20, freq="W-MON")
    rows = []
    for d in dates:
        rows.append({
            "product_id": "SKU-TEST-1",
            "period_start": d,
            "units_sold": 50.0 + np.random.uniform(-5, 5),
            "mean_unit_price": 10.0,
        })
    df = pd.DataFrame(rows)
    return df


import numpy as np


def test_ablation_registry_variant_definitions():
    """Verify runner correctly initializes feature lists for all four variants."""
    runner = FeatureAblationRunner()
    assert len(runner.baseline_features) > 0
    assert len(runner.review_features) > 0
    assert len(runner.competitor_features) > 0


def test_ablation_runner_missing_data_not_run_status(sample_demand_df):
    """Verify that when real reviews/competitor data are absent, E1-E3 are marked NOT_RUN."""
    runner = FeatureAblationRunner()
    manifest, comp_df = runner.run_ablation(
        df=sample_demand_df,
        reviews=None,
        competitor_observations=None,
        allow_synthetic_simulation=False,
    )

    # E0 should be completed
    assert manifest.variant_results["E0_baseline"].status == ExperimentStatus.COMPLETED
    assert manifest.variant_results["E0_baseline"].metrics is not None

    # E1, E2, E3 must be NOT_RUN
    assert manifest.variant_results["E1_reviews"].status == ExperimentStatus.NOT_RUN
    assert "no customer review text" in manifest.variant_results["E1_reviews"].status_reason

    assert manifest.variant_results["E2_competitors"].status == ExperimentStatus.NOT_RUN
    assert "no competitor price observations" in manifest.variant_results["E2_competitors"].status_reason

    assert manifest.variant_results["E3_both"].status == ExperimentStatus.NOT_RUN


def test_ablation_runner_simulation_executes_all_variants(sample_demand_df):
    """Verify that when allow_synthetic_simulation=True, all variants E0-E3 are executed."""
    runner = FeatureAblationRunner()
    origin = sample_demand_df["period_start"].iloc[10]

    synthetic_review = ReviewInsightOutput(
        review_id="SYNTH-R1",
        product_id="SKU-TEST-1",
        sentiment_label=SentimentLabel.POSITIVE,
        sentiment_score=0.75,
        summary="Synthetic test review",
        extraction_method=ExtractionMethod.MOCK,
        review_timestamp=origin - timedelta(days=5),
        is_synthetic=True,
    )

    synthetic_comp = CompetitorObservation(
        observation_id="SYNTH-C1",
        product_id="SKU-TEST-1",
        competitor_id="COMP-A",
        observed_price=9.50,
        currency="GBP",
        observed_at=origin - timedelta(days=2),
        is_synthetic=True,
    )

    manifest, comp_df = runner.run_ablation(
        df=sample_demand_df,
        reviews=[synthetic_review],
        competitor_observations=[synthetic_comp],
        allow_synthetic_simulation=True,
    )

    # All variants should run under simulation
    assert manifest.variant_results["E0_baseline"].status == ExperimentStatus.COMPLETED
    assert manifest.variant_results["E1_reviews"].status == ExperimentStatus.SYNTHETIC_SIMULATED
    assert manifest.variant_results["E2_competitors"].status == ExperimentStatus.SYNTHETIC_SIMULATED
    assert manifest.variant_results["E3_both"].status == ExperimentStatus.SYNTHETIC_SIMULATED

    # Verify deltas are computed
    e1_res = manifest.variant_results["E1_reviews"]
    assert e1_res.metrics.delta_mae is not None
    assert e1_res.metrics.pct_delta_mae is not None
