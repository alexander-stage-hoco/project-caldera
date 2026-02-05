"""Tests for git_utilities module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ..git_utilities import (
    FALLBACK_COMMIT,
    commit_exists,
    fallback_commit_hash,
    git_head,
    git_run,
    is_fallback_commit,
    resolve_commit,
)


class TestFallbackCommitHash:
    """Tests for fallback_commit_hash function."""

    def test_returns_40_zeros(self):
        """Fallback commit should be exactly 40 zeros."""
        result = fallback_commit_hash()
        assert result == "0" * 40
        assert len(result) == 40

    def test_matches_constant(self):
        """Fallback commit should match FALLBACK_COMMIT constant."""
        assert fallback_commit_hash() == FALLBACK_COMMIT


class TestIsFallbackCommit:
    """Tests for is_fallback_commit function."""

    def test_recognizes_fallback(self):
        """Should recognize the fallback commit."""
        assert is_fallback_commit("0" * 40) is True

    def test_rejects_valid_sha(self):
        """Should reject a valid-looking SHA."""
        assert is_fallback_commit("abc123def456abc123def456abc123def456abc1") is False

    def test_rejects_partial_zeros(self):
        """Should reject partially zero strings."""
        assert is_fallback_commit("0" * 39 + "1") is False

    def test_rejects_empty_string(self):
        """Should reject empty string."""
        assert is_fallback_commit("") is False

    def test_rejects_short_zeros(self):
        """Should reject shorter string of zeros."""
        assert is_fallback_commit("0" * 39) is False


class TestGitRun:
    """Tests for git_run function."""

    @patch("subprocess.run")
    def test_runs_git_command(self, mock_run: MagicMock):
        """Should run git command with correct arguments."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "-C", "/repo", "status"],
            returncode=0,
            stdout="",
            stderr="",
        )

        result = git_run(Path("/repo"), ["status"])

        mock_run.assert_called_once_with(
            ["git", "-C", "/repo", "status"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    @patch("subprocess.run")
    def test_passes_multiple_args(self, mock_run: MagicMock):
        """Should pass multiple arguments to git."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="abc123\n",
            stderr="",
        )

        git_run(Path("/repo"), ["rev-parse", "HEAD"])

        mock_run.assert_called_once_with(
            ["git", "-C", "/repo", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        )


class TestGitHead:
    """Tests for git_head function."""

    @patch("subprocess.run")
    def test_returns_sha_on_success(self, mock_run: MagicMock):
        """Should return SHA when git succeeds."""
        sha = "abc123def456abc123def456abc123def456abc1"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"{sha}\n",
            stderr="",
        )

        result = git_head(Path("/repo"))

        assert result == sha

    @patch("subprocess.run")
    def test_returns_none_on_failure(self, mock_run: MagicMock):
        """Should return None when git fails."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository",
        )

        result = git_head(Path("/not-a-repo"))

        assert result is None

    @patch("subprocess.run")
    def test_strips_whitespace(self, mock_run: MagicMock):
        """Should strip whitespace from output."""
        sha = "abc123def456abc123def456abc123def456abc1"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"  {sha}  \n",
            stderr="",
        )

        result = git_head(Path("/repo"))

        assert result == sha


class TestCommitExists:
    """Tests for commit_exists function."""

    @patch("subprocess.run")
    def test_returns_true_when_exists(self, mock_run: MagicMock):
        """Should return True when commit exists."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        result = commit_exists(Path("/repo"), "abc123")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "cat-file" in call_args
        assert "abc123^{commit}" in call_args

    @patch("subprocess.run")
    def test_returns_false_when_missing(self, mock_run: MagicMock):
        """Should return False when commit doesn't exist."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout="",
            stderr="fatal: Not a valid object name",
        )

        result = commit_exists(Path("/repo"), "invalid")

        assert result is False


class TestResolveCommit:
    """Tests for resolve_commit function."""

    @patch("subprocess.run")
    def test_returns_commit_arg_when_exists_in_repo(self, mock_run: MagicMock):
        """Should return commit_arg when it exists in repo_path."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        result = resolve_commit(Path("/repo"), "abc123")

        assert result == "abc123"

    @patch("subprocess.run")
    def test_returns_commit_arg_when_exists_in_fallback(self, mock_run: MagicMock):
        """Should return commit_arg when it exists in fallback_repo."""

        def mock_run_impl(args, **kwargs):
            # First call: check repo_path - fail
            # Second call: check fallback_repo - succeed
            if args[2] == "/repo":
                return subprocess.CompletedProcess(args=args, returncode=128)
            return subprocess.CompletedProcess(args=args, returncode=0)

        mock_run.side_effect = mock_run_impl

        result = resolve_commit(
            Path("/repo"),
            "abc123",
            fallback_repo=Path("/fallback"),
        )

        assert result == "abc123"

    @patch("subprocess.run")
    def test_raises_when_strict_and_commit_not_found(self, mock_run: MagicMock):
        """Should raise ValueError in strict mode when commit not found."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout="",
            stderr="",
        )

        with pytest.raises(ValueError, match="Commit not found in repo"):
            resolve_commit(Path("/repo"), "abc123", strict=True)

    @patch("subprocess.run")
    def test_returns_commit_arg_when_not_strict(self, mock_run: MagicMock):
        """Should return commit_arg as-is in non-strict mode."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout="",
            stderr="",
        )

        result = resolve_commit(Path("/repo"), "abc123", strict=False)

        assert result == "abc123"

    @patch("subprocess.run")
    def test_auto_detects_head_when_no_commit_arg(self, mock_run: MagicMock):
        """Should auto-detect HEAD when commit_arg is None."""
        sha = "def456abc123def456abc123def456abc123def4"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"{sha}\n",
            stderr="",
        )

        result = resolve_commit(Path("/repo"), None)

        assert result == sha

    @patch("subprocess.run")
    def test_falls_back_to_fallback_repo_head(self, mock_run: MagicMock):
        """Should use fallback_repo HEAD when repo_path has none."""
        sha = "def456abc123def456abc123def456abc123def4"

        def mock_run_impl(args, **kwargs):
            # First call: repo_path HEAD - fail
            # Second call: fallback_repo HEAD - succeed
            if args[2] == "/repo":
                return subprocess.CompletedProcess(args=args, returncode=128)
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=f"{sha}\n",
            )

        mock_run.side_effect = mock_run_impl

        result = resolve_commit(
            Path("/repo"),
            None,
            fallback_repo=Path("/fallback"),
        )

        assert result == sha

    @patch("subprocess.run")
    def test_returns_fallback_hash_when_no_git_repo(self, mock_run: MagicMock):
        """Should return fallback hash when not a git repo."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository",
        )

        result = resolve_commit(Path("/not-a-repo"), None)

        assert result == FALLBACK_COMMIT

    @patch("subprocess.run")
    def test_strict_mode_with_fallback_repo(self, mock_run: MagicMock):
        """Should check fallback_repo before raising in strict mode."""

        def mock_run_impl(args, **kwargs):
            # Both repos fail
            return subprocess.CompletedProcess(args=args, returncode=128)

        mock_run.side_effect = mock_run_impl

        with pytest.raises(ValueError, match="Commit not found in repo"):
            resolve_commit(
                Path("/repo"),
                "abc123",
                fallback_repo=Path("/fallback"),
                strict=True,
            )

    @patch("subprocess.run")
    def test_empty_commit_arg_treated_as_none(self, mock_run: MagicMock):
        """Should treat empty string commit_arg same as None."""
        sha = "def456abc123def456abc123def456abc123def4"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"{sha}\n",
            stderr="",
        )

        # Empty string is falsy, so it should auto-detect HEAD
        result = resolve_commit(Path("/repo"), "")

        assert result == sha
