"""Unit tests for checks/accuracy.py module."""

import pytest

from checks.accuracy import (
    CATEGORY,
    check_count_accuracy,
    check_false_positive_rate,
    check_package_accuracy,
    check_severity_accuracy,
    run_accuracy_checks,
)


class TestCheckCountAccuracy:
    """Tests for check_count_accuracy function."""

    def test_count_within_range(self):
        """Test when count is within expected range."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 10,
            }
        }
        ground_truth = {
            "expected_vulnerabilities": {"min": 5, "max": 20},
        }

        result = check_count_accuracy(analysis, ground_truth)

        assert result.passed is True
        assert result.category == CATEGORY

    def test_count_below_range(self):
        """Test when count is below expected range."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 2,
            }
        }
        ground_truth = {
            "expected_vulnerabilities": {"min": 5, "max": 20},
        }

        result = check_count_accuracy(analysis, ground_truth)

        assert result.passed is False
        assert "not in expected range" in result.message

    def test_count_above_range(self):
        """Test when count is above expected range."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 50,
            }
        }
        ground_truth = {
            "expected_vulnerabilities": {"min": 5, "max": 20},
        }

        result = check_count_accuracy(analysis, ground_truth)

        assert result.passed is False

    def test_exact_expected_count(self):
        """Test with exact expected count (not a range)."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 10,
            }
        }
        ground_truth = {
            "expected_vulnerabilities": 10,
        }

        result = check_count_accuracy(analysis, ground_truth)

        assert result.passed is True

    def test_exact_expected_mismatch(self):
        """Test with exact expected count that doesn't match."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 8,
            }
        }
        ground_truth = {
            "expected_vulnerabilities": 10,
        }

        result = check_count_accuracy(analysis, ground_truth)

        assert result.passed is False

    def test_no_expected_vulnerabilities(self):
        """Test when no expected_vulnerabilities specified."""
        analysis = {"summary": {"total_vulnerabilities": 10}}
        ground_truth = {}

        result = check_count_accuracy(analysis, ground_truth)

        assert result.passed is True


class TestCheckSeverityAccuracy:
    """Tests for check_severity_accuracy function."""

    def test_all_severities_match(self):
        """Test when all severity counts match."""
        analysis = {
            "summary": {
                "critical_count": 2,
                "high_count": 5,
                "medium_count": 10,
                "low_count": 3,
            }
        }
        ground_truth = {
            "expected_critical": {"min": 1, "max": 5},
            "expected_high": {"min": 3, "max": 8},
            "expected_medium": {"min": 5, "max": 15},
            "expected_low": {"min": 0, "max": 10},
        }

        result = check_severity_accuracy(analysis, ground_truth)

        assert result.passed is True
        assert "4 severity counts" in result.message

    def test_critical_mismatch(self):
        """Test when critical count doesn't match."""
        analysis = {
            "summary": {
                "critical_count": 10,
            }
        }
        ground_truth = {
            "expected_critical": {"min": 1, "max": 5},
        }

        result = check_severity_accuracy(analysis, ground_truth)

        assert result.passed is False
        assert "critical_count" in result.message

    def test_no_severities_specified(self):
        """Test when no severity expectations specified."""
        analysis = {"summary": {}}
        ground_truth = {}

        result = check_severity_accuracy(analysis, ground_truth)

        assert result.passed is True
        assert "No severity expectations" in result.message


class TestCheckFalsePositiveRate:
    """Tests for check_false_positive_rate function."""

    def test_no_false_positives(self, sample_normalized_analysis):
        """Test when no false positives detected."""
        result = check_false_positive_rate(sample_normalized_analysis, {})

        assert result.passed is True

    def test_expected_zero_but_found_some(self):
        """Test when expected 0 but found vulnerabilities."""
        analysis = {
            "summary": {
                "total_vulnerabilities": 5,
            }
        }
        ground_truth = {
            "expected_vulnerabilities": {"min": 0, "max": 0},
        }

        result = check_false_positive_rate(analysis, ground_truth)

        assert result.passed is False
        assert "Expected 0" in result.message

    def test_forbidden_packages_found(self):
        """Test when forbidden packages are found."""
        analysis = {
            "summary": {"total_vulnerabilities": 2},
            "vulnerabilities": [
                {"package": "safe-pkg"},
                {"package": "forbidden-pkg"},
            ],
        }
        ground_truth = {
            "forbidden_packages": ["forbidden-pkg"],
        }

        result = check_false_positive_rate(analysis, ground_truth)

        assert result.passed is False
        assert "forbidden-pkg" in result.message

    def test_no_forbidden_packages(self):
        """Test when no forbidden packages in results."""
        analysis = {
            "summary": {"total_vulnerabilities": 2},
            "vulnerabilities": [
                {"package": "pkg1"},
                {"package": "pkg2"},
            ],
        }
        ground_truth = {
            "forbidden_packages": ["forbidden-pkg"],
        }

        result = check_false_positive_rate(analysis, ground_truth)

        assert result.passed is True


class TestCheckPackageAccuracy:
    """Tests for check_package_accuracy function."""

    def test_all_required_packages_found(self):
        """Test when all required packages are found."""
        analysis = {
            "vulnerabilities": [
                {"package": "requests"},
                {"package": "urllib3"},
                {"package": "pyyaml"},
            ]
        }
        ground_truth = {
            "required_packages": ["requests", "urllib3"],
        }

        result = check_package_accuracy(analysis, ground_truth)

        assert result.passed is True
        assert "2 required packages detected" in result.message

    def test_missing_required_package(self):
        """Test when a required package is missing."""
        analysis = {
            "vulnerabilities": [
                {"package": "requests"},
            ]
        }
        ground_truth = {
            "required_packages": ["requests", "urllib3"],
        }

        result = check_package_accuracy(analysis, ground_truth)

        assert result.passed is False
        assert "urllib3" in result.message

    def test_no_required_packages_specified(self):
        """Test when no required packages specified."""
        analysis = {"vulnerabilities": []}
        ground_truth = {}

        result = check_package_accuracy(analysis, ground_truth)

        assert result.passed is True


class TestRunAccuracyChecks:
    """Tests for run_accuracy_checks generator."""

    def test_yields_four_checks(self, sample_normalized_analysis, sample_ground_truth_flat):
        """Test that four checks are yielded."""
        results = list(
            run_accuracy_checks(sample_normalized_analysis, sample_ground_truth_flat)
        )

        assert len(results) == 4

    def test_all_checks_have_category(
        self, sample_normalized_analysis, sample_ground_truth_flat
    ):
        """Test that all checks have correct category."""
        results = list(
            run_accuracy_checks(sample_normalized_analysis, sample_ground_truth_flat)
        )

        for result in results:
            assert result.category == CATEGORY
