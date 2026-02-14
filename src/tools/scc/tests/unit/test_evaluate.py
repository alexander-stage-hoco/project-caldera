"""Tests for scripts/evaluate.py - evaluation orchestrator and report generation."""
from __future__ import annotations

import pytest
from scripts.evaluate import (
    generate_check_report,
    generate_scorecard_json,
    generate_scorecard,
    _resolve_results_dir,
)
from scripts.checks import CheckResult, DimensionResult, EvaluationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_check(check_id: str, name: str, passed: bool, message: str = "OK",
               expected=None, actual=None) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        name=name,
        passed=passed,
        message=message,
        expected=expected,
        actual=actual,
    )


@pytest.fixture
def sample_dimensions():
    """Create sample dimension results."""
    oq_checks = [
        make_check("OQ-1", "JSON Valid", True),
        make_check("OQ-2", "Array Structure", True),
        make_check("OQ-3", "Required Fields", True),
        make_check("OQ-4", "Numeric Types", False, "Invalid value", "int", "string"),
    ]
    if_checks = [
        make_check("IF-1", "Output Generated", True),
        make_check("IF-2", "Schema Valid", True),
        make_check("IF-critical-1", "Critical Check", False, "Failed critically"),
    ]
    return [
        DimensionResult("output_quality", 0.20, oq_checks, 4, 0.80),
        DimensionResult("integration_fit", 0.15, if_checks, 3, 0.45),
    ]


@pytest.fixture
def sample_result(sample_dimensions):
    """Create a complete evaluation result."""
    return EvaluationResult(
        run_id="test-run-001",
        timestamp="2026-01-01T00:00:00Z",
        dimensions=sample_dimensions,
        total_score=1.25,
        decision="FAIL",
        summary={"total_checks": 7, "passed_checks": 5, "dimensions_count": 2},
    )


# ---------------------------------------------------------------------------
# Tests: _resolve_results_dir
# ---------------------------------------------------------------------------

class TestResolveResultsDir:
    def test_default_dir(self, tmp_path):
        result = _resolve_results_dir(tmp_path)
        assert result == tmp_path / "evaluation" / "results"

    def test_env_override(self, tmp_path, monkeypatch):
        custom_dir = str(tmp_path / "custom")
        monkeypatch.setenv("EVAL_OUTPUT_DIR", custom_dir)
        result = _resolve_results_dir(tmp_path)
        assert str(result) == custom_dir


# ---------------------------------------------------------------------------
# Tests: generate_check_report
# ---------------------------------------------------------------------------

class TestGenerateCheckReport:
    def test_report_header(self, sample_dimensions):
        report = generate_check_report(sample_dimensions)
        assert "Detailed Check Results" in report

    def test_report_includes_dimensions(self, sample_dimensions):
        report = generate_check_report(sample_dimensions)
        assert "Output Quality" in report
        assert "Integration Fit" in report

    def test_report_includes_pass_fail(self, sample_dimensions):
        report = generate_check_report(sample_dimensions)
        assert "[PASS]" in report
        assert "[FAIL]" in report

    def test_report_includes_scores(self, sample_dimensions):
        report = generate_check_report(sample_dimensions)
        assert "4/5" in report
        assert "3/5" in report

    def test_report_includes_expected_actual_for_failures(self, sample_dimensions):
        report = generate_check_report(sample_dimensions)
        assert "Expected: int" in report
        assert "Actual: string" in report


# ---------------------------------------------------------------------------
# Tests: generate_scorecard_json
# ---------------------------------------------------------------------------

class TestGenerateScorecardJson:
    def test_basic_structure(self, sample_result):
        data = generate_scorecard_json(sample_result)
        assert data["tool"] == "scc"
        assert data["version"] == "1.0.0"
        assert data["generated_at"] == "2026-01-01T00:00:00Z"

    def test_summary_values(self, sample_result):
        data = generate_scorecard_json(sample_result)
        s = data["summary"]
        assert s["total_checks"] == 7
        assert s["passed"] == 5
        assert s["failed"] == 2
        assert s["decision"] == "FAIL"
        assert s["normalized_score"] == 1.25

    def test_dimensions_count(self, sample_result):
        data = generate_scorecard_json(sample_result)
        assert len(data["dimensions"]) == 2

    def test_dimension_details(self, sample_result):
        data = generate_scorecard_json(sample_result)
        d1 = data["dimensions"][0]
        assert d1["id"] == "D1"
        assert d1["name"] == "Output Quality"
        assert d1["weight"] == 0.20
        assert d1["total_checks"] == 4
        assert d1["passed"] == 3
        assert d1["failed"] == 1
        assert d1["score"] == 4

    def test_critical_failures_detected(self, sample_result):
        data = generate_scorecard_json(sample_result)
        assert len(data["critical_failures"]) == 1
        assert data["critical_failures"][0]["check_id"] == "IF-critical-1"

    def test_thresholds_present(self, sample_result):
        data = generate_scorecard_json(sample_result)
        assert "STRONG_PASS" in data["thresholds"]
        assert "FAIL" in data["thresholds"]


# ---------------------------------------------------------------------------
# Tests: generate_scorecard (markdown)
# ---------------------------------------------------------------------------

class TestGenerateScorecard:
    def test_header(self, sample_result):
        md = generate_scorecard(sample_result)
        assert "scc Evaluation Scorecard" in md
        assert sample_result.run_id in md

    def test_dimension_sections(self, sample_result):
        md = generate_scorecard(sample_result)
        assert "Output Quality" in md
        assert "Integration Fit" in md

    def test_decision_in_output(self, sample_result):
        md = generate_scorecard(sample_result)
        assert "FAIL" in md

    def test_strong_pass_message(self, sample_result):
        sample_result.decision = "STRONG_PASS"
        md = generate_scorecard(sample_result)
        assert "approved" in md

    def test_weak_pass_message(self, sample_result):
        sample_result.decision = "WEAK_PASS"
        md = generate_scorecard(sample_result)
        assert "reservations" in md

    def test_fail_message(self, sample_result):
        sample_result.decision = "FAIL"
        md = generate_scorecard(sample_result)
        assert "does not meet" in md
