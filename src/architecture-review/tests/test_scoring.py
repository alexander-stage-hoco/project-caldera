"""Tests for scoring logic."""

from __future__ import annotations

import pytest

from models import DimensionResult, Finding
from scoring import advisory_status, compute_overall, score_dimension, status_from_score


def _f(severity: str) -> Finding:
    """Create a finding with given severity."""
    return Finding(severity=severity, rule_id="TEST", message="test")


class TestScoreDimension:
    def test_no_findings_returns_5(self) -> None:
        assert score_dimension([]) == 5

    def test_info_only_few_returns_4(self) -> None:
        assert score_dimension([_f("info")]) == 4
        assert score_dimension([_f("info")] * 3) == 4

    def test_info_only_many_returns_3(self) -> None:
        assert score_dimension([_f("info")] * 4) == 3
        assert score_dimension([_f("info")] * 10) == 3

    def test_warnings_few_returns_3(self) -> None:
        assert score_dimension([_f("warning")]) == 3
        assert score_dimension([_f("warning")] * 3) == 3

    def test_warnings_many_returns_2(self) -> None:
        assert score_dimension([_f("warning")] * 4) == 2
        assert score_dimension([_f("warning")] * 10) == 2

    def test_errors_few_returns_2(self) -> None:
        assert score_dimension([_f("error")]) == 2
        assert score_dimension([_f("error")] * 2) == 2

    def test_errors_many_returns_1(self) -> None:
        assert score_dimension([_f("error")] * 3) == 1
        assert score_dimension([_f("error")] * 10) == 1

    def test_mixed_severities(self) -> None:
        # 1 error + some info = score 2
        assert score_dimension([_f("error"), _f("info"), _f("info")]) == 2


class TestStatusFromScore:
    def test_pass(self) -> None:
        assert status_from_score(5) == "pass"
        assert status_from_score(4) == "pass"

    def test_warn(self) -> None:
        assert status_from_score(3) == "warn"

    def test_fail(self) -> None:
        assert status_from_score(2) == "fail"
        assert status_from_score(1) == "fail"


class TestComputeOverall:
    def test_weighted_average(self) -> None:
        dims = [
            DimensionResult(dimension="d1", weight=0.5, status="pass", score=5),
            DimensionResult(dimension="d2", weight=0.5, status="fail", score=1),
        ]
        score, status = compute_overall(dims)
        assert score == 3.0
        assert status == "WEAK_PASS"

    def test_normalizes_weights(self) -> None:
        dims = [
            DimensionResult(dimension="d1", weight=0.2, status="pass", score=5),
            DimensionResult(dimension="d2", weight=0.2, status="pass", score=5),
        ]
        score, status = compute_overall(dims)
        assert score == 5.0
        assert status == "STRONG_PASS"

    def test_empty_dimensions(self) -> None:
        score, status = compute_overall([])
        assert score == 5.0
        assert status == "STRONG_PASS"

    def test_single_dimension(self) -> None:
        dims = [DimensionResult(dimension="d1", weight=0.15, status="warn", score=3)]
        score, status = compute_overall(dims)
        assert score == 3.0
        assert status == "WEAK_PASS"


class TestAdvisoryStatus:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (5.0, "STRONG_PASS"),
            (4.5, "STRONG_PASS"),
            (4.0, "STRONG_PASS"),
            (3.9, "PASS"),
            (3.5, "PASS"),
            (3.4, "WEAK_PASS"),
            (3.0, "WEAK_PASS"),
            (2.9, "NEEDS_WORK"),
            (1.0, "NEEDS_WORK"),
        ],
    )
    def test_thresholds(self, score: float, expected: str) -> None:
        assert advisory_status(score) == expected
