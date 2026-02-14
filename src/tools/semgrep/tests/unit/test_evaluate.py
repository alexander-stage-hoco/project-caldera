"""Tests for scripts/evaluate.py - programmatic evaluation runner.

Covers:
- determine_decision threshold logic
- generate_scorecard_json structure
- generate_scorecard_md rendering
- run_evaluation orchestration
- Colors / c / set_color_enabled
- EvaluationReport properties
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from evaluate import (
    determine_decision,
    generate_scorecard_json,
    generate_scorecard_md,
    run_evaluation,
    Colors,
    c,
    set_color_enabled,
)
from checks import CheckResult, CheckCategory, EvaluationReport


# ===========================================================================
# determine_decision
# ===========================================================================

class TestDetermineDecision:
    def test_strong_pass(self):
        # score 0.85 => 4.25 => STRONG_PASS
        assert determine_decision(0.85) == "STRONG_PASS"

    def test_pass(self):
        # score 0.72 => 3.6 => PASS
        assert determine_decision(0.72) == "PASS"

    def test_weak_pass(self):
        # score 0.62 => 3.1 => WEAK_PASS
        assert determine_decision(0.62) == "WEAK_PASS"

    def test_fail(self):
        # score 0.50 => 2.5 => FAIL
        assert determine_decision(0.50) == "FAIL"

    def test_boundary_strong_pass(self):
        assert determine_decision(0.80) == "STRONG_PASS"

    def test_boundary_pass(self):
        assert determine_decision(0.70) == "PASS"

    def test_boundary_weak_pass(self):
        assert determine_decision(0.60) == "WEAK_PASS"

    def test_zero_score(self):
        assert determine_decision(0.0) == "FAIL"

    def test_perfect_score(self):
        assert determine_decision(1.0) == "STRONG_PASS"


# ===========================================================================
# EvaluationReport properties
# ===========================================================================

class TestEvaluationReport:
    def _make_report(self, checks: list[CheckResult] | None = None) -> EvaluationReport:
        if checks is None:
            checks = [
                CheckResult("AC-1", "Check 1", CheckCategory.ACCURACY, True, 0.9, "ok"),
                CheckResult("AC-2", "Check 2", CheckCategory.ACCURACY, False, 0.3, "bad"),
                CheckResult("CV-1", "Check 3", CheckCategory.COVERAGE, True, 0.8, "ok"),
            ]
        return EvaluationReport(
            timestamp="2026-01-01T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )

    def test_passed_count(self):
        r = self._make_report()
        assert r.passed == 2

    def test_failed_count(self):
        r = self._make_report()
        assert r.failed == 1

    def test_total_count(self):
        r = self._make_report()
        assert r.total == 3

    def test_score(self):
        r = self._make_report()
        expected = (0.9 + 0.3 + 0.8) / 3
        assert abs(r.score - expected) < 0.001

    def test_score_empty(self):
        r = self._make_report(checks=[])
        assert r.score == 0.0

    def test_score_by_category(self):
        r = self._make_report()
        cats = r.score_by_category
        assert "accuracy" in cats
        assert "coverage" in cats
        # accuracy = (0.9 + 0.3) / 2 = 0.6
        assert abs(cats["accuracy"] - 0.6) < 0.001

    def test_passed_by_category(self):
        r = self._make_report()
        cats = r.passed_by_category
        assert cats["accuracy"] == (1, 2)
        assert cats["coverage"] == (1, 1)

    def test_to_dict(self):
        r = self._make_report()
        d = r.to_dict()
        assert "summary" in d
        assert d["summary"]["passed"] == 2
        assert "checks" in d
        assert len(d["checks"]) == 3


# ===========================================================================
# generate_scorecard_json
# ===========================================================================

class TestGenerateScorecardJson:
    def test_basic_structure(self):
        report = EvaluationReport(
            timestamp="2026-01-01T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/gt",
            checks=[
                CheckResult("AC-1", "Accuracy check", CheckCategory.ACCURACY, True, 0.9, "ok"),
                CheckResult("PF-1", "Perf check", CheckCategory.PERFORMANCE, True, 0.8, "fast"),
            ],
        )
        sc = generate_scorecard_json(report)
        assert sc["tool"] == "semgrep"
        assert "summary" in sc
        assert sc["summary"]["total_checks"] == 2
        assert sc["summary"]["passed"] == 2
        assert "dimensions" in sc
        assert len(sc["dimensions"]) == 2
        assert "thresholds" in sc

    def test_decision_field(self):
        report = EvaluationReport(
            timestamp="2026-01-01T00:00:00Z",
            analysis_path="/tmp/a.json",
            ground_truth_dir="/tmp/gt",
            checks=[
                CheckResult("AC-1", "c", CheckCategory.ACCURACY, True, 0.9, "ok"),
            ],
        )
        sc = generate_scorecard_json(report)
        assert sc["summary"]["decision"] in ("STRONG_PASS", "PASS", "WEAK_PASS", "FAIL")

    def test_normalized_score_0_to_5(self):
        report = EvaluationReport(
            timestamp="2026-01-01T00:00:00Z",
            analysis_path="/tmp/a.json",
            ground_truth_dir="/tmp/gt",
            checks=[CheckResult("AC-1", "c", CheckCategory.ACCURACY, True, 1.0, "ok")],
        )
        sc = generate_scorecard_json(report)
        assert 0 <= sc["summary"]["normalized_score"] <= 5.0

    def test_metadata_present(self):
        report = EvaluationReport(
            timestamp="2026-01-01T00:00:00Z",
            analysis_path="/path/to/analysis.json",
            ground_truth_dir="/path/to/gt",
            checks=[],
        )
        sc = generate_scorecard_json(report)
        assert sc["metadata"]["analysis_path"] == "/path/to/analysis.json"
        assert sc["metadata"]["ground_truth_dir"] == "/path/to/gt"

    def test_empty_checks(self):
        report = EvaluationReport(
            timestamp="2026-01-01T00:00:00Z",
            analysis_path="/tmp/a.json",
            ground_truth_dir="/tmp/gt",
            checks=[],
        )
        sc = generate_scorecard_json(report)
        assert sc["summary"]["total_checks"] == 0
        assert sc["summary"]["passed"] == 0


# ===========================================================================
# generate_scorecard_md
# ===========================================================================

class TestGenerateScorecardMd:
    def test_has_title(self):
        sc = {
            "generated_at": "2026-01-01",
            "summary": {"decision": "PASS", "score_percent": 80.0, "total_checks": 2, "passed": 2, "failed": 0, "score": 0.8, "normalized_score": 4.0},
            "dimensions": [],
            "critical_failures": [],
            "thresholds": {"PASS": ">= 3.5"},
            "metadata": {},
        }
        md = generate_scorecard_md(sc)
        assert "# Semgrep Evaluation Scorecard" in md

    def test_has_summary_table(self):
        sc = {
            "generated_at": "2026-01-01",
            "summary": {"decision": "PASS", "score_percent": 80.0, "total_checks": 5, "passed": 4, "failed": 1, "score": 0.8, "normalized_score": 4.0},
            "dimensions": [],
            "critical_failures": [],
            "thresholds": {},
            "metadata": {},
        }
        md = generate_scorecard_md(sc)
        assert "| Total Checks | 5 |" in md
        assert "| Passed | 4 |" in md

    def test_dimensions_table(self):
        sc = {
            "generated_at": "2026-01-01",
            "summary": {"decision": "PASS", "score_percent": 80.0, "total_checks": 1, "passed": 1, "failed": 0, "score": 0.8, "normalized_score": 4.0},
            "dimensions": [
                {"name": "Accuracy", "total_checks": 1, "passed": 1, "score": 4.5, "checks": [
                    {"check_id": "AC-1", "passed": True, "message": "good"},
                ]},
            ],
            "critical_failures": [],
            "thresholds": {},
            "metadata": {},
        }
        md = generate_scorecard_md(sc)
        assert "## Dimensions" in md
        assert "Accuracy" in md

    def test_critical_failures(self):
        sc = {
            "generated_at": "2026-01-01",
            "summary": {"decision": "FAIL", "score_percent": 40.0, "total_checks": 1, "passed": 0, "failed": 1, "score": 0.4, "normalized_score": 2.0},
            "dimensions": [],
            "critical_failures": [
                {"check_id": "AC-critical", "name": "Critical Check", "message": "Failed badly"},
            ],
            "thresholds": {},
            "metadata": {},
        }
        md = generate_scorecard_md(sc)
        assert "## Critical Failures" in md
        assert "Failed badly" in md

    def test_metadata_in_footer(self):
        sc = {
            "generated_at": "2026-01-01",
            "summary": {"decision": "PASS", "score_percent": 80.0, "total_checks": 0, "passed": 0, "failed": 0, "score": 0, "normalized_score": 0},
            "dimensions": [],
            "critical_failures": [],
            "thresholds": {},
            "metadata": {"analysis_path": "/my/analysis.json", "ground_truth_dir": "/my/gt"},
        }
        md = generate_scorecard_md(sc)
        assert "/my/analysis.json" in md
        assert "/my/gt" in md

    def test_long_message_truncated(self):
        sc = {
            "generated_at": "2026-01-01",
            "summary": {"decision": "PASS", "score_percent": 80.0, "total_checks": 1, "passed": 1, "failed": 0, "score": 0.8, "normalized_score": 4.0},
            "dimensions": [
                {"name": "Test", "total_checks": 1, "passed": 1, "score": 4.0, "checks": [
                    {"check_id": "T-1", "passed": True, "message": "A" * 100},
                ]},
            ],
            "critical_failures": [],
            "thresholds": {},
            "metadata": {},
        }
        md = generate_scorecard_md(sc)
        # Long messages get truncated at 50 chars + "..."
        assert "..." in md


# ===========================================================================
# run_evaluation
# ===========================================================================

class TestRunEvaluation:
    def test_run_evaluation_produces_report(self, tmp_path: Path):
        """Test full evaluation pipeline with minimal analysis data."""
        analysis_data = {
            "files": [
                {
                    "path": "src/main.py",
                    "language": "python",
                    "lines": 100,
                    "smell_count": 2,
                    "smell_density": 2.0,
                    "by_category": {"error_handling": 2},
                    "by_severity": {"WARNING": 2},
                    "smells": [
                        {"rule_id": "empty-catch", "dd_smell_id": "D1_EMPTY_CATCH", "dd_category": "error_handling", "severity": "WARNING", "line_start": 10, "line_end": 12, "message": "Empty catch"},
                        {"rule_id": "empty-catch-2", "dd_smell_id": "D1_EMPTY_CATCH", "dd_category": "error_handling", "severity": "WARNING", "line_start": 20, "line_end": 22, "message": "Empty catch"},
                    ],
                },
            ],
            "summary": {"total_smells": 2, "total_files": 1, "total_lines": 100},
            "metadata": {"analysis_duration_ms": 3000},
            "_root": {
                "schema_version": "1.0.0",
                "metadata": {"tool_name": "semgrep", "schema_version": "1.0.0"},
            },
        }
        analysis_path = tmp_path / "analysis.json"
        analysis_path.write_text(json.dumps(analysis_data))

        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        (gt_dir / "python.json").write_text(json.dumps({
            "language": "python",
            "files": {
                "main.py": {"expected_smells": [{"smell_id": "D1_EMPTY_CATCH", "count": 2}]},
            },
        }))

        report = run_evaluation(str(analysis_path), str(gt_dir))
        assert report.total > 0
        assert 0.0 <= report.score <= 1.0
        assert isinstance(report.timestamp, str)


# ===========================================================================
# Color helpers (in evaluate.py)
# ===========================================================================

class TestEvaluateColors:
    def test_c_with_color(self):
        set_color_enabled(True)
        result = c("test", Colors.RED)
        assert "test" in result
        assert "\033[" in result

    def test_c_without_color(self):
        set_color_enabled(False)
        result = c("test", Colors.RED)
        assert result == "test"
        set_color_enabled(True)
