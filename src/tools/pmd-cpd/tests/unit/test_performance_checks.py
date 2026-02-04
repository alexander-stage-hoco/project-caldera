"""Unit tests for performance checks (PF-1 to PF-4)."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckCategory
from checks.performance import (
    run_performance_checks,
    _pf1_execution_time,
    _pf2_file_throughput,
    _pf3_memory_efficiency,
    _pf4_incremental_analysis_potential,
)


@pytest.fixture
def fast_analysis():
    """Analysis that completed quickly."""
    return {
        "metadata": {
            "version": "1.0",
            "elapsed_seconds": 10.0,
            "repo_path": "/path/to/repo",
            "analyzed_at": "2025-01-20T10:00:00Z",
        },
        "summary": {"total_files": 50},
        "files": [{"path": f"file{i}.py"} for i in range(50)],
        "duplications": [
            {"clone_id": f"CPD-{i:04d}", "occurrences": [{"file": "a.py"}, {"file": "b.py"}]}
            for i in range(10)
        ],
    }


@pytest.fixture
def slow_analysis():
    """Analysis that took a long time."""
    return {
        "metadata": {
            "version": "1.0",
            "elapsed_seconds": 400.0,
        },
        "summary": {"total_files": 100},
        "files": [{"path": f"file{i}.py"} for i in range(100)],
        "duplications": [],
    }


@pytest.fixture
def very_slow_analysis():
    """Analysis that exceeded acceptable threshold."""
    return {
        "metadata": {
            "version": "1.0",
            "elapsed_seconds": 600.0,
        },
        "summary": {"total_files": 50},
        "files": [{"path": f"file{i}.py"} for i in range(50)],
        "duplications": [],
    }


@pytest.fixture
def high_throughput_analysis():
    """Analysis with high file throughput."""
    return {
        "metadata": {
            "version": "1.0",
            "elapsed_seconds": 5.0,
        },
        "summary": {"total_files": 100},
        "files": [{"path": f"file{i}.py"} for i in range(100)],
        "duplications": [],
    }


@pytest.fixture
def low_throughput_analysis():
    """Analysis with low file throughput."""
    return {
        "metadata": {
            "version": "1.0",
            "elapsed_seconds": 200.0,
        },
        "summary": {"total_files": 50},
        "files": [{"path": f"file{i}.py"} for i in range(50)],
        "duplications": [],
    }


class TestPF1ExecutionTime:
    """Tests for PF-1: Execution time."""

    def test_excellent_execution_time(self, fast_analysis):
        """Test excellent execution time (< 30s)."""
        result = _pf1_execution_time(fast_analysis)

        assert result.check_id == "PF-1"
        assert result.name == "Execution time"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.passed is True
        assert result.score == 1.0
        assert "excellent" in result.message.lower()

    def test_good_execution_time(self):
        """Test good execution time (30s - 120s)."""
        analysis = {"metadata": {"elapsed_seconds": 60.0}}
        result = _pf1_execution_time(analysis)

        assert result.passed is True
        assert result.score == 0.8
        assert "good" in result.message.lower()

    def test_acceptable_execution_time(self):
        """Test acceptable execution time (120s - 300s)."""
        analysis = {"metadata": {"elapsed_seconds": 200.0}}
        result = _pf1_execution_time(analysis)

        assert result.passed is True
        assert result.score == 0.6
        assert "acceptable" in result.message.lower()

    def test_slow_execution_time(self, very_slow_analysis):
        """Test slow execution time (> 300s)."""
        result = _pf1_execution_time(very_slow_analysis)

        assert result.passed is False
        assert result.score == 0.3
        assert "slow" in result.message.lower()

    def test_missing_elapsed_time(self):
        """Test when elapsed time is missing."""
        analysis = {"metadata": {}}
        result = _pf1_execution_time(analysis)

        # Default 0 seconds is excellent
        assert result.passed is True
        assert result.score == 1.0

    def test_evidence_includes_thresholds(self, fast_analysis):
        """Test that evidence includes thresholds."""
        result = _pf1_execution_time(fast_analysis)

        assert "thresholds" in result.evidence
        assert "excellent" in result.evidence["thresholds"]
        assert "good" in result.evidence["thresholds"]
        assert "acceptable" in result.evidence["thresholds"]


class TestPF2FileThroughput:
    """Tests for PF-2: File throughput."""

    def test_excellent_throughput(self, high_throughput_analysis):
        """Test excellent throughput (> 10 files/sec)."""
        result = _pf2_file_throughput(high_throughput_analysis)

        assert result.check_id == "PF-2"
        assert result.name == "File throughput"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.passed is True
        assert result.score == 1.0
        assert "excellent" in result.message.lower()

    def test_good_throughput(self):
        """Test good throughput (5-10 files/sec)."""
        analysis = {
            "metadata": {"elapsed_seconds": 15.0},
            "summary": {"total_files": 100},
            "files": [{}] * 100,  # ~6.67 files/sec
        }
        result = _pf2_file_throughput(analysis)

        assert result.passed is True
        assert result.score == 0.8
        assert "good" in result.message.lower()

    def test_acceptable_throughput(self):
        """Test acceptable throughput (1-5 files/sec)."""
        analysis = {
            "metadata": {"elapsed_seconds": 50.0},
            "summary": {"total_files": 100},
            "files": [{}] * 100,  # 2 files/sec
        }
        result = _pf2_file_throughput(analysis)

        assert result.passed is True
        assert result.score == 0.6
        assert "acceptable" in result.message.lower()

    def test_slow_throughput(self, low_throughput_analysis):
        """Test slow throughput (< 1 file/sec)."""
        result = _pf2_file_throughput(low_throughput_analysis)

        # 50 files / 200s = 0.25 files/sec
        assert result.passed is False
        assert result.score == 0.3
        assert "slow" in result.message.lower()

    def test_no_files(self):
        """Test with no files analyzed."""
        analysis = {
            "metadata": {"elapsed_seconds": 10.0},
            "summary": {"total_files": 0},
            "files": [],
        }
        result = _pf2_file_throughput(analysis)

        assert result.passed is True
        assert result.score == 1.0

    def test_zero_elapsed_time(self):
        """Test with zero elapsed time."""
        analysis = {
            "metadata": {"elapsed_seconds": 0.0},
            "summary": {"total_files": 10},
        }
        result = _pf2_file_throughput(analysis)

        assert result.passed is True

    def test_evidence_includes_stats(self, high_throughput_analysis):
        """Test that evidence includes statistics."""
        result = _pf2_file_throughput(high_throughput_analysis)

        assert "total_files" in result.evidence
        assert "elapsed_seconds" in result.evidence
        assert "files_per_second" in result.evidence


class TestPF3MemoryEfficiency:
    """Tests for PF-3: Memory efficiency."""

    def test_efficient_representation(self, fast_analysis):
        """Test efficient clone representation."""
        result = _pf3_memory_efficiency(fast_analysis)

        assert result.check_id == "PF-3"
        assert result.name == "Memory efficiency"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.passed is True
        assert result.score == 1.0

    def test_reasonable_representation(self):
        """Test reasonable clone representation (3-5 avg occurrences)."""
        analysis = {
            "files": [{"path": f"file{i}.py"} for i in range(10)],
            "duplications": [
                {"clone_id": "CPD-0001", "occurrences": [{}] * 4},  # 4 occurrences
            ],
        }
        result = _pf3_memory_efficiency(analysis)

        assert result.passed is True
        assert result.score == 0.8

    def test_high_occurrence_count(self):
        """Test high occurrence count (> 5 avg)."""
        analysis = {
            "files": [{"path": f"file{i}.py"} for i in range(10)],
            "duplications": [
                {"clone_id": "CPD-0001", "occurrences": [{}] * 10},  # 10 occurrences
            ],
        }
        result = _pf3_memory_efficiency(analysis)

        assert result.passed is True  # Still passes but lower score
        assert result.score == 0.6

    def test_no_files(self):
        """Test with no files analyzed."""
        analysis = {"files": [], "duplications": []}
        result = _pf3_memory_efficiency(analysis)

        assert result.passed is True
        assert result.score == 1.0

    def test_no_duplications(self):
        """Test with no duplications."""
        analysis = {
            "files": [{"path": "test.py"}],
            "duplications": [],
        }
        result = _pf3_memory_efficiency(analysis)

        # No clones = efficient
        assert result.passed is True
        assert result.score == 1.0

    def test_evidence_includes_stats(self, fast_analysis):
        """Test that evidence includes statistics."""
        result = _pf3_memory_efficiency(fast_analysis)

        assert "total_clones" in result.evidence
        assert "total_occurrences" in result.evidence
        assert "avg_occurrences_per_clone" in result.evidence


class TestPF4IncrementalAnalysisPotential:
    """Tests for PF-4: Incremental analysis support."""

    def test_all_metadata_present(self, fast_analysis):
        """Test when all required metadata is present."""
        result = _pf4_incremental_analysis_potential(fast_analysis)

        assert result.check_id == "PF-4"
        assert result.name == "Incremental analysis support"
        assert result.category == CheckCategory.PERFORMANCE
        assert result.passed is True
        assert result.score == 1.0

    def test_partial_metadata(self):
        """Test when only some metadata is present."""
        analysis = {
            "metadata": {
                "version": "1.0",
                "repo_path": "/path/to/repo",
                # Missing analyzed_at
            },
        }
        result = _pf4_incremental_analysis_potential(analysis)

        # 2/3 = 0.666... which is below 0.67 threshold, so passes is False
        assert result.passed is False
        assert result.score == pytest.approx(0.67, rel=0.01)

    def test_missing_all_metadata(self):
        """Test when all incremental metadata is missing."""
        analysis = {"metadata": {}}
        result = _pf4_incremental_analysis_potential(analysis)

        assert result.passed is False
        assert result.score == 0.0
        assert "missing" in result.message.lower()

    def test_evidence_includes_checks(self, fast_analysis):
        """Test that evidence includes metadata checks."""
        result = _pf4_incremental_analysis_potential(fast_analysis)

        assert "has_repo_path" in result.evidence
        assert "has_timestamp" in result.evidence
        assert "has_version" in result.evidence


class TestRunPerformanceChecks:
    """Tests for the run_performance_checks aggregator function."""

    def test_runs_all_checks(self, fast_analysis, tmp_path):
        """Test that all 4 performance checks are run."""
        # Create mock ground truth dir (not used by performance checks)
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()

        results = run_performance_checks(fast_analysis, str(gt_dir))

        assert len(results) == 4
        check_ids = [r.check_id for r in results]
        assert "PF-1" in check_ids
        assert "PF-2" in check_ids
        assert "PF-3" in check_ids
        assert "PF-4" in check_ids

    def test_all_checks_have_correct_category(self, fast_analysis, tmp_path):
        """Test that all checks are categorized as PERFORMANCE."""
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()

        results = run_performance_checks(fast_analysis, str(gt_dir))

        for result in results:
            assert result.category == CheckCategory.PERFORMANCE

    def test_all_checks_pass_for_fast_analysis(self, fast_analysis, tmp_path):
        """Test that all checks pass for a fast, well-structured analysis."""
        gt_dir = tmp_path / "ground-truth"
        gt_dir.mkdir()

        results = run_performance_checks(fast_analysis, str(gt_dir))

        for result in results:
            assert result.passed is True, f"Check {result.check_id} failed: {result.message}"
