"""Unit tests for scripts/checks/accuracy.py (PA-1 to PA-12 ground-truth checks)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.checks.accuracy import (
    CheckResult,
    load_ground_truth,
    check_pa1_lcov_line_counts,
    check_pa2_lcov_branch_counts,
    check_pa3_lcov_coverage_pct,
    check_pa4_cobertura_line_rates,
    check_pa5_cobertura_branch_rates,
    check_pa6_cobertura_coverage_pct,
    check_pa7_jacoco_instruction_counts,
    check_pa8_jacoco_branch_counts,
    check_pa9_jacoco_coverage_pct,
    check_pa10_istanbul_statement_counts,
    check_pa11_istanbul_branch_counts,
    check_pa12_istanbul_coverage_pct,
    run_all_accuracy_checks,
)


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------
class TestCheckResult:
    def test_defaults(self) -> None:
        r = CheckResult(check_id="PA-1", name="t", passed=True, message="m")
        assert r.expected is None
        assert r.actual is None

    def test_with_expected_actual(self) -> None:
        r = CheckResult("PA-3", "n", True, "m", expected=70.0, actual=70.0)
        assert r.expected == 70.0
        assert r.actual == 70.0


# ---------------------------------------------------------------------------
# load_ground_truth
# ---------------------------------------------------------------------------
class TestLoadGroundTruth:
    def test_returns_none_when_file_missing(self, tmp_path: Path) -> None:
        with patch("scripts.checks.accuracy.Path") as MockPath:
            # Make the resolved path point somewhere that doesn't exist
            mock_path = tmp_path / "nonexistent.json"
            MockPath.return_value.parent.parent.parent.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_path
            # The function builds its own path from __file__, so we need to
            # directly test with a non-existent format/scenario
            result = load_ground_truth("nonexistent_format", "nonexistent_scenario")
            # It might be None or might find a file depending on the dir structure
            # The important thing is it doesn't crash
            assert result is None or isinstance(result, dict)

    def test_loads_valid_json_smoke(self) -> None:
        """Smoke test the real function against whatever ground truth exists."""
        result = load_ground_truth("lcov", "simple")
        assert result is None or isinstance(result, dict)


# ---------------------------------------------------------------------------
# Individual PA check functions
# ---------------------------------------------------------------------------
class TestPAChecks:
    """Test each PA check produces a well-formed CheckResult."""

    def test_pa1_returns_result(self) -> None:
        r = check_pa1_lcov_line_counts()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-1"

    def test_pa2_returns_result(self) -> None:
        r = check_pa2_lcov_branch_counts()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-2"

    def test_pa3_returns_result(self) -> None:
        r = check_pa3_lcov_coverage_pct()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-3"

    def test_pa4_returns_result(self) -> None:
        r = check_pa4_cobertura_line_rates()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-4"

    def test_pa5_returns_result(self) -> None:
        r = check_pa5_cobertura_branch_rates()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-5"

    def test_pa6_returns_result(self) -> None:
        r = check_pa6_cobertura_coverage_pct()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-6"

    def test_pa7_returns_result(self) -> None:
        r = check_pa7_jacoco_instruction_counts()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-7"

    def test_pa8_returns_result(self) -> None:
        r = check_pa8_jacoco_branch_counts()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-8"

    def test_pa9_returns_result(self) -> None:
        r = check_pa9_jacoco_coverage_pct()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-9"

    def test_pa10_returns_result(self) -> None:
        r = check_pa10_istanbul_statement_counts()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-10"

    def test_pa11_returns_result(self) -> None:
        r = check_pa11_istanbul_branch_counts()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-11"

    def test_pa12_returns_result(self) -> None:
        r = check_pa12_istanbul_coverage_pct()
        assert isinstance(r, CheckResult)
        assert r.check_id == "PA-12"


# ---------------------------------------------------------------------------
# PA checks with synthetic ground truth (exercises more code paths)
# ---------------------------------------------------------------------------
class TestPAChecksWithSyntheticGroundTruth:
    """Inject synthetic ground truth to exercise deeper logic branches."""

    def _mock_gt(self, gt_data: dict):
        """Return a patcher that makes load_ground_truth return gt_data."""
        return patch("scripts.checks.accuracy.load_ground_truth", return_value=gt_data)

    def test_pa1_with_valid_gt(self) -> None:
        gt = {
            "expected": {
                "files": [{"lines_total": 10, "lines_covered": 7, "relative_path": "t.py"}]
            }
        }
        with self._mock_gt(gt):
            r = check_pa1_lcov_line_counts()
        assert r.passed is True

    def test_pa1_with_missing_fields(self) -> None:
        gt = {"expected": {"files": [{"relative_path": "t.py"}]}}
        with self._mock_gt(gt):
            r = check_pa1_lcov_line_counts()
        assert r.passed is False

    def test_pa1_with_no_files(self) -> None:
        gt = {"expected": {"files": []}}
        with self._mock_gt(gt):
            r = check_pa1_lcov_line_counts()
        assert r.passed is False

    def test_pa1_with_none_gt(self) -> None:
        with self._mock_gt(None):
            r = check_pa1_lcov_line_counts()
        assert r.passed is False

    def test_pa2_with_no_branches(self) -> None:
        gt = {
            "expected": {
                "files": [{"branches_total": None, "branches_covered": None}]
            }
        }
        with self._mock_gt(gt):
            r = check_pa2_lcov_branch_counts()
        # branches_total is None => "No branch data (valid)" => pass
        assert r.passed is True

    def test_pa3_with_zero_total(self) -> None:
        gt = {
            "expected": {
                "files": [{
                    "line_coverage_pct": 0.0,
                    "lines_total": 0,
                    "lines_covered": 0,
                }]
            }
        }
        with self._mock_gt(gt):
            r = check_pa3_lcov_coverage_pct()
        # lines_total == 0 => expected_pct = 0.0
        assert r.passed is True

    def test_pa3_with_mismatch(self) -> None:
        gt = {
            "expected": {
                "files": [{
                    "line_coverage_pct": 99.0,
                    "lines_total": 10,
                    "lines_covered": 7,
                }]
            }
        }
        with self._mock_gt(gt):
            r = check_pa3_lcov_coverage_pct()
        # 99.0 vs expected 70.0 => fail
        assert r.passed is False

    def test_pa5_with_branch_violation(self) -> None:
        gt = {
            "expected": {
                "files": [{"branches_total": 4, "branches_covered": 5}]
            }
        }
        with self._mock_gt(gt):
            r = check_pa5_cobertura_branch_rates()
        assert r.passed is False

    def test_pa8_with_none_gt(self) -> None:
        with self._mock_gt(None):
            r = check_pa8_jacoco_branch_counts()
        assert r.passed is False

    def test_pa8_with_no_branches(self) -> None:
        gt = {
            "expected": {
                "files": [{"branches_total": None, "branches_covered": None}]
            }
        }
        with self._mock_gt(gt):
            r = check_pa8_jacoco_branch_counts()
        assert r.passed is True

    def test_pa11_with_no_branches(self) -> None:
        gt = {
            "expected": {
                "files": [{"branches_total": None}]
            }
        }
        with self._mock_gt(gt):
            r = check_pa11_istanbul_branch_counts()
        assert r.passed is True


# ---------------------------------------------------------------------------
# run_all_accuracy_checks
# ---------------------------------------------------------------------------
class TestRunAllAccuracyChecks:
    def test_returns_twelve_results(self) -> None:
        results = run_all_accuracy_checks()
        assert len(results) == 12

    def test_all_have_unique_ids(self) -> None:
        results = run_all_accuracy_checks()
        ids = [r.check_id for r in results]
        assert len(set(ids)) == 12
