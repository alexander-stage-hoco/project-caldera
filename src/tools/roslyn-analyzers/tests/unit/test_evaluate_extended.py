"""
Extended tests for evaluate.py - covering uncovered functions.

Tests cover:
- generate_scorecard_md: full markdown generation with all sections
- print_simple_report: text output rendering
- run_evaluation: end-to-end evaluation with file I/O
- compute_category_scores edge cases
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from evaluate import (
    generate_scorecard_md,
    print_simple_report,
    run_evaluation,
    generate_scorecard_json,
    render_report,
)
from checks import CheckResult, EvaluationReport


class TestGenerateScorecardMdFull:
    """Test markdown scorecard generation with all sections."""

    def _make_scorecard(self):
        return {
            "generated_at": "2026-01-22T10:00:00Z",
            "summary": {
                "decision": "PASS",
                "score_percent": 78.0,
                "total_checks": 20,
                "passed": 16,
                "failed": 4,
                "score": 0.78,
                "normalized_score": 3.90,
            },
            "dimensions": [
                {
                    "name": "Accuracy",
                    "total_checks": 10,
                    "passed": 8,
                    "score": 4.0,
                    "checks": [
                        {"check_id": "AC-1", "name": "SQL Detection", "passed": True, "message": "All detected"},
                        {"check_id": "AC-2", "name": "XSS Detection", "passed": False, "message": "Missing patterns"},
                    ],
                },
                {
                    "name": "Coverage",
                    "total_checks": 8,
                    "passed": 6,
                    "score": 3.75,
                    "checks": [
                        {"check_id": "CV-1", "name": "Security Rules", "passed": True, "message": "Good coverage"},
                    ],
                },
            ],
            "critical_failures": [
                {"check_id": "CRITICAL-1", "name": "Critical Check", "message": "Failed critically"},
            ],
            "thresholds": {
                "STRONG_PASS": ">= 4.0 (80%+)",
                "PASS": ">= 3.5 (70%+)",
                "WEAK_PASS": ">= 3.0 (60%+)",
                "FAIL": "< 3.0 (below 60%)",
            },
            "metadata": {
                "analysis_file": "/path/to/analysis.json",
            },
        }

    def test_includes_title(self):
        md = generate_scorecard_md(self._make_scorecard())
        assert "# Roslyn Analyzers Evaluation Scorecard" in md

    def test_includes_summary_table(self):
        md = generate_scorecard_md(self._make_scorecard())
        assert "Total Checks" in md
        assert "20" in md
        assert "Passed" in md
        assert "16" in md
        assert "Failed" in md
        assert "3.90" in md

    def test_includes_dimensions_table(self):
        md = generate_scorecard_md(self._make_scorecard())
        assert "## Dimensions" in md
        assert "Accuracy" in md
        assert "Coverage" in md

    def test_includes_critical_failures(self):
        md = generate_scorecard_md(self._make_scorecard())
        assert "## Critical Failures" in md
        assert "CRITICAL-1" in md
        assert "Failed critically" in md

    def test_includes_detailed_results(self):
        md = generate_scorecard_md(self._make_scorecard())
        assert "## Detailed Results" in md
        assert "### Accuracy" in md
        assert "AC-1" in md
        assert "PASS" in md
        assert "AC-2" in md
        assert "FAIL" in md

    def test_includes_thresholds(self):
        md = generate_scorecard_md(self._make_scorecard())
        assert "## Decision Thresholds" in md
        assert "STRONG_PASS" in md
        assert "WEAK_PASS" in md

    def test_includes_metadata_footer(self):
        md = generate_scorecard_md(self._make_scorecard())
        assert "/path/to/analysis.json" in md

    def test_no_dimensions(self):
        scorecard = {
            "generated_at": "",
            "summary": {"decision": "FAIL", "score_percent": 0, "total_checks": 0,
                         "passed": 0, "failed": 0, "score": 0, "normalized_score": 0},
            "dimensions": [],
            "critical_failures": [],
            "thresholds": {},
            "metadata": {},
        }
        md = generate_scorecard_md(scorecard)
        assert "## Dimensions" not in md
        assert "## Detailed Results" not in md

    def test_no_critical_failures(self):
        scorecard = self._make_scorecard()
        scorecard["critical_failures"] = []
        md = generate_scorecard_md(scorecard)
        assert "## Critical Failures" not in md

    def test_long_message_truncated(self):
        """Check messages longer than 50 chars are truncated in detailed results."""
        scorecard = self._make_scorecard()
        long_msg = "A" * 80
        scorecard["dimensions"][0]["checks"][0]["message"] = long_msg
        md = generate_scorecard_md(scorecard)
        assert "..." in md


class TestPrintSimpleReport:
    """Test simple text report rendering."""

    def test_prints_report(self, capsys):
        report = EvaluationReport(
            evaluation_id="test-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={
                "total_checks": 10,
                "passed": 8,
                "failed": 2,
                "pass_rate_pct": 80.0,
                "overall_score": 0.78,
            },
            category_scores={
                "accuracy": {"checks_passed": 4, "checks_total": 5, "score": 0.80},
            },
            checks=[
                {"check_id": "AC-1", "name": "Test Check", "passed": True,
                 "score": 0.9, "message": "All good"},
            ],
            decision="PASS",
            decision_reason="Score meets threshold",
        )

        print_simple_report(report)

        captured = capsys.readouterr()
        assert "ROSLYN ANALYZERS" in captured.out
        assert "Total Checks: 10" in captured.out
        assert "Passed: 8" in captured.out
        assert "Failed: 2" in captured.out
        assert "Pass Rate: 80.0%" in captured.out
        assert "PASS" in captured.out
        assert "accuracy: 4/5" in captured.out
        assert "AC-1" in captured.out


class TestRenderReport:
    """Test render_report with no rich console."""

    def test_render_report_without_rich(self, capsys):
        report = EvaluationReport(
            evaluation_id="test-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={
                "total_checks": 5,
                "passed": 4,
                "failed": 1,
                "pass_rate_pct": 80.0,
                "overall_score": 0.80,
            },
            category_scores={
                "accuracy": {"checks_passed": 2, "checks_total": 3, "score": 0.67},
            },
            checks=[
                {"check_id": "AC-1", "name": "Test", "passed": True, "score": 1.0, "message": "OK"},
            ],
            decision="PASS",
            decision_reason="Score OK",
        )

        # Calling with console=None falls through to print_simple_report
        render_report(report, console=None)

        captured = capsys.readouterr()
        assert "ROSLYN ANALYZERS" in captured.out


class TestRunEvaluation:
    """Test run_evaluation end-to-end with real file I/O."""

    def _write_analysis(self, tmp_path):
        analysis_data = {
            "schema_version": "1.0.0",
            "generated_at": "2026-01-22T10:00:00Z",
            "repo_name": "test-repo",
            "repo_path": "/tmp/test-repo",
            "results": {
                "tool": "roslyn-analyzers",
                "tool_version": "1.0.0",
                "analysis_duration_ms": 5000,
                "summary": {
                    "total_files_analyzed": 2,
                    "total_violations": 5,
                    "files_with_violations": 2,
                    "violations_by_category": {
                        "security": 3, "design": 1, "resource": 1,
                    },
                    "violations_by_severity": {"high": 3, "medium": 2},
                    "violations_by_rule": {"CA3001": 3, "CA1040": 1, "CA2000": 1},
                },
                "files": [
                    {
                        "path": "src/service.cs",
                        "relative_path": "src/service.cs",
                        "lines_of_code": 100,
                        "violation_count": 3,
                        "violations": [
                            {"rule_id": "CA3001", "line_start": 10},
                            {"rule_id": "CA3001", "line_start": 20},
                            {"rule_id": "CA3001", "line_start": 30},
                        ],
                    },
                    {
                        "path": "src/model.cs",
                        "relative_path": "src/model.cs",
                        "lines_of_code": 50,
                        "violation_count": 2,
                        "violations": [
                            {"rule_id": "CA1040", "line_start": 5},
                            {"rule_id": "CA2000", "line_start": 15},
                        ],
                    },
                ],
                "statistics": {},
                "directory_rollup": [],
            },
        }
        analysis_path = tmp_path / "analysis.json"
        analysis_path.write_text(json.dumps(analysis_data))
        return str(analysis_path)

    def _write_ground_truth(self, tmp_path):
        gt_data = {
            "schema_version": "1.0",
            "scenario": "test",
            "summary": {
                "total_expected_violations": 5,
            },
            "files": {},
        }
        gt_path = tmp_path / "csharp.json"
        gt_path.write_text(json.dumps(gt_data))
        return str(tmp_path)  # Return directory, load_ground_truth looks for csharp.json

    def test_run_evaluation_produces_report(self, tmp_path):
        analysis_path = self._write_analysis(tmp_path)
        gt_path = self._write_ground_truth(tmp_path)
        output_path = str(tmp_path / "output" / "report.json")

        report = run_evaluation(
            analysis_path=analysis_path,
            ground_truth_path=gt_path,
            output_path=output_path,
            json_only=True,
            quick=True,  # Skip performance checks for speed
        )

        assert report.decision in ["STRONG_PASS", "PASS", "WEAK_PASS", "FAIL"]
        assert report.summary["total_checks"] > 0

        # Check output file was written
        assert Path(output_path).exists()
        with open(output_path) as f:
            data = json.load(f)
        assert "evaluation_id" in data
        assert "decision" in data

    def test_run_evaluation_writes_scorecard_files(self, tmp_path):
        analysis_path = self._write_analysis(tmp_path)
        gt_path = self._write_ground_truth(tmp_path)
        output_path = str(tmp_path / "output" / "report.json")

        run_evaluation(
            analysis_path=analysis_path,
            ground_truth_path=gt_path,
            output_path=output_path,
            json_only=True,
            quick=True,
        )

        output_dir = tmp_path / "output"
        assert (output_dir / "scorecard.json").exists()
        assert (output_dir / "scorecard.md").exists()
        assert (output_dir / "evaluation_report.json").exists()

        # Verify evaluation_report.json structure
        with open(output_dir / "evaluation_report.json") as f:
            eval_report = json.load(f)
        assert eval_report["tool"] == "roslyn-analyzers"
        assert "decision" in eval_report
        assert "checks" in eval_report

    def test_run_evaluation_quick_skips_performance(self, tmp_path):
        analysis_path = self._write_analysis(tmp_path)
        gt_path = self._write_ground_truth(tmp_path)

        report = run_evaluation(
            analysis_path=analysis_path,
            ground_truth_path=gt_path,
            json_only=True,
            quick=True,
        )

        check_ids = [c["check_id"] for c in report.checks]
        assert not any(c.startswith("PF-") for c in check_ids)

    def test_run_evaluation_full_includes_performance(self, tmp_path):
        analysis_path = self._write_analysis(tmp_path)
        gt_path = self._write_ground_truth(tmp_path)

        report = run_evaluation(
            analysis_path=analysis_path,
            ground_truth_path=gt_path,
            json_only=True,
            quick=False,
        )

        check_ids = [c["check_id"] for c in report.checks]
        assert any(c.startswith("PF-") for c in check_ids)

    def test_run_evaluation_no_output_path(self, tmp_path):
        """When no output_path, scorecard written to default location."""
        analysis_path = self._write_analysis(tmp_path)
        gt_path = self._write_ground_truth(tmp_path)

        report = run_evaluation(
            analysis_path=analysis_path,
            ground_truth_path=gt_path,
            output_path=None,
            json_only=True,
            quick=True,
        )

        assert report.decision is not None


class TestRunEvaluationErrorCases:
    """Test error handling in run_evaluation."""

    def test_missing_analysis_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            run_evaluation(
                analysis_path=str(tmp_path / "nonexistent.json"),
                ground_truth_path=str(tmp_path),
                json_only=True,
                quick=True,
            )

    def test_missing_ground_truth(self, tmp_path):
        # Create analysis file but no ground truth
        analysis_path = tmp_path / "analysis.json"
        analysis_path.write_text(json.dumps({
            "schema_version": "1.0.0",
            "results": {
                "tool": "roslyn-analyzers",
                "summary": {},
                "files": [],
                "statistics": {},
                "directory_rollup": [],
            },
        }))

        with pytest.raises(FileNotFoundError):
            run_evaluation(
                analysis_path=str(analysis_path),
                ground_truth_path=str(tmp_path / "nonexistent_dir"),
                json_only=True,
                quick=True,
            )
