"""Tests for PMD CPD LLM judges.

Tests the evidence collection and response parsing logic for each judge
without invoking the Claude API. Verifies that:
1. Evidence is correctly extracted from analysis results
2. JSON responses are parsed into JudgeResult correctly
3. Fallback parsing works for non-JSON responses
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from evaluation.llm.judges.base import BaseJudge, JudgeResult
from evaluation.llm.judges.duplication_accuracy import DuplicationAccuracyJudge
from evaluation.llm.judges.semantic_detection import SemanticDetectionJudge
from evaluation.llm.judges.cross_file_detection import CrossFileDetectionJudge
from evaluation.llm.judges.actionability import ActionabilityJudge


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_pmd_cpd_output() -> dict[str, Any]:
    """Provide realistic PMD CPD analysis output for testing."""
    return {
        "metadata": {
            "version": "1.0.0",
            "cpd_version": "7.0.0",
            "min_tokens": 100,
            "analyzed_at": "2025-01-24T10:00:00Z",
            "elapsed_seconds": 2.5,
            "ignore_identifiers": False,
            "ignore_literals": False,
        },
        "summary": {
            "total_files": 15,
            "total_clones": 5,
            "duplication_percentage": 12.5,
            "cross_file_clones": 2,
        },
        "files": [
            {
                "path": "src/main.py",
                "total_lines": 200,
                "duplicate_lines": 30,
                "duplicate_blocks": 2,
                "duplication_percentage": 15.0,
                "language": "python",
            },
            {
                "path": "src/utils.py",
                "total_lines": 100,
                "duplicate_lines": 20,
                "duplicate_blocks": 1,
                "duplication_percentage": 20.0,
                "language": "python",
            },
            {
                "path": "src/semantic_dup_example.py",
                "total_lines": 80,
                "duplicate_lines": 15,
                "duplicate_blocks": 1,
                "duplication_percentage": 18.75,
                "language": "python",
            },
            {
                "path": "src/cross_file_a.py",
                "total_lines": 60,
                "duplicate_lines": 20,
                "duplicate_blocks": 1,
                "duplication_percentage": 33.3,
                "language": "python",
            },
            {
                "path": "src/cross_file_b.py",
                "total_lines": 60,
                "duplicate_lines": 20,
                "duplicate_blocks": 1,
                "duplication_percentage": 33.3,
                "language": "python",
            },
        ],
        "duplications": [
            {
                "clone_id": "CPD-0001",
                "lines": 15,
                "tokens": 120,
                "occurrences": [
                    {"file": "src/main.py", "line_start": 10, "line_end": 24},
                    {"file": "src/main.py", "line_start": 50, "line_end": 64},
                ],
                "code_fragment": "def process_data(items):\n    result = []\n    for item in items:\n        result.append(item * 2)\n    return result",
            },
            {
                "clone_id": "CPD-0002",
                "lines": 20,
                "tokens": 150,
                "occurrences": [
                    {"file": "src/cross_file_a.py", "line_start": 10, "line_end": 29},
                    {"file": "src/cross_file_b.py", "line_start": 15, "line_end": 34},
                ],
                "code_fragment": "def shared_logic(data):\n    validated = validate(data)\n    processed = transform(validated)\n    return processed",
            },
            {
                "clone_id": "CPD-0003",
                "lines": 10,
                "tokens": 80,
                "occurrences": [
                    {"file": "src/main.py", "line_start": 100, "line_end": 109},
                    {"file": "src/utils.py", "line_start": 20, "line_end": 29},
                ],
                "code_fragment": "def helper():\n    return 42",
            },
            {
                "clone_id": "CPD-0004",
                "lines": 12,
                "tokens": 95,
                "occurrences": [
                    {"file": "src/utils.py", "line_start": 50, "line_end": 61},
                    {"file": "src/utils.py", "line_start": 70, "line_end": 81},
                ],
                "code_fragment": "for i in range(10):\n    print(i)",
            },
            {
                "clone_id": "CPD-0005",
                "lines": 8,
                "tokens": 60,
                "occurrences": [
                    {"file": "src/semantic_dup_example.py", "line_start": 10, "line_end": 17},
                    {"file": "src/semantic_dup_example.py", "line_start": 30, "line_end": 37},
                ],
                "code_fragment": "x = calculate(a, b)\nreturn x",
            },
        ],
        "statistics": {
            "cross_file_clones": 2,
            "total_tokens": 505,
            "total_duplicate_lines": 65,
            "by_language": {
                "python": {"clone_count": 5, "total_lines": 65}
            },
        },
        "errors": [],
    }


@pytest.fixture
def semantic_mode_output(sample_pmd_cpd_output) -> dict[str, Any]:
    """Provide PMD CPD output with semantic mode enabled."""
    output = sample_pmd_cpd_output.copy()
    output["metadata"] = sample_pmd_cpd_output["metadata"].copy()
    output["metadata"]["ignore_identifiers"] = True
    output["metadata"]["ignore_literals"] = True
    return output


@pytest.fixture
def sample_judge_response_json() -> str:
    """Provide a sample valid JSON response from Claude."""
    return json.dumps({
        "score": 4,
        "confidence": 0.85,
        "reasoning": "The duplication detection shows good accuracy with clear clone identification.",
        "evidence_cited": [
            "5 clones detected across 15 files",
            "Cross-file detection working: 2 cross-file clones",
            "Line counts match expectations",
        ],
        "recommendations": [
            "Consider lowering min_tokens for smaller duplicates",
            "Enable semantic mode for variable-renamed clones",
        ],
        "sub_scores": {
            "genuine_clones": 4,
            "false_positive_rate": 5,
            "location_accuracy": 4,
        },
    })


@pytest.fixture
def sample_judge_response_text() -> str:
    """Provide a sample plain text response (non-JSON) from Claude."""
    return """Based on my analysis, the duplication detection shows reasonable results.

The score: 3 overall because while most clones are detected, there are some gaps
in the semantic detection capabilities.

Key observations:
- 5 clones detected
- Cross-file detection is working
- Some false positives possible

Recommendations:
- Enable semantic mode
- Lower token threshold"""


@pytest.fixture
def tmp_analysis_file(tmp_path: Path, sample_pmd_cpd_output) -> Path:
    """Create a temporary analysis file and return its path."""
    output_dir = tmp_path / "output" / "runs"
    output_dir.mkdir(parents=True)
    analysis_file = output_dir / "synthetic.json"
    analysis_file.write_text(json.dumps(sample_pmd_cpd_output))
    return analysis_file


@pytest.fixture
def tmp_output_dir(tmp_path: Path, sample_pmd_cpd_output) -> Path:
    """Create a temporary output directory with analysis files."""
    output_dir = tmp_path / "output" / "runs"
    output_dir.mkdir(parents=True)

    # Write main analysis
    (output_dir / "synthetic.json").write_text(json.dumps(sample_pmd_cpd_output))

    return output_dir


# ============================================================================
# JudgeResult Tests
# ============================================================================


class TestJudgeResult:
    """Tests for JudgeResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = JudgeResult(
            dimension="test_dimension",
            score=4,
            confidence=0.9,
            reasoning="Test reasoning",
            evidence_cited=["evidence1", "evidence2"],
            recommendations=["rec1"],
            sub_scores={"sub1": 5},
            raw_response="raw",
        )

        d = result.to_dict()

        assert d["dimension"] == "test_dimension"
        assert d["score"] == 4
        assert d["confidence"] == 0.9
        assert d["reasoning"] == "Test reasoning"
        assert d["evidence_cited"] == ["evidence1", "evidence2"]
        assert d["recommendations"] == ["rec1"]
        assert d["sub_scores"] == {"sub1": 5}

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "dimension": "accuracy",
            "score": 5,
            "confidence": 0.95,
            "reasoning": "Excellent results",
            "evidence_cited": ["e1"],
            "recommendations": [],
            "sub_scores": {},
        }

        result = JudgeResult.from_dict(data)

        assert result.dimension == "accuracy"
        assert result.score == 5
        assert result.confidence == 0.95
        assert result.reasoning == "Excellent results"

    def test_from_dict_with_defaults(self):
        """Test from_dict handles missing fields with defaults."""
        data = {"score": 3}

        result = JudgeResult.from_dict(data)

        assert result.dimension == "unknown"
        assert result.score == 3
        assert result.confidence == 0.0
        assert result.reasoning == ""
        assert result.evidence_cited == []
        assert result.recommendations == []
        assert result.sub_scores == {}


# ============================================================================
# DuplicationAccuracyJudge Tests
# ============================================================================


class TestDuplicationAccuracyJudge:
    """Tests for DuplicationAccuracyJudge."""

    def test_dimension_name(self, tmp_path):
        """Test dimension name property."""
        judge = DuplicationAccuracyJudge(working_dir=tmp_path)
        assert judge.dimension_name == "duplication_accuracy"

    def test_weight(self, tmp_path):
        """Test weight property."""
        judge = DuplicationAccuracyJudge(working_dir=tmp_path)
        assert judge.weight == 0.35

    def test_collect_evidence(self, tmp_output_dir, sample_pmd_cpd_output):
        """Test evidence collection from analysis results."""
        judge = DuplicationAccuracyJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        evidence = judge.collect_evidence()

        # Check analysis summary
        assert evidence["analysis_summary"]["total_files"] == 15
        assert evidence["analysis_summary"]["total_clones"] == 5
        assert evidence["analysis_summary"]["duplication_percentage"] == 12.5

        # Check sample duplications (limited to 5)
        assert len(evidence["sample_duplications"]) == 5
        first_dup = evidence["sample_duplications"][0]
        assert first_dup["clone_id"] == "CPD-0001"
        assert first_dup["lines"] == 15
        assert first_dup["tokens"] == 120
        assert first_dup["occurrences"] == 2

        # Check file metrics (limited to 10)
        assert len(evidence["file_metrics"]) == 5  # Only 5 files in sample
        first_file = evidence["file_metrics"][0]
        assert first_file["path"] == "src/main.py"
        assert first_file["total_lines"] == 200
        assert first_file["duplicate_lines"] == 30

    def test_collect_evidence_empty_results(self, tmp_path):
        """Test evidence collection with no analysis files."""
        output_dir = tmp_path / "empty_output"
        output_dir.mkdir(parents=True)

        judge = DuplicationAccuracyJudge(
            output_dir=output_dir,
            working_dir=tmp_path,
        )

        evidence = judge.collect_evidence()

        assert evidence["analysis_summary"] == {}
        assert evidence["sample_duplications"] == []
        assert evidence["file_metrics"] == []

    def test_parse_response_json(self, tmp_path, sample_judge_response_json):
        """Test parsing a valid JSON response."""
        judge = DuplicationAccuracyJudge(working_dir=tmp_path)

        result = judge.parse_response(sample_judge_response_json)

        assert result.dimension == "duplication_accuracy"
        assert result.score == 4
        assert result.confidence == 0.85
        assert "good accuracy" in result.reasoning
        assert len(result.evidence_cited) == 3
        assert len(result.recommendations) == 2
        assert result.sub_scores["genuine_clones"] == 4
        assert result.sub_scores["false_positive_rate"] == 5

    def test_parse_response_text_fallback(self, tmp_path, sample_judge_response_text):
        """Test fallback parsing for non-JSON response."""
        judge = DuplicationAccuracyJudge(working_dir=tmp_path)

        result = judge.parse_response(sample_judge_response_text)

        assert result.dimension == "duplication_accuracy"
        assert result.score == 3  # Extracted from "score: 3"
        assert result.confidence == 0.5  # Default for fallback
        assert result.raw_response == sample_judge_response_text

    def test_evaluate_mocked(self, tmp_output_dir, sample_judge_response_json):
        """Test full evaluate pipeline with mocked Claude invocation."""
        judge = DuplicationAccuracyJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        with patch.object(judge, "invoke_claude", return_value=sample_judge_response_json):
            result = judge.evaluate()

        assert result.dimension == "duplication_accuracy"
        assert result.score == 4
        assert result.confidence == 0.85


# ============================================================================
# SemanticDetectionJudge Tests
# ============================================================================


class TestSemanticDetectionJudge:
    """Tests for SemanticDetectionJudge."""

    def test_dimension_name(self, tmp_path):
        """Test dimension name property."""
        judge = SemanticDetectionJudge(working_dir=tmp_path)
        assert judge.dimension_name == "semantic_detection"

    def test_weight(self, tmp_path):
        """Test weight property."""
        judge = SemanticDetectionJudge(working_dir=tmp_path)
        assert judge.weight == 0.25

    def test_collect_evidence_no_semantic_mode(self, tmp_output_dir):
        """Test evidence collection when semantic mode is disabled."""
        judge = SemanticDetectionJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        evidence = judge.collect_evidence()

        assert evidence["semantic_mode_enabled"] is False
        assert evidence["ignore_identifiers"] is False
        assert evidence["ignore_literals"] is False

        # Should still detect files with "semantic" in path
        assert len(evidence["semantic_files_detected"]) == 1
        assert evidence["semantic_files_detected"][0]["path"] == "src/semantic_dup_example.py"

    def test_collect_evidence_semantic_mode_enabled(self, tmp_path, semantic_mode_output):
        """Test evidence collection when semantic mode is enabled."""
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)
        (output_dir / "semantic.json").write_text(json.dumps(semantic_mode_output))

        judge = SemanticDetectionJudge(
            output_dir=output_dir,
            working_dir=tmp_path,
        )

        evidence = judge.collect_evidence()

        assert evidence["semantic_mode_enabled"] is True
        assert evidence["ignore_identifiers"] is True
        assert evidence["ignore_literals"] is True

    def test_parse_response_with_sub_scores(self, tmp_path):
        """Test parsing response with semantic-specific sub_scores."""
        judge = SemanticDetectionJudge(working_dir=tmp_path)

        response = json.dumps({
            "score": 4,
            "confidence": 0.80,
            "reasoning": "Good semantic detection with identifier ignorance",
            "evidence_cited": ["Semantic mode enabled"],
            "recommendations": [],
            "sub_scores": {
                "identifier_detection": 4,
                "literal_detection": 3,
                "type2_clone_detection": 4,
            },
        })

        result = judge.parse_response(response)

        assert result.sub_scores["identifier_detection"] == 4
        assert result.sub_scores["literal_detection"] == 3
        assert result.sub_scores["type2_clone_detection"] == 4

    def test_evaluate_mocked(self, tmp_output_dir):
        """Test evaluate with mocked Claude invocation."""
        judge = SemanticDetectionJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        mock_response = json.dumps({
            "score": 3,
            "confidence": 0.70,
            "reasoning": "Semantic detection partially working",
            "evidence_cited": [],
            "recommendations": ["Enable ignore_identifiers"],
            "sub_scores": {},
        })

        with patch.object(judge, "invoke_claude", return_value=mock_response):
            result = judge.evaluate()

        assert result.dimension == "semantic_detection"
        assert result.score == 3


# ============================================================================
# CrossFileDetectionJudge Tests
# ============================================================================


class TestCrossFileDetectionJudge:
    """Tests for CrossFileDetectionJudge."""

    def test_dimension_name(self, tmp_path):
        """Test dimension name property."""
        judge = CrossFileDetectionJudge(working_dir=tmp_path)
        assert judge.dimension_name == "cross_file_detection"

    def test_weight(self, tmp_path):
        """Test weight property."""
        judge = CrossFileDetectionJudge(working_dir=tmp_path)
        assert judge.weight == 0.20

    def test_collect_evidence(self, tmp_output_dir):
        """Test evidence collection for cross-file clones."""
        judge = CrossFileDetectionJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        evidence = judge.collect_evidence()

        # Total clones
        assert evidence["total_clone_count"] == 5

        # Cross-file clones (CPD-0002 and CPD-0003 span multiple files)
        assert evidence["cross_file_clone_count"] == 2

        # Check cross-file clone details
        assert len(evidence["cross_file_clones"]) == 2

        # Find CPD-0002 (cross_file_a.py -> cross_file_b.py)
        cross_file_clone = next(
            (c for c in evidence["cross_file_clones"] if c["clone_id"] == "CPD-0002"),
            None
        )
        assert cross_file_clone is not None
        assert set(cross_file_clone["files_involved"]) == {"src/cross_file_a.py", "src/cross_file_b.py"}
        assert cross_file_clone["occurrence_count"] == 2

        # Check cross-file test files detected
        assert len(evidence["cross_file_test_files"]) == 2
        test_file_paths = [f["path"] for f in evidence["cross_file_test_files"]]
        assert "src/cross_file_a.py" in test_file_paths
        assert "src/cross_file_b.py" in test_file_paths

    def test_collect_evidence_no_cross_file_clones(self, tmp_path):
        """Test evidence when there are no cross-file clones."""
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)

        single_file_output = {
            "metadata": {"version": "1.0"},
            "summary": {"total_clones": 1},
            "files": [{"path": "src/single.py", "duplicate_blocks": 2}],
            "duplications": [
                {
                    "clone_id": "CPD-0001",
                    "lines": 10,
                    "occurrences": [
                        {"file": "src/single.py", "line_start": 10, "line_end": 19},
                        {"file": "src/single.py", "line_start": 30, "line_end": 39},
                    ],
                }
            ],
        }
        (output_dir / "single.json").write_text(json.dumps(single_file_output))

        judge = CrossFileDetectionJudge(output_dir=output_dir, working_dir=tmp_path)

        evidence = judge.collect_evidence()

        assert evidence["cross_file_clone_count"] == 0
        assert evidence["cross_file_clones"] == []
        assert evidence["total_clone_count"] == 1

    def test_parse_response_with_sub_scores(self, tmp_path):
        """Test parsing response with cross-file specific sub_scores."""
        judge = CrossFileDetectionJudge(working_dir=tmp_path)

        response = json.dumps({
            "score": 5,
            "confidence": 0.95,
            "reasoning": "Excellent cross-file detection",
            "evidence_cited": ["2 cross-file clones detected"],
            "recommendations": [],
            "sub_scores": {
                "detection_rate": 5,
                "file_linking": 5,
                "reporting_clarity": 4,
            },
        })

        result = judge.parse_response(response)

        assert result.sub_scores["detection_rate"] == 5
        assert result.sub_scores["file_linking"] == 5
        assert result.sub_scores["reporting_clarity"] == 4

    def test_evaluate_mocked(self, tmp_output_dir):
        """Test evaluate with mocked Claude invocation."""
        judge = CrossFileDetectionJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        mock_response = json.dumps({
            "score": 4,
            "confidence": 0.85,
            "reasoning": "Cross-file detection working well",
            "evidence_cited": ["2 cross-file clones found"],
            "recommendations": [],
            "sub_scores": {},
        })

        with patch.object(judge, "invoke_claude", return_value=mock_response):
            result = judge.evaluate()

        assert result.dimension == "cross_file_detection"
        assert result.score == 4


# ============================================================================
# ActionabilityJudge Tests
# ============================================================================


class TestActionabilityJudge:
    """Tests for ActionabilityJudge."""

    def test_dimension_name(self, tmp_path):
        """Test dimension name property."""
        judge = ActionabilityJudge(working_dir=tmp_path)
        assert judge.dimension_name == "actionability"

    def test_weight(self, tmp_path):
        """Test weight property."""
        judge = ActionabilityJudge(working_dir=tmp_path)
        assert judge.weight == 0.20

    def test_collect_evidence(self, tmp_output_dir):
        """Test evidence collection for actionability assessment."""
        judge = ActionabilityJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        evidence = judge.collect_evidence()

        # Report structure
        assert evidence["report_structure"]["has_metadata"] is True
        assert evidence["report_structure"]["has_summary"] is True
        assert evidence["report_structure"]["has_files"] is True
        assert evidence["report_structure"]["has_duplications"] is True
        assert evidence["report_structure"]["has_statistics"] is True

        # Metadata available
        assert evidence["metadata_available"]["version"] is True
        assert evidence["metadata_available"]["cpd_version"] is True
        assert evidence["metadata_available"]["min_tokens"] is True
        assert evidence["metadata_available"]["analyzed_at"] is True
        assert evidence["metadata_available"]["elapsed_seconds"] is True

        # Summary quality
        assert evidence["summary_quality"]["has_total_files"] is True
        assert evidence["summary_quality"]["has_total_clones"] is True
        assert evidence["summary_quality"]["has_duplication_percentage"] is True
        assert evidence["summary_quality"]["has_cross_file_clones"] is True

        # Sample clone details (limited to 3)
        assert len(evidence["sample_clone_details"]) == 3
        first_clone = evidence["sample_clone_details"][0]
        assert first_clone["has_clone_id"] is True
        assert first_clone["has_lines"] is True
        assert first_clone["has_tokens"] is True
        assert first_clone["has_code_fragment"] is True
        assert "file" in first_clone["occurrence_fields"]
        assert "line_start" in first_clone["occurrence_fields"]
        assert "line_end" in first_clone["occurrence_fields"]

    def test_collect_evidence_minimal_output(self, tmp_path):
        """Test evidence collection with minimal analysis output."""
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)

        minimal_output = {
            "duplications": [
                {"clone_id": "CPD-0001", "occurrences": []}
            ]
        }
        (output_dir / "minimal.json").write_text(json.dumps(minimal_output))

        judge = ActionabilityJudge(output_dir=output_dir, working_dir=tmp_path)

        evidence = judge.collect_evidence()

        assert evidence["report_structure"]["has_metadata"] is False
        assert evidence["report_structure"]["has_summary"] is False
        assert evidence["report_structure"]["has_duplications"] is True
        # metadata_available shows what metadata fields exist (all False when no metadata)
        assert all(v is False for v in evidence["metadata_available"].values())
        # summary_quality shows what summary fields exist (all False when no summary)
        assert all(v is False for v in evidence["summary_quality"].values())

    def test_parse_response_with_sub_scores(self, tmp_path):
        """Test parsing response with actionability-specific sub_scores."""
        judge = ActionabilityJudge(working_dir=tmp_path)

        response = json.dumps({
            "score": 4,
            "confidence": 0.80,
            "reasoning": "Reports are actionable with clear locations",
            "evidence_cited": ["Line numbers provided", "Code fragments included"],
            "recommendations": ["Add severity ranking"],
            "sub_scores": {
                "location_clarity": 5,
                "context_provided": 4,
                "prioritization_support": 3,
            },
        })

        result = judge.parse_response(response)

        assert result.sub_scores["location_clarity"] == 5
        assert result.sub_scores["context_provided"] == 4
        assert result.sub_scores["prioritization_support"] == 3

    def test_evaluate_mocked(self, tmp_output_dir):
        """Test evaluate with mocked Claude invocation."""
        judge = ActionabilityJudge(
            output_dir=tmp_output_dir,
            working_dir=tmp_output_dir.parent.parent,
        )

        mock_response = json.dumps({
            "score": 4,
            "confidence": 0.85,
            "reasoning": "Good actionability with clear locations",
            "evidence_cited": [],
            "recommendations": [],
            "sub_scores": {},
        })

        with patch.object(judge, "invoke_claude", return_value=mock_response):
            result = judge.evaluate()

        assert result.dimension == "actionability"
        assert result.score == 4


# ============================================================================
# BaseJudge Tests
# ============================================================================


class TestBaseJudge:
    """Tests for BaseJudge common functionality."""

    def test_build_prompt(self, tmp_path):
        """Test prompt building with evidence substitution."""
        judge = DuplicationAccuracyJudge(working_dir=tmp_path)

        # Include required placeholder keys that the prompt template expects
        evidence = {
            "key": "value",
            "count": 42,
            "evaluation_mode": "synthetic",
            "synthetic_baseline": "N/A - synthetic mode",
            "interpretation_guidance": "Strict ground truth evaluation",
            "analysis_summary": {},
            "sample_duplications": [],
            "file_metrics": [],
        }
        prompt = judge.build_prompt(evidence)

        assert '"key": "value"' in prompt
        assert '"count": 42' in prompt
        assert "{{ evidence }}" not in prompt

    def test_parse_response_extracts_json_from_mixed_text(self, tmp_path):
        """Test JSON extraction from response with surrounding text."""
        judge = DuplicationAccuracyJudge(working_dir=tmp_path)

        response = """Here is my analysis:

```json
{
  "score": 4,
  "confidence": 0.9,
  "reasoning": "Good results",
  "evidence_cited": [],
  "recommendations": [],
  "sub_scores": {}
}
```

Additional thoughts..."""

        result = judge.parse_response(response)

        assert result.score == 4
        assert result.confidence == 0.9

    def test_parse_response_fallback_score_extraction(self, tmp_path):
        """Test fallback score extraction from various text formats."""
        judge = DuplicationAccuracyJudge(working_dir=tmp_path)

        # Test "score: X" format
        result1 = judge.parse_response("Overall score: 4 points")
        assert result1.score == 4

        # Test "score:X" format (no space)
        result2 = judge.parse_response("The score:2 is low")
        assert result2.score == 2

        # Test highest score extraction (should find 5 first)
        result3 = judge.parse_response("score: 5 is excellent, score: 3 is okay")
        assert result3.score == 5

    def test_load_all_analysis_results_multiple_files(self, tmp_path):
        """Test loading multiple analysis files."""
        output_dir = tmp_path / "output" / "runs"
        output_dir.mkdir(parents=True)

        (output_dir / "repo1.json").write_text(json.dumps({"summary": {"total_clones": 5}}))
        (output_dir / "repo2.json").write_text(json.dumps({"summary": {"total_clones": 3}}))
        (output_dir / ".hidden.json").write_text(json.dumps({"should": "skip"}))

        judge = DuplicationAccuracyJudge(output_dir=output_dir, working_dir=tmp_path)

        results = judge.load_all_analysis_results()

        assert len(results) == 2
        assert "repo1" in results
        assert "repo2" in results
        assert ".hidden" not in results
        assert results["repo1"]["summary"]["total_clones"] == 5

    def test_load_all_analysis_results_with_output_dir(self, tmp_path):
        """Test loading analysis results from output_dir."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        # Create analysis file in output_dir
        analysis_file = output_dir / "analysis.json"
        analysis_file.write_text(json.dumps({"summary": {"total_clones": 7}}))

        judge = DuplicationAccuracyJudge(
            output_dir=output_dir,
            working_dir=tmp_path,
        )

        results = judge.load_all_analysis_results()

        assert len(results) == 1
        assert results["analysis"]["summary"]["total_clones"] == 7


# ============================================================================
# Integration Tests (Still Mocked)
# ============================================================================


class TestJudgeIntegration:
    """Integration tests for judge workflows (with mocked Claude)."""

    def test_all_judges_have_unique_dimension_names(self, tmp_path):
        """Verify all judges have unique dimension names."""
        judges = [
            DuplicationAccuracyJudge(working_dir=tmp_path),
            SemanticDetectionJudge(working_dir=tmp_path),
            CrossFileDetectionJudge(working_dir=tmp_path),
            ActionabilityJudge(working_dir=tmp_path),
        ]

        dimension_names = [j.dimension_name for j in judges]

        assert len(dimension_names) == len(set(dimension_names))

    def test_all_judges_weights_sum_to_one(self, tmp_path):
        """Verify all judge weights sum to 1.0."""
        judges = [
            DuplicationAccuracyJudge(working_dir=tmp_path),
            SemanticDetectionJudge(working_dir=tmp_path),
            CrossFileDetectionJudge(working_dir=tmp_path),
            ActionabilityJudge(working_dir=tmp_path),
        ]

        total_weight = sum(j.weight for j in judges)

        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error

    def test_all_judges_produce_results_with_mocked_response(self, tmp_output_dir):
        """Test that all judges produce valid results with mocked responses."""
        judges = [
            DuplicationAccuracyJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
            SemanticDetectionJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
            CrossFileDetectionJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
            ActionabilityJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
        ]

        mock_response = json.dumps({
            "score": 4,
            "confidence": 0.85,
            "reasoning": "Test reasoning",
            "evidence_cited": [],
            "recommendations": [],
            "sub_scores": {},
        })

        for judge in judges:
            with patch.object(judge, "invoke_claude", return_value=mock_response):
                result = judge.evaluate()

            assert isinstance(result, JudgeResult)
            assert result.score == 4
            assert result.confidence == 0.85
            assert result.dimension == judge.dimension_name

    def test_evidence_collection_performance(self, tmp_output_dir):
        """Test that evidence collection completes quickly."""
        import time

        judges = [
            DuplicationAccuracyJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
            SemanticDetectionJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
            CrossFileDetectionJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
            ActionabilityJudge(
                output_dir=tmp_output_dir,
                working_dir=tmp_output_dir.parent.parent,
            ),
        ]

        for judge in judges:
            start = time.time()
            evidence = judge.collect_evidence()
            elapsed = time.time() - start

            assert elapsed < 1.0, f"{judge.dimension_name} evidence collection took {elapsed:.2f}s"
            assert isinstance(evidence, dict)
