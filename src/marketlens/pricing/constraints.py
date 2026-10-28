"""Business constraints evaluation and feasibility auditing for candidate prices."""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from marketlens.logging_config import get_logger

logger = get_logger("marketlens.pricing.constraints")


def check_price_bounds(price: float, price_min: float, price_max: float) -> Tuple[bool, Optional[str]]:
    """Verify candidate price falls within permitted [price_min, price_max] bounds."""
    # Allow 1e-6 epsilon for float boundary comparisons
    if price < price_min - 1e-6:
        return False, f"Price {price:.2f} is below minimum bound {price_min:.2f}"
    if price > price_max + 1e-6:
        return False, f"Price {price:.2f} is above maximum bound {price_max:.2f}"
    return True, None


def check_price_movement(
    price: float, current_price: float, max_change_pct: Optional[float]
) -> Tuple[bool, Optional[str]]:
    """Verify price adjustment does not exceed max_change_pct relative to current_price.

    Formula:
        abs(price - current_price) / current_price <= max_change_pct
    """
    if max_change_pct is None:
        return True, None

    if current_price <= 0:
        return False, f"Invalid current_price {current_price} for price movement check"

    relative_change = abs(price - current_price) / current_price
    if relative_change > max_change_pct + 1e-6:
        return (
            False,
            f"Price change {relative_change * 100:.1f}% exceeds maximum permitted {max_change_pct * 100:.1f}%",
        )
    return True, None


def check_margin_floor(
    price: float, unit_cost: Optional[float], min_margin: Optional[float]
) -> Tuple[bool, Optional[str]]:
    """Verify gross margin (p - c)/p meets or exceeds min_margin threshold."""
    if min_margin is None:
        return True, None

    if unit_cost is None:
        return False, "Cannot enforce min_gross_margin: unit_cost is missing."

    if min_margin >= 1.0 or min_margin < 0.0:
        return False, f"Invalid min_gross_margin {min_margin}: must be in [0.0, 1.0)."

    # Direct margin check: (p - c) / p >= min_margin
    realized_margin = (price - unit_cost) / price
    if realized_margin < min_margin - 1e-6:
        min_required_price = unit_cost / (1.0 - min_margin)
        return (
            False,
            f"Gross margin {realized_margin * 100:.1f}% is below required {min_margin * 100:.1f}% "
            f"(requires price >= {min_required_price:.2f})",
        )
    return True, None


def check_competitor_premium(
    price: float,
    competitor_price: Optional[float],
    max_premium_pct: Optional[float],
) -> Tuple[bool, Optional[str]]:
    """Verify candidate price does not exceed competitor price by more than max_premium_pct."""
    if max_premium_pct is None or competitor_price is None:
        return True, None

    if competitor_price <= 0:
        return True, None  # Skip check if competitor price is non-positive or unavailable

    premium_pct = (price - competitor_price) / competitor_price
    if premium_pct > max_premium_pct + 1e-6:
        return (
            False,
            f"Price premium {premium_pct * 100:.1f}% over competitor ({competitor_price:.2f}) "
            f"exceeds limit {max_premium_pct * 100:.1f}%",
        )
    return True, None


def check_model_support(
    price: float,
    support_min: Optional[float],
    support_max: Optional[float],
    policy: str = "warn",
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Check whether candidate price is within observed historical training support.

    Args:
        price: Candidate price.
        support_min: Minimum price observed in training data for this product/category.
        support_max: Maximum price observed in training data.
        policy: 'reject' to mark candidate infeasible, or 'warn' to emit an advisory warning.

    Returns:
        Tuple of (is_within_support, rejection_reason, warning_message).
    """
    if support_min is None or support_max is None:
        return True, None, "No historical training support metadata available; cannot verify extrapolation."

    is_within = (price >= support_min - 1e-6) and (price <= support_max + 1e-6)
    if is_within:
        return True, None, None

    msg = (
        f"Price {price:.2f} is outside observed historical training support "
        f"[{support_min:.2f}, {support_max:.2f}]."
    )

    if policy.lower() == "reject":
        return False, msg, None
    else:
        return False, None, msg


def evaluate_candidate_constraints(
    price: float,
    price_min: float,
    price_max: float,
    current_price: float,
    unit_cost: Optional[float] = None,
    min_margin: Optional[float] = None,
    max_change_pct: Optional[float] = None,
    competitor_price: Optional[float] = None,
    max_competitor_premium_pct: Optional[float] = None,
    support_min: Optional[float] = None,
    support_max: Optional[float] = None,
    extrapolation_policy: str = "warn",
) -> Tuple[bool, List[str], List[str], bool]:
    """Evaluate all business constraints and model support for a single candidate price.

    Returns:
        Tuple of (is_feasible, rejection_reasons, warnings, is_within_model_support).
    """
    rejections: List[str] = []
    warnings: List[str] = []

    # 1. Price Bounds
    passed_bounds, reason_bounds = check_price_bounds(price, price_min, price_max)
    if not passed_bounds and reason_bounds:
        rejections.append(reason_bounds)

    # 2. Price Movement
    passed_mov, reason_mov = check_price_movement(price, current_price, max_change_pct)
    if not passed_mov and reason_mov:
        rejections.append(reason_mov)

    # 3. Margin Floor
    passed_mar, reason_mar = check_margin_floor(price, unit_cost, min_margin)
    if not passed_mar and reason_mar:
        rejections.append(reason_mar)

    # 4. Competitor Premium
    passed_comp, reason_comp = check_competitor_premium(price, competitor_price, max_competitor_premium_pct)
    if not passed_comp and reason_comp:
        rejections.append(reason_comp)

    # 5. Model Support & Extrapolation
    is_in_support, reason_supp, warn_supp = check_model_support(
        price, support_min, support_max, policy=extrapolation_policy
    )
    if reason_supp:
        rejections.append(reason_supp)
    if warn_supp:
        warnings.append(warn_supp)

    is_feasible = len(rejections) == 0
    return is_feasible, rejections, warnings, is_in_support
