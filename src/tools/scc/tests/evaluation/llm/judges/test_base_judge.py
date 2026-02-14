"""Tests for BaseJudge and JudgeResult.

All tests use REAL data - NO MOCKING.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from evaluation.llm.judges.base import BaseJudge, JudgeResult


class TestJudgeResult:
    """Tests for JudgeResult dataclass."""

    def test_judge_result_defaults(self):
        """Empty lists for optional fields when not provided."""
        result = JudgeResult(
            dimension="test",
            score=3,
            confidence=0.5,
            reasoning="test reasoning"
        )
        assert result.evidence_cited == []
        assert result.recommendations == []
        assert result.sub_scores == {}
        assert result.raw_response == ""

    def test_judge_result_to_dict(self, sample_judge_result: JudgeResult):
        """Serialization to dict works correctly."""
        d = sample_judge_result.to_dict()
        assert isinstance(d, dict)
        assert d["dimension"] == "test_dimension"
        assert d["score"] == 4
        assert d["confidence"] == 0.85
        assert d["reasoning"] == "Test reasoning"
        assert d["evidence_cited"] == ["evidence1", "evidence2"]
        assert d["recommendations"] == ["recommendation1"]
        assert d["sub_scores"] == {"sub1": 4, "sub2": 5}

    def test_judge_result_from_dict(self):
        """Deserialization from dict works correctly."""
        data = {
            "dimension": "my_dimension",
            "score": 5,
            "confidence": 0.95,
            "reasoning": "Excellent",
            "evidence_cited": ["a", "b"],
            "recommendations": ["c"],
            "sub_scores": {"x": 5},
            "raw_response": "raw"
        }
        result = JudgeResult.from_dict(data)
        assert result.dimension == "my_dimension"
        assert result.score == 5
        assert result.confidence == 0.95
        assert result.reasoning == "Excellent"
        assert result.evidence_cited == ["a", "b"]
        assert result.recommendations == ["c"]
        assert result.sub_scores == {"x": 5}
        assert result.raw_response == "raw"

    def test_judge_result_from_dict_missing_optional(self):
        """Deserialization handles missing optional fields."""
        data = {"dimension": "test", "score": 3, "confidence": 0.5, "reasoning": "ok"}
        result = JudgeResult.from_dict(data)
        assert result.evidence_cited == []
        assert result.recommendations == []
        assert result.sub_scores == {}

    def test_judge_result_roundtrip(self, sample_judge_result: JudgeResult):
        """to_dict -> from_dict produces equivalent result."""
        d = sample_judge_result.to_dict()
        result = JudgeResult.from_dict(d)
        assert result.dimension == sample_judge_result.dimension
        assert result.score == sample_judge_result.score
        assert result.confidence == sample_judge_result.confidence
        assert result.reasoning == sample_judge_result.reasoning
        assert result.evidence_cited == sample_judge_result.evidence_cited
        assert result.recommendations == sample_judge_result.recommendations
        assert result.sub_scores == sample_judge_result.sub_scores

    def test_judge_result_score_range(self):
        """Score should be integer 1-5."""
        for score in [1, 2, 3, 4, 5]:
            result = JudgeResult(dimension="test", score=score, confidence=0.5, reasoning="ok")
            assert 1 <= result.score <= 5

    def test_judge_result_confidence_range(self):
        """Confidence should be float 0.0-1.0."""
        for conf in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = JudgeResult(dimension="test", score=3, confidence=conf, reasoning="ok")
            assert 0.0 <= result.confidence <= 1.0


class TestBaseJudge:
    """Tests for BaseJudge base class."""

    def test_dimension_name(self, concrete_judge):
        """dimension_name property returns correct value."""
        assert concrete_judge.dimension_name == "test_dimension"

    def test_weight(self, concrete_judge):
        """weight property returns correct value."""
        assert concrete_judge.weight == 0.10

    def test_prompt_file_path(self, concrete_judge):
        """prompt_file property returns correct path."""
        expected = Path(__file__).parent.parent.parent.parent.parent / "evaluation" / "llm" / "prompts" / "test_dimension.md"
        assert concrete_judge.prompt_file == expected

    def test_load_default_prompt_when_missing(self, concrete_judge):
        """Falls back to get_default_prompt() when file doesn't exist."""
        # test_dimension.md doesn't exist, so should use default
        prompt = concrete_judge.load_prompt_template()
        assert prompt == "Test prompt for {{ key }}"

    def test_load_prompt_from_file(self, poc_root: Path):
        """Loads prompt from file when it exists."""
        from evaluation.llm.judges.directory_analysis import DirectoryAnalysisJudge
        judge = DirectoryAnalysisJudge(working_dir=poc_root)
        prompt = judge.load_prompt_template()
        assert "Directory Analysis" in prompt
        assert "direct" in prompt or "recursive" in prompt

    def test_build_prompt_substitutes_string(self, concrete_judge):
        """{{ key }} is replaced with string value."""
        evidence = {"key": "test_value"}
        prompt = concrete_judge.build_prompt(evidence)
        assert "test_value" in prompt
        assert "{{ key }}" not in prompt

    def test_build_prompt_substitutes_dict(self, concrete_judge):
        """{{ key }} is replaced with JSON dict."""
        concrete_judge._prompt_template = "Data: {{ data }}"
        evidence = {"data": {"a": 1, "b": 2}}
        prompt = concrete_judge.build_prompt(evidence)
        assert '"a": 1' in prompt or '"a":1' in prompt
        assert "{{ data }}" not in prompt

    def test_build_prompt_substitutes_list(self, concrete_judge):
        """{{ key }} is replaced with JSON list."""
        concrete_judge._prompt_template = "Items: {{ items }}"
        evidence = {"items": [1, 2, 3]}
        prompt = concrete_judge.build_prompt(evidence)
        # JSON might be formatted with newlines, check for list elements
        assert "1" in prompt and "2" in prompt and "3" in prompt
        assert "{{ items }}" not in prompt

    def test_build_prompt_nested_dict(self, concrete_judge):
        """Nested dicts are serialized as JSON."""
        concrete_judge._prompt_template = "Nested: {{ nested }}"
        evidence = {"nested": {"level1": {"level2": "value"}}}
        prompt = concrete_judge.build_prompt(evidence)
        assert "level1" in prompt
        assert "level2" in prompt
        assert "value" in prompt

    def test_build_prompt_preserves_unmatched(self, concrete_judge):
        """Unresolved placeholders raise ValueError."""
        concrete_judge._prompt_template = "Has {{ known }} and {{ unknown }}"
        evidence = {"known": "value"}
        with pytest.raises(ValueError, match="Unresolved prompt placeholders"):
            concrete_judge.build_prompt(evidence)

    def test_parse_response_extracts_json(self, concrete_judge, sample_llm_response_valid_json):
        """Extracts valid JSON from response with surrounding text."""
        result = concrete_judge.parse_response(sample_llm_response_valid_json)
        assert result.score == 4
        assert result.confidence == 0.85
        assert "well-structured" in result.reasoning
        assert "field1" in result.evidence_cited
        assert "Consider" in result.recommendations[0]

    def test_parse_response_fallback_score(self, concrete_judge, sample_llm_response_score_in_text):
        """Falls back to extracting 'score: N' from text."""
        result = concrete_judge.parse_response(sample_llm_response_score_in_text)
        assert result.score == 4
        assert result.confidence == 0.5  # Default confidence for fallback

    def test_parse_response_handles_malformed(self, concrete_judge, sample_llm_response_malformed_json):
        """Handles malformed JSON gracefully."""
        result = concrete_judge.parse_response(sample_llm_response_malformed_json)
        assert result.score == 3  # Default score
        assert result.raw_response == sample_llm_response_malformed_json

    def test_parse_response_ignores_json_without_score(self, concrete_judge):
        """Falls back when JSON lacks a valid score field."""
        response = '{"error": "rate limit"}'
        result = concrete_judge.parse_response(response)
        assert result.score == 0
        assert result.raw_response == response

    def test_parse_response_extracts_score_variations(self, concrete_judge):
        """Extracts score from various text formats."""
        test_cases = [
            ("Score: 5", 5),
            ("score:4", 4),
            ("SCORE: 3", 3),
            ("My score: 2", 2),
            ("I give this a score: 1", 1),
        ]
        for text, expected in test_cases:
            result = concrete_judge.parse_response(text)
            assert result.score == expected, f"Failed for '{text}'"

    def test_parse_response_preserves_raw(self, concrete_judge):
        """raw_response is always preserved."""
        response = "Some response text"
        result = concrete_judge.parse_response(response)
        assert result.raw_response == response

    def test_ground_truth_assertions_default(self, concrete_judge):
        """Default ground truth assertions always pass."""
        passed, failures = concrete_judge.run_ground_truth_assertions()
        assert passed is True
        assert failures == []

    def test_collect_evidence(self, concrete_judge):
        """collect_evidence returns expected data."""
        evidence = concrete_judge.collect_evidence()
        assert evidence["key"] == "value"
        assert evidence["nested"]["a"] == 1
        assert evidence["nested"]["b"] == 2


class TestJudgeResultValidation:
    """Tests for JudgeResult value validation."""

    def test_score_boundary_1(self):
        """Score 1 is valid (minimum)."""
        result = JudgeResult(dimension="test", score=1, confidence=0.5, reasoning="ok")
        assert result.score == 1

    def test_score_boundary_5(self):
        """Score 5 is valid (maximum)."""
        result = JudgeResult(dimension="test", score=5, confidence=0.5, reasoning="ok")
        assert result.score == 5

    def test_confidence_boundary_0(self):
        """Confidence 0.0 is valid (minimum)."""
        result = JudgeResult(dimension="test", score=3, confidence=0.0, reasoning="ok")
        assert result.confidence == 0.0

    def test_confidence_boundary_1(self):
        """Confidence 1.0 is valid (maximum)."""
        result = JudgeResult(dimension="test", score=3, confidence=1.0, reasoning="ok")
        assert result.confidence == 1.0

    def test_empty_reasoning_allowed(self):
        """Empty reasoning string is allowed."""
        result = JudgeResult(dimension="test", score=3, confidence=0.5, reasoning="")
        assert result.reasoning == ""

    def test_unicode_in_reasoning(self):
        """Unicode characters in reasoning are preserved."""
        result = JudgeResult(dimension="test", score=3, confidence=0.5, reasoning="Code quality: 优秀 ★★★★☆")
        assert "优秀" in result.reasoning
        assert "★" in result.reasoning
