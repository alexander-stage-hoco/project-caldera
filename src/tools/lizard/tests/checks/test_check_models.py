"""Tests for check models and utilities."""

import pytest

from scripts.checks import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    EvaluationReport,
    create_check_result,
    create_partial_check_result,
)


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_create_valid_check_result(self):
        """Test creating a valid CheckResult."""
        result = CheckResult(
            check_id="AC-1",
            name="Test Check",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            passed=True,
            score=1.0,
            message="All good",
            evidence={"key": "value"},
        )

        assert result.check_id == "AC-1"
        assert result.name == "Test Check"
        assert result.category == CheckCategory.ACCURACY
        assert result.severity == CheckSeverity.HIGH
        assert result.passed
        assert result.score == 1.0
        assert result.message == "All good"
        assert result.evidence == {"key": "value"}

    def test_score_validation_min(self):
        """Test that score below 0 raises ValueError."""
        with pytest.raises(ValueError):
            CheckResult(
                check_id="AC-1",
                name="Test",
                category=CheckCategory.ACCURACY,
                severity=CheckSeverity.HIGH,
                passed=False,
                score=-0.1,
                message="Invalid",
            )

    def test_score_validation_max(self):
        """Test that score above 1 raises ValueError."""
        with pytest.raises(ValueError):
            CheckResult(
                check_id="AC-1",
                name="Test",
                category=CheckCategory.ACCURACY,
                severity=CheckSeverity.HIGH,
                passed=True,
                score=1.1,
                message="Invalid",
            )


class TestEvaluationReport:
    """Tests for EvaluationReport dataclass."""

    def test_empty_report(self):
        """Test empty report properties."""
        report = EvaluationReport(
            timestamp="2026-01-04T12:00:00Z",
            analysis_path="/path/to/output.json",
            ground_truth_path="/path/to/ground-truth",
            checks=[],
        )

        assert report.total_checks == 0
        assert report.passed_checks == 0
        assert report.failed_checks == 0
        assert report.overall_score == 0.0
        assert report.critical_failures == []

    def test_report_with_checks(self):
        """Test report with multiple checks."""
        checks = [
            CheckResult(
                check_id="AC-1",
                name="Check 1",
                category=CheckCategory.ACCURACY,
                severity=CheckSeverity.CRITICAL,
                passed=True,
                score=1.0,
                message="Passed",
            ),
            CheckResult(
                check_id="AC-2",
                name="Check 2",
                category=CheckCategory.ACCURACY,
                severity=CheckSeverity.HIGH,
                passed=False,
                score=0.5,
                message="Partially failed",
            ),
            CheckResult(
                check_id="CV-1",
                name="Check 3",
                category=CheckCategory.COVERAGE,
                severity=CheckSeverity.CRITICAL,
                passed=False,
                score=0.0,
                message="Failed",
            ),
        ]

        report = EvaluationReport(
            timestamp="2026-01-04T12:00:00Z",
            analysis_path="/path/to/output.json",
            ground_truth_path="/path/to/ground-truth",
            checks=checks,
        )

        assert report.total_checks == 3
        assert report.passed_checks == 1
        assert report.failed_checks == 2
        assert report.overall_score == 0.5  # (1.0 + 0.5 + 0.0) / 3
        assert len(report.critical_failures) == 1  # CV-1 failed critically

    def test_by_category(self):
        """Test filtering checks by category."""
        checks = [
            CheckResult(
                check_id="AC-1",
                name="Accuracy 1",
                category=CheckCategory.ACCURACY,
                severity=CheckSeverity.HIGH,
                passed=True,
                score=1.0,
                message="OK",
            ),
            CheckResult(
                check_id="CV-1",
                name="Coverage 1",
                category=CheckCategory.COVERAGE,
                severity=CheckSeverity.HIGH,
                passed=True,
                score=1.0,
                message="OK",
            ),
        ]

        report = EvaluationReport(
            timestamp="2026-01-04T12:00:00Z",
            analysis_path="/path/to/output.json",
            ground_truth_path="/path/to/ground-truth",
            checks=checks,
        )

        accuracy_checks = report.by_category(CheckCategory.ACCURACY)
        coverage_checks = report.by_category(CheckCategory.COVERAGE)
        edge_checks = report.by_category(CheckCategory.EDGE_CASES)

        assert len(accuracy_checks) == 1
        assert len(coverage_checks) == 1
        assert len(edge_checks) == 0

    def test_to_dict(self):
        """Test report serialization to dict."""
        check = CheckResult(
            check_id="AC-1",
            name="Test",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            passed=True,
            score=1.0,
            message="OK",
            evidence={"key": "value"},
        )

        report = EvaluationReport(
            timestamp="2026-01-04T12:00:00Z",
            analysis_path="/path/to/output.json",
            ground_truth_path="/path/to/ground-truth",
            checks=[check],
        )

        result = report.to_dict()

        assert result["timestamp"] == "2026-01-04T12:00:00Z"
        assert result["analysis_path"] == "/path/to/output.json"
        assert result["summary"]["total_checks"] == 1
        assert result["summary"]["passed"] == 1
        assert result["summary"]["score"] == 1.0
        assert len(result["checks"]) == 1
        assert result["checks"][0]["check_id"] == "AC-1"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_create_check_result_passed(self):
        """Test creating a passing check result."""
        result = create_check_result(
            check_id="AC-1",
            name="Test",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            passed=True,
            message="All passed",
        )

        assert result.passed
        assert result.score == 1.0

    def test_create_check_result_failed(self):
        """Test creating a failing check result."""
        result = create_check_result(
            check_id="AC-1",
            name="Test",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            passed=False,
            message="Failed",
        )

        assert not result.passed
        assert result.score == 0.0

    def test_create_partial_check_result(self):
        """Test creating a partial score check result."""
        result = create_partial_check_result(
            check_id="AC-1",
            name="Test",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            score=0.75,
            message="Partially passed",
        )

        assert not result.passed  # 0.75 < 0.8 threshold
        assert result.score == 0.75

    def test_create_partial_check_result_threshold(self):
        """Test partial check result uses 80% threshold for passed."""
        passing = create_partial_check_result(
            check_id="AC-1",
            name="Test",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            score=0.85,
            message="Above threshold",
        )

        failing = create_partial_check_result(
            check_id="AC-2",
            name="Test",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            score=0.79,
            message="Below threshold",
        )

        assert passing.passed
        assert not failing.passed
