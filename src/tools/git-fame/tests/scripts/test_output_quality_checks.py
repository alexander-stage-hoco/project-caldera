"""Tests for git-fame output quality checks.

Tests verify the output quality checks that validate the structure,
completeness, and format of git-fame analysis output.
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
# Schema Structure Tests
# =============================================================================


class TestOutputSchemaStructure:
    """Test output schema structure requirements."""

    def test_top_level_fields_present(self, valid_output_data: dict[str, Any]):
        """Output should have all required top-level fields."""
        required_fields = ["schema_version", "generated_at", "repo_name", "repo_path", "results"]

        for field in required_fields:
            assert field in valid_output_data, f"Missing required field: {field}"

    def test_results_section_present(self, valid_output_data: dict[str, Any]):
        """Results section should have all required fields."""
        results = valid_output_data["results"]
        required_fields = ["tool", "tool_version", "run_id", "provenance", "summary", "authors"]

        for field in required_fields:
            assert field in results, f"Missing required field in results: {field}"

    def test_summary_section_present(self, valid_output_data: dict[str, Any]):
        """Summary section should have all required metrics."""
        summary = valid_output_data["results"]["summary"]
        required_fields = [
            "author_count",
            "total_loc",
            "hhi_index",
            "bus_factor",
            "top_author_pct",
            "top_two_pct",
        ]

        for field in required_fields:
            assert field in summary, f"Missing required field in summary: {field}"

    def test_author_fields_present(self, valid_output_data: dict[str, Any]):
        """Each author should have all required fields."""
        authors = valid_output_data["results"]["authors"]
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
                assert field in author, f"Missing field '{field}' in author {author.get('name', 'unknown')}"

    def test_provenance_fields_present(self, valid_output_data: dict[str, Any]):
        """Provenance section should have required fields."""
        provenance = valid_output_data["results"]["provenance"]
        required_fields = ["tool", "command"]

        for field in required_fields:
            assert field in provenance, f"Missing required field in provenance: {field}"


# =============================================================================
# Field Type Tests
# =============================================================================


class TestFieldTypes:
    """Test that fields have correct types."""

    def test_schema_version_is_string(self, valid_output_data: dict[str, Any]):
        """schema_version should be a string."""
        assert isinstance(valid_output_data["schema_version"], str)

    def test_generated_at_is_string(self, valid_output_data: dict[str, Any]):
        """generated_at should be a string (ISO format)."""
        assert isinstance(valid_output_data["generated_at"], str)

    def test_repo_name_is_string(self, valid_output_data: dict[str, Any]):
        """repo_name should be a string."""
        assert isinstance(valid_output_data["repo_name"], str)

    def test_author_count_is_integer(self, valid_output_data: dict[str, Any]):
        """author_count should be an integer."""
        assert isinstance(valid_output_data["results"]["summary"]["author_count"], int)

    def test_total_loc_is_integer(self, valid_output_data: dict[str, Any]):
        """total_loc should be an integer."""
        assert isinstance(valid_output_data["results"]["summary"]["total_loc"], int)

    def test_hhi_index_is_float(self, valid_output_data: dict[str, Any]):
        """hhi_index should be a float."""
        hhi = valid_output_data["results"]["summary"]["hhi_index"]
        assert isinstance(hhi, (int, float))

    def test_bus_factor_is_integer(self, valid_output_data: dict[str, Any]):
        """bus_factor should be an integer."""
        assert isinstance(valid_output_data["results"]["summary"]["bus_factor"], int)

    def test_ownership_pct_is_float(self, valid_output_data: dict[str, Any]):
        """ownership_pct should be a float."""
        for author in valid_output_data["results"]["authors"]:
            assert isinstance(author["ownership_pct"], (int, float))

    def test_authors_is_list(self, valid_output_data: dict[str, Any]):
        """authors should be a list."""
        assert isinstance(valid_output_data["results"]["authors"], list)


# =============================================================================
# Field Value Validation Tests
# =============================================================================


class TestFieldValues:
    """Test that field values are within valid ranges."""

    def test_schema_version_format(self, valid_output_data: dict[str, Any]):
        """schema_version should follow semver format."""
        version = valid_output_data["schema_version"]
        parts = version.split(".")
        assert len(parts) == 3, f"Version should have 3 parts: {version}"
        for part in parts:
            assert part.isdigit(), f"Version parts should be numeric: {version}"

    def test_generated_at_is_iso_format(self, valid_output_data: dict[str, Any]):
        """generated_at should be valid ISO 8601 format."""
        from datetime import datetime

        timestamp = valid_output_data["generated_at"]
        # Should not raise
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_author_count_non_negative(self, valid_output_data: dict[str, Any]):
        """author_count should be non-negative."""
        count = valid_output_data["results"]["summary"]["author_count"]
        assert count >= 0

    def test_total_loc_non_negative(self, valid_output_data: dict[str, Any]):
        """total_loc should be non-negative."""
        loc = valid_output_data["results"]["summary"]["total_loc"]
        assert loc >= 0

    def test_hhi_index_in_valid_range(self, valid_output_data: dict[str, Any]):
        """hhi_index should be between 0 and 1."""
        hhi = valid_output_data["results"]["summary"]["hhi_index"]
        assert 0 <= hhi <= 1, f"HHI {hhi} out of valid range [0, 1]"

    def test_bus_factor_non_negative(self, valid_output_data: dict[str, Any]):
        """bus_factor should be non-negative."""
        bf = valid_output_data["results"]["summary"]["bus_factor"]
        assert bf >= 0

    def test_bus_factor_at_most_author_count(self, valid_output_data: dict[str, Any]):
        """bus_factor should not exceed author count."""
        bf = valid_output_data["results"]["summary"]["bus_factor"]
        count = valid_output_data["results"]["summary"]["author_count"]
        assert bf <= count

    def test_top_author_pct_in_valid_range(self, valid_output_data: dict[str, Any]):
        """top_author_pct should be between 0 and 100."""
        pct = valid_output_data["results"]["summary"]["top_author_pct"]
        assert 0 <= pct <= 100, f"Top author pct {pct} out of range [0, 100]"

    def test_top_two_pct_in_valid_range(self, valid_output_data: dict[str, Any]):
        """top_two_pct should be between 0 and 100."""
        pct = valid_output_data["results"]["summary"]["top_two_pct"]
        assert 0 <= pct <= 100, f"Top two pct {pct} out of range [0, 100]"

    def test_ownership_pct_in_valid_range(self, valid_output_data: dict[str, Any]):
        """Each author's ownership_pct should be between 0 and 100."""
        for author in valid_output_data["results"]["authors"]:
            pct = author["ownership_pct"]
            assert 0 <= pct <= 100, (
                f"Author {author['name']} ownership {pct} out of range [0, 100]"
            )

    def test_surviving_loc_non_negative(self, valid_output_data: dict[str, Any]):
        """Each author's surviving_loc should be non-negative."""
        for author in valid_output_data["results"]["authors"]:
            loc = author["surviving_loc"]
            assert loc >= 0, f"Author {author['name']} has negative LOC: {loc}"


# =============================================================================
# Consistency Tests
# =============================================================================


class TestOutputConsistency:
    """Test internal consistency of output values."""

    def test_author_count_matches_list_length(self, valid_output_data: dict[str, Any]):
        """author_count should match the length of authors list."""
        count = valid_output_data["results"]["summary"]["author_count"]
        actual_count = len(valid_output_data["results"]["authors"])
        assert count == actual_count

    def test_total_loc_matches_sum(self, valid_output_data: dict[str, Any]):
        """total_loc should match sum of author LOCs."""
        total = valid_output_data["results"]["summary"]["total_loc"]
        calculated = sum(a["surviving_loc"] for a in valid_output_data["results"]["authors"])
        assert total == calculated

    def test_ownership_sums_to_100(self, valid_output_data: dict[str, Any]):
        """Ownership percentages should sum to approximately 100%."""
        total = sum(a["ownership_pct"] for a in valid_output_data["results"]["authors"])
        assert 99.0 <= total <= 100.1, f"Ownership total {total} not close to 100%"

    def test_top_author_pct_matches_first(self, valid_output_data: dict[str, Any]):
        """top_author_pct should match first author's ownership."""
        top_pct = valid_output_data["results"]["summary"]["top_author_pct"]
        first_pct = valid_output_data["results"]["authors"][0]["ownership_pct"]
        assert top_pct == first_pct

    def test_top_two_pct_matches_sum(self, valid_output_data: dict[str, Any]):
        """top_two_pct should match sum of top two authors."""
        authors = valid_output_data["results"]["authors"]
        expected = sum(a["ownership_pct"] for a in authors[:2])
        actual = valid_output_data["results"]["summary"]["top_two_pct"]
        assert abs(expected - actual) < 0.1

    def test_authors_sorted_by_ownership(self, valid_output_data: dict[str, Any]):
        """Authors should be sorted by ownership descending."""
        authors = valid_output_data["results"]["authors"]
        ownerships = [a["ownership_pct"] for a in authors]
        assert ownerships == sorted(ownerships, reverse=True)

    def test_tool_name_consistent(self, valid_output_data: dict[str, Any]):
        """Tool name should be consistent across output."""
        results_tool = valid_output_data["results"]["tool"]
        provenance_tool = valid_output_data["results"]["provenance"]["tool"]
        assert results_tool == provenance_tool == "git-fame"


# =============================================================================
# Empty/Minimal Output Tests
# =============================================================================


class TestEmptyOutput:
    """Test handling of empty or minimal output."""

    def test_empty_authors_valid_structure(self):
        """Empty authors list should still have valid structure."""
        output = {
            "schema_version": "1.0.0",
            "generated_at": "2026-02-06T12:00:00Z",
            "repo_name": "empty-repo",
            "repo_path": "/path/to/empty-repo",
            "results": {
                "tool": "git-fame",
                "tool_version": "3.1.1",
                "run_id": "test-run",
                "provenance": {"tool": "git-fame", "command": "git-fame --format json"},
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

        assert output["results"]["summary"]["author_count"] == 0
        assert output["results"]["summary"]["total_loc"] == 0
        assert len(output["results"]["authors"]) == 0

    def test_single_author_valid(self, single_author_data: dict[str, Any]):
        """Single author output should be valid."""
        output = single_author_data

        assert output["results"]["summary"]["author_count"] == 1
        assert len(output["results"]["authors"]) == 1
        assert output["results"]["summary"]["top_author_pct"] == 100.0
        assert output["results"]["summary"]["hhi_index"] == 1.0


# =============================================================================
# JSON Serialization Tests
# =============================================================================


class TestJSONSerialization:
    """Test that output can be serialized/deserialized correctly."""

    def test_round_trip_serialization(self, valid_output_data: dict[str, Any]):
        """Output should survive JSON round-trip."""
        serialized = json.dumps(valid_output_data)
        deserialized = json.loads(serialized)

        assert deserialized == valid_output_data

    def test_pretty_print_serialization(self, valid_output_data: dict[str, Any]):
        """Output should survive pretty-printed JSON round-trip."""
        serialized = json.dumps(valid_output_data, indent=2)
        deserialized = json.loads(serialized)

        assert deserialized == valid_output_data

    def test_no_non_json_types(self, valid_output_data: dict[str, Any]):
        """Output should not contain non-JSON-serializable types."""
        # This will raise if there are non-serializable types
        json.dumps(valid_output_data)


# =============================================================================
# File Output Tests
# =============================================================================


class TestFileOutput:
    """Test output file creation and content."""

    def test_output_file_created(self, output_dir_with_data: Path):
        """Analysis output file should be created."""
        analysis_file = output_dir_with_data / "latest" / "analysis.json"
        assert analysis_file.exists()

    def test_output_file_valid_json(self, output_dir_with_data: Path):
        """Analysis output file should contain valid JSON."""
        analysis_file = output_dir_with_data / "latest" / "analysis.json"
        content = analysis_file.read_text()
        data = json.loads(content)  # Should not raise

        assert "results" in data

    def test_output_file_not_empty(self, output_dir_with_data: Path):
        """Analysis output file should not be empty."""
        analysis_file = output_dir_with_data / "latest" / "analysis.json"
        content = analysis_file.read_text()

        assert len(content) > 0

    def test_combined_output_valid(self, output_dir_with_multiple_repos: Path):
        """Combined analysis file should contain all repos."""
        combined_file = output_dir_with_multiple_repos / "combined_analysis.json"
        assert combined_file.exists()

        content = json.loads(combined_file.read_text())
        assert len(content) == 4
        assert "single-author" in content
        assert "balanced" in content
