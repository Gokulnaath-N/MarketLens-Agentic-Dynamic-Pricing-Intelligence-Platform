"""MarketLens AI Constrained Pricing Optimization Engine."""

from marketlens.pricing.candidate_generation import generate_candidate_prices
from marketlens.pricing.constraints import (
    check_margin_floor,
    check_model_support,
    check_price_bounds,
    check_price_movement,
    evaluate_candidate_constraints,
)
from marketlens.pricing.explanation import generate_recommendation_explanation
from marketlens.pricing.objectives import (
    calculate_estimated_profit,
    calculate_expected_revenue,
    calculate_gross_margin,
)
from marketlens.pricing.optimizer import PricingOptimizer
from marketlens.pricing.scenario import (
    ConstantElasticityDemandAdapter,
    DemandPredictorProtocol,
    DirectModelPredictor,
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

__all__ = [
    "PricingOptimizer",
    "OptimizationRequest",
    "OptimizationResult",
    "OptimizationObjective",
    "OptimizationStatus",
    "CandidateEvaluation",
    "generate_candidate_prices",
    "calculate_expected_revenue",
    "calculate_estimated_profit",
    "calculate_gross_margin",
    "evaluate_candidate_constraints",
    "check_price_bounds",
    "check_price_movement",
    "check_margin_floor",
    "check_model_support",
    "generate_recommendation_explanation",
    "build_candidate_scenario_batch",
    "validate_model_price_responsiveness",
    "ConstantElasticityDemandAdapter",
    "DirectModelPredictor",
    "DemandPredictorProtocol",
]
