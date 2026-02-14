"""
Tests for performance checks (PF-1 to PF-4).

Tests cover:
- Synthetic analysis speed threshold (PF-1)
- Per-file efficiency calculation (PF-2)
- Throughput LOC/second (PF-3)
- Memory usage estimation (PF-4)
- Edge cases: zero duration, zero files, missing metadata
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.performance import (
    pf1_synthetic_analysis_speed,
    pf2_per_file_efficiency,
    pf3_throughput,
    pf4_memory_usage,
    run_all_performance_checks,
)


def _make_analysis(duration_ms=0, files=None, timestamp=None):
    metadata = {"analysis_duration_ms": duration_ms}
    if timestamp:
        metadata["timestamp"] = timestamp
    return {
        "metadata": metadata,
        "files": files or [],
    }


class TestPF1SyntheticAnalysisSpeed:
    """PF-1: Analysis speed < 30 seconds."""

    def test_fast_analysis_passes(self):
        result = pf1_synthetic_analysis_speed(
            _make_analysis(duration_ms=5000), {}
        )
        assert result.passed is True
        assert result.score > 0
        assert result.check_id == "PF-1"

    def test_slow_analysis_fails(self):
        result = pf1_synthetic_analysis_speed(
            _make_analysis(duration_ms=35000), {}
        )
        assert result.passed is False
        assert result.score == 0

    def test_exactly_at_threshold(self):
        # 30 seconds exactly -> not passed (requires strictly less than)
        result = pf1_synthetic_analysis_speed(
            _make_analysis(duration_ms=30000), {}
        )
        assert result.passed is False

    def test_zero_duration(self):
        result = pf1_synthetic_analysis_speed(
            _make_analysis(duration_ms=0), {}
        )
        assert result.passed is True
        assert result.score == pytest.approx(1.0)


class TestPF2PerFileEfficiency:
    """PF-2: Per-file efficiency < 2000ms average."""

    def test_efficient_analysis(self):
        files = [{"path": f"f{i}.cs"} for i in range(10)]
        result = pf2_per_file_efficiency(
            _make_analysis(duration_ms=10000, files=files), {}
        )
        # 10000ms / 10 files = 1000ms/file < 2000
        assert result.passed is True

    def test_slow_per_file(self):
        files = [{"path": "f1.cs"}]
        result = pf2_per_file_efficiency(
            _make_analysis(duration_ms=5000, files=files), {}
        )
        # 5000ms / 1 file = 5000ms/file >= 2000
        assert result.passed is False

    def test_zero_files(self):
        result = pf2_per_file_efficiency(
            _make_analysis(duration_ms=1000, files=[]), {}
        )
        assert result.passed is False
        assert result.score == 0.0
        assert result.message == "No files analyzed"


class TestPF3Throughput:
    """PF-3: Throughput >= 50 LOC/second."""

    def test_high_throughput(self):
        files = [{"lines_of_code": 1000}]
        result = pf3_throughput(
            _make_analysis(duration_ms=5000, files=files), {}
        )
        # 1000 / 5s = 200 LOC/s >= 50
        assert result.passed is True
        assert result.score == pytest.approx(1.0)  # capped at 1.0

    def test_low_throughput(self):
        files = [{"lines_of_code": 100}]
        result = pf3_throughput(
            _make_analysis(duration_ms=10000, files=files), {}
        )
        # 100 / 10s = 10 LOC/s < 50
        assert result.passed is False
        assert result.score == pytest.approx(10 / 50)

    def test_zero_duration_instant(self):
        result = pf3_throughput(
            _make_analysis(duration_ms=0, files=[{"lines_of_code": 100}]), {}
        )
        assert result.passed is True
        assert result.score == 1.0
        assert "instant" in result.message.lower()

    def test_zero_loc(self):
        files = [{"lines_of_code": 0}]
        result = pf3_throughput(
            _make_analysis(duration_ms=5000, files=files), {}
        )
        # 0 / 5s = 0 LOC/s < 50
        assert result.passed is False


class TestPF4MemoryUsage:
    """PF-4: Memory usage estimation."""

    def test_completed_analysis_passes(self):
        result = pf4_memory_usage(
            _make_analysis(duration_ms=1000, timestamp="2026-01-01T00:00:00Z"), {}
        )
        assert result.passed is True
        assert result.check_id == "PF-4"

    def test_missing_timestamp_fails(self):
        analysis = {"metadata": {}}
        result = pf4_memory_usage(analysis, {})
        assert result.passed is False


class TestRunAllPerformanceChecks:
    """Test run_all_performance_checks returns all 4 checks."""

    def test_returns_4_checks(self):
        analysis = _make_analysis(duration_ms=1000, files=[{"lines_of_code": 100}])
        results = run_all_performance_checks(analysis, {})
        assert len(results) == 4
        check_ids = [r.check_id for r in results]
        assert "PF-1" in check_ids
        assert "PF-2" in check_ids
        assert "PF-3" in check_ids
        assert "PF-4" in check_ids
