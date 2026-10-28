"""Unit tests for pricing objective functions (Revenue, Profit, and Gross Margin)."""

import math
import pytest

from marketlens.pricing.objectives import (
    calculate_estimated_profit,
    calculate_expected_revenue,
    calculate_gross_margin,
)


def test_expected_revenue_valid():
    """Verify standard expected revenue formula p * Q."""
    rev = calculate_expected_revenue(price=10.0, predicted_demand=50.0)
    assert rev == 500.0


def test_expected_revenue_fractional_demand():
    """Verify expected revenue works accurately with fractional expected quantities."""
    rev = calculate_expected_revenue(price=4.99, predicted_demand=12.5)
    assert pytest.approx(rev, 1e-4) == 4.99 * 12.5


def test_expected_revenue_negative_demand_clipped():
    """Verify negative predicted demand is clamped to zero to prevent negative revenue."""
    rev = calculate_expected_revenue(price=15.0, predicted_demand=-5.0)
    assert rev == 0.0


def test_expected_revenue_invalid_inputs():
    """Verify non-finite inputs raise ValueError."""
    with pytest.raises(ValueError, match="Price must be a positive finite number"):
        calculate_expected_revenue(price=0.0, predicted_demand=10.0)

    with pytest.raises(ValueError, match="Price must be a positive finite number"):
        calculate_expected_revenue(price=-10.0, predicted_demand=10.0)

    with pytest.raises(ValueError, match="Price must be a positive finite number"):
        calculate_expected_revenue(price=float("nan"), predicted_demand=10.0)

    with pytest.raises(ValueError, match="Predicted demand must be a finite number"):
        calculate_expected_revenue(price=10.0, predicted_demand=float("inf"))


def test_estimated_profit_valid():
    """Verify estimated contribution profit formula (p - c) * Q."""
    profit = calculate_estimated_profit(price=15.0, unit_cost=10.0, predicted_demand=20.0)
    assert profit == 100.0


def test_estimated_profit_missing_cost_returns_none():
    """Verify profit returns None when unit_cost is not provided."""
    profit = calculate_estimated_profit(price=15.0, unit_cost=None, predicted_demand=20.0)
    assert profit is None


def test_estimated_profit_invalid_cost():
    """Verify invalid unit costs raise ValueError."""
    with pytest.raises(ValueError, match="Unit cost must be a positive finite number"):
        calculate_estimated_profit(price=15.0, unit_cost=-2.0, predicted_demand=20.0)

    with pytest.raises(ValueError, match="Unit cost must be a positive finite number"):
        calculate_estimated_profit(price=15.0, unit_cost=0.0, predicted_demand=20.0)

    with pytest.raises(ValueError, match="Unit cost must be a positive finite number"):
        calculate_estimated_profit(price=15.0, unit_cost=float("nan"), predicted_demand=20.0)


def test_gross_margin_calculation():
    """Verify gross margin proportion (p - c) / p and contrast with markup (p - c) / c."""
    price = 20.0
    unit_cost = 15.0
    margin = calculate_gross_margin(price=price, unit_cost=unit_cost)
    assert margin == (20.0 - 15.0) / 20.0  # 0.25 (25% gross margin)

    # Prove margin is strictly different from markup:
    markup = (20.0 - 15.0) / 15.0  # 0.3333 (33.3% markup)
    assert margin != markup


def test_gross_margin_missing_cost():
    """Verify gross margin returns None when unit_cost is omitted."""
    assert calculate_gross_margin(price=20.0, unit_cost=None) is None
