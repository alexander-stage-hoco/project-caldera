"""
Unit tests for content_enricher.py
"""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.content_enricher import (
    ContentFileMetadata,
    ContentEnrichmentResult,
    BINARY_SIGNATURES,
    detect_binary,
    count_lines,
    compute_hash,
    enrich_file,
    enrich_files,
)


class TestContentFileMetadataDataclass:
    """Tests for ContentFileMetadata dataclass."""

    def test_default_values(self):
        """ContentFileMetadata should have sensible defaults."""
        metadata = ContentFileMetadata()
        assert metadata.line_count is None
        assert metadata.is_binary is False
        assert metadata.content_hash is None

    def test_custom_values(self):
        """ContentFileMetadata should accept custom values."""
        metadata = ContentFileMetadata(
            line_count=100,
            is_binary=True,
            content_hash="abc123",
        )
        assert metadata.line_count == 100
        assert metadata.is_binary is True
        assert metadata.content_hash == "abc123"

    def test_text_file_metadata(self):
        """ContentFileMetadata for a text file."""
        metadata = ContentFileMetadata(
            line_count=50,
            is_binary=False,
            content_hash="sha256hash",
        )
        assert metadata.line_count == 50
        assert metadata.is_binary is False
        assert metadata.content_hash is not None

    def test_binary_file_metadata(self):
        """ContentFileMetadata for a binary file."""
        metadata = ContentFileMetadata(
            line_count=None,
            is_binary=True,
            content_hash="binaryhash",
        )
        assert metadata.line_count is None
        assert metadata.is_binary is True
        assert metadata.content_hash == "binaryhash"


class TestContentEnrichmentResultDataclass:
    """Tests for ContentEnrichmentResult dataclass."""

    def test_default_values(self):
        """ContentEnrichmentResult should have sensible defaults."""
        result = ContentEnrichmentResult()
        assert result.file_metadata == {}
        assert result.enriched_file_count == 0
        assert result.binary_file_count == 0
        assert result.text_file_count == 0
        assert result.skipped_file_count == 0
        assert result.total_lines == 0
        assert result.duration_ms == 0
        assert result.error is None

    def test_with_metadata(self):
        """ContentEnrichmentResult with file metadata."""
        metadata = {
            "src/main.py": ContentFileMetadata(
                line_count=100,
                is_binary=False,
                content_hash="abc123",
            )
        }
        result = ContentEnrichmentResult(
            file_metadata=metadata,
            enriched_file_count=1,
            text_file_count=1,
            total_lines=100,
            duration_ms=50,
        )
        assert len(result.file_metadata) == 1
        assert result.enriched_file_count == 1
        assert result.text_file_count == 1
        assert result.total_lines == 100

    def test_with_error(self):
        """ContentEnrichmentResult with error."""
        result = ContentEnrichmentResult(
            error="Permission denied",
        )
        assert result.error == "Permission denied"


class TestDetectBinary:
    """Tests for detect_binary function."""

    def test_empty_file_is_text(self, tmp_path):
        """Empty file should be detected as text."""
        file = tmp_path / "empty.txt"
        file.write_bytes(b"")
        assert detect_binary(file) is False

    def test_text_file_is_text(self, tmp_path):
        """Plain text file should be detected as text."""
        file = tmp_path / "hello.txt"
        file.write_text("Hello, World!\nThis is a text file.\n")
        assert detect_binary(file) is False

    def test_python_file_is_text(self, tmp_path):
        """Python source file should be detected as text."""
        file = tmp_path / "script.py"
        file.write_text("#!/usr/bin/env python3\nprint('Hello')\n")
        assert detect_binary(file) is False

    def test_utf8_unicode_is_text(self, tmp_path):
        """UTF-8 encoded Unicode file should be detected as text."""
        file = tmp_path / "unicode.txt"
        file.write_text("Hello 世界! 🌍\nこんにちは\n", encoding="utf-8")
        assert detect_binary(file) is False

    def test_null_bytes_are_binary(self, tmp_path):
        """File with null bytes should be detected as binary."""
        file = tmp_path / "binary.bin"
        file.write_bytes(b"Hello\x00World")
        assert detect_binary(file) is True

    def test_png_signature_is_binary(self, tmp_path):
        """PNG file should be detected as binary."""
        file = tmp_path / "image.png"
        file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        assert detect_binary(file) is True

    def test_jpeg_signature_is_binary(self, tmp_path):
        """JPEG file should be detected as binary."""
        file = tmp_path / "image.jpg"
        file.write_bytes(b'\xff\xd8\xff' + b'\x00' * 100)
        assert detect_binary(file) is True

    def test_elf_signature_is_binary(self, tmp_path):
        """ELF executable should be detected as binary."""
        file = tmp_path / "executable"
        file.write_bytes(b'\x7fELF' + b'\x00' * 100)
        assert detect_binary(file) is True

    def test_zip_signature_is_binary(self, tmp_path):
        """ZIP file should be detected as binary."""
        file = tmp_path / "archive.zip"
        file.write_bytes(b'PK\x03\x04' + b'\x00' * 100)
        assert detect_binary(file) is True

    def test_pdf_signature_is_binary(self, tmp_path):
        """PDF file should be detected as binary."""
        file = tmp_path / "document.pdf"
        file.write_bytes(b'%PDF-1.4' + b'\x00' * 100)
        assert detect_binary(file) is True

    def test_gzip_signature_is_binary(self, tmp_path):
        """Gzip file should be detected as binary."""
        file = tmp_path / "archive.gz"
        file.write_bytes(b'\x1f\x8b' + b'\x00' * 100)
        assert detect_binary(file) is True

    def test_macho_signature_is_binary(self, tmp_path):
        """Mach-O binary should be detected as binary."""
        file = tmp_path / "macho"
        file.write_bytes(b'\xcf\xfa\xed\xfe' + b'\x00' * 100)
        assert detect_binary(file) is True

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file should return False (default to text)."""
        file = tmp_path / "nonexistent.txt"
        assert detect_binary(file) is False


class TestCountLines:
    """Tests for count_lines function."""

    def test_empty_file(self, tmp_path):
        """Empty file should have 0 lines."""
        file = tmp_path / "empty.txt"
        file.write_bytes(b"")
        assert count_lines(file) == 0

    def test_single_line_no_newline(self, tmp_path):
        """Single line without newline should count as 1 line."""
        file = tmp_path / "single.txt"
        file.write_text("Hello World")
        assert count_lines(file) == 1

    def test_single_line_with_newline(self, tmp_path):
        """Single line with newline should count as 1 line."""
        file = tmp_path / "single.txt"
        file.write_text("Hello World\n")
        assert count_lines(file) == 1

    def test_multiple_lines(self, tmp_path):
        """Multiple lines should be counted correctly."""
        file = tmp_path / "multi.txt"
        file.write_text("Line 1\nLine 2\nLine 3\n")
        assert count_lines(file) == 3

    def test_multiple_lines_no_trailing_newline(self, tmp_path):
        """Multiple lines without trailing newline."""
        file = tmp_path / "multi.txt"
        file.write_text("Line 1\nLine 2\nLine 3")
        assert count_lines(file) == 3

    def test_only_newlines(self, tmp_path):
        """File with only newlines."""
        file = tmp_path / "newlines.txt"
        file.write_text("\n\n\n")
        assert count_lines(file) == 3

    def test_windows_line_endings(self, tmp_path):
        """Windows line endings should be handled."""
        file = tmp_path / "windows.txt"
        file.write_bytes(b"Line 1\r\nLine 2\r\n")
        # \n is counted, \r is ignored, so 2 lines
        assert count_lines(file) == 2

    def test_mixed_line_endings(self, tmp_path):
        """Mixed line endings should be handled."""
        file = tmp_path / "mixed.txt"
        file.write_bytes(b"Line 1\nLine 2\r\nLine 3\n")
        assert count_lines(file) == 3

    def test_unicode_content(self, tmp_path):
        """Unicode content should be handled."""
        file = tmp_path / "unicode.txt"
        file.write_text("Hello 世界\nこんにちは\n", encoding="utf-8")
        assert count_lines(file) == 2

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file should return 0."""
        file = tmp_path / "nonexistent.txt"
        assert count_lines(file) == 0


class TestComputeHash:
    """Tests for compute_hash function."""

    def test_empty_file_sha256(self, tmp_path):
        """Empty file should have known SHA-256 hash."""
        file = tmp_path / "empty.txt"
        file.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert compute_hash(file) == expected
        assert compute_hash(file) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_simple_content_sha256(self, tmp_path):
        """Simple content should produce correct SHA-256 hash."""
        file = tmp_path / "test.txt"
        content = b"Hello, World!"
        file.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert compute_hash(file) == expected

    def test_sha1_algorithm(self, tmp_path):
        """SHA-1 algorithm should work."""
        file = tmp_path / "test.txt"
        content = b"Hello, World!"
        file.write_bytes(content)
        expected = hashlib.sha1(content).hexdigest()
        assert compute_hash(file, algorithm="sha1") == expected

    def test_md5_algorithm(self, tmp_path):
        """MD5 algorithm should work."""
        file = tmp_path / "test.txt"
        content = b"Hello, World!"
        file.write_bytes(content)
        expected = hashlib.md5(content).hexdigest()
        assert compute_hash(file, algorithm="md5") == expected

    def test_binary_content(self, tmp_path):
        """Binary content should be hashed correctly."""
        file = tmp_path / "binary.bin"
        content = bytes(range(256))
        file.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert compute_hash(file) == expected

    def test_large_content(self, tmp_path):
        """Large content should be hashed correctly."""
        file = tmp_path / "large.txt"
        content = b"x" * 1000000  # 1MB
        file.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert compute_hash(file) == expected

    def test_invalid_algorithm(self, tmp_path):
        """Invalid algorithm should return None."""
        file = tmp_path / "test.txt"
        file.write_bytes(b"content")
        assert compute_hash(file, algorithm="invalid") is None

    def test_nonexistent_file(self, tmp_path):
        """Nonexistent file should return None."""
        file = tmp_path / "nonexistent.txt"
        assert compute_hash(file) is None


class TestEnrichFile:
    """Tests for enrich_file function."""

    def test_text_file(self, tmp_path):
        """Text file should have line count and hash."""
        file = tmp_path / "text.txt"
        file.write_text("Line 1\nLine 2\nLine 3\n")

        metadata = enrich_file(file)

        assert metadata.is_binary is False
        assert metadata.line_count == 3
        assert metadata.content_hash is not None
        assert len(metadata.content_hash) == 64  # SHA-256 hex length

    def test_binary_file(self, tmp_path):
        """Binary file should have no line count but has hash."""
        file = tmp_path / "binary.bin"
        file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

        metadata = enrich_file(file)

        assert metadata.is_binary is True
        assert metadata.line_count is None
        assert metadata.content_hash is not None
        assert len(metadata.content_hash) == 64

    def test_empty_file(self, tmp_path):
        """Empty file should be text with 0 lines."""
        file = tmp_path / "empty.txt"
        file.write_bytes(b"")

        metadata = enrich_file(file)

        assert metadata.is_binary is False
        assert metadata.line_count == 0
        assert metadata.content_hash is not None

    def test_large_file_skipped(self, tmp_path):
        """Files larger than max_size_bytes should be skipped."""
        file = tmp_path / "large.txt"
        file.write_bytes(b"x" * 100)  # 100 bytes

        # Set max size to 50 bytes
        metadata = enrich_file(file, max_size_bytes=50)

        # Should return default metadata (not enriched)
        assert metadata.is_binary is False
        assert metadata.line_count is None
        assert metadata.content_hash is None

    def test_custom_hash_algorithm(self, tmp_path):
        """Custom hash algorithm should be used."""
        file = tmp_path / "test.txt"
        content = b"test content"
        file.write_bytes(content)

        metadata = enrich_file(file, hash_algorithm="sha1")

        expected = hashlib.sha1(content).hexdigest()
        assert metadata.content_hash == expected
        assert len(metadata.content_hash) == 40  # SHA-1 hex length


class TestEnrichFiles:
    """Tests for enrich_files function."""

    def test_empty_file_list(self, tmp_path):
        """Empty file list should return empty result."""
        result = enrich_files(tmp_path, [])

        assert result.file_metadata == {}
        assert result.enriched_file_count == 0
        assert result.binary_file_count == 0
        assert result.text_file_count == 0
        assert result.total_lines == 0

    def test_single_text_file(self, tmp_path):
        """Single text file should be enriched."""
        (tmp_path / "test.txt").write_text("Hello\nWorld\n")

        result = enrich_files(tmp_path, ["test.txt"])

        assert len(result.file_metadata) == 1
        assert result.enriched_file_count == 1
        assert result.text_file_count == 1
        assert result.binary_file_count == 0
        assert result.total_lines == 2
        assert "test.txt" in result.file_metadata
        assert result.file_metadata["test.txt"].line_count == 2

    def test_multiple_files(self, tmp_path):
        """Multiple files should be enriched."""
        (tmp_path / "file1.txt").write_text("Line 1\nLine 2\n")
        (tmp_path / "file2.txt").write_text("A\nB\nC\n")
        (tmp_path / "file3.py").write_text("print('hello')\n")

        result = enrich_files(tmp_path, ["file1.txt", "file2.txt", "file3.py"])

        assert len(result.file_metadata) == 3
        assert result.enriched_file_count == 3
        assert result.text_file_count == 3
        assert result.binary_file_count == 0
        assert result.total_lines == 6  # 2 + 3 + 1

    def test_mixed_text_and_binary(self, tmp_path):
        """Mixed text and binary files."""
        (tmp_path / "text.txt").write_text("Hello\n")
        (tmp_path / "binary.bin").write_bytes(b'\x89PNG' + b'\x00' * 100)

        result = enrich_files(tmp_path, ["text.txt", "binary.bin"])

        assert len(result.file_metadata) == 2
        assert result.text_file_count == 1
        assert result.binary_file_count == 1
        assert result.total_lines == 1

    def test_nonexistent_file_skipped(self, tmp_path):
        """Nonexistent files should be skipped."""
        (tmp_path / "exists.txt").write_text("Hello\n")

        result = enrich_files(tmp_path, ["exists.txt", "nonexistent.txt"])

        assert len(result.file_metadata) == 1
        assert result.enriched_file_count == 1
        assert result.skipped_file_count == 1
        assert "exists.txt" in result.file_metadata
        assert "nonexistent.txt" not in result.file_metadata

    def test_nested_file_paths(self, tmp_path):
        """Files in subdirectories should be enriched."""
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "main.py").write_text("print('hello')\n")

        result = enrich_files(tmp_path, ["src/main.py"])

        assert len(result.file_metadata) == 1
        assert "src/main.py" in result.file_metadata

    def test_duration_tracked(self, tmp_path):
        """Duration should be tracked."""
        (tmp_path / "test.txt").write_text("content\n")

        result = enrich_files(tmp_path, ["test.txt"])

        assert result.duration_ms >= 0


class TestBinarySignatures:
    """Tests for BINARY_SIGNATURES constant."""

    def test_signatures_not_empty(self):
        """BINARY_SIGNATURES should not be empty."""
        assert len(BINARY_SIGNATURES) > 0

    def test_signatures_are_bytes(self):
        """All signatures should be bytes."""
        for sig in BINARY_SIGNATURES:
            assert isinstance(sig, bytes)

    def test_common_signatures_present(self):
        """Common binary signatures should be present."""
        # Check for some common signatures
        signature_starts = [s[:4] for s in BINARY_SIGNATURES]
        assert b'\x7fELF' in BINARY_SIGNATURES  # ELF
        assert b'MZ' in BINARY_SIGNATURES  # DOS/Windows
        assert b'%PDF' in BINARY_SIGNATURES  # PDF


class TestEdgeCases:
    """Tests for edge cases."""

    def test_file_with_only_whitespace(self, tmp_path):
        """File with only whitespace should be text."""
        file = tmp_path / "whitespace.txt"
        file.write_text("   \n\t\n  \n")

        metadata = enrich_file(file)

        assert metadata.is_binary is False
        assert metadata.line_count == 3

    def test_file_with_special_characters(self, tmp_path):
        """File with special characters should be handled."""
        file = tmp_path / "special.txt"
        file.write_text("!@#$%^&*()_+\n<>?:\"{}|\n")

        metadata = enrich_file(file)

        assert metadata.is_binary is False
        assert metadata.line_count == 2

    def test_identical_files_same_hash(self, tmp_path):
        """Identical files should have identical hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = "identical content\n"
        file1.write_text(content)
        file2.write_text(content)

        hash1 = compute_hash(file1)
        hash2 = compute_hash(file2)

        assert hash1 == hash2

    def test_different_files_different_hash(self, tmp_path):
        """Different files should have different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1\n")
        file2.write_text("content 2\n")

        hash1 = compute_hash(file1)
        hash2 = compute_hash(file2)

        assert hash1 != hash2

    def test_very_long_lines(self, tmp_path):
        """File with very long lines should be handled."""
        file = tmp_path / "long_lines.txt"
        file.write_text("x" * 10000 + "\n" + "y" * 10000 + "\n")

        metadata = enrich_file(file)

        assert metadata.is_binary is False
        assert metadata.line_count == 2
        assert metadata.content_hash is not None
