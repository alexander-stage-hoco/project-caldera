"""Tests for scc analyze.py output structure.

Tests that the analyze.py script produces output conforming to
TOOL_REQUIREMENTS.md schema standards.
"""

import pytest
import re
import sys
from pathlib import Path

# Add scripts to path for imports
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

import analyze
from analyze import to_standard_output


def build_output(result: dict) -> dict:
    return to_standard_output(
        result,
        run_id="11111111-1111-1111-1111-111111111111",
        repo_id="22222222-2222-2222-2222-222222222222",
        branch="main",
        commit="a" * 40,
        tool_version="3.6.0",
        timestamp="2026-01-23T12:00:00Z",
    )


class TestToStandardOutput:
    """Tests for the to_standard_output function."""

    def test_output_has_required_top_level_fields(self):
        """Output should have metadata and data sections."""
        result = {"summary": {}, "languages": []}
        output = build_output(result)

        assert "metadata" in output
        assert "data" in output

        metadata = output["metadata"]
        assert metadata["schema_version"] == "1.0.0"
        assert metadata["tool_name"] == "scc"
        assert metadata["tool_version"] == "3.6.0"
        assert metadata["run_id"] == "11111111-1111-1111-1111-111111111111"
        assert metadata["repo_id"] == "22222222-2222-2222-2222-222222222222"
        assert metadata["branch"] == "main"
        assert metadata["commit"] == "a" * 40

    def test_results_has_tool_metadata(self):
        """Data object should have tool and tool_version."""
        result = {"summary": {}}
        output = build_output(result)

        assert "data" in output
        assert output["data"]["tool"] == "scc"
        assert output["data"]["tool_version"] == "3.6.0"

    def test_schema_version_is_valid_semver(self):
        """Schema version should be valid semver format (X.Y.Z)."""
        result = {"summary": {}}
        output = build_output(result)

        semver_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(semver_pattern, output["metadata"]["schema_version"]), \
            f"schema_version '{output['metadata']['schema_version']}' is not valid semver"

    def test_tool_version_is_valid_semver(self):
        """Tool version should be valid semver format (X.Y.Z)."""
        result = {"summary": {}}
        output = build_output(result)

        semver_pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(semver_pattern, output["metadata"]["tool_version"]), \
            f"tool_version '{output['metadata']['tool_version']}' is not valid semver"

    def test_generated_at_removed_from_input(self):
        """timestamp should be in metadata, not in data."""
        result = {"summary": {}, "timestamp": "2026-01-22T00:00:00Z"}
        output = build_output(result)

        assert output["metadata"]["timestamp"] == "2026-01-23T12:00:00Z"
        assert "timestamp" not in output["data"]

    def test_schema_version_not_duplicated_in_results(self):
        """schema_version should be at top level only, not in results."""
        result = {"summary": {}, "schema_version": "1.0"}
        output = build_output(result)

        assert "schema_version" not in output["data"]

    def test_preserves_result_data(self):
        """Original result data should be preserved in results."""
        result = {
            "summary": {"total_files": 10, "total_lines": 1000},
            "files": [{"path": "test.py", "loc": 100}],
            "directories": [{"path": "src", "loc": 500}],
        }
        output = build_output(result)

        assert output["data"]["summary"]["total_files"] == 10
        assert output["data"]["summary"]["total_lines"] == 1000
        assert len(output["data"]["files"]) == 1
        assert len(output["data"]["directories"]) == 1

    def test_tool_metadata_consistency(self):
        """Top-level and results-level tool metadata should match."""
        result = {"summary": {}}
        output = build_output(result)

        assert output["metadata"]["tool_name"] == output["data"]["tool"]
        assert output["metadata"]["tool_version"] == output["data"]["tool_version"]


class TestOutputSchemaCompliance:
    """Tests for schema compliance with TOOL_REQUIREMENTS.md."""

    def test_required_fields_present(self):
        """All required fields must be present."""
        result = {"summary": {}, "languages": []}
        output = build_output(result)

        metadata_fields = [
            "tool_name",
            "tool_version",
            "run_id",
            "repo_id",
            "branch",
            "commit",
            "timestamp",
            "schema_version",
        ]
        for field in metadata_fields:
            assert field in output["metadata"], f"Missing metadata field: {field}"

        data_fields = ["tool", "tool_version", "summary", "languages"]
        for field in data_fields:
            assert field in output["data"], f"Missing data field: {field}"

    def test_tool_name_lowercase(self):
        """Tool name should be lowercase."""
        result = {"summary": {}}
        output = build_output(result)

        assert output["metadata"]["tool_name"] == output["metadata"]["tool_name"].lower()
        assert output["data"]["tool"] == output["data"]["tool"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
