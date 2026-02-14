"""Tests targeting uncovered paths in evaluate.py for coverage improvement."""

from __future__ import annotations

from scripts.evaluate import determine_decision, generate_scorecard_json, run_evaluation
from scripts.checks import CheckResult, CheckCategory, EvaluationReport


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


class TestGenerateScorecardJson:
    """Tests for scorecard JSON generation with category aggregation."""

    def _make_report(self, checks: list[CheckResult]) -> EvaluationReport:
        return EvaluationReport(
            timestamp="2025-01-01T00:00:00",
            analysis_path="/tmp/analysis.json",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )

    def test_scorecard_structure_with_categories(self) -> None:
        checks = [
            CheckResult(
                check_id="AC-1", name="Clone detection",
                category=CheckCategory.ACCURACY, passed=True,
                score=1.0, message="Found 5/5 clones",
            ),
            CheckResult(
                check_id="CV-1", name="Language coverage",
                category=CheckCategory.COVERAGE, passed=False,
                score=0.5, message="3/6 languages",
            ),
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)

        assert scorecard["tool"] == "pmd-cpd"
        assert scorecard["summary"]["total_checks"] == 2
        assert scorecard["summary"]["passed"] == 1
        assert scorecard["summary"]["failed"] == 1
        assert len(scorecard["dimensions"]) == 2
        assert scorecard["summary"]["decision"] in (
            "STRONG_PASS", "PASS", "WEAK_PASS", "FAIL",
        )

    def test_empty_report(self) -> None:
        report = self._make_report([])
        scorecard = generate_scorecard_json(report)
        assert scorecard["summary"]["total_checks"] == 0
        assert scorecard["dimensions"] == []

    def test_all_passing_checks(self) -> None:
        checks = [
            CheckResult(
                check_id=f"AC-{i}", name=f"Check {i}",
                category=CheckCategory.ACCURACY, passed=True,
                score=1.0, message="OK",
            )
            for i in range(1, 5)
        ]
        report = self._make_report(checks)
        scorecard = generate_scorecard_json(report)
        assert scorecard["summary"]["decision"] == "STRONG_PASS"
        assert scorecard["summary"]["score_percent"] == 100.0


class TestRunEvaluation:
    """Tests for the run_evaluation orchestrator."""

    def test_quick_mode_skips_performance(self, tmp_path) -> None:
        # Create minimal analysis file
        import json
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text(json.dumps({
            "data": {
                "summary": {"total_files": 0, "total_clones": 0},
                "files": [],
                "duplications": [],
                "statistics": {},
                "config": {"min_tokens": 50},
                "elapsed_seconds": 1.0,
            }
        }))

        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()

        report_quick = run_evaluation(str(analysis_file), str(gt_dir), quick=True)
        report_full = run_evaluation(str(analysis_file), str(gt_dir), quick=False)

        # Quick mode should have fewer checks (no performance)
        quick_categories = {c.category.value for c in report_quick.checks}
        full_categories = {c.category.value for c in report_full.checks}
        assert "performance" not in quick_categories
        assert "performance" in full_categories
