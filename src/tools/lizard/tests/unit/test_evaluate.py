"""Tests for evaluate.py covering normalization, ground truth loading,
scorecard generation, report printing, and scorecard saving."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts + parent directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir.parent))

from scripts.evaluate import (
    _normalize_analysis,
    load_json,
    load_ground_truth_for_language,
    load_all_ground_truth,
    merge_ground_truth,
    generate_scorecard_json,
    generate_scorecard_md,
    print_report,
    save_scorecards,
    run_evaluation,
)
from scripts.checks import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    EvaluationReport,
)


# =============================================================================
# _normalize_analysis
# =============================================================================

class TestNormalizeAnalysis:
    """Tests for analysis JSON normalization to expected format."""

    def test_envelope_format_extracts_data(self):
        """Envelope format with 'data' key extracts data payload."""
        raw = {
            "schema_version": "1.0",
            "data": {
                "files": [{"path": "a.py"}],
                "summary": {"total_files": 1},
            }
        }
        result = _normalize_analysis(raw)
        assert "files" in result
        assert result["files"] == [{"path": "a.py"}]

    def test_files_at_top_level(self):
        """When files is already at top level, returns as-is."""
        raw = {
            "files": [{"path": "b.py"}],
            "summary": {"total_files": 1},
        }
        result = _normalize_analysis(raw)
        assert result is raw  # Same object returned

    def test_results_key_format(self):
        """Old format with 'results' key gets extracted and reshaped."""
        raw = {
            "schema_version": "1.0",
            "repo_name": "test",
            "repo_path": "/test",
            "results": {
                "files": [{"path": "c.py"}],
                "summary": {"total_files": 1},
                "by_language": {"Python": {}},
                "directories": [],
                "run_id": "run-001",
                "timestamp": "2026-01-20T00:00:00Z",
                "root_path": ".",
                "lizard_version": "1.17.10",
            }
        }
        result = _normalize_analysis(raw)
        assert result["files"] == [{"path": "c.py"}]
        assert result["schema_version"] == "1.0"
        assert result["repo_name"] == "test"
        assert result["run_id"] == "run-001"

    def test_unknown_format_returned_as_is(self):
        """Unknown format is returned unchanged."""
        raw = {"random_key": "value"}
        result = _normalize_analysis(raw)
        assert result is raw

    def test_data_key_not_dict_falls_through(self):
        """If 'data' is not a dict, it falls through to other checks."""
        raw = {"data": "not_a_dict", "files": [{"path": "d.py"}]}
        result = _normalize_analysis(raw)
        # Has 'files' at top level, so returns as-is
        assert result is raw


# =============================================================================
# load_json / load_ground_truth_for_language / load_all_ground_truth
# =============================================================================

class TestGroundTruthLoading:
    """Tests for ground truth file loading."""

    def test_load_json(self, tmp_path):
        """load_json reads and parses a JSON file."""
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}')
        result = load_json(f)
        assert result == {"key": "value"}

    def test_load_ground_truth_for_language_exists(self, tmp_path):
        """load_ground_truth_for_language returns data when file exists."""
        gt = tmp_path / "python.json"
        gt.write_text('{"files": {"main.py": {"expected_functions": 5}}}')
        result = load_ground_truth_for_language(tmp_path, "python")
        assert result is not None
        assert "files" in result

    def test_load_ground_truth_for_language_missing(self, tmp_path):
        """load_ground_truth_for_language returns None when file missing."""
        result = load_ground_truth_for_language(tmp_path, "java")
        assert result is None

    def test_load_all_ground_truth(self, tmp_path):
        """load_all_ground_truth loads all JSON files in directory."""
        (tmp_path / "python.json").write_text('{"files": {}}')
        (tmp_path / "csharp.json").write_text('{"files": {}}')
        result = load_all_ground_truth(tmp_path)
        assert "python" in result
        assert "csharp" in result
        assert len(result) == 2

    def test_load_all_ground_truth_empty_dir(self, tmp_path):
        """Empty directory returns empty dict."""
        result = load_all_ground_truth(tmp_path)
        assert result == {}


# =============================================================================
# merge_ground_truth
# =============================================================================

class TestMergeGroundTruth:
    """Tests for merging multi-language ground truth."""

    def test_merge_single_language(self):
        """Single language merges correctly."""
        gt = {
            "python": {
                "files": {
                    "main.py": {"expected_functions": 3, "total_ccn": 10}
                }
            }
        }
        merged = merge_ground_truth(gt)
        assert merged["languages"] == ["python"]
        assert "python/main.py" in merged["files"]
        assert merged["total_functions"] == 3
        assert merged["total_ccn"] == 10

    def test_merge_multiple_languages(self):
        """Multiple languages merge with prefixed paths."""
        gt = {
            "python": {
                "files": {
                    "main.py": {"expected_functions": 2, "total_ccn": 5}
                }
            },
            "csharp": {
                "files": {
                    "Program.cs": {"expected_functions": 4, "total_ccn": 8}
                }
            },
        }
        merged = merge_ground_truth(gt)
        assert len(merged["languages"]) == 2
        assert "python/main.py" in merged["files"]
        assert "csharp/Program.cs" in merged["files"]
        assert merged["total_functions"] == 6
        assert merged["total_ccn"] == 13

    def test_merge_empty(self):
        """Empty ground truth produces empty merge."""
        merged = merge_ground_truth({})
        assert merged["languages"] == []
        assert merged["files"] == {}
        assert merged["total_functions"] == 0

    def test_merge_missing_fields_default_to_zero(self):
        """Files missing expected_functions or total_ccn default to 0."""
        gt = {
            "go": {
                "files": {
                    "main.go": {}  # No expected_functions or total_ccn
                }
            }
        }
        merged = merge_ground_truth(gt)
        assert merged["total_functions"] == 0
        assert merged["total_ccn"] == 0


# =============================================================================
# generate_scorecard_json
# =============================================================================

class TestGenerateScorecardJson:
    """Tests for scorecard JSON generation from EvaluationReport."""

    def _make_report(self, checks: list[CheckResult]) -> EvaluationReport:
        return EvaluationReport(
            timestamp="2026-01-20T12:00:00Z",
            analysis_path="/test/output.json",
            ground_truth_path="/test/ground-truth",
            checks=checks,
        )

    def test_all_passing_strong_pass(self):
        """All checks passing produces STRONG_PASS decision."""
        checks = [
            CheckResult("AC-1", "test1", CheckCategory.ACCURACY, CheckSeverity.CRITICAL,
                        True, 1.0, "ok"),
            CheckResult("CV-1", "test2", CheckCategory.COVERAGE, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)

        assert scorecard["summary"]["decision"] == "STRONG_PASS"
        assert scorecard["summary"]["score"] == 1.0
        assert scorecard["summary"]["normalized_score"] == 5.0
        assert scorecard["tool"] == "lizard"
        assert len(scorecard["dimensions"]) == 2

    def test_all_failing_gives_fail(self):
        """All checks failing produces FAIL decision."""
        checks = [
            CheckResult("AC-1", "test1", CheckCategory.ACCURACY, CheckSeverity.CRITICAL,
                        False, 0.0, "bad"),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)

        assert scorecard["summary"]["decision"] == "FAIL"
        assert scorecard["summary"]["score"] == 0.0
        assert scorecard["summary"]["normalized_score"] == 1.0

    def test_mixed_results_decision_thresholds(self):
        """Mixed results produce appropriate decision based on score."""
        # Score 0.75 -> normalized = 1 + 0.75*4 = 4.0 -> STRONG_PASS
        checks = [
            CheckResult("AC-1", "t1", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-2", "t2", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-3", "t3", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-4", "t4", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        False, 0.0, "bad"),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)
        assert scorecard["summary"]["decision"] == "STRONG_PASS"

    def test_severity_breakdown_in_dimensions(self):
        """Dimensions include severity breakdown."""
        checks = [
            CheckResult("AC-1", "t1", CheckCategory.ACCURACY, CheckSeverity.CRITICAL,
                        True, 1.0, "ok"),
            CheckResult("AC-2", "t2", CheckCategory.ACCURACY, CheckSeverity.LOW,
                        False, 0.0, "bad"),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)

        dim = scorecard["dimensions"][0]
        assert dim["category"] == "accuracy"
        assert "critical" in dim["by_severity"]
        assert "low" in dim["by_severity"]
        assert dim["by_severity"]["critical"]["passed"] == 1
        assert dim["by_severity"]["low"]["passed"] == 0

    def test_critical_failures_listed(self):
        """Critical failures are explicitly listed in scorecard."""
        checks = [
            CheckResult("AC-1", "critical_test", CheckCategory.ACCURACY,
                        CheckSeverity.CRITICAL, False, 0.0, "critical failure"),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)

        assert len(scorecard["critical_failures"]) == 1
        assert scorecard["critical_failures"][0]["check_id"] == "AC-1"

    def test_weak_pass_boundary(self):
        """Score right at the WEAK_PASS boundary (normalized 3.0)."""
        # normalized = 1 + score * 4, so score = 0.5 gives normalized = 3.0 -> WEAK_PASS
        checks = [
            CheckResult("AC-1", "t1", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-2", "t2", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        False, 0.0, "bad"),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)
        assert scorecard["summary"]["decision"] == "WEAK_PASS"

    def test_pass_boundary(self):
        """Score at PASS boundary (normalized >= 3.5 but < 4.0)."""
        # score = 0.625 -> normalized = 1 + 0.625*4 = 3.5 -> PASS
        checks = [
            CheckResult("AC-1", "t1", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-2", "t2", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-3", "t3", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-4", "t4", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-5", "t5", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-6", "t6", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        False, 0.0, "bad"),
            CheckResult("AC-7", "t7", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        False, 0.0, "bad"),
            CheckResult("AC-8", "t8", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        False, 0.0, "bad"),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)
        assert scorecard["summary"]["decision"] == "PASS"


# =============================================================================
# generate_scorecard_md
# =============================================================================

class TestGenerateScorecardMd:
    """Tests for markdown scorecard generation."""

    def _make_report_and_scorecard(self, checks):
        report = EvaluationReport(
            timestamp="2026-01-20T12:00:00Z",
            analysis_path="/test/output.json",
            ground_truth_path="/test/ground-truth",
            checks=checks,
        )
        scorecard = generate_scorecard_json(report)
        return report, scorecard

    def test_contains_header_and_summary(self):
        """Markdown contains title, decision, and summary table."""
        checks = [
            CheckResult("AC-1", "test1", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
        ]
        report, scorecard = self._make_report_and_scorecard(checks)
        md = generate_scorecard_md(report, scorecard)

        assert "# Lizard Evaluation Scorecard" in md
        assert "STRONG_PASS" in md
        assert "## Summary" in md
        assert "Total Checks" in md
        assert "Passed" in md

    def test_contains_dimensions_table(self):
        """Markdown contains dimensions table."""
        checks = [
            CheckResult("AC-1", "test1", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("CV-1", "test2", CheckCategory.COVERAGE, CheckSeverity.MEDIUM,
                        True, 1.0, "ok"),
        ]
        report, scorecard = self._make_report_and_scorecard(checks)
        md = generate_scorecard_md(report, scorecard)

        assert "## Dimensions" in md
        assert "Accuracy" in md
        assert "Coverage" in md

    def test_contains_critical_failures_section(self):
        """Markdown includes critical failures when present."""
        checks = [
            CheckResult("AC-1", "critical_fail", CheckCategory.ACCURACY,
                        CheckSeverity.CRITICAL, False, 0.0, "Something broke"),
        ]
        report, scorecard = self._make_report_and_scorecard(checks)
        md = generate_scorecard_md(report, scorecard)

        assert "## Critical Failures" in md
        assert "AC-1" in md

    def test_no_critical_failures_section_when_none(self):
        """Markdown omits critical failures section when none."""
        checks = [
            CheckResult("AC-1", "ok", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "fine"),
        ]
        report, scorecard = self._make_report_and_scorecard(checks)
        md = generate_scorecard_md(report, scorecard)

        assert "## Critical Failures" not in md

    def test_contains_detailed_results(self):
        """Markdown contains detailed check results by category."""
        checks = [
            CheckResult("AC-1", "accuracy_check", CheckCategory.ACCURACY,
                        CheckSeverity.HIGH, True, 0.9, "mostly ok"),
        ]
        report, scorecard = self._make_report_and_scorecard(checks)
        md = generate_scorecard_md(report, scorecard)

        assert "## Detailed Results" in md
        assert "AC-1" in md
        assert "PASS" in md

    def test_long_message_truncated(self):
        """Check messages longer than 50 chars get truncated with '...'."""
        long_msg = "A" * 60
        checks = [
            CheckResult("AC-1", "test", CheckCategory.ACCURACY,
                        CheckSeverity.HIGH, True, 1.0, long_msg),
        ]
        report, scorecard = self._make_report_and_scorecard(checks)
        md = generate_scorecard_md(report, scorecard)

        assert "..." in md  # Truncation indicator


# =============================================================================
# print_report
# =============================================================================

class TestPrintReport:
    """Tests for console report printing."""

    def test_prints_header(self, capsys):
        """print_report outputs header with timestamp."""
        report = EvaluationReport(
            timestamp="2026-01-20T12:00:00Z",
            analysis_path="/test/output.json",
            ground_truth_path="/test/gt",
            checks=[
                CheckResult("AC-1", "test", CheckCategory.ACCURACY,
                            CheckSeverity.HIGH, True, 1.0, "ok"),
            ],
        )
        print_report(report)
        captured = capsys.readouterr()
        assert "LIZARD EVALUATION REPORT" in captured.out
        assert "2026-01-20T12:00:00Z" in captured.out
        assert "SUMMARY" in captured.out

    def test_prints_critical_failures(self, capsys):
        """print_report shows critical failures section."""
        report = EvaluationReport(
            timestamp="2026-01-20T12:00:00Z",
            analysis_path="/test/output.json",
            ground_truth_path="/test/gt",
            checks=[
                CheckResult("AC-1", "critical_fail", CheckCategory.ACCURACY,
                            CheckSeverity.CRITICAL, False, 0.0, "big problem"),
            ],
        )
        print_report(report)
        captured = capsys.readouterr()
        assert "CRITICAL FAILURES" in captured.out
        assert "big problem" in captured.out

    def test_verbose_shows_evidence(self, capsys):
        """Verbose mode includes evidence in output."""
        report = EvaluationReport(
            timestamp="2026-01-20T12:00:00Z",
            analysis_path="/test/output.json",
            ground_truth_path="/test/gt",
            checks=[
                CheckResult("AC-1", "test", CheckCategory.ACCURACY,
                            CheckSeverity.HIGH, True, 1.0, "ok",
                            evidence={"detail": "some_evidence"}),
            ],
        )
        print_report(report, verbose=True)
        captured = capsys.readouterr()
        assert "some_evidence" in captured.out


# =============================================================================
# save_scorecards
# =============================================================================

class TestSaveScorecard:
    """Tests for saving scorecard files to disk."""

    def test_saves_json_and_md(self, tmp_path):
        """save_scorecards writes both scorecard.json and scorecard.md."""
        report = EvaluationReport(
            timestamp="2026-01-20T12:00:00Z",
            analysis_path="/test/output.json",
            ground_truth_path="/test/gt",
            checks=[
                CheckResult("AC-1", "test", CheckCategory.ACCURACY,
                            CheckSeverity.HIGH, True, 1.0, "ok"),
            ],
        )
        save_scorecards(report, tmp_path)

        assert (tmp_path / "scorecard.json").exists()
        assert (tmp_path / "scorecard.md").exists()

        # Verify JSON is valid
        data = json.loads((tmp_path / "scorecard.json").read_text())
        assert data["tool"] == "lizard"
        assert "summary" in data

        # Verify Markdown has content
        md = (tmp_path / "scorecard.md").read_text()
        assert "# Lizard Evaluation Scorecard" in md

    def test_creates_output_directory(self, tmp_path):
        """save_scorecards creates the output directory if missing."""
        out = tmp_path / "new" / "nested" / "dir"
        report = EvaluationReport(
            timestamp="2026-01-20T12:00:00Z",
            analysis_path="/test/output.json",
            ground_truth_path="/test/gt",
            checks=[],
        )
        save_scorecards(report, out)
        assert out.exists()


# =============================================================================
# EvaluationReport
# =============================================================================

class TestEvaluationReport:
    """Tests for EvaluationReport computed properties."""

    def test_empty_report_score(self):
        """Empty report has 0 score."""
        report = EvaluationReport("ts", "path", "gt", checks=[])
        assert report.overall_score == 0.0
        assert report.total_checks == 0
        assert report.passed_checks == 0
        assert report.failed_checks == 0

    def test_to_dict_decision_logic(self):
        """to_dict produces correct decision based on score."""
        # All passing -> STRONG_PASS
        report = EvaluationReport(
            "ts", "path", "gt",
            checks=[
                CheckResult("A", "t", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                            True, 1.0, "ok"),
            ],
        )
        d = report.to_dict()
        assert d["decision"] == "STRONG_PASS"
        assert d["score"] == 1.0

    def test_by_category_filters(self):
        """by_category returns only checks in that category."""
        checks = [
            CheckResult("AC-1", "t1", CheckCategory.ACCURACY, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("CV-1", "t2", CheckCategory.COVERAGE, CheckSeverity.HIGH,
                        True, 1.0, "ok"),
            CheckResult("AC-2", "t3", CheckCategory.ACCURACY, CheckSeverity.LOW,
                        False, 0.0, "bad"),
        ]
        report = EvaluationReport("ts", "path", "gt", checks=checks)
        acc = report.by_category(CheckCategory.ACCURACY)
        assert len(acc) == 2
        cov = report.by_category(CheckCategory.COVERAGE)
        assert len(cov) == 1
