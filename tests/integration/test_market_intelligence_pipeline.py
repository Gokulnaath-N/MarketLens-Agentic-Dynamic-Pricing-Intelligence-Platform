"""Integration test for the MarketLens AI Agentic Market Intelligence Pipeline."""

from datetime import datetime, timezone, timedelta
import pytest

from marketlens.agents.competitor_monitor import CompetitorMonitorAgent
from marketlens.agents.review_insights import ReviewInsightAgent
from marketlens.agents.schemas import (
    ChangeDirection,
    CompetitorObservation,
    ExtractionMethod,
    ReviewInputRecord,
    SignalQualityStatus,
)
from marketlens.agents.service import MarketIntelligenceService
from marketlens.agents.signal_aggregator import MarketSignalAggregator


def test_market_intelligence_end_to_end_pipeline():
    """Verify end-to-end market intelligence pipeline from raw inputs to canonical signal aggregate."""
    as_of = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)
    product_id = "TEST-PROD-001"

    # 1. Review Ingestion & Extraction
    review_agent = ReviewInsightAgent(extraction_method=ExtractionMethod.RULE_BASED)
    raw_reviews = [
        ReviewInputRecord(
            review_id=f"REV-{i}",
            product_id=product_id,
            review_text=f"Review {i}: Excellent quality and fast shipping! Contact: user{i}@example.com",
            review_timestamp=as_of - timedelta(days=i),
        )
        for i in range(1, 6)
    ]
    # Add one future review to test leakage safety
    raw_reviews.append(
        ReviewInputRecord(
            review_id="REV-FUTURE",
            product_id=product_id,
            review_text="Future review that should not leak!",
            review_timestamp=as_of + timedelta(days=2),
        )
    )

    review_insights = review_agent.process_batch(raw_reviews)
    assert len(review_insights) == 6

    # 2. Competitor Price Monitoring
    comp_agent = CompetitorMonitorAgent(price_change_threshold_pct=5.0)
    obs_t0 = CompetitorObservation(
        observation_id="OBS-1",
        product_id=product_id,
        competitor_id="COMPETITOR-X",
        observed_price=25.00,
        currency="GBP",
        observed_at=as_of - timedelta(days=4),
        is_synthetic=True,
    )
    obs_t1 = CompetitorObservation(
        observation_id="OBS-2",
        product_id=product_id,
        competitor_id="COMPETITOR-X",
        observed_price=22.50,
        currency="GBP",
        observed_at=as_of - timedelta(days=1),
        is_synthetic=True,
    )

    change_event = comp_agent.detect_change(obs_t0, obs_t1)
    assert change_event.direction == ChangeDirection.DECREASE
    assert change_event.percentage_change == pytest.approx(-10.0)
    assert change_event.threshold_exceeded is True

    # 3. Time-Aligned Leakage-Safe Aggregation
    aggregator = MarketSignalAggregator(
        review_window_days=30,
        competitor_window_days=7,
        min_reviews_for_aggregate=5,
    )
    market_signal = aggregator.aggregate(
        product_id=product_id,
        as_of_timestamp=as_of,
        reviews=review_insights,
        competitor_observations=[obs_t0, obs_t1],
        competitor_events=[change_event],
    )

    # 4. Assertions on Final Feature Vector
    assert market_signal.product_id == product_id
    assert market_signal.as_of_timestamp == as_of
    # Future review was purged (5 historical reviews retained)
    assert market_signal.review_count == 5
    assert market_signal.usable_review_count == 5
    assert market_signal.mean_sentiment_score > 0.0
    assert market_signal.positive_review_ratio == 1.0
    assert "REV-FUTURE" not in market_signal.provenance_record_ids

    # Competitor signals
    assert market_signal.competitor_count == 1
    assert market_signal.min_competitor_price == 22.50
    assert market_signal.latest_competitor_price_change_pct == pytest.approx(-10.0)
    assert market_signal.competitor_price_drop_flag is True

    # Quality & Provenance
    assert market_signal.is_synthetic is True  # Marked because synthetic competitor fixtures were used
    assert market_signal.quality_status == SignalQualityStatus.SYNTHETIC_ONLY
    assert len(market_signal.provenance_record_ids) == 7  # 5 reviews + 2 comp obs
