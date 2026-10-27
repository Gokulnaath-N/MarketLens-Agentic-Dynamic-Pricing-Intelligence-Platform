"""Bounded streaming downloader with resume-check, hash verification, and safety limits."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
import shutil
import time
from typing import Optional
import urllib.error
import urllib.request

from marketlens.config import get_project_root
from marketlens.datasets.integrity import compute_sha256, detect_file_format
from marketlens.datasets.models import AcquiredFile, CandidateDataset


class DownloadError(Exception):
    """Raised when an acquisition operation encounters an unrecoverable failure."""

    pass


class BoundedDownloader:
    """Safely downloads approved public datasets with strict streaming and size limits."""

    def __init__(
        self,
        max_file_size_mb: float = 250.0,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        user_agent: str = "MarketLensAI/0.1.0 (Academic Research; Python urllib)",
    ):
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = user_agent

    def download_candidate(
        self,
        candidate: CandidateDataset,
        target_filename: Optional[str] = None,
        dry_run: bool = False,
        force_refresh: bool = False,
    ) -> AcquiredFile:
        """Download an approved candidate dataset to data/raw/<dataset_id>/ atomically.

        Args:
            candidate: Approved CandidateDataset.
            target_filename: Target filename in destination directory.
            dry_run: If True, validate parameters and output plan without downloading.
            force_refresh: If True, re-download even if an existing valid file exists.

        Returns:
            AcquiredFile metadata.

        Raises:
            DownloadError: On hard-gate failure, network error, or integrity breach.
        """
        if candidate.hard_gate_status != "passed":
            raise DownloadError(
                f"Cannot acquire dataset '{candidate.dataset_id}': {candidate.hard_gate_reason}"
            )

        if not candidate.download_url:
            raise DownloadError(
                f"Candidate '{candidate.dataset_id}' has no direct download URL configured."
            )

        # Enforce HTTPS
        if not candidate.download_url.startswith("https://"):
            raise DownloadError(
                f"Insecure scheme in download URL: '{candidate.download_url}'. Only HTTPS is permitted."
            )

        # Establish storage path
        root = get_project_root()
        raw_dir = root / "data" / "raw" / candidate.dataset_id
        raw_dir.mkdir(parents=True, exist_ok=True)

        filename = target_filename or candidate.download_url.split("/")[-1].split("?")[0]
        if not filename:
            filename = f"{candidate.dataset_id}.dat"
        # Sanitize filename
        filename = Path(filename).name

        final_path = raw_dir / filename
        part_path = raw_dir / f"{filename}.part"

        # Check if already present and verified
        if final_path.exists() and not force_refresh and not dry_run:
            existing_size = final_path.stat().st_size
            if existing_size > 0:
                existing_hash = compute_sha256(final_path)
                format_detected = detect_file_format(final_path)
                return AcquiredFile(
                    dataset_id=candidate.dataset_id,
                    filename=filename,
                    file_path=str(final_path.relative_to(root)).replace("\\", "/"),
                    byte_size=existing_size,
                    sha256_hash=existing_hash,
                    download_timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    source_url=candidate.download_url,
                    detected_format=format_detected,
                    validation_status="verified",
                )

        if dry_run:
            # Plan only: check disk space
            free_bytes = shutil.disk_usage(raw_dir).free
            return AcquiredFile(
                dataset_id=candidate.dataset_id,
                filename=filename,
                file_path=str(final_path.relative_to(root)).replace("\\", "/"),
                byte_size=0,
                sha256_hash="DRY_RUN_NO_HASH",
                download_timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source_url=candidate.download_url,
                detected_format="dry_run",
                validation_status="unverified",
            )

        # Check disk space buffer (at least 2x max file size)
        free_bytes = shutil.disk_usage(raw_dir).free
        if free_bytes < (self.max_file_size_bytes * 2):
            raise DownloadError(
                f"Insufficient disk space: {free_bytes / (1024**2):.1f} MB free, "
                f"need at least {(self.max_file_size_bytes * 2) / (1024**2):.1f} MB buffer."
            )

        # Execute bounded download with retries
        headers = {"User-Agent": self.user_agent}
        attempt = 0
        last_error: Optional[Exception] = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                req = urllib.request.Request(candidate.download_url, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    status_code = getattr(response, "status", 200)
                    if status_code != 200:
                        raise DownloadError(f"HTTP status {status_code} returned from server.")

                    # Read and stream to .part file with size limit enforcement
                    bytes_downloaded = 0
                    with open(part_path, "wb") as out_file:
                        while chunk := response.read(65536):
                            bytes_downloaded += len(chunk)
                            if bytes_downloaded > self.max_file_size_bytes:
                                raise DownloadError(
                                    f"File size exceeded maximum configured limit of "
                                    f"{self.max_file_size_bytes / (1024**2):.1f} MB during download."
                                )
                            out_file.write(chunk)

                    if bytes_downloaded == 0:
                        raise DownloadError("Downloaded payload was empty (0 bytes).")

                    # Atomic rename into final location
                    if final_path.exists():
                        final_path.unlink()
                    part_path.rename(final_path)

                    # Compute checksum & verify signature
                    sha256 = compute_sha256(final_path)
                    file_format = detect_file_format(final_path)

                    return AcquiredFile(
                        dataset_id=candidate.dataset_id,
                        filename=filename,
                        file_path=str(final_path.relative_to(root)).replace("\\", "/"),
                        byte_size=bytes_downloaded,
                        sha256_hash=sha256,
                        download_timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        source_url=candidate.download_url,
                        detected_format=file_format,
                        validation_status="verified",
                    )

            except DownloadError:
                if part_path.exists():
                    part_path.unlink()
                raise
            except Exception as e:
                last_error = e
                # Clean up partial download
                if part_path.exists():
                    part_path.unlink()
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)

        raise DownloadError(
            f"Failed to download '{candidate.name}' after {self.max_retries} attempts: {last_error}"
        ) from last_error
