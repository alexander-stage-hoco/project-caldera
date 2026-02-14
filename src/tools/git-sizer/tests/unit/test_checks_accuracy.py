"""Unit tests for scripts.checks.accuracy — AC-1 through AC-8."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.checks.accuracy import run_accuracy_checks
from scripts.checks import CheckCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_analysis(repos: list[dict]) -> dict:
    """Build a minimal analysis dict compatible with run_accuracy_checks."""
    return {"repositories": repos}


def _repo(name: str, **overrides) -> dict:
    """Build a single repo entry."""
    base: dict = {"repository": name, "metrics": {}, "violations": [], "health_grade": "A", "lfs_candidates": []}
    base.update(overrides)
    return base


def _run(analysis: dict, tmp_path: Path) -> list:
    """Run accuracy checks with an empty ground-truth directory."""
    gt_dir = tmp_path / "gt"
    gt_dir.mkdir(exist_ok=True)
    return run_accuracy_checks(analysis, str(gt_dir))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAC1LargeBlobDetection:
    def test_detected_above_threshold(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("bloated", metrics={"max_blob_size": 10 * 1024 * 1024}),
        ])
        results = _run(analysis, tmp_path)
        ac1 = [r for r in results if r.check_id == "AC-1"][0]
        assert ac1.passed is True
        assert ac1.score == pytest.approx(1.0)

    def test_below_threshold(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("bloated", metrics={"max_blob_size": 1 * 1024 * 1024}),
        ])
        results = _run(analysis, tmp_path)
        ac1 = [r for r in results if r.check_id == "AC-1"][0]
        assert ac1.passed is False

    def test_missing_bloated_repo(self, tmp_path: Path):
        analysis = _build_analysis([_repo("healthy")])
        results = _run(analysis, tmp_path)
        ac1 = [r for r in results if r.check_id == "AC-1"][0]
        assert ac1.passed is False
        assert ac1.score == 0.0


class TestAC2TotalBlobSize:
    def test_above_threshold(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("bloated", metrics={"blob_total_size": 22 * 1024 * 1024}),
        ])
        results = _run(analysis, tmp_path)
        ac2 = [r for r in results if r.check_id == "AC-2"][0]
        assert ac2.passed is True

    def test_below_threshold(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("bloated", metrics={"blob_total_size": 5 * 1024 * 1024}),
        ])
        results = _run(analysis, tmp_path)
        ac2 = [r for r in results if r.check_id == "AC-2"][0]
        assert ac2.passed is False


class TestAC3CommitCount:
    def test_exact_match(self, tmp_path: Path):
        analysis = _build_analysis([_repo("deep-history", metrics={"commit_count": 501})])
        results = _run(analysis, tmp_path)
        ac3 = [r for r in results if r.check_id == "AC-3"][0]
        assert ac3.passed is True
        assert ac3.score == 1.0

    def test_out_of_range(self, tmp_path: Path):
        analysis = _build_analysis([_repo("deep-history", metrics={"commit_count": 200})])
        results = _run(analysis, tmp_path)
        ac3 = [r for r in results if r.check_id == "AC-3"][0]
        assert ac3.passed is False

    def test_missing_repo(self, tmp_path: Path):
        results = _run(_build_analysis([]), tmp_path)
        ac3 = [r for r in results if r.check_id == "AC-3"][0]
        assert ac3.passed is False
        assert ac3.score == 0.0


class TestAC4TreeEntries:
    def test_sufficient_entries(self, tmp_path: Path):
        analysis = _build_analysis([_repo("wide-tree", metrics={"max_tree_entries": 1000})])
        results = _run(analysis, tmp_path)
        ac4 = [r for r in results if r.check_id == "AC-4"][0]
        assert ac4.passed is True

    def test_insufficient_entries(self, tmp_path: Path):
        analysis = _build_analysis([_repo("wide-tree", metrics={"max_tree_entries": 500})])
        results = _run(analysis, tmp_path)
        ac4 = [r for r in results if r.check_id == "AC-4"][0]
        assert ac4.passed is False


class TestAC5PathDepth:
    def test_deep_path(self, tmp_path: Path):
        analysis = _build_analysis([_repo("wide-tree", metrics={"max_path_depth": 20})])
        results = _run(analysis, tmp_path)
        ac5 = [r for r in results if r.check_id == "AC-5"][0]
        assert ac5.passed is True

    def test_shallow_path(self, tmp_path: Path):
        analysis = _build_analysis([_repo("wide-tree", metrics={"max_path_depth": 5})])
        results = _run(analysis, tmp_path)
        ac5 = [r for r in results if r.check_id == "AC-5"][0]
        assert ac5.passed is False


class TestAC6HealthGrade:
    def test_correct_grades(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("healthy", health_grade="A"),
            _repo("bloated", health_grade="D"),
            _repo("wide-tree", health_grade="C"),
        ])
        results = _run(analysis, tmp_path)
        ac6 = [r for r in results if r.check_id == "AC-6"][0]
        assert ac6.passed is True
        assert ac6.score == pytest.approx(1.0)

    def test_incorrect_grades(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("healthy", health_grade="F"),
            _repo("bloated", health_grade="A"),
        ])
        results = _run(analysis, tmp_path)
        ac6 = [r for r in results if r.check_id == "AC-6"][0]
        assert ac6.passed is False
        assert ac6.score == 0.0

    def test_no_repos(self, tmp_path: Path):
        results = _run(_build_analysis([]), tmp_path)
        ac6 = [r for r in results if r.check_id == "AC-6"][0]
        assert ac6.passed is False
        assert ac6.score == 0.0


class TestAC7LFSCandidates:
    def test_has_candidates(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("bloated", lfs_candidates=["large.bin", "huge.dat"]),
        ])
        results = _run(analysis, tmp_path)
        ac7 = [r for r in results if r.check_id == "AC-7"][0]
        assert ac7.passed is True
        assert ac7.score == 1.0

    def test_no_candidates(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("bloated", lfs_candidates=[]),
        ])
        results = _run(analysis, tmp_path)
        ac7 = [r for r in results if r.check_id == "AC-7"][0]
        assert ac7.passed is False

    def test_missing_bloated(self, tmp_path: Path):
        results = _run(_build_analysis([_repo("healthy")]), tmp_path)
        ac7 = [r for r in results if r.check_id == "AC-7"][0]
        assert ac7.passed is False


class TestAC8ThresholdViolations:
    def test_all_correct(self, tmp_path: Path):
        analysis = _build_analysis([
            _repo("bloated", violations=[{"m": 1}]),
            _repo("wide-tree", violations=[{"m": 1}, {"m": 2}]),
            _repo("healthy", violations=[]),
            _repo("deep-history", violations=[]),
        ])
        results = _run(analysis, tmp_path)
        ac8 = [r for r in results if r.check_id == "AC-8"][0]
        assert ac8.passed is True
        assert ac8.score == 1.0

    def test_no_repos_found(self, tmp_path: Path):
        results = _run(_build_analysis([_repo("other")]), tmp_path)
        ac8 = [r for r in results if r.check_id == "AC-8"][0]
        assert ac8.score == 0.0


class TestAllChecksReturned:
    def test_always_returns_8_checks(self, tmp_path: Path):
        results = _run(_build_analysis([]), tmp_path)
        assert len(results) == 8
        ids = {r.check_id for r in results}
        for i in range(1, 9):
            assert f"AC-{i}" in ids

    def test_all_are_accuracy_category(self, tmp_path: Path):
        results = _run(_build_analysis([]), tmp_path)
        for r in results:
            assert r.category == CheckCategory.ACCURACY
