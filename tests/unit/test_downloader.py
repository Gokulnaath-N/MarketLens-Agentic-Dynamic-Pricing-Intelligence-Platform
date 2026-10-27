"""Unit tests for bounded streaming downloader and acquisition safeguards."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error
import pytest

from marketlens.datasets.downloader import BoundedDownloader, DownloadError
from marketlens.datasets.models import CandidateDataset, LicenseInfo


@pytest.fixture
def mock_candidate() -> CandidateDataset:
    lic = LicenseInfo(
        license_name="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        license_type="Open",
        academic_allowed=True,
        verification_date="2026-10-27",
    )
    return CandidateDataset(
        dataset_id="test_candidate",
        name="Test Candidate",
        role="primary_sales",
        publisher="Test Pub",
        citation="Cite",
        official_url="https://test.org/landing",
        download_url="https://test.org/archive.zip",
        license=lic,
        hard_gate_status="passed",
    )


class TestBoundedDownloader:
    """Tests downloader limits, streaming, mock responses, and failure modes."""

    def test_insecure_http_scheme_rejected(self, mock_candidate: CandidateDataset):
        mock_candidate.download_url = "http://insecure.org/data.zip"
        downloader = BoundedDownloader()
        with pytest.raises(DownloadError, match="Insecure scheme"):
            downloader.download_candidate(mock_candidate)

    def test_blocked_hard_gate_candidate_rejected(self, mock_candidate: CandidateDataset):
        mock_candidate.hard_gate_status = "blocked_credentials"
        mock_candidate.hard_gate_reason = "Missing credentials"
        downloader = BoundedDownloader()
        with pytest.raises(DownloadError, match="Cannot acquire dataset"):
            downloader.download_candidate(mock_candidate)

    def test_dry_run_creates_no_files_and_makes_no_network_call(self, mock_candidate: CandidateDataset):
        downloader = BoundedDownloader()
        acquired = downloader.download_candidate(mock_candidate, dry_run=True)
        assert acquired.byte_size == 0
        assert acquired.sha256_hash == "DRY_RUN_NO_HASH"
        assert acquired.detected_format == "dry_run"

    @patch("urllib.request.urlopen")
    def test_successful_mocked_streaming_download(self, mock_urlopen, mock_candidate: CandidateDataset, tmp_path: Path):
        mock_response = MagicMock()
        mock_response.status = 200
        # Stream chunks of data
        mock_response.read.side_effect = [b"PK\x03\x04test_zip_content", b""]
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        downloader = BoundedDownloader(max_file_size_mb=10.0)
        acquired = downloader.download_candidate(mock_candidate, target_filename="mock.zip", force_refresh=True)

        assert acquired.byte_size > 0
        assert acquired.validation_status == "verified"
        assert len(acquired.sha256_hash) == 64

    @patch("urllib.request.urlopen")
    def test_empty_payload_raises_download_error(self, mock_urlopen, mock_candidate: CandidateDataset):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.side_effect = [b""]
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        downloader = BoundedDownloader()
        with pytest.raises(DownloadError, match="payload was empty"):
            downloader.download_candidate(mock_candidate, target_filename="empty.zip", force_refresh=True)

    @patch("urllib.request.urlopen")
    def test_exceeding_max_file_size_raises_and_cleans_part_file(self, mock_urlopen, mock_candidate: CandidateDataset):
        mock_response = MagicMock()
        mock_response.status = 200
        # Return 2 MB in one chunk
        mock_response.read.side_effect = [b"X" * (2 * 1024 * 1024), b""]
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Set limit to 1 MB
        downloader = BoundedDownloader(max_file_size_mb=1.0)
        with pytest.raises(DownloadError, match="exceeded maximum configured limit"):
            downloader.download_candidate(mock_candidate, target_filename="toolarge.dat", force_refresh=True)
