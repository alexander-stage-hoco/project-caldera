"""Tests for scripts/scoring.py - evaluation scoring logic."""
from __future__ import annotations

import pytest
from scripts.scoring import (
    compute_dimension_score,
    compute_dimension_result,
    compute_total_score,
    determine_decision,
    format_score_summary,
    SCORING_TABLES,
    DIMENSION_WEIGHTS,
)
from scripts.checks import CheckResult, DimensionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_checks(passed: int, failed: int) -> list[CheckResult]:
    """Create a list of check results with given pass/fail counts."""
    checks = []
    for i in range(passed):
        checks.append(CheckResult(
            check_id=f"T-{i+1}",
            name=f"Check {i+1}",
            passed=True,
            message="OK",
        ))
    for i in range(failed):
        checks.append(CheckResult(
            check_id=f"T-{passed+i+1}",
            name=f"Check {passed+i+1}",
            passed=False,
            message="Failed",
        ))
    return checks


# ---------------------------------------------------------------------------
# Tests: compute_dimension_score
# ---------------------------------------------------------------------------

class TestComputeDimensionScore:
    """Tests for compute_dimension_score."""

    def test_all_checks_pass_output_quality(self):
        checks = make_checks(8, 0)
        assert compute_dimension_score(checks, "output_quality") == 5

    def test_most_checks_pass_output_quality(self):
        checks = make_checks(7, 1)
        assert compute_dimension_score(checks, "output_quality") == 4

    def test_some_checks_pass_output_quality(self):
        checks = make_checks(5, 3)
        assert compute_dimension_score(checks, "output_quality") == 3

    def test_few_checks_pass_output_quality(self):
        checks = make_checks(3, 5)
        assert compute_dimension_score(checks, "output_quality") == 2

    def test_zero_checks_pass(self):
        checks = make_checks(0, 8)
        assert compute_dimension_score(checks, "output_quality") == 1

    def test_license_dimension_scoring(self):
        # License has different thresholds: {3: 5, 2: 4, 1: 3, 0: 2}
        assert compute_dimension_score(make_checks(3, 0), "license") == 5
        assert compute_dimension_score(make_checks(2, 1), "license") == 4
        assert compute_dimension_score(make_checks(1, 2), "license") == 3
        assert compute_dimension_score(make_checks(0, 3), "license") == 2

    def test_unknown_dimension_defaults_to_1(self):
        checks = make_checks(10, 0)
        assert compute_dimension_score(checks, "nonexistent") == 1

    def test_performance_dimension(self):
        assert compute_dimension_score(make_checks(4, 0), "performance") == 5
        assert compute_dimension_score(make_checks(3, 1), "performance") == 4
        assert compute_dimension_score(make_checks(2, 2), "performance") == 3
        assert compute_dimension_score(make_checks(1, 3), "performance") == 2
        assert compute_dimension_score(make_checks(0, 4), "performance") == 1


# ---------------------------------------------------------------------------
# Tests: compute_dimension_result
# ---------------------------------------------------------------------------

class TestComputeDimensionResult:
    """Tests for compute_dimension_result."""

    def test_basic_result(self):
        checks = make_checks(8, 0)
        result = compute_dimension_result(checks, "output_quality")

        assert isinstance(result, DimensionResult)
        assert result.dimension == "output_quality"
        assert result.weight == DIMENSION_WEIGHTS["output_quality"]
        assert result.score == 5
        assert result.weighted_score == 5 * DIMENSION_WEIGHTS["output_quality"]
        assert result.checks_passed == 8
        assert result.checks_total == 8

    def test_partial_pass(self):
        checks = make_checks(5, 3)
        result = compute_dimension_result(checks, "output_quality")
        assert result.checks_passed == 5
        assert result.checks_total == 8
        assert result.score == 3

    def test_unknown_dimension_zero_weight(self):
        checks = make_checks(5, 0)
        result = compute_dimension_result(checks, "unknown_dim")
        assert result.weight == 0.0
        assert result.weighted_score == 0.0


# ---------------------------------------------------------------------------
# Tests: compute_total_score
# ---------------------------------------------------------------------------

class TestComputeTotalScore:
    """Tests for compute_total_score."""

    def test_sum_of_weighted_scores(self):
        dims = [
            DimensionResult("a", 0.5, [], 5, 2.5),
            DimensionResult("b", 0.3, [], 4, 1.2),
            DimensionResult("c", 0.2, [], 3, 0.6),
        ]
        assert compute_total_score(dims) == pytest.approx(4.3)

    def test_empty_dimensions(self):
        assert compute_total_score([]) == 0.0


# ---------------------------------------------------------------------------
# Tests: determine_decision
# ---------------------------------------------------------------------------

class TestDetermineDecision:
    """Tests for determine_decision."""

    def test_strong_pass(self):
        assert determine_decision(4.5) == "STRONG_PASS"
        assert determine_decision(4.0) == "STRONG_PASS"

    def test_pass(self):
        assert determine_decision(3.5) == "PASS"
        assert determine_decision(3.9) == "PASS"

    def test_weak_pass(self):
        assert determine_decision(3.0) == "WEAK_PASS"
        assert determine_decision(3.4) == "WEAK_PASS"

    def test_fail(self):
        assert determine_decision(2.9) == "FAIL"
        assert determine_decision(0.0) == "FAIL"
        assert determine_decision(1.5) == "FAIL"


# ---------------------------------------------------------------------------
# Tests: format_score_summary
# ---------------------------------------------------------------------------

class TestFormatScoreSummary:
    """Tests for format_score_summary."""

    def test_basic_format(self):
        dims = [
            DimensionResult("output_quality", 0.20, make_checks(8, 0), 5, 1.0),
            DimensionResult("integration_fit", 0.15, make_checks(5, 1), 4, 0.6),
        ]
        output = format_score_summary(dims, 1.6, "FAIL")

        assert "Scoring Summary" in output
        assert "Output Quality" in output
        assert "Integration Fit" in output
        assert "TOTAL" in output
        assert "FAIL" in output
        assert "1.60" in output
