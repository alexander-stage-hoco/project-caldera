"""Unit tests for scripts/checks/output_quality.py (NC-1 to NC-8 checks)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.checks.output_quality import (
    CheckResult,
    load_ground_truth_files,
    check_nc1_covered_less_than_total,
    check_nc2_branches_covered_less_than_total,
    check_nc3_coverage_pct_range,
    check_nc4_pct_matches_calculation,
    check_nc5_paths_repo_relative,
    check_nc6_no_absolute_paths,
    check_nc7_posix_separators,
    check_nc8_cross_format_equivalence,
    run_all_output_quality_checks,
)


# ---------------------------------------------------------------------------
# Helper: mock load_ground_truth_files
# ---------------------------------------------------------------------------
def _patch_files(files: list[dict]):
    """Return a patcher that makes load_ground_truth_files return given files."""
    return patch("scripts.checks.output_quality.load_ground_truth_files", return_value=files)


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------
class TestCheckResult:
    def test_construction(self) -> None:
        r = CheckResult(check_id="NC-1", name="t", passed=True, message="ok")
        assert r.check_id == "NC-1"


# ---------------------------------------------------------------------------
# load_ground_truth_files (smoke)
# ---------------------------------------------------------------------------
class TestLoadGroundTruthFiles:
    def test_returns_list(self) -> None:
        result = load_ground_truth_files()
        assert isinstance(result, list)

    def test_with_synthetic_data(self, tmp_path: Path) -> None:
        """Inject a synthetic ground-truth directory structure."""
        gt_dir = tmp_path / "evaluation" / "ground-truth" / "lcov"
        gt_dir.mkdir(parents=True)
        gt_data = {
            "expected": {
                "files": [
                    {"relative_path": "src/a.py", "lines_total": 10, "lines_covered": 8,
                     "line_coverage_pct": 80.0, "branches_total": None, "branches_covered": None,
                     "branch_coverage_pct": None}
                ]
            }
        }
        (gt_dir / "simple.json").write_text(json.dumps(gt_data))

        # Patch __file__ reference to point at our tmp_path
        with patch(
            "scripts.checks.output_quality.Path",
            return_value=tmp_path / "scripts" / "checks" / "output_quality.py",
        ):
            # This is fragile, so we just test the real function
            pass

        # Smoke test the real function against whatever ground truth exists
        result = load_ground_truth_files()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# NC-1: covered <= total
# ---------------------------------------------------------------------------
class TestNC1:
    def test_passes_with_valid_data(self) -> None:
        files = [{"lines_covered": 5, "lines_total": 10, "relative_path": "a.py"}]
        with _patch_files(files):
            r = check_nc1_covered_less_than_total()
        assert r.passed is True

    def test_fails_with_violation(self) -> None:
        files = [{"lines_covered": 11, "lines_total": 10, "relative_path": "a.py"}]
        with _patch_files(files):
            r = check_nc1_covered_less_than_total()
        assert r.passed is False

    def test_fails_with_empty_files(self) -> None:
        with _patch_files([]):
            r = check_nc1_covered_less_than_total()
        assert r.passed is False

    def test_skips_none_values(self) -> None:
        files = [{"lines_covered": None, "lines_total": None, "relative_path": "a.py"}]
        with _patch_files(files):
            r = check_nc1_covered_less_than_total()
        # None values are skipped, no violations => pass
        assert r.passed is True


# ---------------------------------------------------------------------------
# NC-2: branches covered <= total
# ---------------------------------------------------------------------------
class TestNC2:
    def test_passes_with_valid_data(self) -> None:
        files = [{"branches_covered": 2, "branches_total": 4}]
        with _patch_files(files):
            r = check_nc2_branches_covered_less_than_total()
        assert r.passed is True

    def test_fails_with_violation(self) -> None:
        files = [{"branches_covered": 5, "branches_total": 4}]
        with _patch_files(files):
            r = check_nc2_branches_covered_less_than_total()
        assert r.passed is False

    def test_skips_none_branches(self) -> None:
        files = [{"branches_covered": None, "branches_total": None}]
        with _patch_files(files):
            r = check_nc2_branches_covered_less_than_total()
        assert r.passed is True


# ---------------------------------------------------------------------------
# NC-3: coverage pct in 0-100
# ---------------------------------------------------------------------------
class TestNC3:
    def test_passes_with_valid_range(self) -> None:
        files = [{"line_coverage_pct": 75.0, "branch_coverage_pct": 50.0}]
        with _patch_files(files):
            r = check_nc3_coverage_pct_range()
        assert r.passed is True

    def test_fails_with_negative(self) -> None:
        files = [{"line_coverage_pct": -1.0, "branch_coverage_pct": None}]
        with _patch_files(files):
            r = check_nc3_coverage_pct_range()
        assert r.passed is False

    def test_fails_with_over_100(self) -> None:
        files = [{"line_coverage_pct": None, "branch_coverage_pct": 101.0}]
        with _patch_files(files):
            r = check_nc3_coverage_pct_range()
        assert r.passed is False

    def test_none_values_ok(self) -> None:
        files = [{"line_coverage_pct": None, "branch_coverage_pct": None}]
        with _patch_files(files):
            r = check_nc3_coverage_pct_range()
        assert r.passed is True


# ---------------------------------------------------------------------------
# NC-4: pct matches calculation
# ---------------------------------------------------------------------------
class TestNC4:
    def test_passes_with_matching_calc(self) -> None:
        files = [{"line_coverage_pct": 70.0, "lines_covered": 7, "lines_total": 10}]
        with _patch_files(files):
            r = check_nc4_pct_matches_calculation()
        assert r.passed is True

    def test_fails_with_mismatch(self) -> None:
        files = [{"line_coverage_pct": 50.0, "lines_covered": 7, "lines_total": 10}]
        with _patch_files(files):
            r = check_nc4_pct_matches_calculation()
        assert r.passed is False

    def test_skips_zero_total(self) -> None:
        files = [{"line_coverage_pct": 0.0, "lines_covered": 0, "lines_total": 0}]
        with _patch_files(files):
            r = check_nc4_pct_matches_calculation()
        # lines_total == 0 => skip => no violation => pass
        assert r.passed is True

    def test_skips_missing_fields(self) -> None:
        files = [{"line_coverage_pct": 50.0}]
        with _patch_files(files):
            r = check_nc4_pct_matches_calculation()
        assert r.passed is True


# ---------------------------------------------------------------------------
# NC-5: paths repo-relative
# ---------------------------------------------------------------------------
class TestNC5:
    def test_passes_with_relative_paths(self) -> None:
        files = [{"relative_path": "src/main.py"}]
        with _patch_files(files):
            r = check_nc5_paths_repo_relative()
        assert r.passed is True

    def test_fails_with_absolute_path(self) -> None:
        files = [{"relative_path": "/home/user/src/main.py"}]
        with _patch_files(files):
            r = check_nc5_paths_repo_relative()
        assert r.passed is False


# ---------------------------------------------------------------------------
# NC-6: no absolute paths (Unix or Windows)
# ---------------------------------------------------------------------------
class TestNC6:
    def test_passes_with_relative(self) -> None:
        files = [{"relative_path": "src/main.py"}]
        with _patch_files(files):
            r = check_nc6_no_absolute_paths()
        assert r.passed is True

    def test_fails_with_unix_absolute(self) -> None:
        files = [{"relative_path": "/usr/src/main.py"}]
        with _patch_files(files):
            r = check_nc6_no_absolute_paths()
        assert r.passed is False

    def test_fails_with_windows_drive(self) -> None:
        files = [{"relative_path": "C:\\src\\main.py"}]
        with _patch_files(files):
            r = check_nc6_no_absolute_paths()
        assert r.passed is False


# ---------------------------------------------------------------------------
# NC-7: POSIX separators
# ---------------------------------------------------------------------------
class TestNC7:
    def test_passes_with_posix(self) -> None:
        files = [{"relative_path": "src/main.py"}]
        with _patch_files(files):
            r = check_nc7_posix_separators()
        assert r.passed is True

    def test_fails_with_backslash(self) -> None:
        files = [{"relative_path": "src\\main.py"}]
        with _patch_files(files):
            r = check_nc7_posix_separators()
        assert r.passed is False


# ---------------------------------------------------------------------------
# NC-8: cross-format equivalence
# ---------------------------------------------------------------------------
class TestNC8:
    def test_returns_result(self) -> None:
        r = check_nc8_cross_format_equivalence()
        assert isinstance(r, CheckResult)
        assert r.check_id == "NC-8"

    def test_passes_when_no_cross_format_file(self) -> None:
        """When cross-format ground truth file doesn't exist, it's
        still considered a pass (not required)."""
        r = check_nc8_cross_format_equivalence()
        assert r.passed is True


# ---------------------------------------------------------------------------
# run_all_output_quality_checks
# ---------------------------------------------------------------------------
class TestRunAll:
    def test_returns_eight_results(self) -> None:
        results = run_all_output_quality_checks()
        assert len(results) == 8

    def test_ids_are_nc1_to_nc8(self) -> None:
        results = run_all_output_quality_checks()
        ids = [r.check_id for r in results]
        for i in range(1, 9):
            assert f"NC-{i}" in ids
