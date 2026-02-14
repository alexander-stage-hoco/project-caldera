"""Tests for scripts/error_analyzer.py - LLM failure analysis."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from scripts.checks import CheckResult
from scripts.error_analyzer import (
    analyze_failure,
    analyze_all_failures,
    generate_failure_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def passing_check():
    return CheckResult(
        check_id="T-1",
        name="Passing Check",
        passed=True,
        message="All good",
    )


@pytest.fixture
def failing_check():
    return CheckResult(
        check_id="OQ-1",
        name="JSON Valid",
        passed=False,
        message="JSON parse error at line 5",
        expected="valid JSON",
        actual="parse error",
        evidence={"error": "Unexpected token"},
    )


@pytest.fixture
def failing_check_no_evidence():
    return CheckResult(
        check_id="OQ-2",
        name="Array Structure",
        passed=False,
        message="Root is dict not list",
        expected="list",
        actual="dict",
    )


# ---------------------------------------------------------------------------
# Tests: analyze_failure
# ---------------------------------------------------------------------------

class TestAnalyzeFailure:
    """Tests for analyze_failure function."""

    def test_passing_check_returns_early(self, passing_check):
        result = analyze_failure(passing_check)
        assert result["llm_available"] is False
        assert "passed" in result["analysis"].lower()

    @patch("scripts.error_analyzer.get_provider", return_value=None)
    def test_no_provider_returns_fallback(self, mock_provider, failing_check):
        result = analyze_failure(failing_check)
        assert result["llm_available"] is False
        assert result["root_cause"] == "Unknown"
        assert "Manual investigation" in result["remediation"]

    @patch("scripts.error_analyzer.get_provider")
    def test_successful_llm_analysis(self, mock_get_provider, failing_check):
        mock_provider = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Root cause: malformed JSON output"
        mock_provider.complete.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        result = analyze_failure(failing_check)
        assert result["llm_available"] is True
        assert "malformed JSON" in result["analysis"]

    @patch("scripts.error_analyzer.get_provider")
    def test_llm_error_handled(self, mock_get_provider, failing_check):
        mock_provider = MagicMock()
        mock_provider.complete.side_effect = RuntimeError("API timeout")
        mock_get_provider.return_value = mock_provider

        result = analyze_failure(failing_check)
        assert result["llm_available"] is True
        assert "error" in result
        assert "API timeout" in result["error"]


# ---------------------------------------------------------------------------
# Tests: analyze_all_failures
# ---------------------------------------------------------------------------

class TestAnalyzeAllFailures:
    """Tests for analyze_all_failures function."""

    def test_all_passing_returns_summary(self, passing_check):
        result = analyze_all_failures([passing_check, passing_check])
        assert "summary" in result
        assert "passed" in result["summary"].lower()

    @patch("scripts.error_analyzer.get_provider", return_value=None)
    def test_analyzes_each_failure(self, mock_provider, failing_check, passing_check):
        result = analyze_all_failures([passing_check, failing_check])
        assert "OQ-1" in result
        assert result["OQ-1"]["llm_available"] is False

    @patch("scripts.error_analyzer.get_provider", return_value=None)
    def test_multiple_failures(self, mock_provider, failing_check, failing_check_no_evidence):
        result = analyze_all_failures([failing_check, failing_check_no_evidence])
        assert "OQ-1" in result
        assert "OQ-2" in result


# ---------------------------------------------------------------------------
# Tests: generate_failure_report
# ---------------------------------------------------------------------------

class TestGenerateFailureReport:
    """Tests for generate_failure_report function."""

    def test_all_passing_report(self, passing_check):
        report = generate_failure_report([passing_check])
        assert "All checks passed" in report
        assert "Failure Analysis Report" in report

    @patch("scripts.error_analyzer.get_provider", return_value=None)
    def test_failure_report_contains_details(self, mock_provider, failing_check):
        report = generate_failure_report([failing_check])
        assert "OQ-1" in report
        assert "JSON Valid" in report
        assert "FAILED" in report
        assert "Expected:" in report
        assert "Actual:" in report

    @patch("scripts.error_analyzer.get_provider", return_value=None)
    def test_report_without_expected_actual(self, mock_provider, failing_check_no_evidence):
        # failing_check_no_evidence has expected and actual set
        check = CheckResult(
            check_id="X-1",
            name="No Details",
            passed=False,
            message="Something failed",
        )
        report = generate_failure_report([check])
        assert "X-1" in report
        assert "Something failed" in report
