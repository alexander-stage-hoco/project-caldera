"""Unit tests for git-fame evaluate.py functions.

Covers find_output_dir, run_evaluation, determine_decision,
generate_scorecard_json, and generate_scorecard.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from evaluate import (
    calculate_dimension_score,
    classify_score,
    determine_decision,
    find_output_dir,
    generate_scorecard,
    generate_scorecard_json,
    run_evaluation,
)


# =============================================================================
# find_output_dir Tests
# =============================================================================


class TestFindOutputDir:
    """Test output directory discovery logic."""

    def test_finds_latest_run_dir_in_outputs(self, tmp_path: Path):
        """Should find the most recently modified run directory."""
        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()

        run1 = outputs_dir / "run-001"
        run1.mkdir()
        (run1 / "output.json").write_text("{}")

        run2 = outputs_dir / "run-002"
        run2.mkdir()
        (run2 / "output.json").write_text("{}")

        result = find_output_dir(tmp_path)
        # Should return one of the run dirs (the most recently modified)
        assert result.parent == outputs_dir

    def test_falls_back_to_output_dir(self, tmp_path: Path):
        """Should fall back to 'output' directory when 'outputs' doesn't exist."""
        result = find_output_dir(tmp_path)
        assert result == tmp_path / "output"

    def test_falls_back_when_outputs_empty(self, tmp_path: Path):
        """Should fall back to 'output' when outputs dir exists but is empty."""
        (tmp_path / "outputs").mkdir()
        result = find_output_dir(tmp_path)
        assert result == tmp_path / "output"

    def test_outputs_with_files_only_falls_back(self, tmp_path: Path):
        """outputs dir with files (not dirs) should fall back."""
        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()
        (outputs_dir / "readme.txt").write_text("not a directory")
        result = find_output_dir(tmp_path)
        assert result == tmp_path / "output"


# =============================================================================
# determine_decision Tests
# =============================================================================


class TestDetermineDecision:
    """Test score-to-decision mapping (different thresholds than classify_score)."""

    def test_strong_pass(self):
        assert determine_decision(4.5) == "STRONG_PASS"
        assert determine_decision(5.0) == "STRONG_PASS"
        assert determine_decision(4.0) == "STRONG_PASS"

    def test_pass(self):
        assert determine_decision(3.5) == "PASS"
        assert determine_decision(3.9) == "PASS"

    def test_weak_pass(self):
        assert determine_decision(3.0) == "WEAK_PASS"
        assert determine_decision(3.4) == "WEAK_PASS"

    def test_fail(self):
        assert determine_decision(2.9) == "FAIL"
        assert determine_decision(0.0) == "FAIL"
        assert determine_decision(2.0) == "FAIL"


# =============================================================================
# generate_scorecard_json Tests
# =============================================================================


class TestGenerateScorecardJson:
    """Test structured scorecard JSON generation."""

    @pytest.fixture
    def sample_results(self) -> dict[str, Any]:
        """Minimal evaluation results for testing scorecard generation."""
        return {
            "timestamp": "2026-02-14T10:00:00+00:00",
            "tool": "git-fame",
            "version": "3.1.1",
            "overall_score": 4.2,
            "classification": "PASS",
            "dimensions": {
                "output_quality": {
                    "weight": 0.20,
                    "score": 5.0,
                    "checks": [
                        {"check": "OQ-1", "passed": True, "message": "Schema version present"},
                        {"check": "OQ-2", "passed": True, "message": "Valid timestamps"},
                    ],
                },
                "authorship_accuracy": {
                    "weight": 0.20,
                    "score": 3.75,
                    "checks": [
                        {"check": "AA-1", "passed": True, "message": "LOC matches"},
                        {"check": "AA-2", "passed": True, "message": "Author count matches"},
                        {"check": "AA-3", "passed": True, "message": "Top author LOC OK"},
                        {"check": "AA-4", "passed": False, "message": "Ownership mismatch"},
                    ],
                },
                "reliability": {
                    "weight": 0.15,
                    "score": 5.0,
                    "checks": [
                        {"check": "RL-1", "passed": True, "message": "Deterministic output"},
                    ],
                },
            },
        }

    def test_scorecard_json_structure(self, sample_results: dict[str, Any]):
        """Scorecard JSON should have all required top-level keys."""
        scorecard = generate_scorecard_json(sample_results)

        assert scorecard["tool"] == "git-fame"
        assert scorecard["version"] == "3.1.1"
        assert "summary" in scorecard
        assert "dimensions" in scorecard
        assert "thresholds" in scorecard

    def test_scorecard_summary_counts(self, sample_results: dict[str, Any]):
        """Summary should accurately count passed and failed checks."""
        scorecard = generate_scorecard_json(sample_results)
        summary = scorecard["summary"]

        assert summary["total_checks"] == 7  # 2 + 4 + 1
        assert summary["passed"] == 6
        assert summary["failed"] == 1

    def test_scorecard_summary_score_calculation(self, sample_results: dict[str, Any]):
        """Summary score should be normalized from overall_score."""
        scorecard = generate_scorecard_json(sample_results)
        summary = scorecard["summary"]

        assert summary["score"] == round(4.2 / 5.0, 4)
        assert summary["score_percent"] == round(4.2 / 5.0 * 100, 2)
        assert summary["normalized_score"] == 4.2

    def test_scorecard_decision_uses_determine_decision(self, sample_results: dict[str, Any]):
        """Decision should use determine_decision, not classify_score."""
        scorecard = generate_scorecard_json(sample_results)
        assert scorecard["summary"]["decision"] == "STRONG_PASS"  # 4.2 >= 4.0

    def test_scorecard_dimensions_structure(self, sample_results: dict[str, Any]):
        """Each dimension should have correct structure."""
        scorecard = generate_scorecard_json(sample_results)

        assert len(scorecard["dimensions"]) == 3
        dim = scorecard["dimensions"][0]
        assert "id" in dim
        assert "name" in dim
        assert "weight" in dim
        assert "total_checks" in dim
        assert "passed" in dim
        assert "failed" in dim
        assert "score" in dim
        assert "weighted_score" in dim
        assert "checks" in dim

    def test_scorecard_dimension_ids(self, sample_results: dict[str, Any]):
        """Dimension IDs should be D1, D2, D3, etc."""
        scorecard = generate_scorecard_json(sample_results)

        ids = [d["id"] for d in scorecard["dimensions"]]
        assert ids == ["D1", "D2", "D3"]

    def test_scorecard_check_structure(self, sample_results: dict[str, Any]):
        """Each check should have check_id, name, passed, message."""
        scorecard = generate_scorecard_json(sample_results)

        for dim in scorecard["dimensions"]:
            for check in dim["checks"]:
                assert "check_id" in check
                assert "name" in check
                assert "passed" in check
                assert "message" in check

    def test_scorecard_weighted_scores(self, sample_results: dict[str, Any]):
        """Weighted scores should be score * weight."""
        scorecard = generate_scorecard_json(sample_results)

        for dim in scorecard["dimensions"]:
            expected = round(dim["score"] * dim["weight"], 2)
            assert dim["weighted_score"] == expected

    def test_scorecard_thresholds_present(self, sample_results: dict[str, Any]):
        """Thresholds section should have all four categories."""
        scorecard = generate_scorecard_json(sample_results)
        thresholds = scorecard["thresholds"]

        assert "STRONG_PASS" in thresholds
        assert "PASS" in thresholds
        assert "WEAK_PASS" in thresholds
        assert "FAIL" in thresholds


# =============================================================================
# generate_scorecard (Markdown) Tests
# =============================================================================


class TestGenerateScorecard:
    """Test markdown scorecard generation."""

    @pytest.fixture
    def sample_results(self) -> dict[str, Any]:
        """Minimal results for scorecard generation."""
        return {
            "timestamp": "2026-02-14T10:00:00+00:00",
            "tool": "git-fame",
            "version": "3.1.1",
            "overall_score": 4.0,
            "classification": "PASS",
            "dimensions": {
                "output_quality": {
                    "weight": 0.20,
                    "score": 4.5,
                    "checks": [
                        {"check": "OQ-1", "passed": True, "message": "OK"},
                        {"check": "OQ-2", "passed": False, "message": "Missing timestamp in repo-x"},
                    ],
                },
            },
        }

    def test_scorecard_file_created(self, tmp_path: Path, sample_results: dict[str, Any]):
        """Scorecard file should be created at the specified path."""
        output = tmp_path / "scorecard.md"
        generate_scorecard(sample_results, output)
        assert output.exists()

    def test_scorecard_has_header(self, tmp_path: Path, sample_results: dict[str, Any]):
        """Scorecard should start with a title."""
        output = tmp_path / "scorecard.md"
        generate_scorecard(sample_results, output)
        content = output.read_text()
        assert "git-fame Evaluation Scorecard" in content

    def test_scorecard_has_overall_score(self, tmp_path: Path, sample_results: dict[str, Any]):
        """Scorecard should include the overall score."""
        output = tmp_path / "scorecard.md"
        generate_scorecard(sample_results, output)
        content = output.read_text()
        assert "4.0/5.0" in content

    def test_scorecard_has_dimension_table(self, tmp_path: Path, sample_results: dict[str, Any]):
        """Scorecard should include dimension summary table."""
        output = tmp_path / "scorecard.md"
        generate_scorecard(sample_results, output)
        content = output.read_text()
        assert "Output Quality" in content
        assert "20%" in content

    def test_scorecard_has_check_details(self, tmp_path: Path, sample_results: dict[str, Any]):
        """Scorecard should include individual check details."""
        output = tmp_path / "scorecard.md"
        generate_scorecard(sample_results, output)
        content = output.read_text()
        assert "OQ-1" in content
        assert "PASS" in content
        assert "FAIL" in content

    def test_scorecard_truncates_long_messages(self, tmp_path: Path):
        """Messages longer than 60 chars should be truncated."""
        results = {
            "timestamp": "2026-02-14T10:00:00+00:00",
            "tool": "git-fame",
            "version": "3.1.1",
            "overall_score": 3.0,
            "classification": "MARGINAL_FAIL",
            "dimensions": {
                "test_dim": {
                    "weight": 1.0,
                    "score": 3.0,
                    "checks": [
                        {"check": "T-1", "passed": False, "message": "A" * 80},
                    ],
                },
            },
        }
        output = tmp_path / "scorecard.md"
        generate_scorecard(results, output)
        content = output.read_text()
        # The message should be truncated with ...
        assert "..." in content


# =============================================================================
# run_evaluation Tests
# =============================================================================


class TestRunEvaluation:
    """Test the run_evaluation orchestration function."""

    def test_run_evaluation_returns_all_dimensions(self, tmp_path: Path):
        """run_evaluation should return results for all 6 dimensions."""
        # Create the expected directory structure
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        gt_dir = tmp_path / "evaluation" / "ground-truth"
        gt_dir.mkdir(parents=True)
        (gt_dir / "synthetic.json").write_text("{}")

        # Mock all check classes to return simple results
        mock_checks = [{"check": "TEST", "passed": True, "message": "OK"}]

        mock_oq = MagicMock()
        mock_oq.run_all.return_value = mock_checks

        mock_aa = MagicMock()
        mock_aa.run_all.return_value = mock_checks

        mock_rel = MagicMock()
        mock_rel.run_all.return_value = mock_checks

        mock_perf = MagicMock()
        mock_perf.run_all.return_value = mock_checks

        mock_int = MagicMock()
        mock_int.run_all.return_value = mock_checks

        mock_inst = MagicMock()
        mock_inst.run_all.return_value = mock_checks

        with patch("evaluate.find_output_dir", return_value=output_dir), \
             patch("evaluate.OutputQualityChecks", return_value=mock_oq), \
             patch("evaluate.AuthorshipAccuracyChecks", return_value=mock_aa), \
             patch("evaluate.ReliabilityChecks", return_value=mock_rel), \
             patch("evaluate.PerformanceChecks", return_value=mock_perf), \
             patch("evaluate.IntegrationFitChecks", return_value=mock_int), \
             patch("evaluate.InstallationChecks", return_value=mock_inst):
            results = run_evaluation(tmp_path)

        assert "overall_score" in results
        assert "classification" in results
        assert "dimensions" in results
        assert len(results["dimensions"]) == 6
        assert "output_quality" in results["dimensions"]
        assert "authorship_accuracy" in results["dimensions"]
        assert "reliability" in results["dimensions"]
        assert "performance" in results["dimensions"]
        assert "integration_fit" in results["dimensions"]
        assert "installation" in results["dimensions"]

    def test_run_evaluation_weighted_score(self, tmp_path: Path):
        """Weighted score should reflect dimension weights."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        gt_dir = tmp_path / "evaluation" / "ground-truth"
        gt_dir.mkdir(parents=True)
        (gt_dir / "synthetic.json").write_text("{}")

        all_pass = [{"check": "T", "passed": True, "message": "OK"}]
        all_fail = [{"check": "T", "passed": False, "message": "FAIL"}]

        mock_oq = MagicMock()
        mock_oq.run_all.return_value = all_pass  # 5.0

        mock_aa = MagicMock()
        mock_aa.run_all.return_value = all_fail  # 0.0

        mock_rel = MagicMock()
        mock_rel.run_all.return_value = all_pass  # 5.0

        mock_perf = MagicMock()
        mock_perf.run_all.return_value = all_pass  # 5.0

        mock_int = MagicMock()
        mock_int.run_all.return_value = all_pass  # 5.0

        mock_inst = MagicMock()
        mock_inst.run_all.return_value = all_pass  # 5.0

        with patch("evaluate.find_output_dir", return_value=output_dir), \
             patch("evaluate.OutputQualityChecks", return_value=mock_oq), \
             patch("evaluate.AuthorshipAccuracyChecks", return_value=mock_aa), \
             patch("evaluate.ReliabilityChecks", return_value=mock_rel), \
             patch("evaluate.PerformanceChecks", return_value=mock_perf), \
             patch("evaluate.IntegrationFitChecks", return_value=mock_int), \
             patch("evaluate.InstallationChecks", return_value=mock_inst):
            results = run_evaluation(tmp_path)

        # 5*0.20 + 0*0.20 + 5*0.15 + 5*0.15 + 5*0.15 + 5*0.15 = 1.0 + 0 + 3.0 = 4.0
        assert results["overall_score"] == 4.0

    def test_run_evaluation_summary_counts(self, tmp_path: Path):
        """Summary should correctly count total passed/failed checks."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        eval_repos = tmp_path / "eval-repos"
        eval_repos.mkdir()
        gt_dir = tmp_path / "evaluation" / "ground-truth"
        gt_dir.mkdir(parents=True)
        (gt_dir / "synthetic.json").write_text("{}")

        two_checks = [
            {"check": "A", "passed": True, "message": "OK"},
            {"check": "B", "passed": False, "message": "FAIL"},
        ]
        one_check = [{"check": "C", "passed": True, "message": "OK"}]

        mock_oq = MagicMock()
        mock_oq.run_all.return_value = two_checks
        mock_aa = MagicMock()
        mock_aa.run_all.return_value = one_check
        mock_rel = MagicMock()
        mock_rel.run_all.return_value = one_check
        mock_perf = MagicMock()
        mock_perf.run_all.return_value = one_check
        mock_int = MagicMock()
        mock_int.run_all.return_value = one_check
        mock_inst = MagicMock()
        mock_inst.run_all.return_value = one_check

        with patch("evaluate.find_output_dir", return_value=output_dir), \
             patch("evaluate.OutputQualityChecks", return_value=mock_oq), \
             patch("evaluate.AuthorshipAccuracyChecks", return_value=mock_aa), \
             patch("evaluate.ReliabilityChecks", return_value=mock_rel), \
             patch("evaluate.PerformanceChecks", return_value=mock_perf), \
             patch("evaluate.IntegrationFitChecks", return_value=mock_int), \
             patch("evaluate.InstallationChecks", return_value=mock_inst):
            results = run_evaluation(tmp_path)

        assert results["summary"]["total_checks"] == 7
        assert results["summary"]["passed"] == 6
        assert results["summary"]["failed"] == 1
