"""Tests for scripts/llm_evaluate.py - LLM evaluation report and combined scoring.

Covers:
- LLMEvaluationReport properties (weighted_score, avg_confidence, decision, to_dict)
- calculate_combined_score
- Color helpers (c, set_color_enabled)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

# llm_evaluate.py uses relative-style imports from evaluation.llm (via sys.path manipulation),
# so we import through the scripts package.
_tool_root = str(Path(__file__).parent.parent.parent)
if _tool_root not in sys.path:
    sys.path.insert(0, _tool_root)

from scripts.llm_evaluate import (
    LLMEvaluationReport,
    calculate_combined_score,
    c as llm_c,
    set_color_enabled as llm_set_color_enabled,
    Colors,
)


# Build JudgeResult-like objects for testing
@dataclass
class MockJudgeResult:
    dimension: str
    score: int
    confidence: float
    reasoning: str = "test reasoning"
    evidence_cited: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    sub_scores: dict = field(default_factory=dict)
    raw_response: str = ""

    def to_dict(self):
        return {
            "dimension": self.dimension,
            "score": self.score,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence_cited": self.evidence_cited,
            "recommendations": self.recommendations,
            "sub_scores": self.sub_scores,
        }


# ===========================================================================
# LLMEvaluationReport
# ===========================================================================

class TestLLMEvaluationReport:
    def _make_report(self, results=None) -> LLMEvaluationReport:
        if results is None:
            results = [
                MockJudgeResult(dimension="smell_accuracy", score=4, confidence=0.9),
                MockJudgeResult(dimension="rule_coverage", score=3, confidence=0.8),
                MockJudgeResult(dimension="false_positive_rate", score=5, confidence=0.95),
                MockJudgeResult(dimension="actionability", score=4, confidence=0.85),
            ]
        return LLMEvaluationReport(
            timestamp="2026-01-01T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            results=results,
            model="haiku",
        )

    def test_weighted_score(self):
        report = self._make_report()
        # Expected: 4*0.35 + 3*0.25 + 5*0.20 + 4*0.20 = 1.4+0.75+1.0+0.8 = 3.95
        assert abs(report.weighted_score - 3.95) < 0.01

    def test_weighted_score_empty(self):
        report = self._make_report(results=[])
        assert report.weighted_score == 0.0

    def test_avg_confidence(self):
        report = self._make_report()
        expected = (0.9 + 0.8 + 0.95 + 0.85) / 4
        assert abs(report.avg_confidence - expected) < 0.001

    def test_avg_confidence_empty(self):
        report = self._make_report(results=[])
        assert report.avg_confidence == 0.0

    def test_decision_strong_pass(self):
        results = [MockJudgeResult(dimension="smell_accuracy", score=5, confidence=0.9)]
        report = self._make_report(results=results)
        assert report.decision == "STRONG_PASS"

    def test_decision_pass(self):
        results = [
            MockJudgeResult(dimension="smell_accuracy", score=4, confidence=0.9),
            MockJudgeResult(dimension="rule_coverage", score=3, confidence=0.8),
        ]
        report = self._make_report(results=results)
        # 4*0.35 + 3*0.25 = 1.4+0.75=2.15, total_weight=0.6, weighted=2.15/0.6=3.583
        assert report.decision == "PASS"

    def test_decision_weak_pass(self):
        results = [
            MockJudgeResult(dimension="smell_accuracy", score=3, confidence=0.7),
            MockJudgeResult(dimension="rule_coverage", score=3, confidence=0.7),
        ]
        report = self._make_report(results=results)
        assert report.decision == "WEAK_PASS"

    def test_decision_fail(self):
        results = [
            MockJudgeResult(dimension="smell_accuracy", score=1, confidence=0.5),
            MockJudgeResult(dimension="rule_coverage", score=2, confidence=0.5),
        ]
        report = self._make_report(results=results)
        assert report.decision == "FAIL"

    def test_to_dict_structure(self):
        report = self._make_report()
        d = report.to_dict()
        assert d["timestamp"] == "2026-01-01T00:00:00Z"
        assert d["model"] == "haiku"
        assert "decision" in d
        assert "score" in d
        assert "dimensions" in d
        assert len(d["dimensions"]) == 4
        assert "summary" in d
        assert d["summary"]["dimension_count"] == 4

    def test_to_dict_programmatic_input(self):
        report = self._make_report()
        report.programmatic_input = {"score": 0.85, "decision": "PASS"}
        d = report.to_dict()
        assert d["programmatic_input"]["score"] == 0.85

    def test_get_weight_default(self):
        report = self._make_report()
        # Unknown dimension should return 0.25
        assert report._get_weight("unknown_dimension") == 0.25

    def test_get_weight_known(self):
        report = self._make_report()
        assert report._get_weight("smell_accuracy") == 0.35
        assert report._get_weight("rule_coverage") == 0.25
        assert report._get_weight("false_positive_rate") == 0.20
        assert report._get_weight("actionability") == 0.20


# ===========================================================================
# calculate_combined_score
# ===========================================================================

class TestCalculateCombinedScore:
    def test_basic_calculation(self):
        result = calculate_combined_score(
            programmatic_score=0.80,
            llm_score=4.0,
        )
        # programmatic normalized: 0.80*4+1=4.2, combined=4.2*0.6+4.0*0.4=2.52+1.6=4.12
        assert abs(result["combined_score"] - 4.12) < 0.01
        assert result["decision"] == "STRONG_PASS"

    def test_programmatic_already_on_5_scale(self):
        result = calculate_combined_score(
            programmatic_score=3.5,  # Already on 1-5 scale
            llm_score=3.5,
        )
        # programmatic_normalized=3.5, combined=3.5*0.6+3.5*0.4=2.1+1.4=3.5
        assert abs(result["combined_score"] - 3.5) < 0.01
        assert result["decision"] == "PASS"

    def test_low_scores_fail(self):
        result = calculate_combined_score(
            programmatic_score=0.20,
            llm_score=1.5,
        )
        # programmatic normalized: 0.2*4+1=1.8, combined=1.8*0.6+1.5*0.4=1.08+0.6=1.68
        assert result["decision"] == "FAIL"
        assert result["combined_score"] < 3.0

    def test_weak_pass_boundary(self):
        result = calculate_combined_score(
            programmatic_score=0.50,
            llm_score=3.0,
        )
        # programmatic normalized: 0.5*4+1=3.0, combined=3.0*0.6+3.0*0.4=1.8+1.2=3.0
        assert result["decision"] == "WEAK_PASS"

    def test_perfect_scores(self):
        result = calculate_combined_score(
            programmatic_score=1.0,
            llm_score=5.0,
        )
        # programmatic normalized: 1.0*4+1=5.0, combined=5.0*0.6+5.0*0.4=5.0
        assert result["combined_score"] == 5.0
        assert result["decision"] == "STRONG_PASS"

    def test_custom_weights(self):
        result = calculate_combined_score(
            programmatic_score=0.80,
            llm_score=4.0,
            programmatic_weight=0.50,
            llm_weight=0.50,
        )
        # programmatic normalized: 4.2, combined=4.2*0.5+4.0*0.5=2.1+2.0=4.1
        assert abs(result["combined_score"] - 4.10) < 0.01

    def test_result_has_all_fields(self):
        result = calculate_combined_score(
            programmatic_score=0.80,
            llm_score=4.0,
        )
        assert "combined_score" in result
        assert "programmatic_contribution" in result
        assert "llm_contribution" in result
        assert "programmatic_normalized" in result
        assert "llm_score" in result
        assert "decision" in result


# ===========================================================================
# Color helpers
# ===========================================================================

class TestLLMEvaluateColors:
    def test_c_with_color(self):
        llm_set_color_enabled(True)
        result = llm_c("hello", Colors.GREEN)
        assert "hello" in result
        assert "\033[" in result

    def test_c_without_color(self):
        llm_set_color_enabled(False)
        result = llm_c("hello", Colors.GREEN)
        assert result == "hello"
        llm_set_color_enabled(True)
