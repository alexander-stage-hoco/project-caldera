"""Extended tests for scripts/evaluate.py - run_all_checks and main function."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from scripts.checks import CheckResult, DimensionResult, EvaluationResult
from scripts.evaluate import (
    run_scc_analysis,
    run_envelope_analysis,
    run_all_checks,
    generate_scorecard,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_check(check_id="OQ-1", name="Test Check", passed=True, message="OK"):
    return CheckResult(
        check_id=check_id,
        name=name,
        passed=passed,
        message=message,
    )


def _make_dim_result(dimension="output_quality", score=4, checks_passed=7, checks_total=8, weight=0.15):
    checks = [_make_check(f"{dimension[:2].upper()}-{i+1}", passed=(i < checks_passed))
              for i in range(checks_total)]
    return DimensionResult(
        dimension=dimension,
        weight=weight,
        score=score,
        weighted_score=score * weight,
        checks=checks,
    )


# ---------------------------------------------------------------------------
# Tests: run_scc_analysis
# ---------------------------------------------------------------------------

class TestRunSccAnalysis:
    @patch("scripts.evaluate.subprocess.run")
    def test_successful_run(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"Name": "Python", "Code": 100}]',
            stderr=""
        )
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        exit_code, stderr = run_scc_analysis(tmp_path, results_dir)
        assert exit_code == 0
        assert stderr == ""
        assert (results_dir / "raw_scc_output.json").exists()

    @patch("scripts.evaluate.subprocess.run")
    def test_failed_run(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="binary not found"
        )
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        exit_code, stderr = run_scc_analysis(tmp_path, results_dir)
        assert exit_code == 1
        assert "binary not found" in stderr


# ---------------------------------------------------------------------------
# Tests: run_all_checks
# ---------------------------------------------------------------------------

class TestRunAllChecks:
    @patch("scripts.evaluate.run_cocomo_checks")
    @patch("scripts.evaluate.run_directory_analysis_checks")
    @patch("scripts.evaluate.run_per_file_checks")
    @patch("scripts.evaluate.run_license_checks")
    @patch("scripts.evaluate.run_coverage_checks")
    @patch("scripts.evaluate.run_installation_checks")
    @patch("scripts.evaluate.run_performance_checks")
    @patch("scripts.evaluate.run_reliability_checks")
    @patch("scripts.evaluate.run_integration_fit_checks")
    @patch("scripts.evaluate.run_output_quality_checks")
    @patch("scripts.evaluate.run_envelope_analysis")
    @patch("scripts.evaluate.run_scc_analysis")
    def test_returns_10_dimensions(
        self,
        mock_scc,
        mock_envelope,
        mock_oq,
        mock_if,
        mock_rl,
        mock_pf,
        mock_in,
        mock_cv,
        mock_cl,
        mock_pfr,
        mock_da,
        mock_co,
        tmp_path,
    ):
        # Setup mock return values
        mock_scc.return_value = (0, "")
        mock_envelope.return_value = None

        # Each check runner returns a list of CheckResults
        checks = [_make_check()]
        mock_oq.return_value = checks
        mock_if.return_value = checks
        mock_rl.return_value = checks
        mock_pf.return_value = checks
        mock_in.return_value = checks
        mock_cv.return_value = checks
        mock_cl.return_value = checks
        mock_pfr.return_value = checks
        mock_da.return_value = checks
        mock_co.return_value = checks

        # Create necessary dirs
        results_dir = tmp_path / "evaluation" / "results"
        results_dir.mkdir(parents=True)

        dimensions = run_all_checks(tmp_path)
        assert len(dimensions) == 10
        assert all(isinstance(d, DimensionResult) for d in dimensions)

    @patch("scripts.evaluate.run_cocomo_checks")
    @patch("scripts.evaluate.run_directory_analysis_checks")
    @patch("scripts.evaluate.run_per_file_checks")
    @patch("scripts.evaluate.run_license_checks")
    @patch("scripts.evaluate.run_coverage_checks")
    @patch("scripts.evaluate.run_installation_checks")
    @patch("scripts.evaluate.run_performance_checks")
    @patch("scripts.evaluate.run_reliability_checks")
    @patch("scripts.evaluate.run_integration_fit_checks")
    @patch("scripts.evaluate.run_output_quality_checks")
    @patch("scripts.evaluate.run_envelope_analysis")
    @patch("scripts.evaluate.run_scc_analysis")
    def test_uses_existing_directory_analysis(
        self,
        mock_scc,
        mock_envelope,
        mock_oq,
        mock_if,
        mock_rl,
        mock_pf,
        mock_in,
        mock_cv,
        mock_cl,
        mock_pfr,
        mock_da,
        mock_co,
        tmp_path,
    ):
        mock_scc.return_value = (0, "")
        mock_envelope.return_value = None

        checks = [_make_check()]
        for m in [mock_oq, mock_if, mock_rl, mock_pf, mock_in, mock_cv, mock_cl, mock_pfr, mock_da, mock_co]:
            m.return_value = checks

        results_dir = tmp_path / "evaluation" / "results"
        results_dir.mkdir(parents=True)
        # Create a directory_analysis.json so it gets loaded
        da_data = {"directories": [], "files": [], "summary": {"total_files": 0}}
        (results_dir / "directory_analysis.json").write_text(json.dumps(da_data))

        dimensions = run_all_checks(tmp_path)
        assert len(dimensions) == 10


# ---------------------------------------------------------------------------
# Tests: generate_scorecard with full result
# ---------------------------------------------------------------------------

class TestGenerateScorecardFull:
    def test_strong_pass_message(self):
        dimensions = [
            _make_dim_result("output_quality", 5, 8, 8, 0.15),
            _make_dim_result("integration_fit", 5, 6, 6, 0.15),
        ]
        result = EvaluationResult(
            run_id="test-001",
            timestamp="2026-01-15T00:00:00Z",
            dimensions=dimensions,
            total_score=4.5,
            decision="STRONG_PASS",
            summary={"total_checks": 14, "passed_checks": 14, "dimensions_count": 2},
        )
        content = generate_scorecard(result)
        assert "STRONG_PASS" in content
        assert "approved" in content

    def test_weak_pass_message(self):
        dimensions = [_make_dim_result("output_quality", 3, 5, 8, 0.15)]
        result = EvaluationResult(
            run_id="test-002",
            timestamp="2026-01-15T00:00:00Z",
            dimensions=dimensions,
            total_score=3.1,
            decision="WEAK_PASS",
            summary={"total_checks": 8, "passed_checks": 5, "dimensions_count": 1},
        )
        content = generate_scorecard(result)
        assert "WEAK_PASS" in content
        assert "reservations" in content

    def test_fail_message(self):
        dimensions = [_make_dim_result("output_quality", 2, 3, 8, 0.15)]
        result = EvaluationResult(
            run_id="test-003",
            timestamp="2026-01-15T00:00:00Z",
            dimensions=dimensions,
            total_score=2.0,
            decision="FAIL",
            summary={"total_checks": 8, "passed_checks": 3, "dimensions_count": 1},
        )
        content = generate_scorecard(result)
        assert "FAIL" in content
        assert "does not meet" in content

    def test_contains_dimension_sections(self):
        dimensions = [
            _make_dim_result("output_quality", 4, 7, 8, 0.15),
            _make_dim_result("reliability", 5, 5, 5, 0.10),
        ]
        result = EvaluationResult(
            run_id="test-004",
            timestamp="2026-01-15T00:00:00Z",
            dimensions=dimensions,
            total_score=4.2,
            decision="STRONG_PASS",
            summary={},
        )
        content = generate_scorecard(result)
        assert "Output Quality" in content
        assert "Reliability" in content
        assert "Weighted:" in content
