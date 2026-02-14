"""Unit tests for scripts.checks.edge_cases — EC-1 through EC-8."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.checks.edge_cases import run_edge_case_checks
from scripts.checks import CheckCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo(name: str, **overrides) -> dict:
    base: dict = {
        "repository": name,
        "metrics": {},
        "violations": [],
        "health_grade": "A",
        "tool": "git-sizer",
        "raw_output": {"some": "data"},
    }
    base.update(overrides)
    return base


def _analysis(repos: list[dict]) -> dict:
    return {"repositories": repos}


# ---------------------------------------------------------------------------
# EC-1: Minimal repo handling
# ---------------------------------------------------------------------------

class TestEC1MinimalRepo:
    def test_pass_when_healthy_has_commits(self):
        repo = _repo("healthy", metrics={"commit_count": 5})
        results = run_edge_case_checks(_analysis([repo]))
        ec1 = [r for r in results if r.check_id == "EC-1"][0]
        assert ec1.passed is True
        assert ec1.score == 1.0

    def test_fail_when_healthy_missing(self):
        results = run_edge_case_checks(_analysis([_repo("other")]))
        ec1 = [r for r in results if r.check_id == "EC-1"][0]
        assert ec1.passed is False

    def test_fail_when_zero_commits(self):
        repo = _repo("healthy", metrics={"commit_count": 0})
        results = run_edge_case_checks(_analysis([repo]))
        ec1 = [r for r in results if r.check_id == "EC-1"][0]
        assert ec1.passed is False


# ---------------------------------------------------------------------------
# EC-2: Large history handling
# ---------------------------------------------------------------------------

class TestEC2LargeHistory:
    def test_pass_with_many_commits(self):
        repo = _repo("deep-history", metrics={"commit_count": 501})
        results = run_edge_case_checks(_analysis([repo]))
        ec2 = [r for r in results if r.check_id == "EC-2"][0]
        assert ec2.passed is True

    def test_fail_with_few_commits(self):
        repo = _repo("deep-history", metrics={"commit_count": 100})
        results = run_edge_case_checks(_analysis([repo]))
        ec2 = [r for r in results if r.check_id == "EC-2"][0]
        assert ec2.passed is False


# ---------------------------------------------------------------------------
# EC-3: Wide tree handling
# ---------------------------------------------------------------------------

class TestEC3WideTree:
    def test_pass_with_many_entries(self):
        repo = _repo("wide-tree", metrics={"max_tree_entries": 1000})
        results = run_edge_case_checks(_analysis([repo]))
        ec3 = [r for r in results if r.check_id == "EC-3"][0]
        assert ec3.passed is True

    def test_fail_with_few_entries(self):
        repo = _repo("wide-tree", metrics={"max_tree_entries": 100})
        results = run_edge_case_checks(_analysis([repo]))
        ec3 = [r for r in results if r.check_id == "EC-3"][0]
        assert ec3.passed is False


# ---------------------------------------------------------------------------
# EC-4: Deep path handling
# ---------------------------------------------------------------------------

class TestEC4DeepPath:
    def test_pass_with_deep_path(self):
        repo = _repo("wide-tree", metrics={"max_path_depth": 15})
        results = run_edge_case_checks(_analysis([repo]))
        ec4 = [r for r in results if r.check_id == "EC-4"][0]
        assert ec4.passed is True

    def test_fail_with_shallow_path(self):
        repo = _repo("wide-tree", metrics={"max_path_depth": 5})
        results = run_edge_case_checks(_analysis([repo]))
        ec4 = [r for r in results if r.check_id == "EC-4"][0]
        assert ec4.passed is False


# ---------------------------------------------------------------------------
# EC-5: No violations case
# ---------------------------------------------------------------------------

class TestEC5NoViolations:
    def test_pass_when_healthy_has_no_violations(self):
        repo = _repo("healthy", violations=[])
        results = run_edge_case_checks(_analysis([repo]))
        ec5 = [r for r in results if r.check_id == "EC-5"][0]
        assert ec5.passed is True

    def test_fail_when_healthy_has_violations(self):
        repo = _repo("healthy", violations=[{"metric": "x", "level": 1}])
        results = run_edge_case_checks(_analysis([repo]))
        ec5 = [r for r in results if r.check_id == "EC-5"][0]
        assert ec5.passed is False


# ---------------------------------------------------------------------------
# EC-6: Multiple violations case
# ---------------------------------------------------------------------------

class TestEC6MultipleViolations:
    def test_pass_when_wide_tree_has_multiple(self):
        repo = _repo("wide-tree", violations=[{"m": 1}, {"m": 2}])
        results = run_edge_case_checks(_analysis([repo]))
        ec6 = [r for r in results if r.check_id == "EC-6"][0]
        assert ec6.passed is True

    def test_fail_when_wide_tree_has_single(self):
        repo = _repo("wide-tree", violations=[{"m": 1}])
        results = run_edge_case_checks(_analysis([repo]))
        ec6 = [r for r in results if r.check_id == "EC-6"][0]
        assert ec6.passed is False


# ---------------------------------------------------------------------------
# EC-7: JSON output validity
# ---------------------------------------------------------------------------

class TestEC7JSONValidity:
    def test_pass_when_all_repos_have_required_fields(self):
        repo = _repo("r1", tool="git-sizer", health_grade="A", metrics={"x": 1})
        results = run_edge_case_checks(_analysis([repo]))
        ec7 = [r for r in results if r.check_id == "EC-7"][0]
        assert ec7.passed is True
        assert ec7.score == 1.0

    def test_fail_when_fields_missing(self):
        repo = {"repository": "r1"}  # no tool, health_grade, or metrics
        results = run_edge_case_checks(_analysis([repo]))
        ec7 = [r for r in results if r.check_id == "EC-7"][0]
        assert ec7.passed is False
        assert ec7.score == 0.0


# ---------------------------------------------------------------------------
# EC-8: Raw output preservation
# ---------------------------------------------------------------------------

class TestEC8RawOutput:
    def test_pass_when_raw_present(self):
        repo = _repo("r1", raw_output={"data": "value"})
        results = run_edge_case_checks(_analysis([repo]))
        ec8 = [r for r in results if r.check_id == "EC-8"][0]
        assert ec8.passed is True

    def test_fail_when_raw_missing(self):
        repo = _repo("r1")
        repo.pop("raw_output", None)
        results = run_edge_case_checks(_analysis([repo]))
        ec8 = [r for r in results if r.check_id == "EC-8"][0]
        assert ec8.passed is False

    def test_fail_when_raw_empty(self):
        repo = _repo("r1", raw_output={})
        results = run_edge_case_checks(_analysis([repo]))
        ec8 = [r for r in results if r.check_id == "EC-8"][0]
        assert ec8.passed is False


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------

class TestStructure:
    def test_always_returns_8_checks(self):
        results = run_edge_case_checks(_analysis([]))
        assert len(results) == 8
        ids = {r.check_id for r in results}
        for i in range(1, 9):
            assert f"EC-{i}" in ids

    def test_all_are_edge_case_category(self):
        results = run_edge_case_checks(_analysis([_repo("healthy")]))
        for r in results:
            assert r.category == CheckCategory.EDGE_CASES
