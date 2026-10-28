"""Unit tests for MarketLens AI agentic market intelligence schemas."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from marketlens.agents.schemas import (
    ChangeDirection,
    CompetitorChangeEvent,
    CompetitorObservation,
    ExtractionMethod,
    MarketSignalAggregate,
    ReviewInputRecord,
    ReviewInsightOutput,
    SentimentLabel,
    SignalQualityStatus,
    ValidationStatus,
)


def test_review_input_record_valid():
    """Verify valid review input instantiation and default fields."""
    rec = ReviewInputRecord(
        review_id="REV-001",
        product_id="PROD-123",
        review_text="Excellent product quality and fast delivery!",
        rating=5.0,
        source_name="uci_online_retail",
    )
    assert rec.review_id == "REV-001"
    assert rec.product_id == "PROD-123"
    assert rec.rating == 5.0
    assert not rec.is_synthetic
    assert rec.ingested_at is not None


def test_review_input_record_invalid_rating():
    """Verify rating bounds [1.0, 5.0]."""
    with pytest.raises(ValidationError):
        ReviewInputRecord(
            review_id="REV-002",
            product_id="PROD-123",
            review_text="Terrible",
            rating=6.0,  # Invalid: > 5.0
        )
    with pytest.raises(ValidationError):
        ReviewInputRecord(
            review_id="REV-003",
            product_id="PROD-123",
            review_text="Terrible",
            rating=0.5,  # Invalid: < 1.0
        )


def test_review_insight_output_sentiment_bounds():
    """Verify sentiment score bounds [-1.0, 1.0] and enum validation."""
    valid_insight = ReviewInsightOutput(
        review_id="REV-001",
        product_id="PROD-123",
        sentiment_label=SentimentLabel.POSITIVE,
        sentiment_score=0.85,
        summary="Customer loved the product quality.",
        extraction_method=ExtractionMethod.MOCK,
    )
    assert valid_insight.sentiment_score == 0.85
    assert valid_insight.validation_status == ValidationStatus.VALIDATED

    # Out of bounds sentiment score
    with pytest.raises(ValidationError):
        ReviewInsightOutput(
            review_id="REV-001",
            product_id="PROD-123",
            sentiment_label=SentimentLabel.POSITIVE,
            sentiment_score=1.5,
            summary="Invalid score",
            extraction_method=ExtractionMethod.MOCK,
        )


def test_competitor_observation_price_validation():
    """Verify competitor observation validates positive finite prices."""
    obs = CompetitorObservation(
        observation_id="OBS-001",
        product_id="PROD-123",
        competitor_id="COMP-A",
        observed_price=19.99,
        currency="GBP",
        observed_at=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
    )
    assert obs.observed_price == 19.99

    # Zero price must fail
    with pytest.raises(ValidationError):
        CompetitorObservation(
            observation_id="OBS-002",
            product_id="PROD-123",
            competitor_id="COMP-A",
            observed_price=0.0,
            observed_at=datetime.now(timezone.utc),
        )

    # Negative price must fail
    with pytest.raises(ValidationError):
        CompetitorObservation(
            observation_id="OBS-003",
            product_id="PROD-123",
            competitor_id="COMP-A",
            observed_price=-5.50,
            observed_at=datetime.now(timezone.utc),
        )

    # NaN must fail
    with pytest.raises(ValidationError):
        CompetitorObservation(
            observation_id="OBS-004",
            product_id="PROD-123",
            competitor_id="COMP-A",
            observed_price=float("nan"),
            observed_at=datetime.now(timezone.utc),
        )


def test_competitor_change_event():
    """Verify competitor change event fields and direction enum."""
    event = CompetitorChangeEvent(
        event_id="EVT-001",
        product_id="PROD-123",
        competitor_id="COMP-A",
        previous_price=20.0,
        current_price=18.0,
        absolute_change=-2.0,
        percentage_change=-10.0,
        direction=ChangeDirection.DECREASE,
        threshold_exceeded=True,
        previous_observed_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
        current_observed_at=datetime(2026, 1, 12, tzinfo=timezone.utc),
        age_hours=48.0,
        currency="GBP",
        is_synthetic=True,
    )
    assert event.direction == ChangeDirection.DECREASE
    assert event.threshold_exceeded is True
    assert event.is_synthetic is True


def test_market_signal_aggregate_defaults():
    """Verify market signal aggregate construction and quality flag defaults."""
    as_of = datetime(2026, 2, 1, tzinfo=timezone.utc)
    agg = MarketSignalAggregate(
        product_id="PROD-123",
        as_of_timestamp=as_of,
        quality_status=SignalQualityStatus.INSUFFICIENT_SAMPLE,
    )
    assert agg.product_id == "PROD-123"
    assert agg.as_of_timestamp == as_of
    assert agg.review_count == 0
    assert agg.usable_review_count == 0
    assert agg.quality_status == SignalQualityStatus.INSUFFICIENT_SAMPLE
    assert agg.feature_version == "v1"
