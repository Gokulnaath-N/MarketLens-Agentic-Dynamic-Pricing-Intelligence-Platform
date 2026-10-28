"""Health and system status endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter

from marketlens.api.schemas import HealthResponse, ModuleStatus, SystemStatusResponse
from marketlens.config import get_project_root
from marketlens.datasets.manifests import load_datasets_manifest

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Basic health probe."""
    return HealthResponse(status="healthy")


@router.get("/system/status", response_model=SystemStatusResponse)
def get_system_status() -> SystemStatusResponse:
    """Full platform status and module availability report."""
    root = get_project_root()
    manifest = load_datasets_manifest()

    # Module checks
    modules = [
        ModuleStatus(
            name="datasets",
            available=len(manifest) > 0,
            status_label="Registered" if manifest else "Unregistered",
            details=f"{len(manifest)} acquired source(s) tracked in manifest.",
        ),
        ModuleStatus(
            name="forecasting",
            available=(root / "artifacts" / "model_comparison.json").is_file(),
            status_label="Evaluated" if (root / "artifacts" / "model_comparison.json").is_file() else "Pending Evaluation",
            details="Baseline models evaluated on held-out test splits." if (root / "artifacts" / "model_comparison.json").is_file() else "No baseline artifacts found.",
        ),
        ModuleStatus(
            name="pricing_optimizer",
            available=True,
            status_label="Operational",
            details="Constrained optimization engine ready with revenue & profit objectives.",
        ),
        ModuleStatus(
            name="market_intelligence",
            available=True,
            status_label="Operational (Local/Mock/Heuristic)",
            details="Review insight extraction and competitor monitoring adapters active.",
        ),
        ModuleStatus(
            name="experiments",
            available=(root / "artifacts" / "phase5" / "ablation_run_manifest.json").is_file(),
            status_label="Completed" if (root / "artifacts" / "phase5" / "ablation_run_manifest.json").is_file() else "Pending",
            details="Phase 5 four-way feature ablation suite recorded." if (root / "artifacts" / "phase5" / "ablation_run_manifest.json").is_file() else "No ablation runs recorded.",
        ),
    ]

    # Datasets summary
    ds_summary = {
        "registered_count": len(manifest),
        "dataset_ids": list(manifest.keys()),
    }

    # Model summary
    model_summary = {}
    model_cmp_file = root / "artifacts" / "model_comparison.json"
    if model_cmp_file.is_file():
        try:
            with open(model_cmp_file, "r", encoding="utf-8") as f:
                model_summary = json.load(f)
        except Exception:
            model_summary = {"error": "Could not read model_comparison.json"}

    # Phase 5 ablation summary
    ablation_summary = {}
    ablation_file = root / "artifacts" / "phase5" / "ablation_run_manifest.json"
    if ablation_file.is_file():
        try:
            with open(ablation_file, "r", encoding="utf-8") as f:
                ab_data = json.load(f)
                ablation_summary = {
                    "run_id": ab_data.get("run_id"),
                    "timestamp": ab_data.get("timestamp_utc"),
                    "experiments_count": len(ab_data.get("experiments", {})),
                }
        except Exception:
            ablation_summary = {"error": "Could not read ablation_run_manifest.json"}

    return SystemStatusResponse(
        health="operational",
        modules=modules,
        dataset_summary=ds_summary,
        models_summary=model_summary,
        phase5_ablation_summary=ablation_summary,
    )
