"""Tests for git-fame analyze.py functions.

Tests verify mathematical correctness of concentration metrics,
bus factor calculations, and output transformations.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from analyze import compute_bus_factor, compute_hhi, transform_output


# =============================================================================
# HHI (Herfindahl-Hirschman Index) Tests
# =============================================================================


class TestComputeHHI:
    """Test HHI concentration index calculation."""

    def test_hhi_single_author_is_one(self):
        """Single author with 100% ownership should have HHI=1.0."""
        ownership_pcts = [100.0]
        hhi = compute_hhi(ownership_pcts)
        assert hhi == 1.0, f"Single author HHI should be 1.0, got {hhi}"

    def test_hhi_two_equal_authors(self):
        """Two authors with 50% each should have HHI=0.5."""
        ownership_pcts = [50.0, 50.0]
        hhi = compute_hhi(ownership_pcts)
        assert abs(hhi - 0.5) < 0.001, f"Two equal authors HHI should be 0.5, got {hhi}"

    def test_hhi_four_equal_authors(self):
        """Four authors with 25% each should have HHI=0.25."""
        ownership_pcts = [25.0, 25.0, 25.0, 25.0]
        hhi = compute_hhi(ownership_pcts)
        assert abs(hhi - 0.25) < 0.001, f"Four equal authors HHI should be 0.25, got {hhi}"

    def test_hhi_ten_equal_authors(self):
        """Ten authors with 10% each should have HHI=0.1."""
        ownership_pcts = [10.0] * 10
        hhi = compute_hhi(ownership_pcts)
        assert abs(hhi - 0.1) < 0.001, f"Ten equal authors HHI should be 0.1, got {hhi}"

    def test_hhi_50_30_20_split(self):
        """Three authors with 50/30/20 split should have HHI=0.38."""
        ownership_pcts = [50.0, 30.0, 20.0]
        hhi = compute_hhi(ownership_pcts)
        # HHI = 0.5^2 + 0.3^2 + 0.2^2 = 0.25 + 0.09 + 0.04 = 0.38
        expected = 0.25 + 0.09 + 0.04
        assert abs(hhi - expected) < 0.001, f"50/30/20 split HHI should be {expected}, got {hhi}"

    def test_hhi_90_5_5_split(self):
        """Dominant author (90%) with two minor (5% each) should have HHI~0.815."""
        ownership_pcts = [90.0, 5.0, 5.0]
        hhi = compute_hhi(ownership_pcts)
        # HHI = 0.9^2 + 0.05^2 + 0.05^2 = 0.81 + 0.0025 + 0.0025 = 0.815
        expected = 0.81 + 0.0025 + 0.0025
        assert abs(hhi - expected) < 0.001, f"90/5/5 split HHI should be {expected}, got {hhi}"

    def test_hhi_empty_list_returns_zero(self):
        """Empty ownership list should return HHI=0."""
        hhi = compute_hhi([])
        assert hhi == 0.0, f"Empty list HHI should be 0.0, got {hhi}"

    def test_hhi_range_always_valid(self):
        """HHI should always be in range [0, 1]."""
        test_cases = [
            [100.0],
            [50.0, 50.0],
            [33.33, 33.33, 33.34],
            [70.0, 20.0, 10.0],
            [25.0, 25.0, 25.0, 25.0],
        ]
        for pcts in test_cases:
            hhi = compute_hhi(pcts)
            assert 0.0 <= hhi <= 1.0, f"HHI {hhi} out of range for {pcts}"

    def test_hhi_order_independent(self):
        """HHI should be the same regardless of ownership order."""
        pcts_sorted = [50.0, 30.0, 20.0]
        pcts_unsorted = [20.0, 50.0, 30.0]
        pcts_reversed = [20.0, 30.0, 50.0]

        hhi_sorted = compute_hhi(pcts_sorted)
        hhi_unsorted = compute_hhi(pcts_unsorted)
        hhi_reversed = compute_hhi(pcts_reversed)

        assert hhi_sorted == hhi_unsorted == hhi_reversed

    def test_hhi_more_authors_means_lower_hhi(self):
        """With equal distribution, more authors means lower HHI."""
        hhi_2 = compute_hhi([50.0, 50.0])  # 0.5
        hhi_4 = compute_hhi([25.0, 25.0, 25.0, 25.0])  # 0.25
        hhi_10 = compute_hhi([10.0] * 10)  # 0.1

        assert hhi_10 < hhi_4 < hhi_2


# =============================================================================
# Bus Factor Tests
# =============================================================================


class TestComputeBusFactor:
    """Test bus factor calculation."""

    def test_bus_factor_single_author(self):
        """Single author should have bus factor of 1."""
        ownership_pcts = [100.0]
        bus_factor = compute_bus_factor(ownership_pcts)
        assert bus_factor == 1, f"Single author bus factor should be 1, got {bus_factor}"

    def test_bus_factor_two_equal_authors(self):
        """Two 50% authors - need 1 for 50% threshold."""
        ownership_pcts = [50.0, 50.0]
        bus_factor = compute_bus_factor(ownership_pcts)
        assert bus_factor == 1, f"Two equal authors bus factor should be 1, got {bus_factor}"

    def test_bus_factor_two_equal_authors_higher_threshold(self):
        """Two 50% authors with 75% threshold - need 2 authors."""
        ownership_pcts = [50.0, 50.0]
        bus_factor = compute_bus_factor(ownership_pcts, threshold=75.0)
        assert bus_factor == 2, f"Two equal authors at 75% threshold should be 2, got {bus_factor}"

    def test_bus_factor_four_equal_authors(self):
        """Four 25% authors - need 2 for 50% threshold."""
        ownership_pcts = [25.0, 25.0, 25.0, 25.0]
        bus_factor = compute_bus_factor(ownership_pcts)
        assert bus_factor == 2, f"Four equal authors bus factor should be 2, got {bus_factor}"

    def test_bus_factor_dominant_author(self):
        """Dominant author (90%) should have bus factor of 1."""
        ownership_pcts = [90.0, 5.0, 5.0]
        bus_factor = compute_bus_factor(ownership_pcts)
        assert bus_factor == 1, f"90% dominant author bus factor should be 1, got {bus_factor}"

    def test_bus_factor_50_30_20_split(self):
        """50/30/20 split should have bus factor of 1 (top author exceeds 50%)."""
        ownership_pcts = [50.0, 30.0, 20.0]
        bus_factor = compute_bus_factor(ownership_pcts)
        assert bus_factor == 1, f"50/30/20 split bus factor should be 1, got {bus_factor}"

    def test_bus_factor_40_35_25_split(self):
        """40/35/25 split should have bus factor of 2 (need 40+35=75 for 50+%)."""
        ownership_pcts = [40.0, 35.0, 25.0]
        bus_factor = compute_bus_factor(ownership_pcts)
        assert bus_factor == 2, f"40/35/25 split bus factor should be 2, got {bus_factor}"

    def test_bus_factor_empty_list_returns_zero(self):
        """Empty ownership list should return bus factor of 0."""
        bus_factor = compute_bus_factor([])
        assert bus_factor == 0, f"Empty list bus factor should be 0, got {bus_factor}"

    def test_bus_factor_threshold_at_boundary(self):
        """Test bus factor when cumulative hits exactly 50%."""
        ownership_pcts = [50.0, 50.0]
        bus_factor = compute_bus_factor(ownership_pcts, threshold=50.0)
        # First author hits exactly 50%, so bus factor should be 1
        assert bus_factor == 1

    def test_bus_factor_unsorted_input(self):
        """Bus factor should correctly handle unsorted input by sorting."""
        ownership_pcts = [10.0, 50.0, 20.0, 20.0]
        bus_factor = compute_bus_factor(ownership_pcts)
        # Sorted: [50, 20, 20, 10] - first author >= 50%
        assert bus_factor == 1

    def test_bus_factor_all_return_count_if_threshold_not_met(self):
        """If threshold can't be met, return total count."""
        # 5 authors with 10% each can never reach 50% with just 4
        # But cumulative of all 5 is 50%, so should return 5 at threshold 50
        ownership_pcts = [10.0, 10.0, 10.0, 10.0, 10.0]
        bus_factor = compute_bus_factor(ownership_pcts, threshold=50.0)
        assert bus_factor == 5

    def test_bus_factor_custom_thresholds(self):
        """Test with various threshold values."""
        ownership_pcts = [30.0, 25.0, 20.0, 15.0, 10.0]

        # Threshold 25%: first author (30) exceeds
        assert compute_bus_factor(ownership_pcts, threshold=25.0) == 1

        # Threshold 50%: 30+25=55% >= 50%
        assert compute_bus_factor(ownership_pcts, threshold=50.0) == 2

        # Threshold 75%: 30+25+20=75% >= 75%
        assert compute_bus_factor(ownership_pcts, threshold=75.0) == 3

        # Threshold 90%: 30+25+20+15=90% >= 90%
        assert compute_bus_factor(ownership_pcts, threshold=90.0) == 4


# =============================================================================
# Transform Output Tests
# =============================================================================


class TestTransformOutput:
    """Test output transformation from raw git-fame to Caldera envelope format."""

    @pytest.fixture
    def raw_git_fame_output(self) -> dict[str, Any]:
        """Sample raw git-fame JSON output using actual git-fame column names."""
        return {
            "data": [
                ["Alice Developer", 500, 20, 10],  # Author, loc, coms, fils
                ["Bob Engineer", 300, 15, 8],
                ["Carol Coder", 200, 10, 5],
            ],
            "columns": ["Author", "loc", "coms", "fils"],
        }

    @pytest.fixture
    def empty_git_fame_output(self) -> dict[str, Any]:
        """Empty git-fame output (no data)."""
        return {"data": [], "columns": []}

    @pytest.fixture
    def default_transform_args(self) -> dict[str, Any]:
        """Default arguments for transform_output calls."""
        return {
            "insertions_map": {
                "Alice Developer": 500,
                "Bob Engineer": 300,
                "Carol Coder": 200,
            },
            "deletions_map": {
                "Alice Developer": 50,
                "Bob Engineer": 30,
                "Carol Coder": 20,
            },
            "repo_path": Path("/path/to/repo"),
            "run_id": "test-run",
            "repo_id": "test-repo-id",
            "branch": "main",
            "commit": "a" * 40,
        }

    def test_transform_output_structure(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Transformed output should have Caldera envelope structure."""
        result = transform_output(raw_git_fame_output, **default_transform_args)

        # Caldera envelope has metadata and data sections
        assert "metadata" in result
        assert "data" in result

    def test_transform_output_metadata_structure(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Metadata section should have correct structure."""
        result = transform_output(raw_git_fame_output, **default_transform_args)
        metadata = result["metadata"]

        assert metadata["tool_name"] == "git-fame"
        assert "tool_version" in metadata
        assert metadata["run_id"] == "test-run"
        assert metadata["repo_id"] == "test-repo-id"
        assert metadata["branch"] == "main"
        assert metadata["commit"] == "a" * 40
        assert "timestamp" in metadata
        assert "schema_version" in metadata

    def test_transform_output_data_structure(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Data section should have correct structure."""
        result = transform_output(raw_git_fame_output, **default_transform_args)
        data = result["data"]

        assert data["tool"] == "git-fame"
        assert "tool_version" in data
        assert "provenance" in data
        assert "summary" in data
        assert "authors" in data

    def test_transform_output_author_count(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Author count should match input data."""
        result = transform_output(raw_git_fame_output, **default_transform_args)

        assert result["data"]["summary"]["author_count"] == 3
        assert len(result["data"]["authors"]) == 3

    def test_transform_output_total_loc(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Total LOC should sum all author LOCs."""
        result = transform_output(raw_git_fame_output, **default_transform_args)

        # 500 + 300 + 200 = 1000
        assert result["data"]["summary"]["total_loc"] == 1000

    def test_transform_output_ownership_percentages(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Ownership percentages should be correctly calculated."""
        result = transform_output(raw_git_fame_output, **default_transform_args)
        authors = result["data"]["authors"]

        # Authors should be sorted by ownership descending
        assert authors[0]["name"] == "Alice Developer"
        assert authors[0]["ownership_pct"] == 50.0  # 500/1000 * 100

        assert authors[1]["name"] == "Bob Engineer"
        assert authors[1]["ownership_pct"] == 30.0  # 300/1000 * 100

        assert authors[2]["name"] == "Carol Coder"
        assert authors[2]["ownership_pct"] == 20.0  # 200/1000 * 100

    def test_transform_output_hhi_calculation(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """HHI should be correctly calculated from ownership percentages."""
        result = transform_output(raw_git_fame_output, **default_transform_args)

        # HHI = 0.5^2 + 0.3^2 + 0.2^2 = 0.25 + 0.09 + 0.04 = 0.38
        expected_hhi = 0.38
        assert abs(result["data"]["summary"]["hhi_index"] - expected_hhi) < 0.01

    def test_transform_output_bus_factor_calculation(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Bus factor should be correctly calculated."""
        result = transform_output(raw_git_fame_output, **default_transform_args)

        # With 50% top author, bus factor should be 1
        assert result["data"]["summary"]["bus_factor"] == 1

    def test_transform_output_top_author_pct(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Top author percentage should match highest ownership."""
        result = transform_output(raw_git_fame_output, **default_transform_args)

        assert result["data"]["summary"]["top_author_pct"] == 50.0

    def test_transform_output_top_two_pct(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Top two percentage should sum top two ownerships."""
        result = transform_output(raw_git_fame_output, **default_transform_args)

        # 50% + 30% = 80%
        assert result["data"]["summary"]["top_two_pct"] == 80.0

    def test_transform_output_empty_data(
        self, empty_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Empty data should produce valid output with zero values."""
        result = transform_output(empty_git_fame_output, **default_transform_args)

        summary = result["data"]["summary"]
        assert summary["author_count"] == 0
        assert summary["total_loc"] == 0
        assert summary["hhi_index"] == 0.0
        assert summary["bus_factor"] == 0
        assert summary["top_author_pct"] == 0.0
        assert result["data"]["authors"] == []

    def test_transform_output_author_fields(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Each author should have all required fields."""
        result = transform_output(raw_git_fame_output, **default_transform_args)
        authors = result["data"]["authors"]

        required_fields = [
            "name",
            "surviving_loc",
            "insertions_total",
            "deletions_total",
            "commit_count",
            "files_touched",
            "ownership_pct",
        ]

        for author in authors:
            for field in required_fields:
                assert field in author, f"Missing field: {field}"

    def test_transform_output_sorted_by_ownership(
        self, raw_git_fame_output: dict[str, Any], default_transform_args: dict
    ):
        """Authors should be sorted by ownership percentage descending."""
        result = transform_output(raw_git_fame_output, **default_transform_args)
        authors = result["data"]["authors"]

        ownerships = [a["ownership_pct"] for a in authors]
        assert ownerships == sorted(ownerships, reverse=True)


# =============================================================================
# Provenance Tests
# =============================================================================


class TestProvenance:
    """Test provenance information in output."""

    @pytest.fixture
    def sample_raw_output(self) -> dict[str, Any]:
        """Sample raw git-fame output using actual git-fame column names."""
        return {
            "data": [["Alice", 100, 5, 3]],  # Author, loc, coms, fils
            "columns": ["Author", "loc", "coms", "fils"],
        }

    @pytest.fixture
    def default_transform_args(self) -> dict[str, Any]:
        """Default arguments for transform_output calls."""
        return {
            "insertions_map": {"Alice": 100},
            "deletions_map": {"Alice": 10},
            "repo_path": Path("/path/to/repo"),
            "run_id": "test-run",
            "repo_id": "test-repo-id",
            "branch": "main",
            "commit": "a" * 40,
        }

    def test_provenance_contains_tool_name(
        self, sample_raw_output: dict[str, Any], default_transform_args: dict
    ):
        """Provenance should contain tool name."""
        result = transform_output(sample_raw_output, **default_transform_args)
        provenance = result["data"]["provenance"]

        assert provenance["tool"] == "git-fame"

    def test_provenance_contains_commands(
        self, sample_raw_output: dict[str, Any], default_transform_args: dict
    ):
        """Provenance should contain the commands used."""
        result = transform_output(sample_raw_output, **default_transform_args)
        provenance = result["data"]["provenance"]

        assert "commands" in provenance
        assert len(provenance["commands"]) == 3
        assert "git-fame" in provenance["commands"][0]
        assert "--loc surviving" in provenance["commands"][0]
        assert "--loc ins" in provenance["commands"][1]
        assert "--loc del" in provenance["commands"][2]

    def test_run_id_preserved(
        self, sample_raw_output: dict[str, Any], default_transform_args: dict
    ):
        """Run ID should be preserved in metadata."""
        run_id = "custom-run-id-12345"
        args = {**default_transform_args, "run_id": run_id}
        result = transform_output(sample_raw_output, **args)

        assert result["metadata"]["run_id"] == run_id

    def test_repo_name_preserved(
        self, sample_raw_output: dict[str, Any], default_transform_args: dict
    ):
        """Repository name should be derived from path."""
        repo_path = Path("/custom/path/to/my-repo")
        args = {**default_transform_args, "repo_path": repo_path}
        result = transform_output(sample_raw_output, **args)

        assert result["data"]["repo_name"] == "my-repo"

    def test_timestamp_is_valid_iso_format(
        self, sample_raw_output: dict[str, Any], default_transform_args: dict
    ):
        """timestamp should be a valid ISO format timestamp."""
        from datetime import datetime

        result = transform_output(sample_raw_output, **default_transform_args)

        timestamp = result["metadata"]["timestamp"]
        # Should not raise if valid ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_schema_version_present(
        self, sample_raw_output: dict[str, Any], default_transform_args: dict
    ):
        """Schema version should be present in metadata."""
        result = transform_output(sample_raw_output, **default_transform_args)

        assert result["metadata"]["schema_version"] == "1.0.0"
