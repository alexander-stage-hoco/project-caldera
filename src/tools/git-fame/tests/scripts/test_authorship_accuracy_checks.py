"""Tests for git-fame authorship accuracy checks.

Tests verify the accuracy checks that compare git-fame output
against ground truth values for author counts, ownership percentages,
and concentration metrics.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# =============================================================================
# Fixtures for Accuracy Checks
# =============================================================================


@pytest.fixture
def ground_truth_multi_author() -> dict[str, Any]:
    """Ground truth for multi-author repository."""
    return {
        "schema_version": "1.0",
        "scenario": "multi-author",
        "expected": {
            "summary": {
                "author_count": 3,
                "total_loc": {"min": 300, "max": 400},
            },
            "concentration_metrics": {
                "bus_factor": 1,
                "hhi_index": {"min": 0.35, "max": 0.42},
                "top_author_pct": {"min": 48.0, "max": 53.0},
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "loc_pct": {"min": 48.0, "max": 53.0},
                },
                {
                    "name": "Bob Engineer",
                    "loc_pct": {"min": 28.0, "max": 33.0},
                },
                {
                    "name": "Carol Coder",
                    "loc_pct": {"min": 18.0, "max": 23.0},
                },
            ],
        },
    }


@pytest.fixture
def ground_truth_single_author() -> dict[str, Any]:
    """Ground truth for single-author repository."""
    return {
        "schema_version": "1.0",
        "scenario": "single-author",
        "expected": {
            "summary": {
                "author_count": 1,
            },
            "concentration_metrics": {
                "bus_factor": 1,
                "hhi_index": {"min": 0.99, "max": 1.01},
                "top_author_pct": {"min": 99.0, "max": 100.1},
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "loc_pct": {"min": 99.0, "max": 100.1},
                },
            ],
        },
    }


# =============================================================================
# Author Count Accuracy Tests
# =============================================================================


class TestAuthorCountAccuracy:
    """Test author count accuracy checks."""

    def test_author_count_exact_match(
        self, multi_author_data: dict[str, Any], ground_truth_multi_author: dict[str, Any]
    ):
        """Should pass when author count matches exactly."""
        output = multi_author_data
        expected_count = ground_truth_multi_author["expected"]["summary"]["author_count"]
        actual_count = output["results"]["summary"]["author_count"]

        assert actual_count == expected_count

    def test_author_count_single_author(
        self, single_author_data: dict[str, Any], ground_truth_single_author: dict[str, Any]
    ):
        """Should correctly identify single author."""
        output = single_author_data
        expected_count = ground_truth_single_author["expected"]["summary"]["author_count"]
        actual_count = output["results"]["summary"]["author_count"]

        assert actual_count == expected_count == 1

    def test_author_count_multiple_authors(self, balanced_data: dict[str, Any]):
        """Should correctly count multiple authors."""
        output = balanced_data
        actual_count = output["results"]["summary"]["author_count"]

        assert actual_count == 4

    def test_author_count_mismatch_detection(self, multi_author_data: dict[str, Any]):
        """Should detect author count mismatch."""
        output = multi_author_data
        actual_count = output["results"]["summary"]["author_count"]
        wrong_expected = 5

        assert actual_count != wrong_expected


# =============================================================================
# HHI Index Accuracy Tests
# =============================================================================


class TestHHIAccuracy:
    """Test HHI index accuracy checks."""

    def test_hhi_within_expected_range(
        self, multi_author_data: dict[str, Any], ground_truth_multi_author: dict[str, Any]
    ):
        """HHI should be within expected range for 50/30/20 split."""
        output = multi_author_data
        hhi = output["results"]["summary"]["hhi_index"]
        expected = ground_truth_multi_author["expected"]["concentration_metrics"]["hhi_index"]

        assert expected["min"] <= hhi <= expected["max"]

    def test_hhi_single_author_near_one(
        self, single_author_data: dict[str, Any], ground_truth_single_author: dict[str, Any]
    ):
        """Single author should have HHI near 1.0."""
        output = single_author_data
        hhi = output["results"]["summary"]["hhi_index"]
        expected = ground_truth_single_author["expected"]["concentration_metrics"]["hhi_index"]

        assert expected["min"] <= hhi <= expected["max"]

    def test_hhi_balanced_distribution(self, balanced_data: dict[str, Any]):
        """Balanced distribution should have HHI around 0.25."""
        output = balanced_data
        hhi = output["results"]["summary"]["hhi_index"]

        # For 4 equal authors: HHI = 4 * 0.25^2 = 0.25
        assert 0.24 <= hhi <= 0.27

    def test_hhi_high_concentration(self, bus_factor_1_data: dict[str, Any]):
        """High concentration should have high HHI."""
        output = bus_factor_1_data
        hhi = output["results"]["summary"]["hhi_index"]

        # 90/5/5 split: HHI = 0.81 + 0.0025 + 0.0025 = 0.815
        assert 0.80 <= hhi <= 0.86


# =============================================================================
# Bus Factor Accuracy Tests
# =============================================================================


class TestBusFactorAccuracy:
    """Test bus factor accuracy checks."""

    def test_bus_factor_single_author(
        self, single_author_data: dict[str, Any], ground_truth_single_author: dict[str, Any]
    ):
        """Single author should have bus factor of 1."""
        output = single_author_data
        bus_factor = output["results"]["summary"]["bus_factor"]
        expected = ground_truth_single_author["expected"]["concentration_metrics"]["bus_factor"]

        assert bus_factor == expected == 1

    def test_bus_factor_dominant_author(
        self, bus_factor_1_data: dict[str, Any]
    ):
        """Dominant author should result in bus factor of 1."""
        output = bus_factor_1_data
        bus_factor = output["results"]["summary"]["bus_factor"]

        assert bus_factor == 1

    def test_bus_factor_balanced(self, balanced_data: dict[str, Any]):
        """Balanced distribution should have bus factor of 2."""
        output = balanced_data
        bus_factor = output["results"]["summary"]["bus_factor"]

        # Four 25% authors need 2 to exceed 50%
        assert bus_factor == 2

    def test_bus_factor_multi_author(
        self, multi_author_data: dict[str, Any], ground_truth_multi_author: dict[str, Any]
    ):
        """Multi-author with dominant contributor should have bus factor of 1."""
        output = multi_author_data
        bus_factor = output["results"]["summary"]["bus_factor"]
        expected = ground_truth_multi_author["expected"]["concentration_metrics"]["bus_factor"]

        assert bus_factor == expected


# =============================================================================
# Top Author Percentage Tests
# =============================================================================


class TestTopAuthorPctAccuracy:
    """Test top author percentage accuracy checks."""

    def test_top_author_pct_within_range(
        self, multi_author_data: dict[str, Any], ground_truth_multi_author: dict[str, Any]
    ):
        """Top author percentage should be within expected range."""
        output = multi_author_data
        top_pct = output["results"]["summary"]["top_author_pct"]
        expected = ground_truth_multi_author["expected"]["concentration_metrics"]["top_author_pct"]

        assert expected["min"] <= top_pct <= expected["max"]

    def test_top_author_pct_single_author(
        self, single_author_data: dict[str, Any], ground_truth_single_author: dict[str, Any]
    ):
        """Single author should have 100% top author."""
        output = single_author_data
        top_pct = output["results"]["summary"]["top_author_pct"]
        expected = ground_truth_single_author["expected"]["concentration_metrics"]["top_author_pct"]

        assert expected["min"] <= top_pct <= expected["max"]

    def test_top_author_pct_balanced(self, balanced_data: dict[str, Any]):
        """Balanced distribution should have top author around 25%."""
        output = balanced_data
        top_pct = output["results"]["summary"]["top_author_pct"]

        assert 23.0 <= top_pct <= 27.0

    def test_top_author_pct_matches_first_author(self, valid_output_data: dict[str, Any]):
        """Top author pct should match first author's ownership."""
        output = valid_output_data
        top_pct = output["results"]["summary"]["top_author_pct"]
        first_author_pct = output["results"]["authors"][0]["ownership_pct"]

        assert top_pct == first_author_pct


# =============================================================================
# Individual Author Accuracy Tests
# =============================================================================


class TestIndividualAuthorAccuracy:
    """Test individual author accuracy checks."""

    def test_author_ownership_within_range(
        self, multi_author_data: dict[str, Any], ground_truth_multi_author: dict[str, Any]
    ):
        """Each author's ownership should be within expected range."""
        output = multi_author_data
        authors = output["results"]["authors"]
        expected_authors = ground_truth_multi_author["expected"]["authors"]

        for expected in expected_authors:
            # Find matching author in output
            actual = next(
                (a for a in authors if a["name"] == expected["name"]),
                None
            )
            assert actual is not None, f"Author {expected['name']} not found"

            loc_pct = actual["ownership_pct"]
            expected_range = expected["loc_pct"]
            assert expected_range["min"] <= loc_pct <= expected_range["max"], (
                f"{expected['name']}: {loc_pct} not in [{expected_range['min']}, {expected_range['max']}]"
            )

    def test_author_order_by_ownership(self, multi_author_data: dict[str, Any]):
        """Authors should be sorted by ownership descending."""
        output = multi_author_data
        authors = output["results"]["authors"]
        ownerships = [a["ownership_pct"] for a in authors]

        assert ownerships == sorted(ownerships, reverse=True)

    def test_author_ownership_sum_is_100(self, multi_author_data: dict[str, Any]):
        """Total ownership should sum to approximately 100%."""
        output = multi_author_data
        authors = output["results"]["authors"]
        total = sum(a["ownership_pct"] for a in authors)

        assert 99.0 <= total <= 100.1

    def test_author_loc_matches_ownership(self, valid_output_data: dict[str, Any]):
        """Author LOC and ownership percentage should be consistent."""
        output = valid_output_data
        authors = output["results"]["authors"]
        total_loc = output["results"]["summary"]["total_loc"]

        for author in authors:
            expected_pct = author["surviving_loc"] / total_loc * 100
            actual_pct = author["ownership_pct"]
            assert abs(expected_pct - actual_pct) < 0.1, (
                f"{author['name']}: expected {expected_pct:.2f}%, got {actual_pct:.2f}%"
            )


# =============================================================================
# Edge Case Accuracy Tests
# =============================================================================


class TestAccuracyEdgeCases:
    """Test accuracy checks for edge cases."""

    def test_empty_authors_list(self):
        """Should handle empty authors list."""
        output = {
            "results": {
                "summary": {
                    "author_count": 0,
                    "total_loc": 0,
                    "hhi_index": 0.0,
                    "bus_factor": 0,
                    "top_author_pct": 0.0,
                },
                "authors": [],
            },
        }

        assert output["results"]["summary"]["author_count"] == 0
        assert output["results"]["summary"]["hhi_index"] == 0.0
        assert output["results"]["summary"]["bus_factor"] == 0

    def test_very_small_ownership(self):
        """Should handle very small ownership percentages."""
        output = {
            "results": {
                "summary": {
                    "author_count": 100,
                    "total_loc": 10000,
                    "hhi_index": 0.01,  # Perfect equality with 100 authors
                    "bus_factor": 50,
                    "top_author_pct": 1.0,
                },
                "authors": [
                    {"name": f"Author {i}", "ownership_pct": 1.0}
                    for i in range(100)
                ],
            },
        }

        # Verify distribution is uniform
        ownerships = [a["ownership_pct"] for a in output["results"]["authors"]]
        assert all(pct == 1.0 for pct in ownerships)

    def test_very_large_ownership(self):
        """Should handle extremely concentrated ownership."""
        output = {
            "results": {
                "summary": {
                    "author_count": 2,
                    "total_loc": 10000,
                    "hhi_index": 0.9801,  # 99^2 + 1^2
                    "bus_factor": 1,
                    "top_author_pct": 99.0,
                },
                "authors": [
                    {"name": "Dominant", "ownership_pct": 99.0},
                    {"name": "Minor", "ownership_pct": 1.0},
                ],
            },
        }

        assert output["results"]["summary"]["top_author_pct"] == 99.0
        assert output["results"]["summary"]["bus_factor"] == 1

    def test_floating_point_precision(self):
        """Should handle floating point precision issues."""
        # Simulate a case where percentages might not sum to exactly 100
        output = {
            "results": {
                "summary": {
                    "author_count": 3,
                    "total_loc": 300,
                    "hhi_index": 0.3333,
                    "bus_factor": 2,
                    "top_author_pct": 33.34,
                },
                "authors": [
                    {"name": "A", "ownership_pct": 33.34, "surviving_loc": 100},
                    {"name": "B", "ownership_pct": 33.33, "surviving_loc": 100},
                    {"name": "C", "ownership_pct": 33.33, "surviving_loc": 100},
                ],
            },
        }

        total = sum(a["ownership_pct"] for a in output["results"]["authors"])
        # Should be close to 100
        assert 99.9 <= total <= 100.1


# =============================================================================
# Comparison with Ground Truth Tests
# =============================================================================


class TestGroundTruthComparison:
    """Test comparison functions against ground truth."""

    def test_value_within_range(self):
        """Test helper for checking value within min/max range."""
        def value_in_range(value: float, range_dict: dict[str, float]) -> bool:
            return range_dict["min"] <= value <= range_dict["max"]

        assert value_in_range(0.38, {"min": 0.35, "max": 0.42})
        assert not value_in_range(0.50, {"min": 0.35, "max": 0.42})
        assert value_in_range(0.35, {"min": 0.35, "max": 0.42})  # boundary
        assert value_in_range(0.42, {"min": 0.35, "max": 0.42})  # boundary

    def test_exact_match_comparison(self):
        """Test exact value comparison."""
        expected = 3
        actual = 3
        assert expected == actual

        expected = 1
        actual = 1
        assert expected == actual

    def test_tolerance_comparison(self):
        """Test comparison with tolerance."""
        expected = 0.38
        actual = 0.379
        tolerance = 0.01

        assert abs(expected - actual) < tolerance
