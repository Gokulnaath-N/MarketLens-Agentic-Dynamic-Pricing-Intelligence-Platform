"""Experiments and ablation study endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from marketlens.api.schemas import ExperimentRunItem
from marketlens.config import get_project_root

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("", response_model=List[ExperimentRunItem])
def list_experiments() -> List[ExperimentRunItem]:
    """Retrieve Phase 5 ablation study experiments and performance deltas."""
    root = get_project_root()
    manifest_file = root / "artifacts" / "phase5" / "ablation_run_manifest.json"

    if not manifest_file.is_file():
        return []

    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        run_id = data.get("run_id", "phase5_run")
        timestamp = data.get("timestamp_utc", "")
        experiments = data.get("experiments", {})

        items: List[ExperimentRunItem] = []
        for exp_key, exp_data in experiments.items():
            metrics = exp_data.get("metrics", {})
            deltas = exp_data.get("deltas_vs_baseline", {})
            items.append(
                ExperimentRunItem(
                    run_id=run_id,
                    timestamp_utc=timestamp,
                    ablation_type=exp_data.get("ablation_type", exp_key),
                    description=exp_data.get("description", ""),
                    features_count=len(exp_data.get("features", [])),
                    mae=round(float(metrics.get("mae", 0.0)), 4),
                    rmse=round(float(metrics.get("rmse", 0.0)), 4),
                    wape=round(float(metrics.get("wape", 0.0)), 4),
                    r2=round(float(metrics.get("r2", 0.0)), 4),
                    delta_wape_vs_baseline=round(float(deltas.get("delta_wape", 0.0)), 4),
                    delta_mae_vs_baseline=round(float(deltas.get("delta_mae", 0.0)), 4),
                )
            )

        return items
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read ablation experiments: {str(e)}"
        )


@router.get("/{run_id}", response_model=Dict[str, Any])
def get_experiment_detail(run_id: str) -> Dict[str, Any]:
    """Retrieve full experiment run manifest by run_id."""
    root = get_project_root()
    manifest_file = root / "artifacts" / "phase5" / "ablation_run_manifest.json"

    if not manifest_file.is_file():
        raise HTTPException(status_code=404, detail="No experiments manifest found.")

    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("run_id") != run_id and run_id != "latest":
            raise HTTPException(
                status_code=404, detail=f"Experiment run '{run_id}' not found."
            )

        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load experiment: {str(e)}"
        )
