"""Time-aligned Market Signal Aggregator preventing temporal leakage across market intelligence sources."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from marketlens.agents.competitor_monitor import summarize_competitor_signals
from marketlens.agents.review_insights import aggregate_review_signals
from marketlens.agents.schemas import (
    CompetitorChangeEvent,
    CompetitorObservation,
    MarketSignalAggregate,
    ReviewInsightOutput,
    SignalQualityStatus,
)
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.agents.signal_aggregator")


class MarketSignalAggregator:
    """Aggregates review perception signals and competitor price changes into time-aligned feature vectors."""

    def __init__(
        self,
        review_window_days: int = 30,
        competitor_window_days: int = 7,
        min_reviews_for_aggregate: int = 5,
    ):
        self.review_window_days = int(review_window_days)
        self.competitor_window_days = int(competitor_window_days)
        self.min_reviews = int(min_reviews_for_aggregate)

    def aggregate(
        self,
        product_id: str,
        as_of_timestamp: datetime,
        reviews: Optional[List[ReviewInsightOutput]] = None,
        competitor_observations: Optional[List[CompetitorObservation]] = None,
        competitor_events: Optional[List[CompetitorChangeEvent]] = None,
    ) -> MarketSignalAggregate:
        """Construct a leakage-safe market signal aggregate for product_id as of as_of_timestamp.

        Leakage-Safe Rule:
            All input observations with timestamps strictly after as_of_timestamp are purged.
            Only historical observations falling within the lookback window are retained.
        """
        warnings: List[str] = []
        provenance_ids: List[str] = []
        is_synthetic = False

        # Normalize timezone awareness
        if as_of_timestamp.tzinfo is None:
            as_of_timestamp = as_of_timestamp.replace(tzinfo=timezone.utc)

        # 1. Filter Reviews
        eligible_reviews: List[ReviewInsightOutput] = []
        if reviews:
            review_cutoff = as_of_timestamp - timedelta(days=self.review_window_days)
            for r in reviews:
                if r.product_id != product_id:
                    continue

                r_time = r.review_timestamp or r.processed_at
                if r_time.tzinfo is None:
                    r_time = r_time.replace(tzinfo=timezone.utc)

                # Strict anti-leakage filter
                if r_time > as_of_timestamp:
                    continue  # Purge future reviews

                if r_time >= review_cutoff:
                    eligible_reviews.append(r)
                    provenance_ids.append(r.review_id)
                    if r.is_synthetic:
                        is_synthetic = True

        # 2. Filter Competitor Observations & Events
        eligible_comp_obs: List[CompetitorObservation] = []
        if competitor_observations:
            comp_cutoff = as_of_timestamp - timedelta(days=self.competitor_window_days)
            for obs in competitor_observations:
                if obs.product_id != product_id:
                    continue

                obs_time = obs.observed_at
                if obs_time.tzinfo is None:
                    obs_time = obs_time.replace(tzinfo=timezone.utc)

                # Strict anti-leakage filter
                if obs_time > as_of_timestamp:
                    continue  # Purge future competitor price scrapes

                if obs_time >= comp_cutoff:
                    eligible_comp_obs.append(obs)
                    provenance_ids.append(obs.observation_id)
                    if obs.is_synthetic:
                        is_synthetic = True

        eligible_comp_events: List[CompetitorChangeEvent] = []
        if competitor_events:
            for evt in competitor_events:
                if evt.product_id != product_id:
                    continue
                evt_time = evt.current_observed_at
                if evt_time.tzinfo is None:
                    evt_time = evt_time.replace(tzinfo=timezone.utc)
                if evt_time <= as_of_timestamp:
                    eligible_comp_events.append(evt)
                    if evt.is_synthetic:
                        is_synthetic = True

        # 3. Compute Aggregates
        review_metrics = aggregate_review_signals(eligible_reviews)
        competitor_metrics = summarize_competitor_signals(eligible_comp_obs, eligible_comp_events)

        # 4. Assess Data Quality & Freshness Status
        has_reviews = review_metrics["review_count"] > 0
        has_competitors = competitor_metrics["competitor_count"] > 0

        if not has_reviews and not has_competitors:
            quality_status = SignalQualityStatus.MISSING
            warnings.append("No active review or competitor observations available in lookback window.")
        elif is_synthetic:
            quality_status = SignalQualityStatus.SYNTHETIC_ONLY
            warnings.append("Market features derived partially or fully from synthetic simulation records.")
        elif has_reviews and review_metrics["usable_review_count"] < self.min_reviews:
            quality_status = SignalQualityStatus.INSUFFICIENT_SAMPLE
            warnings.append(
                f"Usable review count ({review_metrics['usable_review_count']}) is below minimum "
                f"sample threshold ({self.min_reviews})."
            )
        else:
            quality_status = SignalQualityStatus.AVAILABLE

        return MarketSignalAggregate(
            product_id=product_id,
            as_of_timestamp=as_of_timestamp,
            review_count=review_metrics["review_count"],
            usable_review_count=review_metrics["usable_review_count"],
            mean_sentiment_score=review_metrics["mean_sentiment_score"],
            positive_review_ratio=review_metrics["positive_review_ratio"],
            negative_review_ratio=review_metrics["negative_review_ratio"],
            aspect_counts=review_metrics["aspect_counts"],
            complaint_counts=review_metrics["complaint_counts"],
            competitor_count=competitor_metrics["competitor_count"],
            min_competitor_price=competitor_metrics["min_competitor_price"],
            mean_competitor_price=competitor_metrics["mean_competitor_price"],
            max_competitor_price=competitor_metrics["max_competitor_price"],
            latest_competitor_price_change_pct=competitor_metrics["latest_competitor_price_change_pct"],
            competitor_price_drop_flag=competitor_metrics["competitor_price_drop_flag"],
            quality_status=quality_status,
            is_synthetic=is_synthetic,
            provenance_record_ids=provenance_ids,
            warnings=warnings,
        )
