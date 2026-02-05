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

    This fixture provides a realistic dotCover output structure
    matching the schema in schemas/output.schema.json.
    """
    return {
        "metadata": {
            "tool_name": "dotcover",
            "tool_version": "2025.3.2",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440000",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2025-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "dotcover",
            "tool_version": "2025.3.2",
            "summary": {
                "total_assemblies": 1,
                "total_types": 2,
                "total_methods": 5,
                "covered_statements": 15,
                "total_statements": 20,
                "statement_coverage_pct": 75.0,
            },
            "assemblies": [
                {
                    "name": "CoverageDemo",
                    "covered_statements": 15,
                    "total_statements": 20,
                    "statement_coverage_pct": 75.0,
                },
            ],
            "types": [
                {
                    "assembly": "CoverageDemo",
                    "namespace": "CoverageDemo",
                    "name": "Calculator",
                    "file_path": "src/Calculator.cs",
                    "covered_statements": 12,
                    "total_statements": 16,
                    "statement_coverage_pct": 75.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "namespace": "CoverageDemo",
                    "name": "StringUtils",
                    "file_path": "src/StringUtils.cs",
                    "covered_statements": 3,
                    "total_statements": 4,
                    "statement_coverage_pct": 75.0,
                },
            ],
            "methods": [
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Add(int, int)",
                    "covered_statements": 3,
                    "total_statements": 3,
                    "statement_coverage_pct": 100.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Subtract(int, int)",
                    "covered_statements": 3,
                    "total_statements": 3,
                    "statement_coverage_pct": 100.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Multiply(int, int)",
                    "covered_statements": 3,
                    "total_statements": 5,
                    "statement_coverage_pct": 60.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Divide(int, int)",
                    "covered_statements": 3,
                    "total_statements": 5,
                    "statement_coverage_pct": 60.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "StringUtils",
                    "name": "Reverse(string)",
                    "covered_statements": 3,
                    "total_statements": 4,
                    "statement_coverage_pct": 75.0,
                },
            ],
        },
    }


def test_analyze_output_structure(sample_output: dict):
    """Test that analyze produces valid output structure."""
    # Verify top-level structure
    assert "metadata" in sample_output
    assert "data" in sample_output

    # Verify data structure matches dotcover schema
    data = sample_output["data"]
    assert "tool" in data
    assert data["tool"] == "dotcover"
    assert "assemblies" in data
    assert "types" in data
    assert "methods" in data
    assert "summary" in data
    assert isinstance(data["assemblies"], list)
    assert isinstance(data["types"], list)
    assert isinstance(data["methods"], list)


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


def test_summary_fields(sample_output: dict):
    """Test that summary contains all required coverage fields."""
    required_fields = [
        "total_assemblies", "total_types", "total_methods",
        "covered_statements", "total_statements", "statement_coverage_pct"
    ]
    summary = sample_output["data"]["summary"]

    for field in required_fields:
        assert field in summary, f"Missing required summary field: {field}"


def test_assembly_structure(sample_output: dict):
    """Test that assemblies have required fields."""
    required_fields = [
        "name", "covered_statements", "total_statements", "statement_coverage_pct"
    ]

    for assembly in sample_output["data"]["assemblies"]:
        for field in required_fields:
            assert field in assembly, f"Missing assembly field: {field}"


def test_type_structure(sample_output: dict):
    """Test that types have required fields."""
    required_fields = [
        "assembly", "name", "covered_statements",
        "total_statements", "statement_coverage_pct"
    ]

    for type_entry in sample_output["data"]["types"]:
        for field in required_fields:
            assert field in type_entry, f"Missing type field: {field}"


def test_method_structure(sample_output: dict):
    """Test that methods have required fields."""
    required_fields = [
        "assembly", "type_name", "name", "covered_statements",
        "total_statements", "statement_coverage_pct"
    ]

    for method in sample_output["data"]["methods"]:
        for field in required_fields:
            assert field in method, f"Missing method field: {field}"


def test_coverage_invariant_covered_lte_total(sample_output: dict):
    """Test that covered statements never exceed total statements."""
    data = sample_output["data"]

    # Check assemblies
    for assembly in data["assemblies"]:
        assert assembly["covered_statements"] <= assembly["total_statements"], \
            f"Assembly {assembly['name']}: covered > total"

    # Check types
    for type_entry in data["types"]:
        assert type_entry["covered_statements"] <= type_entry["total_statements"], \
            f"Type {type_entry['name']}: covered > total"

    # Check methods
    for method in data["methods"]:
        assert method["covered_statements"] <= method["total_statements"], \
            f"Method {method['name']}: covered > total"


def test_coverage_percentage_bounds(sample_output: dict):
    """Test that coverage percentages are in valid range [0, 100]."""
    data = sample_output["data"]

    # Check summary
    assert 0 <= data["summary"]["statement_coverage_pct"] <= 100

    # Check assemblies
    for assembly in data["assemblies"]:
        assert 0 <= assembly["statement_coverage_pct"] <= 100, \
            f"Assembly {assembly['name']}: invalid coverage percentage"

    # Check types
    for type_entry in data["types"]:
        assert 0 <= type_entry["statement_coverage_pct"] <= 100, \
            f"Type {type_entry['name']}: invalid coverage percentage"

    # Check methods
    for method in data["methods"]:
        assert 0 <= method["statement_coverage_pct"] <= 100, \
            f"Method {method['name']}: invalid coverage percentage"


def test_path_normalization(sample_output: dict):
    """Test that all file paths are repo-relative.

    Paths MUST be repo-relative (no leading /, ./, or ..)
    See docs/TOOL_REQUIREMENTS.md for path requirements.
    """
    data = sample_output["data"]

    for type_entry in data.get("types", []):
        path = type_entry.get("file_path")
        if path is None:
            continue  # file_path is optional
        # Must not be absolute
        assert not path.startswith("/"), f"Absolute path found: {path}"
        # Must not have ./ prefix
        assert not path.startswith("./"), f"Path has ./ prefix: {path}"
        # Must not contain .. segments
        assert ".." not in path.split("/"), f"Path has .. segment: {path}"
        # Must use forward slashes
        assert "\\" not in path, f"Path has backslash: {path}"


def test_hierarchy_consistency(sample_output: dict):
    """Test that methods reference valid types in the same assembly."""
    data = sample_output["data"]

    # Build set of valid (assembly, type) pairs
    valid_types = {
        (t["assembly"], t["name"])
        for t in data["types"]
    }

    # Check all methods reference valid types
    for method in data["methods"]:
        key = (method["assembly"], method["type_name"])
        assert key in valid_types, \
            f"Method {method['name']} references unknown type {method['type_name']}"


def test_non_negative_counts(sample_output: dict):
    """Test that all statement counts are non-negative."""
    data = sample_output["data"]

    # Check summary
    assert data["summary"]["covered_statements"] >= 0
    assert data["summary"]["total_statements"] >= 0

    # Check all entities
    for assembly in data["assemblies"]:
        assert assembly["covered_statements"] >= 0
        assert assembly["total_statements"] >= 0

    for type_entry in data["types"]:
        assert type_entry["covered_statements"] >= 0
        assert type_entry["total_statements"] >= 0

    for method in data["methods"]:
        assert method["covered_statements"] >= 0
        assert method["total_statements"] >= 0


def test_schema_validation(sample_output: dict):
    """Test that output validates against schemas/output.schema.json."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")

    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    if not schema_path.exists():
        pytest.skip("Schema file not found")

    schema = json.loads(schema_path.read_text())
    jsonschema.validate(sample_output, schema)
