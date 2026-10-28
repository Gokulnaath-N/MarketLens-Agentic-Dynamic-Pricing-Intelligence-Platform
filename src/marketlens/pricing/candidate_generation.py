"""Deterministic, decimal-safe candidate price grid generation."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
import math

from marketlens.logging_config import get_logger

logger = get_logger("marketlens.pricing.candidate_generation")


def generate_candidate_prices(
    price_min: float,
    price_max: float,
    current_price: Optional[float] = None,
    price_step: Optional[float] = None,
    num_candidates: int = 21,
    max_candidates: int = 101,
    precision: int = 2,
    include_current_price: bool = True,
) -> Tuple[List[float], List[str]]:
    """Generate a sorted, deduplicated, decimal-safe grid of candidate selling prices.

    Args:
        price_min: Minimum allowable price (> 0).
        price_max: Maximum allowable price (>= price_min).
        current_price: Optional current selling price. If within bounds, guaranteed to be included.
        price_step: Optional absolute increment between prices.
        num_candidates: Number of points if price_step is not specified.
        max_candidates: Hard safety limit on the maximum number of grid points.
        precision: Currency decimal places for rounding (default 2).
        include_current_price: Whether to explicitly include current_price if valid.

    Returns:
        Tuple of (sorted_unique_prices, generation_notes).

    Raises:
        ValueError: If bounds or parameters are invalid, non-finite, or exceed safety limits.
    """
    notes: List[str] = []

    # 1. Validation of inputs
    for name, val in [("price_min", price_min), ("price_max", price_max)]:
        if math.isnan(val) or math.isinf(val) or val <= 0:
            raise ValueError(f"{name} must be a positive finite number, got {val}")

    if price_min > price_max:
        raise ValueError(f"price_min ({price_min}) cannot exceed price_max ({price_max})")

    if max_candidates < 2:
        raise ValueError(f"max_candidates must be at least 2, got {max_candidates}")

    # Decimal representations
    quant_exp = Decimal(10) ** -precision
    dec_min = Decimal(str(price_min)).quantize(quant_exp, rounding=ROUND_HALF_UP)
    dec_max = Decimal(str(price_max)).quantize(quant_exp, rounding=ROUND_HALF_UP)

    # Edge case: single price point
    if dec_min == dec_max:
        return [float(dec_min)], ["Single point grid: price_min equals price_max."]

    # 2. Determine step size
    if price_step is not None:
        if math.isnan(price_step) or math.isinf(price_step) or price_step <= 0:
            raise ValueError(f"price_step must be positive finite, got {price_step}")
        dec_step = Decimal(str(price_step)).quantize(quant_exp, rounding=ROUND_HALF_UP)
        if dec_step <= Decimal("0"):
            dec_step = Decimal(str(10 ** -precision))
    else:
        if num_candidates < 2:
            num_candidates = 2
        # Calculate step to span [dec_min, dec_max] across num_candidates points
        raw_step = (dec_max - dec_min) / Decimal(str(num_candidates - 1))
        dec_step = max(raw_step.quantize(quant_exp, rounding=ROUND_HALF_UP), Decimal(str(10 ** -precision)))

    # 3. Safety check on resulting count
    estimated_points = int(math.ceil((dec_max - dec_min) / dec_step)) + 1
    if estimated_points > max_candidates:
        raise ValueError(
            f"Requested grid would generate {estimated_points} points, exceeding max_candidates limit ({max_candidates}). "
            f"Increase price_step or adjust price bounds."
        )

    # 4. Generate candidate points
    candidates: List[Decimal] = []
    curr = dec_min
    while curr < dec_max:
        candidates.append(curr)
        curr = (curr + dec_step).quantize(quant_exp, rounding=ROUND_HALF_UP)

    # Always ensure dec_max is included as the upper bound endpoint
    if not candidates or candidates[-1] < dec_max:
        candidates.append(dec_max)

    # 5. Optionally include current_price
    if include_current_price and current_price is not None:
        if not math.isnan(current_price) and not math.isinf(current_price) and current_price > 0:
            dec_current = Decimal(str(current_price)).quantize(quant_exp, rounding=ROUND_HALF_UP)
            if dec_min <= dec_current <= dec_max:
                candidates.append(dec_current)
            else:
                notes.append(
                    f"Current price {float(dec_current)} is outside bounds [{float(dec_min)}, {float(dec_max)}] and was omitted."
                )

    # 6. Deduplicate and sort
    unique_sorted = sorted({p for p in candidates if p > Decimal("0")})
    result_floats = [float(p) for p in unique_sorted]

    if len(result_floats) > max_candidates:
        # Truncate if inclusion tipped it over (unlikely with unique set)
        result_floats = result_floats[:max_candidates]
        notes.append(f"Grid truncated to max_candidates ({max_candidates}).")

    return result_floats, notes
