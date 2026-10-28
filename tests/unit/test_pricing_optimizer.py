"""Unit and integration tests for the Master Pricing Optimizer."""

import numpy as np
import pytest

from marketlens.pricing.optimizer import PricingOptimizer
from marketlens.pricing.scenario import ConstantElasticityDemandAdapter
from marketlens.pricing.schemas import (
    OptimizationObjective,
    OptimizationRequest,
    OptimizationStatus,
)


class PriceInvariantMockPredictor:
    """Mock predictor returning constant demand regardless of candidate price."""

    def predict(self, df, feature_cols):
        return np.full(len(df), 50.0)

    def is_price_responsive(self):
        return False


def test_optimizer_revenue_maximization():
    """Verify optimizer selects candidate maximizing expected revenue."""
    current_price = 10.0
    base_demand = 100.0
    # Elasticity = -1.0 means p * Q(p) is flat; elasticity = -0.5 means revenue increases with price
    # elasticity = -2.0 means revenue decreases with price
    adapter = ConstantElasticityDemandAdapter(
        base_demand=base_demand,
        reference_price=current_price,
        elasticity=-2.0,  # Revenue = p * 100 * (p/10)^-2 = 10000 / p. Lower price yields higher revenue
    )

    optimizer = PricingOptimizer(extrapolation_policy="warn")
    request = OptimizationRequest(
        product_id="test_sku_1",
        current_price=current_price,
        price_min=5.0,
        price_max=15.0,
        price_step=1.0,
        objective=OptimizationObjective.REVENUE,
    )

    result = optimizer.optimize(request, predictor=adapter)
    assert result.status == OptimizationStatus.SUCCESS
    assert result.is_feasible
    assert result.recommended_price == 5.0  # lowest price maximizes 1/p revenue
    assert result.human_approval_required is True


def test_optimizer_profit_maximization_with_cost():
    """Verify optimizer selects candidate maximizing contribution profit."""
    current_price = 10.0
    unit_cost = 6.0
    # Demand curve: linear or power
    adapter = ConstantElasticityDemandAdapter(
        base_demand=100.0,
        reference_price=current_price,
        elasticity=-1.5,
    )

    optimizer = PricingOptimizer()
    request = OptimizationRequest(
        product_id="test_sku_2",
        current_price=current_price,
        price_min=7.0,
        price_max=20.0,
        price_step=1.0,
        objective=OptimizationObjective.PROFIT,
        unit_cost=unit_cost,
    )

    result = optimizer.optimize(request, predictor=adapter)
    assert result.status == OptimizationStatus.SUCCESS
    assert result.recommended_price is not None
    assert result.estimated_profit is not None
    assert result.gross_margin is not None
    assert result.gross_margin > 0.0


def test_optimizer_profit_requires_unit_cost():
    """Verify Pydantic validation fails if profit objective is requested without unit_cost."""
    with pytest.raises(ValueError, match="strictly requires a positive unit_cost"):
        OptimizationRequest(
            product_id="test_sku_no_cost",
            current_price=10.0,
            price_min=5.0,
            price_max=15.0,
            objective=OptimizationObjective.PROFIT,
            unit_cost=None,
        )


def test_optimizer_rejects_price_invariant_model():
    """Verify optimizer halts and returns PRICE_INVARIANT_MODEL when model does not respond to price."""
    mock_predictor = PriceInvariantMockPredictor()
    optimizer = PricingOptimizer(enforce_price_responsiveness=True)

    request = OptimizationRequest(
        product_id="test_sku_flat",
        current_price=10.0,
        price_min=5.0,
        price_max=15.0,
        price_step=1.0,
        objective=OptimizationObjective.REVENUE,
    )

    result = optimizer.optimize(request, predictor=mock_predictor)
    assert result.status == OptimizationStatus.PRICE_INVARIANT_MODEL
    assert not result.is_feasible
    assert result.recommended_price is None
    assert any("price-invariant" in w for w in result.warnings)


def test_optimizer_no_feasible_candidates():
    """Verify NO_FEASIBLE_CANDIDATE when all candidates violate constraints."""
    adapter = ConstantElasticityDemandAdapter(
        base_demand=100.0,
        reference_price=10.0,
        elasticity=-1.0,
    )
    optimizer = PricingOptimizer()

    # Set impossible constraints: max_change_pct = 0.01 (only allows 9.9 to 10.1), but grid is [15, 20]
    request = OptimizationRequest(
        product_id="test_sku_infeasible",
        current_price=10.0,
        price_min=15.0,
        price_max=20.0,
        price_step=1.0,
        max_price_change_pct=0.05,  # max price allowed is 10.5, all candidates are >= 15
        objective=OptimizationObjective.REVENUE,
    )

    result = optimizer.optimize(request, predictor=adapter)
    assert result.status == OptimizationStatus.NO_FEASIBLE_CANDIDATE
    assert result.feasible_candidates == 0
    assert result.recommended_price is None


def test_optimizer_tie_breaking_closest_to_current():
    """Verify tie-breaking prefers candidate closest to current price."""
    # Build a predictor where prices 8.0 and 12.0 yield identical revenue
    class SymmetricPredictor:
        def predict(self, df, feature_cols):
            # Demand is 100/p for all prices, so p * Q = 100 constant!
            prices = df["candidate_price"].values
            return 100.0 / prices

        def is_price_responsive(self):
            return True

    optimizer = PricingOptimizer(
        tie_breaking_strategy="closest_to_current",
        tie_breaking_tolerance=1e-4,
    )

    request = OptimizationRequest(
        product_id="test_sku_tie",
        current_price=10.0,
        price_min=6.0,
        price_max=14.0,
        price_step=1.0,
        objective=OptimizationObjective.REVENUE,
    )

    result = optimizer.optimize(request, predictor=SymmetricPredictor())
    assert result.status == OptimizationStatus.SUCCESS
    # Since all yield identical revenue (100.0), candidate closest to 10.0 is 10.0
    assert result.recommended_price == 10.0


def test_optimizer_extrapolation_policy_reject():
    """Verify extrapolation policy 'reject' rejects candidates outside training support."""
    adapter = ConstantElasticityDemandAdapter(
        base_demand=100.0,
        reference_price=10.0,
        elasticity=-1.0,
    )
    optimizer = PricingOptimizer(extrapolation_policy="reject")

    request = OptimizationRequest(
        product_id="test_sku_support",
        current_price=10.0,
        price_min=5.0,
        price_max=25.0,
        price_step=5.0,
        objective=OptimizationObjective.REVENUE,
    )

    # Historical support is [8.0, 15.0]
    result = optimizer.optimize(request, predictor=adapter, support_min=8.0, support_max=15.0)
    assert result.status == OptimizationStatus.SUCCESS
    # Candidates 5.0, 20.0, 25.0 should be marked infeasible under 'reject' policy
    for cand in result.candidates:
        if cand.candidate_price < 8.0 or cand.candidate_price > 15.0:
            assert not cand.is_feasible
            assert any("training support" in r for r in cand.rejection_reasons)
        else:
            assert cand.is_feasible
