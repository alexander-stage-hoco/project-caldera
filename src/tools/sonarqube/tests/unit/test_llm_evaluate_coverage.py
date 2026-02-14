"""Tests targeting uncovered paths in llm_evaluate.py for coverage improvement."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.llm_evaluate import (
    LLMEvaluationReport,
    calculate_combined_score,
    set_color_enabled,
    print_llm_report,
)


class TestLLMEvaluationReport:
    """Tests for the LLM evaluation report class."""

    def _make_result(self, dimension: str, score: float, confidence: float) -> MagicMock:
        r = MagicMock()
        r.dimension = dimension
        r.score = score
        r.confidence = confidence
        r.to_dict.return_value = {
            "dimension": dimension,
            "score": score,
            "confidence": confidence,
        }
        return r

    def test_weighted_score_computation(self) -> None:
        results = [
            self._make_result("issue_accuracy", 4.5, 0.9),
            self._make_result("coverage_completeness", 3.0, 0.8),
            self._make_result("actionability", 4.0, 0.85),
        ]
        report = LLMEvaluationReport(
            timestamp="2025-01-01T00:00:00Z",
            analysis_path="/tmp/test.json",
            results=results,
        )
        # Weighted: 4.5*0.35 + 3.0*0.25 + 4.0*0.20 = 1.575 + 0.75 + 0.80 = 3.125
        # Total weight: 0.35 + 0.25 + 0.20 = 0.80
        # Result: 3.125 / 0.80 = 3.90625
        assert 3.5 < report.weighted_score < 4.5

    def test_avg_confidence(self) -> None:
        results = [
            self._make_result("issue_accuracy", 4.0, 0.9),
            self._make_result("coverage_completeness", 3.0, 0.8),
        ]
        report = LLMEvaluationReport(
            timestamp="t", analysis_path="a", results=results,
        )
        assert report.avg_confidence == pytest.approx(0.85)

    def test_empty_results(self) -> None:
        report = LLMEvaluationReport(
            timestamp="t", analysis_path="a", results=[],
        )
        assert report.weighted_score == 0.0
        assert report.avg_confidence == 0.0

    def test_to_dict(self) -> None:
        results = [self._make_result("issue_accuracy", 4.0, 0.9)]
        report = LLMEvaluationReport(
            timestamp="2025-01-01", analysis_path="/tmp/test",
            results=results,
        )
        d = report.to_dict()
        assert d["summary"]["dimension_count"] == 1
        assert "weighted_score" in d["summary"]


class TestCalculateCombinedScore:
    """Tests for combined programmatic + LLM scoring."""

    def test_strong_pass(self) -> None:
        result = calculate_combined_score(
            programmatic_score=0.9,  # -> 4.6 on 1-5
            llm_score=4.5,
        )
        assert result["decision"] == "STRONG_PASS"
        assert result["combined_score"] > 4.0

    def test_pass(self) -> None:
        result = calculate_combined_score(
            programmatic_score=0.7,  # -> 3.8 on 1-5
            llm_score=3.0,
        )
        # 3.8*0.6 + 3.0*0.4 = 2.28 + 1.2 = 3.48
        assert result["decision"] in ("PASS", "WEAK_PASS")

    def test_weak_pass(self) -> None:
        result = calculate_combined_score(
            programmatic_score=0.6,  # -> 3.4 on 1-5
            llm_score=2.5,
        )
        # 3.4*0.6 + 2.5*0.4 = 2.04 + 1.0 = 3.04
        assert result["decision"] == "WEAK_PASS"

    def test_fail(self) -> None:
        result = calculate_combined_score(
            programmatic_score=0.3,  # -> 2.2 on 1-5
            llm_score=2.0,
        )
        # 2.2*0.6 + 2.0*0.4 = 1.32 + 0.8 = 2.12
        assert result["decision"] == "FAIL"
        assert result["combined_score"] < 3.0

    def test_already_on_1_5_scale(self) -> None:
        result = calculate_combined_score(
            programmatic_score=4.0,  # Already 1-5
            llm_score=4.0,
        )
        # 4.0*0.6 + 4.0*0.4 = 4.0
        assert result["combined_score"] == 4.0
        assert result["decision"] == "STRONG_PASS"


class TestPrintLlmReport:
    """Tests for console output."""

    def test_print_with_results(self, capsys) -> None:
        set_color_enabled(False)
        r = MagicMock()
        r.dimension = "issue_accuracy"
        r.score = 4.5
        r.confidence = 0.9
        r.reasoning = "Good results"
        r.evidence = []
        report = LLMEvaluationReport(
            timestamp="2025-01-01", analysis_path="/tmp/test",
            results=[r],
        )
        print_llm_report(report)
        captured = capsys.readouterr()
        assert "LLM EVALUATION" in captured.out

    def test_print_empty_report(self, capsys) -> None:
        set_color_enabled(False)
        report = LLMEvaluationReport(
            timestamp="2025-01-01", analysis_path="/tmp/test",
            results=[],
        )
        print_llm_report(report)
        captured = capsys.readouterr()
        assert "LLM" in captured.out
