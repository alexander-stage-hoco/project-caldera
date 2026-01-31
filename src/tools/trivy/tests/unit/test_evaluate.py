"""Unit tests for trivy evaluate module."""

import pytest


class TestVulnerabilityCountCheck:
    """Tests for vulnerability count check."""

    def test_count_within_range(self):
        """Test when count is within expected range."""
        from scripts.evaluate import check_vulnerability_count

        # Use envelope format with both metadata and data
        data = {
            "metadata": {"tool_name": "trivy"},
            "data": {
                "vulnerabilities": [{"id": "CVE-1"}, {"id": "CVE-2"}, {"id": "CVE-3"}]
            }
        }
        ground_truth = {"expected_vulnerabilities": {"min": 1, "max": 10}}

        result = check_vulnerability_count(data, ground_truth)
        assert result.passed is True
        assert result.score == 1.0

    def test_count_below_range(self):
        """Test when count is below expected range."""
        from scripts.evaluate import check_vulnerability_count

        data = {"metadata": {}, "data": {"vulnerabilities": []}}
        ground_truth = {"expected_vulnerabilities": {"min": 5, "max": 10}}

        result = check_vulnerability_count(data, ground_truth)
        assert result.passed is False


class TestRequiredFieldsCheck:
    """Tests for required fields check."""

    def test_all_fields_present(self):
        """Test when all required fields are present."""
        from scripts.evaluate import check_required_fields

        data = {
            "metadata": {},
            "data": {
                "vulnerabilities": [
                    {"id": "CVE-1", "package": "lodash", "severity": "HIGH"}
                ]
            }
        }

        result = check_required_fields(data, None)
        assert result.passed is True

    def test_missing_fields(self):
        """Test when required fields are missing."""
        from scripts.evaluate import check_required_fields

        data = {
            "metadata": {},
            "data": {
                "vulnerabilities": [{"id": "CVE-1"}]  # Missing package, severity
            }
        }

        result = check_required_fields(data, None)
        assert result.passed is False


class TestComputeScores:
    """Tests for score computation."""

    def test_all_passed(self):
        """Test score computation when all checks pass."""
        from scripts.evaluate import compute_scores, CheckResult

        results = [
            CheckResult("C1", "Check 1", "accuracy", "high", True, 1.0, "", {}),
            CheckResult("C2", "Check 2", "accuracy", "high", True, 1.0, "", {}),
        ]

        scores = compute_scores(results)
        assert scores["overall"]["pass_rate"] == 1.0
        assert scores["overall"]["passed"] == 2

    def test_partial_pass(self):
        """Test score computation with partial passes."""
        from scripts.evaluate import compute_scores, CheckResult

        results = [
            CheckResult("C1", "Check 1", "accuracy", "high", True, 1.0, "", {}),
            CheckResult("C2", "Check 2", "accuracy", "high", False, 0.0, "", {}),
        ]

        scores = compute_scores(results)
        assert scores["overall"]["pass_rate"] == 0.5
