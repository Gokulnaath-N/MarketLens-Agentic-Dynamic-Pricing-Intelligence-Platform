"""Unit tests for dataset manifest serialization, provenance tracking, and candidate inventory."""

from __future__ import annotations

from pathlib import Path
import pytest

from marketlens.datasets.manifests import (
    load_candidate_inventory,
    load_datasets_manifest,
    record_acquired_file,
    save_candidate_inventory,
    save_datasets_manifest,
)
from marketlens.datasets.models import AcquiredFile, CandidateDataset, DatasetProvenance, LicenseInfo


@pytest.fixture
def mock_manifest_file(tmp_path: Path) -> Path:
    return tmp_path / "test_manifest.json"


@pytest.fixture
def mock_inventory_file(tmp_path: Path) -> Path:
    return tmp_path / "test_inventory.json"


class TestDatasetManifests:
    """Tests manifest round-trip loading, saving, and deduplication."""

    def test_save_and_load_candidate_inventory(self, mock_inventory_file: Path):
        lic = LicenseInfo(
            license_name="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            license_type="Open",
            academic_allowed=True,
            verification_date="2026-10-27",
        )
        c = CandidateDataset(
            dataset_id="test_cand",
            name="Test",
            role="sales",
            publisher="TestPub",
            citation="Cite",
            official_url="https://test.org",
            license=lic,
        )

        save_candidate_inventory([c], output_path=mock_inventory_file)
        loaded = load_candidate_inventory(input_path=mock_inventory_file)
        assert len(loaded) == 1
        assert loaded[0].dataset_id == "test_cand"
        assert loaded[0].name == "Test"

    def test_record_acquired_file_idempotence(self, mock_manifest_file: Path):
        file1 = AcquiredFile(
            dataset_id="test_ds",
            filename="data.csv",
            file_path="data/raw/test_ds/data.csv",
            byte_size=1024,
            sha256_hash="abc123def456",
            download_timestamp_utc="2026-10-27T12:00:00Z",
            source_url="https://test.org/data.csv",
            detected_format="csv",
            validation_status="verified",
        )

        # First record
        record_acquired_file(
            dataset_id="test_ds",
            dataset_name="Test Dataset",
            publisher="Pub",
            license_name="MIT",
            license_url="https://mit.edu",
            citation="Cite",
            acquired_file=file1,
            manifest_path=mock_manifest_file,
        )

        manifest = load_datasets_manifest(mock_manifest_file)
        assert "test_ds" in manifest
        assert len(manifest["test_ds"].files) == 1

        # Second record with updated hash (should update existing file, not append duplicate)
        file1_updated = file1.model_copy(update={"sha256_hash": "new_hash_789"})
        record_acquired_file(
            dataset_id="test_ds",
            dataset_name="Test Dataset",
            publisher="Pub",
            license_name="MIT",
            license_url="https://mit.edu",
            citation="Cite",
            acquired_file=file1_updated,
            manifest_path=mock_manifest_file,
        )

        manifest_updated = load_datasets_manifest(mock_manifest_file)
        assert len(manifest_updated["test_ds"].files) == 1
        assert manifest_updated["test_ds"].files[0].sha256_hash == "new_hash_789"
