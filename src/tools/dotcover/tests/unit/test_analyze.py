"""Unit tests for dotcover analyze script.

For implementation examples, see:
- src/tools/scc/tests/unit/test_analyze.py
- src/tools/lizard/tests/unit/test_analyze.py
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


# Fixture: sample analysis output
@pytest.fixture
def sample_output() -> dict:
    """Load a sample output.json for testing.

    TODO: Replace with actual output from your tool.
    Option 1: Load from evaluation/results/output.json
    Option 2: Create minimal valid output inline
    """
    return {
        "metadata": {
            "tool_name": "dotcover",
            "tool_version": "1.0.0",
            "run_id": "test-run-id",
            "repo_id": "test-repo-id",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2025-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "dotcover",
            "tool_version": "1.0.0",
            "files": [
                {"path": "src/main.py", "size_bytes": 100},
            ],
            "summary": {
                "file_count": 1,
                "total_bytes": 100,
            },
        },
    }


def test_analyze_output_structure(sample_output: dict):
    """Test that analyze produces valid output structure."""
    # Verify top-level structure
    assert "metadata" in sample_output
    assert "data" in sample_output

    # Verify data structure
    data = sample_output["data"]
    assert "tool" in data
    assert "files" in data
    assert isinstance(data["files"], list)


def test_analyze_metadata_fields(sample_output: dict):
    """Test that all required metadata fields are present."""
    required_fields = [
        "tool_name", "tool_version", "run_id", "repo_id",
        "branch", "commit", "timestamp", "schema_version"
    ]
    metadata = sample_output["metadata"]

    for field in required_fields:
        assert field in metadata, f"Missing required field: {field}"
        assert metadata[field], f"Field is empty: {field}"


def test_path_normalization(sample_output: dict):
    """Test that all paths are repo-relative.

    Paths MUST be repo-relative (no leading /, ./, or ..)
    See docs/TOOL_REQUIREMENTS.md for path requirements.
    """
    data = sample_output["data"]

    for file_entry in data.get("files", []):
        path = file_entry.get("path", "")
        # Must not be absolute
        assert not path.startswith("/"), f"Absolute path found: {path}"
        # Must not have ./ prefix
        assert not path.startswith("./"), f"Path has ./ prefix: {path}"
        # Must not contain .. segments
        assert ".." not in path.split("/"), f"Path has .. segment: {path}"
        # Must use forward slashes
        assert "\\" not in path, f"Path has backslash: {path}"


# TODO: Add tool-specific tests below
#
# def test_metric_values_in_range(sample_output: dict):
#     """Test that metric values are within expected ranges."""
#     ...
#
# def test_schema_validation():
#     """Test that output validates against schemas/output.schema.json."""
#     import jsonschema
#     schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
#     schema = json.loads(schema_path.read_text())
#     jsonschema.validate(sample_output, schema)
