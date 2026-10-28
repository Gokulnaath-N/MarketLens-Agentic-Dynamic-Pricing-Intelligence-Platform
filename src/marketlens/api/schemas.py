"""Pydantic schemas for MarketLens AI REST API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from marketlens.pricing.schemas import (
    CandidateEvaluation,
    OptimizationObjective,
    OptimizationRequest,
    OptimizationResult,
    OptimizationStatus,
)


class HealthResponse(BaseModel):
    """API health status schema."""

    status: str = Field(default="healthy", description="Overall service status.")
    app_name: str = Field(default="MarketLens AI Dynamic Pricing Intelligence Platform")
    version: str = Field(default="0.1.0")
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ModuleStatus(BaseModel):
    """Status summary for a platform subsystem."""

    name: str
    available: bool
    status_label: str
    details: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """Detailed platform status response."""

    health: str = "operational"
    backend_version: str = "0.1.0"
    environment: str = "local"
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    modules: List[ModuleStatus] = Field(default_factory=list)
    dataset_summary: Dict[str, Any] = Field(default_factory=dict)
    models_summary: Any = Field(default_factory=dict)
    phase5_ablation_summary: Dict[str, Any] = Field(default_factory=dict)


class DatasetFileItem(BaseModel):
    """Individual dataset file provenance information."""

    filename: str
    file_path: str
    detected_format: str
    byte_size: int
    sha256_hash: str
    validation_status: str


class DatasetRecord(BaseModel):
    """Dataset item in repository registry."""

    dataset_id: str
    name: str
    publisher: str
    license_name: str
    license_url: str
    acquired_at_utc: str
    citation: str
    files: List[DatasetFileItem] = Field(default_factory=list)
    has_profile: bool = False


class DatasetProfileSummary(BaseModel):
    """Dataset tabular profile metadata."""

    dataset_id: str
    source_file: str
    profiled_at_utc: str
    row_count: int
    column_count: int
    min_timestamp: Optional[str] = None
    max_timestamp: Optional[str] = None
    detected_target_column: Optional[str] = None
    detected_price_column: Optional[str] = None
    detected_time_column: Optional[str] = None
    detected_identifier_columns: List[str] = Field(default_factory=list)
    suitability_for_forecasting: str
    data_quality_issues: List[str] = Field(default_factory=list)
    column_profiles: Dict[str, Any] = Field(default_factory=dict)


class ModelMetricItem(BaseModel):
    """Individual model evaluation metric row."""

    model_name: str
    mae: float
    rmse: float
    wape: float
    r2: float
    evaluation_split: str = "test"


class ForecastModelListResponse(BaseModel):
    """Available models and baseline metrics."""

    models: List[str]
    target_column: str = "units_sold"
    frequency: str = "W-MON"
    evaluation_artifacts_exist: bool = False
    metrics: List[ModelMetricItem] = Field(default_factory=list)
    predictions_preview: List[Dict[str, Any]] = Field(default_factory=list)


class LiveForecastRequest(BaseModel):
    """Request schema for on-demand demand inference."""

    product_id: str = Field(default="22423", description="Product SKU")
    candidate_price: float = Field(..., gt=0.0, description="Evaluated selling price")
    horizon_weeks: int = Field(default=1, ge=1, le=12, description="Forecast steps ahead")
    elasticity: float = Field(default=-1.5, lt=0.0, description="Assumed or estimated price elasticity")
    base_demand: float = Field(default=50.0, gt=0.0, description="Base demand volume at reference price")
    reference_price: float = Field(default=12.75, gt=0.0, description="Reference price for demand adjustment")


class LiveForecastResponse(BaseModel):
    """Demand forecast inference response."""

    product_id: str
    candidate_price: float
    predicted_demand: float
    expected_revenue: float
    horizon_weeks: int
    model_type: str
    is_synthetic: bool
    explanation: str


class CompetitorPriceItem(BaseModel):
    """Competitor price observation."""

    product_id: str
    competitor_name: str
    observed_price: float
    currency: str = "GBP"
    observed_date: str
    source_type: str = "manual_observation"


class ReviewSentimentItem(BaseModel):
    """Review sentiment observation."""

    review_id: str
    product_id: str
    sentiment_label: str
    sentiment_score: float
    rating: Optional[float] = None
    aspects: List[str] = Field(default_factory=list)
    complaint_categories: List[str] = Field(default_factory=list)
    praise_categories: List[str] = Field(default_factory=list)
    summary: str = ""
    evidence_excerpt: Optional[str] = None


class MarketIntelligenceSummary(BaseModel):
    """Aggregated market intelligence status and signals."""

    total_reviews_analyzed: int = 0
    sentiment_breakdown: Dict[str, int] = Field(default_factory=dict)
    top_aspects: List[Dict[str, Any]] = Field(default_factory=list)
    competitors_monitored: List[str] = Field(default_factory=list)
    recent_competitor_observations: List[CompetitorPriceItem] = Field(default_factory=list)
    recent_reviews: List[ReviewSentimentItem] = Field(default_factory=list)
    is_live_feed_available: bool = False
    source_attribution: str = "MarketLens AI Synthesized & Acquired Signal Adapters"


class ExperimentRunItem(BaseModel):
    """Phase 5 Feature ablation experiment run summary."""

    run_id: str
    timestamp_utc: str
    ablation_type: str
    description: str
    features_count: int
    mae: float
    rmse: float
    wape: float
    r2: float
    delta_wape_vs_baseline: float
    delta_mae_vs_baseline: float
