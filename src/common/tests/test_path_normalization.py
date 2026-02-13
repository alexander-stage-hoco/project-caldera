"""Tests for path normalization utilities."""
from __future__ import annotations

from common.path_normalization import is_repo_relative_path


class TestIsRepoRelativePath:
    def test_rejects_dotdot_segment(self) -> None:
        assert is_repo_relative_path("src/../etc/passwd") is False

    def test_rejects_leading_tilde(self) -> None:
        assert is_repo_relative_path("~/secrets") is False

    def test_rejects_bare_dotdot(self) -> None:
        assert is_repo_relative_path("..") is False

    def test_accepts_valid_path(self) -> None:
        assert is_repo_relative_path("src/main.py") is True

    def test_rejects_empty(self) -> None:
        assert is_repo_relative_path("") is False

    def test_rejects_absolute(self) -> None:
        assert is_repo_relative_path("/usr/bin") is False

    def test_rejects_dot_prefix(self) -> None:
        assert is_repo_relative_path("./src") is False

    def test_rejects_backslash(self) -> None:
        assert is_repo_relative_path("src\\main.py") is False

    def test_accepts_dot_directory(self) -> None:
        assert is_repo_relative_path(".github/workflows/ci.yml") is True

    def test_accepts_dotfile(self) -> None:
        assert is_repo_relative_path(".env") is True

    def test_rejects_dotdot_at_end(self) -> None:
        assert is_repo_relative_path("src/..") is False

    def test_accepts_dotdot_in_filename(self) -> None:
        """A filename like 'foo..bar' is valid — only standalone '..' segments are rejected."""
        assert is_repo_relative_path("src/foo..bar") is True
