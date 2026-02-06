"""Unit tests for evaluate.py module.

This module tests the evaluate.py functions by importing from the scripts package.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import from scripts package (conftest.py sets up the path)
from scripts.evaluate import (
    c,
    set_color_enabled,
    determine_decision,
    generate_scorecard_json,
    generate_scorecard_md,
    run_evaluation,
    print_report,
    main,
    Colors,
)
from checks import CheckResult, CheckCategory, EvaluationReport


class TestColorHelpers:
    """Tests for color helper functions."""

    def test_c_with_color_enabled(self) -> None:
        """c() should apply color codes when enabled."""
        set_color_enabled(True)
        result = c("test", Colors.RED)
        assert Colors.RED in result
        assert "test" in result
        assert Colors.RESET in result

    def test_c_without_color(self) -> None:
        """c() should return plain text when colors disabled."""
        set_color_enabled(False)
        result = c("test", Colors.RED)
        assert result == "test"
        assert Colors.RED not in result

    def test_c_multiple_codes(self) -> None:
        """c() should combine multiple color codes."""
        set_color_enabled(True)
        result = c("bold red", Colors.RED, Colors.BOLD)
        assert Colors.RED in result
        assert Colors.BOLD in result
        assert "bold red" in result

    def test_c_converts_to_string(self) -> None:
        """c() should convert non-string values to string."""
        set_color_enabled(False)
        result = c(123, Colors.RED)
        assert result == "123"

    def test_set_color_enabled_toggle(self) -> None:
        """set_color_enabled should toggle color state."""
        set_color_enabled(True)
        assert c("test", Colors.RED) != "test"

        set_color_enabled(False)
        assert c("test", Colors.RED) == "test"


class TestDetermineDecision:
    """Tests for determine_decision function."""

    def test_strong_pass_threshold(self) -> None:
        """Score >= 0.8 (4.0 normalized) should be STRONG_PASS."""
        assert determine_decision(0.8) == "STRONG_PASS"
        assert determine_decision(0.85) == "STRONG_PASS"
        assert determine_decision(1.0) == "STRONG_PASS"

    def test_pass_threshold(self) -> None:
        """Score >= 0.7 (3.5 normalized) should be PASS."""
        assert determine_decision(0.7) == "PASS"
        assert determine_decision(0.75) == "PASS"
        assert determine_decision(0.79) == "PASS"

    def test_weak_pass_threshold(self) -> None:
        """Score >= 0.6 (3.0 normalized) should be WEAK_PASS."""
        assert determine_decision(0.6) == "WEAK_PASS"
        assert determine_decision(0.65) == "WEAK_PASS"
        assert determine_decision(0.69) == "WEAK_PASS"

    def test_fail_threshold(self) -> None:
        """Score < 0.6 (3.0 normalized) should be FAIL."""
        assert determine_decision(0.59) == "FAIL"
        assert determine_decision(0.5) == "FAIL"
        assert determine_decision(0.0) == "FAIL"

    def test_boundary_values(self) -> None:
        """Test exact boundary values."""
        # 0.8 * 5.0 = 4.0, should be STRONG_PASS
        assert determine_decision(0.8) == "STRONG_PASS"
        # 0.7 * 5.0 = 3.5, should be PASS
        assert determine_decision(0.7) == "PASS"
        # 0.6 * 5.0 = 3.0, should be WEAK_PASS
        assert determine_decision(0.6) == "WEAK_PASS"


class TestGenerateScorecardJson:
    """Tests for generate_scorecard_json function."""

    def test_scorecard_structure(self, mock_evaluation_report: EvaluationReport) -> None:
        """Scorecard should have correct top-level structure."""
        scorecard = generate_scorecard_json(mock_evaluation_report)

        assert scorecard["tool"] == "devskim"
        assert scorecard["version"] == "1.0.0"
        assert "generated_at" in scorecard
        assert "description" in scorecard
        assert "summary" in scorecard
        assert "dimensions" in scorecard
        assert "thresholds" in scorecard
        assert "metadata" in scorecard

    def test_summary_section(self, mock_evaluation_report: EvaluationReport) -> None:
        """Summary should contain correct metrics."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        summary = scorecard["summary"]

        assert summary["total_checks"] == 4
        assert summary["passed"] == 3
        assert summary["failed"] == 1
        assert "score" in summary
        assert "score_percent" in summary
        assert "normalized_score" in summary
        assert "decision" in summary

    def test_dimensions_structure(self, mock_evaluation_report: EvaluationReport) -> None:
        """Dimensions should be correctly structured."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        dimensions = scorecard["dimensions"]

        assert len(dimensions) > 0
        for dim in dimensions:
            assert "id" in dim
            assert "name" in dim
            assert "weight" in dim
            assert "total_checks" in dim
            assert "passed" in dim
            assert "failed" in dim
            assert "score" in dim
            assert "checks" in dim

    def test_critical_failures_empty(self, mock_evaluation_report: EvaluationReport) -> None:
        """Critical failures should be empty when no critical checks fail."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        assert scorecard["critical_failures"] == []

    def test_critical_failures_populated(self) -> None:
        """Critical failures should list failed critical checks."""
        checks = [
            CheckResult(
                check_id="critical-1",
                name="Critical security check",
                category=CheckCategory.ACCURACY,
                passed=False,
                score=0.0,
                message="Critical issue found",
            ),
        ]
        report = EvaluationReport(
            timestamp="2026-01-22T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/ground-truth",
            checks=checks,
        )

        scorecard = generate_scorecard_json(report)
        assert len(scorecard["critical_failures"]) == 1
        assert scorecard["critical_failures"][0]["check_id"] == "critical-1"

    def test_metadata_section(self, mock_evaluation_report: EvaluationReport) -> None:
        """Metadata should contain analysis and ground truth paths."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        metadata = scorecard["metadata"]

        assert metadata["analysis_path"] == "/tmp/analysis.json"
        assert metadata["ground_truth_dir"] == "/tmp/ground-truth"

    def test_empty_report(self) -> None:
        """Empty report should produce valid scorecard."""
        report = EvaluationReport(
            timestamp="2026-01-22T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/ground-truth",
            checks=[],
        )

        scorecard = generate_scorecard_json(report)
        assert scorecard["summary"]["total_checks"] == 0
        assert scorecard["dimensions"] == []


class TestGenerateScorecardMd:
    """Tests for generate_scorecard_md function."""

    def test_markdown_header(self, mock_evaluation_report: EvaluationReport) -> None:
        """Markdown should have correct header."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        md = generate_scorecard_md(scorecard)

        assert "# DevSkim Evaluation Scorecard" in md
        assert "**Generated:**" in md
        assert "**Decision:**" in md
        assert "**Score:**" in md

    def test_summary_table(self, mock_evaluation_report: EvaluationReport) -> None:
        """Markdown should have summary table."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        md = generate_scorecard_md(scorecard)

        assert "## Summary" in md
        assert "| Metric | Value |" in md
        assert "| Total Checks |" in md
        assert "| Passed |" in md
        assert "| Failed |" in md

    def test_dimensions_table(self, mock_evaluation_report: EvaluationReport) -> None:
        """Markdown should have dimensions table."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        md = generate_scorecard_md(scorecard)

        assert "## Dimensions" in md
        assert "| Dimension | Checks | Passed | Score |" in md

    def test_detailed_results_section(self, mock_evaluation_report: EvaluationReport) -> None:
        """Markdown should have detailed results."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        md = generate_scorecard_md(scorecard)

        assert "## Detailed Results" in md
        assert "| Check | Status | Message |" in md

    def test_thresholds_section(self, mock_evaluation_report: EvaluationReport) -> None:
        """Markdown should have threshold definitions."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        md = generate_scorecard_md(scorecard)

        assert "## Decision Thresholds" in md
        assert "STRONG_PASS" in md
        assert "PASS" in md
        assert "WEAK_PASS" in md
        assert "FAIL" in md

    def test_message_truncation(self) -> None:
        """Long messages should be truncated in markdown."""
        checks = [
            CheckResult(
                check_id="AC-1",
                name="Test check",
                category=CheckCategory.ACCURACY,
                passed=True,
                score=1.0,
                message="A" * 100,  # Very long message
            ),
        ]
        report = EvaluationReport(
            timestamp="2026-01-22T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/ground-truth",
            checks=checks,
        )

        scorecard = generate_scorecard_json(report)
        md = generate_scorecard_md(scorecard)

        # Long messages should be truncated with ...
        assert "..." in md

    def test_footer_metadata(self, mock_evaluation_report: EvaluationReport) -> None:
        """Markdown should have footer with metadata."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        md = generate_scorecard_md(scorecard)

        assert "*Analysis:" in md
        assert "*Ground Truth:" in md


class TestRunEvaluation:
    """Tests for run_evaluation function."""

    @patch("scripts.evaluate.run_performance_checks", return_value=[])
    @patch("scripts.evaluate.run_integration_fit_checks", return_value=[])
    @patch("scripts.evaluate.run_output_quality_checks", return_value=[])
    @patch("scripts.evaluate.run_edge_case_checks", return_value=[])
    @patch("scripts.evaluate.run_coverage_checks", return_value=[])
    @patch("scripts.evaluate.run_accuracy_checks", return_value=[])
    @patch("scripts.evaluate.load_analysis", return_value={"files": [], "summary": {}})
    def test_run_all_categories(
        self,
        mock_load,
        mock_accuracy,
        mock_coverage,
        mock_edge,
        mock_output,
        mock_integration,
        mock_perf,
    ) -> None:
        """run_evaluation should call all check categories."""
        report = run_evaluation(
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/ground-truth",
        )

        mock_load.assert_called_once_with("/tmp/analysis.json")
        mock_accuracy.assert_called_once()
        mock_coverage.assert_called_once()
        mock_edge.assert_called_once()
        mock_output.assert_called_once()
        mock_integration.assert_called_once()
        mock_perf.assert_called_once()

    @patch("scripts.evaluate.run_performance_checks", return_value=[])
    @patch("scripts.evaluate.run_integration_fit_checks", return_value=[])
    @patch("scripts.evaluate.run_output_quality_checks", return_value=[])
    @patch("scripts.evaluate.run_edge_case_checks", return_value=[])
    @patch("scripts.evaluate.run_coverage_checks", return_value=[])
    @patch("scripts.evaluate.run_accuracy_checks", return_value=[])
    @patch("scripts.evaluate.load_analysis", return_value={"files": [], "summary": {}})
    def test_skip_performance_checks(
        self,
        mock_load,
        mock_accuracy,
        mock_coverage,
        mock_edge,
        mock_output,
        mock_integration,
        mock_perf,
    ) -> None:
        """skip_performance=True should skip performance checks."""
        report = run_evaluation(
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/ground-truth",
            skip_performance=True,
        )

        mock_perf.assert_not_called()

    @patch("scripts.evaluate.run_performance_checks", return_value=[])
    @patch("scripts.evaluate.run_integration_fit_checks", return_value=[])
    @patch("scripts.evaluate.run_output_quality_checks", return_value=[])
    @patch("scripts.evaluate.run_edge_case_checks", return_value=[])
    @patch("scripts.evaluate.run_coverage_checks", return_value=[])
    @patch("scripts.evaluate.run_accuracy_checks")
    @patch("scripts.evaluate.load_analysis", return_value={"files": [], "summary": {}})
    def test_report_type(
        self,
        mock_load,
        mock_accuracy,
        mock_coverage,
        mock_edge,
        mock_output,
        mock_integration,
        mock_perf,
    ) -> None:
        """run_evaluation should return EvaluationReport."""
        mock_accuracy.return_value = [
            CheckResult(
                check_id="AC-1",
                name="Test",
                category=CheckCategory.ACCURACY,
                passed=True,
                score=1.0,
                message="OK",
            ),
        ]

        report = run_evaluation(
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/ground-truth",
        )

        assert isinstance(report, EvaluationReport)
        assert report.analysis_path == "/tmp/analysis.json"
        assert report.ground_truth_dir == "/tmp/ground-truth"


class TestPrintReport:
    """Tests for print_report function."""

    def test_print_summary(self, mock_evaluation_report: EvaluationReport, capsys) -> None:
        """print_report should output summary."""
        set_color_enabled(False)
        print_report(mock_evaluation_report)
        captured = capsys.readouterr()

        assert "SUMMARY" in captured.out
        assert "Total Checks:" in captured.out
        assert "Passed:" in captured.out
        assert "Failed:" in captured.out

    def test_print_scores(self, mock_evaluation_report: EvaluationReport, capsys) -> None:
        """print_report should output category scores."""
        set_color_enabled(False)
        print_report(mock_evaluation_report)
        captured = capsys.readouterr()

        assert "SCORE BY CATEGORY" in captured.out
        assert "accuracy" in captured.out.lower()

    def test_print_details(self, mock_evaluation_report: EvaluationReport, capsys) -> None:
        """print_report should output detailed results."""
        set_color_enabled(False)
        print_report(mock_evaluation_report)
        captured = capsys.readouterr()

        assert "DETAILED RESULTS" in captured.out
        assert "AC-1" in captured.out
        assert "PASS" in captured.out

    def test_print_decision(self, mock_evaluation_report: EvaluationReport, capsys) -> None:
        """print_report should output decision."""
        set_color_enabled(False)
        print_report(mock_evaluation_report)
        captured = capsys.readouterr()

        assert "DECISION:" in captured.out


class TestEvaluationReportIntegration:
    """Integration tests for EvaluationReport functionality."""

    def test_report_score_calculation(self) -> None:
        """EvaluationReport should calculate scores correctly."""
        checks = [
            CheckResult(
                check_id="AC-1",
                name="Test 1",
                category=CheckCategory.ACCURACY,
                passed=True,
                score=1.0,
                message="OK",
            ),
            CheckResult(
                check_id="AC-2",
                name="Test 2",
                category=CheckCategory.ACCURACY,
                passed=False,
                score=0.0,
                message="Failed",
            ),
        ]

        report = EvaluationReport(
            timestamp="2026-01-22T00:00:00Z",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/ground-truth",
            checks=checks,
        )

        assert report.passed == 1
        assert report.failed == 1
        assert report.total == 2
        assert report.score == 0.5

    def test_report_score_by_category(self, mock_evaluation_report: EvaluationReport) -> None:
        """Score by category should be calculated correctly."""
        scores = mock_evaluation_report.score_by_category

        assert "accuracy" in scores
        assert "coverage" in scores
        assert "performance" in scores
        assert scores["accuracy"] == 1.0
        assert scores["coverage"] == 1.0
        assert scores["performance"] == 0.5

    def test_report_passed_by_category(self, mock_evaluation_report: EvaluationReport) -> None:
        """Passed by category should return (passed, total) tuples."""
        passed = mock_evaluation_report.passed_by_category

        assert passed["accuracy"] == (2, 2)
        assert passed["coverage"] == (1, 1)
        assert passed["performance"] == (0, 1)

    def test_report_decision(self) -> None:
        """Report decision should be based on score."""
        # High score report (>= 0.8)
        high_checks = [
            CheckResult("AC-1", "Test", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("AC-2", "Test", CheckCategory.ACCURACY, True, 1.0, "OK"),
        ]
        high_report = EvaluationReport("2026-01-22", "/tmp", "/tmp", high_checks)
        assert high_report.decision == "STRONG_PASS"

        # Low score report (< 0.5)
        low_checks = [
            CheckResult("AC-1", "Test", CheckCategory.ACCURACY, False, 0.0, "Fail"),
            CheckResult("AC-2", "Test", CheckCategory.ACCURACY, False, 0.0, "Fail"),
        ]
        low_report = EvaluationReport("2026-01-22", "/tmp", "/tmp", low_checks)
        assert low_report.decision == "FAIL"

    def test_report_decision_pass(self) -> None:
        """Report decision PASS for scores >= 0.6 and < 0.8."""
        # Score = 0.7 (average of 1.0, 1.0, 0.0, 0.8)
        checks = [
            CheckResult("AC-1", "Test", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("AC-2", "Test", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("AC-3", "Test", CheckCategory.ACCURACY, False, 0.0, "Fail"),
            CheckResult("AC-4", "Test", CheckCategory.ACCURACY, True, 0.8, "OK"),
        ]
        report = EvaluationReport("2026-01-22", "/tmp", "/tmp", checks)
        # Score = (1.0 + 1.0 + 0.0 + 0.8) / 4 = 0.7
        assert report.decision == "PASS"

    def test_report_decision_weak_pass(self) -> None:
        """Report decision WEAK_PASS for scores >= 0.5 and < 0.6."""
        # Score = 0.55 (average of 1.0, 0.0, 0.55, 0.65)
        checks = [
            CheckResult("AC-1", "Test", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("AC-2", "Test", CheckCategory.ACCURACY, False, 0.0, "Fail"),
            CheckResult("AC-3", "Test", CheckCategory.ACCURACY, True, 0.55, "OK"),
            CheckResult("AC-4", "Test", CheckCategory.ACCURACY, True, 0.65, "OK"),
        ]
        report = EvaluationReport("2026-01-22", "/tmp", "/tmp", checks)
        # Score = (1.0 + 0.0 + 0.55 + 0.65) / 4 = 0.55
        assert report.decision == "WEAK_PASS"

    def test_report_to_dict(self, mock_evaluation_report: EvaluationReport) -> None:
        """to_dict should produce JSON-serializable dict."""
        d = mock_evaluation_report.to_dict()

        # Verify structure
        assert "timestamp" in d
        assert "summary" in d
        assert "checks" in d
        assert d["summary"]["total"] == 4

        # Should be JSON serializable
        json_str = json.dumps(d)
        assert len(json_str) > 0


class TestScorecardIntegration:
    """Integration tests for scorecard generation."""

    def test_scorecard_json_full_workflow(self, mock_evaluation_report: EvaluationReport) -> None:
        """Test complete scorecard JSON generation workflow."""
        scorecard = generate_scorecard_json(mock_evaluation_report)

        # Verify complete structure
        assert scorecard["tool"] == "devskim"
        assert scorecard["version"] == "1.0.0"
        assert "generated_at" in scorecard
        assert "summary" in scorecard
        assert "dimensions" in scorecard
        assert "thresholds" in scorecard
        assert "metadata" in scorecard

        # Verify summary accuracy
        summary = scorecard["summary"]
        assert summary["total_checks"] == mock_evaluation_report.total
        assert summary["passed"] == mock_evaluation_report.passed
        assert summary["failed"] == mock_evaluation_report.failed

        # Verify JSON serializable
        json_str = json.dumps(scorecard, indent=2)
        assert len(json_str) > 0

    def test_scorecard_md_full_workflow(self, mock_evaluation_report: EvaluationReport) -> None:
        """Test complete scorecard markdown generation workflow."""
        scorecard = generate_scorecard_json(mock_evaluation_report)
        md = generate_scorecard_md(scorecard)

        # Verify all sections present
        assert "# DevSkim Evaluation Scorecard" in md
        assert "## Summary" in md
        assert "## Dimensions" in md
        assert "## Detailed Results" in md
        assert "## Decision Thresholds" in md

        # Verify specific content
        assert "**Generated:**" in md
        assert "**Decision:**" in md
        assert "| Total Checks |" in md

    def test_scorecard_with_all_passing(self) -> None:
        """Scorecard with all checks passing should show STRONG_PASS."""
        checks = [
            CheckResult("AC-1", "Test 1", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("AC-2", "Test 2", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("CV-1", "Test 3", CheckCategory.COVERAGE, True, 1.0, "OK"),
        ]
        report = EvaluationReport("2026-01-22", "/tmp", "/tmp", checks)

        scorecard = generate_scorecard_json(report)

        assert scorecard["summary"]["decision"] == "STRONG_PASS"
        assert scorecard["summary"]["score"] == 1.0
        assert scorecard["summary"]["passed"] == 3
        assert scorecard["summary"]["failed"] == 0

    def test_scorecard_with_all_failing(self) -> None:
        """Scorecard with all checks failing should show FAIL."""
        checks = [
            CheckResult("AC-1", "Test 1", CheckCategory.ACCURACY, False, 0.0, "Fail"),
            CheckResult("AC-2", "Test 2", CheckCategory.ACCURACY, False, 0.0, "Fail"),
        ]
        report = EvaluationReport("2026-01-22", "/tmp", "/tmp", checks)

        scorecard = generate_scorecard_json(report)

        assert scorecard["summary"]["decision"] == "FAIL"
        assert scorecard["summary"]["score"] == 0.0
        assert scorecard["summary"]["passed"] == 0
        assert scorecard["summary"]["failed"] == 2

    def test_scorecard_dimensions_grouping(self) -> None:
        """Dimensions should group checks by category."""
        checks = [
            CheckResult("AC-1", "Accuracy 1", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("AC-2", "Accuracy 2", CheckCategory.ACCURACY, True, 1.0, "OK"),
            CheckResult("CV-1", "Coverage 1", CheckCategory.COVERAGE, True, 1.0, "OK"),
            CheckResult("PF-1", "Perf 1", CheckCategory.PERFORMANCE, False, 0.0, "Slow"),
        ]
        report = EvaluationReport("2026-01-22", "/tmp", "/tmp", checks)

        scorecard = generate_scorecard_json(report)
        dimensions = scorecard["dimensions"]

        assert len(dimensions) == 3  # accuracy, coverage, performance

        # Find each category
        dim_names = [d["name"].lower() for d in dimensions]
        assert "accuracy" in dim_names
        assert "coverage" in dim_names
        assert "performance" in dim_names

        # Verify accuracy dimension
        accuracy_dim = next(d for d in dimensions if "accuracy" in d["name"].lower())
        assert accuracy_dim["total_checks"] == 2
        assert accuracy_dim["passed"] == 2
        assert len(accuracy_dim["checks"]) == 2

    def test_markdown_truncates_long_messages(self) -> None:
        """Long messages in markdown should be truncated."""
        long_message = "A" * 100
        checks = [
            CheckResult("AC-1", "Test", CheckCategory.ACCURACY, True, 1.0, long_message),
        ]
        report = EvaluationReport("2026-01-22", "/tmp", "/tmp", checks)

        scorecard = generate_scorecard_json(report)
        md = generate_scorecard_md(scorecard)

        # Original long message should not appear in full
        assert long_message not in md
        # But truncated version with ellipsis should
        assert "..." in md


class TestMainFunction:
    """Tests for main() function."""

    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_with_explicit_analysis(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        mock_evaluation_report,
        tmp_path,
    ) -> None:
        """main() with explicit analysis path should work."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": [], "summary": {}}')

        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        output_file = tmp_path / "report.json"

        mock_run_eval.return_value = mock_evaluation_report
        mock_json.return_value = {"summary": {"score": 0.875}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            "--json",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Score is 0.875, should pass
            assert exc_info.value.code == 0

        mock_run_eval.assert_called_once()

    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_quick_mode(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        mock_evaluation_report,
        tmp_path,
    ) -> None:
        """--quick flag should skip performance checks."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": []}')

        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        output_file = tmp_path / "report.json"

        mock_run_eval.return_value = mock_evaluation_report
        mock_json.return_value = {"summary": {}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            "--quick",
            "--json",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

        # Verify skip_performance was True
        call_kwargs = mock_run_eval.call_args[1]
        assert call_kwargs["skip_performance"] is True

    @patch("scripts.evaluate.set_color_enabled")
    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_no_color(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        mock_set_color,
        mock_evaluation_report,
        tmp_path,
    ) -> None:
        """--no-color flag should disable colors."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": []}')

        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        output_file = tmp_path / "report.json"

        mock_run_eval.return_value = mock_evaluation_report
        mock_json.return_value = {"summary": {}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            "--no-color",
            "--json",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

        mock_set_color.assert_called_with(False)

    def test_main_missing_analysis_file(self, tmp_path) -> None:
        """main() should error on missing analysis file."""
        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        test_args = [
            "evaluate",
            "--analysis", str(tmp_path / "nonexistent.json"),
            "--ground-truth", str(ground_truth_dir),
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_creates_ground_truth_dir(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        mock_evaluation_report,
        tmp_path,
    ) -> None:
        """main() should create ground truth dir if missing."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": []}')

        ground_truth_dir = tmp_path / "new-ground-truth"
        output_file = tmp_path / "report.json"

        mock_run_eval.return_value = mock_evaluation_report
        mock_json.return_value = {"summary": {}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            "--json",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

        assert ground_truth_dir.exists()

    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_exit_code_pass(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        tmp_path,
    ) -> None:
        """main() should exit 0 when score >= 0.5."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": []}')

        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        output_file = tmp_path / "report.json"

        # Create report with score >= 0.5
        passing_report = EvaluationReport(
            timestamp="2026-01-22T00:00:00Z",
            analysis_path=str(analysis_file),
            ground_truth_dir=str(ground_truth_dir),
            checks=[
                CheckResult("AC-1", "Test", CheckCategory.ACCURACY, True, 1.0, "OK"),
            ],
        )

        mock_run_eval.return_value = passing_report
        mock_json.return_value = {"summary": {}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            "--json",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_exit_code_fail(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        tmp_path,
    ) -> None:
        """main() should exit 1 when score < 0.5."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": []}')

        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        output_file = tmp_path / "report.json"

        # Create report with score < 0.5
        failing_report = EvaluationReport(
            timestamp="2026-01-22T00:00:00Z",
            analysis_path=str(analysis_file),
            ground_truth_dir=str(ground_truth_dir),
            checks=[
                CheckResult("AC-1", "Test", CheckCategory.ACCURACY, False, 0.0, "Fail"),
            ],
        )

        mock_run_eval.return_value = failing_report
        mock_json.return_value = {"summary": {}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            "--json",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_json_mode_no_print(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        mock_evaluation_report,
        tmp_path,
    ) -> None:
        """--json flag should skip print_report."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": []}')

        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        output_file = tmp_path / "report.json"

        mock_run_eval.return_value = mock_evaluation_report
        mock_json.return_value = {"summary": {}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            "--json",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

        # print_report should NOT be called in json mode
        mock_print.assert_not_called()

    @patch("scripts.evaluate.generate_scorecard_md")
    @patch("scripts.evaluate.generate_scorecard_json")
    @patch("scripts.evaluate.print_report")
    @patch("scripts.evaluate.run_evaluation")
    def test_main_console_mode_calls_print(
        self,
        mock_run_eval,
        mock_print,
        mock_json,
        mock_md,
        mock_evaluation_report,
        tmp_path,
    ) -> None:
        """Without --json flag, print_report should be called."""
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text('{"files": []}')

        ground_truth_dir = tmp_path / "ground-truth"
        ground_truth_dir.mkdir()

        output_file = tmp_path / "report.json"

        mock_run_eval.return_value = mock_evaluation_report
        mock_json.return_value = {"summary": {}}
        mock_md.return_value = "# Scorecard"

        test_args = [
            "evaluate",
            "--analysis", str(analysis_file),
            "--ground-truth", str(ground_truth_dir),
            "--output", str(output_file),
            # No --json flag
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

        # print_report SHOULD be called in console mode
        mock_print.assert_called_once_with(mock_evaluation_report)
