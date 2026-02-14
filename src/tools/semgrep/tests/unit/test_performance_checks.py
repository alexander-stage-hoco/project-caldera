"""Tests for performance checks (PF-1 to PF-4) in scripts/checks/performance.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.performance import run_performance_checks
from checks import CheckCategory


def _analysis(duration_ms: int = 5000, total_files: int = 10, total_lines: int = 1000) -> dict:
    """Build a minimal analysis dict with timing and size metadata."""
    return {
        "metadata": {"analysis_duration_ms": duration_ms},
        "summary": {"total_files": total_files, "total_lines": total_lines},
    }


class TestPF1SyntheticSpeed:
    """PF-1: Overall analysis speed < 45s."""

    def test_fast_analysis_passes(self):
        results = run_performance_checks(_analysis(duration_ms=2000))
        pf1 = next(r for r in results if r.check_id == "PF-1")
        assert pf1.passed is True
        assert pf1.category == CheckCategory.PERFORMANCE

    def test_slow_analysis_fails(self):
        results = run_performance_checks(_analysis(duration_ms=60000))
        pf1 = next(r for r in results if r.check_id == "PF-1")
        assert pf1.passed is False

    def test_zero_duration(self):
        results = run_performance_checks(_analysis(duration_ms=0))
        pf1 = next(r for r in results if r.check_id == "PF-1")
        assert pf1.passed is True


class TestPF2PerFileEfficiency:
    """PF-2: Per-file analysis < 1000ms."""

    def test_efficient(self):
        # 5000ms / 10 files = 500ms/file => passes
        results = run_performance_checks(_analysis(duration_ms=5000, total_files=10))
        pf2 = next(r for r in results if r.check_id == "PF-2")
        assert pf2.passed is True

    def test_inefficient(self):
        # 20000ms / 2 files = 10000ms/file => fails
        results = run_performance_checks(_analysis(duration_ms=20000, total_files=2))
        pf2 = next(r for r in results if r.check_id == "PF-2")
        assert pf2.passed is False


class TestPF3Throughput:
    """PF-3: Lines per second >= 100."""

    def test_good_throughput(self):
        # 1000 lines in 1s = 1000 LOC/s
        results = run_performance_checks(_analysis(duration_ms=1000, total_lines=1000))
        pf3 = next(r for r in results if r.check_id == "PF-3")
        assert pf3.passed is True

    def test_low_throughput(self):
        # 10 lines in 10s = 1 LOC/s
        results = run_performance_checks(_analysis(duration_ms=10000, total_lines=10))
        pf3 = next(r for r in results if r.check_id == "PF-3")
        assert pf3.passed is False


class TestPF4StartupOverhead:
    """PF-4: Startup ratio < 90%."""

    def test_low_startup(self):
        # 10 files, 5s total: startup_estimate = 5 - 10*0.1 = 4s, ratio = 0.8 < 0.9
        results = run_performance_checks(_analysis(duration_ms=5000, total_files=10))
        pf4 = next(r for r in results if r.check_id == "PF-4")
        assert pf4.passed is True

    def test_high_startup(self):
        # 1 file, 10s total: startup_estimate = 10 - 0.1 = 9.9, ratio = 0.99 >= 0.9
        results = run_performance_checks(_analysis(duration_ms=10000, total_files=1))
        pf4 = next(r for r in results if r.check_id == "PF-4")
        assert pf4.passed is False

    def test_zero_files(self):
        results = run_performance_checks(_analysis(duration_ms=1000, total_files=0))
        pf4 = next(r for r in results if r.check_id == "PF-4")
        assert pf4.passed is True
        assert pf4.score == 0.5


class TestRunPerformanceChecks:
    def test_returns_four_checks(self):
        results = run_performance_checks(_analysis())
        assert len(results) == 4
        ids = [r.check_id for r in results]
        assert ids == ["PF-1", "PF-2", "PF-3", "PF-4"]

    def test_all_pass_for_fast_small_analysis(self):
        results = run_performance_checks(_analysis(duration_ms=1000, total_files=100, total_lines=5000))
        assert all(r.passed for r in results)

    def test_score_capped_at_one(self):
        # Very fast => score should still be <= 1.0
        results = run_performance_checks(_analysis(duration_ms=100, total_files=50, total_lines=10000))
        for r in results:
            assert r.score <= 1.0
