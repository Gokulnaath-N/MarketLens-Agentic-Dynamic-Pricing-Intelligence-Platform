"""Unit tests for pricing business constraints, margins, and model support boundaries."""

import pytest

from marketlens.pricing.constraints import (
    check_margin_floor,
    check_model_support,
    check_price_bounds,
    check_price_movement,
    evaluate_candidate_constraints,
)


def test_check_price_bounds():
    """Verify minimum and maximum price boundary enforcement."""
    # Within bounds
    ok, reason = check_price_bounds(price=10.0, price_min=5.0, price_max=15.0)
    assert ok and reason is None

    # Below min
    ok, reason = check_price_bounds(price=4.99, price_min=5.0, price_max=15.0)
    assert not ok and "below minimum" in reason

    # Above max
    ok, reason = check_price_bounds(price=15.01, price_min=5.0, price_max=15.0)
    assert not ok and "above maximum" in reason

    # Exact boundary
    ok_min, _ = check_price_bounds(price=5.0, price_min=5.0, price_max=15.0)
    ok_max, _ = check_price_bounds(price=15.0, price_min=5.0, price_max=15.0)
    assert ok_min and ok_max


def test_check_price_movement():
    """Verify maximum allowed percentage price change relative to current price."""
    current = 100.0
    max_change = 0.20  # 20% max change

    # Allowed adjustments (between 80 and 120)
    ok_same, _ = check_price_movement(100.0, current, max_change)
    ok_up, _ = check_price_movement(120.0, current, max_change)
    ok_down, _ = check_price_movement(80.0, current, max_change)
    assert ok_same and ok_up and ok_down

    # Violating adjustments
    ok_too_high, reason_high = check_price_movement(121.0, current, max_change)
    ok_too_low, reason_low = check_price_movement(79.0, current, max_change)
    assert not ok_too_high and "exceeds maximum permitted" in reason_high
    assert not ok_too_low and "exceeds maximum permitted" in reason_low


def test_check_margin_floor():
    """Verify gross margin floor constraint: (p - c) / p >= min_margin."""
    unit_cost = 60.0
    min_margin = 0.25  # requires price >= 60 / (1 - 0.25) = 80.0

    # At or above floor
    ok_at, _ = check_margin_floor(price=80.0, unit_cost=unit_cost, min_margin=min_margin)
    ok_above, _ = check_margin_floor(price=100.0, unit_cost=unit_cost, min_margin=min_margin)
    assert ok_at and ok_above

    # Below floor
    ok_below, reason = check_margin_floor(price=75.0, unit_cost=unit_cost, min_margin=min_margin)
    assert not ok_below
    assert "below required" in reason

    # Missing cost when margin is required
    ok_missing, reason_missing = check_margin_floor(price=80.0, unit_cost=None, min_margin=min_margin)
    assert not ok_missing
    assert "unit_cost is missing" in reason_missing


def test_check_model_support():
    """Verify extrapolation detection and policy behavior."""
    support_min = 10.0
    support_max = 50.0

    # Within support
    in_supp, rej, warn = check_model_support(25.0, support_min, support_max, policy="warn")
    assert in_supp and rej is None and warn is None

    # Outside support with warn policy
    in_supp_w, rej_w, warn_w = check_model_support(60.0, support_min, support_max, policy="warn")
    assert not in_supp_w
    assert rej_w is None
    assert "outside observed historical training support" in warn_w

    # Outside support with reject policy
    in_supp_r, rej_r, warn_r = check_model_support(60.0, support_min, support_max, policy="reject")
    assert not in_supp_r
    assert rej_r is not None
    assert warn_r is None


def test_evaluate_candidate_constraints_combined():
    """Verify multi-constraint evaluation on a single candidate."""
    feasible, rejections, warnings, in_support = evaluate_candidate_constraints(
        price=110.0,
        price_min=50.0,
        price_max=150.0,
        current_price=100.0,
        unit_cost=80.0,
        min_margin=0.20,  # requires p >= 100
        max_change_pct=0.15,  # allows p in [85, 115]
        support_min=60.0,
        support_max=120.0,
        extrapolation_policy="warn",
    )
    assert feasible
    assert len(rejections) == 0
    assert in_support
