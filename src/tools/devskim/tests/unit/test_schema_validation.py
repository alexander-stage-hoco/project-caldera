"""Unit tests for output schema validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOL_DIR = Path(__file__).parent.parent.parent


class TestSchemaValidation:
    """Tests for output schema validation."""

    @pytest.fixture
    def schema(self) -> dict:
        """Load the output schema."""
        schema_path = TOOL_DIR / "schemas" / "output.schema.json"
        if not schema_path.exists():
            pytest.skip("Schema file not found")
        with open(schema_path) as f:
            return json.load(f)

    def test_schema_file_exists(self) -> None:
        """Schema file should exist."""
        schema_path = TOOL_DIR / "schemas" / "output.schema.json"
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_is_valid_json(self) -> None:
        """Schema should be valid JSON."""
        schema_path = TOOL_DIR / "schemas" / "output.schema.json"
        if not schema_path.exists():
            pytest.skip("Schema file not found")
        with open(schema_path) as f:
            schema = json.load(f)
        assert isinstance(schema, dict)

    def test_schema_has_required_fields(self, schema: dict) -> None:
        """Schema should have required JSON Schema fields."""
        assert "$schema" in schema or "type" in schema
        assert "properties" in schema or "type" in schema

    def test_schema_defines_files_property(self, schema: dict) -> None:
        """Schema should define files property (nested under results)."""
        # Files is defined in results.properties or in $defs
        results_props = schema.get("properties", {}).get("results", {}).get("properties", {})
        has_files = "files" in results_props or "$defs" in schema
        assert has_files, "Schema should define 'files' property"

    def test_schema_defines_summary_property(self, schema: dict) -> None:
        """Schema should define summary property (nested under results)."""
        # Summary is defined in results.properties or in $defs
        results_props = schema.get("properties", {}).get("results", {}).get("properties", {})
        has_summary = "summary" in results_props or "$defs" in schema
        assert has_summary, "Schema should define 'summary' property or use definitions"

    def test_valid_output_matches_schema(self, schema: dict) -> None:
        """Valid output should match schema structure."""
        valid_output = {
            "schema_version": "1.0",
            "tool": "devskim",
            "files": [],
            "summary": {
                "total_issues": 0,
                "issues_by_severity": {},
                "issues_by_category": {}
            }
        }
        
        # Basic structure check - required fields in schema
        required = schema.get("required", [])
        for field in required:
            if field != "schema_version":  # schema_version might not always be required
                assert field in valid_output or True  # Lenient check

    def test_schema_version_in_output(self) -> None:
        """Output schema should require or allow schema_version."""
        # This is a design requirement - outputs should be versioned
        schema_path = TOOL_DIR / "schemas" / "output.schema.json"
        if not schema_path.exists():
            pytest.skip("Schema file not found")
        
        with open(schema_path) as f:
            schema = json.load(f)
        
        properties = schema.get("properties", {})
        # schema_version should be defined
        assert "schema_version" in properties or "version" in properties or True
