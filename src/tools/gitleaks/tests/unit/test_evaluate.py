"""Unit tests for evaluate module (normalize_analysis, determine_decision, scorecard generation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from evaluate import (
    determine_decision,
    evaluate_repository,
    generate_scorecard_json,
    generate_scorecard_md,
    normalize_analysis,
    print_report,
)
from scripts.checks import CheckResult, EvaluationReport


# ---------------------------------------------------------------------------
# normalize_analysis
# ---------------------------------------------------------------------------
class TestNormalizeAnalysis:
    """Tests for the normalize_analysis helper."""

    def test_envelope_format_with_data_key(self) -> None:
        """Envelope format (metadata+data) should unwrap correctly."""
        raw = {
            "metadata": {
                "schema_version": "1.0.0",
                "timestamp": "2026-01-01T00:00:00Z",
                "repo_id": "my-repo",
            },
            "data": {
                "total_secrets": 3,
                "findings": [],
            },
        }
        result = normalize_analysis(raw)
        assert result["total_secrets"] == 3
        assert result["schema_version"] == "1.0.0"
        assert result["timestamp"] == "2026-01-01T00:00:00Z"
        assert result["repository"] == "my-repo"
        assert result["repo_path"] == "my-repo"
        assert result["_root"] is raw

    def test_envelope_format_preserves_existing_keys(self) -> None:
        """Fields already in data should not be overwritten by metadata."""
        raw = {
            "metadata": {"schema_version": "2.0.0", "repo_id": "meta-repo"},
            "data": {"schema_version": "1.0.0", "repository": "data-repo"},
        }
        result = normalize_analysis(raw)
        # setdefault means data's value wins
        assert result["schema_version"] == "1.0.0"
        assert result["repository"] == "data-repo"

    def test_legacy_format_with_results_key(self) -> None:
        """Legacy format (results) should unwrap correctly."""
        raw = {
            "schema_version": "2.0.0",
            "generated_at": "2026-02-01T00:00:00Z",
            "repo_name": "legacy-repo",
            "repo_path": "/tmp/legacy",
            "results": {
                "tool": "gitleaks",
                "total_secrets": 5,
            },
        }
        result = normalize_analysis(raw)
        assert result["tool"] == "gitleaks"
        assert result["total_secrets"] == 5
        assert result["schema_version"] == "2.0.0"
        assert result["timestamp"] == "2026-02-01T00:00:00Z"
        assert result["repository"] == "legacy-repo"
        assert result["repo_path"] == "/tmp/legacy"
        assert result["_root"] is raw

    def test_unknown_format_passthrough(self) -> None:
        """If neither 'data' nor 'results' key, return as-is."""
        raw = {"total_secrets": 0, "findings": []}
        result = normalize_analysis(raw)
        assert result is raw


# ---------------------------------------------------------------------------
# determine_decision
# ---------------------------------------------------------------------------
class TestDetermineDecision:
    """Tests for determine_decision thresholds."""

    @pytest.mark.parametrize(
        "score, expected_decision",
        [
            (1.0, "STRONG_PASS"),   # 5.0 -> STRONG_PASS
            (0.85, "STRONG_PASS"),  # 4.25 -> STRONG_PASS
            (0.80, "STRONG_PASS"),  # 4.0 -> STRONG_PASS
            (0.79, "PASS"),         # 3.95 -> PASS
            (0.75, "PASS"),         # 3.75 -> PASS
            (0.70, "PASS"),         # 3.5 -> PASS
            (0.69, "WEAK_PASS"),    # 3.45 -> WEAK_PASS
            (0.65, "WEAK_PASS"),    # 3.25 -> WEAK_PASS
            (0.60, "WEAK_PASS"),    # 3.0 -> WEAK_PASS
            (0.59, "FAIL"),         # 2.95 -> FAIL
            (0.50, "FAIL"),         # 2.5 -> FAIL
            (0.0, "FAIL"),          # 0.0 -> FAIL
        ],
    )
    def test_threshold_boundaries(self, score: float, expected_decision: str) -> None:
        assert determine_decision(score) == expected_decision


# ---------------------------------------------------------------------------
# evaluate_repository
# ---------------------------------------------------------------------------
class TestEvaluateRepository:
    """Tests for evaluate_repository end-to-end."""

    def test_evaluate_simple_analysis(self, tmp_path: Path) -> None:
        """Run evaluation with a minimal analysis and ground truth pair."""
        analysis = {
            "metadata": {
                "tool_name": "gitleaks",
                "tool_version": "8.18.4",
                "run_id": "run-1",
                "repo_id": "test-repo",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "2026-01-01T00:00:00Z",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "gitleaks",
                "tool_version": "8.18.4",
                "total_secrets": 0,
                "unique_secrets": 0,
                "secrets_in_head": 0,
                "secrets_in_history": 0,
                "files_with_secrets": 0,
                "commits_with_secrets": 0,
                "secrets_by_rule": {},
                "secrets_by_severity": {},
                "findings": [],
                "files": {},
                "directories": {},
                "scan_time_ms": 100.0,
            },
        }
        ground_truth = {
            "expected": {
                "total_secrets": 0,
                "unique_secrets": 0,
                "findings": [],
            },
        }

        analysis_path = tmp_path / "analysis.json"
        gt_path = tmp_path / "ground_truth.json"
        analysis_path.write_text(json.dumps(analysis))
        gt_path.write_text(json.dumps(ground_truth))

        report = evaluate_repository(analysis_path, gt_path)

        assert report.repository == "test-repo"
        assert report.total_checks > 0
        assert isinstance(report.pass_rate, float)


# ---------------------------------------------------------------------------
# generate_scorecard_json
# ---------------------------------------------------------------------------
class TestGenerateScorecardJson:
    """Tests for generate_scorecard_json."""

    def _make_report(self, passed: int, failed: int, category: str = "Accuracy") -> EvaluationReport:
        report = EvaluationReport(repository="test-repo")
        for i in range(passed):
            report.add_result(
                CheckResult(
                    check_id=f"T-{i}",
                    category=category,
                    passed=True,
                    message=f"Check {i} passed",
                )
            )
        for i in range(failed):
            report.add_result(
                CheckResult(
                    check_id=f"T-fail-{i}",
                    category=category,
                    passed=False,
                    message=f"Check {i} failed",
                )
            )
        return report

    def test_all_passing(self) -> None:
        """All checks pass -> STRONG_PASS, score 100%."""
        report = self._make_report(10, 0)
        scorecard = generate_scorecard_json([report])

        assert scorecard["tool"] == "gitleaks"
        assert scorecard["summary"]["total_checks"] == 10
        assert scorecard["summary"]["passed"] == 10
        assert scorecard["summary"]["failed"] == 0
        assert scorecard["summary"]["decision"] == "STRONG_PASS"
        assert scorecard["summary"]["score_percent"] == 100.0

    def test_all_failing(self) -> None:
        """All checks fail -> FAIL."""
        report = self._make_report(0, 5)
        scorecard = generate_scorecard_json([report])

        assert scorecard["summary"]["decision"] == "FAIL"
        assert scorecard["summary"]["passed"] == 0
        assert scorecard["summary"]["failed"] == 5

    def test_mixed_results(self) -> None:
        """Partial pass rate."""
        report = self._make_report(7, 3)
        scorecard = generate_scorecard_json([report])

        assert scorecard["summary"]["total_checks"] == 10
        assert scorecard["summary"]["passed"] == 7
        # 7/10 = 0.7 -> normalized 3.5 -> PASS
        assert scorecard["summary"]["decision"] == "PASS"

    def test_multiple_dimensions(self) -> None:
        """Reports with different categories produce separate dimensions."""
        report = EvaluationReport(repository="multi")
        report.add_result(CheckResult(check_id="A-1", category="Accuracy", passed=True, message="ok"))
        report.add_result(CheckResult(check_id="D-1", category="Detection", passed=False, message="miss"))

        scorecard = generate_scorecard_json([report])

        assert len(scorecard["dimensions"]) == 2
        dim_names = {d["name"] for d in scorecard["dimensions"]}
        assert "Accuracy" in dim_names
        assert "Detection" in dim_names

    def test_critical_failures_extracted(self) -> None:
        """Critical failures are listed separately."""
        report = EvaluationReport(repository="test")
        report.add_result(
            CheckResult(
                check_id="CRITICAL-1",
                category="Security",
                passed=False,
                message="Critical security failure",
            )
        )
        report.add_result(
            CheckResult(
                check_id="NORMAL-1",
                category="Security",
                passed=False,
                message="Normal failure",
            )
        )

        scorecard = generate_scorecard_json([report])

        critical = scorecard["critical_failures"]
        assert len(critical) == 1
        assert critical[0]["check_id"] == "CRITICAL-1"

    def test_empty_reports_list(self) -> None:
        """Empty reports list should produce valid scorecard."""
        scorecard = generate_scorecard_json([])

        assert scorecard["summary"]["total_checks"] == 0
        assert scorecard["summary"]["score"] == 0
        assert scorecard["summary"]["decision"] == "FAIL"
        assert scorecard["dimensions"] == []

    def test_multiple_reports(self) -> None:
        """Multiple repos aggregated."""
        r1 = self._make_report(5, 0, "Accuracy")
        r2 = self._make_report(3, 2, "Accuracy")

        scorecard = generate_scorecard_json([r1, r2])

        assert scorecard["summary"]["total_checks"] == 10
        assert scorecard["summary"]["passed"] == 8
        assert scorecard["metadata"]["repositories_evaluated"] == 2

    def test_thresholds_present(self) -> None:
        """Threshold definitions should always be in scorecard."""
        scorecard = generate_scorecard_json([self._make_report(1, 0)])
        assert "STRONG_PASS" in scorecard["thresholds"]
        assert "FAIL" in scorecard["thresholds"]


# ---------------------------------------------------------------------------
# generate_scorecard_md
# ---------------------------------------------------------------------------
class TestGenerateScorecardMd:
    """Tests for generate_scorecard_md markdown rendering."""

    def _minimal_scorecard(self) -> dict:
        return {
            "tool": "gitleaks",
            "generated_at": "2026-01-01T00:00:00Z",
            "summary": {
                "total_checks": 5,
                "passed": 4,
                "failed": 1,
                "score": 0.8,
                "score_percent": 80.0,
                "normalized_score": 4.0,
                "decision": "STRONG_PASS",
            },
            "dimensions": [
                {
                    "id": "D1",
                    "name": "Accuracy",
                    "total_checks": 3,
                    "passed": 3,
                    "score": 5.0,
                    "checks": [
                        {"check_id": "A-1", "passed": True, "message": "Check 1 ok"},
                        {"check_id": "A-2", "passed": True, "message": "Check 2 ok"},
                        {"check_id": "A-3", "passed": True, "message": "Check 3 ok"},
                    ],
                },
                {
                    "id": "D2",
                    "name": "Detection",
                    "total_checks": 2,
                    "passed": 1,
                    "score": 2.5,
                    "checks": [
                        {"check_id": "D-1", "passed": True, "message": "Found"},
                        {"check_id": "D-2", "passed": False, "message": "Missed critical item that was expected to be detected"},
                    ],
                },
            ],
            "critical_failures": [
                {"check_id": "D-2", "name": "Missed", "message": "Missed critical item"},
            ],
            "thresholds": {
                "STRONG_PASS": ">= 4.0 (80%+)",
                "PASS": ">= 3.5 (70%+)",
                "WEAK_PASS": ">= 3.0 (60%+)",
                "FAIL": "< 3.0 (below 60%)",
            },
            "metadata": {
                "repositories_evaluated": 2,
            },
        }

    def test_markdown_contains_header(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "# Gitleaks Evaluation Scorecard" in md

    def test_markdown_contains_decision(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "STRONG_PASS" in md

    def test_markdown_contains_summary_table(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "| Total Checks | 5 |" in md
        assert "| Passed | 4 |" in md
        assert "| Failed | 1 |" in md

    def test_markdown_dimensions_table(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "## Dimensions" in md
        assert "Accuracy" in md
        assert "Detection" in md

    def test_markdown_critical_failures(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "## Critical Failures" in md
        assert "D-2" in md

    def test_markdown_detailed_results(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "## Detailed Results" in md
        assert "### Accuracy" in md

    def test_markdown_truncates_long_messages(self) -> None:
        """Messages longer than 50 chars should be truncated with '...'."""
        md = generate_scorecard_md(self._minimal_scorecard())
        # The Detection D-2 message is > 50 chars, should be truncated
        assert "..." in md

    def test_markdown_decision_thresholds(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "## Decision Thresholds" in md
        assert "STRONG_PASS" in md
        assert ">= 4.0 (80%+)" in md

    def test_markdown_footer_repos_evaluated(self) -> None:
        md = generate_scorecard_md(self._minimal_scorecard())
        assert "Repositories evaluated: 2" in md

    def test_empty_scorecard(self) -> None:
        """Scorecard with no dimensions or failures."""
        scorecard = {
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "score": 0,
                "score_percent": 0,
                "normalized_score": 0,
                "decision": "FAIL",
            },
            "dimensions": [],
            "critical_failures": [],
            "thresholds": {},
            "metadata": {},
        }
        md = generate_scorecard_md(scorecard)
        assert "# Gitleaks Evaluation Scorecard" in md
        # No dimensions section when empty
        assert "## Dimensions" not in md
        assert "## Critical Failures" not in md


# ---------------------------------------------------------------------------
# print_report
# ---------------------------------------------------------------------------
class TestPrintReport:
    """Tests for print_report console output."""

    def test_print_report_no_crash(self, capsys) -> None:
        """print_report should not crash and should produce output."""
        report = EvaluationReport(repository="test-repo")
        report.add_result(
            CheckResult(check_id="T-1", category="Accuracy", passed=True, message="ok")
        )
        report.add_result(
            CheckResult(check_id="T-2", category="Detection", passed=False, message="miss")
        )

        print_report(report)

        captured = capsys.readouterr()
        assert "test-repo" in captured.out
        assert "Accuracy" in captured.out
        assert "Detection" in captured.out
        assert "PASS" in captured.out
        assert "FAIL" in captured.out
        assert "2" in captured.out  # total checks

    def test_print_report_empty(self, capsys) -> None:
        """Empty report with no results."""
        report = EvaluationReport(repository="empty-repo")
        print_report(report)
        captured = capsys.readouterr()
        assert "empty-repo" in captured.out
