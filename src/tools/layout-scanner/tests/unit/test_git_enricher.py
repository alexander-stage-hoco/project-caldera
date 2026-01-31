"""
Unit tests for git_enricher.py
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.git_enricher import (
    GitFileMetadata,
    GitEnrichmentResult,
    is_git_repository,
    get_tracked_files,
    _parse_git_log_output,
    get_file_git_metadata,
    enrich_files,
)


class TestGitFileMetadataDataclass:
    """Tests for GitFileMetadata dataclass."""

    def test_default_values(self):
        """GitFileMetadata should have sensible defaults."""
        metadata = GitFileMetadata()
        assert metadata.first_commit_date is None
        assert metadata.last_commit_date is None
        assert metadata.commit_count == 0
        assert metadata.author_count == 0

    def test_custom_values(self):
        """GitFileMetadata should accept custom values."""
        metadata = GitFileMetadata(
            first_commit_date="2024-01-01T10:00:00+00:00",
            last_commit_date="2024-06-15T14:30:00+00:00",
            commit_count=15,
            author_count=3,
        )
        assert metadata.first_commit_date == "2024-01-01T10:00:00+00:00"
        assert metadata.last_commit_date == "2024-06-15T14:30:00+00:00"
        assert metadata.commit_count == 15
        assert metadata.author_count == 3


class TestGitEnrichmentResultDataclass:
    """Tests for GitEnrichmentResult dataclass."""

    def test_default_values(self):
        """GitEnrichmentResult should have sensible defaults."""
        result = GitEnrichmentResult(is_git_repo=True)
        assert result.is_git_repo is True
        assert result.file_metadata == {}
        assert result.tracked_file_count == 0
        assert result.enriched_file_count == 0
        assert result.duration_ms == 0
        assert result.error is None

    def test_non_git_repo(self):
        """GitEnrichmentResult for non-git repo."""
        result = GitEnrichmentResult(is_git_repo=False)
        assert result.is_git_repo is False
        assert result.file_metadata == {}

    def test_with_metadata(self):
        """GitEnrichmentResult with file metadata."""
        metadata = {
            "src/main.py": GitFileMetadata(
                first_commit_date="2024-01-01T10:00:00+00:00",
                last_commit_date="2024-01-15T12:00:00+00:00",
                commit_count=5,
                author_count=2,
            )
        }
        result = GitEnrichmentResult(
            is_git_repo=True,
            file_metadata=metadata,
            tracked_file_count=10,
            enriched_file_count=1,
            duration_ms=150,
        )
        assert result.is_git_repo is True
        assert len(result.file_metadata) == 1
        assert result.file_metadata["src/main.py"].commit_count == 5


class TestIsGitRepository:
    """Tests for is_git_repository function."""

    def test_git_repo_returns_true(self, tmp_path):
        """Should return True for git repository."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        assert is_git_repository(tmp_path) is True

    def test_non_git_returns_false(self, tmp_path):
        """Should return False for non-git directory."""
        assert is_git_repository(tmp_path) is False

    def test_handles_nonexistent_path(self, tmp_path):
        """Should return False for nonexistent path."""
        nonexistent = tmp_path / "does_not_exist"
        assert is_git_repository(nonexistent) is False

    @patch("scripts.git_enricher.subprocess.run")
    def test_handles_timeout(self, mock_run, tmp_path):
        """Should return False on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=10)
        assert is_git_repository(tmp_path) is False


class TestGetTrackedFiles:
    """Tests for get_tracked_files function."""

    def test_empty_repo(self, tmp_path):
        """Should return empty set for repo with no commits."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        tracked = get_tracked_files(tmp_path)
        assert tracked == set()

    def test_tracked_files_returned(self, tmp_path):
        """Should return tracked files after commit."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Create and add files
        (tmp_path / "file1.py").write_text("code")
        (tmp_path / "file2.py").write_text("more code")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=tmp_path,
            capture_output=True,
        )

        tracked = get_tracked_files(tmp_path)
        assert "file1.py" in tracked
        assert "file2.py" in tracked

    def test_untracked_files_excluded(self, tmp_path):
        """Should not include untracked files."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Create committed file
        (tmp_path / "tracked.py").write_text("code")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Create untracked file
        (tmp_path / "untracked.py").write_text("untracked")

        tracked = get_tracked_files(tmp_path)
        assert "tracked.py" in tracked
        assert "untracked.py" not in tracked


class TestParseGitLogOutput:
    """Tests for _parse_git_log_output function."""

    def test_empty_output(self):
        """Should handle empty output."""
        result = _parse_git_log_output("")
        assert result == {}

    def test_single_commit_single_file(self):
        """Should parse single commit with single file."""
        output = "abc123|author@example.com|2024-01-15T10:30:00+00:00\n\nfile.py"
        result = _parse_git_log_output(output)
        assert "file.py" in result
        assert len(result["file.py"]) == 1
        assert result["file.py"][0] == ("author@example.com", "2024-01-15T10:30:00+00:00")

    def test_single_commit_multiple_files(self):
        """Should parse single commit with multiple files."""
        output = "abc123|author@example.com|2024-01-15T10:30:00+00:00\n\nfile1.py\nfile2.py"
        result = _parse_git_log_output(output)
        assert "file1.py" in result
        assert "file2.py" in result

    def test_multiple_commits_same_file(self):
        """Should aggregate commits for same file."""
        output = (
            "abc123|alice@example.com|2024-01-15T10:30:00+00:00\n\n"
            "file.py\n\n"
            "def456|bob@example.com|2024-01-10T09:00:00+00:00\n\n"
            "file.py"
        )
        result = _parse_git_log_output(output)
        assert "file.py" in result
        assert len(result["file.py"]) == 2

    def test_whitespace_handling(self):
        """Should handle whitespace correctly."""
        output = "abc123|author@example.com|2024-01-15T10:30:00+00:00\n\n  file.py  "
        result = _parse_git_log_output(output)
        assert "file.py" in result


class TestGetFileGitMetadata:
    """Tests for get_file_git_metadata function."""

    def test_empty_file_list(self, tmp_path):
        """Should handle empty file list."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        result = get_file_git_metadata(tmp_path, [])
        assert result == {}

    def test_untracked_files_excluded(self, tmp_path):
        """Should exclude untracked files from query."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        result = get_file_git_metadata(tmp_path, ["untracked.py"])
        assert result == {}

    def test_tracked_file_metadata(self, tmp_path):
        """Should get metadata for tracked files."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Create and commit file
        (tmp_path / "main.py").write_text("code")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=tmp_path,
            capture_output=True,
        )

        result = get_file_git_metadata(tmp_path, ["main.py"])

        assert "main.py" in result
        assert result["main.py"].commit_count >= 1
        assert result["main.py"].author_count >= 1
        assert result["main.py"].first_commit_date is not None
        assert result["main.py"].last_commit_date is not None

    def test_multiple_commits(self, tmp_path):
        """Should track multiple commits correctly."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # First commit
        (tmp_path / "main.py").write_text("v1")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "v1"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Second commit
        (tmp_path / "main.py").write_text("v2")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "v2"],
            cwd=tmp_path,
            capture_output=True,
        )

        result = get_file_git_metadata(tmp_path, ["main.py"])

        assert "main.py" in result
        assert result["main.py"].commit_count == 2


class TestEnrichFiles:
    """Tests for enrich_files function."""

    def test_non_git_repo(self, tmp_path):
        """Should return is_git_repo=False for non-git directory."""
        result = enrich_files(tmp_path, ["file.py"])
        assert result.is_git_repo is False
        assert result.file_metadata == {}

    def test_git_repo_empty_files(self, tmp_path):
        """Should handle empty file list."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        result = enrich_files(tmp_path, [])
        assert result.is_git_repo is True
        assert result.tracked_file_count == 0

    def test_git_repo_with_tracked_files(self, tmp_path):
        """Should enrich tracked files."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Create and commit file
        (tmp_path / "main.py").write_text("code")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmp_path,
            capture_output=True,
        )

        result = enrich_files(tmp_path, ["main.py"])

        assert result.is_git_repo is True
        assert result.tracked_file_count == 1
        assert result.enriched_file_count == 1
        assert "main.py" in result.file_metadata
        assert result.duration_ms >= 0

    def test_mixed_tracked_untracked(self, tmp_path):
        """Should only enrich tracked files."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Create tracked file
        (tmp_path / "tracked.py").write_text("code")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Create untracked file
        (tmp_path / "untracked.py").write_text("code")

        result = enrich_files(tmp_path, ["tracked.py", "untracked.py"])

        assert result.is_git_repo is True
        assert result.tracked_file_count == 1
        assert "tracked.py" in result.file_metadata
        assert "untracked.py" not in result.file_metadata

    def test_date_ordering(self, tmp_path):
        """First commit date should be <= last commit date."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Multiple commits
        (tmp_path / "main.py").write_text("v1")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "v1"],
            cwd=tmp_path,
            capture_output=True,
        )

        (tmp_path / "main.py").write_text("v2")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "v2"],
            cwd=tmp_path,
            capture_output=True,
        )

        result = enrich_files(tmp_path, ["main.py"])

        metadata = result.file_metadata.get("main.py")
        assert metadata is not None
        assert metadata.first_commit_date <= metadata.last_commit_date


class TestGitMetadataChecks:
    """Tests for git metadata evaluation checks."""

    def test_check_imports(self):
        """Should be able to import git metadata checks."""
        from scripts.checks.git_metadata import (
            run_git_metadata_checks,
            check_git_pass_recorded,
            check_dates_valid_iso8601,
            check_date_ordering,
            check_commit_count_valid,
            check_author_count_valid,
            check_git_coverage,
        )

    def test_run_checks_without_git_pass(self):
        """Should return empty list when git pass not enabled."""
        from scripts.checks.git_metadata import run_git_metadata_checks

        output = {"passes_completed": ["filesystem"], "files": {}}
        checks = run_git_metadata_checks(output)
        assert checks == []

    def test_run_checks_with_git_pass(self):
        """Should run checks when git pass enabled."""
        from scripts.checks.git_metadata import run_git_metadata_checks

        output = {
            "passes_completed": ["filesystem", "git"],
            "files": {
                "test.py": {
                    "first_commit_date": "2024-01-01T10:00:00+00:00",
                    "last_commit_date": "2024-01-15T12:00:00+00:00",
                    "commit_count": 5,
                    "author_count": 2,
                }
            },
        }
        checks = run_git_metadata_checks(output)
        assert len(checks) == 6  # GT-1 through GT-6

    def test_check_date_ordering_valid(self):
        """Should pass when first_commit <= last_commit."""
        from scripts.checks.git_metadata import check_date_ordering

        output = {
            "files": {
                "test.py": {
                    "first_commit_date": "2024-01-01T10:00:00+00:00",
                    "last_commit_date": "2024-01-15T12:00:00+00:00",
                }
            }
        }
        result = check_date_ordering(output)
        assert result.passed is True

    def test_check_date_ordering_invalid(self):
        """Should fail when first_commit > last_commit."""
        from scripts.checks.git_metadata import check_date_ordering

        output = {
            "files": {
                "test.py": {
                    "first_commit_date": "2024-01-15T12:00:00+00:00",
                    "last_commit_date": "2024-01-01T10:00:00+00:00",
                }
            }
        }
        result = check_date_ordering(output)
        assert result.passed is False

    def test_check_git_coverage_high(self):
        """Should pass when >50% files have git metadata."""
        from scripts.checks.git_metadata import check_git_coverage

        output = {
            "files": {
                "tracked1.py": {"commit_count": 5},
                "tracked2.py": {"commit_count": 3},
                "untracked.py": {"commit_count": None},
            }
        }
        result = check_git_coverage(output)
        assert result.passed is True
        assert "2/3" in result.message

    def test_check_git_coverage_low(self):
        """Should fail when <50% files have git metadata."""
        from scripts.checks.git_metadata import check_git_coverage

        output = {
            "files": {
                "tracked.py": {"commit_count": 5},
                "untracked1.py": {"commit_count": None},
                "untracked2.py": {"commit_count": None},
                "untracked3.py": {"commit_count": None},
            }
        }
        result = check_git_coverage(output)
        assert result.passed is False
