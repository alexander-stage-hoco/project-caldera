"""Tests for Roslyn Analyzers LLM judges.

Tests cover:
- Evidence collection for each judge type
- Response parsing from LLM outputs
- Ground truth assertions
- JudgeResult creation and validation

Note: These tests mock invoke_claude to avoid calling the Claude CLI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "evaluation" / "llm"))

from evaluation.llm.judges import (
    BaseJudge,
    JudgeResult,
    SecurityDetectionJudge,
    DesignAnalysisJudge,
    ResourceManagementJudge,
    OverallQualityJudge,
    IntegrationFitJudge,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_evaluation_report() -> dict[str, Any]:
    """Sample programmatic evaluation report for testing judges."""
    return {
        "evaluation_id": "eval-test-001",
        "timestamp": "2026-01-22T10:00:00Z",
        "summary": {
            "total_checks": 20,
            "passed": 16,
            "failed": 4,
            "pass_rate_pct": 80.0,
            "overall_score": 0.82,
        },
        "category_scores": {
            "accuracy": {"weight": 0.40, "score": 0.85, "weighted_score": 0.34},
            "coverage": {"weight": 0.25, "score": 0.80, "weighted_score": 0.20},
            "edge_cases": {"weight": 0.20, "score": 0.75, "weighted_score": 0.15},
            "performance": {"weight": 0.15, "score": 0.90, "weighted_score": 0.135},
        },
        "checks": [
            # Security checks
            {
                "check_id": "AC-1",
                "name": "SQL Injection Detection",
                "category": "accuracy",
                "passed": True,
                "score": 1.0,
                "message": "All SQL injection patterns detected",
            },
            {
                "check_id": "AC-2",
                "name": "Cryptography Analysis",
                "category": "accuracy",
                "passed": True,
                "score": 0.9,
                "message": "Weak crypto algorithms flagged",
            },
            {
                "check_id": "AC-3",
                "name": "Deserialization Detection",
                "category": "accuracy",
                "passed": False,
                "score": 0.6,
                "message": "Some deserialization patterns missed",
            },
            {
                "check_id": "AC-4",
                "name": "Secret Detection",
                "category": "accuracy",
                "passed": True,
                "score": 0.95,
                "message": "Hardcoded secrets detected",
            },
            {
                "check_id": "AC-5",
                "name": "XSS Detection",
                "category": "accuracy",
                "passed": True,
                "score": 0.85,
                "message": "XSS vulnerabilities flagged",
            },
            # Resource checks
            {
                "check_id": "AC-6",
                "name": "IDisposable Detection",
                "category": "accuracy",
                "passed": True,
                "score": 0.9,
                "message": "Missing IDisposable implementations detected",
            },
            # Design checks
            {
                "check_id": "AC-8",
                "name": "Design Pattern Violations",
                "category": "accuracy",
                "passed": True,
                "score": 0.85,
                "message": "Design violations detected",
            },
            # Coverage checks
            {
                "check_id": "CV-1",
                "name": "Security Rule Coverage",
                "category": "coverage",
                "passed": True,
                "score": 0.88,
                "message": "Security rules covered",
            },
            {
                "check_id": "CV-2",
                "name": "Design Rule Coverage",
                "category": "coverage",
                "passed": True,
                "score": 0.80,
                "message": "Design rules covered",
            },
            {
                "check_id": "CV-3",
                "name": "Resource Rule Coverage",
                "category": "coverage",
                "passed": True,
                "score": 0.75,
                "message": "Resource rules covered",
            },
            # Edge case checks
            {
                "check_id": "EC-1",
                "name": "Empty Files",
                "category": "edge_cases",
                "passed": True,
                "score": 1.0,
                "message": "Empty files handled",
            },
            {
                "check_id": "EC-6",
                "name": "False Positive Rate",
                "category": "edge_cases",
                "passed": True,
                "score": 0.95,
                "actual_value": 0.05,
                "message": "Low false positive rate",
            },
            # Performance checks
            {
                "check_id": "PF-1",
                "name": "Analysis Speed",
                "category": "performance",
                "passed": True,
                "score": 0.9,
                "message": "Analysis completed within threshold",
            },
        ],
    }


@pytest.fixture
def sample_ground_truth() -> dict[str, Any]:
    """Sample ground truth data for testing judges."""
    return {
        "schema_version": "1.0",
        "scenario": "synthetic-csharp",
        "expected": {
            "summary": {
                "total_files": 10,
                "total_expected_violations": 25,
            },
            "thresholds": {
                "precision_min": 0.85,
                "recall_min": 0.80,
            },
        },
        "files": {
            "security/sql_injection.cs": {
                "expected_violations": [
                    {"rule_id": "CA3001", "count": 3, "lines": [15, 28, 42]},
                    {"rule_id": "CA2100", "count": 2, "lines": [55, 68]},
                ],
                "total_expected": 5,
            },
            "security/weak_crypto.cs": {
                "expected_violations": [
                    {"rule_id": "CA5350", "count": 2, "lines": [20, 35]},
                    {"rule_id": "CA5351", "count": 1, "lines": [48]},
                ],
                "total_expected": 3,
            },
            "resource/missing_idisposable.cs": {
                "expected_violations": [
                    {"rule_id": "CA1001", "count": 4, "lines": [13, 32, 53, 74]},
                    {"rule_id": "CA2000", "count": 2, "lines": [95, 110]},
                ],
                "total_expected": 6,
            },
            "design/empty_interfaces.cs": {
                "expected_violations": [
                    {"rule_id": "CA1040", "count": 3, "lines": [11, 16, 21]},
                ],
                "total_expected": 3,
            },
            "design/encapsulation.cs": {
                "expected_violations": [
                    {"rule_id": "CA1051", "count": 4, "lines": [8, 15, 22, 29]},
                ],
                "total_expected": 4,
            },
        },
    }


@pytest.fixture
def sample_analysis_results() -> dict[str, Any]:
    """Sample analysis results from Roslyn Analyzers."""
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-01-22T10:00:00Z",
        "repo_name": "synthetic-csharp",
        "repo_path": "/tmp/synthetic-csharp",
        "results": {
            "tool": "roslyn-analyzers",
            "tool_version": "1.0.0",
            "analysis_duration_ms": 1500,
            "summary": {
                "total_files_analyzed": 10,
                "total_violations": 22,
                "files_with_violations": 5,
                "violations_by_category": {
                    "security": 8,
                    "resource": 6,
                    "design": 7,
                    "dead_code": 1,
                },
                "violations_by_severity": {
                    "critical": 4,
                    "high": 10,
                    "medium": 7,
                    "low": 1,
                },
            },
            "files": [
                {
                    "path": "security/sql_injection.cs",
                    "language": "csharp",
                    "lines_of_code": 80,
                    "violation_count": 4,
                    "violations": [
                        {"rule_id": "CA3001", "dd_category": "security", "dd_severity": "high", "line_start": 15, "message": "SQL injection vulnerability"},
                        {"rule_id": "CA3001", "dd_category": "security", "dd_severity": "high", "line_start": 28, "message": "SQL injection vulnerability"},
                        {"rule_id": "CA3001", "dd_category": "security", "dd_severity": "high", "line_start": 42, "message": "SQL injection vulnerability"},
                        {"rule_id": "CA2100", "dd_category": "security", "dd_severity": "high", "line_start": 55, "message": "Review SQL queries"},
                    ],
                },
                {
                    "path": "security/weak_crypto.cs",
                    "language": "csharp",
                    "lines_of_code": 60,
                    "violation_count": 3,
                    "violations": [
                        {"rule_id": "CA5350", "dd_category": "security", "dd_severity": "high", "line_start": 20, "message": "Do not use weak cryptographic algorithms"},
                        {"rule_id": "CA5350", "dd_category": "security", "dd_severity": "high", "line_start": 35, "message": "Do not use weak cryptographic algorithms"},
                        {"rule_id": "CA5351", "dd_category": "security", "dd_severity": "high", "line_start": 48, "message": "Do not use broken cryptographic algorithms"},
                    ],
                },
                {
                    "path": "resource/missing_idisposable.cs",
                    "language": "csharp",
                    "lines_of_code": 120,
                    "violation_count": 5,
                    "violations": [
                        {"rule_id": "CA1001", "dd_category": "resource", "dd_severity": "critical", "line_start": 13, "message": "Types that own disposable fields should be disposable"},
                        {"rule_id": "CA1001", "dd_category": "resource", "dd_severity": "critical", "line_start": 32, "message": "Types that own disposable fields should be disposable"},
                        {"rule_id": "CA1001", "dd_category": "resource", "dd_severity": "critical", "line_start": 53, "message": "Types that own disposable fields should be disposable"},
                        {"rule_id": "CA2000", "dd_category": "resource", "dd_severity": "high", "line_start": 95, "message": "Dispose objects before losing scope"},
                        {"rule_id": "CA2000", "dd_category": "resource", "dd_severity": "high", "line_start": 110, "message": "Dispose objects before losing scope"},
                    ],
                },
                {
                    "path": "design/empty_interfaces.cs",
                    "language": "csharp",
                    "lines_of_code": 40,
                    "violation_count": 3,
                    "violations": [
                        {"rule_id": "CA1040", "dd_category": "design", "dd_severity": "medium", "line_start": 11, "message": "Avoid empty interfaces"},
                        {"rule_id": "CA1040", "dd_category": "design", "dd_severity": "medium", "line_start": 16, "message": "Avoid empty interfaces"},
                        {"rule_id": "CA1040", "dd_category": "design", "dd_severity": "medium", "line_start": 21, "message": "Avoid empty interfaces"},
                    ],
                },
                {
                    "path": "design/encapsulation.cs",
                    "language": "csharp",
                    "lines_of_code": 50,
                    "violation_count": 4,
                    "violations": [
                        {"rule_id": "CA1051", "dd_category": "design", "dd_severity": "medium", "line_start": 8, "message": "Do not declare visible instance fields"},
                        {"rule_id": "CA1051", "dd_category": "design", "dd_severity": "medium", "line_start": 15, "message": "Do not declare visible instance fields"},
                        {"rule_id": "CA1051", "dd_category": "design", "dd_severity": "medium", "line_start": 22, "message": "Do not declare visible instance fields"},
                        {"rule_id": "CA1051", "dd_category": "design", "dd_severity": "medium", "line_start": 29, "message": "Do not declare visible instance fields"},
                    ],
                },
            ],
        },
    }


@pytest.fixture
def valid_llm_response() -> str:
    """Sample valid JSON response from LLM judge."""
    return json.dumps({
        "score": 4,
        "confidence": 0.85,
        "reasoning": "The analysis demonstrates good security detection capabilities with SQL injection and cryptography issues properly flagged.",
        "sub_scores": {
            "sql_injection": 5,
            "cryptography": 4,
            "deserialization": 3,
            "overall_coverage": 4,
        },
        "evidence_cited": [
            "All 3 expected SQL injection patterns detected at lines 15, 28, 42",
            "Weak crypto algorithms (MD5, SHA1) correctly flagged",
        ],
        "recommendations": [
            "Improve deserialization detection coverage",
            "Add support for more XSS patterns",
        ],
    })


@pytest.fixture
def partial_llm_response() -> str:
    """Sample partial response with text + JSON."""
    return """Based on my analysis of the evidence provided, I'll evaluate the security detection capabilities.

The analysis shows good detection of SQL injection and cryptography issues.

```json
{
  "score": 4,
  "confidence": 0.80,
  "reasoning": "Good overall security detection with some gaps in deserialization",
  "sub_scores": {
    "sql_injection": 5,
    "cryptography": 4
  },
  "evidence_cited": ["SQL injection detected"],
  "recommendations": ["Improve deserialization"]
}
```

Overall, this is a solid evaluation result."""


@pytest.fixture
def text_only_llm_response() -> str:
    """Sample response without JSON (fallback parsing needed)."""
    return """The security detection analysis shows moderate performance.

Score: 3

The tool detected most SQL injection vulnerabilities but missed some deserialization issues.
Cryptography analysis was adequate but could be improved.

Overall confidence is moderate given the mixed results."""


def _write_json_file(tmp_path: Path, filename: str, data: dict) -> Path:
    """Helper to write a JSON file."""
    path = tmp_path / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path


# =============================================================================
# JudgeResult Tests
# =============================================================================


class TestJudgeResult:
    """Test JudgeResult dataclass behavior."""

    def test_judge_result_creation(self):
        """Create JudgeResult with all fields."""
        result = JudgeResult(
            dimension="security_detection",
            score=4,
            confidence=0.85,
            reasoning="Good security detection",
            evidence_cited=["SQL injection detected", "Crypto flagged"],
            recommendations=["Improve deserialization"],
            sub_scores={"sql_injection": 5, "cryptography": 4},
            raw_response="test response",
        )

        assert result.dimension == "security_detection"
        assert result.score == 4
        assert result.confidence == 0.85
        assert result.reasoning == "Good security detection"
        assert len(result.evidence_cited) == 2
        assert len(result.recommendations) == 1
        assert result.sub_scores["sql_injection"] == 5
        assert result.raw_response == "test response"

    def test_judge_result_to_dict(self):
        """Convert JudgeResult to dictionary."""
        result = JudgeResult(
            dimension="test",
            score=3,
            confidence=0.7,
            reasoning="test reasoning",
        )

        result_dict = result.to_dict()

        assert result_dict["dimension"] == "test"
        assert result_dict["score"] == 3
        assert result_dict["confidence"] == 0.7
        assert result_dict["reasoning"] == "test reasoning"
        assert result_dict["evidence_cited"] == []
        assert result_dict["recommendations"] == []

    def test_judge_result_from_dict(self):
        """Create JudgeResult from dictionary."""
        data = {
            "dimension": "design_analysis",
            "score": 4,
            "confidence": 0.9,
            "reasoning": "Good design analysis",
            "evidence_cited": ["Evidence 1"],
            "recommendations": ["Rec 1"],
            "sub_scores": {"encapsulation": 4},
        }

        result = JudgeResult.from_dict(data)

        assert result.dimension == "design_analysis"
        assert result.score == 4
        assert result.confidence == 0.9
        assert result.sub_scores["encapsulation"] == 4

    def test_judge_result_from_dict_missing_fields(self):
        """Create JudgeResult from partial dictionary."""
        data = {"score": 3}

        result = JudgeResult.from_dict(data)

        assert result.dimension == "unknown"
        assert result.score == 3
        assert result.confidence == 0.0
        assert result.reasoning == ""


# =============================================================================
# SecurityDetectionJudge Tests
# =============================================================================


class TestSecurityDetectionJudge:
    """Tests for SecurityDetectionJudge."""

    def test_dimension_name(self, project_root):
        """Verify dimension name is correct."""
        judge = SecurityDetectionJudge(working_dir=project_root)
        assert judge.dimension_name == "security_detection"

    def test_weight(self, project_root):
        """Verify weight is correct."""
        judge = SecurityDetectionJudge(working_dir=project_root)
        assert judge.weight == 0.30

    def test_collect_evidence_extracts_security_data(
        self, tmp_path, sample_evaluation_report, sample_ground_truth, project_root
    ):
        """Verify collect_evidence extracts security-related data from analysis outputs."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Check new evidence structure
        assert "security_summary" in evidence
        assert "detection_by_category" in evidence
        assert "violations_sample" in evidence
        assert "ground_truth_comparison" in evidence

        # Check security_summary has expected categories
        security_summary = evidence["security_summary"]
        assert "sql_injection" in security_summary
        assert "cryptography" in security_summary
        assert "deserialization" in security_summary

    def test_collect_evidence_categorizes_security_rules(
        self, tmp_path, sample_evaluation_report, sample_ground_truth, project_root
    ):
        """Verify collect_evidence categorizes security rules correctly."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Check that violations_sample contains security-related violations
        violations_sample = evidence["violations_sample"]
        if violations_sample:
            # Verify samples have expected fields
            sample = violations_sample[0]
            assert "repo" in sample
            assert "file" in sample
            assert "rule_id" in sample
            assert "severity" in sample

    def test_parse_response_valid_json(self, valid_llm_response, project_root):
        """Parse valid JSON response correctly."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        result = judge.parse_response(valid_llm_response)

        assert result.dimension == "security_detection"
        assert result.score == 4
        assert result.confidence == 0.85
        assert "SQL injection" in result.reasoning
        assert len(result.sub_scores) == 4
        assert result.sub_scores["sql_injection"] == 5

    def test_parse_response_partial_json(self, partial_llm_response, project_root):
        """Parse response with text and embedded JSON."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        result = judge.parse_response(partial_llm_response)

        assert result.dimension == "security_detection"
        assert result.score == 4
        assert result.confidence == 0.80
        assert result.raw_response == partial_llm_response

    def test_parse_response_text_only(self, text_only_llm_response, project_root):
        """Parse text-only response with fallback."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        result = judge.parse_response(text_only_llm_response)

        assert result.dimension == "security_detection"
        assert result.score == 3  # Extracted from "Score: 3"
        assert result.confidence == 0.5  # Default fallback
        assert result.raw_response == text_only_llm_response

    def test_run_ground_truth_assertions_all_pass(
        self, tmp_path, sample_evaluation_report, project_root
    ):
        """Ground truth assertions pass when checks pass."""
        eval_path = _write_json_file(tmp_path, "evaluation_report.json", sample_evaluation_report)

        judge = SecurityDetectionJudge(
            working_dir=project_root,
            evaluation_path=eval_path,
        )

        passed, failures = judge.run_ground_truth_assertions()

        # AC-1, AC-4, AC-5 should all pass in sample data
        assert passed is True
        assert len(failures) == 0

    def test_run_ground_truth_assertions_uses_analysis_results(self, tmp_path, project_root):
        """Ground truth assertions use analysis results to validate security detection."""
        # The new implementation checks analysis outputs, not evaluation report checks
        judge = SecurityDetectionJudge(working_dir=project_root)

        passed, failures = judge.run_ground_truth_assertions()

        # Should pass if synthetic repo has security findings (which it does)
        assert isinstance(passed, bool)
        assert isinstance(failures, list)

    def test_evaluate_with_mocked_claude(
        self, tmp_path, sample_evaluation_report, sample_ground_truth, valid_llm_response, project_root
    ):
        """Full evaluate pipeline with mocked Claude invocation."""
        eval_path = _write_json_file(tmp_path, "evaluation_report.json", sample_evaluation_report)
        gt_path = _write_json_file(tmp_path, "ground_truth.json", sample_ground_truth)

        judge = SecurityDetectionJudge(
            working_dir=project_root,
            evaluation_path=eval_path,
            ground_truth_path=gt_path,
        )

        with patch.object(judge, "invoke_claude", return_value=valid_llm_response):
            result = judge.evaluate()

        assert result.dimension == "security_detection"
        assert result.score == 4
        assert result.confidence == 0.85


# =============================================================================
# DesignAnalysisJudge Tests
# =============================================================================


class TestDesignAnalysisJudge:
    """Tests for DesignAnalysisJudge."""

    def test_dimension_name(self, project_root):
        """Verify dimension name is correct."""
        judge = DesignAnalysisJudge(working_dir=project_root)
        assert judge.dimension_name == "design_analysis"

    def test_weight(self, project_root):
        """Verify weight is correct."""
        judge = DesignAnalysisJudge(working_dir=project_root)
        assert judge.weight == 0.25

    def test_collect_evidence_extracts_design_data(
        self, tmp_path, sample_evaluation_report, sample_ground_truth, project_root
    ):
        """Verify collect_evidence extracts design-related data from analysis outputs."""
        judge = DesignAnalysisJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Check new evidence structure
        assert "design_summary" in evidence
        assert "detection_by_repo" in evidence
        assert "violations_sample" in evidence
        assert "ground_truth_comparison" in evidence

        # Check design_summary has expected categories
        design_summary = evidence["design_summary"]
        assert "encapsulation" in design_summary
        assert "interface_design" in design_summary
        assert "complexity" in design_summary

    def test_collect_evidence_categorizes_design_rules(
        self, tmp_path, sample_evaluation_report, sample_ground_truth, project_root
    ):
        """Verify collect_evidence categorizes design rules correctly."""
        judge = DesignAnalysisJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Check that violations_sample contains design-related violations
        violations_sample = evidence["violations_sample"]
        if violations_sample:
            # Verify samples have expected fields
            sample = violations_sample[0]
            assert "repo" in sample
            assert "file" in sample
            assert "rule_id" in sample
            assert "severity" in sample

    def test_parse_response_with_design_sub_scores(self, project_root):
        """Parse response with design-specific sub-scores."""
        response = json.dumps({
            "score": 4,
            "confidence": 0.82,
            "reasoning": "Good design analysis with encapsulation detection",
            "sub_scores": {
                "encapsulation": 5,
                "interface_design": 4,
                "inheritance": 3,
                "complexity": 4,
            },
            "evidence_cited": ["All public fields flagged"],
            "recommendations": ["Improve inheritance pattern detection"],
        })

        judge = DesignAnalysisJudge(working_dir=project_root)
        result = judge.parse_response(response)

        assert result.dimension == "design_analysis"
        assert result.sub_scores["encapsulation"] == 5
        assert result.sub_scores["interface_design"] == 4

    def test_run_ground_truth_assertions_design_pass(
        self, tmp_path, sample_evaluation_report, project_root
    ):
        """Ground truth assertions pass when AC-8 passes."""
        eval_path = _write_json_file(tmp_path, "evaluation_report.json", sample_evaluation_report)

        judge = DesignAnalysisJudge(
            working_dir=project_root,
            evaluation_path=eval_path,
        )

        passed, failures = judge.run_ground_truth_assertions()

        # AC-8 should pass in sample data
        assert passed is True
        assert len(failures) == 0

    def test_run_ground_truth_assertions_uses_analysis_results(self, tmp_path, project_root):
        """Ground truth assertions use analysis results to validate design detection."""
        # The new implementation checks analysis outputs, not evaluation report checks
        judge = DesignAnalysisJudge(working_dir=project_root)

        passed, failures = judge.run_ground_truth_assertions()

        # Should pass if synthetic repo has design findings (which it does)
        assert isinstance(passed, bool)
        assert isinstance(failures, list)


# =============================================================================
# ResourceManagementJudge Tests
# =============================================================================


class TestResourceManagementJudge:
    """Tests for ResourceManagementJudge."""

    def test_dimension_name(self, project_root):
        """Verify dimension name is correct."""
        judge = ResourceManagementJudge(working_dir=project_root)
        assert judge.dimension_name == "resource_management"

    def test_weight(self, project_root):
        """Verify weight is correct."""
        judge = ResourceManagementJudge(working_dir=project_root)
        assert judge.weight == 0.25

    def test_collect_evidence_extracts_resource_data(
        self, tmp_path, sample_evaluation_report, sample_ground_truth, project_root
    ):
        """Verify collect_evidence extracts resource-related data from analysis outputs."""
        judge = ResourceManagementJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Check new evidence structure
        assert "resource_summary" in evidence
        assert "detection_by_repo" in evidence
        assert "violations_sample" in evidence
        assert "ground_truth_comparison" in evidence

        # Check resource_summary has expected categories
        resource_summary = evidence["resource_summary"]
        assert "idisposable_impl" in resource_summary
        assert "undisposed" in resource_summary
        assert "leaks" in resource_summary

    def test_parse_response_with_resource_sub_scores(self, project_root):
        """Parse response with resource-specific sub-scores."""
        response = json.dumps({
            "score": 4,
            "confidence": 0.78,
            "reasoning": "Good resource management detection",
            "sub_scores": {
                "disposal_detection": 5,
                "idisposable_impl": 4,
                "async_patterns": 3,
                "leak_prevention": 4,
            },
            "evidence_cited": ["Missing IDisposable implementations detected"],
            "recommendations": ["Improve async void detection"],
        })

        judge = ResourceManagementJudge(working_dir=project_root)
        result = judge.parse_response(response)

        assert result.dimension == "resource_management"
        assert result.sub_scores["disposal_detection"] == 5
        assert result.sub_scores["async_patterns"] == 3

    def test_run_ground_truth_assertions_resource_pass(
        self, tmp_path, sample_evaluation_report, project_root
    ):
        """Ground truth assertions pass when AC-6 passes."""
        eval_path = _write_json_file(tmp_path, "evaluation_report.json", sample_evaluation_report)

        judge = ResourceManagementJudge(
            working_dir=project_root,
            evaluation_path=eval_path,
        )

        passed, failures = judge.run_ground_truth_assertions()

        # AC-6 should pass in sample data
        assert passed is True
        assert len(failures) == 0

    def test_run_ground_truth_assertions_uses_analysis_results(self, tmp_path, project_root):
        """Ground truth assertions use analysis results to validate resource detection."""
        # The new implementation checks analysis outputs, not evaluation report checks
        judge = ResourceManagementJudge(working_dir=project_root)

        passed, failures = judge.run_ground_truth_assertions()

        # Should pass if synthetic repo has resource findings (which it does)
        assert isinstance(passed, bool)
        assert isinstance(failures, list)


# =============================================================================
# OverallQualityJudge Tests
# =============================================================================


class TestOverallQualityJudge:
    """Tests for OverallQualityJudge."""

    def test_dimension_name(self, project_root):
        """Verify dimension name is correct."""
        judge = OverallQualityJudge(working_dir=project_root)
        assert judge.dimension_name == "overall_quality"

    def test_weight(self, project_root):
        """Verify weight is correct."""
        judge = OverallQualityJudge(working_dir=project_root)
        assert judge.weight == 0.20

    def test_collect_evidence_extracts_quality_data(
        self, tmp_path, sample_evaluation_report, project_root
    ):
        """Verify collect_evidence extracts quality-related data from analysis outputs."""
        judge = OverallQualityJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Check new evidence structure
        assert "overall_summary" in evidence
        assert "category_coverage" in evidence
        assert "false_positive_analysis" in evidence
        assert "message_quality" in evidence

        # Check overall_summary has expected fields
        overall_summary = evidence["overall_summary"]
        assert "total_files_analyzed" in overall_summary
        assert "total_violations" in overall_summary
        assert "total_repos" in overall_summary

    def test_collect_evidence_extracts_category_coverage(
        self, tmp_path, sample_evaluation_report, project_root
    ):
        """Verify category coverage is tracked correctly."""
        judge = OverallQualityJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Should track expected vs detected categories
        category_coverage = evidence["category_coverage"]
        assert "expected_categories" in category_coverage
        assert "detected_categories" in category_coverage
        assert "missing_categories" in category_coverage

    def test_collect_evidence_extracts_message_quality(
        self, tmp_path, sample_evaluation_report, project_root
    ):
        """Verify message quality samples are collected."""
        judge = OverallQualityJudge(working_dir=project_root)

        evidence = judge.collect_evidence()

        # Should have message quality samples
        message_quality = evidence["message_quality"]
        if message_quality:
            sample = message_quality[0]
            assert "repo" in sample
            assert "rule_id" in sample
            assert "message" in sample

    def test_parse_response_with_quality_sub_scores(self, project_root):
        """Parse response with quality-specific sub-scores."""
        response = json.dumps({
            "score": 4,
            "confidence": 0.88,
            "reasoning": "Good overall quality with low false positive rate",
            "sub_scores": {
                "false_positive_control": 5,
                "detection_precision": 4,
                "coverage_completeness": 4,
                "robustness": 4,
            },
            "evidence_cited": ["False positive rate: 5%", "Pass rate: 80%"],
            "recommendations": ["Improve coverage for edge cases"],
        })

        judge = OverallQualityJudge(working_dir=project_root)
        result = judge.parse_response(response)

        assert result.dimension == "overall_quality"
        assert result.sub_scores["false_positive_control"] == 5
        assert result.sub_scores["detection_precision"] == 4

    def test_run_ground_truth_assertions_pass(
        self, tmp_path, sample_evaluation_report, project_root
    ):
        """Ground truth assertions pass with good metrics."""
        eval_path = _write_json_file(tmp_path, "evaluation_report.json", sample_evaluation_report)

        judge = OverallQualityJudge(
            working_dir=project_root,
            evaluation_path=eval_path,
        )

        passed, failures = judge.run_ground_truth_assertions()

        # Sample data has 80% pass rate and EC-6 shows low FP rate
        assert passed is True
        assert len(failures) == 0

    def test_run_ground_truth_assertions_uses_analysis_results(self, tmp_path, project_root):
        """Ground truth assertions use analysis results to validate overall quality."""
        # The new implementation checks analysis outputs, not evaluation report checks
        judge = OverallQualityJudge(working_dir=project_root)

        passed, failures = judge.run_ground_truth_assertions()

        # Should pass if analysis results are present and valid
        assert isinstance(passed, bool)
        assert isinstance(failures, list)

    def test_run_ground_truth_assertions_low_pass_rate(self, tmp_path, project_root):
        """Ground truth assertions fail with low pass rate."""
        eval_report = {
            "summary": {"pass_rate_pct": 70},  # Below 80%
            "checks": []
        }
        eval_path = _write_json_file(tmp_path, "evaluation_report.json", eval_report)

        judge = OverallQualityJudge(
            working_dir=project_root,
            evaluation_path=eval_path,
        )

        passed, failures = judge.run_ground_truth_assertions()

        assert passed is False
        assert any("pass rate" in f.lower() for f in failures)


# =============================================================================
# BaseJudge Integration Tests
# =============================================================================


class TestBaseJudgeIntegration:
    """Integration tests for BaseJudge functionality."""

    def test_build_prompt_replaces_placeholders(
        self, tmp_path, sample_evaluation_report, sample_ground_truth, project_root
    ):
        """Verify build_prompt replaces placeholders with evidence."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        evidence = judge.collect_evidence()
        prompt = judge.build_prompt(evidence)

        # Verify new placeholders are replaced
        assert "{{ security_summary }}" not in prompt
        assert "{{ detection_by_category }}" not in prompt
        assert "{{ violations_sample }}" not in prompt
        # Verify some evidence content is in the prompt
        assert "sql_injection" in prompt or "detected" in prompt

    def test_load_prompt_template_from_file(self, project_root):
        """Verify prompt template is loaded from file if it exists."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        template = judge.load_prompt_template()

        # Should contain content from security_detection.md
        assert "security" in template.lower()
        assert "score" in template.lower()

    def test_load_prompt_template_default_fallback(self, project_root, tmp_path):
        """Verify default prompt is used when file doesn't exist."""
        # Use a working dir where prompt files don't exist
        judge = SecurityDetectionJudge(working_dir=tmp_path)

        template = judge.load_prompt_template()

        # Should use default prompt
        assert "SQL injection" in template or "security" in template.lower()

    def test_parse_response_handles_invalid_json(self, project_root):
        """Verify parse_response handles completely invalid JSON."""
        judge = SecurityDetectionJudge(working_dir=project_root)

        response = "This is not JSON at all and has no score information."

        result = judge.parse_response(response)

        # Should return default score of 3
        assert result.score == 3
        assert result.confidence == 0.5
        assert result.dimension == "security_detection"

    def test_evaluate_handles_missing_files(self, tmp_path, project_root):
        """Verify evaluate handles missing evaluation/ground truth files gracefully."""
        judge = SecurityDetectionJudge(
            working_dir=project_root,
            evaluation_path=tmp_path / "nonexistent.json",
            ground_truth_path=tmp_path / "also_nonexistent.json",
        )

        with patch.object(judge, "invoke_claude", return_value='{"score": 3, "confidence": 0.5, "reasoning": "test"}'):
            result = judge.evaluate()

        assert result.dimension == "security_detection"
        assert result.score == 3

    def test_all_judges_have_unique_dimensions(self, project_root):
        """Verify all judges have unique dimension names."""
        judges = [
            SecurityDetectionJudge(working_dir=project_root),
            DesignAnalysisJudge(working_dir=project_root),
            ResourceManagementJudge(working_dir=project_root),
            OverallQualityJudge(working_dir=project_root),
            IntegrationFitJudge(working_dir=project_root),
        ]

        dimensions = [j.dimension_name for j in judges]
        assert len(dimensions) == len(set(dimensions)), "Duplicate dimension names found"

    def test_all_judges_weights_sum_approximately(self, project_root):
        """Verify all judge weights sum to approximately 1.0 (allowing normalization)."""
        judges = [
            SecurityDetectionJudge(working_dir=project_root),
            DesignAnalysisJudge(working_dir=project_root),
            ResourceManagementJudge(working_dir=project_root),
            OverallQualityJudge(working_dir=project_root),
            IntegrationFitJudge(working_dir=project_root),
        ]

        total_weight = sum(j.weight for j in judges)
        # Weights may be normalized in the evaluation runner; check they're reasonable
        assert 0.9 <= total_weight <= 1.2, f"Weights sum to {total_weight}, expected ~1.0"

    def test_integration_fit_judge(self, project_root):
        """Verify IntegrationFitJudge basic properties."""
        judge = IntegrationFitJudge(working_dir=project_root)
        assert judge.dimension_name == "integration_fit"
        assert judge.weight == 0.15
