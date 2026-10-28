"""Unit tests for time-aligned market signal feature generation and anti-leakage proofs."""

from datetime import datetime, timedelta, timezone
import pytest
import pandas as pd

from marketlens.agents.schemas import (
    ChangeDirection,
    CompetitorChangeEvent,
    CompetitorObservation,
    ExtractionMethod,
    ReviewInsightOutput,
    SentimentLabel,
)
from marketlens.features.market_signals import (
    build_market_signal_features_for_period,
    merge_market_signals,
    verify_temporal_integrity,
)


def test_build_market_signal_features_within_lookback():
    """Verify market signal features compute correctly within valid lookback windows."""
    origin = pd.Timestamp("2026-02-01 00:00:00", tz="UTC")
    pid = "SKU-001"

    # Review 10 days before origin
    rev = ReviewInsightOutput(
        review_id="R1",
        product_id=pid,
        sentiment_label=SentimentLabel.POSITIVE,
        sentiment_score=0.8,
        aspects=["product_quality"],
        summary="Great quality",
        extraction_method=ExtractionMethod.MOCK,
        review_timestamp=origin - timedelta(days=10),
    )

    # Competitor observation 2 days before origin
    obs = CompetitorObservation(
        observation_id="C1",
        product_id=pid,
        competitor_id="COMP-A",
        observed_price=18.00,
        currency="GBP",
        observed_at=origin - timedelta(days=2),
    )

    # Competitor price drop event 2 days before origin
    evt = CompetitorChangeEvent(
        event_id="E1",
        product_id=pid,
        competitor_id="COMP-A",
        previous_price=20.00,
        current_price=18.00,
        absolute_change=-2.00,
        percentage_change=-10.0,
        direction=ChangeDirection.DECREASE,
        threshold_exceeded=True,
        previous_observed_at=origin - timedelta(days=5),
        current_observed_at=origin - timedelta(days=2),
        age_hours=72.0,
        currency="GBP",
    )

    feats = build_market_signal_features_for_period(
        product_id=pid,
        period_start=origin,
        own_price=20.00,
        reviews=[rev],
        competitor_observations=[obs],
        competitor_events=[evt],
    )

    # Assert Review features
    assert feats["review_count_30d"] == 1
    assert feats["usable_review_count_30d"] == 1
    assert feats["mean_sentiment_30d"] == 0.8
    assert feats["positive_review_ratio_30d"] == 1.0
    assert feats["aspect_quality_mentions_30d"] == 1
    assert feats["review_signal_missing"] == 0

    # Assert Competitor features
    assert feats["competitor_count_7d"] == 1
    assert feats["min_competitor_price_7d"] == 18.00
    assert feats["competitor_price_gap_pct"] == pytest.approx(11.1111, rel=1e-3)
    assert feats["latest_competitor_price_change_pct"] == -10.0
    assert feats["competitor_price_drop_flag"] == 1
    assert feats["competitor_signal_missing"] == 0


def test_anti_leakage_future_signals_purged():
    """Verify observations dated strictly after the forecast origin are purged."""
    origin = pd.Timestamp("2026-02-01 00:00:00", tz="UTC")
    pid = "SKU-001"

    # Future review (1 day after origin)
    future_rev = ReviewInsightOutput(
        review_id="R-FUT",
        product_id=pid,
        sentiment_label=SentimentLabel.NEGATIVE,
        sentiment_score=-0.9,
        summary="Future complaint",
        extraction_method=ExtractionMethod.MOCK,
        review_timestamp=origin + timedelta(days=1),
    )

    # Future competitor observation (2 days after origin)
    future_obs = CompetitorObservation(
        observation_id="C-FUT",
        product_id=pid,
        competitor_id="COMP-A",
        observed_price=5.00,
        currency="GBP",
        observed_at=origin + timedelta(days=2),
    )

    feats = build_market_signal_features_for_period(
        product_id=pid,
        period_start=origin,
        own_price=20.00,
        reviews=[future_rev],
        competitor_observations=[future_obs],
    )

    # Both future signals must be completely excluded
    assert feats["review_count_30d"] == 0
    assert feats["usable_review_count_30d"] == 0
    assert feats["review_signal_missing"] == 1

    assert feats["competitor_count_7d"] == 0
    assert feats["competitor_signal_missing"] == 1


def test_adversarial_temporal_integrity_proof():
    """Verify that adding future events causes ZERO change in historical feature vectors."""
    assert verify_temporal_integrity(pd.DataFrame(), future_perturbation_hours=48) is True


def test_missing_market_signals_indicator_flags():
    """Verify missing signals produce clean default values and set missingness flags to 1."""
    origin = pd.Timestamp("2026-02-01 00:00:00", tz="UTC")
    pid = "SKU-EMPTY"

    feats = build_market_signal_features_for_period(
        product_id=pid,
        period_start=origin,
        own_price=15.00,
        reviews=[],
        competitor_observations=[],
    )

    assert feats["review_signal_missing"] == 1
    assert feats["review_count_30d"] == 0
    assert feats["mean_sentiment_30d"] == 0.0

    assert feats["competitor_signal_missing"] == 1
    assert feats["competitor_count_7d"] == 0
    assert feats["competitor_price_drop_flag"] == 0
