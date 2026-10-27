"""Pydantic data models for dataset discovery, acquisition, provenance, and profiling."""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class LicenseInfo(BaseModel):
    """Metadata regarding a candidate source's license and permitted use."""

    model_config = ConfigDict(extra="ignore")

    license_name: str
    license_url: str
    license_type: str = Field(description="e.g. Open / Attribution, Non-Commercial, Custom")
    commercial_allowed: bool = False
    academic_allowed: bool = True
    requires_attribution: bool = True
    verification_date: str = Field(description="ISO date when license terms were verified")


class CandidateDataset(BaseModel):
    """Metadata, feature availability, and rights evaluation for candidate sources."""

    model_config = ConfigDict(extra="ignore")

    dataset_id: str
    name: str
    role: str = Field(description="primary_sales, review_benchmark, forecasting_benchmark, etc.")
    publisher: str
    citation: str
    official_url: str
    download_url: Optional[str] = None
    license: LicenseInfo
    requires_auth: bool = False
    auth_type: Optional[str] = None
    estimated_size_mb: Optional[float] = None
    
    # Feature availability flags
    has_sales_quantity: bool = False
    has_observed_price: bool = False
    has_timestamps: bool = False
    has_customer_reviews: bool = False
    has_competitor_prices: bool = False
    has_unit_costs: bool = False
    has_inventory_or_promotions: bool = False

    # Evaluation gates and scoring
    hard_gate_status: Literal["passed", "blocked_credentials", "blocked_license", "review_required"] = "passed"
    hard_gate_reason: str = ""
    suitability_score: float = 0.0
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    known_limitations: list[str] = Field(default_factory=list)

    decision: Literal["selected", "optional", "blocked", "rejected"] = "optional"
    decision_reason: str = ""


class AcquiredFile(BaseModel):
    """Audit record for a physical file downloaded to local raw storage."""

    model_config = ConfigDict(extra="ignore")

    dataset_id: str
    filename: str
    file_path: str = Field(description="Path relative to the project root")
    byte_size: int
    sha256_hash: str
    download_timestamp_utc: str
    source_url: str
    detected_format: str
    validation_status: Literal["verified", "failed", "unverified"] = "verified"


class DatasetProvenance(BaseModel):
    """Manifest record representing an acquired dataset bundle and its files."""

    model_config = ConfigDict(extra="ignore")

    dataset_id: str
    name: str
    version: str = "1.0"
    publisher: str
    license_name: str
    license_url: str
    citation: str
    acquired_at_utc: str
    files: list[AcquiredFile] = Field(default_factory=list)
    notes: str = ""


class ColumnProfile(BaseModel):
    """Statistical and schema summary for a single tabular column."""

    model_config = ConfigDict(extra="ignore")

    name: str
    inferred_type: str
    total_count: int
    missing_count: int
    missing_pct: float
    distinct_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    median_value: Optional[Any] = None
    sample_values: list[Any] = Field(default_factory=list)


class DataProfileReport(BaseModel):
    """Comprehensive read-only data profiling report for an acquired tabular file."""

    model_config = ConfigDict(extra="ignore")

    dataset_id: str
    source_file: str
    profiled_at_utc: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile] = Field(default_factory=list)
    min_timestamp: Optional[str] = None
    max_timestamp: Optional[str] = None
    duplicate_rows_detected: Optional[int] = None
    detected_identifier_columns: list[str] = Field(default_factory=list)
    detected_target_column: Optional[str] = None
    detected_price_column: Optional[str] = None
    detected_time_column: Optional[str] = None
    data_quality_issues: list[str] = Field(default_factory=list)
    suitability_for_forecasting: str = ""
    unsupported_fields: list[str] = Field(default_factory=list)
