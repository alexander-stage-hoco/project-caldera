"""Unit tests for scripts.evaluate — run_all_checks, create_report, determine_decision,
generate_scorecard_json, generate_scorecard_md, print_report."""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.evaluate import (
    create_report,
    determine_decision,
    generate_scorecard_json,
    generate_scorecard_md,
    print_report,
    run_all_checks,
)
from scripts.checks import CheckCategory, CheckResult, EvaluationReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(cid: str, cat: CheckCategory, passed: bool, score: float) -> CheckResult:
    return CheckResult(
        check_id=cid, name=f"Check {cid}", category=cat,
        passed=passed, score=score, message="ok" if passed else "fail",
    )


def _full_analysis(tmp_path: Path) -> dict:
    """Build analysis + ground truth dir good enough for run_all_checks."""
    return {
        "repositories": [
            {
                "repository": "healthy",
                "metrics": {
                    "commit_count": 10,
                    "commit_total_size": 5000,
                    "max_commit_size": 500,
                    "max_history_depth": 10,
                    "tree_count": 50,
                    "tree_total_size": 20000,
                    "tree_total_entries": 200,
                    "max_tree_entries": 20,
                    "blob_count": 40,
                    "blob_total_size": 100000,
                    "max_blob_size": 5000,
                    "reference_count": 3,
                    "branch_count": 1,
                    "tag_count": 0,
                    "max_path_depth": 3,
                    "max_path_length": 40,
                    "expanded_tree_count": 50,
                    "expanded_blob_count": 40,
                    "expanded_blob_size": 100000,
                },
                "health_grade": "A",
                "violations": [],
                "tool": "git-sizer",
                "raw_output": {"data": "value"},
                "duration_ms": 100,
                "lfs_candidates": [],
            },
        ],
        "summary": {},
    }


# ---------------------------------------------------------------------------
# determine_decision
# ---------------------------------------------------------------------------

class TestDetermineDecision:
    def test_strong_pass(self):
        assert determine_decision(0.85) == "STRONG_PASS"
        assert determine_decision(1.0) == "STRONG_PASS"

    def test_pass(self):
        assert determine_decision(0.75) == "PASS"

    def test_weak_pass(self):
        assert determine_decision(0.65) == "WEAK_PASS"

    def test_fail(self):
        assert determine_decision(0.5) == "FAIL"
        assert determine_decision(0.0) == "FAIL"

    def test_boundary_values(self):
        # 0.8 * 5 = 4.0 -> STRONG_PASS
        assert determine_decision(0.8) == "STRONG_PASS"
        # 0.7 * 5 = 3.5 -> PASS
        assert determine_decision(0.7) == "PASS"
        # 0.6 * 5 = 3.0 -> WEAK_PASS
        assert determine_decision(0.6) == "WEAK_PASS"
        # 0.59 * 5 = 2.95 -> FAIL
        assert determine_decision(0.59) == "FAIL"


# ---------------------------------------------------------------------------
# run_all_checks
# ---------------------------------------------------------------------------

class TestRunAllChecks:
    def test_returns_28_checks(self, tmp_path: Path):
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        analysis = _full_analysis(tmp_path)
        checks = run_all_checks(analysis, str(gt_dir))
        # 8 accuracy + 8 coverage + 8 edge cases + 4 performance = 28
        assert len(checks) == 28

    def test_categories_present(self, tmp_path: Path):
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        analysis = _full_analysis(tmp_path)
        checks = run_all_checks(analysis, str(gt_dir))
        categories = {c.category.value for c in checks}
        assert "accuracy" in categories
        assert "coverage" in categories
        assert "edge_cases" in categories
        assert "performance" in categories

    def test_skip_long_checks_passed_through(self, tmp_path: Path):
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        analysis = _full_analysis(tmp_path)
        # Should not raise
        checks = run_all_checks(analysis, str(gt_dir), skip_long_checks=True)
        assert len(checks) == 28


# ---------------------------------------------------------------------------
# create_report
# ---------------------------------------------------------------------------

class TestCreateReport:
    def test_creates_evaluation_report(self):
        checks = [_check("AC-1", CheckCategory.ACCURACY, True, 0.9)]
        report = create_report("/tmp/analysis", "/tmp/gt", {}, checks)
        assert isinstance(report, EvaluationReport)
        assert report.analysis_path == "/tmp/analysis"
        assert report.ground_truth_dir == "/tmp/gt"
        assert report.total == 1


# ---------------------------------------------------------------------------
# generate_scorecard_json
# ---------------------------------------------------------------------------

class TestGenerateScorecardJson:
    def _make_report(self) -> EvaluationReport:
        checks = [
            _check("AC-1", CheckCategory.ACCURACY, True, 0.9),
            _check("AC-2", CheckCategory.ACCURACY, False, 0.4),
            _check("CV-1", CheckCategory.COVERAGE, True, 1.0),
            _check("EC-1", CheckCategory.EDGE_CASES, True, 0.8),
            _check("PF-1", CheckCategory.PERFORMANCE, True, 0.7),
        ]
        return EvaluationReport(
            timestamp="2026-01-30T00:00:00",
            analysis_path="/tmp/a",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )

    def test_top_level_fields(self):
        sc = generate_scorecard_json(self._make_report())
        assert sc["tool"] == "git-sizer"
        assert sc["version"] == "1.0.0"
        assert "summary" in sc
        assert "dimensions" in sc
        assert "thresholds" in sc
        assert "metadata" in sc

    def test_summary_fields(self):
        sc = generate_scorecard_json(self._make_report())
        summary = sc["summary"]
        assert summary["total_checks"] == 5
        assert summary["passed"] == 4
        assert summary["failed"] == 1
        assert "score" in summary
        assert "score_percent" in summary
        assert "normalized_score" in summary
        assert "decision" in summary

    def test_dimensions_created(self):
        sc = generate_scorecard_json(self._make_report())
        dims = sc["dimensions"]
        assert len(dims) == 4  # 4 categories
        dim_names = {d["name"] for d in dims}
        assert "Accuracy" in dim_names
        assert "Coverage" in dim_names
        assert "Edge Cases" in dim_names
        assert "Performance" in dim_names

    def test_dimension_structure(self):
        sc = generate_scorecard_json(self._make_report())
        dim = sc["dimensions"][0]
        assert "id" in dim
        assert "name" in dim
        assert "weight" in dim
        assert "total_checks" in dim
        assert "passed" in dim
        assert "failed" in dim
        assert "score" in dim
        assert "checks" in dim

    def test_critical_failures_empty_by_default(self):
        sc = generate_scorecard_json(self._make_report())
        assert sc["critical_failures"] == []

    def test_is_json_serializable(self):
        sc = generate_scorecard_json(self._make_report())
        json_str = json.dumps(sc)
        parsed = json.loads(json_str)
        assert parsed["tool"] == "git-sizer"


# ---------------------------------------------------------------------------
# generate_scorecard_md
# ---------------------------------------------------------------------------

class TestGenerateScorecardMd:
    def test_contains_key_elements(self):
        scorecard = {
            "generated_at": "2026-01-30T00:00:00",
            "summary": {
                "decision": "PASS",
                "score_percent": 76.0,
                "total_checks": 28,
                "passed": 21,
                "failed": 7,
                "normalized_score": 3.8,
            },
        }
        md = generate_scorecard_md(scorecard)
        assert "# Git-Sizer Evaluation Scorecard" in md
        assert "PASS" in md
        assert "76.0%" in md
        assert "28" in md
        assert "3.8" in md

    def test_returns_string(self):
        scorecard = {"generated_at": "", "summary": {}}
        md = generate_scorecard_md(scorecard)
        assert isinstance(md, str)


# ---------------------------------------------------------------------------
# print_report
# ---------------------------------------------------------------------------

class TestPrintReport:
    def test_prints_to_stdout(self, capsys):
        checks = [
            _check("AC-1", CheckCategory.ACCURACY, True, 0.9),
            _check("AC-2", CheckCategory.ACCURACY, False, 0.4),
            _check("CV-1", CheckCategory.COVERAGE, True, 1.0),
        ]
        report = EvaluationReport(
            timestamp="2026-01-30T00:00:00",
            analysis_path="/tmp/a",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )
        print_report(report)
        captured = capsys.readouterr()
        assert "GIT-SIZER EVALUATION REPORT" in captured.out
        assert "OVERALL SUMMARY" in captured.out
        assert "CATEGORY BREAKDOWN" in captured.out
        assert "DETAILED RESULTS" in captured.out
        assert "FINAL VERDICT" in captured.out
        assert "AC-1" in captured.out
        assert "AC-2" in captured.out

    def test_shows_failure_messages(self, capsys):
        checks = [
            CheckResult(
                check_id="AC-1", name="Test", category=CheckCategory.ACCURACY,
                passed=False, score=0.0, message="Something went wrong",
            ),
        ]
        report = EvaluationReport(
            timestamp="2026-01-30T00:00:00",
            analysis_path="/tmp/a",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )
        print_report(report)
        captured = capsys.readouterr()
        assert "Something went wrong" in captured.out
