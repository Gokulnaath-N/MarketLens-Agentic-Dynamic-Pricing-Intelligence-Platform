"""Unit tests for deterministic candidate price grid generation."""

import math
import pytest

from marketlens.pricing.candidate_generation import generate_candidate_prices


def test_candidate_generation_default_step():
    """Verify standard candidate generation across a valid interval."""
    candidates, notes = generate_candidate_prices(
        price_min=10.0,
        price_max=20.0,
        current_price=15.0,
        num_candidates=11,
    )
    assert len(candidates) == 11
    assert candidates[0] == 10.0
    assert candidates[-1] == 20.0
    assert 15.0 in candidates
    # Check monotonic sorting
    assert candidates == sorted(candidates)


def test_candidate_generation_explicit_step():
    """Verify grid generation with explicit step increment."""
    candidates, notes = generate_candidate_prices(
        price_min=5.0,
        price_max=6.0,
        price_step=0.25,
        current_price=5.50,
    )
    assert candidates == [5.0, 5.25, 5.5, 5.75, 6.0]


def test_candidate_generation_non_divisible_step():
    """Verify endpoint is preserved when step does not evenly divide the interval."""
    candidates, notes = generate_candidate_prices(
        price_min=1.0,
        price_max=2.5,
        price_step=0.4,
    )
    assert candidates[0] == 1.0
    assert candidates[-1] == 2.5
    assert all(c >= 1.0 and c <= 2.5 for c in candidates)


def test_candidate_generation_single_point():
    """Verify behavior when price_min equals price_max."""
    candidates, notes = generate_candidate_prices(
        price_min=12.50,
        price_max=12.50,
    )
    assert candidates == [12.50]
    assert any("Single point" in n for n in notes)


def test_candidate_generation_current_price_inclusion():
    """Verify current_price inside bounds is included, while outside is omitted."""
    # Inside bounds
    candidates_in, notes_in = generate_candidate_prices(
        price_min=10.0,
        price_max=20.0,
        current_price=13.37,
        num_candidates=5,
    )
    assert 13.37 in candidates_in

    # Outside bounds
    candidates_out, notes_out = generate_candidate_prices(
        price_min=10.0,
        price_max=20.0,
        current_price=25.0,
        num_candidates=5,
    )
    assert 25.0 not in candidates_out
    assert any("outside bounds" in n for n in notes_out)


def test_candidate_generation_max_candidates_limit():
    """Verify error raised when requested range exceeds max_candidates limit."""
    with pytest.raises(ValueError, match="exceeding max_candidates limit"):
        generate_candidate_prices(
            price_min=1.0,
            price_max=100.0,
            price_step=0.01,
            max_candidates=50,
        )


def test_candidate_generation_invalid_bounds():
    """Verify validation errors for inverted or negative bounds."""
    with pytest.raises(ValueError, match="cannot exceed price_max"):
        generate_candidate_prices(price_min=20.0, price_max=10.0)

    with pytest.raises(ValueError, match="must be a positive finite number"):
        generate_candidate_prices(price_min=-5.0, price_max=10.0)

    with pytest.raises(ValueError, match="must be a positive finite number"):
        generate_candidate_prices(price_min=0.0, price_max=10.0)

    with pytest.raises(ValueError, match="must be a positive finite number"):
        generate_candidate_prices(price_min=float("nan"), price_max=10.0)


def test_candidate_generation_invalid_step():
    """Verify validation errors for zero, negative, or non-finite step."""
    with pytest.raises(ValueError, match="price_step must be positive finite"):
        generate_candidate_prices(price_min=5.0, price_max=10.0, price_step=0.0)

    with pytest.raises(ValueError, match="price_step must be positive finite"):
        generate_candidate_prices(price_min=5.0, price_max=10.0, price_step=-0.5)

    with pytest.raises(ValueError, match="price_step must be positive finite"):
        generate_candidate_prices(price_min=5.0, price_max=10.0, price_step=float("nan"))

