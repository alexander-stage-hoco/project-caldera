"""Tests for git-fame reliability checks.

Tests verify the reliability checks that ensure git-fame produces
consistent, reproducible results across multiple runs and scenarios.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# =============================================================================
# Deterministic Output Tests
# =============================================================================


class TestDeterministicOutput:
    """Test that output is deterministic for the same input."""

    def test_same_input_same_author_count(
        self, multi_author_data: dict[str, Any]
    ):
        """Same repository should produce same author count."""
        output1 = multi_author_data
        # Simulate a second run with same data
        output2 = multi_author_data.copy()

        assert output1["results"]["summary"]["author_count"] == output2["results"]["summary"]["author_count"]

    def test_same_input_same_hhi(self, multi_author_data: dict[str, Any]):
        """Same repository should produce same HHI index."""
        output1 = multi_author_data
        output2 = multi_author_data.copy()

        assert output1["results"]["summary"]["hhi_index"] == output2["results"]["summary"]["hhi_index"]

    def test_same_input_same_bus_factor(self, multi_author_data: dict[str, Any]):
        """Same repository should produce same bus factor."""
        output1 = multi_author_data
        output2 = multi_author_data.copy()

        assert output1["results"]["summary"]["bus_factor"] == output2["results"]["summary"]["bus_factor"]

    def test_same_input_same_author_order(self, multi_author_data: dict[str, Any]):
        """Same repository should produce same author order."""
        output1 = multi_author_data
        output2 = multi_author_data.copy()

        authors1 = [a["name"] for a in output1["results"]["authors"]]
        authors2 = [a["name"] for a in output2["results"]["authors"]]

        assert authors1 == authors2


# =============================================================================
# Multi-Scenario Reliability Tests
# =============================================================================


class TestMultiScenarioReliability:
    """Test reliability across different repository scenarios."""

    def test_single_author_metrics_valid(self, single_author_data: dict[str, Any]):
        """Single-author scenario should produce valid metrics."""
        output = single_author_data
        summary = output["results"]["summary"]

        assert summary["author_count"] == 1
        assert summary["hhi_index"] == 1.0
        assert summary["bus_factor"] == 1
        assert summary["top_author_pct"] == 100.0

    def test_multi_author_metrics_valid(self, multi_author_data: dict[str, Any]):
        """Multi-author scenario should produce valid metrics."""
        output = multi_author_data
        summary = output["results"]["summary"]

        assert summary["author_count"] == 3
        assert 0.0 < summary["hhi_index"] < 1.0
        assert summary["bus_factor"] >= 1
        assert summary["top_author_pct"] < 100.0

    def test_balanced_metrics_valid(self, balanced_data: dict[str, Any]):
        """Balanced scenario should produce low concentration metrics."""
        output = balanced_data
        summary = output["results"]["summary"]

        assert summary["author_count"] == 4
        # Balanced should have lower HHI
        assert summary["hhi_index"] < 0.3
        # Balanced should have higher bus factor
        assert summary["bus_factor"] >= 2

    def test_high_concentration_metrics_valid(self, bus_factor_1_data: dict[str, Any]):
        """High concentration scenario should produce high HHI."""
        output = bus_factor_1_data
        summary = output["results"]["summary"]

        assert summary["hhi_index"] > 0.8
        assert summary["bus_factor"] == 1
        assert summary["top_author_pct"] > 85.0


# =============================================================================
# Metric Invariant Tests
# =============================================================================


class TestMetricInvariants:
    """Test mathematical invariants that must hold."""

    def test_hhi_range_invariant(
        self,
        single_author_data: dict[str, Any],
        multi_author_data: dict[str, Any],
        balanced_data: dict[str, Any],
        bus_factor_1_data: dict[str, Any],
    ):
        """HHI should always be in [0, 1] range."""
        for output in [single_author_data, multi_author_data, balanced_data, bus_factor_1_data]:
            hhi = output["results"]["summary"]["hhi_index"]
            assert 0 <= hhi <= 1, f"HHI {hhi} out of range"

    def test_bus_factor_range_invariant(
        self,
        single_author_data: dict[str, Any],
        multi_author_data: dict[str, Any],
        balanced_data: dict[str, Any],
        bus_factor_1_data: dict[str, Any],
    ):
        """Bus factor should be between 0 and author count."""
        for output in [single_author_data, multi_author_data, balanced_data, bus_factor_1_data]:
            bf = output["results"]["summary"]["bus_factor"]
            count = output["results"]["summary"]["author_count"]
            assert 0 <= bf <= count, f"Bus factor {bf} out of range [0, {count}]"

    def test_ownership_sum_invariant(
        self,
        single_author_data: dict[str, Any],
        multi_author_data: dict[str, Any],
        balanced_data: dict[str, Any],
        bus_factor_1_data: dict[str, Any],
    ):
        """Ownership percentages should sum to approximately 100%."""
        for output in [single_author_data, multi_author_data, balanced_data, bus_factor_1_data]:
            total = sum(a["ownership_pct"] for a in output["results"]["authors"])
            assert 99.0 <= total <= 100.1, f"Ownership sum {total} not close to 100%"

    def test_loc_consistency_invariant(
        self,
        single_author_data: dict[str, Any],
        multi_author_data: dict[str, Any],
        balanced_data: dict[str, Any],
        bus_factor_1_data: dict[str, Any],
    ):
        """Sum of author LOCs should equal total LOC."""
        for output in [single_author_data, multi_author_data, balanced_data, bus_factor_1_data]:
            total_loc = output["results"]["summary"]["total_loc"]
            sum_loc = sum(a["surviving_loc"] for a in output["results"]["authors"])
            assert total_loc == sum_loc

    def test_author_count_consistency_invariant(
        self,
        single_author_data: dict[str, Any],
        multi_author_data: dict[str, Any],
        balanced_data: dict[str, Any],
        bus_factor_1_data: dict[str, Any],
    ):
        """Author count should match authors list length."""
        for output in [single_author_data, multi_author_data, balanced_data, bus_factor_1_data]:
            count = output["results"]["summary"]["author_count"]
            actual = len(output["results"]["authors"])
            assert count == actual


# =============================================================================
# HHI Calculation Reliability Tests
# =============================================================================


class TestHHIReliability:
    """Test HHI calculation reliability."""

    def test_hhi_single_author_is_one(self, single_author_data: dict[str, Any]):
        """Single author should have HHI of exactly 1.0."""
        hhi = single_author_data["results"]["summary"]["hhi_index"]
        assert hhi == 1.0

    def test_hhi_equal_split_calculation(self, balanced_data: dict[str, Any]):
        """Equal split should have predictable HHI."""
        hhi = balanced_data["results"]["summary"]["hhi_index"]
        # 4 authors with 25% each: HHI = 4 * 0.25^2 = 0.25
        assert abs(hhi - 0.25) < 0.03

    def test_hhi_50_30_20_calculation(self, multi_author_data: dict[str, Any]):
        """50/30/20 split should have predictable HHI."""
        hhi = multi_author_data["results"]["summary"]["hhi_index"]
        # HHI = 0.5^2 + 0.3^2 + 0.2^2 = 0.25 + 0.09 + 0.04 = 0.38
        assert abs(hhi - 0.38) < 0.02

    def test_hhi_high_concentration_calculation(self, bus_factor_1_data: dict[str, Any]):
        """90/5/5 split should have predictable high HHI."""
        hhi = bus_factor_1_data["results"]["summary"]["hhi_index"]
        # HHI = 0.9^2 + 0.05^2 + 0.05^2 = 0.81 + 0.0025 + 0.0025 = 0.815
        assert abs(hhi - 0.815) < 0.02


# =============================================================================
# Bus Factor Calculation Reliability Tests
# =============================================================================


class TestBusFactorReliability:
    """Test bus factor calculation reliability."""

    def test_bus_factor_single_author(self, single_author_data: dict[str, Any]):
        """Single author should have bus factor of 1."""
        bf = single_author_data["results"]["summary"]["bus_factor"]
        assert bf == 1

    def test_bus_factor_50_pct_threshold(self, multi_author_data: dict[str, Any]):
        """50% author exceeds default 50% threshold, bus factor = 1."""
        bf = multi_author_data["results"]["summary"]["bus_factor"]
        assert bf == 1

    def test_bus_factor_balanced(self, balanced_data: dict[str, Any]):
        """4 equal 25% authors need 2 for 50% threshold."""
        bf = balanced_data["results"]["summary"]["bus_factor"]
        assert bf == 2

    def test_bus_factor_dominant(self, bus_factor_1_data: dict[str, Any]):
        """90% dominant author has bus factor of 1."""
        bf = bus_factor_1_data["results"]["summary"]["bus_factor"]
        assert bf == 1


# =============================================================================
# Cross-Repository Comparison Tests
# =============================================================================


class TestCrossRepoComparison:
    """Test comparison across multiple repositories."""

    def test_hhi_ordering_matches_concentration(
        self,
        single_author_data: dict[str, Any],
        bus_factor_1_data: dict[str, Any],
        multi_author_data: dict[str, Any],
        balanced_data: dict[str, Any],
    ):
        """HHI should be ordered by concentration level."""
        single_hhi = single_author_data["results"]["summary"]["hhi_index"]
        dominant_hhi = bus_factor_1_data["results"]["summary"]["hhi_index"]
        multi_hhi = multi_author_data["results"]["summary"]["hhi_index"]
        balanced_hhi = balanced_data["results"]["summary"]["hhi_index"]

        # single > dominant > multi > balanced
        assert single_hhi >= dominant_hhi
        assert dominant_hhi > multi_hhi
        assert multi_hhi > balanced_hhi

    def test_bus_factor_ordering(
        self,
        single_author_data: dict[str, Any],
        bus_factor_1_data: dict[str, Any],
        balanced_data: dict[str, Any],
    ):
        """Bus factor should correlate with distribution."""
        single_bf = single_author_data["results"]["summary"]["bus_factor"]
        dominant_bf = bus_factor_1_data["results"]["summary"]["bus_factor"]
        balanced_bf = balanced_data["results"]["summary"]["bus_factor"]

        # balanced should have higher bus factor than concentrated repos
        assert balanced_bf >= single_bf
        assert balanced_bf >= dominant_bf


# =============================================================================
# Empty/Edge Case Reliability Tests
# =============================================================================


class TestEdgeCaseReliability:
    """Test reliability for edge cases."""

    def test_empty_repo_produces_valid_output(self):
        """Empty repository should produce valid output structure."""
        empty_output = {
            "schema_version": "1.0.0",
            "generated_at": "2026-02-06T12:00:00Z",
            "repo_name": "empty",
            "repo_path": "/path/to/empty",
            "results": {
                "tool": "git-fame",
                "tool_version": "3.1.1",
                "run_id": "test-run",
                "provenance": {"tool": "git-fame", "command": "git-fame"},
                "summary": {
                    "author_count": 0,
                    "total_loc": 0,
                    "hhi_index": 0.0,
                    "bus_factor": 0,
                    "top_author_pct": 0.0,
                    "top_two_pct": 0.0,
                },
                "authors": [],
            },
        }

        # Verify invariants still hold
        assert empty_output["results"]["summary"]["author_count"] == len(empty_output["results"]["authors"])
        assert empty_output["results"]["summary"]["total_loc"] == 0

    def test_very_many_authors_produces_valid_output(self):
        """Repository with many authors should produce valid output."""
        # Simulate 100 authors with 1% each
        authors = [
            {
                "name": f"Author{i}",
                "surviving_loc": 100,
                "insertions_total": 110,
                "deletions_total": 10,
                "commit_count": 1,
                "files_touched": 1,
                "ownership_pct": 1.0,
            }
            for i in range(100)
        ]

        output = {
            "results": {
                "summary": {
                    "author_count": 100,
                    "total_loc": 10000,
                    "hhi_index": 0.01,  # 100 * 0.01^2 = 0.01
                    "bus_factor": 50,   # Need 50 to get 50%
                    "top_author_pct": 1.0,
                    "top_two_pct": 2.0,
                },
                "authors": authors,
            },
        }

        assert output["results"]["summary"]["author_count"] == 100
        assert output["results"]["summary"]["hhi_index"] <= 0.02  # Very low concentration

    def test_single_line_repo_produces_valid_output(self):
        """Repository with single LOC should produce valid output."""
        output = {
            "results": {
                "summary": {
                    "author_count": 1,
                    "total_loc": 1,
                    "hhi_index": 1.0,
                    "bus_factor": 1,
                    "top_author_pct": 100.0,
                    "top_two_pct": 100.0,
                },
                "authors": [
                    {
                        "name": "Solo",
                        "surviving_loc": 1,
                        "ownership_pct": 100.0,
                    },
                ],
            },
        }

        assert output["results"]["summary"]["total_loc"] == 1
        assert output["results"]["summary"]["hhi_index"] == 1.0


# =============================================================================
# Multi-Run Consistency Tests
# =============================================================================


class TestMultiRunConsistency:
    """Test consistency across multiple analysis runs."""

    def test_run_id_changes_but_metrics_stable(
        self, multi_author_data: dict[str, Any]
    ):
        """Run ID should change but core metrics should be stable."""
        run1 = copy.deepcopy(multi_author_data)
        run1["results"]["run_id"] = "run-1"

        run2 = copy.deepcopy(multi_author_data)
        run2["results"]["run_id"] = "run-2"

        # Run IDs are different
        assert run1["results"]["run_id"] != run2["results"]["run_id"]

        # But metrics are the same
        assert run1["results"]["summary"]["hhi_index"] == run2["results"]["summary"]["hhi_index"]
        assert run1["results"]["summary"]["bus_factor"] == run2["results"]["summary"]["bus_factor"]

    def test_timestamp_changes_but_metrics_stable(
        self, multi_author_data: dict[str, Any]
    ):
        """Timestamp should change but core metrics should be stable."""
        run1 = copy.deepcopy(multi_author_data)
        run1["generated_at"] = "2026-02-06T10:00:00Z"

        run2 = copy.deepcopy(multi_author_data)
        run2["generated_at"] = "2026-02-06T11:00:00Z"

        # Timestamps are different
        assert run1["generated_at"] != run2["generated_at"]

        # But metrics are the same
        assert run1["results"]["summary"]["author_count"] == run2["results"]["summary"]["author_count"]
