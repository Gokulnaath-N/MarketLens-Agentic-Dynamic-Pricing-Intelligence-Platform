"""Adapter for UCI Online Retail II dataset acquisition and archive extraction."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import List

from marketlens.config import get_project_root
from marketlens.datasets.adapters.base import BaseDatasetAdapter
from marketlens.datasets.downloader import BoundedDownloader
from marketlens.datasets.integrity import compute_sha256, detect_file_format, safe_extract_zip
from marketlens.datasets.models import AcquiredFile, CandidateDataset


class UCIOnlineRetailIIAdapter(BaseDatasetAdapter):
    """Adapter for downloading and safely unpacking the UCI Online Retail II dataset."""

    def __init__(self, downloader: BoundedDownloader | None = None):
        self.downloader = downloader or BoundedDownloader()

    def acquire(
        self,
        candidate: CandidateDataset,
        dry_run: bool = False,
        force: bool = False,
    ) -> List[AcquiredFile]:
        """Download zip archive from UCI and extract tabular files safely."""
        root = get_project_root()
        archive_file = self.downloader.download_candidate(
            candidate=candidate,
            target_filename="online_retail_ii.zip",
            dry_run=dry_run,
            force_refresh=force,
        )

        acquired_files = [archive_file]
        if dry_run:
            return acquired_files

        # Safely extract archive members into data/raw/uci_online_retail_ii/
        archive_path = root / archive_file.file_path
        extract_dir = archive_path.parent

        extracted_paths = safe_extract_zip(archive_path, extract_dir)
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for ext_path in extracted_paths:
            if ext_path.resolve() == archive_path.resolve():
                continue
            ext_size = ext_path.stat().st_size
            ext_hash = compute_sha256(ext_path)
            fmt = detect_file_format(ext_path)
            rel_path = str(ext_path.relative_to(root)).replace("\\", "/")

            acquired_files.append(
                AcquiredFile(
                    dataset_id=candidate.dataset_id,
                    filename=ext_path.name,
                    file_path=rel_path,
                    byte_size=ext_size,
                    sha256_hash=ext_hash,
                    download_timestamp_utc=now_utc,
                    source_url=candidate.download_url or "",
                    detected_format=fmt,
                    validation_status="verified",
                )
            )

        return acquired_files
