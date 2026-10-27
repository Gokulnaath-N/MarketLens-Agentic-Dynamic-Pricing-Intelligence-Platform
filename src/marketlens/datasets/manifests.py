"""Manifest serialization and provenance tracking for datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional
from marketlens.config import get_project_root
from marketlens.datasets.models import AcquiredFile, CandidateDataset, DatasetProvenance


def get_manifests_dir() -> Path:
    """Return Path to data/manifests/ directory."""
    path = get_project_root() / "data" / "manifests"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_candidate_inventory(
    candidates: List[CandidateDataset],
    output_path: Optional[Path] = None,
) -> Path:
    """Save evaluated dataset candidates to dataset_candidate_inventory.json."""
    dest = output_path or (get_manifests_dir() / "dataset_candidate_inventory.json")
    data = [c.model_dump() for c in candidates]
    dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return dest


def load_candidate_inventory(input_path: Optional[Path] = None) -> List[CandidateDataset]:
    """Load candidates from dataset_candidate_inventory.json."""
    src = input_path or (get_manifests_dir() / "dataset_candidate_inventory.json")
    if not src.exists():
        return []
    content = src.read_text(encoding="utf-8")
    data = json.loads(content)
    return [CandidateDataset.model_validate(item) for item in data]


def save_datasets_manifest(
    manifest_records: Dict[str, DatasetProvenance],
    output_path: Optional[Path] = None,
) -> Path:
    """Save acquired dataset provenance records to datasets_manifest.json."""
    dest = output_path or (get_manifests_dir() / "datasets_manifest.json")
    data = {k: v.model_dump() for k, v in manifest_records.items()}
    dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return dest


def load_datasets_manifest(input_path: Optional[Path] = None) -> Dict[str, DatasetProvenance]:
    """Load acquired dataset records from datasets_manifest.json."""
    src = input_path or (get_manifests_dir() / "datasets_manifest.json")
    if not src.exists():
        return {}
    content = src.read_text(encoding="utf-8")
    data = json.loads(content)
    return {k: DatasetProvenance.model_validate(v) for k, v in data.items()}


def record_acquired_file(
    dataset_id: str,
    dataset_name: str,
    publisher: str,
    license_name: str,
    license_url: str,
    citation: str,
    acquired_file: AcquiredFile,
    manifest_path: Optional[Path] = None,
) -> DatasetProvenance:
    """Idempotently add an acquired file to the datasets manifest."""
    manifest = load_datasets_manifest(manifest_path)
    
    if dataset_id not in manifest:
        prov = DatasetProvenance(
            dataset_id=dataset_id,
            name=dataset_name,
            publisher=publisher,
            license_name=license_name,
            license_url=license_url,
            citation=citation,
            acquired_at_utc=acquired_file.download_timestamp_utc,
            files=[acquired_file],
        )
        manifest[dataset_id] = prov
    else:
        prov = manifest[dataset_id]
        # Replace existing record for the same file or append
        existing_idx = next(
            (i for i, f in enumerate(prov.files) if f.filename == acquired_file.filename),
            None,
        )
        if existing_idx is not None:
            prov.files[existing_idx] = acquired_file
        else:
            prov.files.append(acquired_file)

    save_datasets_manifest(manifest, manifest_path)
    return prov
