"""Extended unit tests for scripts.analyze — covering identify_lfs_candidates,
get_binary_version, and run_git_sizer."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.analyze import (
    ThresholdViolation,
    RepositoryMetrics,
    RepositoryAnalysis,
    calculate_health_grade,
    calculate_threshold_level,
    format_bytes,
    get_binary_version,
    identify_lfs_candidates,
    run_git_sizer,
    build_analysis_data,
)


# ---------------------------------------------------------------------------
# get_binary_version
# ---------------------------------------------------------------------------

class TestGetBinaryVersion:
    @patch("scripts.analyze.get_binary_version_raw", return_value="git-sizer release 1.5.0")
    def test_extracts_semver(self, mock_raw):
        assert get_binary_version() == "1.5.0"

    @patch("scripts.analyze.get_binary_version_raw", return_value="1.5.0")
    def test_extracts_bare_semver(self, mock_raw):
        assert get_binary_version() == "1.5.0"

    @patch("scripts.analyze.get_binary_version_raw", return_value="unknown")
    def test_returns_raw_when_no_semver(self, mock_raw):
        assert get_binary_version() == "unknown"

    @patch("scripts.analyze.get_binary_version_raw", return_value="not installed")
    def test_returns_raw_when_not_installed(self, mock_raw):
        assert get_binary_version() == "not installed"


# ---------------------------------------------------------------------------
# identify_lfs_candidates
# ---------------------------------------------------------------------------

class TestIdentifyLFSCandidates:
    def test_no_candidates_below_threshold(self):
        raw = {"max_blob_size": 500}
        assert identify_lfs_candidates(raw) == []

    def test_no_candidates_at_threshold(self):
        raw = {"max_blob_size": 1024 * 1024}
        # No blob ref provided, so no candidate path extracted
        assert identify_lfs_candidates(raw) == []

    def test_identifies_candidate_with_ref(self):
        raw = {
            "max_blob_size": 10 * 1024 * 1024,
            "max_blob_size_blob": "refs/heads/main:assets/large-model.bin)",
        }
        candidates = identify_lfs_candidates(raw)
        assert len(candidates) == 1
        assert "assets/large-model.bin" in candidates[0]

    def test_ref_without_colon(self):
        raw = {
            "max_blob_size": 10 * 1024 * 1024,
            "max_blob_size_blob": "abc123",
        }
        candidates = identify_lfs_candidates(raw)
        assert candidates == []

    def test_custom_threshold(self):
        raw = {"max_blob_size": 500, "max_blob_size_blob": "ref:path/file.dat)"}
        # Default threshold 1 MiB -> no candidate
        assert identify_lfs_candidates(raw) == []
        # Lower threshold -> detected
        assert len(identify_lfs_candidates(raw, threshold_bytes=100)) == 1

    def test_empty_raw_output(self):
        assert identify_lfs_candidates({}) == []

    def test_empty_blob_ref(self):
        raw = {"max_blob_size": 2 * 1024 * 1024, "max_blob_size_blob": ""}
        assert identify_lfs_candidates(raw) == []


# ---------------------------------------------------------------------------
# run_git_sizer
# ---------------------------------------------------------------------------

class TestRunGitSizer:
    @patch("scripts.analyze.ensure_binary")
    @patch("subprocess.run")
    def test_successful_run(self, mock_run, mock_ensure):
        mock_ensure.return_value = Path("/bin/git-sizer")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"unique_commit_count": 42})
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        output, duration = run_git_sizer(Path("/tmp/repo"))
        assert output["unique_commit_count"] == 42
        assert isinstance(duration, int)
        assert duration >= 0

    @patch("scripts.analyze.ensure_binary")
    @patch("subprocess.run")
    def test_failure_raises(self, mock_run, mock_ensure):
        mock_ensure.return_value = Path("/bin/git-sizer")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repo"
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="git-sizer failed"):
            run_git_sizer(Path("/tmp/bad"))

    @patch("scripts.analyze.ensure_binary")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git-sizer", timeout=300))
    def test_timeout_raises(self, mock_run, mock_ensure):
        mock_ensure.return_value = Path("/bin/git-sizer")
        with pytest.raises(RuntimeError, match="timed out"):
            run_git_sizer(Path("/tmp/slow"))

    @patch("scripts.analyze.ensure_binary")
    @patch("subprocess.run")
    def test_nonzero_return_with_stdout_succeeds(self, mock_run, mock_ensure):
        """git-sizer returns nonzero when violations detected but still provides output."""
        mock_ensure.return_value = Path("/bin/git-sizer")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = json.dumps({"unique_commit_count": 10})
        mock_result.stderr = "warnings"
        mock_run.return_value = mock_result

        output, duration = run_git_sizer(Path("/tmp/repo"))
        assert output["unique_commit_count"] == 10


# ---------------------------------------------------------------------------
# calculate_threshold_level — additional edge cases
# ---------------------------------------------------------------------------

class TestCalculateThresholdLevelExtended:
    def test_commit_count_levels(self):
        assert calculate_threshold_level("commit_count", 5000) == 0
        assert calculate_threshold_level("commit_count", 10000) == 1
        assert calculate_threshold_level("commit_count", 50000) == 2
        assert calculate_threshold_level("commit_count", 200000) == 3
        assert calculate_threshold_level("commit_count", 1000000) == 4

    def test_blob_total_size_levels(self):
        assert calculate_threshold_level("blob_total_size", 50 * 1024 * 1024) == 0
        assert calculate_threshold_level("blob_total_size", 100 * 1024 * 1024) == 1
        assert calculate_threshold_level("blob_total_size", 500 * 1024 * 1024) == 2
        assert calculate_threshold_level("blob_total_size", 1024 * 1024 * 1024) == 3
        assert calculate_threshold_level("blob_total_size", 5 * 1024 * 1024 * 1024) == 4

    def test_max_tree_entries_levels(self):
        assert calculate_threshold_level("max_tree_entries", 500) == 0
        assert calculate_threshold_level("max_tree_entries", 1000) == 1
        assert calculate_threshold_level("max_tree_entries", 5000) == 2
        assert calculate_threshold_level("max_tree_entries", 10000) == 3
        assert calculate_threshold_level("max_tree_entries", 50000) == 4

    def test_max_history_depth_levels(self):
        assert calculate_threshold_level("max_history_depth", 5000) == 0
        assert calculate_threshold_level("max_history_depth", 10000) == 1
        assert calculate_threshold_level("max_history_depth", 500000) == 4

    def test_expanded_blob_count_levels(self):
        assert calculate_threshold_level("expanded_blob_count", 5000) == 0
        assert calculate_threshold_level("expanded_blob_count", 10000) == 1
        assert calculate_threshold_level("expanded_blob_count", 500000) == 4

    def test_zero_value(self):
        assert calculate_threshold_level("max_blob_size", 0) == 0
        assert calculate_threshold_level("commit_count", 0) == 0


# ---------------------------------------------------------------------------
# calculate_health_grade — additional edges
# ---------------------------------------------------------------------------

class TestCalculateHealthGradeExtended:
    def test_many_level_2_violations_gives_c(self):
        violations = [ThresholdViolation("m", "", 0, 2) for _ in range(4)]
        assert calculate_health_grade(violations) == "C"

    def test_few_level_2_violations_gives_c_plus(self):
        violations = [ThresholdViolation("m", "", 0, 2) for _ in range(3)]
        assert calculate_health_grade(violations) == "C+"

    def test_many_level_1_violations_gives_b(self):
        violations = [ThresholdViolation("m", "", 0, 1) for _ in range(6)]
        assert calculate_health_grade(violations) == "B"

    def test_few_level_1_violations_gives_b_plus(self):
        violations = [ThresholdViolation("m", "", 0, 1) for _ in range(5)]
        assert calculate_health_grade(violations) == "B+"


# ---------------------------------------------------------------------------
# build_analysis_data
# ---------------------------------------------------------------------------

class TestBuildAnalysisDataExtended:
    def test_includes_lfs_candidates(self):
        metrics = RepositoryMetrics()
        analysis = RepositoryAnalysis(
            git_sizer_version="1.5.0",
            duration_ms=200,
            metrics=metrics,
            health_grade="A",
            violations=[],
            lfs_candidates=["big.bin", "model.h5"],
            raw_output={"key": "val"},
        )
        data = build_analysis_data(analysis, "my-repo")
        assert data["lfs_candidates"] == ["big.bin", "model.h5"]
        assert data["tool"] == "git-sizer"
        assert data["repo_name"] == "my-repo"
        assert data["raw_output"] == {"key": "val"}

    def test_violations_serialized(self):
        v = ThresholdViolation("max_blob_size", "10.0 MiB", 10485760, 2, "ref:path")
        metrics = RepositoryMetrics()
        analysis = RepositoryAnalysis(
            git_sizer_version="1.5.0",
            duration_ms=100,
            metrics=metrics,
            violations=[v],
        )
        data = build_analysis_data(analysis, "r1")
        assert len(data["violations"]) == 1
        assert data["violations"][0]["metric"] == "max_blob_size"
