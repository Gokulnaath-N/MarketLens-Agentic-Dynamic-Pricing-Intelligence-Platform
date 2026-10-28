"""Objective calculations: Revenue, Profit, and Gross Margin with numerical safety."""

from __future__ import annotations

import math
from typing import Optional


def calculate_expected_revenue(price: float, predicted_demand: float) -> float:
    """Compute expected revenue: p * Q_hat(p).

    Args:
        price: Candidate selling price (> 0).
        predicted_demand: Model-predicted expected units.

    Returns:
        Expected revenue. If predicted_demand is <= 0, returns 0.0.

    Raises:
        ValueError: If price is non-finite or <= 0, or predicted_demand is non-finite.
    """
    if math.isnan(price) or math.isinf(price) or price <= 0:
        raise ValueError(f"Price must be a positive finite number, got {price}")
    if math.isnan(predicted_demand) or math.isinf(predicted_demand):
        raise ValueError(f"Predicted demand must be a finite number, got {predicted_demand}")

    effective_demand = max(0.0, float(predicted_demand))
    return float(price * effective_demand)


def calculate_estimated_profit(price: float, unit_cost: Optional[float], predicted_demand: float) -> Optional[float]:
    """Compute estimated profit: (p - c) * Q_hat(p).

    Args:
        price: Candidate selling price (> 0).
        unit_cost: Wholesale unit cost (COGS). Must be finite and > 0.
        predicted_demand: Model-predicted expected units.

    Returns:
        Estimated profit, or None if unit_cost is None.

    Raises:
        ValueError: If price or unit_cost is invalid, non-finite, or <= 0.
    """
    if unit_cost is None:
        return None

    if math.isnan(unit_cost) or math.isinf(unit_cost) or unit_cost <= 0:
        raise ValueError(f"Unit cost must be a positive finite number, got {unit_cost}")
    if math.isnan(price) or math.isinf(price) or price <= 0:
        raise ValueError(f"Price must be a positive finite number, got {price}")
    if math.isnan(predicted_demand) or math.isinf(predicted_demand):
        raise ValueError(f"Predicted demand must be a finite number, got {predicted_demand}")

    effective_demand = max(0.0, float(predicted_demand))
    return float((price - unit_cost) * effective_demand)


def calculate_gross_margin(price: float, unit_cost: Optional[float]) -> Optional[float]:
    """Compute gross margin proportion: (p - c) / p.

    Note:
        Gross margin represents the percentage of selling price that exceeds unit cost.
        It is strictly defined as (p - c) / p, NOT markup (p - c) / c.

    Args:
        price: Candidate selling price (> 0).
        unit_cost: Wholesale unit cost (COGS).

    Returns:
        Gross margin proportion (e.g. 0.25 for 25%), or None if unit_cost is None.

    Raises:
        ValueError: If price is non-finite or <= 0.
    """
    if unit_cost is None:
        return None

    if math.isnan(price) or math.isinf(price) or price <= 0:
        raise ValueError(f"Price must be a positive finite number, got {price}")
    if math.isnan(unit_cost) or math.isinf(unit_cost) or unit_cost <= 0:
        raise ValueError(f"Unit cost must be a positive finite number, got {unit_cost}")

    return float((price - unit_cost) / price)
