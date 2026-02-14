"""Unit tests for evaluate.py: CheckResult, check runners, scoring, and main."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.evaluate import (
    CheckResult,
    run_parser_accuracy_checks,
    run_normalization_checks,
    run_format_coverage_checks,
    run_edge_case_checks,
    run_performance_checks,
)


# ---------------------------------------------------------------------------
# CheckResult dataclass
# ---------------------------------------------------------------------------
class TestCheckResult:
    def test_basic_construction(self) -> None:
        r = CheckResult(check_id="PA-1", name="test", passed=True, message="ok")
        assert r.check_id == "PA-1"
        assert r.passed is True
        assert r.weight == 1.0

    def test_weight_override(self) -> None:
        r = CheckResult(check_id="X", name="x", passed=False, message="m", weight=0.5)
        assert r.weight == 0.5


# ---------------------------------------------------------------------------
# run_parser_accuracy_checks (PA-1 to PA-12)
# ---------------------------------------------------------------------------
class TestRunParserAccuracyChecks:
    def test_returns_twelve_results(self) -> None:
        results = run_parser_accuracy_checks()
        assert len(results) == 12
        ids = [r.check_id for r in results]
        for i in range(1, 13):
            assert f"PA-{i}" in ids

    def test_all_checks_have_check_id_and_name(self) -> None:
        for r in run_parser_accuracy_checks():
            assert r.check_id
            assert r.name

    def test_pa1_lcov_line_counts_pass(self) -> None:
        results = run_parser_accuracy_checks()
        pa1 = next(r for r in results if r.check_id == "PA-1")
        assert pa1.passed is True

    def test_pa2_lcov_branch_counts_pass(self) -> None:
        results = run_parser_accuracy_checks()
        pa2 = next(r for r in results if r.check_id == "PA-2")
        assert pa2.passed is True

    def test_pa3_lcov_coverage_pct_pass(self) -> None:
        results = run_parser_accuracy_checks()
        pa3 = next(r for r in results if r.check_id == "PA-3")
        assert pa3.passed is True

    def test_pa4_cobertura_line_rates_pass(self) -> None:
        results = run_parser_accuracy_checks()
        pa4 = next(r for r in results if r.check_id == "PA-4")
        assert pa4.passed is True

    def test_pa5_cobertura_branch_pass(self) -> None:
        results = run_parser_accuracy_checks()
        pa5 = next(r for r in results if r.check_id == "PA-5")
        assert pa5.passed is True

    def test_pa6_cobertura_coverage_pct_pass(self) -> None:
        results = run_parser_accuracy_checks()
        pa6 = next(r for r in results if r.check_id == "PA-6")
        assert pa6.passed is True

    def test_pa7_to_pa9_jacoco_pass(self) -> None:
        results = run_parser_accuracy_checks()
        for i in range(7, 10):
            r = next(r for r in results if r.check_id == f"PA-{i}")
            assert r.passed is True, f"PA-{i} failed: {r.message}"

    def test_pa10_to_pa12_istanbul_pass(self) -> None:
        results = run_parser_accuracy_checks()
        for i in range(10, 13):
            r = next(r for r in results if r.check_id == f"PA-{i}")
            assert r.passed is True, f"PA-{i} failed: {r.message}"


# ---------------------------------------------------------------------------
# run_normalization_checks (NC-1 to NC-8)
# ---------------------------------------------------------------------------
class TestRunNormalizationChecks:
    def test_returns_eight_results(self) -> None:
        results = run_normalization_checks()
        assert len(results) == 8

    def test_all_pass(self) -> None:
        results = run_normalization_checks()
        for r in results:
            assert r.passed is True, f"{r.check_id} failed: {r.message}"

    def test_nc1_covered_le_total(self) -> None:
        results = run_normalization_checks()
        nc1 = next(r for r in results if r.check_id == "NC-1")
        assert nc1.passed is True

    def test_nc5_paths_repo_relative(self) -> None:
        results = run_normalization_checks()
        nc5 = next(r for r in results if r.check_id == "NC-5")
        assert nc5.passed is True

    def test_nc7_posix_separators(self) -> None:
        results = run_normalization_checks()
        nc7 = next(r for r in results if r.check_id == "NC-7")
        assert nc7.passed is True


# ---------------------------------------------------------------------------
# run_format_coverage_checks (FC-1 to FC-6)
# ---------------------------------------------------------------------------
class TestRunFormatCoverageChecks:
    def test_returns_six_results(self) -> None:
        results = run_format_coverage_checks()
        assert len(results) == 6

    def test_all_pass(self) -> None:
        results = run_format_coverage_checks()
        for r in results:
            assert r.passed is True, f"{r.check_id} failed: {r.message}"

    def test_fc1_lcov_detection(self) -> None:
        results = run_format_coverage_checks()
        fc1 = next(r for r in results if r.check_id == "FC-1")
        assert fc1.passed is True

    def test_fc6_invalid_format(self) -> None:
        results = run_format_coverage_checks()
        fc6 = next(r for r in results if r.check_id == "FC-6")
        assert fc6.passed is True


# ---------------------------------------------------------------------------
# run_edge_case_checks (EC-1 to EC-8)
# ---------------------------------------------------------------------------
class TestRunEdgeCaseChecks:
    def test_returns_eight_results(self) -> None:
        results = run_edge_case_checks()
        assert len(results) == 8

    def test_ec1_empty_file(self) -> None:
        results = run_edge_case_checks()
        ec1 = next(r for r in results if r.check_id == "EC-1")
        assert ec1.passed is True

    def test_ec2_zero_coverage(self) -> None:
        results = run_edge_case_checks()
        ec2 = next(r for r in results if r.check_id == "EC-2")
        assert ec2.passed is True

    def test_ec3_full_coverage(self) -> None:
        results = run_edge_case_checks()
        ec3 = next(r for r in results if r.check_id == "EC-3")
        assert ec3.passed is True

    def test_ec4_unicode_paths(self) -> None:
        results = run_edge_case_checks()
        ec4 = next(r for r in results if r.check_id == "EC-4")
        assert ec4.passed is True

    def test_ec5_deep_paths(self) -> None:
        results = run_edge_case_checks()
        ec5 = next(r for r in results if r.check_id == "EC-5")
        assert ec5.passed is True

    def test_ec6_special_chars(self) -> None:
        results = run_edge_case_checks()
        ec6 = next(r for r in results if r.check_id == "EC-6")
        assert ec6.passed is True

    def test_ec7_malformed_xml(self) -> None:
        results = run_edge_case_checks()
        ec7 = next(r for r in results if r.check_id == "EC-7")
        assert ec7.passed is True

    def test_ec8_required_fields(self) -> None:
        results = run_edge_case_checks()
        ec8 = next(r for r in results if r.check_id == "EC-8")
        assert ec8.passed is True

    def test_all_pass(self) -> None:
        results = run_edge_case_checks()
        for r in results:
            assert r.passed is True, f"{r.check_id} failed: {r.message}"


# ---------------------------------------------------------------------------
# run_performance_checks (PF-1 to PF-4)
# ---------------------------------------------------------------------------
class TestRunPerformanceChecks:
    def test_returns_four_results(self) -> None:
        results = run_performance_checks()
        assert len(results) == 4

    def test_pf1_small_file_timing(self) -> None:
        results = run_performance_checks()
        pf1 = next(r for r in results if r.check_id == "PF-1")
        assert pf1.passed is True

    def test_pf2_medium_file_timing(self) -> None:
        results = run_performance_checks()
        pf2 = next(r for r in results if r.check_id == "PF-2")
        assert pf2.passed is True

    def test_all_pass(self) -> None:
        results = run_performance_checks()
        for r in results:
            assert r.passed is True, f"{r.check_id} failed: {r.message}"


# ---------------------------------------------------------------------------
# evaluate.main
# ---------------------------------------------------------------------------
class TestEvaluateMain:
    def test_main_writes_scorecard_and_json(self, tmp_path: Path) -> None:
        """main() should write scorecard.md and JSON result files."""
        with patch.dict("os.environ", {"EVAL_OUTPUT_DIR": str(tmp_path)}):
            from scripts.evaluate import main
            main()

        assert (tmp_path / "scorecard.md").exists()
        assert (tmp_path / "evaluation_results.json").exists()
        assert (tmp_path / "evaluation_report.json").exists()

        # Verify JSON structure
        data = json.loads((tmp_path / "evaluation_results.json").read_text())
        assert "score" in data
        assert "decision" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)
        assert data["total"] > 0

    def test_main_decision_logic(self, tmp_path: Path) -> None:
        """All built-in checks should pass, yielding STRONG_PASS."""
        with patch.dict("os.environ", {"EVAL_OUTPUT_DIR": str(tmp_path)}):
            from scripts.evaluate import main
            main()

        data = json.loads((tmp_path / "evaluation_results.json").read_text())
        # All parser checks pass so score should be high
        assert data["score"] >= 90.0
        assert data["decision"] in ("STRONG_PASS", "PASS")

    def test_main_scorecard_contains_headings(self, tmp_path: Path) -> None:
        with patch.dict("os.environ", {"EVAL_OUTPUT_DIR": str(tmp_path)}):
            from scripts.evaluate import main
            main()

        content = (tmp_path / "scorecard.md").read_text()
        assert "# coverage-ingest Evaluation Scorecard" in content
        assert "**Score:**" in content
        assert "**Decision:**" in content
