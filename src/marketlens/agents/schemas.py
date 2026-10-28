"""Typed Pydantic schemas for MarketLens AI market intelligence workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SentimentLabel(str, Enum):
    """Normalized sentiment classifications."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    """Schema validation status."""

    VALIDATED = "validated"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class ExtractionMethod(str, Enum):
    """Method utilized for signal extraction."""

    LLM = "llm"
    RULE_BASED = "rule_based"
    MOCK = "mock"


class ChangeDirection(str, Enum):
    """Direction of observed price movement."""

    INCREASE = "increase"
    DECREASE = "decrease"
    UNCHANGED = "unchanged"


class SignalQualityStatus(str, Enum):
    """Data quality and coverage status for aggregated market signals."""

    AVAILABLE = "available"
    MISSING = "missing"
    STALE = "stale"
    INSUFFICIENT_SAMPLE = "insufficient_sample"
    SYNTHETIC_ONLY = "synthetic_only"
    CONFLICTING = "conflicting"


class ReviewInputRecord(BaseModel):
    """Input contract for raw or sanitized customer review records."""

    review_id: str = Field(..., min_length=1, description="Unique source or derived review identifier.")
    product_id: str = Field(..., min_length=1, description="Product identifier scoped to source namespace.")
    review_text: str = Field(..., description="Raw or preprocessed customer feedback text.")
    review_timestamp: Optional[datetime] = Field(default=None, description="Timestamp review was submitted or published.")
    rating: Optional[float] = Field(default=None, ge=1.0, le=5.0, description="Numerical rating on standard 1-5 scale.")
    source_name: str = Field(default="unknown_source", description="Originating dataset or feed identifier.")
    source_record_id: Optional[str] = Field(default=None, description="Original row ID in raw source data.")
    is_synthetic: bool = Field(default=False, description="Whether record is synthetic test data.")
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewInsightOutput(BaseModel):
    """Structured perception signals extracted from a customer review."""

    review_id: str
    product_id: str
    sentiment_label: SentimentLabel
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Normalized score from -1.0 (very negative) to +1.0 (very positive).")
    aspects: List[str] = Field(default_factory=list, description="Extracted product aspect categories.")
    complaint_categories: List[str] = Field(default_factory=list, description="Specific complaint types identified.")
    praise_categories: List[str] = Field(default_factory=list, description="Specific positive praise types identified.")
    summary: str = Field(..., description="Evidence-grounded concise summary.")
    evidence_excerpt: Optional[str] = Field(default=None, description="Exact quotation from review text supporting findings.")
    extraction_method: ExtractionMethod
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: str = "v1"
    validation_status: ValidationStatus = ValidationStatus.VALIDATED
    warnings: List[str] = Field(default_factory=list)
    is_synthetic: bool = False
    review_timestamp: Optional[datetime] = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CompetitorObservation(BaseModel):
    """Raw observation of a competitor's selling price at a specific time."""

    observation_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1, description="Internal product key mapped to competitor SKU.")
    competitor_id: str = Field(..., min_length=1, description="Identifier of competitor merchant.")
    observed_price: float = Field(..., gt=0.0, description="Observed selling price.")
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    observed_at: datetime = Field(..., description="Timestamp of price observation.")
    source_name: str = Field(default="manual_import")
    is_synthetic: bool = Field(default=False)

    @field_validator("observed_price", mode="after")
    @classmethod
    def validate_finite_price(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v) or v <= 0:
            raise ValueError(f"Price must be a positive finite number, got {v}")
        return v


class CompetitorChangeEvent(BaseModel):
    """Deterministic price movement event between two comparable observations."""

    event_id: str
    product_id: str
    competitor_id: str
    previous_price: float
    current_price: float
    absolute_change: float
    percentage_change: float
    direction: ChangeDirection
    threshold_exceeded: bool
    previous_observed_at: datetime
    current_observed_at: datetime
    age_hours: float
    currency: str
    is_stale: bool = False
    is_synthetic: bool = False
    warnings: List[str] = Field(default_factory=list)


class MarketSignalAggregate(BaseModel):
    """Time-aligned, canonical market intelligence feature vector for a product at forecast origin."""

    product_id: str
    as_of_timestamp: datetime = Field(..., description="Forecast decision origin timestamp.")
    
    # Review signal aggregates
    review_count: int = 0
    usable_review_count: int = 0
    mean_sentiment_score: Optional[float] = None
    positive_review_ratio: Optional[float] = None
    negative_review_ratio: Optional[float] = None
    aspect_counts: Dict[str, int] = Field(default_factory=dict)
    complaint_counts: Dict[str, int] = Field(default_factory=dict)
    
    # Competitor signal aggregates
    competitor_count: int = 0
    min_competitor_price: Optional[float] = None
    mean_competitor_price: Optional[float] = None
    max_competitor_price: Optional[float] = None
    latest_competitor_price_change_pct: Optional[float] = None
    competitor_price_drop_flag: bool = False
    
    # Provenance and Quality
    quality_status: SignalQualityStatus = SignalQualityStatus.AVAILABLE
    is_synthetic: bool = False
    feature_version: str = "v1"
    provenance_record_ids: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
