"""Dataset endpoints for registry, files, and profiling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from marketlens.api.schemas import DatasetFileItem, DatasetProfileSummary, DatasetRecord
from marketlens.config import get_project_root
from marketlens.datasets.manifests import load_datasets_manifest
from marketlens.datasets.registry import DatasetRegistry

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("", response_model=List[DatasetRecord])
def list_datasets() -> List[DatasetRecord]:
    """List all registered datasets and their local acquisition status."""
    root = get_project_root()
    manifest = load_datasets_manifest()
    registry = DatasetRegistry()
    candidates = {c.dataset_id: c for c in registry.list_candidates()}

    results: List[DatasetRecord] = []

    # Include acquired from manifest
    for ds_id, prov in manifest.items():
        profile_path = root / "data" / "manifests" / "profiles" / f"{ds_id}_profile.json"
        files_items = [
            DatasetFileItem(
                filename=f.filename,
                file_path=str(f.file_path),
                detected_format=f.detected_format,
                byte_size=f.byte_size,
                sha256_hash=f.sha256_hash,
                validation_status=f.validation_status,
            )
            for f in prov.files
        ]

        results.append(
            DatasetRecord(
                dataset_id=ds_id,
                name=prov.name,
                publisher=prov.publisher,
                license_name=prov.license_name,
                license_url=prov.license_url,
                acquired_at_utc=prov.acquired_at_utc,
                citation=prov.citation,
                files=files_items,
                has_profile=profile_path.is_file(),
            )
        )

    # For any candidates not yet acquired, add unacquired records
    for ds_id, cand in candidates.items():
        if ds_id not in manifest:
            profile_path = root / "data" / "manifests" / "profiles" / f"{ds_id}_profile.json"
            results.append(
                DatasetRecord(
                    dataset_id=ds_id,
                    name=cand.name,
                    publisher=cand.publisher,
                    license_name=cand.license.license_name,
                    license_url=cand.license.license_url or "",
                    acquired_at_utc="Not Acquired",
                    citation=cand.citation or "",
                    files=[],
                    has_profile=profile_path.is_file(),
                )
            )

    return results


@router.get("/{dataset_id}/profile", response_model=DatasetProfileSummary)
def get_dataset_profile(dataset_id: str) -> DatasetProfileSummary:
    """Retrieve statistical data profile report for a dataset."""
    root = get_project_root()
    profile_path = root / "data" / "manifests" / "profiles" / f"{dataset_id}_profile.json"

    if not profile_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Profile report for dataset '{dataset_id}' not found. Profile must be generated first.",
        )

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return DatasetProfileSummary(
            dataset_id=data.get("dataset_id", dataset_id),
            source_file=data.get("source_file", "unknown"),
            profiled_at_utc=data.get("profiled_at_utc", ""),
            row_count=data.get("row_count", 0),
            column_count=data.get("column_count", 0),
            min_timestamp=data.get("min_timestamp"),
            max_timestamp=data.get("max_timestamp"),
            detected_target_column=data.get("detected_target_column"),
            detected_price_column=data.get("detected_price_column"),
            detected_time_column=data.get("detected_time_column"),
            detected_identifier_columns=data.get("detected_identifier_columns", []),
            suitability_for_forecasting=data.get("suitability_for_forecasting", "unknown"),
            data_quality_issues=data.get("data_quality_issues", []),
            column_profiles=data.get("column_profiles", {}),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load profile report: {str(e)}"
        )
