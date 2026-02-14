"""Unit tests for scripts.checks.coverage — CV-1 through CV-8."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.checks.coverage import run_coverage_checks
from scripts.checks import CheckCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _full_metrics() -> dict:
    """A repo with every metric populated."""
    return {
        "blob_count": 100,
        "blob_total_size": 500000,
        "max_blob_size": 50000,
        "tree_count": 200,
        "tree_total_size": 80000,
        "tree_total_entries": 1000,
        "max_tree_entries": 50,
        "commit_count": 300,
        "commit_total_size": 60000,
        "max_commit_size": 2000,
        "max_history_depth": 300,
        "reference_count": 15,
        "branch_count": 5,
        "tag_count": 3,
        "max_path_depth": 8,
        "max_path_length": 120,
        "expanded_tree_count": 250,
        "expanded_blob_count": 180,
        "expanded_blob_size": 400000,
    }


def _repo(name: str, metrics: dict | None = None, **extra) -> dict:
    base: dict = {
        "repository": name,
        "metrics": metrics if metrics is not None else _full_metrics(),
        "health_grade": "A",
        "violations": [],
    }
    base.update(extra)
    return base


def _analysis(repos: list[dict]) -> dict:
    return {"repositories": repos}


# ---------------------------------------------------------------------------
# Tests — empty repos edge case
# ---------------------------------------------------------------------------

class TestNoRepos:
    def test_empty_repos_returns_8_failing_checks(self):
        results = run_coverage_checks(_analysis([]))
        assert len(results) == 8
        for r in results:
            assert r.passed is False
            assert r.score == 0.0
            assert r.category == CheckCategory.COVERAGE


# ---------------------------------------------------------------------------
# Tests — full coverage
# ---------------------------------------------------------------------------

class TestFullCoverage:
    """All metrics populated -> all checks should pass."""

    def test_all_pass_with_full_metrics(self):
        results = run_coverage_checks(_analysis([_repo("r1"), _repo("r2")]))
        for r in results:
            assert r.passed is True, f"{r.check_id} failed: {r.message}"
            assert r.score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Individual check tests
# ---------------------------------------------------------------------------

class TestCV1BlobMetrics:
    def test_pass_when_all_present(self):
        results = run_coverage_checks(_analysis([_repo("r1")]))
        cv1 = [r for r in results if r.check_id == "CV-1"][0]
        assert cv1.passed is True

    def test_fail_when_missing(self):
        repo = _repo("r1", metrics={"blob_count": 1})  # missing blob_total_size, max_blob_size
        results = run_coverage_checks(_analysis([repo]))
        cv1 = [r for r in results if r.check_id == "CV-1"][0]
        assert cv1.score == pytest.approx(1.0 / 3.0)
        assert cv1.passed is False


class TestCV2TreeMetrics:
    def test_pass_when_all_present(self):
        results = run_coverage_checks(_analysis([_repo("r1")]))
        cv2 = [r for r in results if r.check_id == "CV-2"][0]
        assert cv2.passed is True

    def test_partial_coverage(self):
        repo = _repo("r1", metrics={"tree_count": 1, "tree_total_size": 2})
        results = run_coverage_checks(_analysis([repo]))
        cv2 = [r for r in results if r.check_id == "CV-2"][0]
        assert cv2.score == pytest.approx(2.0 / 4.0)


class TestCV3CommitMetrics:
    def test_pass_when_all_present(self):
        results = run_coverage_checks(_analysis([_repo("r1")]))
        cv3 = [r for r in results if r.check_id == "CV-3"][0]
        assert cv3.passed is True


class TestCV4ReferenceMetrics:
    def test_pass_when_all_present(self):
        results = run_coverage_checks(_analysis([_repo("r1")]))
        cv4 = [r for r in results if r.check_id == "CV-4"][0]
        assert cv4.passed is True


class TestCV5PathMetrics:
    def test_pass_when_all_present(self):
        results = run_coverage_checks(_analysis([_repo("r1")]))
        cv5 = [r for r in results if r.check_id == "CV-5"][0]
        assert cv5.passed is True


class TestCV6ExpandedMetrics:
    def test_pass_when_all_present(self):
        results = run_coverage_checks(_analysis([_repo("r1")]))
        cv6 = [r for r in results if r.check_id == "CV-6"][0]
        assert cv6.passed is True

    def test_fail_when_missing(self):
        repo = _repo("r1", metrics={})
        results = run_coverage_checks(_analysis([repo]))
        cv6 = [r for r in results if r.check_id == "CV-6"][0]
        assert cv6.passed is False
        assert cv6.score == 0.0


class TestCV7HealthGrade:
    def test_pass_when_grade_present(self):
        results = run_coverage_checks(_analysis([_repo("r1")]))
        cv7 = [r for r in results if r.check_id == "CV-7"][0]
        assert cv7.passed is True

    def test_fail_when_no_grade(self):
        repo = _repo("r1")
        repo["health_grade"] = ""  # Falsy but present
        results = run_coverage_checks(_analysis([repo]))
        cv7 = [r for r in results if r.check_id == "CV-7"][0]
        assert cv7.passed is False


class TestCV8ViolationDetails:
    def test_pass_with_complete_violations(self):
        repo = _repo("r1", violations=[{"metric": "m", "level": 1}])
        results = run_coverage_checks(_analysis([repo]))
        cv8 = [r for r in results if r.check_id == "CV-8"][0]
        assert cv8.passed is True
        assert cv8.score == 1.0

    def test_pass_with_no_violations(self):
        """No violations to check => passes by default."""
        repo = _repo("r1", violations=[])
        results = run_coverage_checks(_analysis([repo]))
        cv8 = [r for r in results if r.check_id == "CV-8"][0]
        assert cv8.passed is True
        assert cv8.score == 1.0

    def test_fail_with_incomplete_violations(self):
        repo = _repo("r1", violations=[{"metric": "m"}])  # missing 'level'
        results = run_coverage_checks(_analysis([repo]))
        cv8 = [r for r in results if r.check_id == "CV-8"][0]
        assert cv8.passed is False
        assert cv8.score == 0.0
