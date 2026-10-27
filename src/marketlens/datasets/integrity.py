"""File integrity verification, checksum calculation, and safe archive extraction."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import List, Tuple
import zipfile


class IntegrityError(Exception):
    """Raised when a file fails checksum or format signature verification."""

    pass


class ArchiveSecurityError(Exception):
    """Raised when an archive fails safety checks (zip bomb, path traversal)."""

    pass


def compute_sha256(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Compute the SHA-256 hash of a file efficiently using streaming chunks.

    Args:
        file_path: Path to the target file.
        chunk_size: Byte size per chunk.

    Returns:
        Hexadecimal SHA-256 string.
    """
    hasher = hashlib.sha256()
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hash calculation: {path}")

    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def detect_file_format(file_path: str | Path) -> str:
    """Inspect magic bytes of a file to detect its actual format."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "rb") as f:
        header = f.read(16)

    if path.suffix.lower() == ".xlsx" and header.startswith(b"PK\x03\x04"):
        return "xlsx"
    if header.startswith(b"PK\x03\x04"):
        return "zip"
    if header.startswith(b"\x1f\x8b"):
        return "gzip"
    if header.startswith(b"PAR1"):
        return "parquet"
    if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "xls" # Compound file binary format (legacy Excel)
    if path.suffix.lower() in [".csv", ".txt", ".tsv"]:
        return "csv"
    if path.suffix.lower() in [".xlsx"]:
        return "xlsx"

    return "unknown"


def validate_archive_safety(
    archive_path: str | Path,
    max_members: int = 100,
    max_uncompressed_bytes: int = 500 * 1024 * 1024, # 500 MB limit
    max_expansion_ratio: float = 20.0,
) -> List[str]:
    """Inspect a zip archive before extraction to prevent zip bombs and directory traversal.

    Args:
        archive_path: Path to the zip archive.
        max_members: Maximum allowable files in archive.
        max_uncompressed_bytes: Maximum total uncompressed byte size.
        max_expansion_ratio: Maximum allowable ratio of uncompressed to compressed size.

    Returns:
        List of verified safe member names.

    Raises:
        ArchiveSecurityError: If the archive violates any safety constraint.
    """
    path = Path(archive_path)
    if not zipfile.is_zipfile(path):
        raise ArchiveSecurityError(f"Not a valid zip archive: {path.name}")

    compressed_size = max(1, path.stat().st_size)
    total_uncompressed = 0
    safe_members: list[str] = []

    with zipfile.ZipFile(path, "r") as zf:
        infolist = zf.infolist()

        if len(infolist) > max_members:
            raise ArchiveSecurityError(
                f"Archive contains {len(infolist)} files, exceeding limit of {max_members}."
            )

        for info in infolist:
            # 1. Path traversal checks
            target_name = info.filename.replace("\\", "/")
            if target_name.startswith("/") or target_name.startswith("../") or "/../" in target_name:
                raise ArchiveSecurityError(
                    f"Path traversal detected in archive member: '{info.filename}'"
                )

            # Prevent Windows drive letters or absolute paths
            if ":" in target_name:
                raise ArchiveSecurityError(
                    f"Forbidden absolute path or drive letter in member: '{info.filename}'"
                )

            total_uncompressed += info.file_size
            safe_members.append(info.filename)

        # 2. Size limit checks
        if total_uncompressed > max_uncompressed_bytes:
            raise ArchiveSecurityError(
                f"Archive uncompressed size ({total_uncompressed / (1024**2):.1f} MB) "
                f"exceeds limit ({max_uncompressed_bytes / (1024**2):.1f} MB)."
            )

        # 3. Expansion ratio check
        ratio = total_uncompressed / compressed_size
        if ratio > max_expansion_ratio and total_uncompressed > (10 * 1024 * 1024):
            raise ArchiveSecurityError(
                f"Suspicious expansion ratio ({ratio:.1f}x) detected, exceeding {max_expansion_ratio}x limit."
            )

    return safe_members


def safe_extract_zip(
    archive_path: str | Path,
    extract_to_dir: str | Path,
) -> List[Path]:
    """Safely extract all members of a verified zip archive.

    Returns:
        List of Path objects for all extracted files.
    """
    path = Path(archive_path)
    dest = Path(extract_to_dir)
    dest.mkdir(parents=True, exist_ok=True)

    safe_members = validate_archive_safety(path)
    extracted_paths: list[Path] = []

    with zipfile.ZipFile(path, "r") as zf:
        for member in safe_members:
            zf.extract(member, path=dest)
            extracted_file = dest / member
            if extracted_file.is_file():
                extracted_paths.append(extracted_file)

    return extracted_paths
