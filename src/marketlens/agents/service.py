"""Market Intelligence Service coordinating review analysis, competitor monitoring, and signal aggregation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from marketlens.agents.competitor_monitor import CompetitorMonitorAgent
from marketlens.agents.review_insights import ReviewInsightAgent
from marketlens.agents.schemas import (
    CompetitorChangeEvent,
    CompetitorObservation,
    ExtractionMethod,
    MarketSignalAggregate,
    ReviewInputRecord,
    ReviewInsightOutput,
)
from marketlens.agents.signal_aggregator import MarketSignalAggregator
from marketlens.config import get_project_root, load_yaml_config
from marketlens.llm.factory import get_llm_service
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.agents.service")


class MarketIntelligenceService:
    """Unified service exposing MarketLens AI Phase 4 agentic market intelligence capabilities."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_yaml_config("agents.yaml")
        self.llm_service = get_llm_service(self.config)

        gen_cfg = self.config.get("general", {})
        provider_name = gen_cfg.get("default_provider", "mock")
        ext_method = ExtractionMethod.MOCK if provider_name == "mock" else ExtractionMethod.RULE_BASED

        self.review_agent = ReviewInsightAgent(
            llm_service=self.llm_service,
            extraction_method=ext_method,
        )

        comp_cfg = self.config.get("competitor_monitoring_agent", {})
        thresh = comp_cfg.get("price_change_alert_threshold_pct", 5.0)
        max_age_days = comp_cfg.get("max_observation_age_days", 7)

        self.competitor_agent = CompetitorMonitorAgent(
            price_change_threshold_pct=thresh,
            max_observation_age_hours=max_age_days * 24.0,
        )

        agg_cfg = self.config.get("market_signal_aggregator", {})
        align_days = agg_cfg.get("time_alignment_window_days", 7)

        self.aggregator = MarketSignalAggregator(
            review_window_days=30,
            competitor_window_days=align_days,
            min_reviews_for_aggregate=5,
        )

    def analyze_reviews(self, reviews: List[ReviewInputRecord]) -> List[ReviewInsightOutput]:
        """Process batch of customer review records."""
        logger.info(f"Analyzing {len(reviews)} review records...")
        return self.review_agent.process_batch(reviews)

    def monitor_competitors(self, observations: List[CompetitorObservation]) -> List[CompetitorChangeEvent]:
        """Detect deterministic price change events across competitor observations."""
        logger.info(f"Monitoring {len(observations)} competitor price observations...")
        return self.competitor_agent.monitor_stream(observations)

    def aggregate_signals(
        self,
        product_id: str,
        as_of_timestamp: datetime,
        reviews: Optional[List[ReviewInsightOutput]] = None,
        competitor_observations: Optional[List[CompetitorObservation]] = None,
        competitor_events: Optional[List[CompetitorChangeEvent]] = None,
    ) -> MarketSignalAggregate:
        """Construct time-aligned, leakage-safe market signal feature aggregate."""
        return self.aggregator.aggregate(
            product_id=product_id,
            as_of_timestamp=as_of_timestamp,
            reviews=reviews,
            competitor_observations=competitor_observations,
            competitor_events=competitor_events,
        )
