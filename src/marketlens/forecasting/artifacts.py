"""Artifact persistence for processed datasets, predictions, metrics, and lineage manifests."""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict
import pandas as pd

from marketlens.config import get_project_root
from marketlens.datasets.integrity import compute_sha256
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.forecasting.artifacts")


def save_processed_datasets(
    sales_df: pd.DataFrame,
    demand_df: pd.DataFrame,
    output_dir: Path | None = None,
) -> Dict[str, str]:
    """Persist canonical sales observations and regularized demand time series to Parquet.

    Returns:
        Dictionary mapping dataset name to relative file path.
    """
    root = get_project_root()
    dest = output_dir or (root / "data" / "processed")
    dest.mkdir(parents=True, exist_ok=True)

    sales_path = dest / "sales_observations.parquet"
    demand_path = dest / "demand_timeseries.parquet"

    # Save to Parquet
    logger.info(f"Saving {len(sales_df):,} canonical sales rows to {sales_path.name}...")
    sales_df.to_parquet(sales_path, index=False)

    # Convert object columns if any in demand_df for safe parquet writing
    demand_to_save = demand_df.copy()
    if "data_quality_flags" in demand_to_save.columns:
        demand_to_save["data_quality_flags"] = demand_to_save["data_quality_flags"].astype(str)

    logger.info(f"Saving {len(demand_to_save):,} demand time-series rows to {demand_path.name}...")
    demand_to_save.to_parquet(demand_path, index=False)

    return {
        "sales_observations": str(sales_path.relative_to(root)).replace("\\", "/"),
        "demand_timeseries": str(demand_path.relative_to(root)).replace("\\", "/"),
    }


def save_evaluation_artifacts(
    metrics_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
    split_metadata: Dict[str, Any],
    cleaning_audit: Dict[str, Any],
    output_dir: Path | None = None,
) -> Dict[str, str]:
    """Persist model evaluation results, prediction tables, and derived lineage manifest.

    Returns:
        Dictionary mapping artifact name to relative path.
    """
    root = get_project_root()
    dest = output_dir or (root / "artifacts")
    dest.mkdir(parents=True, exist_ok=True)

    # 1. Model comparison metrics
    metrics_csv = dest / "model_comparison.csv"
    metrics_json = dest / "model_comparison.json"
    metrics_df.to_csv(metrics_csv, index=False)
    metrics_df.to_json(metrics_json, orient="records", indent=2)

    # 2. Test predictions
    preds_parquet = dest / "test_predictions.parquet"
    predictions_df.to_parquet(preds_parquet, index=False)

    # 3. Derived-data manifest in data/manifests/
    manifests_dir = root / "data" / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    derived_manifest_path = manifests_dir / "derived_data_manifest.json"

    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    derived_manifest = {
        "manifest_type": "derived_data_lineage",
        "created_at_utc": now_utc,
        "input_dataset": "uci_online_retail_ii",
        "cleaning_audit": cleaning_audit,
        "split_metadata": split_metadata,
        "artifacts": {
            "sales_observations_parquet": {
                "path": "data/processed/sales_observations.parquet",
                "sha256": compute_sha256(root / "data" / "processed" / "sales_observations.parquet"),
            },
            "demand_timeseries_parquet": {
                "path": "data/processed/demand_timeseries.parquet",
                "sha256": compute_sha256(root / "data" / "processed" / "demand_timeseries.parquet"),
            },
            "test_predictions_parquet": {
                "path": "artifacts/test_predictions.parquet",
                "sha256": compute_sha256(preds_parquet),
            },
            "model_comparison_json": {
                "path": "artifacts/model_comparison.json",
                "sha256": compute_sha256(metrics_json),
            },
        },
    }
    derived_manifest_path.write_text(json.dumps(derived_manifest, indent=2), encoding="utf-8")

    logger.info(f"Saved evaluation artifacts and derived manifest to: {derived_manifest_path.relative_to(root)}")
    return {
        "metrics_csv": str(metrics_csv.relative_to(root)).replace("\\", "/"),
        "metrics_json": str(metrics_json.relative_to(root)).replace("\\", "/"),
        "predictions_parquet": str(preds_parquet.relative_to(root)).replace("\\", "/"),
        "derived_manifest": str(derived_manifest_path.relative_to(root)).replace("\\", "/"),
    }
