"""Unit tests for MarketSignalAggregator: temporal alignment, anti-leakage, and provenance tracking."""

import pytest
from datetime import datetime, timezone, timedelta

from marketlens.agents.schemas import (
    CompetitorObservation,
    ExtractionMethod,
    ReviewInsightOutput,
    SentimentLabel,
    SignalQualityStatus,
    ValidationStatus,
)
from marketlens.agents.signal_aggregator import MarketSignalAggregator


def test_anti_leakage_temporal_filter():
    """Verify observations dated strictly after as_of_timestamp are excluded."""
    aggregator = MarketSignalAggregator(review_window_days=30, competitor_window_days=7)
    as_of = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)

    # 1 valid historical review
    rev_past = ReviewInsightOutput(
        review_id="REV-PAST",
        product_id="P1",
        sentiment_label=SentimentLabel.POSITIVE,
        sentiment_score=0.8,
        summary="Good",
        extraction_method=ExtractionMethod.MOCK,
        processed_at=as_of - timedelta(days=5),
    )
    # 1 future review (leakage risk)
    rev_future = ReviewInsightOutput(
        review_id="REV-FUTURE",
        product_id="P1",
        sentiment_label=SentimentLabel.NEGATIVE,
        sentiment_score=-0.8,
        summary="Bad",
        extraction_method=ExtractionMethod.MOCK,
        processed_at=as_of + timedelta(days=2),
    )

    agg = aggregator.aggregate(
        product_id="P1",
        as_of_timestamp=as_of,
        reviews=[rev_past, rev_future],
    )

    assert agg.review_count == 1
    assert "REV-PAST" in agg.provenance_record_ids
    assert "REV-FUTURE" not in agg.provenance_record_ids


def test_lookback_window_cutoff():
    """Verify observations older than the lookback window are excluded."""
    aggregator = MarketSignalAggregator(review_window_days=30)
    as_of = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)

    # Review 40 days old (outside 30-day window)
    rev_old = ReviewInsightOutput(
        review_id="REV-OLD",
        product_id="P1",
        sentiment_label=SentimentLabel.POSITIVE,
        sentiment_score=0.9,
        summary="Ancient",
        extraction_method=ExtractionMethod.MOCK,
        processed_at=as_of - timedelta(days=40),
    )

    agg = aggregator.aggregate(
        product_id="P1",
        as_of_timestamp=as_of,
        reviews=[rev_old],
    )
    assert agg.review_count == 0
    assert "REV-OLD" not in agg.provenance_record_ids


def test_insufficient_sample_quality_flag():
    """Verify small sample size (< min_reviews) sets INSUFFICIENT_SAMPLE quality status."""
    aggregator = MarketSignalAggregator(min_reviews_for_aggregate=5)
    as_of = datetime(2026, 2, 1, tzinfo=timezone.utc)

    # Only 2 reviews
    reviews = [
        ReviewInsightOutput(
            review_id=f"REV-{i}",
            product_id="P1",
            sentiment_label=SentimentLabel.POSITIVE,
            sentiment_score=0.7,
            summary="Fine",
            extraction_method=ExtractionMethod.MOCK,
            processed_at=as_of - timedelta(days=i),
        )
        for i in range(1, 3)
    ]

    agg = aggregator.aggregate(
        product_id="P1",
        as_of_timestamp=as_of,
        reviews=reviews,
    )
    assert agg.review_count == 2
    assert agg.quality_status == SignalQualityStatus.INSUFFICIENT_SAMPLE


def test_synthetic_flag_propagation():
    """Verify presence of synthetic observations sets is_synthetic=True and SYNTHETIC_ONLY."""
    aggregator = MarketSignalAggregator(min_reviews_for_aggregate=1)
    as_of = datetime(2026, 2, 1, tzinfo=timezone.utc)

    obs_synthetic = CompetitorObservation(
        observation_id="OBS-SYNTH",
        product_id="P1",
        competitor_id="COMP-A",
        observed_price=45.0,
        currency="GBP",
        observed_at=as_of - timedelta(days=1),
        is_synthetic=True,
    )

    agg = aggregator.aggregate(
        product_id="P1",
        as_of_timestamp=as_of,
        competitor_observations=[obs_synthetic],
    )
    assert agg.is_synthetic is True
    assert agg.quality_status == SignalQualityStatus.SYNTHETIC_ONLY
    assert agg.competitor_count == 1
    assert agg.min_competitor_price == 45.0
