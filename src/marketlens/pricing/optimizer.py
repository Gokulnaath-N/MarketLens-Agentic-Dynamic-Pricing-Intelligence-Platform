"""Master constrained pricing optimization engine."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from marketlens.logging_config import get_logger
from marketlens.pricing.candidate_generation import generate_candidate_prices
from marketlens.pricing.constraints import evaluate_candidate_constraints
from marketlens.pricing.explanation import generate_recommendation_explanation
from marketlens.pricing.objectives import (
    calculate_estimated_profit,
    calculate_expected_revenue,
    calculate_gross_margin,
)
from marketlens.pricing.scenario import (
    build_candidate_scenario_batch,
    validate_model_price_responsiveness,
)
from marketlens.pricing.schemas import (
    CandidateEvaluation,
    OptimizationObjective,
    OptimizationRequest,
    OptimizationResult,
    OptimizationStatus,
)

logger = get_logger("marketlens.pricing.optimizer")


class PricingOptimizer:
    """Constrained pricing optimization engine.

    Evaluates candidate prices on a discrete grid, computes expected revenue and profit,
    enforces business constraints and model-support boundaries, and returns auditable proposals.
    """

    def __init__(
        self,
        tie_breaking_strategy: str = "closest_to_current",
        tie_breaking_tolerance: float = 1e-4,
        extrapolation_policy: str = "warn",
        currency_precision: int = 2,
        max_candidates: int = 101,
        enforce_price_responsiveness: bool = True,
    ):
        self.tie_breaking_strategy = tie_breaking_strategy.lower()
        self.tie_breaking_tolerance = float(tie_breaking_tolerance)
        self.extrapolation_policy = extrapolation_policy.lower()
        self.currency_precision = int(currency_precision)
        self.max_candidates = int(max_candidates)
        self.enforce_price_responsiveness = enforce_price_responsiveness

    def optimize(
        self,
        request: OptimizationRequest,
        predictor: Any,
        feature_cols: Optional[List[str]] = None,
        support_min: Optional[float] = None,
        support_max: Optional[float] = None,
    ) -> OptimizationResult:
        """Execute full optimization flow for a given request and demand predictor.

        Args:
            request: Validated OptimizationRequest contract.
            predictor: Demand predictor object conforming to DemandPredictorProtocol.
            feature_cols: Optional list of expected feature column names.
            support_min: Historical minimum observed price for product.
            support_max: Historical maximum observed price for product.

        Returns:
            OptimizationResult containing candidate table, optimal proposal, and explanation.
        """
        feature_columns = feature_cols or []
        warnings: List[str] = []

        # 1. Generate discrete candidate prices
        try:
            candidates, grid_notes = generate_candidate_prices(
                price_min=request.price_min,
                price_max=request.price_max,
                current_price=request.current_price,
                price_step=request.price_step,
                num_candidates=request.num_candidates or 21,
                max_candidates=self.max_candidates,
                precision=self.currency_precision,
                include_current_price=True,
            )
            warnings.extend(grid_notes)
        except Exception as e:
            logger.error(f"Candidate grid generation failed: {e}")
            return OptimizationResult(
                product_id=request.product_id,
                forecast_horizon=request.forecast_horizon,
                objective=request.objective,
                currency=request.currency,
                current_price=request.current_price,
                status=OptimizationStatus.INPUT_VALIDATION_ERROR,
                is_feasible=False,
                warnings=[f"Grid generation error: {e}"],
                explanation=f"Optimization failed: Unable to generate candidate price grid: {e}",
            )

        # 2. Pricing Validity Gate: verify model is price-responsive
        if self.enforce_price_responsiveness:
            is_responsive = validate_model_price_responsiveness(
                predictor=predictor,
                test_prices=[request.price_min, request.price_max],
                fixed_context=request.demand_context,
                feature_cols=feature_columns,
            )
            if not is_responsive:
                msg = (
                    "Model is price-invariant: Predicted demand does not vary across candidate prices. "
                    "Cannot optimize price using a model that lacks price-response sensitivity."
                )
                logger.warning(msg)
                return OptimizationResult(
                    product_id=request.product_id,
                    forecast_horizon=request.forecast_horizon,
                    objective=request.objective,
                    currency=request.currency,
                    current_price=request.current_price,
                    status=OptimizationStatus.PRICE_INVARIANT_MODEL,
                    is_feasible=False,
                    total_candidates=len(candidates),
                    warnings=[msg],
                    explanation=(
                        f"Optimization halted for product {request.product_id}: The supplied demand model "
                        f"is invariant to candidate price changes. Evaluating revenue or profit against a flat "
                        f"demand curve would trivially select the highest permitted price bound without empirical justification."
                    ),
                )

        # 3. Construct scenario batch and generate predictions
        scenario_df = build_candidate_scenario_batch(
            candidate_prices=candidates,
            fixed_context=request.demand_context,
        )

        try:
            raw_predictions = predictor.predict(scenario_df, feature_cols=feature_columns)
            predicted_demand_array = np.asarray(raw_predictions, dtype=float)
        except Exception as e:
            logger.error(f"Demand prediction failed: {e}")
            return OptimizationResult(
                product_id=request.product_id,
                forecast_horizon=request.forecast_horizon,
                objective=request.objective,
                currency=request.currency,
                current_price=request.current_price,
                status=OptimizationStatus.INPUT_VALIDATION_ERROR,
                is_feasible=False,
                warnings=[f"Predictor error: {e}"],
                explanation=f"Demand predictor failed during scenario scoring: {e}",
            )

        # 4. Evaluate each candidate
        candidate_evals: List[CandidateEvaluation] = []
        for price, demand in zip(candidates, predicted_demand_array):
            finite_demand = max(0.0, float(demand))
            revenue = calculate_expected_revenue(price, finite_demand)
            profit = calculate_estimated_profit(price, request.unit_cost, finite_demand)
            margin = calculate_gross_margin(price, request.unit_cost)

            is_feasible, rejections, cand_warnings, is_in_support = evaluate_candidate_constraints(
                price=price,
                price_min=request.price_min,
                price_max=request.price_max,
                current_price=request.current_price,
                unit_cost=request.unit_cost,
                min_margin=request.min_gross_margin,
                max_change_pct=request.max_price_change_pct,
                competitor_price=request.competitor_reference_price,
                max_competitor_premium_pct=request.max_competitor_price_premium_pct,
                support_min=support_min,
                support_max=support_max,
                extrapolation_policy=self.extrapolation_policy,
            )

            cand_eval = CandidateEvaluation(
                candidate_price=price,
                predicted_demand=finite_demand,
                expected_revenue=revenue,
                estimated_profit=profit,
                gross_margin=margin,
                is_within_model_support=is_in_support,
                is_feasible=is_feasible,
                rejection_reasons=rejections,
                warnings=cand_warnings,
            )
            candidate_evals.append(cand_eval)

        # 5. Filter feasible candidates
        feasible_evals = [c for c in candidate_evals if c.is_feasible]

        if not feasible_evals:
            result = OptimizationResult(
                product_id=request.product_id,
                forecast_horizon=request.forecast_horizon,
                objective=request.objective,
                currency=request.currency,
                current_price=request.current_price,
                status=OptimizationStatus.NO_FEASIBLE_CANDIDATE,
                total_candidates=len(candidate_evals),
                feasible_candidates=0,
                is_feasible=False,
                candidates=candidate_evals,
                warnings=warnings + ["No candidate price satisfied all active business constraints."],
            )
            result.explanation = generate_recommendation_explanation(result)
            return result

        # 6. Rank and select winning candidate
        winning_candidate = self._select_best_candidate(
            feasible_candidates=feasible_evals,
            objective=request.objective,
            current_price=request.current_price,
        )

        result = OptimizationResult(
            product_id=request.product_id,
            forecast_horizon=request.forecast_horizon,
            objective=request.objective,
            currency=request.currency,
            current_price=request.current_price,
            recommended_price=winning_candidate.candidate_price,
            predicted_demand=winning_candidate.predicted_demand,
            expected_revenue=winning_candidate.expected_revenue,
            estimated_profit=winning_candidate.estimated_profit,
            gross_margin=winning_candidate.gross_margin,
            status=OptimizationStatus.SUCCESS,
            total_candidates=len(candidate_evals),
            feasible_candidates=len(feasible_evals),
            is_within_model_support=winning_candidate.is_within_model_support,
            is_feasible=True,
            human_approval_required=True,
            candidates=candidate_evals,
            warnings=warnings + winning_candidate.warnings,
            is_synthetic=request.is_synthetic,
            model_metadata={
                "model_version": request.model_version,
                "support_min": support_min,
                "support_max": support_max,
                "extrapolation_policy": self.extrapolation_policy,
            },
        )
        result.explanation = generate_recommendation_explanation(result)
        return result

    def _select_best_candidate(
        self,
        feasible_candidates: List[CandidateEvaluation],
        objective: OptimizationObjective,
        current_price: float,
    ) -> CandidateEvaluation:
        """Select top candidate using primary objective and deterministic tie-breaking."""
        # Function to extract objective value
        def get_val(c: CandidateEvaluation) -> float:
            if objective == OptimizationObjective.PROFIT:
                return c.estimated_profit if c.estimated_profit is not None else -float("inf")
            return c.expected_revenue

        # Find maximum value
        max_val = max(get_val(c) for c in feasible_candidates)

        # Collect ties within numerical tolerance
        top_candidates = [
            c for c in feasible_candidates if abs(get_val(c) - max_val) <= self.tie_breaking_tolerance
        ]

        if len(top_candidates) == 1:
            return top_candidates[0]

        # Tie-breaking logic
        if self.tie_breaking_strategy == "closest_to_current":
            # Prefer candidate with minimum distance to current_price, then lower price
            return min(top_candidates, key=lambda c: (abs(c.candidate_price - current_price), c.candidate_price))
        elif self.tie_breaking_strategy == "lowest_price":
            return min(top_candidates, key=lambda c: c.candidate_price)
        elif self.tie_breaking_strategy == "highest_price":
            return max(top_candidates, key=lambda c: c.candidate_price)
        else:
            return min(top_candidates, key=lambda c: (abs(c.candidate_price - current_price), c.candidate_price))
