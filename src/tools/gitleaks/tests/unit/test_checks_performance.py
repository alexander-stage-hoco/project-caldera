"""Unit tests for performance checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.performance import run_performance_checks


class TestPerformanceChecks:
    """Tests for run_performance_checks function."""

    def test_sp1_scan_time_within_threshold(self) -> None:
        """SP-1: Scan time within threshold passes."""
        analysis = {"results": {"scan_time_ms": 5000}}
        ground_truth = {"thresholds": {"max_scan_time_ms": 10000}}

        results = run_performance_checks(analysis, ground_truth)
        sp1 = next(r for r in results if r.check_id == "SP-1")

        assert sp1.passed is True
        assert sp1.category == "Performance"

    def test_sp1_scan_time_exceeds_threshold(self) -> None:
        """SP-1: Scan time exceeds threshold fails."""
        analysis = {"results": {"scan_time_ms": 15000}}
        ground_truth = {"thresholds": {"max_scan_time_ms": 10000}}

        results = run_performance_checks(analysis, ground_truth)
        sp1 = next(r for r in results if r.check_id == "SP-1")

        assert sp1.passed is False

    def test_sp1_uses_default_threshold(self) -> None:
        """SP-1: Uses default 10000ms threshold if not specified."""
        analysis = {"results": {"scan_time_ms": 5000}}
        ground_truth = {}  # No thresholds specified

        results = run_performance_checks(analysis, ground_truth)
        sp1 = next(r for r in results if r.check_id == "SP-1")

        assert sp1.passed is True

    def test_sp1_default_threshold_exceeded(self) -> None:
        """SP-1: Exceeds default threshold fails."""
        analysis = {"results": {"scan_time_ms": 12000}}
        ground_truth = {}  # Uses default 10000ms

        results = run_performance_checks(analysis, ground_truth)
        sp1 = next(r for r in results if r.check_id == "SP-1")

        assert sp1.passed is False

    def test_sp2_time_per_commit_reasonable(self) -> None:
        """SP-2: Time per commit within threshold passes."""
        analysis = {
            "results": {
                "scan_time_ms": 2000,
                "commits_with_secrets": 4,
            }
        }
        ground_truth = {"thresholds": {"max_ms_per_commit": 1000}}

        results = run_performance_checks(analysis, ground_truth)
        sp2 = next(r for r in results if r.check_id == "SP-2")

        assert sp2.passed is True  # 2000/4 = 500ms per commit

    def test_sp2_time_per_commit_exceeds(self) -> None:
        """SP-2: Time per commit exceeds threshold fails."""
        analysis = {
            "results": {
                "scan_time_ms": 5000,
                "commits_with_secrets": 2,
            }
        }
        ground_truth = {"thresholds": {"max_ms_per_commit": 1000}}

        results = run_performance_checks(analysis, ground_truth)
        sp2 = next(r for r in results if r.check_id == "SP-2")

        assert sp2.passed is False  # 5000/2 = 2500ms per commit

    def test_sp2_no_commits_with_secrets_na(self) -> None:
        """SP-2: No commits with secrets is N/A."""
        analysis = {
            "results": {
                "scan_time_ms": 1000,
                "commits_with_secrets": 0,
            }
        }
        ground_truth = {}

        results = run_performance_checks(analysis, ground_truth)
        sp2 = next(r for r in results if r.check_id == "SP-2")

        assert sp2.passed is True
        assert "N/A" in sp2.message

    def test_sp2_single_commit(self) -> None:
        """SP-2: Single commit calculation."""
        analysis = {
            "results": {
                "scan_time_ms": 800,
                "commits_with_secrets": 1,
            }
        }
        ground_truth = {"thresholds": {"max_ms_per_commit": 1000}}

        results = run_performance_checks(analysis, ground_truth)
        sp2 = next(r for r in results if r.check_id == "SP-2")

        assert sp2.passed is True

    def test_sp3_time_per_finding_reasonable(self) -> None:
        """SP-3: Time per finding within threshold passes."""
        analysis = {
            "results": {
                "scan_time_ms": 1000,
                "total_secrets": 5,
            }
        }
        ground_truth = {"thresholds": {"max_ms_per_finding": 500}}

        results = run_performance_checks(analysis, ground_truth)
        sp3 = next(r for r in results if r.check_id == "SP-3")

        assert sp3.passed is True  # 1000/5 = 200ms per finding

    def test_sp3_time_per_finding_exceeds(self) -> None:
        """SP-3: Time per finding exceeds threshold fails."""
        analysis = {
            "results": {
                "scan_time_ms": 3000,
                "total_secrets": 2,
            }
        }
        ground_truth = {"thresholds": {"max_ms_per_finding": 500}}

        results = run_performance_checks(analysis, ground_truth)
        sp3 = next(r for r in results if r.check_id == "SP-3")

        assert sp3.passed is False  # 3000/2 = 1500ms per finding

    def test_sp3_no_secrets_na(self) -> None:
        """SP-3: No secrets found is N/A."""
        analysis = {
            "results": {
                "scan_time_ms": 1000,
                "total_secrets": 0,
            }
        }
        ground_truth = {}

        results = run_performance_checks(analysis, ground_truth)
        sp3 = next(r for r in results if r.check_id == "SP-3")

        assert sp3.passed is True
        assert "N/A" in sp3.message

    def test_sp4_findings_within_limit(self) -> None:
        """SP-4: Findings count within threshold passes."""
        analysis = {
            "results": {
                "findings": [{"file_path": f"file{i}.txt"} for i in range(50)]
            }
        }
        ground_truth = {"thresholds": {"max_findings_for_test": 100}}

        results = run_performance_checks(analysis, ground_truth)
        sp4 = next(r for r in results if r.check_id == "SP-4")

        assert sp4.passed is True
        assert "50" in sp4.message

    def test_sp4_findings_exceed_limit(self) -> None:
        """SP-4: Findings count exceeds threshold fails."""
        analysis = {
            "results": {
                "findings": [{"file_path": f"file{i}.txt"} for i in range(150)]
            }
        }
        ground_truth = {"thresholds": {"max_findings_for_test": 100}}

        results = run_performance_checks(analysis, ground_truth)
        sp4 = next(r for r in results if r.check_id == "SP-4")

        assert sp4.passed is False
        assert "150" in sp4.message

    def test_sp4_uses_default_threshold(self) -> None:
        """SP-4: Uses default 100 finding limit if not specified."""
        analysis = {
            "results": {
                "findings": [{"file_path": f"file{i}.txt"} for i in range(75)]
            }
        }
        ground_truth = {}

        results = run_performance_checks(analysis, ground_truth)
        sp4 = next(r for r in results if r.check_id == "SP-4")

        assert sp4.passed is True

    def test_sp4_empty_findings(self) -> None:
        """SP-4: Empty findings passes."""
        analysis = {"results": {"findings": []}}
        ground_truth = {}

        results = run_performance_checks(analysis, ground_truth)
        sp4 = next(r for r in results if r.check_id == "SP-4")

        assert sp4.passed is True

    def test_all_checks_return_4_results(self) -> None:
        """All 4 performance checks should be returned."""
        analysis = {
            "results": {
                "scan_time_ms": 1000,
                "commits_with_secrets": 1,
                "total_secrets": 1,
                "findings": [],
            }
        }
        ground_truth = {}

        results = run_performance_checks(analysis, ground_truth)

        assert len(results) == 4
        check_ids = {r.check_id for r in results}
        expected_ids = {f"SP-{i}" for i in range(1, 5)}
        assert check_ids == expected_ids

    def test_handles_flat_analysis_format(self) -> None:
        """Should handle flat analysis format (no results wrapper)."""
        analysis = {
            "scan_time_ms": 1000,
            "commits_with_secrets": 2,
            "total_secrets": 3,
            "findings": [],
        }
        ground_truth = {"thresholds": {"max_scan_time_ms": 5000}}

        results = run_performance_checks(analysis, ground_truth)
        sp1 = next(r for r in results if r.check_id == "SP-1")

        assert sp1.passed is True

    def test_realistic_scenario_passes(self) -> None:
        """Realistic scenario with typical values."""
        analysis = {
            "results": {
                "scan_time_ms": 2500,
                "commits_with_secrets": 3,
                "total_secrets": 5,
                "findings": [
                    {"file_path": ".env", "line_number": 1},
                    {"file_path": ".env", "line_number": 5},
                    {"file_path": "config.py", "line_number": 10},
                    {"file_path": "secrets.txt", "line_number": 1},
                    {"file_path": "api.py", "line_number": 15},
                ],
            }
        }
        ground_truth = {
            "thresholds": {
                "max_scan_time_ms": 5000,
                "max_ms_per_commit": 1000,
                "max_ms_per_finding": 500,
                "max_findings_for_test": 100,
            }
        }

        results = run_performance_checks(analysis, ground_truth)

        for result in results:
            assert result.passed is True, f"{result.check_id} failed: {result.message}"
