"""Pricing optimization endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from marketlens.pricing.optimizer import PricingOptimizer
from marketlens.pricing.scenario import ConstantElasticityDemandAdapter
from marketlens.pricing.schemas import (
    OptimizationRequest,
    OptimizationResult,
    OptimizationStatus,
)

router = APIRouter(prefix="/pricing", tags=["Pricing Optimizer"])


@router.post("/optimize", response_model=OptimizationResult)
def optimize_pricing(request: OptimizationRequest) -> OptimizationResult:
    """Execute constrained price optimization for candidate SKU.
    
    Evaluates candidate prices, calculates predicted demand, expected revenue,
    and profit (when unit_cost is provided), enforcing business constraints.
    """
    try:
        # Build scenario demand predictor using constant elasticity
        # Reference demand defaults to 50 if context not supplied
        base_demand = float(request.demand_context.get("base_demand", 50.0))
        elasticity = float(request.demand_context.get("elasticity", -1.5))

        predictor = ConstantElasticityDemandAdapter(
            base_demand=base_demand,
            reference_price=request.current_price,
            elasticity=elasticity,
            is_synthetic=request.is_synthetic,
        )

        optimizer = PricingOptimizer(
            tie_breaking_strategy="closest_to_current",
            extrapolation_policy="warn",
        )

        # Observed support range (optional bounds)
        support_min = request.price_min * 0.8
        support_max = request.price_max * 1.2

        result = optimizer.optimize(
            request=request,
            predictor=predictor,
            support_min=support_min,
            support_max=support_max,
        )

        return result

    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization engine failure: {str(e)}",
        )
