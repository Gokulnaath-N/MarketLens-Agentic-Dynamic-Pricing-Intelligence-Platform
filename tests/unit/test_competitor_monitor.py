"""Unit tests for CompetitorMonitorAgent: deterministic change detection and threshold alerts."""

import pytest
from datetime import datetime, timezone, timedelta

from marketlens.agents.competitor_monitor import CompetitorMonitorAgent
from marketlens.agents.schemas import (
    ChangeDirection,
    CompetitorObservation,
)


def test_competitor_price_increase_and_threshold():
    """Verify deterministic price increase calculation and threshold trigger."""
    agent = CompetitorMonitorAgent(price_change_threshold_pct=5.0)
    t0 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc)

    obs1 = CompetitorObservation(
        observation_id="OBS-1",
        product_id="P1",
        competitor_id="C1",
        observed_price=100.0,
        currency="GBP",
        observed_at=t0,
    )
    obs2 = CompetitorObservation(
        observation_id="OBS-2",
        product_id="P1",
        competitor_id="C1",
        observed_price=110.0,
        currency="GBP",
        observed_at=t1,
    )

    evt = agent.detect_change(obs1, obs2)
    assert evt.direction == ChangeDirection.INCREASE
    assert evt.absolute_change == pytest.approx(10.0)
    assert evt.percentage_change == pytest.approx(10.0)
    assert evt.threshold_exceeded is True
    assert evt.age_hours == pytest.approx(24.0)
    assert evt.is_stale is False


def test_competitor_price_decrease_below_threshold():
    """Verify small price decrease below threshold does not trigger alert."""
    agent = CompetitorMonitorAgent(price_change_threshold_pct=5.0)
    t0 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc)

    obs1 = CompetitorObservation(
        observation_id="OBS-1",
        product_id="P1",
        competitor_id="C1",
        observed_price=100.0,
        currency="GBP",
        observed_at=t0,
    )
    obs2 = CompetitorObservation(
        observation_id="OBS-2",
        product_id="P1",
        competitor_id="C1",
        observed_price=98.0,
        currency="GBP",
        observed_at=t1,
    )

    evt = agent.detect_change(obs1, obs2)
    assert evt.direction == ChangeDirection.DECREASE
    assert evt.absolute_change == pytest.approx(-2.0)
    assert evt.percentage_change == pytest.approx(-2.0)
    assert evt.threshold_exceeded is False


def test_competitor_price_unchanged():
    """Verify identical prices are classified as UNCHANGED."""
    agent = CompetitorMonitorAgent(price_change_threshold_pct=5.0)
    t0 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc)

    obs1 = CompetitorObservation(
        observation_id="OBS-1",
        product_id="P1",
        competitor_id="C1",
        observed_price=50.0,
        currency="GBP",
        observed_at=t0,
    )
    obs2 = CompetitorObservation(
        observation_id="OBS-2",
        product_id="P1",
        competitor_id="C1",
        observed_price=50.0,
        currency="GBP",
        observed_at=t1,
    )

    evt = agent.detect_change(obs1, obs2)
    assert evt.direction == ChangeDirection.UNCHANGED
    assert evt.absolute_change == 0.0
    assert evt.percentage_change == 0.0
    assert evt.threshold_exceeded is False


def test_incomparable_product_or_currency_raises():
    """Verify comparing different products or different currencies raises ValueError."""
    agent = CompetitorMonitorAgent()
    t0 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc)

    # Product mismatch
    obs1 = CompetitorObservation(observation_id="O1", product_id="P1", competitor_id="C1", observed_price=10.0, currency="GBP", observed_at=t0)
    obs2 = CompetitorObservation(observation_id="O2", product_id="P2", competitor_id="C1", observed_price=12.0, currency="GBP", observed_at=t1)
    with pytest.raises(ValueError, match="Product ID mismatch"):
        agent.detect_change(obs1, obs2)

    # Currency mismatch
    obs3 = CompetitorObservation(observation_id="O3", product_id="P1", competitor_id="C1", observed_price=12.0, currency="USD", observed_at=t1)
    with pytest.raises(ValueError, match="Currency mismatch"):
        agent.detect_change(obs1, obs3)


def test_chronological_inversion_raises():
    """Verify that inverted timestamps (curr older than prev) raises ValueError."""
    agent = CompetitorMonitorAgent()
    t0 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 8, 10, 0, tzinfo=timezone.utc)  # Inverted

    obs1 = CompetitorObservation(observation_id="O1", product_id="P1", competitor_id="C1", observed_price=10.0, currency="GBP", observed_at=t0)
    obs2 = CompetitorObservation(observation_id="O2", product_id="P1", competitor_id="C1", observed_price=12.0, currency="GBP", observed_at=t1)

    with pytest.raises(ValueError, match="Chronological inversion"):
        agent.detect_change(obs1, obs2)


def test_stale_observation_flag():
    """Verify that observation gaps exceeding max_observation_age_hours are flagged as stale."""
    agent = CompetitorMonitorAgent(max_observation_age_hours=48.0)
    t0 = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)  # 9 days gap > 48h

    obs1 = CompetitorObservation(observation_id="O1", product_id="P1", competitor_id="C1", observed_price=20.0, currency="GBP", observed_at=t0)
    obs2 = CompetitorObservation(observation_id="O2", product_id="P1", competitor_id="C1", observed_price=22.0, currency="GBP", observed_at=t1)

    evt = agent.detect_change(obs1, obs2)
    assert evt.is_stale is True
    assert any("exceeds max age threshold" in w for w in evt.warnings)
