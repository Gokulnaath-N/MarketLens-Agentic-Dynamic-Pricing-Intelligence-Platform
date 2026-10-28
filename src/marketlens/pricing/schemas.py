"""Typed input/output schemas and contracts for the MarketLens AI pricing engine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class OptimizationObjective(str, Enum):
    """Supported optimization objectives."""

    REVENUE = "revenue"
    PROFIT = "profit"


class OptimizationStatus(str, Enum):
    """Terminal statuses for pricing optimization."""

    SUCCESS = "SUCCESS"
    NO_FEASIBLE_CANDIDATE = "NO_FEASIBLE_CANDIDATE"
    INPUT_VALIDATION_ERROR = "INPUT_VALIDATION_ERROR"
    PRICE_INVARIANT_MODEL = "PRICE_INVARIANT_MODEL"
    MISSING_COST_DATA = "MISSING_COST_DATA"


class OptimizationRequest(BaseModel):
    """Input contract for pricing optimization requests."""

    product_id: str = Field(..., min_length=1, description="Unique product SKU or canonical identifier.")
    current_price: float = Field(..., gt=0.0, description="Current selling/reference price. Must be finite > 0.")
    price_min: float = Field(..., gt=0.0, description="Minimum allowed candidate price.")
    price_max: float = Field(..., gt=0.0, description="Maximum allowed candidate price.")
    price_step: Optional[float] = Field(default=None, gt=0.0, description="Explicit grid step. If omitted, num_candidates is used.")
    num_candidates: Optional[int] = Field(default=21, ge=2, le=101, description="Grid candidate count when step is omitted.")
    objective: OptimizationObjective = Field(default=OptimizationObjective.REVENUE, description="Target optimization objective.")
    unit_cost: Optional[float] = Field(default=None, gt=0.0, description="Wholesale cost (COGS). Required if objective is profit.")
    min_gross_margin: Optional[float] = Field(default=None, ge=0.0, lt=1.0, description="Minimum gross margin floor (0.0 <= m < 1.0).")
    max_price_change_pct: Optional[float] = Field(default=None, ge=0.0, description="Maximum allowed percentage price change from current price.")
    competitor_reference_price: Optional[float] = Field(default=None, gt=0.0, description="Validated competitor price observation.")
    max_competitor_price_premium_pct: Optional[float] = Field(default=None, ge=0.0, description="Maximum allowed premium over competitor price.")
    currency: str = Field(default="GBP", description="ISO 4217 currency code.")
    forecast_horizon: int = Field(default=1, ge=1, description="Target forecast period steps ahead.")
    demand_context: Dict[str, Any] = Field(default_factory=dict, description="Feature dictionary containing fixed product/period signals.")
    is_synthetic: bool = Field(default=False, description="Whether input data or costs originate from synthetic simulation.")
    model_version: Optional[str] = Field(default=None, description="Identifier of the demand forecasting model.")

    @field_validator("current_price", "price_min", "price_max", "price_step", "unit_cost", mode="after")
    @classmethod
    def validate_finite_numbers(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("Numeric values must be finite and not NaN.")
        return v

    @model_validator(mode="after")
    def validate_bounds_and_requirements(self) -> OptimizationRequest:
        if self.price_min > self.price_max:
            raise ValueError(f"price_min ({self.price_min}) cannot exceed price_max ({self.price_max}).")

        if self.objective == OptimizationObjective.PROFIT and (self.unit_cost is None or self.unit_cost <= 0):
            raise ValueError("Optimization objective 'profit' strictly requires a positive unit_cost.")

        if self.min_gross_margin is not None and self.unit_cost is None:
            raise ValueError("min_gross_margin constraint requires unit_cost to be provided.")

        return self


class CandidateEvaluation(BaseModel):
    """Detailed evaluation metrics and constraint audits for a single candidate price."""

    candidate_price: float = Field(..., description="Evaluated candidate selling price.")
    predicted_demand: float = Field(..., description="Model-predicted expected demand quantity.")
    expected_revenue: float = Field(..., description="Computed expected revenue: candidate_price * predicted_demand.")
    estimated_profit: Optional[float] = Field(default=None, description="Computed estimated profit: (candidate_price - unit_cost) * predicted_demand.")
    gross_margin: Optional[float] = Field(default=None, description="Computed gross margin proportion: (candidate_price - unit_cost) / candidate_price.")
    is_within_model_support: bool = Field(default=True, description="Whether price lies within observed historical training support.")
    is_feasible: bool = Field(default=True, description="Whether candidate satisfies all active hard business constraints.")
    rejection_reasons: List[str] = Field(default_factory=list, description="List of constraints violated by this candidate.")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings or advisories for this candidate.")


class OptimizationResult(BaseModel):
    """Auditable output contract returned by the pricing optimizer."""

    product_id: str
    forecast_horizon: int
    objective: OptimizationObjective
    currency: str
    current_price: float
    recommended_price: Optional[float] = None
    predicted_demand: Optional[float] = None
    expected_revenue: Optional[float] = None
    estimated_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    status: OptimizationStatus = OptimizationStatus.SUCCESS
    total_candidates: int = 0
    feasible_candidates: int = 0
    is_feasible: bool = True
    is_within_model_support: bool = True
    human_approval_required: bool = True
    candidates: List[CandidateEvaluation] = Field(default_factory=list)
    explanation: str = ""
    warnings: List[str] = Field(default_factory=list)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool = False
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
