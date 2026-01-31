"""Tests for shared BaseJudge implementation.

Tests cover:
- JudgeResult dataclass serialization
- BaseJudge.validate_claude_cli()
- invoke_claude() with mocked subprocess
- Heuristic fallback when use_llm=False
- parse_response() JSON extraction
- Error handling for malformed responses
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add src/shared to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.evaluation.base_judge import BaseJudge, JudgeResult


class TestJudgeResult:
    """Tests for JudgeResult dataclass."""

    def test_create_with_defaults(self):
        """JudgeResult should create with default values for optional fields."""
        result = JudgeResult(
            dimension="accuracy",
            score=4,
            confidence=0.85,
            reasoning="Test reasoning",
        )

        assert result.dimension == "accuracy"
        assert result.score == 4
        assert result.confidence == 0.85
        assert result.reasoning == "Test reasoning"
        assert result.evidence_cited == []
        assert result.recommendations == []
        assert result.sub_scores == {}
        assert result.raw_response == ""

    def test_create_with_all_fields(self):
        """JudgeResult should accept all fields."""
        result = JudgeResult(
            dimension="coverage",
            score=5,
            confidence=0.95,
            reasoning="Excellent coverage",
            evidence_cited=["File A had 100% coverage"],
            recommendations=["Consider edge cases"],
            sub_scores={"line_coverage": 5, "branch_coverage": 4},
            raw_response='{"score": 5}',
        )

        assert result.dimension == "coverage"
        assert result.score == 5
        assert len(result.evidence_cited) == 1
        assert len(result.recommendations) == 1
        assert result.sub_scores["line_coverage"] == 5
        assert result.raw_response == '{"score": 5}'

    def test_to_dict(self):
        """JudgeResult should serialize to dictionary."""
        result = JudgeResult(
            dimension="accuracy",
            score=4,
            confidence=0.85,
            reasoning="Test reasoning",
            evidence_cited=["evidence 1"],
            recommendations=["rec 1"],
            sub_scores={"sub1": 4},
            raw_response="raw",
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["dimension"] == "accuracy"
        assert data["score"] == 4
        assert data["confidence"] == 0.85
        assert data["reasoning"] == "Test reasoning"
        assert data["evidence_cited"] == ["evidence 1"]
        assert data["recommendations"] == ["rec 1"]
        assert data["sub_scores"] == {"sub1": 4}
        assert data["raw_response"] == "raw"

    def test_from_dict(self):
        """JudgeResult should deserialize from dictionary."""
        data = {
            "dimension": "accuracy",
            "score": 4,
            "confidence": 0.85,
            "reasoning": "Test",
            "evidence_cited": ["e1"],
            "recommendations": ["r1"],
            "sub_scores": {"s1": 4},
            "raw_response": "raw",
        }

        result = JudgeResult.from_dict(data)

        assert result.dimension == "accuracy"
        assert result.score == 4
        assert result.confidence == 0.85
        assert result.reasoning == "Test"
        assert result.evidence_cited == ["e1"]
        assert result.recommendations == ["r1"]
        assert result.sub_scores == {"s1": 4}
        assert result.raw_response == "raw"

    def test_from_dict_with_missing_fields(self):
        """JudgeResult.from_dict should handle missing fields gracefully."""
        data = {"score": 3}

        result = JudgeResult.from_dict(data)

        assert result.dimension == "unknown"
        assert result.score == 3
        assert result.confidence == 0.0
        assert result.reasoning == ""
        assert result.evidence_cited == []
        assert result.recommendations == []
        assert result.sub_scores == {}
        assert result.raw_response == ""

    def test_is_passing_default_threshold(self):
        """is_passing should use default threshold of 3."""
        passing = JudgeResult(dimension="test", score=3, confidence=0.8, reasoning="")
        failing = JudgeResult(dimension="test", score=2, confidence=0.8, reasoning="")

        assert passing.is_passing() is True
        assert failing.is_passing() is False

    def test_is_passing_custom_threshold(self):
        """is_passing should accept custom threshold."""
        result = JudgeResult(dimension="test", score=4, confidence=0.8, reasoning="")

        assert result.is_passing(threshold=4) is True
        assert result.is_passing(threshold=5) is False

    def test_json_serialization_roundtrip(self):
        """JudgeResult should survive JSON serialization roundtrip."""
        original = JudgeResult(
            dimension="accuracy",
            score=4,
            confidence=0.85,
            reasoning="Test",
            evidence_cited=["e1", "e2"],
            recommendations=["r1"],
            sub_scores={"s1": 4, "s2": 5},
            raw_response="raw response",
        )

        json_str = json.dumps(original.to_dict())
        data = json.loads(json_str)
        restored = JudgeResult.from_dict(data)

        assert restored.dimension == original.dimension
        assert restored.score == original.score
        assert restored.confidence == original.confidence
        assert restored.reasoning == original.reasoning
        assert restored.evidence_cited == original.evidence_cited
        assert restored.recommendations == original.recommendations
        assert restored.sub_scores == original.sub_scores
        assert restored.raw_response == original.raw_response


# Concrete implementation for testing abstract BaseJudge
class TestJudge(BaseJudge):
    """Concrete judge implementation for testing."""

    @property
    def dimension_name(self) -> str:
        return "test_dimension"

    @property
    def weight(self) -> float:
        return 0.25

    def collect_evidence(self) -> dict[str, Any]:
        return {"test_key": "test_value", "files_analyzed": 5}

    def get_default_prompt(self) -> str:
        return """Test prompt template.
{{ evidence }}
Respond with JSON."""


class TestBaseJudgeValidation:
    """Tests for BaseJudge class methods and validation."""

    def test_validate_claude_cli_found(self):
        """validate_claude_cli should return True when CLI is available."""
        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            with patch("os.access", return_value=True):
                is_valid, message = BaseJudge.validate_claude_cli()

                assert is_valid is True
                assert message == "/usr/local/bin/claude"

    def test_validate_claude_cli_not_found(self):
        """validate_claude_cli should return False when CLI not in PATH."""
        with patch("shutil.which", return_value=None):
            is_valid, message = BaseJudge.validate_claude_cli()

            assert is_valid is False
            assert "not found" in message.lower()

    def test_validate_claude_cli_not_executable(self):
        """validate_claude_cli should return False when CLI not executable."""
        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            with patch("os.access", return_value=False):
                is_valid, message = BaseJudge.validate_claude_cli()

                assert is_valid is False
                assert "not executable" in message.lower()


class TestBaseJudgeInit:
    """Tests for BaseJudge initialization."""

    def test_default_initialization(self, tmp_path):
        """BaseJudge should initialize with default values."""
        judge = TestJudge(working_dir=tmp_path)

        assert judge.model == "sonnet"
        assert judge.timeout == 120
        assert judge.working_dir == tmp_path
        assert judge.use_llm is True

    def test_custom_initialization(self, tmp_path):
        """BaseJudge should accept custom parameters."""
        output_dir = tmp_path / "output"
        gt_dir = tmp_path / "ground-truth"

        judge = TestJudge(
            model="opus",
            timeout=60,
            working_dir=tmp_path,
            output_dir=output_dir,
            ground_truth_dir=gt_dir,
            use_llm=False,
        )

        assert judge.model == "opus"
        assert judge.timeout == 60
        assert judge.output_dir == output_dir
        assert judge.ground_truth_dir == gt_dir
        assert judge.use_llm is False

    def test_dimension_name_property(self, tmp_path):
        """dimension_name should return the abstract property value."""
        judge = TestJudge(working_dir=tmp_path)

        assert judge.dimension_name == "test_dimension"

    def test_weight_property(self, tmp_path):
        """weight should return the abstract property value."""
        judge = TestJudge(working_dir=tmp_path)

        assert judge.weight == 0.25


class TestBaseJudgePrompts:
    """Tests for prompt loading and building."""

    def test_get_default_prompt(self, tmp_path):
        """get_default_prompt should return the template string."""
        judge = TestJudge(working_dir=tmp_path)

        prompt = judge.get_default_prompt()

        assert "{{ evidence }}" in prompt
        assert "Test prompt template" in prompt

    def test_load_prompt_template_uses_default(self, tmp_path):
        """load_prompt_template should use default when file doesn't exist."""
        judge = TestJudge(working_dir=tmp_path)

        template = judge.load_prompt_template()

        assert "{{ evidence }}" in template

    def test_build_prompt_injects_evidence(self, tmp_path):
        """build_prompt should replace {{ evidence }} with JSON."""
        judge = TestJudge(working_dir=tmp_path)
        evidence = {"key1": "value1", "key2": 42}

        prompt = judge.build_prompt(evidence)

        assert "key1" in prompt
        assert "value1" in prompt
        assert "42" in prompt
        assert "{{ evidence }}" not in prompt


class TestBaseJudgeParseResponse:
    """Tests for LLM response parsing."""

    def test_parse_response_valid_json(self, tmp_path):
        """parse_response should extract valid JSON response."""
        judge = TestJudge(working_dir=tmp_path)
        response = '''Here is my evaluation:
{
    "score": 4,
    "confidence": 0.85,
    "reasoning": "Good coverage",
    "evidence_cited": ["File A"],
    "recommendations": ["Add tests"]
}
'''

        result = judge.parse_response(response)

        assert result.score == 4
        assert result.confidence == 0.85
        assert result.reasoning == "Good coverage"
        assert result.evidence_cited == ["File A"]
        assert result.recommendations == ["Add tests"]
        assert result.dimension == "test_dimension"
        assert result.raw_response == response

    def test_parse_response_extracts_embedded_json(self, tmp_path):
        """parse_response should extract JSON embedded in text."""
        judge = TestJudge(working_dir=tmp_path)
        response = 'Some preamble text {"score": 5, "reasoning": "Excellent"} and more text'

        result = judge.parse_response(response)

        assert result.score == 5
        assert result.reasoning == "Excellent"

    def test_parse_response_fallback_score_in_text(self, tmp_path):
        """parse_response should extract score from text when JSON fails."""
        judge = TestJudge(working_dir=tmp_path)
        response = "Based on my analysis, I give a score: 4 for this dimension."

        result = judge.parse_response(response)

        assert result.score == 4
        assert result.confidence == 0.5  # Fallback confidence
        assert result.dimension == "test_dimension"

    def test_parse_response_default_score_3(self, tmp_path):
        """parse_response should default to score 3 when no score found."""
        judge = TestJudge(working_dir=tmp_path)
        response = "This is some text without any score mentioned."

        result = judge.parse_response(response)

        assert result.score == 3
        assert result.confidence == 0.5

    def test_parse_response_malformed_json(self, tmp_path):
        """parse_response should handle malformed JSON gracefully."""
        judge = TestJudge(working_dir=tmp_path)
        response = '{"score": 4, "reasoning": incomplete json'

        result = judge.parse_response(response)

        # Should fall back to text extraction
        assert result.score == 4 or result.score == 3  # May find score: 4
        assert result.dimension == "test_dimension"

    def test_parse_response_empty_string(self, tmp_path):
        """parse_response should handle empty response."""
        judge = TestJudge(working_dir=tmp_path)
        response = ""

        result = judge.parse_response(response)

        assert result.score == 3
        assert result.reasoning == "No response received"


class TestBaseJudgeInvokeClaude:
    """Tests for Claude invocation (mocked)."""

    def test_invoke_claude_prefers_sdk(self, tmp_path):
        """invoke_claude should prefer SDK over CLI."""
        judge = TestJudge(working_dir=tmp_path)

        with patch.object(judge, "_invoke_via_sdk", return_value="SDK response") as mock_sdk:
            with patch.object(judge, "_invoke_via_cli") as mock_cli:
                result = judge.invoke_claude("test prompt")

                assert result == "SDK response"
                mock_sdk.assert_called_once_with("test prompt")
                mock_cli.assert_not_called()

    def test_invoke_claude_falls_back_to_cli(self, tmp_path):
        """invoke_claude should fall back to CLI when SDK returns None."""
        judge = TestJudge(working_dir=tmp_path)

        with patch.object(judge, "_invoke_via_sdk", return_value=None):
            with patch.object(judge, "_invoke_via_cli", return_value="CLI response") as mock_cli:
                result = judge.invoke_claude("test prompt")

                assert result == "CLI response"
                mock_cli.assert_called_once_with("test prompt")

    def test_invoke_via_cli_success(self, tmp_path):
        """_invoke_via_cli should return stdout on success."""
        judge = TestJudge(working_dir=tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"score": 4}'

        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.run", return_value=mock_result):
                result = judge._invoke_via_cli("test prompt")

                assert result == '{"score": 4}'

    def test_invoke_via_cli_not_found(self, tmp_path):
        """_invoke_via_cli should return error when CLI not found."""
        judge = TestJudge(working_dir=tmp_path)

        with patch("shutil.which", return_value=None):
            result = judge._invoke_via_cli("test prompt")

            assert "Error" in result
            assert "not found" in result.lower()

    def test_invoke_via_cli_timeout(self, tmp_path):
        """_invoke_via_cli should handle timeout."""
        judge = TestJudge(working_dir=tmp_path, timeout=5)

        import subprocess
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 5)):
                result = judge._invoke_via_cli("test prompt")

                assert "Error" in result
                assert "timed out" in result.lower()

    def test_invoke_via_cli_nonzero_exit(self, tmp_path):
        """_invoke_via_cli should handle non-zero exit code."""
        judge = TestJudge(working_dir=tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Some error occurred"

        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("subprocess.run", return_value=mock_result):
                result = judge._invoke_via_cli("test prompt")

                assert "Error" in result
                assert "exit 1" in result


class TestBaseJudgeHeuristic:
    """Tests for heuristic evaluation fallback."""

    def test_heuristic_evaluation_default(self, tmp_path):
        """Default heuristic evaluation should return neutral score."""
        judge = TestJudge(working_dir=tmp_path, use_llm=False)

        result = judge.run_heuristic_evaluation({})

        assert result.score == 3
        assert result.confidence == 0.6
        assert "not implemented" in result.reasoning.lower()

    def test_evaluate_uses_heuristic_when_use_llm_false(self, tmp_path):
        """evaluate() should use heuristic when use_llm=False."""
        judge = TestJudge(working_dir=tmp_path, use_llm=False)

        with patch.object(judge, "run_heuristic_evaluation", return_value=JudgeResult(
            dimension="test",
            score=4,
            confidence=0.8,
            reasoning="Heuristic",
        )) as mock_heuristic:
            with patch.object(judge, "invoke_claude") as mock_invoke:
                result = judge.evaluate()

                mock_heuristic.assert_called_once()
                mock_invoke.assert_not_called()
                assert result.score == 4


class TestBaseJudgeDataLoading:
    """Tests for analysis and ground truth loading."""

    def test_load_analysis_results_empty_dir(self, tmp_path):
        """load_analysis_results should return empty dict for empty dir."""
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)

        judge = TestJudge(working_dir=tmp_path, output_dir=output_dir)
        results = judge.load_analysis_results()

        assert results == {}

    def test_load_analysis_results_with_files(self, tmp_path):
        """load_analysis_results should load all JSON files."""
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)

        # Create test files
        (output_dir / "repo1.json").write_text('{"files": []}')
        (output_dir / "repo2.json").write_text('{"data": {"files": []}}')

        judge = TestJudge(working_dir=tmp_path, output_dir=output_dir)
        results = judge.load_analysis_results()

        assert "repo1" in results
        assert "repo2" in results

    def test_load_analysis_results_skips_invalid_json(self, tmp_path):
        """load_analysis_results should skip invalid JSON files."""
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)

        (output_dir / "valid.json").write_text('{"files": []}')
        (output_dir / "invalid.json").write_text('not valid json')

        judge = TestJudge(working_dir=tmp_path, output_dir=output_dir)
        results = judge.load_analysis_results()

        assert "valid" in results
        assert "invalid" not in results

    def test_load_ground_truth(self, tmp_path):
        """load_ground_truth should load all ground truth files."""
        gt_dir = tmp_path / "evaluation" / "ground-truth"
        gt_dir.mkdir(parents=True)

        (gt_dir / "repo1.json").write_text('{"id": "repo1", "expected": {}}')
        (gt_dir / "repo2.json").write_text('{"expected": {}}')

        judge = TestJudge(working_dir=tmp_path, ground_truth_dir=gt_dir)
        results = judge.load_ground_truth()

        assert "repo1" in results
        assert "repo2" in results

    def test_extract_files_current_format(self):
        """extract_files should handle results.files format."""
        analysis = {
            "results": {
                "files": [{"path": "a.py"}, {"path": "b.py"}]
            }
        }

        files = BaseJudge.extract_files(analysis)

        assert len(files) == 2
        assert files[0]["path"] == "a.py"

    def test_extract_files_legacy_format(self):
        """extract_files should handle direct files format."""
        analysis = {
            "files": [{"path": "a.py"}, {"path": "b.py"}]
        }

        files = BaseJudge.extract_files(analysis)

        assert len(files) == 2

    def test_extract_summary_current_format(self):
        """extract_summary should handle results.summary format."""
        analysis = {
            "results": {
                "summary": {"total": 10}
            }
        }

        summary = BaseJudge.extract_summary(analysis)

        assert summary["total"] == 10

    def test_extract_summary_legacy_format(self):
        """extract_summary should handle direct summary format."""
        analysis = {
            "summary": {"total": 10}
        }

        summary = BaseJudge.extract_summary(analysis)

        assert summary["total"] == 10


class TestBaseJudgeFullEvaluation:
    """Tests for full evaluation pipeline."""

    def test_evaluate_full_pipeline(self, tmp_path):
        """evaluate() should run the full pipeline."""
        judge = TestJudge(working_dir=tmp_path)

        mock_response = json.dumps({
            "score": 4,
            "confidence": 0.85,
            "reasoning": "Good results",
        })

        with patch.object(judge, "invoke_claude", return_value=mock_response):
            result = judge.evaluate()

            assert result.score == 4
            assert result.confidence == 0.85
            assert result.dimension == "test_dimension"

    def test_run_ground_truth_assertions_default(self, tmp_path):
        """Default ground truth assertions should pass."""
        judge = TestJudge(working_dir=tmp_path)

        passed, failures = judge.run_ground_truth_assertions()

        assert passed is True
        assert failures == []

    def test_legacy_get_prompt(self, tmp_path):
        """Legacy get_prompt should work like build_prompt."""
        judge = TestJudge(working_dir=tmp_path)
        evidence = {"key": "value"}

        legacy_prompt = judge.get_prompt(evidence)
        new_prompt = judge.build_prompt(evidence)

        assert legacy_prompt == new_prompt
