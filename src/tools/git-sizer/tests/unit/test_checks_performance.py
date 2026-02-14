"""Unit tests for scripts.checks.performance — PF-1 through PF-4."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.checks.performance import run_performance_checks
from scripts.checks import CheckCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo(name: str, duration_ms: int = 100, **overrides) -> dict:
    base: dict = {
        "repository": name,
        "duration_ms": duration_ms,
        "metrics": {},
        "raw_output": {"some": "data"},
    }
    base.update(overrides)
    return base


def _analysis(repos: list[dict]) -> dict:
    return {"repositories": repos, "summary": {}}


# ---------------------------------------------------------------------------
# PF-1: Total analysis speed
# ---------------------------------------------------------------------------

class TestPF1TotalSpeed:
    def test_pass_when_fast(self):
        repos = [_repo("r1", 500), _repo("r2", 500)]
        results = run_performance_checks(_analysis(repos))
        pf1 = [r for r in results if r.check_id == "PF-1"][0]
        assert pf1.passed is True

    def test_fail_when_slow(self):
        repos = [_repo("r1", 3000), _repo("r2", 3000)]
        results = run_performance_checks(_analysis(repos))
        pf1 = [r for r in results if r.check_id == "PF-1"][0]
        assert pf1.passed is False

    def test_zero_duration(self):
        repos = [_repo("r1", 0)]
        results = run_performance_checks(_analysis(repos))
        pf1 = [r for r in results if r.check_id == "PF-1"][0]
        assert pf1.passed is True


# ---------------------------------------------------------------------------
# PF-2: Per-repo analysis speed
# ---------------------------------------------------------------------------

class TestPF2PerRepoSpeed:
    def test_pass_when_all_fast(self):
        repos = [_repo("r1", 500), _repo("r2", 1000), _repo("r3", 1500)]
        results = run_performance_checks(_analysis(repos))
        pf2 = [r for r in results if r.check_id == "PF-2"][0]
        assert pf2.passed is True
        assert pf2.score == 1.0

    def test_fail_when_too_many_slow(self):
        repos = [_repo("r1", 3000), _repo("r2", 3000), _repo("r3", 3000), _repo("r4", 100)]
        results = run_performance_checks(_analysis(repos))
        pf2 = [r for r in results if r.check_id == "PF-2"][0]
        assert pf2.passed is False

    def test_empty_repos(self):
        results = run_performance_checks(_analysis([]))
        pf2 = [r for r in results if r.check_id == "PF-2"][0]
        assert pf2.score == 0.0


# ---------------------------------------------------------------------------
# PF-3: Large repo handling
# ---------------------------------------------------------------------------

class TestPF3LargeRepo:
    def test_pass_deep_history_fast(self):
        repos = [_repo("deep-history", 5000)]
        results = run_performance_checks(_analysis(repos))
        pf3 = [r for r in results if r.check_id == "PF-3"][0]
        assert pf3.passed is True

    def test_fail_deep_history_slow(self):
        repos = [_repo("deep-history", 60000)]
        results = run_performance_checks(_analysis(repos))
        pf3 = [r for r in results if r.check_id == "PF-3"][0]
        assert pf3.passed is False

    def test_missing_deep_history(self):
        repos = [_repo("healthy", 100)]
        results = run_performance_checks(_analysis(repos))
        pf3 = [r for r in results if r.check_id == "PF-3"][0]
        assert pf3.passed is False
        assert pf3.score == 0.0


# ---------------------------------------------------------------------------
# PF-4: Memory efficiency (output size)
# ---------------------------------------------------------------------------

class TestPF4OutputSize:
    def test_pass_small_output(self):
        repos = [_repo("r1", raw_output={"k": "v"})]
        results = run_performance_checks(_analysis(repos))
        pf4 = [r for r in results if r.check_id == "PF-4"][0]
        assert pf4.passed is True

    def test_fail_large_output(self):
        huge_data = {"data": "x" * 200000}
        repos = [_repo("r1", raw_output=huge_data)]
        results = run_performance_checks(_analysis(repos))
        pf4 = [r for r in results if r.check_id == "PF-4"][0]
        assert pf4.passed is False

    def test_empty_repos_passes(self):
        results = run_performance_checks(_analysis([]))
        pf4 = [r for r in results if r.check_id == "PF-4"][0]
        assert pf4.passed is True  # 0 < 100KB


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------

class TestStructure:
    def test_always_returns_4_checks(self):
        results = run_performance_checks(_analysis([]))
        assert len(results) == 4
        ids = {r.check_id for r in results}
        for i in range(1, 5):
            assert f"PF-{i}" in ids

    def test_all_are_performance_category(self):
        results = run_performance_checks(_analysis([_repo("r1")]))
        for r in results:
            assert r.category == CheckCategory.PERFORMANCE

    def test_skip_long_checks_parameter_accepted(self):
        """Ensure skip_long_checks parameter is accepted (even if unused currently)."""
        results = run_performance_checks(_analysis([_repo("r1")]), skip_long_checks=True)
        assert len(results) == 4
