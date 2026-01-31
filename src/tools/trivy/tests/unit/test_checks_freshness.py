"""Unit tests for checks/freshness.py module."""

import pytest

from checks.freshness import (
    CATEGORY,
    check_freshness_presence,
    check_outdated_count,
    check_registry_coverage,
    check_version_delta_accuracy,
    run_freshness_checks,
)


class TestCheckFreshnessPresence:
    """Tests for check_freshness_presence function."""

    def test_freshness_present_when_expected(self, sample_freshness_analysis):
        """Test when freshness is present and expected."""
        ground_truth = {"freshness_expected": True}

        result = check_freshness_presence(sample_freshness_analysis, ground_truth)

        assert result.passed is True
        assert result.category == CATEGORY
        assert "Freshness data present" in result.message

    def test_freshness_missing_when_expected(self):
        """Test when freshness is missing but expected."""
        analysis = {"freshness": {"checked": False}}
        ground_truth = {"freshness_expected": True}

        result = check_freshness_presence(analysis, ground_truth)

        assert result.passed is False
        assert "not performed" in result.message

    def test_freshness_not_expected_and_not_checked(self):
        """Test when freshness is not expected and not checked."""
        analysis = {}
        ground_truth = {"freshness_expected": False}

        result = check_freshness_presence(analysis, ground_truth)

        assert result.passed is True
        assert "not required" in result.message

    def test_freshness_checked_but_not_expected(self):
        """Test when freshness is checked but not expected."""
        analysis = {
            "freshness": {
                "checked": True,
                "total_packages": 5,
                "outdated_count": 2,
            }
        }
        ground_truth = {"freshness_expected": False}

        result = check_freshness_presence(analysis, ground_truth)

        # Should pass - extra data is fine
        assert result.passed is True


class TestCheckOutdatedCount:
    """Tests for check_outdated_count function."""

    def test_outdated_count_within_range(self, sample_freshness_analysis):
        """Test when outdated count is within expected range."""
        ground_truth = {
            "expected_outdated_count": {"min": 1, "max": 5},
        }

        result = check_outdated_count(sample_freshness_analysis, ground_truth)

        assert result.passed is True
        assert "within" in result.message

    def test_outdated_count_below_range(self, sample_freshness_analysis):
        """Test when outdated count is below expected range."""
        ground_truth = {
            "expected_outdated_count": {"min": 10, "max": 20},
        }

        result = check_outdated_count(sample_freshness_analysis, ground_truth)

        assert result.passed is False
        assert "outside" in result.message

    def test_freshness_not_checked(self):
        """Test when freshness is not checked."""
        analysis = {"freshness": {"checked": False}}
        ground_truth = {}

        result = check_outdated_count(analysis, ground_truth)

        assert result.passed is True
        assert "Skipped" in result.message

    def test_no_expectation_set(self, sample_freshness_analysis):
        """Test when no outdated count expectation is set."""
        ground_truth = {}

        result = check_outdated_count(sample_freshness_analysis, ground_truth)

        assert result.passed is True
        assert "no specific expectation" in result.message


class TestCheckVersionDeltaAccuracy:
    """Tests for check_version_delta_accuracy function."""

    def test_consistent_version_deltas(self, sample_freshness_analysis):
        """Test with consistent version delta calculations."""
        ground_truth = {}

        result = check_version_delta_accuracy(sample_freshness_analysis, ground_truth)

        assert result.passed is True
        assert "consistent" in result.message.lower()

    def test_inconsistent_outdated_flag(self):
        """Test when package has delta but is_outdated=False."""
        analysis = {
            "freshness": {
                "checked": True,
                "packages": [
                    {
                        "package": "pkg",
                        "major_versions_behind": 1,
                        "minor_versions_behind": 0,
                        "patch_versions_behind": 0,
                        "is_outdated": False,  # Should be True
                    }
                ],
            }
        }
        ground_truth = {}

        result = check_version_delta_accuracy(analysis, ground_truth)

        assert result.passed is False
        assert "inconsistencies" in result.message.lower()

    def test_negative_version_delta(self):
        """Test when version delta is negative."""
        analysis = {
            "freshness": {
                "checked": True,
                "packages": [
                    {
                        "package": "pkg",
                        "major_versions_behind": -1,
                        "minor_versions_behind": 0,
                        "patch_versions_behind": 0,
                        "is_outdated": True,
                    }
                ],
            }
        }
        ground_truth = {}

        result = check_version_delta_accuracy(analysis, ground_truth)

        assert result.passed is False

    def test_freshness_not_checked(self):
        """Test when freshness is not checked."""
        analysis = {}
        ground_truth = {}

        result = check_version_delta_accuracy(analysis, ground_truth)

        assert result.passed is True
        assert "Skipped" in result.message


class TestCheckRegistryCoverage:
    """Tests for check_registry_coverage function."""

    def test_good_coverage(self, sample_freshness_analysis):
        """Test with good registry coverage."""
        ground_truth = {}

        result = check_registry_coverage(sample_freshness_analysis, ground_truth)

        assert result.passed is True
        assert "pip" in result.message

    def test_missing_coverage(self):
        """Test when a supported type is missing coverage."""
        analysis = {
            "freshness": {
                "checked": True,
                "packages": [],  # No packages covered
            },
            "targets": [{"type": "pip"}],  # But pip is used
        }
        ground_truth = {}

        result = check_registry_coverage(analysis, ground_truth)

        assert result.passed is False
        assert "Missing" in result.message

    def test_freshness_not_checked(self):
        """Test when freshness is not checked."""
        analysis = {}
        ground_truth = {}

        result = check_registry_coverage(analysis, ground_truth)

        assert result.passed is True
        assert "Skipped" in result.message


class TestRunFreshnessChecks:
    """Tests for run_freshness_checks generator."""

    def test_yields_four_checks(self, sample_freshness_analysis):
        """Test that four checks are yielded."""
        ground_truth = {}

        results = list(run_freshness_checks(sample_freshness_analysis, ground_truth))

        assert len(results) == 4

    def test_all_checks_have_category(self, sample_freshness_analysis):
        """Test that all checks have correct category."""
        ground_truth = {}

        results = list(run_freshness_checks(sample_freshness_analysis, ground_truth))

        for result in results:
            assert result.category == CATEGORY

    def test_check_ids(self, sample_freshness_analysis):
        """Test that correct check IDs are returned."""
        ground_truth = {}

        results = list(run_freshness_checks(sample_freshness_analysis, ground_truth))

        check_ids = [r.check_id for r in results]
        assert "FQ01_freshness_presence" in check_ids
        assert "FQ02_outdated_count" in check_ids
        assert "FQ03_version_delta" in check_ids
        assert "FQ04_registry_coverage" in check_ids
