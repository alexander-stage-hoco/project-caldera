"""Tests for performance checks (PF-1 to PF-4)."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.checks import CheckCategory, CheckSeverity
from scripts.checks.performance import (
    check_pf1_synthetic_repo_speed,
    check_pf2_real_repo_click,
    check_pf3_real_repo_picocli,
    check_pf4_memory_usage,
    run_performance_checks,
    _run_lizard_timed,
    _get_memory_usage_mb,
)


class TestPF1SyntheticRepoSpeed:
    """Tests for PF-1: Synthetic repo speed check."""

    def test_check_metadata(self):
        """Test PF-1 check has correct metadata."""
        result = check_pf1_synthetic_repo_speed()

        assert result.check_id == "PF-1"
        assert result.name == "Synthetic repo speed"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.severity == CheckSeverity.HIGH

    def test_missing_path_fails(self, tmp_path):
        """Test PF-1 fails when path doesn't exist."""
        missing_path = tmp_path / "nonexistent"
        result = check_pf1_synthetic_repo_speed(missing_path)

        assert not result.passed
        assert "not found" in result.message

    @patch("scripts.checks.performance._run_lizard_timed")
    def test_fast_analysis_passes(self, mock_run):
        """Test PF-1 passes when analysis is fast."""
        mock_run.return_value = (0.5, None)  # 0.5 seconds, no error

        result = check_pf1_synthetic_repo_speed()

        assert result.passed or result.score > 0.8
        assert result.evidence["elapsed_seconds"] <= 2.0

    @patch("scripts.checks.performance._run_lizard_timed")
    def test_slow_analysis_fails(self, mock_run):
        """Test PF-1 fails when analysis is too slow."""
        mock_run.return_value = (10.0, None)  # 10 seconds, no error

        result = check_pf1_synthetic_repo_speed()

        assert not result.passed
        assert result.score < 1.0

    @patch("scripts.checks.performance._run_lizard_timed")
    def test_at_threshold(self, mock_run):
        """Test PF-1 at exactly threshold."""
        mock_run.return_value = (2.0, None)  # Exactly at threshold

        result = check_pf1_synthetic_repo_speed()

        # At threshold should pass (<=)
        assert result.passed
        assert result.score == 1.0

    @patch("scripts.checks.performance._run_lizard_timed")
    def test_error_handling(self, mock_run):
        """Test PF-1 handles lizard errors."""
        mock_run.return_value = (0.0, "lizard not found in PATH")

        result = check_pf1_synthetic_repo_speed()

        assert not result.passed
        assert "error" in result.evidence


class TestPF2RealRepoClick:
    """Tests for PF-2: Real repo click speed check."""

    def test_check_metadata(self):
        """Test PF-2 check has correct metadata."""
        result = check_pf2_real_repo_click()

        assert result.check_id == "PF-2"
        assert result.name == "Real repo: click"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.severity == CheckSeverity.MEDIUM

    def test_missing_path_skips(self, tmp_path):
        """Test PF-2 skips when click repo doesn't exist."""
        missing_path = tmp_path / "nonexistent" / "click"
        result = check_pf2_real_repo_click(missing_path)

        # Should pass with skip
        assert result.passed
        assert result.evidence.get("skipped", False)

    @patch("scripts.checks.performance._run_lizard_timed")
    def test_fast_analysis_passes(self, mock_run, tmp_path):
        """Test PF-2 passes when analysis is fast."""
        # Create a fake click directory
        click_dir = tmp_path / "click"
        click_dir.mkdir()

        mock_run.return_value = (2.0, None)  # 2 seconds, no error

        result = check_pf2_real_repo_click(click_dir)

        assert result.passed
        assert result.evidence["threshold_seconds"] == 5.0


class TestPF3RealRepoPicocli:
    """Tests for PF-3: Real repo picocli speed check."""

    def test_check_metadata(self):
        """Test PF-3 check has correct metadata."""
        result = check_pf3_real_repo_picocli()

        assert result.check_id == "PF-3"
        assert result.name == "Real repo: picocli"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.severity == CheckSeverity.MEDIUM

    def test_missing_path_skips(self, tmp_path):
        """Test PF-3 skips when picocli repo doesn't exist."""
        missing_path = tmp_path / "nonexistent" / "picocli"
        result = check_pf3_real_repo_picocli(missing_path)

        # Should pass with skip
        assert result.passed
        assert result.evidence.get("skipped", False)

    @patch("scripts.checks.performance._run_lizard_timed")
    def test_fast_analysis_passes(self, mock_run, tmp_path):
        """Test PF-3 passes when analysis is fast."""
        # Create a fake picocli/src directory
        picocli_dir = tmp_path / "picocli"
        picocli_dir.mkdir()
        src_dir = picocli_dir / "src"
        src_dir.mkdir()

        mock_run.return_value = (15.0, None)  # 15 seconds, no error

        result = check_pf3_real_repo_picocli(picocli_dir)

        assert result.passed
        assert result.evidence["threshold_seconds"] == 30.0


class TestPF4MemoryUsage:
    """Tests for PF-4: Memory usage check."""

    def test_check_metadata(self, sample_analysis):
        """Test PF-4 check has correct metadata."""
        result = check_pf4_memory_usage(sample_analysis)

        assert result.check_id == "PF-4"
        assert result.name == "Memory usage"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.severity == CheckSeverity.LOW

    def test_with_sample_analysis(self, sample_analysis):
        """Test PF-4 with sample analysis data."""
        result = check_pf4_memory_usage(sample_analysis)

        # Check has expected structure
        assert result.check_id == "PF-4"
        # Memory may not be measurable on all systems
        if not result.evidence.get("skipped", False):
            assert "memory_mb" in result.evidence
            assert "threshold_mb" in result.evidence
            assert result.evidence["threshold_mb"] == 500.0

    @patch("scripts.checks.performance._get_memory_usage_mb")
    def test_low_memory_passes(self, mock_mem, sample_analysis):
        """Test PF-4 passes with low memory usage."""
        mock_mem.return_value = 100.0  # 100MB

        result = check_pf4_memory_usage(sample_analysis)

        assert result.passed
        assert result.evidence["memory_mb"] == 100.0

    @patch("scripts.checks.performance._get_memory_usage_mb")
    def test_high_memory_fails(self, mock_mem, sample_analysis):
        """Test PF-4 fails with high memory usage."""
        # 800MB gives score of 500/800 = 0.625 which is < 0.8 threshold
        mock_mem.return_value = 800.0

        result = check_pf4_memory_usage(sample_analysis)

        assert not result.passed
        assert result.score < 0.8

    @patch("scripts.checks.performance._get_memory_usage_mb")
    def test_unmeasurable_memory_skips(self, mock_mem, sample_analysis):
        """Test PF-4 skips when memory can't be measured."""
        mock_mem.return_value = None

        result = check_pf4_memory_usage(sample_analysis)

        # Should pass with skip when unable to measure
        assert result.passed
        assert result.evidence.get("skipped", False)


class TestRunPerformanceChecks:
    """Tests for running all performance checks."""

    def test_returns_list(self, sample_analysis):
        """Test that run_performance_checks returns a list."""
        results = run_performance_checks(sample_analysis)

        assert isinstance(results, list)

    def test_runs_all_four_checks(self, sample_analysis):
        """Test that all 4 performance checks are run."""
        results = run_performance_checks(sample_analysis)

        assert len(results) == 4
        check_ids = [r.check_id for r in results]
        assert "PF-1" in check_ids
        assert "PF-2" in check_ids
        assert "PF-3" in check_ids
        assert "PF-4" in check_ids

    def test_all_checks_have_performance_category(self, sample_analysis):
        """Test that all checks are categorized as PERFORMANCE."""
        results = run_performance_checks(sample_analysis)

        for result in results:
            assert result.category == CheckCategory.PERFORMANCE

    def test_with_custom_path(self, sample_analysis, tmp_path):
        """Test run_performance_checks with custom eval_repos_path."""
        results = run_performance_checks(sample_analysis, eval_repos_path=tmp_path)

        # Should still return 4 checks
        assert len(results) == 4


class TestRunLizardTimed:
    """Tests for the _run_lizard_timed helper function."""

    def test_with_nonexistent_path(self, tmp_path):
        """Test timing with nonexistent path."""
        # This will likely fail but we're testing the function works
        elapsed, error = _run_lizard_timed(tmp_path / "nonexistent")

        # Should return an error since path doesn't exist
        # (actual behavior depends on lizard's handling of missing paths)
        assert isinstance(elapsed, float)
        assert error is None or isinstance(error, str)

    def test_returns_tuple(self, tmp_path):
        """Test that _run_lizard_timed returns a tuple."""
        result = _run_lizard_timed(tmp_path)

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestGetMemoryUsageMB:
    """Tests for the _get_memory_usage_mb helper function."""

    def test_returns_float_or_none(self):
        """Test that _get_memory_usage_mb returns float or None."""
        result = _get_memory_usage_mb()

        assert result is None or isinstance(result, float)

    def test_non_negative_if_measurable(self):
        """Test that memory usage is non-negative if measurable."""
        result = _get_memory_usage_mb()

        if result is not None:
            assert result >= 0
