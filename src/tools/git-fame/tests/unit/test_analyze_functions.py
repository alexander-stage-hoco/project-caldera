"""Unit tests for git-fame analyze.py functions: run_git_fame, extract_author_metric,
get_git_info, fallback_commit_hash, and analyze_repo.

These tests use mocking to avoid actual subprocess calls and focus on
pure logic paths including error handling, edge cases, and file I/O.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from analyze import (
    run_git_fame,
    extract_author_metric,
    get_git_info,
    fallback_commit_hash,
    analyze_repo,
)


# =============================================================================
# run_git_fame Tests
# =============================================================================


class TestRunGitFame:
    """Test run_git_fame subprocess invocation and output parsing."""

    def test_successful_run_returns_parsed_json(self, tmp_path: Path):
        """Successful git-fame run should return parsed JSON output."""
        expected = {
            "data": [["Alice", 100, 5, 3]],
            "columns": ["Author", "loc", "coms", "fils"],
        }
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(expected)
        mock_result.stderr = ""

        with patch("analyze.subprocess.run", return_value=mock_result):
            result = run_git_fame(tmp_path)

        assert result == expected

    def test_nonzero_returncode_returns_empty_dict(self, tmp_path: Path):
        """Non-zero return code should return empty dict."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "some error"

        with patch("analyze.subprocess.run", return_value=mock_result):
            result = run_git_fame(tmp_path)

        assert result == {}

    def test_invalid_json_output_returns_empty_dict(self, tmp_path: Path):
        """Invalid JSON in stdout should return empty dict."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not valid json {{"
        mock_result.stderr = ""

        with patch("analyze.subprocess.run", return_value=mock_result):
            result = run_git_fame(tmp_path)

        assert result == {}

    def test_by_extension_flag_appends_bytype(self, tmp_path: Path):
        """When by_extension=True, --bytype should be in the command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": [], "columns": []}'

        with patch("analyze.subprocess.run", return_value=mock_result) as mock_run:
            run_git_fame(tmp_path, by_extension=True)

        cmd = mock_run.call_args[0][0]
        assert "--bytype" in cmd

    def test_since_flag_appended(self, tmp_path: Path):
        """When since is provided, --since should be in the command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": [], "columns": []}'

        with patch("analyze.subprocess.run", return_value=mock_result) as mock_run:
            run_git_fame(tmp_path, since="2024-01-01")

        cmd = mock_run.call_args[0][0]
        assert "--since" in cmd
        assert "2024-01-01" in cmd

    def test_until_flag_appended(self, tmp_path: Path):
        """When until is provided, --until should be in the command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": [], "columns": []}'

        with patch("analyze.subprocess.run", return_value=mock_result) as mock_run:
            run_git_fame(tmp_path, until="2024-12-31")

        cmd = mock_run.call_args[0][0]
        assert "--until" in cmd
        assert "2024-12-31" in cmd

    def test_loc_mode_passed_to_command(self, tmp_path: Path):
        """The loc_mode parameter should be passed as --loc argument."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": [], "columns": []}'

        with patch("analyze.subprocess.run", return_value=mock_result) as mock_run:
            run_git_fame(tmp_path, loc_mode="ins")

        cmd = mock_run.call_args[0][0]
        loc_idx = cmd.index("--loc")
        assert cmd[loc_idx + 1] == "ins"

    def test_default_flags_present(self, tmp_path: Path):
        """Default run should include --format json, --branch HEAD, --loc surviving."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": [], "columns": []}'

        with patch("analyze.subprocess.run", return_value=mock_result) as mock_run:
            run_git_fame(tmp_path)

        cmd = mock_run.call_args[0][0]
        assert "--format" in cmd
        assert "json" in cmd
        assert "--branch" in cmd
        assert "HEAD" in cmd
        assert "--loc" in cmd
        assert "surviving" in cmd


# =============================================================================
# extract_author_metric Tests
# =============================================================================


class TestExtractAuthorMetric:
    """Test extraction of author metrics from raw git-fame output."""

    def test_basic_loc_extraction(self):
        """Should extract loc values by author name."""
        raw_output = {
            "data": [["Alice", 500], ["Bob", 300]],
            "columns": ["Author", "loc"],
        }
        result = extract_author_metric(raw_output)
        assert result == {"Alice": 500, "Bob": 300}

    def test_custom_metric_column(self):
        """Should extract a different metric column."""
        raw_output = {
            "data": [["Alice", 500, 50], ["Bob", 300, 30]],
            "columns": ["Author", "loc", "coms"],
        }
        result = extract_author_metric(raw_output, metric_col="coms")
        assert result == {"Alice": 50, "Bob": 30}

    def test_empty_data_returns_empty_dict(self):
        """Empty data should return empty dict."""
        raw_output = {"data": [], "columns": ["Author", "loc"]}
        result = extract_author_metric(raw_output)
        assert result == {}

    def test_missing_columns_key(self):
        """Missing columns key should still work with index fallback."""
        raw_output = {"data": [["Alice", 100]], "columns": []}
        result = extract_author_metric(raw_output)
        # With empty columns, col_idx is empty, fallback to index 0 for Author and 1 for loc
        assert result == {"Alice": 100}

    def test_float_values_converted_to_int(self):
        """Float metric values should be converted to int."""
        raw_output = {
            "data": [["Alice", 100.5]],
            "columns": ["Author", "loc"],
        }
        result = extract_author_metric(raw_output)
        assert result == {"Alice": 100}

    def test_non_numeric_values_become_zero(self):
        """Non-numeric metric values should become 0."""
        raw_output = {
            "data": [["Alice", "N/A"]],
            "columns": ["Author", "loc"],
        }
        result = extract_author_metric(raw_output)
        assert result == {"Alice": 0}

    def test_missing_data_key_returns_empty(self):
        """Missing 'data' key should return empty dict."""
        raw_output = {"columns": ["Author", "loc"]}
        result = extract_author_metric(raw_output)
        assert result == {}

    def test_multiple_authors_with_varying_types(self):
        """Should handle a mix of int, float, and string values."""
        raw_output = {
            "data": [
                ["Alice", 100],
                ["Bob", 200.7],
                ["Carol", "bad"],
            ],
            "columns": ["Author", "loc"],
        }
        result = extract_author_metric(raw_output)
        assert result == {"Alice": 100, "Bob": 200, "Carol": 0}


# =============================================================================
# get_git_info Tests
# =============================================================================


class TestGetGitInfo:
    """Test git branch and commit retrieval."""

    def test_successful_git_info(self, tmp_path: Path):
        """Should return branch and commit from successful git commands."""
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "rev-parse" in cmd and "--abbrev-ref" in cmd:
                result.stdout = "main\n"
            elif "rev-parse" in cmd:
                result.stdout = "abc123" + "0" * 34 + "\n"
            return result

        with patch("analyze.subprocess.run", side_effect=mock_run):
            branch, commit = get_git_info(tmp_path)

        assert branch == "main"
        assert commit == "abc123" + "0" * 34

    def test_branch_failure_returns_unknown(self, tmp_path: Path):
        """Failed branch detection should return 'unknown'."""
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "--abbrev-ref" in cmd:
                result.returncode = 1
                result.stdout = ""
            else:
                result.returncode = 0
                result.stdout = "a" * 40 + "\n"
            return result

        with patch("analyze.subprocess.run", side_effect=mock_run):
            branch, commit = get_git_info(tmp_path)

        assert branch == "unknown"
        assert commit == "a" * 40

    def test_commit_failure_falls_back_to_content_hash(self, tmp_path: Path):
        """Failed commit detection should fall back to content hash."""
        # Create a file so fallback_commit_hash has something to hash
        (tmp_path / "test.txt").write_text("hello")

        def mock_run(cmd, **kwargs):
            result = MagicMock()
            if "--abbrev-ref" in cmd:
                result.returncode = 0
                result.stdout = "main\n"
            else:
                result.returncode = 1
                result.stdout = ""
            return result

        with patch("analyze.subprocess.run", side_effect=mock_run):
            branch, commit = get_git_info(tmp_path)

        assert branch == "main"
        assert len(commit) == 40  # SHA1 hex digest

    def test_exception_returns_unknown_and_fallback(self, tmp_path: Path):
        """Exception during git calls should return unknown + fallback hash."""
        (tmp_path / "file.py").write_text("code")

        with patch("analyze.subprocess.run", side_effect=Exception("fail")):
            branch, commit = get_git_info(tmp_path)

        assert branch == "unknown"
        assert len(commit) == 40


# =============================================================================
# fallback_commit_hash Tests
# =============================================================================


class TestFallbackCommitHash:
    """Test deterministic content hash for non-git repos."""

    def test_deterministic_for_same_content(self, tmp_path: Path):
        """Same file content should produce same hash."""
        (tmp_path / "a.py").write_text("print('hello')")
        (tmp_path / "b.py").write_text("print('world')")

        hash1 = fallback_commit_hash(tmp_path)
        hash2 = fallback_commit_hash(tmp_path)

        assert hash1 == hash2
        assert len(hash1) == 40

    def test_different_content_produces_different_hash(self, tmp_path: Path):
        """Different content should produce different hash."""
        dir1 = tmp_path / "repo1"
        dir1.mkdir()
        (dir1 / "a.py").write_text("v1")

        dir2 = tmp_path / "repo2"
        dir2.mkdir()
        (dir2 / "a.py").write_text("v2")

        assert fallback_commit_hash(dir1) != fallback_commit_hash(dir2)

    def test_empty_directory_produces_valid_hash(self, tmp_path: Path):
        """Empty directory should produce a valid 40-char hex hash."""
        h = fallback_commit_hash(tmp_path)
        assert len(h) == 40
        assert all(c in "0123456789abcdef" for c in h)

    def test_git_directory_excluded(self, tmp_path: Path):
        """Files inside .git/ should be excluded from hash."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("repo config")
        (tmp_path / "main.py").write_text("code")

        hash_with_git = fallback_commit_hash(tmp_path)

        # Hash should be the same as if .git didn't exist
        dir2 = tmp_path / "clean"
        dir2.mkdir()
        (dir2 / "main.py").write_text("code")

        hash_without_git = fallback_commit_hash(dir2)

        assert hash_with_git == hash_without_git

    def test_file_read_error_skipped(self, tmp_path: Path):
        """Files that raise OSError on read should be skipped."""
        (tmp_path / "ok.py").write_text("good")
        # This should not crash
        h = fallback_commit_hash(tmp_path)
        assert len(h) == 40


# =============================================================================
# analyze_repo Tests
# =============================================================================


class TestAnalyzeRepo:
    """Test the analyze_repo orchestration function."""

    @pytest.fixture
    def mock_git_fame_responses(self):
        """Set up mock responses for the three git-fame runs."""
        surviving = {
            "data": [["Alice", 100, 5, 3], ["Bob", 50, 3, 2]],
            "columns": ["Author", "loc", "coms", "fils"],
        }
        insertions = {
            "data": [["Alice", 120], ["Bob", 60]],
            "columns": ["Author", "loc"],
        }
        deletions = {
            "data": [["Alice", 20], ["Bob", 10]],
            "columns": ["Author", "loc"],
        }
        return [surviving, insertions, deletions]

    def test_analyze_repo_file_output(self, tmp_path: Path, mock_git_fame_responses: list):
        """analyze_repo should write JSON to output file when path ends in .json."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        output_path = tmp_path / "output.json"

        call_count = 0

        def mock_run_git_fame(rp, by_ext=False, since=None, until=None, loc_mode="surviving"):
            nonlocal call_count
            result = mock_git_fame_responses[call_count]
            call_count += 1
            return result

        with patch("analyze.run_git_fame", side_effect=mock_run_git_fame), \
             patch("analyze.get_git_info", return_value=("main", "a" * 40)):
            result = analyze_repo(
                repo_path,
                output_path,
                run_id="test-run",
                repo_id="test-repo",
                branch="main",
                commit="a" * 40,
            )

        assert output_path.exists()
        written = json.loads(output_path.read_text())
        assert "metadata" in written
        assert "data" in written
        assert written["data"]["summary"]["author_count"] == 2

    def test_analyze_repo_directory_output(self, tmp_path: Path, mock_git_fame_responses: list):
        """analyze_repo should create run directory structure when output is directory."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        call_count = 0

        def mock_run_git_fame(rp, by_ext=False, since=None, until=None, loc_mode="surviving"):
            nonlocal call_count
            result = mock_git_fame_responses[call_count]
            call_count += 1
            return result

        with patch("analyze.run_git_fame", side_effect=mock_run_git_fame), \
             patch("analyze.get_git_info", return_value=("main", "a" * 40)):
            result = analyze_repo(
                repo_path,
                output_dir,
                run_id="run-123",
                repo_id="test-repo",
                branch="main",
                commit="a" * 40,
            )

        run_dir = output_dir / "runs" / "run-123"
        assert run_dir.exists()
        assert (run_dir / "analysis.json").exists()
        assert (run_dir / "raw_git_fame.json").exists()
        assert (run_dir / "metadata.json").exists()
        assert (output_dir / "latest").is_symlink()

    def test_analyze_repo_empty_output(self, tmp_path: Path):
        """Empty git-fame output should return empty dict."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        output_path = tmp_path / "output.json"

        with patch("analyze.run_git_fame", return_value={}), \
             patch("analyze.get_git_info", return_value=("main", "a" * 40)):
            result = analyze_repo(
                repo_path,
                output_path,
                run_id="test-run",
                repo_id="test-repo",
                branch="main",
                commit="a" * 40,
            )

        assert result == {}

    def test_analyze_repo_auto_detects_git_info(self, tmp_path: Path, mock_git_fame_responses: list):
        """When branch/commit not provided, should auto-detect from git."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        output_path = tmp_path / "output.json"

        call_count = 0

        def mock_run_git_fame(rp, by_ext=False, since=None, until=None, loc_mode="surviving"):
            nonlocal call_count
            result = mock_git_fame_responses[call_count]
            call_count += 1
            return result

        with patch("analyze.run_git_fame", side_effect=mock_run_git_fame), \
             patch("analyze.get_git_info", return_value=("develop", "b" * 40)) as mock_info:
            result = analyze_repo(
                repo_path,
                output_path,
                run_id="test-run",
                repo_id="test-repo",
            )

        mock_info.assert_called_once_with(repo_path)
        assert result["metadata"]["branch"] == "develop"
        assert result["metadata"]["commit"] == "b" * 40

    def test_analyze_repo_generates_ids_when_missing(self, tmp_path: Path, mock_git_fame_responses: list):
        """When run_id/repo_id not provided, should generate UUIDs."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        output_path = tmp_path / "output.json"

        call_count = 0

        def mock_run_git_fame(rp, by_ext=False, since=None, until=None, loc_mode="surviving"):
            nonlocal call_count
            result = mock_git_fame_responses[call_count]
            call_count += 1
            return result

        with patch("analyze.run_git_fame", side_effect=mock_run_git_fame), \
             patch("analyze.get_git_info", return_value=("main", "a" * 40)), \
             patch.dict("os.environ", {}, clear=True):
            result = analyze_repo(repo_path, output_path)

        # Should have generated a UUID for run_id and repo_id
        assert result["metadata"]["run_id"] is not None
        assert len(result["metadata"]["run_id"]) > 0

    def test_analyze_repo_replaces_existing_symlink(self, tmp_path: Path, mock_git_fame_responses: list):
        """Existing latest symlink should be replaced."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create existing latest symlink
        runs_dir = output_dir / "runs" / "old-run"
        runs_dir.mkdir(parents=True)
        latest = output_dir / "latest"
        latest.symlink_to("runs/old-run")

        call_count = 0

        def mock_run_git_fame(rp, by_ext=False, since=None, until=None, loc_mode="surviving"):
            nonlocal call_count
            result = mock_git_fame_responses[call_count]
            call_count += 1
            return result

        with patch("analyze.run_git_fame", side_effect=mock_run_git_fame), \
             patch("analyze.get_git_info", return_value=("main", "a" * 40)):
            analyze_repo(
                repo_path, output_dir,
                run_id="new-run", repo_id="test", branch="main", commit="a" * 40,
            )

        # Latest should now point to new run
        assert latest.is_symlink()
        assert "new-run" in str(latest.resolve().name) or "new-run" in str(latest.readlink())
