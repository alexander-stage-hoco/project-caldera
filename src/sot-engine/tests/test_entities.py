from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from persistence.entities import (
    LayoutDirectory,
    LayoutFile,
    ToolRun,
    _validate_relative_path,
)


class TestLayoutFileValidation:
    """Tests for LayoutFile.__post_init__ validation."""

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

    def test_run_pk_zero_raises(self) -> None:
        """run_pk=0 must raise ValueError because _validate_positive_pk requires > 0."""
        with pytest.raises(ValueError, match="run_pk must be positive"):
            self._make_layout_file(run_pk=0)


class TestLayoutDirectoryValidation:
    """Tests for LayoutDirectory.__post_init__ validation."""

    def _make_layout_directory(self, **overrides) -> LayoutDirectory:
        defaults = dict(
            run_pk=1,
            directory_id="d-001",
            relative_path="src",
            parent_id=None,
            depth=0,
            file_count=5,
            total_size_bytes=1000,
        )
        defaults.update(overrides)
        return LayoutDirectory(**defaults)

    def test_negative_depth_raises(self) -> None:
        """Negative depth must raise ValueError via _validate_non_negative."""
        with pytest.raises(ValueError, match="depth must be >= 0"):
            self._make_layout_directory(depth=-1)

    def test_depth_zero_accepted(self) -> None:
        """Depth 0 is valid for root directories."""
        d = self._make_layout_directory(depth=0)
        assert d.depth == 0


class TestToolRunValidation:
    """Tests for ToolRun.__post_init__ validation."""

    def _make_tool_run(self, **overrides) -> ToolRun:
        from datetime import datetime
        defaults = dict(
            collection_run_id="col-1",
            repo_id="repo-1",
            run_id="run-1",
            tool_name="scc",
            tool_version="3.0.0",
            schema_version="1.0.0",
            branch="main",
            commit="a" * 40,
            timestamp=datetime(2025, 1, 1),
        )
        defaults.update(overrides)
        return ToolRun(**defaults)

    def test_commit_39_chars_raises(self) -> None:
        """Commit with 39 chars (one short) must raise ValueError."""
        with pytest.raises(ValueError, match="commit must be a 40-hex string"):
            self._make_tool_run(commit="a" * 39)

    def test_commit_41_chars_raises(self) -> None:
        """Commit with 41 chars (one too many) must also raise."""
        with pytest.raises(ValueError, match="commit must be a 40-hex string"):
            self._make_tool_run(commit="a" * 41)

    def test_commit_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="commit must be a 40-hex string"):
            self._make_tool_run(commit="")


class TestValidateRelativePath:
    """Tests for _validate_relative_path with various invalid inputs."""

    def test_dotdot_prefix_raises(self) -> None:
        """Path starting with '../' must raise ValueError."""
        with pytest.raises(ValueError, match="must not contain '\\.\\.'"):
            _validate_relative_path("../secret", "test_path")

    def test_dot_slash_prefix_raises(self) -> None:
        """Path starting with './' must raise ValueError."""
        with pytest.raises(ValueError, match="must be repo-relative"):
            _validate_relative_path("./foo", "test_path")

    def test_backslash_path_raises(self) -> None:
        """Paths with backslashes must raise ValueError."""
        with pytest.raises(ValueError, match="must use '/' separators"):
            _validate_relative_path("src\\main.py", "test_path")

    def test_absolute_unix_path_raises(self) -> None:
        """Absolute Unix path must raise ValueError."""
        with pytest.raises(ValueError, match="must be repo-relative"):
            _validate_relative_path("/usr/bin/python", "test_path")

    def test_tilde_path_raises(self) -> None:
        """Path starting with ~ must raise ValueError."""
        with pytest.raises(ValueError, match="must be repo-relative"):
            _validate_relative_path("~/Documents/file.txt", "test_path")

    def test_dotdot_in_middle_raises(self) -> None:
        """Path with '..' as a segment in the middle must raise."""
        with pytest.raises(ValueError, match="must not contain '\\.\\.'"):
            _validate_relative_path("src/../secret/file.py", "test_path")

    def test_valid_path_accepted(self) -> None:
        """Normal repo-relative path should not raise."""
        _validate_relative_path("src/main.py", "test_path")  # no exception


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
