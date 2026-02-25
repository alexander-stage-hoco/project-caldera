from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from persistence.entities import LayoutFile


class TestLayoutFileFingerprint:
    """Tests for stable_fingerprint validation on LayoutFile."""

    def _make_layout_file(self, **overrides) -> LayoutFile:
        defaults = dict(
            run_pk=1,
            file_id="f-001",
            relative_path="src/app.py",
            directory_id="d-001",
            filename="app.py",
            extension=".py",
            language="Python",
            category="source",
            size_bytes=100,
            line_count=10,
            is_binary=False,
        )
        defaults.update(overrides)
        return LayoutFile(**defaults)

    def test_valid_sha256_fingerprint(self) -> None:
        f = self._make_layout_file(stable_fingerprint="a" * 64)
        assert f.stable_fingerprint == "a" * 64

    def test_valid_sha1_fingerprint(self) -> None:
        f = self._make_layout_file(stable_fingerprint="b" * 40)
        assert f.stable_fingerprint == "b" * 40

    def test_valid_md5_fingerprint(self) -> None:
        f = self._make_layout_file(stable_fingerprint="c" * 32)
        assert f.stable_fingerprint == "c" * 32

    def test_none_fingerprint(self) -> None:
        f = self._make_layout_file(stable_fingerprint=None)
        assert f.stable_fingerprint is None

    def test_default_fingerprint_is_none(self) -> None:
        f = self._make_layout_file()
        assert f.stable_fingerprint is None

    def test_invalid_length_raises(self) -> None:
        with pytest.raises(ValueError, match="stable_fingerprint must be a valid hex hash"):
            self._make_layout_file(stable_fingerprint="abc123")

    def test_invalid_length_50_raises(self) -> None:
        with pytest.raises(ValueError, match="stable_fingerprint must be a valid hex hash"):
            self._make_layout_file(stable_fingerprint="x" * 50)

    def test_empty_string_fingerprint_raises(self) -> None:
        """Empty string has length 0, not in (32, 40, 64) → ValueError."""
        with pytest.raises(ValueError, match="stable_fingerprint must be a valid hex hash"):
            self._make_layout_file(stable_fingerprint="")

    def test_non_hex_chars_accepted(self) -> None:
        """Non-hex chars pass because validation is length-only."""
        f = self._make_layout_file(stable_fingerprint="z" * 64)
        assert f.stable_fingerprint == "z" * 64

    def test_mixed_case_hex_accepted(self) -> None:
        """Mixed-case hex string of valid length passes."""
        mixed = ("aAbBcCdD" * 8)  # 64 chars
        f = self._make_layout_file(stable_fingerprint=mixed)
        assert f.stable_fingerprint == mixed

    def test_fingerprint_length_1_raises(self) -> None:
        with pytest.raises(ValueError, match="stable_fingerprint must be a valid hex hash"):
            self._make_layout_file(stable_fingerprint="a")

    def test_fingerprint_length_128_raises(self) -> None:
        with pytest.raises(ValueError, match="stable_fingerprint must be a valid hex hash"):
            self._make_layout_file(stable_fingerprint="a" * 128)
