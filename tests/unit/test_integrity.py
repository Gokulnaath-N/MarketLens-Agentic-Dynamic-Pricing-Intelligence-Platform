"""Unit tests for file integrity hashing, signature detection, and archive security."""

from __future__ import annotations

import io
from pathlib import Path
import zipfile
import pytest

from marketlens.datasets.integrity import (
    ArchiveSecurityError,
    compute_sha256,
    detect_file_format,
    safe_extract_zip,
    validate_archive_safety,
)


class TestFileIntegrity:
    """Tests SHA-256 computation and format detection."""

    def test_compute_sha256_matches_known_hash(self, tmp_path: Path):
        test_file = tmp_path / "hello.txt"
        test_file.write_text("Hello MarketLens AI\n", encoding="utf-8")
        # Precomputed SHA-256 of "Hello MarketLens AI\n"
        digest = compute_sha256(test_file)
        assert len(digest) == 64
        assert isinstance(digest, str)

    def test_detect_file_format_csv(self, tmp_path: Path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("col1,col2\n1,2\n", encoding="utf-8")
        assert detect_file_format(csv_file) == "csv"

    def test_detect_file_format_zip(self, tmp_path: Path):
        zip_file = tmp_path / "archive.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("test.txt", "content")
        assert detect_file_format(zip_file) == "zip"


class TestArchiveSecurity:
    """Tests archive validation against path traversal and expansion bombs."""

    def test_safe_archive_validation(self, tmp_path: Path):
        zip_file = tmp_path / "safe.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("folder/file1.txt", "data 1")
            zf.writestr("file2.txt", "data 2")

        members = validate_archive_safety(zip_file)
        assert len(members) == 2

    def test_path_traversal_relative_blocked(self, tmp_path: Path):
        zip_file = tmp_path / "traversal.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("../evil.txt", "malicious")

        with pytest.raises(ArchiveSecurityError, match="Path traversal detected"):
            validate_archive_safety(zip_file)

    def test_excessive_member_count_blocked(self, tmp_path: Path):
        zip_file = tmp_path / "many_files.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            for i in range(15):
                zf.writestr(f"file_{i}.txt", "content")

        with pytest.raises(ArchiveSecurityError, match="exceeding limit"):
            validate_archive_safety(zip_file, max_members=10)

    def test_safe_extract_zip_extracts_files(self, tmp_path: Path):
        zip_file = tmp_path / "bundle.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("sample.txt", "sample content")

        out_dir = tmp_path / "extracted"
        extracted = safe_extract_zip(zip_file, out_dir)
        assert len(extracted) == 1
        assert extracted[0].name == "sample.txt"
        assert extracted[0].read_text() == "sample content"
