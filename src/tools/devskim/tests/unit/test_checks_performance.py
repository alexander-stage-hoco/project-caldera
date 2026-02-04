"""Unit tests for performance checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.performance import run_performance_checks
from checks import CheckCategory


class TestPerformanceChecks:
    """Tests for run_performance_checks function."""

    def test_all_performance_checks_returned(self) -> None:
        """All performance checks should be returned."""
        analysis = {
            "files": [],
            "summary": {"total_files": 10, "total_lines": 500},
            "metadata": {"analysis_duration_ms": 1000, "run_id": "test-123"}
        }
        results = run_performance_checks(analysis)

        # Should have at least 4 performance checks
        assert len(results) >= 4
        for r in results:
            assert r.category == CheckCategory.PERFORMANCE

    def test_pf1_execution_time(self) -> None:
        """PF-1: Execution time check."""
        analysis = {
            "metadata": {"analysis_duration_ms": 500, "run_id": "test-123"},
            "summary": {"total_files": 10, "total_lines": 500},
            "files": [{"path": f"file{i}.cs"} for i in range(10)],
            "directories": []
        }
        results = run_performance_checks(analysis)

        pf1 = next((r for r in results if r.check_id == "PF-1"), None)
        assert pf1 is not None
        assert pf1.category == CheckCategory.PERFORMANCE
        # Fast execution should pass
        assert pf1.passed is True

    def test_pf2_files_per_second(self) -> None:
        """PF-2: Files per second throughput."""
        analysis = {
            "metadata": {"analysis_duration_ms": 1000, "run_id": "test-123"},
            "summary": {"total_files": 20, "total_lines": 1000},
            "files": [{"path": f"file{i}.cs"} for i in range(20)],
            "directories": []
        }
        results = run_performance_checks(analysis)

        pf2 = next((r for r in results if r.check_id == "PF-2"), None)
        assert pf2 is not None
        assert pf2.category == CheckCategory.PERFORMANCE

    def test_pf3_memory_efficiency(self) -> None:
        """PF-3: Lines per second throughput check (not memory efficiency)."""
        analysis = {
            "metadata": {"analysis_duration_ms": 1000, "run_id": "test-123"},
            "summary": {"total_files": 10, "total_lines": 5000},
            "files": [],
            "directories": []
        }
        results = run_performance_checks(analysis)

        pf3 = next((r for r in results if r.check_id == "PF-3"), None)
        assert pf3 is not None
        assert pf3.category == CheckCategory.PERFORMANCE

    def test_pf4_startup_time(self) -> None:
        """PF-4: Result completeness check (not startup time)."""
        analysis = {
            "metadata": {"analysis_duration_ms": 500, "run_id": "test-123"},
            "summary": {"total_files": 5, "total_lines": 200},
            "files": [],
            "directories": [],
            "statistics": {}
        }
        results = run_performance_checks(analysis)

        pf4 = next((r for r in results if r.check_id == "PF-4"), None)
        assert pf4 is not None
        assert pf4.category == CheckCategory.PERFORMANCE

    def test_slow_execution_fails(self) -> None:
        """Slow execution should fail performance check."""
        analysis = {
            "metadata": {"analysis_duration_ms": 300000},  # 5 minutes
            "summary": {"total_files": 1, "total_lines": 100},
            "files": [{"path": "single.cs"}]
        }
        results = run_performance_checks(analysis)

        pf1 = next((r for r in results if r.check_id == "PF-1"), None)
        assert pf1 is not None
        assert pf1.score < 1.0  # Should have reduced score

    def test_missing_metadata_handles_gracefully(self) -> None:
        """Missing metadata should not raise errors."""
        analysis = {"files": [], "summary": {}}
        results = run_performance_checks(analysis)

        # Should still return results
        assert len(results) >= 4
        for r in results:
            assert r.category == CheckCategory.PERFORMANCE

    def test_performance_check_scores_in_range(self) -> None:
        """All performance scores should be between 0 and 1."""
        analysis = {
            "metadata": {"analysis_duration_ms": 1000, "run_id": "test-123"},
            "summary": {"total_files": 10, "total_lines": 500},
            "files": [{"path": f"file{i}.cs"} for i in range(10)]
        }
        results = run_performance_checks(analysis)

        for r in results:
            assert 0.0 <= r.score <= 1.0
