"""Unit tests for LLM judge infrastructure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from evaluation.llm.judges.base import BaseJudge, JudgeResult
from evaluation.llm.judges import (
    SmellAccuracyJudge,
    RuleCoverageJudge,
    FalsePositiveRateJudge,
    ActionabilityJudge,
)


class TestJudgeResult:
    """Tests for JudgeResult dataclass."""

    def test_create_judge_result(self):
        """Test creating a JudgeResult with all fields."""
        result = JudgeResult(
            dimension="smell_accuracy",
            score=4,
            confidence=0.85,
            reasoning="Good detection with minor issues",
            evidence_cited=["file1.py:10", "file2.py:25"],
            recommendations=["Add more rules for async patterns"],
            sub_scores={"true_positives": 4, "category_accuracy": 5},
            raw_response="full response text",
        )

        assert result.dimension == "smell_accuracy"
        assert result.score == 4
        assert result.confidence == 0.85
        assert len(result.evidence_cited) == 2
        assert len(result.recommendations) == 1
        assert result.sub_scores["true_positives"] == 4

    def test_judge_result_to_dict(self):
        """Test serialization to dictionary."""
        result = JudgeResult(
            dimension="rule_coverage",
            score=3,
            confidence=0.7,
            reasoning="Moderate coverage",
        )

        data = result.to_dict()

        assert data["dimension"] == "rule_coverage"
        assert data["score"] == 3
        assert data["confidence"] == 0.7
        assert data["reasoning"] == "Moderate coverage"
        assert "evidence_cited" in data
        assert "recommendations" in data

    def test_judge_result_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "dimension": "actionability",
            "score": 5,
            "confidence": 0.95,
            "reasoning": "Excellent actionability",
            "evidence_cited": ["clear messages"],
            "recommendations": [],
            "sub_scores": {"message_clarity": 5},
            "raw_response": "response",
        }

        result = JudgeResult.from_dict(data)

        assert result.dimension == "actionability"
        assert result.score == 5
        assert result.confidence == 0.95
        assert result.sub_scores["message_clarity"] == 5

    def test_judge_result_from_dict_with_missing_fields(self):
        """Test deserialization handles missing fields gracefully."""
        data = {"score": 3}

        result = JudgeResult.from_dict(data)

        assert result.dimension == "unknown"
        assert result.score == 3
        assert result.confidence == 0.0
        assert result.reasoning == ""
        assert result.evidence_cited == []

    def test_judge_result_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = JudgeResult(
            dimension="false_positive_rate",
            score=4,
            confidence=0.8,
            reasoning="Low FP rate",
            evidence_cited=["clean files passed"],
            recommendations=["improve context awareness"],
            sub_scores={"clean_file_precision": 5, "severity_calibration": 3},
            raw_response="original response",
        )

        data = original.to_dict()
        restored = JudgeResult.from_dict(data)

        assert restored.dimension == original.dimension
        assert restored.score == original.score
        assert restored.confidence == original.confidence
        assert restored.sub_scores == original.sub_scores


class TestBaseJudge:
    """Tests for BaseJudge class methods."""

    @pytest.fixture
    def temp_working_dir(self, tmp_path: Path) -> Path:
        """Create a temporary working directory with analysis output."""
        # Create output directory
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)

        # Create sample analysis file
        analysis = {
            "files": [
                {
                    "path": "src/main.py",
                    "language": "python",
                    "smell_count": 2,
                    "smells": [
                        {
                            "rule_id": "DD-D1-EMPTY-CATCH-python",
                            "dd_smell_id": "D1_EMPTY_CATCH",
                            "dd_category": "error_handling",
                            "severity": "WARNING",
                            "line_start": 10,
                            "line_end": 12,
                            "message": "Empty catch block detected",
                        },
                        {
                            "rule_id": "DD-E2-ASYNC-VOID-python",
                            "dd_smell_id": "E2_ASYNC_VOID",
                            "dd_category": "async_concurrency",
                            "severity": "WARNING",
                            "line_start": 25,
                            "line_end": 30,
                            "message": "Async method returns void",
                        },
                    ],
                }
            ],
            "summary": {"total_smells": 2, "total_files": 1, "files_with_smells": 1},
        }
        (output_dir / "test_repo.json").write_text(json.dumps(analysis))

        # Create ground truth directory
        gt_dir = tmp_path / "evaluation" / "ground-truth"
        gt_dir.mkdir(parents=True)

        gt = {
            "language": "python",
            "files": {
                "main.py": {
                    "expected_smells": ["D1_EMPTY_CATCH", "E2_ASYNC_VOID"],
                    "expected_count_min": 1,
                    "expected_count_max": 5,
                }
            },
        }
        (gt_dir / "python.json").write_text(json.dumps(gt))

        return tmp_path

    @pytest.fixture
    def smell_accuracy_judge(self, temp_working_dir: Path) -> SmellAccuracyJudge:
        """Create a SmellAccuracyJudge with temp working dir."""
        return SmellAccuracyJudge(
            working_dir=temp_working_dir,
            output_dir=temp_working_dir / "output" / "runs",
        )

    def test_load_prompt_template_from_file(self, smell_accuracy_judge: SmellAccuracyJudge):
        """Test loading prompt template from file."""
        # The prompt file should exist
        prompt_file = smell_accuracy_judge.prompt_file
        assert prompt_file.exists(), f"Prompt file not found at {prompt_file}"

        template = smell_accuracy_judge.load_prompt_template()

        assert "{{ evidence }}" in template
        assert len(template) > 100

    def test_load_prompt_template_uses_default_if_missing(self, tmp_path: Path):
        """Test that default prompt is used when file is missing."""
        # Create a judge and test that get_default_prompt returns a valid template
        judge = SmellAccuracyJudge(
            working_dir=tmp_path,
            output_dir=tmp_path / "output",
        )

        # Get the default prompt directly
        default_template = judge.get_default_prompt()

        # Verify the default prompt is valid
        assert "smell" in default_template.lower() or "accuracy" in default_template.lower()
        assert len(default_template) > 50
        assert "{{ " in default_template or "{{" in default_template  # Has placeholders

    def test_build_prompt_substitutes_evidence(self, smell_accuracy_judge: SmellAccuracyJudge):
        """Test that evidence is correctly substituted into prompt."""
        evidence = {
            "sample_smells": [{"rule_id": "test-rule", "severity": "WARNING"}],
            "total_smells": 5,
            "interpretation_guidance": "Test guidance",
            "synthetic_baseline": "Test baseline",
            "evaluation_mode": "synthetic",
        }

        prompt = smell_accuracy_judge.build_prompt(evidence)

        assert "test-rule" in prompt
        assert "WARNING" in prompt
        assert "{{ evidence }}" not in prompt

    def test_parse_response_extracts_json(self, smell_accuracy_judge: SmellAccuracyJudge):
        """Test parsing valid JSON response."""
        response = '''Here is my analysis:

{
  "dimension": "smell_accuracy",
  "score": 4,
  "confidence": 0.85,
  "reasoning": "Good smell detection accuracy",
  "evidence_cited": ["file1.py"],
  "recommendations": ["Add more rules"],
  "sub_scores": {"true_positives": 4}
}

That concludes my evaluation.'''

        result = smell_accuracy_judge.parse_response(response)

        assert result.score == 4
        assert result.confidence == 0.85
        assert result.dimension == "smell_accuracy"
        assert "Good smell detection" in result.reasoning

    def test_parse_response_handles_malformed_json(self, smell_accuracy_judge: SmellAccuracyJudge):
        """Test parsing handles malformed JSON gracefully."""
        # Use the pattern the fallback actually looks for: "score: X" or "score:X"
        response = "Based on analysis, score: 4 out of 5. Overall good results."

        result = smell_accuracy_judge.parse_response(response)

        # Should use fallback score extraction
        assert result.score == 4
        assert result.confidence == 0.5  # Default confidence
        assert result.dimension == "smell_accuracy"

    def test_parse_response_extracts_score_from_text(self, smell_accuracy_judge: SmellAccuracyJudge):
        """Test fallback score extraction from text."""
        response = "Based on my analysis, I give this a score: 3 overall."

        result = smell_accuracy_judge.parse_response(response)

        assert result.score == 3

    def test_collect_evidence_returns_dict(self, smell_accuracy_judge: SmellAccuracyJudge):
        """Test that collect_evidence returns properly structured data."""
        evidence = smell_accuracy_judge.collect_evidence()

        assert isinstance(evidence, dict)
        assert "sample_smells" in evidence
        assert "total_smells" in evidence


class TestSmellAccuracyJudge:
    """Tests for SmellAccuracyJudge specific functionality."""

    def test_dimension_name(self):
        """Test dimension name is correct."""
        judge = SmellAccuracyJudge()
        assert judge.dimension_name == "smell_accuracy"

    def test_weight(self):
        """Test weight is correct."""
        judge = SmellAccuracyJudge()
        assert judge.weight == 0.35


class TestRuleCoverageJudge:
    """Tests for RuleCoverageJudge specific functionality."""

    def test_dimension_name(self):
        """Test dimension name is correct."""
        judge = RuleCoverageJudge()
        assert judge.dimension_name == "rule_coverage"

    def test_weight(self):
        """Test weight is correct."""
        judge = RuleCoverageJudge()
        assert judge.weight == 0.25


class TestFalsePositiveRateJudge:
    """Tests for FalsePositiveRateJudge specific functionality."""

    def test_dimension_name(self):
        """Test dimension name is correct."""
        judge = FalsePositiveRateJudge()
        assert judge.dimension_name == "false_positive_rate"

    def test_weight(self):
        """Test weight is correct."""
        judge = FalsePositiveRateJudge()
        assert judge.weight == 0.20


class TestActionabilityJudge:
    """Tests for ActionabilityJudge specific functionality."""

    def test_dimension_name(self):
        """Test dimension name is correct."""
        judge = ActionabilityJudge()
        assert judge.dimension_name == "actionability"

    def test_weight(self):
        """Test weight is correct."""
        judge = ActionabilityJudge()
        assert judge.weight == 0.20


class TestJudgeWeights:
    """Tests to verify judge weights sum to 1.0."""

    def test_all_weights_sum_to_one(self):
        """Verify all judge weights sum to 1.0."""
        judges = [
            SmellAccuracyJudge(),
            RuleCoverageJudge(),
            FalsePositiveRateJudge(),
            ActionabilityJudge(),
        ]

        total_weight = sum(j.weight for j in judges)

        assert total_weight == pytest.approx(1.0)


class TestInvokeClaude:
    """Tests for Claude invocation via LLMClient."""

    def test_invoke_claude_uses_llm_client(self):
        """Test that invoke_claude delegates to _llm_client.invoke()."""
        judge = SmellAccuracyJudge()
        judge._llm_client = MagicMock()
        judge._llm_client.invoke.return_value = "LLM response"
        judge._llm_client.is_error_response.return_value = False
        judge._logger = None

        result = judge.invoke_claude("test prompt")

        assert result == "LLM response"
        judge._llm_client.invoke.assert_called_once_with("test prompt")

    def test_invoke_claude_handles_error_response(self):
        """Test that invoke_claude handles error responses from LLMClient."""
        judge = SmellAccuracyJudge()
        judge._llm_client = MagicMock()
        judge._llm_client.invoke.return_value = "Error: connection failed"
        judge._llm_client.is_error_response.return_value = True
        judge._llm_client.is_timeout_error.return_value = False
        judge._logger = None

        result = judge.invoke_claude("test prompt")

        assert result == "Error: connection failed"

    def test_invoke_claude_handles_timeout_error(self):
        """Test that invoke_claude handles timeout errors from LLMClient."""
        judge = SmellAccuracyJudge()
        judge._llm_client = MagicMock()
        judge._llm_client.invoke.return_value = "Error: timed out after 120s"
        judge._llm_client.is_error_response.return_value = True
        judge._llm_client.is_timeout_error.return_value = True
        judge._logger = None

        result = judge.invoke_claude("test prompt")

        assert "timed out" in result.lower()
