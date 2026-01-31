"""Unit tests for checks/iac.py module."""

import pytest

from checks.iac import (
    CATEGORY,
    check_actionability_rate,
    check_iac_severity_distribution,
    check_iac_total_count,
    check_iac_type_coverage,
    check_required_iac_ids,
    run_iac_checks,
)


class TestCheckIacTotalCount:
    """Tests for check_iac_total_count function."""

    def test_count_within_range(self, sample_iac_analysis):
        """Test when IaC count is within expected range."""
        ground_truth = {
            "iac_expected": True,
            "expected_iac": {
                "total": {"min": 1, "max": 10},
            },
        }

        result = check_iac_total_count(sample_iac_analysis, ground_truth)

        assert result.passed is True
        assert result.category == CATEGORY

    def test_count_below_range(self, sample_iac_analysis):
        """Test when IaC count is below expected range."""
        ground_truth = {
            "iac_expected": True,
            "expected_iac": {
                "total": {"min": 10, "max": 20},
            },
        }

        result = check_iac_total_count(sample_iac_analysis, ground_truth)

        assert result.passed is False
        assert "not in range" in result.message

    def test_no_expected_total_specified(self, sample_iac_analysis):
        """Test when no expected_iac.total specified."""
        ground_truth = {
            "iac_expected": True,
            "expected_iac": {},
        }

        result = check_iac_total_count(sample_iac_analysis, ground_truth)

        assert result.passed is True


class TestCheckIacSeverityDistribution:
    """Tests for check_iac_severity_distribution function."""

    def test_severity_within_range(self, sample_iac_analysis):
        """Test when IaC severity counts are within range."""
        ground_truth = {
            "iac_expected": True,
            "expected_iac": {
                "critical": {"min": 1, "max": 5},
                "high": {"min": 1, "max": 5},
            },
        }

        result = check_iac_severity_distribution(sample_iac_analysis, ground_truth)

        assert result.passed is True

    def test_critical_above_range(self, sample_iac_analysis):
        """Test when critical count is above range."""
        ground_truth = {
            "iac_expected": True,
            "expected_iac": {
                "critical": {"min": 0, "max": 0},
            },
        }

        result = check_iac_severity_distribution(sample_iac_analysis, ground_truth)

        assert result.passed is False
        assert "critical" in result.message.lower()


class TestCheckIacTypeCoverage:
    """Tests for check_iac_type_coverage function."""

    def test_all_types_detected(self, sample_iac_analysis):
        """Test when all required IaC types are detected."""
        ground_truth = {
            "iac_expected": True,
            "required_iac_types": ["dockerfile", "kubernetes"],
        }

        result = check_iac_type_coverage(sample_iac_analysis, ground_truth)

        assert result.passed is True

    def test_missing_type(self, sample_iac_analysis):
        """Test when a required IaC type is missing."""
        ground_truth = {
            "iac_expected": True,
            "required_iac_types": ["dockerfile", "terraform"],
        }

        result = check_iac_type_coverage(sample_iac_analysis, ground_truth)

        assert result.passed is False
        assert "terraform" in result.message.lower()

    def test_no_required_types_specified(self, sample_iac_analysis):
        """Test when no required types specified."""
        ground_truth = {
            "iac_expected": True,
        }

        result = check_iac_type_coverage(sample_iac_analysis, ground_truth)

        assert result.passed is True


class TestCheckRequiredIacIds:
    """Tests for check_required_iac_ids function."""

    def test_all_ids_detected(self, sample_iac_analysis):
        """Test when all required IaC IDs are detected."""
        ground_truth = {
            "iac_expected": True,
            "required_iac_ids": ["DS002", "KSV001"],
        }

        result = check_required_iac_ids(sample_iac_analysis, ground_truth)

        assert result.passed is True
        assert "2 required IaC issues detected" in result.message

    def test_missing_id(self, sample_iac_analysis):
        """Test when a required IaC ID is missing."""
        ground_truth = {
            "iac_expected": True,
            "required_iac_ids": ["DS002", "DS999"],
        }

        result = check_required_iac_ids(sample_iac_analysis, ground_truth)

        assert result.passed is False
        assert "DS999" in result.message

    def test_no_required_ids_specified(self, sample_iac_analysis):
        """Test when no required IDs specified."""
        ground_truth = {
            "iac_expected": True,
        }

        result = check_required_iac_ids(sample_iac_analysis, ground_truth)

        assert result.passed is True


class TestCheckActionabilityRate:
    """Tests for check_actionability_rate function."""

    def test_high_actionability(self, sample_iac_analysis):
        """Test with high actionability rate."""
        ground_truth = {"iac_expected": True}

        result = check_actionability_rate(sample_iac_analysis, ground_truth)

        assert result.passed is True
        assert "100.0%" in result.message

    def test_low_actionability(self):
        """Test with low actionability rate."""
        analysis = {
            "iac_misconfigurations": {
                "total_count": 3,
                "misconfigurations": [
                    {"id": "1", "resolution": ""},  # No resolution
                    {"id": "2", "resolution": "short"},  # Too short
                    {"id": "3", "resolution": ""},  # No resolution
                ],
            }
        }
        ground_truth = {"iac_expected": True}

        result = check_actionability_rate(analysis, ground_truth)

        assert result.passed is False
        assert "below 80%" in result.message

    def test_no_misconfigurations(self):
        """Test with no misconfigurations."""
        analysis = {
            "iac_misconfigurations": {
                "total_count": 0,
                "misconfigurations": [],
            }
        }
        ground_truth = {"iac_expected": True}

        result = check_actionability_rate(analysis, ground_truth)

        assert result.passed is True


class TestRunIacChecks:
    """Tests for run_iac_checks generator."""

    def test_no_checks_when_not_expected(self, sample_iac_analysis):
        """Test that no checks run when IaC is not expected."""
        ground_truth = {"iac_expected": False}

        results = list(run_iac_checks(sample_iac_analysis, ground_truth))

        assert len(results) == 0

    def test_yields_five_checks_when_expected(self, sample_iac_analysis):
        """Test that five checks are yielded when IaC is expected."""
        ground_truth = {"iac_expected": True}

        results = list(run_iac_checks(sample_iac_analysis, ground_truth))

        assert len(results) == 5

    def test_check_ids_when_expected(self, sample_iac_analysis):
        """Test that correct check IDs are returned."""
        ground_truth = {"iac_expected": True}

        results = list(run_iac_checks(sample_iac_analysis, ground_truth))

        check_ids = [r.check_id for r in results]
        assert "iac_total_count" in check_ids
        assert "iac_severity_distribution" in check_ids
        assert "iac_type_coverage" in check_ids
        assert "required_iac_ids" in check_ids
        assert "iac_actionability" in check_ids
