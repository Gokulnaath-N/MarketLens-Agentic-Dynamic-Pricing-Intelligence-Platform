"""Deterministic, evidence-based explanation generator for pricing recommendations."""

from __future__ import annotations

from typing import List, Optional
from marketlens.pricing.schemas import OptimizationObjective, OptimizationResult


def generate_recommendation_explanation(result: OptimizationResult) -> str:
    """Generate a structured, evidence-based human-readable explanation of the optimization result.

    Note:
        This function generates deterministic text from verified calculation outcomes.
        It does not make false causal claims or state that prices are globally optimal.
    """
    lines: List[str] = []

    lines.append(f"### Pricing Recommendation Summary (Product: {result.product_id})")
    lines.append(f"- **Optimization Objective:** {result.objective.value.upper()}")
    lines.append(f"- **Current Selling Price:** {result.current_price:.2f} {result.currency}")

    if result.recommended_price is None or not result.is_feasible:
        lines.append("\n**Status: INFEASIBLE / NO RECOMMENDATION**")
        lines.append(
            f"Evaluated {result.total_candidates} candidate prices, but none satisfied all active business constraints."
        )
        if result.warnings:
            lines.append("\n**Active Issues & Caveats:**")
            for w in result.warnings:
                lines.append(f"- {w}")
        lines.append("\n> [!WARNING]\n> Human review required. Live prices must not be changed.")
        return "\n".join(lines)

    # Comparison metrics
    diff_val = result.recommended_price - result.current_price
    diff_pct = (diff_val / result.current_price) * 100.0
    direction = "increase" if diff_val > 0 else ("decrease" if diff_val < 0 else "unchanged")

    lines.append(
        f"- **Recommended Candidate Price:** {result.recommended_price:.2f} {result.currency} "
        f"({direction} of {abs(diff_val):.2f} {result.currency} / {abs(diff_pct):.1f}%)"
    )
    if result.predicted_demand is not None:
        lines.append(f"- **Expected Demand (Period {result.forecast_horizon}):** {result.predicted_demand:.1f} units")
    if result.expected_revenue is not None:
        lines.append(f"- **Estimated Expected Revenue:** {result.expected_revenue:.2f} {result.currency}")
    if result.estimated_profit is not None:
        margin_str = f" ({result.gross_margin * 100:.1f}% gross margin)" if result.gross_margin is not None else ""
        lines.append(f"- **Estimated Contribution Profit:** {result.estimated_profit:.2f} {result.currency}{margin_str}")

    lines.append(f"\n**Grid Search Audit:**")
    lines.append(
        f"- Evaluated {result.total_candidates} discrete candidates; {result.feasible_candidates} met all constraints."
    )
    support_status = "Within observed historical training range." if result.is_within_model_support else "EXTRAPOLATION: Outside historical training range."
    lines.append(f"- **Model Support:** {support_status}")

    if result.warnings:
        lines.append("\n**Advisories & Active Warnings:**")
        for w in result.warnings:
            lines.append(f"- {w}")

    lines.append("\n**Decision-Support & Causal Caveats:**")
    lines.append(
        "- This recommendation maximizes the chosen objective **only among the discrete candidate grid** evaluated."
    )
    lines.append(
        "- Observational demand models reflect historical correlations and do **not** prove causal elasticity."
    )
    lines.append(
        "- **Human Approval Required:** This output is an advisory proposal and must be reviewed and approved by human pricing managers before any action."
    )

    return "\n".join(lines)
