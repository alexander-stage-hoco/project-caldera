"""Integration tests for LLM judge evaluation.

These tests require either:
1. ANTHROPIC_API_KEY environment variable set, OR
2. Claude CLI installed and configured

Tests are marked with @pytest.mark.llm and skipped if neither is available.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from evaluation.llm.judges import (
    SmellAccuracyJudge,
    RuleCoverageJudge,
    FalsePositiveRateJudge,
    ActionabilityJudge,
    JudgeResult,
)
from shared.evaluation.base_judge import HAS_ANTHROPIC_SDK


def llm_available() -> bool:
    """Check if LLM invocation is available (SDK or CLI)."""
    # Check for API key (SDK path)
    if HAS_ANTHROPIC_SDK and os.environ.get("ANTHROPIC_API_KEY"):
        return True
    # Check for Claude CLI
    if shutil.which("claude"):
        return True
    return False


# Skip all tests in this module if LLM not available
pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(
        not llm_available(),
        reason="LLM not available (need ANTHROPIC_API_KEY or claude CLI)"
    ),
]


@pytest.fixture
def sample_analysis_output(tmp_path: Path) -> Path:
    """Create a realistic sample analysis output for testing."""
    output_dir = tmp_path / "output" / "runs"
    output_dir.mkdir(parents=True)

    analysis = {
        "files": [
            {
                "path": "src/services/user_service.py",
                "language": "python",
                "smell_count": 3,
                "smells": [
                    {
                        "rule_id": "DD-D1-EMPTY-CATCH-python",
                        "dd_smell_id": "D1_EMPTY_CATCH",
                        "dd_category": "error_handling",
                        "severity": "WARNING",
                        "line_start": 45,
                        "line_end": 47,
                        "message": "Empty except block silently swallows exception. Add logging or specific error handling.",
                    },
                    {
                        "rule_id": "DD-F3-HTTPCLIENT-NEW-python",
                        "dd_smell_id": "F3_HTTPCLIENT_NEW",
                        "dd_category": "resource_management",
                        "severity": "WARNING",
                        "line_start": 23,
                        "line_end": 23,
                        "message": "Creating new HTTP client in method. Consider using a shared client for connection pooling.",
                    },
                    {
                        "rule_id": "python.lang.security.audit.hardcoded-password",
                        "dd_smell_id": "SEC_HARDCODED_CREDS",
                        "dd_category": "security",
                        "severity": "ERROR",
                        "line_start": 12,
                        "line_end": 12,
                        "message": "Hardcoded password detected. Use environment variables or a secrets manager.",
                    },
                ],
            },
            {
                "path": "src/utils/helpers.py",
                "language": "python",
                "smell_count": 1,
                "smells": [
                    {
                        "rule_id": "DD-I1-UNUSED-IMPORT-python",
                        "dd_smell_id": "I1_UNUSED_IMPORT",
                        "dd_category": "dead_code",
                        "severity": "INFO",
                        "line_start": 5,
                        "line_end": 5,
                        "message": "Unused import 'os'. Remove to clean up code.",
                    },
                ],
            },
            {
                "path": "tests/test_no_smell_clean.py",
                "language": "python",
                "smell_count": 0,
                "smells": [],
            },
        ],
        "summary": {
            "total_smells": 4,
            "total_files": 3,
            "files_with_smells": 2,
        },
    }

    (output_dir / "test_repo.json").write_text(json.dumps(analysis, indent=2))

    # Create ground truth
    gt_dir = tmp_path / "evaluation" / "ground-truth"
    gt_dir.mkdir(parents=True)

    ground_truth = {
        "language": "python",
        "files": {
            "user_service.py": {
                "expected_smells": ["D1_EMPTY_CATCH", "F3_HTTPCLIENT_NEW", "SEC_HARDCODED_CREDS"],
                "expected_count_min": 2,
                "expected_count_max": 5,
            },
            "helpers.py": {
                "expected_smells": ["I1_UNUSED_IMPORT"],
                "expected_count_min": 0,
                "expected_count_max": 2,
            },
            "test_no_smell_clean.py": {
                "expected_smells": [],
                "expected_count_min": 0,
                "expected_count_max": 0,
            },
        },
    }
    (gt_dir / "python.json").write_text(json.dumps(ground_truth, indent=2))

    return tmp_path


class TestSmellAccuracyJudgeIntegration:
    """Integration tests for SmellAccuracyJudge with real LLM."""

    def test_evaluate_with_real_llm(self, sample_analysis_output: Path):
        """Test full evaluation pipeline with real LLM.

        This test verifies:
        1. Evidence collection works
        2. Prompt building works (or gracefully handles placeholder issues)
        3. LLM invocation succeeds (if prompt builds successfully)
        4. Response parsing produces valid JudgeResult
        """
        judge = SmellAccuracyJudge(
            model="haiku",  # Use fastest/cheapest model for tests
            timeout=120,
            working_dir=sample_analysis_output,
            output_dir=sample_analysis_output / "output" / "runs",
        )

        result = judge.evaluate()

        # Verify result structure
        assert isinstance(result, JudgeResult)
        assert result.dimension == "smell_accuracy"
        assert 1 <= result.score <= 5
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.reasoning) > 0

    def test_collect_evidence_structure(self, sample_analysis_output: Path):
        """Test that evidence collection produces expected structure."""
        judge = SmellAccuracyJudge(
            working_dir=sample_analysis_output,
            output_dir=sample_analysis_output / "output" / "runs",
        )

        evidence = judge.collect_evidence()

        assert "sample_smells" in evidence
        assert "ground_truth_comparison" in evidence
        assert "by_category" in evidence
        assert "total_smells" in evidence
        assert evidence["total_smells"] == 4

    def test_ground_truth_assertions_pass(self, sample_analysis_output: Path):
        """Test ground truth assertions pass for valid data."""
        judge = SmellAccuracyJudge(
            working_dir=sample_analysis_output,
            output_dir=sample_analysis_output / "output" / "runs",
        )

        passed, failures = judge.run_ground_truth_assertions()

        assert passed, f"Assertions failed: {failures}"


class TestRuleCoverageJudgeIntegration:
    """Integration tests for RuleCoverageJudge."""

    def test_collect_evidence_structure(self, sample_analysis_output: Path):
        """Test evidence collection produces expected structure."""
        judge = RuleCoverageJudge(
            working_dir=sample_analysis_output,
            output_dir=sample_analysis_output / "output" / "runs",
        )

        evidence = judge.collect_evidence()

        assert "language_stats" in evidence
        assert "category_stats" in evidence
        assert "languages_covered" in evidence
        assert "categories_covered" in evidence


class TestFalsePositiveRateJudgeIntegration:
    """Integration tests for FalsePositiveRateJudge."""

    def test_collect_evidence_detects_clean_files(self, sample_analysis_output: Path):
        """Test that clean files are identified correctly."""
        judge = FalsePositiveRateJudge(
            working_dir=sample_analysis_output,
            output_dir=sample_analysis_output / "output" / "runs",
        )

        evidence = judge.collect_evidence()

        assert "clean_file_results" in evidence
        assert evidence["clean_files_tested"] >= 1
        # The no_smell file should have 0 smells
        for clean_file in evidence["clean_file_results"]:
            if "no_smell" in clean_file["file"]:
                assert clean_file["smell_count"] == 0


class TestActionabilityJudgeIntegration:
    """Integration tests for ActionabilityJudge."""

    def test_collect_evidence_analyzes_messages(self, sample_analysis_output: Path):
        """Test evidence collection analyzes message quality."""
        judge = ActionabilityJudge(
            working_dir=sample_analysis_output,
            output_dir=sample_analysis_output / "output" / "runs",
        )

        evidence = judge.collect_evidence()

        assert "sample_messages" in evidence
        assert "fix_suggestion_rate" in evidence
        assert "severity_usage" in evidence
        assert "location_quality" in evidence


@pytest.mark.slow
class TestFullEvaluationPipeline:
    """End-to-end tests for the full evaluation pipeline.

    These tests invoke real LLM calls and may be slow/expensive.
    """

    def test_all_judges_can_evaluate(self, sample_analysis_output: Path):
        """Test that all judges can complete evaluation successfully."""
        judges = [
            SmellAccuracyJudge(
                model="haiku",
                working_dir=sample_analysis_output,
                output_dir=sample_analysis_output / "output" / "runs",
            ),
            RuleCoverageJudge(
                model="haiku",
                working_dir=sample_analysis_output,
                output_dir=sample_analysis_output / "output" / "runs",
            ),
            FalsePositiveRateJudge(
                model="haiku",
                working_dir=sample_analysis_output,
                output_dir=sample_analysis_output / "output" / "runs",
            ),
            ActionabilityJudge(
                model="haiku",
                working_dir=sample_analysis_output,
                output_dir=sample_analysis_output / "output" / "runs",
            ),
        ]

        results = []
        for judge in judges:
            result = judge.evaluate()
            results.append(result)

            # Verify each result
            assert isinstance(result, JudgeResult)
            assert 1 <= result.score <= 5
            assert 0.0 <= result.confidence <= 1.0

        # Calculate weighted score
        total_weight = sum(j.weight for j in judges)
        weighted_score = sum(
            r.score * j.weight for r, j in zip(results, judges)
        ) / total_weight

        assert 1.0 <= weighted_score <= 5.0
