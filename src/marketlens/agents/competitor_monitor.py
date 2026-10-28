"""Competitor Monitoring Agent: deterministic price change detection and threshold alerts."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from marketlens.agents.schemas import (
    ChangeDirection,
    CompetitorChangeEvent,
    CompetitorObservation,
)
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.agents.competitor_monitor")


class CompetitorMonitorAgent:
    """Deterministic competitor price observation monitor and change detector."""

    def __init__(
        self,
        price_change_threshold_pct: float = 5.0,
        max_observation_age_hours: float = 168.0,  # 7 days
    ):
        self.threshold_pct = float(price_change_threshold_pct)
        self.max_age_hours = float(max_observation_age_hours)

    def detect_change(
        self,
        prev_obs: CompetitorObservation,
        curr_obs: CompetitorObservation,
    ) -> CompetitorChangeEvent:
        """Calculate deterministic price change metrics between two sequential observations.

        Raises:
            ValueError: If observations are incomparable (currency mismatch, product mismatch, non-positive price).
        """
        if prev_obs.product_id != curr_obs.product_id:
            raise ValueError(
                f"Product ID mismatch: cannot compare '{prev_obs.product_id}' with '{curr_obs.product_id}'"
            )

        if prev_obs.currency != curr_obs.currency:
            raise ValueError(
                f"Currency mismatch: cannot compare '{prev_obs.currency}' with '{curr_obs.currency}'"
            )

        if prev_obs.competitor_id != curr_obs.competitor_id:
            logger.warning(
                f"Comparing observations from different competitors ({prev_obs.competitor_id} vs {curr_obs.competitor_id})"
            )

        if prev_obs.observed_price <= 0 or curr_obs.observed_price <= 0:
            raise ValueError("Observed prices must be strictly greater than zero.")

        if curr_obs.observed_at < prev_obs.observed_at:
            raise ValueError(
                f"Chronological inversion: current observation ({curr_obs.observed_at}) "
                f"is older than previous observation ({prev_obs.observed_at})."
            )

        warnings: List[str] = []
        p_prev = prev_obs.observed_price
        p_curr = curr_obs.observed_price

        # Deterministic Python arithmetic
        abs_change = p_curr - p_prev
        pct_change = (abs_change / p_prev) * 100.0

        if abs_change > 1e-4:
            direction = ChangeDirection.INCREASE
        elif abs_change < -1e-4:
            direction = ChangeDirection.DECREASE
        else:
            direction = ChangeDirection.UNCHANGED

        threshold_exceeded = abs(pct_change) >= self.threshold_pct

        # Age calculation in hours
        time_diff = curr_obs.observed_at - prev_obs.observed_at
        age_hours = time_diff.total_seconds() / 3600.0

        is_stale = age_hours > self.max_age_hours
        if is_stale:
            warnings.append(
                f"Observation gap of {age_hours:.1f} hours exceeds max age threshold ({self.max_age_hours}h)."
            )

        is_synthetic = prev_obs.is_synthetic or curr_obs.is_synthetic
        if is_synthetic:
            warnings.append("Event derived from synthetic test fixtures.")

        event_id = f"evt_{prev_obs.observation_id}_{curr_obs.observation_id}"

        return CompetitorChangeEvent(
            event_id=event_id,
            product_id=curr_obs.product_id,
            competitor_id=curr_obs.competitor_id,
            previous_price=round(p_prev, 2),
            current_price=round(p_curr, 2),
            absolute_change=round(abs_change, 2),
            percentage_change=round(pct_change, 2),
            direction=direction,
            threshold_exceeded=threshold_exceeded,
            previous_observed_at=prev_obs.observed_at,
            current_observed_at=curr_obs.observed_at,
            age_hours=round(age_hours, 1),
            currency=curr_obs.currency,
            is_stale=is_stale,
            is_synthetic=is_synthetic,
            warnings=warnings,
        )

    def monitor_stream(
        self,
        observations: List[CompetitorObservation],
    ) -> List[CompetitorChangeEvent]:
        """Process a series of competitor price observations and detect sequential change events."""
        if len(observations) < 2:
            return []

        # Group by (product_id, competitor_id, currency)
        grouped: Dict[Tuple[str, str, str], List[CompetitorObservation]] = {}
        for obs in observations:
            key = (obs.product_id, obs.competitor_id, obs.currency)
            grouped.setdefault(key, []).append(obs)

        events: List[CompetitorChangeEvent] = []
        for key, obs_list in grouped.items():
            # Sort chronologically
            sorted_obs = sorted(obs_list, key=lambda o: o.observed_at)
            for i in range(1, len(sorted_obs)):
                prev = sorted_obs[i - 1]
                curr = sorted_obs[i]
                try:
                    evt = self.detect_change(prev, curr)
                    events.append(evt)
                except Exception as e:
                    logger.warning(f"Failed to compute change event for {key}: {e}")

        return events


def summarize_competitor_signals(
    observations: List[CompetitorObservation],
    events: Optional[List[CompetitorChangeEvent]] = None,
) -> Dict[str, Any]:
    """Calculate summary statistics across active competitor observations."""
    if not observations:
        return {
            "competitor_count": 0,
            "min_competitor_price": None,
            "mean_competitor_price": None,
            "max_competitor_price": None,
            "latest_competitor_price_change_pct": None,
            "competitor_price_drop_flag": False,
        }

    prices = [o.observed_price for o in observations if o.observed_price > 0]
    if not prices:
        return {
            "competitor_count": 0,
            "min_competitor_price": None,
            "mean_competitor_price": None,
            "max_competitor_price": None,
            "latest_competitor_price_change_pct": None,
            "competitor_price_drop_flag": False,
        }

    unique_competitors = {o.competitor_id for o in observations}
    min_price = min(prices)
    mean_price = sum(prices) / len(prices)
    max_price = max(prices)

    latest_change_pct = None
    drop_flag = False

    if events:
        sorted_events = sorted(events, key=lambda e: e.current_observed_at, reverse=True)
        if sorted_events:
            latest_change_pct = sorted_events[0].percentage_change
            # Flag true if any recent event exceeded threshold with a price decrease
            drop_flag = any(
                e.threshold_exceeded and e.direction == ChangeDirection.DECREASE for e in sorted_events
            )

    return {
        "competitor_count": len(unique_competitors),
        "min_competitor_price": round(min_price, 2),
        "mean_competitor_price": round(mean_price, 2),
        "max_competitor_price": round(max_price, 2),
        "latest_competitor_price_change_pct": latest_change_pct,
        "competitor_price_drop_flag": drop_flag,
    }
