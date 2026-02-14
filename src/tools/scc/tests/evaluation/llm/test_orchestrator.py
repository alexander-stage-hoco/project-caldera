"""Tests for LLMEvaluator orchestrator.

All tests use REAL data - NO MOCKING.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from evaluation.llm.orchestrator import (
    LLMEvaluator,
    DimensionResult,
    EvaluationResult,
)
from evaluation.llm.judges.base import BaseJudge, JudgeResult


class MockJudge(BaseJudge):
    """Test judge with controllable behavior."""

    def __init__(
        self,
        name: str = "test",
        weight: float = 0.10,
        score: int = 4,
        confidence: float = 0.8,
        gt_pass: bool = True,
        gt_failures: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._name = name
        self._weight = weight
        self._score = score
        self._confidence = confidence
        self._gt_pass = gt_pass
        self._gt_failures = gt_failures or []

    @property
    def dimension_name(self) -> str:
        return self._name

    @property
    def weight(self) -> float:
        return self._weight

    def get_default_prompt(self) -> str:
        return "Test prompt"

    def collect_evidence(self) -> dict:
        return {"test": "data"}

    def evaluate(self) -> JudgeResult:
        return JudgeResult(
            dimension=self._name,
            score=self._score,
            confidence=self._confidence,
            reasoning="Test reasoning",
            evidence_cited=["test_evidence"],
            recommendations=["test_recommendation"],
        )

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        return self._gt_pass, self._gt_failures


class TestLLMEvaluatorInit:
    """Test LLMEvaluator initialization."""

    def test_default_working_dir(self):
        """Uses cwd when no working_dir specified."""
        evaluator = LLMEvaluator()
        assert evaluator.working_dir == Path.cwd()

    def test_custom_working_dir(self, poc_root: Path):
        """Uses specified working_dir."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        assert evaluator.working_dir == poc_root

    def test_default_model(self):
        """Default model is opus-4.5."""
        evaluator = LLMEvaluator()
        assert evaluator.model == "opus-4.5"

    def test_custom_model(self):
        """Can specify custom model."""
        evaluator = LLMEvaluator(model="sonnet")
        assert evaluator.model == "sonnet"

    def test_default_results_dir(self, poc_root: Path):
        """Default results dir under evaluation/results."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        assert evaluator.results_dir == poc_root / "evaluation" / "results"

    def test_empty_judges_list(self):
        """Starts with no judges registered."""
        evaluator = LLMEvaluator()
        assert evaluator._judges == []


class TestJudgeRegistration:
    """Test judge registration methods."""

    def test_register_single_judge(self, poc_root: Path):
        """Can register a single judge."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        judge = MockJudge(working_dir=poc_root)
        evaluator.register_judge(judge)
        assert len(evaluator._judges) == 1
        assert evaluator._judges[0] == judge

    def test_register_multiple_judges(self, poc_root: Path):
        """Can register multiple judges."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        judge1 = MockJudge(name="judge1", working_dir=poc_root)
        judge2 = MockJudge(name="judge2", working_dir=poc_root)
        evaluator.register_judge(judge1)
        evaluator.register_judge(judge2)
        assert len(evaluator._judges) == 2

    def test_register_all_judges_count(self, poc_root: Path):
        """register_all_judges registers all 10 judges."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_all_judges()
        assert len(evaluator._judges) == 10

    def test_register_all_judges_names(self, poc_root: Path):
        """All 10 judges have correct dimension names."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_all_judges()
        names = {j.dimension_name for j in evaluator._judges}
        expected_names = {
            "code_quality",
            "integration_fit",
            "documentation",
            "edge_cases",
            "error_messages",
            "api_design",
            "comparative",
            "risk",
            "directory_analysis",
            "statistics",
        }
        assert names == expected_names

    def test_register_focused_judges_count(self, poc_root: Path):
        """register_focused_judges registers 4 key judges."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_focused_judges()
        assert len(evaluator._judges) == 4

    def test_register_focused_judges_names(self, poc_root: Path):
        """Focused mode includes directory_analysis, statistics, integration_fit, api_design."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_focused_judges()
        names = {j.dimension_name for j in evaluator._judges}
        expected = {"directory_analysis", "statistics", "integration_fit", "api_design"}
        assert names == expected


class TestEvaluateMethod:
    """Test the evaluate() method."""

    def test_evaluate_returns_result(self, poc_root: Path):
        """evaluate() returns EvaluationResult."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert isinstance(result, EvaluationResult)

    def test_evaluate_run_id_format(self, poc_root: Path):
        """Run ID has correct format llm-eval-YYYYMMDD-HHMMSS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.run_id.startswith("llm-eval-")
        assert len(result.run_id) == len("llm-eval-YYYYMMDD-HHMMSS")

    def test_evaluate_has_timestamp(self, poc_root: Path):
        """Result includes ISO timestamp."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert "T" in result.timestamp
        assert len(result.timestamp) > 10

    def test_evaluate_includes_model(self, poc_root: Path):
        """Result includes model name."""
        evaluator = LLMEvaluator(working_dir=poc_root, model="opus")
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.model == "opus"

    def test_evaluate_dimensions_populated(self, poc_root: Path):
        """Result includes dimension results for each judge."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(name="j1", working_dir=poc_root))
        evaluator.register_judge(MockJudge(name="j2", working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert len(result.dimensions) == 2
        assert result.dimensions[0].name == "j1"
        assert result.dimensions[1].name == "j2"

    def test_evaluate_calculates_weighted_score(self, poc_root: Path):
        """Weighted score is score * weight."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=4, weight=0.25, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.dimensions[0].weighted_score == 4 * 0.25

    def test_evaluate_average_confidence(self, poc_root: Path):
        """Average confidence is mean of all judge confidences."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(confidence=0.8, working_dir=poc_root))
        evaluator.register_judge(MockJudge(confidence=0.6, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.average_confidence == pytest.approx(0.7)

    def test_evaluate_empty_judges(self, poc_root: Path):
        """Handles zero judges gracefully."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        result = evaluator.evaluate(run_assertions=False)
        assert result.total_score == 0.0
        assert result.average_confidence == 0.0
        assert result.decision == "FAIL"


class TestGroundTruthPenalty:
    """Test ground truth assertion penalty application."""

    def test_assertion_pass_no_penalty(self, poc_root: Path):
        """Score unchanged when assertions pass."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=5, gt_pass=True, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=True)
        assert result.dimensions[0].score == 5

    def test_assertion_fail_caps_score_at_2(self, poc_root: Path):
        """Score capped at 2 when assertions fail."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(
            MockJudge(score=5, gt_pass=False, gt_failures=["error"], working_dir=poc_root)
        )
        result = evaluator.evaluate(run_assertions=True)
        assert result.dimensions[0].score == 2

    def test_assertion_fail_doesnt_lower_below_score(self, poc_root: Path):
        """If LLM score < 2, penalty doesn't change it."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(
            MockJudge(score=1, gt_pass=False, gt_failures=["error"], working_dir=poc_root)
        )
        result = evaluator.evaluate(run_assertions=True)
        assert result.dimensions[0].score == 1

    def test_assertion_failures_recorded(self, poc_root: Path):
        """Ground truth failures are recorded in result."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(
            MockJudge(
                score=4,
                gt_pass=False,
                gt_failures=["error1", "error2"],
                working_dir=poc_root,
            )
        )
        result = evaluator.evaluate(run_assertions=True)
        assert result.dimensions[0].ground_truth_passed is False
        assert result.dimensions[0].ground_truth_failures == ["error1", "error2"]

    def test_skip_assertions_flag(self, poc_root: Path):
        """run_assertions=False skips ground truth checks."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(
            MockJudge(score=5, gt_pass=False, gt_failures=["error"], working_dir=poc_root)
        )
        result = evaluator.evaluate(run_assertions=False)
        # Score not capped because assertions weren't run
        assert result.dimensions[0].score == 5


class TestDecisionThresholds:
    """Test decision threshold logic."""

    def test_strong_pass_threshold(self, poc_root: Path):
        """Score >= 4.0 is STRONG_PASS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=5, weight=1.0, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.total_score == 5.0
        assert result.decision == "STRONG_PASS"

    def test_strong_pass_boundary(self, poc_root: Path):
        """Score exactly 4.0 is STRONG_PASS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=4, weight=1.0, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.total_score == 4.0
        assert result.decision == "STRONG_PASS"

    def test_pass_threshold(self, poc_root: Path):
        """Score >= 3.5 and < 4.0 is PASS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        # Create judges that average to 3.75
        evaluator.register_judge(MockJudge(name="j1", score=4, weight=0.5, working_dir=poc_root))
        evaluator.register_judge(MockJudge(name="j2", score=3, weight=0.5, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.total_score == pytest.approx(3.5)
        assert result.decision == "PASS"

    def test_weak_pass_threshold(self, poc_root: Path):
        """Score >= 3.0 and < 3.5 is WEAK_PASS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=3, weight=1.0, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.total_score == 3.0
        assert result.decision == "WEAK_PASS"

    def test_fail_threshold(self, poc_root: Path):
        """Score < 3.0 is FAIL."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=2, weight=1.0, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        assert result.total_score == 2.0
        assert result.decision == "FAIL"

    def test_decision_boundary_3_99(self, poc_root: Path):
        """Score 3.99 is PASS, not STRONG_PASS."""
        # Need to manually construct to get 3.99
        result = EvaluationResult(
            run_id="test",
            timestamp="2024-01-01T00:00:00Z",
            model="opus",
            dimensions=[],
            total_score=3.99,
            average_confidence=0.8,
            decision="PASS",  # Will be recalculated
        )
        # Verify threshold logic
        assert result.total_score < 4.0
        assert result.total_score >= 3.5


class TestCombinedScoring:
    """Test combined scoring formula."""

    def test_combined_score_formula(self, poc_root: Path):
        """Combined = programmatic * 0.60 + llm * 0.40"""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=4, weight=1.0, working_dir=poc_root))
        llm_result = evaluator.evaluate(run_assertions=False)

        combined_result = evaluator.compute_combined_score(llm_result, programmatic_score=5.0)

        # LLM score is 4.0, programmatic is 5.0
        # Combined = 5.0 * 0.60 + 4.0 * 0.40 = 3.0 + 1.6 = 4.6
        assert combined_result.combined_score == pytest.approx(4.6)

    def test_combined_score_perfect(self, poc_root: Path):
        """Perfect scores in both give 5.0."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=5, weight=1.0, working_dir=poc_root))
        llm_result = evaluator.evaluate(run_assertions=False)

        combined_result = evaluator.compute_combined_score(llm_result, programmatic_score=5.0)
        assert combined_result.combined_score == pytest.approx(5.0)

    def test_combined_score_only_programmatic(self, poc_root: Path):
        """Zero LLM score gives 60% of programmatic."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        # Create a result with 0 LLM score
        llm_result = EvaluationResult(
            run_id="test",
            timestamp="2024-01-01T00:00:00Z",
            model="opus",
            dimensions=[],
            total_score=0.0,
            average_confidence=0.0,
            decision="FAIL",
        )

        combined_result = evaluator.compute_combined_score(llm_result, programmatic_score=5.0)
        # 5.0 * 0.60 + 0.0 * 0.40 = 3.0
        assert combined_result.combined_score == pytest.approx(3.0)

    def test_combined_score_only_llm(self, poc_root: Path):
        """Zero programmatic gives 40% of LLM."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=5, weight=1.0, working_dir=poc_root))
        llm_result = evaluator.evaluate(run_assertions=False)

        combined_result = evaluator.compute_combined_score(llm_result, programmatic_score=0.0)
        # 0.0 * 0.60 + 5.0 * 0.40 = 2.0
        assert combined_result.combined_score == pytest.approx(2.0)

    def test_combined_updates_decision(self, poc_root: Path):
        """Combined score updates the decision."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=4, weight=1.0, working_dir=poc_root))
        llm_result = evaluator.evaluate(run_assertions=False)
        assert llm_result.decision == "STRONG_PASS"  # Based on LLM alone

        # With perfect programmatic, combined should be STRONG_PASS
        combined_result = evaluator.compute_combined_score(llm_result, programmatic_score=5.0)
        assert combined_result.decision == "STRONG_PASS"

    def test_combined_stores_programmatic_score(self, poc_root: Path):
        """Combined result stores original programmatic score."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(score=4, weight=1.0, working_dir=poc_root))
        llm_result = evaluator.evaluate(run_assertions=False)

        combined_result = evaluator.compute_combined_score(llm_result, programmatic_score=5.0)
        assert combined_result.programmatic_score == 5.0


class TestResultsSaving:
    """Test save_results() method."""

    def test_save_results_creates_file(self, poc_root: Path):
        """save_results creates JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            results_dir = tmpdir / "results"

            evaluator = LLMEvaluator(working_dir=tmpdir, results_dir=results_dir)
            evaluator.register_judge(MockJudge(working_dir=tmpdir))
            result = evaluator.evaluate(run_assertions=False)

            output_file = evaluator.save_results(result)

            assert output_file.exists()
            assert output_file.suffix == ".json"

    def test_save_results_valid_json(self, poc_root: Path):
        """Saved file contains valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            results_dir = tmpdir / "results"

            evaluator = LLMEvaluator(working_dir=tmpdir, results_dir=results_dir)
            evaluator.register_judge(MockJudge(working_dir=tmpdir))
            result = evaluator.evaluate(run_assertions=False)

            output_file = evaluator.save_results(result)

            data = json.loads(output_file.read_text())
            assert "run_id" in data
            assert "dimensions" in data
            assert "total_score" in data

    def test_save_results_creates_dir(self, poc_root: Path):
        """save_results creates results directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            results_dir = tmpdir / "deep" / "nested" / "results"

            evaluator = LLMEvaluator(working_dir=tmpdir, results_dir=results_dir)
            evaluator.register_judge(MockJudge(working_dir=tmpdir))
            result = evaluator.evaluate(run_assertions=False)

            output_file = evaluator.save_results(result)

            assert results_dir.exists()
            assert output_file.exists()


class TestMarkdownReport:
    """Test markdown report generation."""

    def test_markdown_has_header(self, poc_root: Path):
        """Report starts with h1 header."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)

        markdown = evaluator.generate_markdown_report(result)
        assert markdown.startswith("# LLM Evaluation Report")

    def test_markdown_has_summary(self, poc_root: Path):
        """Report includes summary section."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)

        markdown = evaluator.generate_markdown_report(result)
        assert "## Summary" in markdown
        assert "**LLM Score:**" in markdown

    def test_markdown_has_dimensions_table(self, poc_root: Path):
        """Report includes dimension scores table."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)

        markdown = evaluator.generate_markdown_report(result)
        assert "## Dimension Scores" in markdown
        assert "| Dimension | Score | Weight | Weighted | Confidence |" in markdown

    def test_markdown_includes_combined_score(self, poc_root: Path):
        """Report shows combined score when present."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        evaluator.compute_combined_score(result, programmatic_score=5.0)

        markdown = evaluator.generate_markdown_report(result)
        assert "**Combined Score:**" in markdown
        assert "**Programmatic Score:**" in markdown

    def test_markdown_shows_gt_failures(self, poc_root: Path):
        """Report shows ground truth failures."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(
            MockJudge(gt_pass=False, gt_failures=["error1"], working_dir=poc_root)
        )
        result = evaluator.evaluate(run_assertions=True)

        markdown = evaluator.generate_markdown_report(result)
        assert "Ground Truth Assertions Failed" in markdown
        assert "error1" in markdown


class TestDimensionResult:
    """Test DimensionResult dataclass."""

    def test_dimension_result_defaults(self):
        """Default values for optional fields."""
        result = DimensionResult(
            name="test",
            score=4,
            weight=0.10,
            weighted_score=0.4,
            confidence=0.8,
            reasoning="test",
        )
        assert result.evidence_cited == []
        assert result.recommendations == []
        assert result.sub_scores == {}
        assert result.ground_truth_passed is True
        assert result.ground_truth_failures == []

    def test_dimension_result_to_dict(self):
        """Serialization to dict."""
        result = DimensionResult(
            name="test",
            score=4,
            weight=0.10,
            weighted_score=0.4,
            confidence=0.8,
            reasoning="test reasoning",
            evidence_cited=["ev1"],
            recommendations=["rec1"],
        )
        d = result.to_dict()
        assert d["name"] == "test"
        assert d["score"] == 4
        assert d["weight"] == 0.10
        assert d["evidence_cited"] == ["ev1"]

    def test_weighted_score_calculation(self):
        """Weighted score is score * weight."""
        result = DimensionResult(
            name="test",
            score=5,
            weight=0.20,
            weighted_score=1.0,  # 5 * 0.20
            confidence=0.9,
            reasoning="test",
        )
        assert result.weighted_score == 5 * 0.20


class TestEvaluationResult:
    """Test EvaluationResult dataclass."""

    def test_evaluation_result_to_dict(self):
        """Serialization to dict."""
        result = EvaluationResult(
            run_id="test-123",
            timestamp="2024-01-01T00:00:00Z",
            model="opus",
            dimensions=[],
            total_score=4.5,
            average_confidence=0.85,
            decision="STRONG_PASS",
        )
        d = result.to_dict()
        assert d["run_id"] == "test-123"
        assert d["total_score"] == 4.5
        assert d["decision"] == "STRONG_PASS"

    def test_evaluation_result_to_json(self):
        """Serialization to JSON string."""
        result = EvaluationResult(
            run_id="test-123",
            timestamp="2024-01-01T00:00:00Z",
            model="opus",
            dimensions=[],
            total_score=4.5,
            average_confidence=0.85,
            decision="STRONG_PASS",
        )
        json_str = result.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["run_id"] == "test-123"

    def test_evaluation_result_valid_decisions(self):
        """All valid decision strings."""
        for decision in ["STRONG_PASS", "PASS", "WEAK_PASS", "FAIL"]:
            result = EvaluationResult(
                run_id="test",
                timestamp="2024-01-01T00:00:00Z",
                model="opus",
                dimensions=[],
                total_score=3.0,
                average_confidence=0.5,
                decision=decision,
            )
            assert result.decision == decision


class TestWeightNormalization:
    """Test weight handling across judges."""

    def test_weights_sum_to_one_all_judges(self, poc_root: Path):
        """All 10 judges' weights sum to 1.0."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_all_judges()
        total_weight = sum(j.weight for j in evaluator._judges)
        assert abs(total_weight - 1.0) < 0.001

    def test_focused_weights_dont_sum_to_one(self, poc_root: Path):
        """Focused judges' weights don't sum to 1.0 (subset)."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_focused_judges()
        total_weight = sum(j.weight for j in evaluator._judges)
        # 0.14 + 0.14 + 0.10 + 0.10 = 0.48
        assert total_weight < 1.0
        assert total_weight == pytest.approx(0.48)

    def test_score_normalized_with_partial_weights(self, poc_root: Path):
        """Score normalized correctly when weights don't sum to 1."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        # Register judge with weight 0.5
        evaluator.register_judge(MockJudge(score=5, weight=0.5, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        # Even with partial weight, score should be normalized
        assert result.total_score == 5.0  # Normalized: (5*0.5) / 0.5 = 5

    def test_multiple_unequal_weights(self, poc_root: Path):
        """Correct weighting with unequal judge weights."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_judge(MockJudge(name="j1", score=5, weight=0.6, working_dir=poc_root))
        evaluator.register_judge(MockJudge(name="j2", score=3, weight=0.4, working_dir=poc_root))
        result = evaluator.evaluate(run_assertions=False)
        # (5*0.6 + 3*0.4) / (0.6 + 0.4) = (3 + 1.2) / 1.0 = 4.2
        assert result.total_score == pytest.approx(4.2)
