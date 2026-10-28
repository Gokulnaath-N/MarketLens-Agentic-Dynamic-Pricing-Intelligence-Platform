"""Typed schemas and data contracts for Phase 5 feature ablation experiments."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExperimentVariant(str, Enum):
    """The four canonical feature ablation variants."""

    E0 = "E0_baseline"
    E1 = "E1_reviews"
    E2 = "E2_competitors"
    E3 = "E3_both"


class ExperimentStatus(str, Enum):
    """Execution status of an experiment variant."""

    COMPLETED = "COMPLETED"
    NOT_RUN = "NOT_RUN"
    FAILED = "FAILED"
    SYNTHETIC_SIMULATED = "SYNTHETIC_SIMULATED"


class MetricResult(BaseModel):
    """Evaluation metrics for a specific variant and model."""

    mae: float
    rmse: float
    wape: float
    mase: float
    r2: float
    delta_mae: Optional[float] = None
    delta_rmse: Optional[float] = None
    delta_wape: Optional[float] = None
    pct_delta_mae: Optional[float] = None
    pct_delta_rmse: Optional[float] = None


class VariantRunResult(BaseModel):
    """Complete execution record for an experiment variant."""

    variant_id: ExperimentVariant
    status: ExperimentStatus
    status_reason: Optional[str] = None
    feature_count: int = 0
    feature_names: List[str] = Field(default_factory=list)
    model_name: str = "random_forest"
    test_rows: int = 0
    metrics: Optional[MetricResult] = None
    pricing_recommendation: Optional[Dict[str, Any]] = None
    run_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_synthetic: bool = False


class AblationRunManifest(BaseModel):
    """Provenance and summary manifest for a complete Phase 5 ablation study run."""

    run_id: str
    experiment_name: str = "phase5_hybrid_feature_ablation"
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    primary_dataset: str
    target_column: str
    forecast_horizon: int
    train_range: List[str]
    val_range: List[str]
    test_range: List[str]
    shared_cohort_test_rows: int
    variant_results: Dict[str, VariantRunResult] = Field(default_factory=dict)
    summary_notes: List[str] = Field(default_factory=list)
