"""
Content metadata enricher for Layout Scanner.

This module analyzes file contents to populate:
- line_count: Number of lines in text files
- is_binary: Whether the file is binary or text
- content_hash: SHA-256 hash of file contents
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Binary detection: common binary file signatures (magic bytes)
BINARY_SIGNATURES = [
    b'\x7fELF',      # ELF executable
    b'MZ',           # DOS/Windows executable
    b'\x89PNG',      # PNG image
    b'\xff\xd8\xff', # JPEG image
    b'GIF8',         # GIF image
    b'PK\x03\x04',   # ZIP archive
    b'PK\x05\x06',   # ZIP archive (empty)
    b'\x1f\x8b',     # Gzip
    b'BZh',          # Bzip2
    b'\xfd7zXZ',     # XZ
    b'Rar!',         # RAR archive
    b'\x00asm',      # WebAssembly
    b'%PDF',         # PDF
    b'\xca\xfe\xba\xbe',  # Mach-O (universal binary)
    b'\xcf\xfa\xed\xfe',  # Mach-O (64-bit)
    b'\xce\xfa\xed\xfe',  # Mach-O (32-bit)
]

# Default buffer size for streaming operations
BUFFER_SIZE = 65536  # 64KB


@dataclass
class ContentFileMetadata:
    """Content metadata for a single file."""

    line_count: int | None = None
    is_binary: bool = False
    content_hash: str | None = None


@dataclass
class ContentEnrichmentResult:
    """Result of content enrichment pass."""

    file_metadata: dict[str, ContentFileMetadata] = field(default_factory=dict)
    enriched_file_count: int = 0
    binary_file_count: int = 0
    text_file_count: int = 0
    skipped_file_count: int = 0
    total_lines: int = 0
    duration_ms: int = 0
    error: str | None = None


def detect_binary(file_path: Path, sample_size: int = 8192) -> bool:
    """
    Detect if a file is binary by examining its contents.

    Uses multiple heuristics:
    1. Check for known binary file signatures (magic bytes)
    2. Check for null bytes in the sample
    3. Check ratio of non-printable characters

    Args:
        file_path: Path to the file
        sample_size: Number of bytes to sample from the start

    Returns:
        True if file appears to be binary, False if text
    """
    try:
        with open(file_path, "rb") as f:
            sample = f.read(sample_size)

        if not sample:
            return False  # Empty file is considered text

        # Check for known binary signatures
        for signature in BINARY_SIGNATURES:
            if sample.startswith(signature):
                return True

        # Check for null bytes (strong indicator of binary)
        if b'\x00' in sample:
            return True

        # Check ratio of non-text bytes
        # Text files should be mostly printable ASCII or valid UTF-8
        try:
            sample.decode('utf-8')
            # Successfully decoded as UTF-8, likely text
            return False
        except UnicodeDecodeError:
            # Try to detect if mostly printable
            text_chars = sum(
                1 for byte in sample
                if byte in range(32, 127) or byte in (9, 10, 13)  # printable + tab, newline, cr
            )
            # If less than 70% text characters, consider binary
            return text_chars / len(sample) < 0.70

    except (IOError, OSError) as e:
        logger.warning(f"Error reading file for binary detection: {file_path}: {e}")
        return False  # Default to text on error


def count_lines(file_path: Path) -> int:
    """
    Count the number of lines in a text file.

    Uses streaming to handle large files efficiently.

    Args:
        file_path: Path to the file

    Returns:
        Number of lines (newline-terminated sequences)
    """
    try:
        line_count = 0
        with open(file_path, "rb") as f:
            # Read in chunks for memory efficiency
            while chunk := f.read(BUFFER_SIZE):
                line_count += chunk.count(b'\n')

        # If file doesn't end with newline but has content, count last line
        # We need to check the last byte
        if line_count == 0:
            # Check if file has any content
            with open(file_path, "rb") as f:
                f.seek(0, 2)  # Seek to end
                if f.tell() > 0:
                    line_count = 1
        else:
            # Check if file ends with newline
            with open(file_path, "rb") as f:
                f.seek(-1, 2)  # Seek to last byte
                last_byte = f.read(1)
                if last_byte != b'\n':
                    line_count += 1

        return line_count

    except (IOError, OSError) as e:
        logger.warning(f"Error counting lines: {file_path}: {e}")
        return 0


def compute_hash(file_path: Path, algorithm: str = "sha256") -> str | None:
    """
    Compute hash of file contents.

    Uses streaming to handle large files efficiently.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (sha256, sha1, md5)

    Returns:
        Hex string of hash, or None on error
    """
    try:
        hasher = hashlib.new(algorithm)

        with open(file_path, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                hasher.update(chunk)

        return hasher.hexdigest()

    except (IOError, OSError) as e:
        logger.warning(f"Error computing hash: {file_path}: {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid hash algorithm: {algorithm}: {e}")
        return None


def enrich_file(
    file_path: Path,
    max_size_bytes: int = 104857600,
    hash_algorithm: str = "sha256",
) -> ContentFileMetadata:
    """
    Enrich a single file with content metadata.

    Args:
        file_path: Path to the file
        max_size_bytes: Maximum file size to process (default 100MB)
        hash_algorithm: Hash algorithm to use

    Returns:
        ContentFileMetadata with populated fields
    """
    metadata = ContentFileMetadata()

    try:
        # Check file size
        file_size = file_path.stat().st_size

        if file_size > max_size_bytes:
            logger.debug(f"Skipping large file: {file_path} ({file_size} bytes)")
            return metadata

        # Detect if binary
        metadata.is_binary = detect_binary(file_path)

        # Count lines only for text files
        if not metadata.is_binary:
            metadata.line_count = count_lines(file_path)

        # Compute hash for all files
        metadata.content_hash = compute_hash(file_path, hash_algorithm)

    except (IOError, OSError) as e:
        logger.warning(f"Error enriching file: {file_path}: {e}")

    return metadata


def enrich_files(
    repo_path: Path,
    file_paths: list[str],
    max_size_bytes: int = 104857600,
    hash_algorithm: str = "sha256",
) -> ContentEnrichmentResult:
    """
    Enrich multiple files with content metadata.

    This is the main entry point for content enrichment.

    Args:
        repo_path: Path to repository root
        file_paths: List of relative file paths to enrich
        max_size_bytes: Maximum file size to process
        hash_algorithm: Hash algorithm to use

    Returns:
        ContentEnrichmentResult with metadata for all files
    """
    start_time = datetime.now()

    result = ContentEnrichmentResult()

    for rel_path in file_paths:
        full_path = repo_path / rel_path

        if not full_path.is_file():
            result.skipped_file_count += 1
            continue

        try:
            metadata = enrich_file(full_path, max_size_bytes, hash_algorithm)
            result.file_metadata[rel_path] = metadata
            result.enriched_file_count += 1

            if metadata.is_binary:
                result.binary_file_count += 1
            else:
                result.text_file_count += 1
                if metadata.line_count:
                    result.total_lines += metadata.line_count

        except Exception as e:
            logger.warning(f"Error processing file {rel_path}: {e}")
            result.skipped_file_count += 1

    result.duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

    return result
