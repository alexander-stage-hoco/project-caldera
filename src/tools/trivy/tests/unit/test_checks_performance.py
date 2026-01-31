"""Unit tests for checks/performance.py module."""

import pytest

from checks.performance import (
    CATEGORY,
    SMALL_REPO_THRESHOLD_MS,
    check_memory_not_excessive,
    check_small_repo_speed,
    run_performance_checks,
)


class TestCheckSmallRepoSpeed:
    """Tests for check_small_repo_speed function."""

    def test_fast_scan(self):
        """Test with fast scan time."""
        analysis = {"scan_time_ms": 500.0}

        result = check_small_repo_speed(analysis)

        assert result.passed is True
        assert result.category == CATEGORY
        assert "500ms" in result.message

    def test_slow_scan(self):
        """Test with slow scan time."""
        analysis = {"scan_time_ms": 60000.0}  # 60 seconds

        result = check_small_repo_speed(analysis)

        assert result.passed is False
        assert "threshold" in result.message.lower()

    def test_exactly_at_threshold(self):
        """Test with scan time exactly at threshold."""
        analysis = {"scan_time_ms": SMALL_REPO_THRESHOLD_MS}

        result = check_small_repo_speed(analysis)

        assert result.passed is True

    def test_above_threshold(self):
        """Test with scan time above threshold."""
        analysis = {"scan_time_ms": SMALL_REPO_THRESHOLD_MS + 1}

        result = check_small_repo_speed(analysis)

        assert result.passed is False

    def test_no_scan_time(self):
        """Test with no scan time recorded."""
        analysis = {"scan_time_ms": 0}

        result = check_small_repo_speed(analysis)

        assert result.passed is True
        assert "cached or skipped" in result.message.lower()

    def test_negative_scan_time(self):
        """Test with negative scan time (edge case)."""
        analysis = {"scan_time_ms": -100}

        result = check_small_repo_speed(analysis)

        assert result.passed is True


class TestCheckMemoryNotExcessive:
    """Tests for check_memory_not_excessive function."""

    def test_valid_output(self, sample_normalized_analysis):
        """Test with valid output indicating no memory issues."""
        result = check_memory_not_excessive(sample_normalized_analysis)

        assert result.passed is True
        assert "without memory issues" in result.message

    def test_missing_summary(self):
        """Test when summary is missing (possible crash)."""
        analysis = {}

        result = check_memory_not_excessive(analysis)

        assert result.passed is False
        assert "memory/crash" in result.message.lower()

    def test_empty_summary(self):
        """Test when summary is empty."""
        analysis = {"summary": {}}

        result = check_memory_not_excessive(analysis)

        # Empty dict is falsy in Python, so treated as "no summary found"
        # This is expected behavior - empty summary could indicate issues
        assert result.passed is False


class TestRunPerformanceChecks:
    """Tests for run_performance_checks generator."""

    def test_yields_two_checks(self, sample_normalized_analysis):
        """Test that two checks are yielded."""
        ground_truth = {}

        results = list(
            run_performance_checks(sample_normalized_analysis, ground_truth)
        )

        assert len(results) == 2

    def test_check_ids(self, sample_normalized_analysis):
        """Test that correct check IDs are returned."""
        ground_truth = {}

        results = list(
            run_performance_checks(sample_normalized_analysis, ground_truth)
        )

        check_ids = [r.check_id for r in results]
        assert "small_repo_speed" in check_ids
        assert "memory_not_excessive" in check_ids

    def test_all_checks_have_category(self, sample_normalized_analysis):
        """Test that all checks have correct category."""
        ground_truth = {}

        results = list(
            run_performance_checks(sample_normalized_analysis, ground_truth)
        )

        for result in results:
            assert result.category == CATEGORY


class TestPerformanceThresholds:
    """Tests for performance threshold constants."""

    def test_small_repo_threshold(self):
        """Test that small repo threshold is reasonable."""
        assert SMALL_REPO_THRESHOLD_MS == 30000  # 30 seconds
        assert SMALL_REPO_THRESHOLD_MS > 0

    def test_threshold_is_numeric(self):
        """Test that threshold is a number."""
        assert isinstance(SMALL_REPO_THRESHOLD_MS, (int, float))
