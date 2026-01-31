"""Tests for layout-scanner performance checks (PF-1 to PF-5).

Tests the performance checks including PF-5 (deep nesting performance validation).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckCategory, CheckResult
from checks.performance import (
    check_deep_nesting_performance,
    check_files_per_second,
    check_small_repo_speed,
    check_medium_repo_speed,
    check_large_repo_speed,
    run_performance_checks,
    DEEP_NESTING_THRESHOLDS,
)


class TestPF5DeepNestingPerformance:
    """Tests for PF-5: Deep nesting performance validation."""

    def test_pf5_passes_for_shallow_directory(self):
        """PF-5 should pass for repos with shallow nesting (<10 levels)."""
        output = {
            "statistics": {
                "scan_duration_ms": 100,
                "max_directory_depth": 5,
                "total_files": 100,
                "total_directories": 20,
            },
            "files": [],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.passed is True
        assert "not a deep nesting scenario" in result.message.lower()

    def test_pf5_passes_for_efficient_deep_nesting(self):
        """PF-5 should pass when deep nesting is handled efficiently."""
        output = {
            "statistics": {
                "scan_duration_ms": 500,
                "max_directory_depth": 25,
                "total_files": 1000,
                "total_directories": 200,
            },
            "files": [],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        assert result.passed is True
        assert "efficient" in result.message.lower()

    def test_pf5_fails_on_timeout(self):
        """PF-5 should fail when scan exceeds timeout threshold."""
        output = {
            "statistics": {
                "scan_duration_ms": 10000,  # Exceeds 5000ms threshold
                "max_directory_depth": 25,
                "total_files": 100,
                "total_directories": 50,
            },
            "files": [],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        assert result.passed is False
        assert "exceeds" in result.message.lower()
        assert result.evidence.get("timeout_threshold_ms") == DEEP_NESTING_THRESHOLDS["timeout_ms"]

    def test_pf5_fails_on_nonlinear_scaling(self):
        """PF-5 should fail when performance indicates non-linear scaling."""
        output = {
            "statistics": {
                "scan_duration_ms": 5000,  # 5ms per item - too slow
                "max_directory_depth": 20,
                "total_files": 500,
                "total_directories": 500,
            },
            "files": [],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        assert result.passed is False
        assert "non-linear" in result.message.lower() or "scaling" in result.message.lower()

    def test_pf5_infers_depth_from_file_paths(self):
        """PF-5 should infer depth from file paths if not in statistics."""
        output = {
            "statistics": {
                "scan_duration_ms": 100,
                "total_files": 50,
                "total_directories": 25,
                # max_directory_depth not provided
            },
            "files": [
                {"path": "a/b/c/d/e/f/g/h/i/j/k/file.txt"},  # 11 levels deep
            ],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        # Should detect deep nesting from file paths
        assert result.evidence.get("max_depth", 0) >= 10

    def test_pf5_respects_ground_truth_thresholds(self):
        """PF-5 should use ground truth thresholds when provided."""
        output = {
            "statistics": {
                "scan_duration_ms": 8000,  # Would fail default threshold
                "max_directory_depth": 30,
                "total_files": 1000,
                "total_directories": 200,
            },
            "files": [],
        }
        ground_truth = {
            "thresholds": {
                "deep_nesting_timeout_ms": 10000,  # Custom higher threshold
                "deep_nesting_max_ms_per_item": 8.0,
            },
        }

        result = check_deep_nesting_performance(output, ground_truth)

        assert result.check_id == "PF-5"
        assert result.passed is True  # Should pass with custom threshold

    def test_pf5_calculates_ms_per_item(self):
        """PF-5 should calculate and report ms per item for O(n) validation."""
        output = {
            "statistics": {
                "scan_duration_ms": 1000,
                "max_directory_depth": 15,
                "total_files": 500,
                "total_directories": 500,
            },
            "files": [],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        # Should pass - 1ms per 1000 items is well under threshold
        assert result.passed is True

    def test_pf5_handles_zero_duration(self):
        """PF-5 should handle zero duration gracefully."""
        output = {
            "statistics": {
                "scan_duration_ms": 0,
                "max_directory_depth": 20,
                "total_files": 100,
                "total_directories": 50,
            },
            "files": [],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        # Zero duration should pass (instant scan)
        assert result.passed is True

    def test_pf5_handles_empty_output(self):
        """PF-5 should handle empty output gracefully."""
        output = {
            "statistics": {},
            "files": [],
        }

        result = check_deep_nesting_performance(output)

        assert result.check_id == "PF-5"
        # Empty output = no deep nesting, should pass
        assert result.passed is True


class TestRunPerformanceChecks:
    """Tests for run_performance_checks including PF-5."""

    def test_includes_pf5(self):
        """run_performance_checks should include PF-5."""
        output = {
            "statistics": {
                "total_files": 100,
                "scan_duration_ms": 100,
                "max_directory_depth": 5,
            },
            "files": [],
        }

        results = run_performance_checks(output)

        check_ids = [r.check_id for r in results]
        assert "PF-5" in check_ids, "PF-5 should be included in performance checks"

    def test_returns_five_checks(self):
        """run_performance_checks should return all 5 checks."""
        output = {
            "statistics": {
                "total_files": 500,
                "scan_duration_ms": 500,
            },
            "files": [],
        }

        results = run_performance_checks(output)

        assert len(results) == 5
        check_ids = [r.check_id for r in results]
        assert "PF-1" in check_ids
        assert "PF-2" in check_ids
        assert "PF-3" in check_ids
        assert "PF-4" in check_ids
        assert "PF-5" in check_ids

    def test_all_checks_return_check_result(self):
        """All performance checks should return CheckResult objects."""
        output = {
            "statistics": {
                "total_files": 100,
                "scan_duration_ms": 100,
            },
            "files": [],
        }

        results = run_performance_checks(output)

        for result in results:
            assert isinstance(result, CheckResult)
            assert result.category == CheckCategory.PERFORMANCE
            assert isinstance(result.passed, bool)
            assert 0.0 <= result.score <= 1.0
