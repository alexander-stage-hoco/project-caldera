"""Tests targeting uncovered paths in evaluate.py for coverage improvement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.evaluate import (
    determine_decision,
    generate_scorecard,
    generate_scorecard_md,
    run_all_checks,
    set_color_enabled,
    print_report,
)
from scripts.checks import (
    CheckResult,
    CheckCategory,
    EvaluationReport,
)


class TestDetermineDecision:
    """Tests for all 4 decision branches."""

    def test_strong_pass(self) -> None:
        assert determine_decision(0.85) == "STRONG_PASS"

    def test_pass(self) -> None:
        assert determine_decision(0.72) == "PASS"

    def test_weak_pass(self) -> None:
        assert determine_decision(0.62) == "WEAK_PASS"

    def test_fail(self) -> None:
        assert determine_decision(0.50) == "FAIL"

    def test_boundary_strong_pass(self) -> None:
        assert determine_decision(0.80) == "STRONG_PASS"

    def test_boundary_pass(self) -> None:
        assert determine_decision(0.70) == "PASS"

    def test_boundary_weak_pass(self) -> None:
        assert determine_decision(0.60) == "WEAK_PASS"


class TestGenerateScorecard:
    """Tests for scorecard JSON generation."""

    def _make_report(self, checks: list[CheckResult]) -> EvaluationReport:
        return EvaluationReport(
            timestamp="2025-01-01T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )

    def test_scorecard_with_categories(self) -> None:
        checks = [
            CheckResult(
                check_id="SQ-AC-1", name="Issue count",
                category=CheckCategory.ACCURACY, passed=True,
                score=1.0, message="OK",
            ),
            CheckResult(
                check_id="SQ-CV-1", name="Coverage",
                category=CheckCategory.COVERAGE, passed=False,
                score=0.5, message="Missing metrics",
            ),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard(report)

        assert scorecard["tool"] == "sonarqube"
        assert scorecard["summary"]["total_checks"] == 2
        assert scorecard["summary"]["passed"] == 1
        assert scorecard["summary"]["failed"] == 1
        assert len(scorecard["dimensions"]) == 2

    def test_empty_report(self) -> None:
        report = self._make_report([])
        scorecard = generate_scorecard(report)
        assert scorecard["summary"]["total_checks"] == 0


class TestGenerateScorecardMd:
    """Tests for markdown scorecard generation."""

    def test_markdown_structure(self) -> None:
        scorecard = {
            "generated_at": "2025-01-01T00:00:00Z",
            "summary": {
                "decision": "PASS",
                "score_percent": 75.0,
                "total_checks": 10,
                "passed": 7,
                "failed": 3,
                "score": 0.75,
                "normalized_score": 3.75,
            },
            "dimensions": [
                {
                    "name": "Accuracy",
                    "total_checks": 5,
                    "passed": 4,
                    "score": 0.8,
                    "checks": [
                        {"check_id": "SQ-AC-1", "passed": True, "name": "Test", "score": 1.0, "message": "OK"},
                    ],
                },
            ],
            "thresholds": {
                "STRONG_PASS": ">= 4.0",
                "FAIL": "< 3.0",
            },
        }
        md = generate_scorecard_md(scorecard)
        assert "# SonarQube Evaluation Scorecard" in md
        assert "PASS" in md
        assert "Accuracy" in md


class TestRunAllChecks:
    """Tests for check orchestration."""

    def test_runs_all_categories(self) -> None:
        data = {
            "issues": {
                "total_issues": 5,
                "by_severity": {"MAJOR": 3, "MINOR": 2},
                "by_type": {"BUG": 1, "CODE_SMELL": 4},
                "rollups": {},
            },
            "measures": {"metrics": {}},
            "quality_gate": {"status": "OK"},
            "components": {},
            "duplications": {},
        }
        checks = run_all_checks(data, None, skip_performance=False)
        categories = {c.category.value for c in checks}
        assert "accuracy" in categories
        assert "coverage" in categories

    def test_skip_performance(self) -> None:
        data = {
            "issues": {"total_issues": 0, "by_severity": {}, "by_type": {}, "rollups": {}},
            "measures": {"metrics": {}},
            "quality_gate": {},
            "components": {},
            "duplications": {},
        }
        checks_full = run_all_checks(data, None, skip_performance=False)
        checks_quick = run_all_checks(data, None, skip_performance=True)

        full_cats = {c.category.value for c in checks_full}
        quick_cats = {c.category.value for c in checks_quick}
        assert "performance" in full_cats
        assert "performance" not in quick_cats


class TestPrintReport:
    """Test print_report covers console output paths."""

    def test_print_report_passing(self, capsys) -> None:
        set_color_enabled(False)
        checks = [
            CheckResult(
                check_id="SQ-AC-1", name="Issue count",
                category=CheckCategory.ACCURACY, passed=True,
                score=1.0, message="OK",
            ),
        ]
        report = EvaluationReport(
            timestamp="2025-01-01T00:00:00Z",
            analysis_path="/tmp/test.json",
            ground_truth_dir="",
            checks=checks,
        )
        print_report(report)
        captured = capsys.readouterr()
        assert "EVALUATION REPORT" in captured.out
        assert "STRONG_PASS" in captured.out

    def test_print_report_with_failures(self, capsys) -> None:
        set_color_enabled(False)
        checks = [
            CheckResult(
                check_id="SQ-AC-1", name="Issue count",
                category=CheckCategory.ACCURACY, passed=False,
                score=0.0, message="Expected 5, got 0",
            ),
        ]
        report = EvaluationReport(
            timestamp="2025-01-01T00:00:00Z",
            analysis_path="/tmp/test.json",
            ground_truth_dir="",
            checks=checks,
        )
        print_report(report)
        captured = capsys.readouterr()
        assert "FAILED CHECKS" in captured.out
        assert "FAIL" in captured.out
