"""Additional unit tests for check classes targeting remaining uncovered branches.

Covers edge cases in reliability, performance, integration_fit, and
authorship_accuracy that were not covered by the primary test file.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from checks.reliability import ReliabilityChecks
from checks.performance import PerformanceChecks
from checks.integration_fit import IntegrationFitChecks
from checks.authorship_accuracy import AuthorshipAccuracyChecks
from checks.output_quality import OutputQualityChecks


def _make_envelope(
    authors: list[dict] | None = None,
    summary: dict | None = None,
    files: list[dict] | None = None,
) -> dict:
    """Create a standard Caldera envelope analysis dict."""
    if authors is None:
        authors = [
            {"name": "Alice", "surviving_loc": 700, "ownership_pct": 70.0},
            {"name": "Bob", "surviving_loc": 300, "ownership_pct": 30.0},
        ]
    if summary is None:
        summary = {
            "author_count": len(authors),
            "total_loc": sum(a.get("surviving_loc", 0) for a in authors),
            "hhi_index": 0.58,
            "bus_factor": 1,
            "top_author_pct": 70.0,
            "top_two_pct": 100.0,
        }
    data: dict = {
        "tool": "git-fame",
        "tool_version": "3.1.1",
        "summary": summary,
        "authors": authors,
    }
    if files is not None:
        data["files"] = files
    return {
        "metadata": {
            "tool_name": "git-fame",
            "tool_version": "3.1.1",
            "run_id": "test-run",
            "repo_id": "test-repo",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2026-02-14T12:00:00+00:00",
            "schema_version": "1.0.0",
        },
        "data": data,
    }


def _write_combined(output_dir: Path, analyses: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "combined_analysis.json").write_text(json.dumps(analyses, indent=2))
    return output_dir


# =============================================================================
# ReliabilityChecks - additional branch coverage
# =============================================================================


class TestReliabilityAdditional:
    """Cover remaining branches in ReliabilityChecks."""

    def test_rl1_uses_non_synthetic_repos(self, tmp_path: Path):
        """RL-1 should find repos at eval_repos root when synthetic dir missing."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        # No synthetic dir - place repo directly
        repo = eval_repos / "direct-repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        output = json.dumps({"data": [["Alice", 100]], "columns": ["Author", "loc"]})
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = output
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", eval_repos)
            results = checker.run_all()

        rl1 = next(r for r in results if r["check"] == "RL-1")
        assert rl1["passed"]

    def test_rl1_synthetic_dir_is_git_repo(self, tmp_path: Path):
        """RL-1 should use synthetic dir itself if it's a .git repo."""
        eval_repos = tmp_path / "eval-repos"
        synthetic = eval_repos / "synthetic"
        synthetic.mkdir(parents=True)
        (synthetic / ".git").mkdir()

        output = json.dumps({"data": [["Alice", 100]], "columns": ["Author", "loc"]})
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = output
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", eval_repos)
            results = checker.run_all()

        rl1 = next(r for r in results if r["check"] == "RL-1")
        assert rl1["passed"]

    def test_rl1_synthetic_dir_empty_no_git(self, tmp_path: Path):
        """RL-1 should fail when synthetic dir exists but has no git repos."""
        eval_repos = tmp_path / "eval-repos"
        synthetic = eval_repos / "synthetic"
        synthetic.mkdir(parents=True)
        # synthetic exists but has no .git subdirs

        checker = ReliabilityChecks(tmp_path / "out", eval_repos)
        results = checker.run_all()
        rl1 = next(r for r in results if r["check"] == "RL-1")
        assert not rl1["passed"]

    def test_rl1_run_fails(self, tmp_path: Path):
        """RL-1 should fail when git-fame returns non-zero."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal error"
        mock_result.stdout = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl1 = next(r for r in results if r["check"] == "RL-1")
        assert not rl1["passed"]
        assert "failed" in rl1["message"].lower()

    def test_rl1_non_deterministic(self, tmp_path: Path):
        """RL-1 should fail when two runs produce different output."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        call_count = 0

        def mock_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            if call_count == 1:
                result.stdout = json.dumps({"data": [["Alice", 100]], "columns": ["Author", "loc"]})
            else:
                result.stdout = json.dumps({"data": [["Alice", 200]], "columns": ["Author", "loc"]})
            return result

        with patch("checks.reliability.subprocess.run", side_effect=mock_run):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl1 = next(r for r in results if r["check"] == "RL-1")
        assert not rl1["passed"]

    def test_rl2_empty_repo_nonzero_with_informative_message(self, tmp_path: Path):
        """RL-2 should pass when empty repo returns non-zero with informative stderr."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "empty"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "no commits found in empty repository"

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl2 = next(r for r in results if r["check"] == "RL-2")
        assert rl2["passed"]

    def test_rl2_empty_repo_nonzero_unhelpful_stderr(self, tmp_path: Path):
        """RL-2 should fail when empty repo returns non-zero with unhelpful stderr."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "empty"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "segfault: core dumped"

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl2 = next(r for r in results if r["check"] == "RL-2")
        assert not rl2["passed"]

    def test_rl2_empty_repo_with_data(self, tmp_path: Path):
        """RL-2 should pass when empty repo returns data (non-empty but still handled)."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "empty"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "data": [["Ghost", 10]],
            "columns": ["Author", "loc"],
        })
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl2 = next(r for r in results if r["check"] == "RL-2")
        assert rl2["passed"]

    def test_rl3_checks_analysis_data_for_single_author(self, tmp_path: Path):
        """RL-3 should check analysis data for single-author repos."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        (eval_repos / "synthetic").mkdir()

        # Create analysis data that matches single-author
        analysis = _make_envelope(
            authors=[{"name": "Alice", "surviving_loc": 500, "ownership_pct": 100.0}],
            summary={"author_count": 1, "total_loc": 500, "hhi_index": 1.0, "bus_factor": 1, "top_author_pct": 100.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"single-author-test": analysis})

        checker = ReliabilityChecks(output_dir, eval_repos)
        results = checker.run_all()
        rl3 = next(r for r in results if r["check"] == "RL-3")
        # Should use analysis data fallback with "single" in repo name
        assert rl3["passed"]

    def test_rl3_fails_on_command_error(self, tmp_path: Path):
        """RL-3 should fail when git-fame command fails on single-author repo."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "single-author"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal error"
        mock_result.stdout = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl3 = next(r for r in results if r["check"] == "RL-3")
        assert not rl3["passed"]

    def test_rl4_fails_on_command_error(self, tmp_path: Path):
        """RL-4 should fail when git-fame command fails on rename repo."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "rename-test"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal error"
        mock_result.stdout = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl4 = next(r for r in results if r["check"] == "RL-4")
        assert not rl4["passed"]

    def test_rl4_fails_empty_data_from_rename_repo(self, tmp_path: Path):
        """RL-4 should fail when rename repo returns no data."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "rename-test"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"data": [], "columns": []})
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", tmp_path / "eval-repos")
            results = checker.run_all()

        rl4 = next(r for r in results if r["check"] == "RL-4")
        assert not rl4["passed"]

    def test_run_git_fame_handles_timeout(self, tmp_path: Path):
        """_run_git_fame should handle timeout."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        with patch("checks.reliability.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(cmd="test", timeout=60)):
            checker = ReliabilityChecks(tmp_path / "out", eval_repos)
            output, rc, stderr = checker._run_git_fame(tmp_path)

        assert output == {}
        assert rc == -1
        assert "Timeout" in stderr

    def test_run_git_fame_handles_file_not_found(self, tmp_path: Path):
        """_run_git_fame should handle FileNotFoundError."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        with patch("checks.reliability.subprocess.run", side_effect=FileNotFoundError):
            checker = ReliabilityChecks(tmp_path / "out", eval_repos)
            output, rc, stderr = checker._run_git_fame(tmp_path)

        assert output == {}
        assert rc == -1

    def test_run_git_fame_handles_json_parse_error(self, tmp_path: Path):
        """_run_git_fame should handle invalid JSON output."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not json {{"
        mock_result.stderr = ""

        with patch("checks.reliability.subprocess.run", return_value=mock_result):
            checker = ReliabilityChecks(tmp_path / "out", eval_repos)
            output, rc, stderr = checker._run_git_fame(tmp_path)

        assert output == {}
        assert "JSON parse error" in stderr


# =============================================================================
# PerformanceChecks - additional branch coverage
# =============================================================================


class TestPerformanceAdditional:
    """Cover remaining branches in PerformanceChecks."""

    def test_pf1_nonzero_but_fast(self, tmp_path: Path):
        """PF-1 should pass when returncode != 0 but within time threshold."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = lambda rp, timeout=120: (2.0, 1, "warning")

        result = checker._check_small_repo_speed()
        assert result["passed"]

    def test_pf1_execution_failed(self, tmp_path: Path):
        """PF-1 should fail when execution returns -1."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = lambda rp, timeout=120: (0.0, -1, "git-fame not found")

        result = checker._check_small_repo_speed()
        assert not result["passed"]

    def test_pf2_skips_no_repos(self, tmp_path: Path):
        """PF-2 should skip (pass) when no repos available."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        checker = PerformanceChecks(tmp_path / "output", eval_repos)
        result = checker._check_medium_repo_speed()
        assert result["passed"]
        assert "skipped" in result["message"].lower()

    def test_pf2_fails_execution_error(self, tmp_path: Path):
        """PF-2 should fail when execution returns -1."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = lambda rp, timeout=120: (0.0, -1, "not found")

        result = checker._check_medium_repo_speed()
        assert not result["passed"]

    def test_pf2_fails_too_slow(self, tmp_path: Path):
        """PF-2 should fail when execution exceeds threshold."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = lambda rp, timeout=120: (35.0, 0, "")

        result = checker._check_medium_repo_speed()
        assert not result["passed"]

    def test_pf3_fails_high_memory(self, tmp_path: Path):
        """PF-3 should fail when memory usage exceeds threshold."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": []}'
        mock_result.stderr = ""

        mock_usage = MagicMock()
        mock_usage.ru_maxrss = 600 * 1024 * 1024  # 600MB in bytes (Darwin)

        with patch("checks.performance.subprocess.run", return_value=mock_result), \
             patch("checks.performance.resource.getrusage", return_value=mock_usage), \
             patch("platform.system", return_value="Darwin"):
            checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
            result = checker._check_memory_usage()

        assert not result["passed"]

    def test_pf4_fails_degradation(self, tmp_path: Path):
        """PF-4 should fail when second run is much slower."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        run_count = 0

        def mock_timed(repo_path, timeout=120):
            nonlocal run_count
            run_count += 1
            if run_count == 1:
                return (1.0, 0, "")
            else:
                return (3.0, 0, "")  # 200% slower and > 2s

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = mock_timed

        result = checker._check_incremental_speed()
        assert not result["passed"]

    def test_pf4_skips_no_repo(self, tmp_path: Path):
        """PF-4 should skip when no test repo available."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        checker = PerformanceChecks(tmp_path / "output", eval_repos)
        result = checker._check_incremental_speed()
        assert result["passed"]
        assert "skipped" in result["message"].lower()

    def test_pf4_fails_run_error(self, tmp_path: Path):
        """PF-4 should fail when a run errors."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = lambda rp, timeout=120: (0.0, -1, "fail")

        result = checker._check_incremental_speed()
        assert not result["passed"]

    def test_pf4_reports_improvement(self, tmp_path: Path):
        """PF-4 should report improvement when second run is faster."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        run_count = 0

        def mock_timed(repo_path, timeout=120):
            nonlocal run_count
            run_count += 1
            if run_count == 1:
                return (2.0, 0, "")
            else:
                return (1.0, 0, "")  # Faster

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = mock_timed

        result = checker._check_incremental_speed()
        assert result["passed"]
        assert "faster" in result["message"].lower()

    def test_pf4_handles_zero_first_run(self, tmp_path: Path):
        """PF-4 should handle zero-time first run gracefully."""
        eval_repos = tmp_path / "eval-repos" / "synthetic" / "repo"
        eval_repos.mkdir(parents=True)
        (eval_repos / ".git").mkdir()

        run_count = 0

        def mock_timed(repo_path, timeout=120):
            nonlocal run_count
            run_count += 1
            return (0.0, 0, "")

        checker = PerformanceChecks(tmp_path / "output", tmp_path / "eval-repos")
        checker._run_git_fame_timed = mock_timed

        result = checker._check_incremental_speed()
        assert result["passed"]

    def test_run_git_fame_timed_handles_timeout(self, tmp_path: Path):
        """_run_git_fame_timed should return timeout value on timeout."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        with patch("checks.performance.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(cmd="test", timeout=60)):
            checker = PerformanceChecks(tmp_path / "output", eval_repos)
            elapsed, rc, stderr = checker._run_git_fame_timed(tmp_path, timeout=60)

        assert elapsed == 60
        assert rc == -1

    def test_run_git_fame_timed_handles_file_not_found(self, tmp_path: Path):
        """_run_git_fame_timed should handle FileNotFoundError."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()

        with patch("checks.performance.subprocess.run", side_effect=FileNotFoundError):
            checker = PerformanceChecks(tmp_path / "output", eval_repos)
            elapsed, rc, stderr = checker._run_git_fame_timed(tmp_path)

        assert rc == -1

    def test_find_test_repo_checks_real_dir(self, tmp_path: Path):
        """_find_test_repo should check real dir when synthetic has no repos."""
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        (eval_repos / "synthetic").mkdir()
        real_repo = eval_repos / "real" / "my-project"
        real_repo.mkdir(parents=True)
        (real_repo / ".git").mkdir()

        checker = PerformanceChecks(tmp_path / "output", eval_repos)
        found = checker._find_test_repo()
        assert found is not None


# =============================================================================
# IntegrationFitChecks - additional branch coverage
# =============================================================================


class TestIntegrationFitAdditional:
    """Cover remaining branches in IntegrationFitChecks."""

    def test_if4_validates_legacy_format(self, tmp_path: Path):
        """IF-4 should validate legacy format (no metadata/data envelope)."""
        legacy_data = {
            "schema_version": "1.0.0",
            "generated_at": "2026-02-14T12:00:00Z",
            "repo_name": "test",
            "results": {
                "tool": "git-fame",
                "summary": {"author_count": 1},
                "authors": [{"name": "Alice"}],
            },
        }
        output_dir = _write_combined(tmp_path / "out", {"test-repo": legacy_data})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if4 = next(r for r in results if r["check"] == "IF-4")
        assert if4["passed"]

    def test_if4_fails_missing_legacy_fields(self, tmp_path: Path):
        """IF-4 should fail for legacy format missing required fields."""
        legacy_data = {
            "repo_name": "test",
            # missing schema_version, generated_at, results
        }
        output_dir = _write_combined(tmp_path / "out", {"test-repo": legacy_data})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if4 = next(r for r in results if r["check"] == "IF-4")
        assert not if4["passed"]

    def test_if4_fails_type_error_authors_not_list(self, tmp_path: Path):
        """IF-4 should fail when authors is not a list."""
        analysis = _make_envelope()
        analysis["data"]["authors"] = "not a list"
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if4 = next(r for r in results if r["check"] == "IF-4")
        assert not if4["passed"]

    def test_if3_passes_with_directory_data(self, tmp_path: Path):
        """IF-3 should pass when directory data is present."""
        analysis = _make_envelope()
        analysis["data"]["directories"] = [{"path": "src/", "author_count": 2}]
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if3 = next(r for r in results if r["check"] == "IF-3")
        assert if3["passed"]
        assert "directories" in if3["message"].lower()

    def test_if1_fails_empty_path(self, tmp_path: Path):
        """IF-1 should fail when a file path is empty."""
        analysis = _make_envelope(files=[{"path": "", "author": "Alice", "loc": 100}])
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = IntegrationFitChecks(output_dir)
        results = checker.run_all()
        if1 = next(r for r in results if r["check"] == "IF-1")
        assert not if1["passed"]


# =============================================================================
# AuthorshipAccuracyChecks - additional branch coverage
# =============================================================================


class TestAuthorshipAccuracyAdditional:
    """Cover remaining branches in AuthorshipAccuracyChecks."""

    def test_aa3_no_authors_found(self, tmp_path: Path):
        """AA-3 should fail when analysis has no authors but ground truth expects top author."""
        analysis = _make_envelope(
            authors=[],
            summary={"author_count": 0, "total_loc": 0, "hhi_index": 0.0, "bus_factor": 0, "top_author_pct": 0.0, "top_two_pct": 0.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})

        gt = {
            "test-repo": {
                "expected_top_author_loc": 500,
            }
        }
        gt_file = tmp_path / "gt.json"
        gt_file.write_text(json.dumps(gt))

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa3 = next(r for r in results if r["check"] == "AA-3")
        assert not aa3["passed"]

    def test_aa3_top_author_below_threshold(self, tmp_path: Path):
        """AA-3 should fail when top author LOC is below 90% of expected."""
        analysis = _make_envelope(
            authors=[{"name": "Alice", "surviving_loc": 100, "ownership_pct": 100.0}],
            summary={"author_count": 1, "total_loc": 100, "hhi_index": 1.0, "bus_factor": 1, "top_author_pct": 100.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})

        gt = {
            "test-repo": {
                "expected_top_author_loc": 500,  # 90% = 450, actual = 100 -> fail
            }
        }
        gt_file = tmp_path / "gt.json"
        gt_file.write_text(json.dumps(gt))

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa3 = next(r for r in results if r["check"] == "AA-3")
        assert not aa3["passed"]

    def test_aa4_author_not_found(self, tmp_path: Path):
        """AA-4 should report author not found when expected author missing from output."""
        analysis = _make_envelope(
            authors=[{"name": "Alice", "surviving_loc": 1000, "ownership_pct": 100.0}],
            summary={"author_count": 1, "total_loc": 1000, "hhi_index": 1.0, "bus_factor": 1, "top_author_pct": 100.0, "top_two_pct": 100.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"test-repo": analysis})

        gt = {
            "test-repo": {
                "expected_authors": {"Alice": 100.0, "Bob": 0.0},
            }
        }
        gt_file = tmp_path / "gt.json"
        gt_file.write_text(json.dumps(gt))

        checker = AuthorshipAccuracyChecks(output_dir, gt_file)
        results = checker.run_all()
        aa4 = next(r for r in results if r["check"] == "AA-4")
        assert not aa4["passed"]
        assert "not found" in aa4["message"]

    def test_aa8_files_with_missing_attribution(self, tmp_path: Path):
        """AA-8 should fail when files are present but lack author attribution."""
        analysis = _make_envelope(
            files=[
                {"path": "a.py", "author": "Alice", "loc": 100},
                {"path": "b.py", "loc": 50},  # missing author
            ]
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = AuthorshipAccuracyChecks(output_dir, tmp_path / "nonexistent.json")
        results = checker.run_all()
        aa8 = next(r for r in results if r["check"] == "AA-8")
        assert not aa8["passed"]

    def test_aa8_files_all_attributed(self, tmp_path: Path):
        """AA-8 should pass when all files have author attribution."""
        analysis = _make_envelope(
            files=[
                {"path": "a.py", "author": "Alice", "loc": 100},
                {"path": "b.py", "author": "Bob", "loc": 50},
            ]
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = AuthorshipAccuracyChecks(output_dir, tmp_path / "nonexistent.json")
        results = checker.run_all()
        aa8 = next(r for r in results if r["check"] == "AA-8")
        assert aa8["passed"]

    def test_aa8_no_authors_no_files(self, tmp_path: Path):
        """AA-8 should fail when neither files nor authors exist."""
        analysis = _make_envelope(
            authors=[],
            summary={"author_count": 0, "total_loc": 0, "hhi_index": 0.0, "bus_factor": 0, "top_author_pct": 0.0, "top_two_pct": 0.0}
        )
        output_dir = _write_combined(tmp_path / "out", {"repo": analysis})

        checker = AuthorshipAccuracyChecks(output_dir, tmp_path / "nonexistent.json")
        results = checker.run_all()
        aa8 = next(r for r in results if r["check"] == "AA-8")
        assert not aa8["passed"]


# =============================================================================
# OutputQualityChecks - legacy format coverage
# =============================================================================


class TestOutputQualityLegacyFormat:
    """Cover legacy format branches in OutputQualityChecks."""

    def test_oq1_legacy_format_schema_version(self, tmp_path: Path):
        """OQ-1 should find schema_version in legacy top-level format."""
        legacy = {
            "schema_version": "1.0.0",
            "generated_at": "2026-02-14T12:00:00+00:00",
            "repo_name": "test",
            "results": {
                "tool": "git-fame",
                "summary": {"author_count": 1, "total_loc": 100, "hhi_index": 1.0, "bus_factor": 1, "top_author_pct": 100.0},
                "authors": [{"name": "Alice", "surviving_loc": 100, "ownership_pct": 100.0}],
            },
        }
        output_dir = _write_combined(tmp_path / "out", {"repo": legacy})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq1 = next(r for r in results if r["check"] == "OQ-1")
        assert oq1["passed"]

    def test_oq2_legacy_format_timestamp(self, tmp_path: Path):
        """OQ-2 should find generated_at in legacy format."""
        legacy = {
            "schema_version": "1.0.0",
            "generated_at": "2026-02-14T12:00:00+00:00",
            "repo_name": "test",
            "results": {
                "tool": "git-fame",
                "summary": {"author_count": 1, "total_loc": 100, "hhi_index": 1.0, "bus_factor": 1, "top_author_pct": 100.0},
                "authors": [{"name": "Alice", "surviving_loc": 100, "ownership_pct": 100.0}],
            },
        }
        output_dir = _write_combined(tmp_path / "out", {"repo": legacy})

        checker = OutputQualityChecks(output_dir)
        results = checker.run_all()
        oq2 = next(r for r in results if r["check"] == "OQ-2")
        assert oq2["passed"]
