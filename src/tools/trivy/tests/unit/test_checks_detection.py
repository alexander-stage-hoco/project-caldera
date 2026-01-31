"""Unit tests for checks/detection.py module."""

import pytest

from checks.detection import (
    CATEGORY,
    check_critical_detected,
    check_fix_availability,
    check_severity_distribution,
    check_target_identification,
    run_detection_checks,
)


class TestCheckCriticalDetected:
    """Tests for check_critical_detected function."""

    def test_all_required_cves_detected(self):
        """Test when all required CVEs are detected."""
        analysis = {
            "vulnerabilities": [
                {"id": "CVE-2021-0001"},
                {"id": "CVE-2021-0002"},
                {"id": "CVE-2021-0003"},
            ]
        }
        ground_truth = {
            "required_cves": ["CVE-2021-0001", "CVE-2021-0002"],
        }

        result = check_critical_detected(analysis, ground_truth)

        assert result.passed is True
        assert result.category == CATEGORY
        assert "2 required CVEs detected" in result.message

    def test_missing_required_cve(self):
        """Test when a required CVE is missing."""
        analysis = {
            "vulnerabilities": [
                {"id": "CVE-2021-0001"},
            ]
        }
        ground_truth = {
            "required_cves": ["CVE-2021-0001", "CVE-2021-0002"],
        }

        result = check_critical_detected(analysis, ground_truth)

        assert result.passed is False
        assert "CVE-2021-0002" in result.message

    def test_no_required_cves_specified(self):
        """Test when no required CVEs are specified."""
        analysis = {"vulnerabilities": [{"id": "CVE-2021-0001"}]}
        ground_truth = {}

        result = check_critical_detected(analysis, ground_truth)

        assert result.passed is True
        assert "No required CVEs specified" in result.message

    def test_empty_vulnerabilities(self):
        """Test with empty vulnerability list."""
        analysis = {"vulnerabilities": []}
        ground_truth = {"required_cves": ["CVE-2021-0001"]}

        result = check_critical_detected(analysis, ground_truth)

        assert result.passed is False


class TestCheckSeverityDistribution:
    """Tests for check_severity_distribution function."""

    def test_severity_within_range(self):
        """Test when severity counts are within expected range."""
        analysis = {
            "summary": {
                "critical_count": 2,
                "high_count": 5,
            }
        }
        ground_truth = {
            "expected_critical": {"min": 1, "max": 5},
            "expected_high": {"min": 0, "max": 10},
        }

        result = check_severity_distribution(analysis, ground_truth)

        assert result.passed is True

    def test_critical_below_range(self):
        """Test when critical count is below expected range."""
        analysis = {
            "summary": {
                "critical_count": 0,
                "high_count": 5,
            }
        }
        ground_truth = {
            "expected_critical": {"min": 1, "max": 5},
        }

        result = check_severity_distribution(analysis, ground_truth)

        assert result.passed is False
        assert "critical" in result.message.lower()

    def test_critical_above_range(self):
        """Test when critical count is above expected range."""
        analysis = {
            "summary": {
                "critical_count": 10,
                "high_count": 5,
            }
        }
        ground_truth = {
            "expected_critical": {"min": 1, "max": 5},
        }

        result = check_severity_distribution(analysis, ground_truth)

        assert result.passed is False

    def test_exact_expected_critical(self):
        """Test with exact expected critical count (not a range)."""
        analysis = {
            "summary": {
                "critical_count": 3,
            }
        }
        ground_truth = {
            "expected_critical": 3,
        }

        result = check_severity_distribution(analysis, ground_truth)

        assert result.passed is True

    def test_exact_expected_mismatch(self):
        """Test with exact expected count that doesn't match."""
        analysis = {
            "summary": {
                "critical_count": 5,
            }
        }
        ground_truth = {
            "expected_critical": 3,
        }

        result = check_severity_distribution(analysis, ground_truth)

        assert result.passed is False


class TestCheckTargetIdentification:
    """Tests for check_target_identification function."""

    def test_targets_within_range(self):
        """Test when target count is within expected range."""
        analysis = {
            "targets": [
                {"path": "requirements.txt", "type": "pip"},
                {"path": "package.json", "type": "npm"},
            ]
        }
        ground_truth = {
            "expected_targets": {"min": 1, "max": 5},
        }

        result = check_target_identification(analysis, ground_truth)

        assert result.passed is True
        assert "2 targets" in result.message

    def test_no_targets_when_expected(self):
        """Test when no targets found but expected."""
        analysis = {"targets": []}
        ground_truth = {
            "expected_targets": {"min": 1, "max": 5},
        }

        result = check_target_identification(analysis, ground_truth)

        assert result.passed is False
        assert "not in range" in result.message

    def test_no_expected_targets_specified(self):
        """Test when no expected_targets specified."""
        analysis = {"targets": []}
        ground_truth = {}

        result = check_target_identification(analysis, ground_truth)

        assert result.passed is True


class TestCheckFixAvailability:
    """Tests for check_fix_availability function."""

    def test_fix_pct_within_range(self):
        """Test when fix_available_pct is within range."""
        analysis = {
            "summary": {
                "fix_available_pct": 80.0,
            }
        }
        ground_truth = {
            "expected_fix_available_pct": {"min": 50, "max": 100},
        }

        result = check_fix_availability(analysis, ground_truth)

        assert result.passed is True

    def test_fix_pct_below_range(self):
        """Test when fix_available_pct is below range."""
        analysis = {
            "summary": {
                "fix_available_pct": 30.0,
            }
        }
        ground_truth = {
            "expected_fix_available_pct": {"min": 50, "max": 100},
        }

        result = check_fix_availability(analysis, ground_truth)

        assert result.passed is False

    def test_no_expected_fix_pct_specified(self):
        """Test when no expected_fix_available_pct specified."""
        analysis = {"summary": {"fix_available_pct": 50.0}}
        ground_truth = {}

        result = check_fix_availability(analysis, ground_truth)

        assert result.passed is True


class TestRunDetectionChecks:
    """Tests for run_detection_checks generator."""

    def test_yields_four_checks(self, sample_normalized_analysis, sample_ground_truth_flat):
        """Test that four checks are yielded."""
        results = list(
            run_detection_checks(sample_normalized_analysis, sample_ground_truth_flat)
        )

        assert len(results) == 4

    def test_check_ids(self, sample_normalized_analysis, sample_ground_truth_flat):
        """Test that correct check IDs are returned."""
        results = list(
            run_detection_checks(sample_normalized_analysis, sample_ground_truth_flat)
        )

        check_ids = [r.check_id for r in results]
        assert "critical_detected" in check_ids
        assert "severity_distribution" in check_ids
        assert "target_identification" in check_ids
        assert "fix_availability" in check_ids
