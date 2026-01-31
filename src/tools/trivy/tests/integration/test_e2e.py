"""End-to-end integration tests for Trivy tool."""

import json
from pathlib import Path

import pytest


@pytest.mark.integration
class TestTrivyE2E:
    """End-to-end tests for Trivy analysis pipeline."""

    def test_output_schema_validation(self):
        """Test that output matches the JSON schema."""
        # This test requires a pre-generated output file
        output_dir = Path(__file__).parent.parent.parent / "output" / "runs"
        schema_path = Path(__file__).parent.parent.parent / "schemas" / "output.schema.json"

        if not schema_path.exists():
            pytest.skip("Schema file not found")

        output_files = list(output_dir.glob("*.json"))
        if not output_files:
            pytest.skip("No output files to validate")

        import jsonschema

        schema = json.loads(schema_path.read_text())

        for output_file in output_files:
            data = json.loads(output_file.read_text())
            jsonschema.validate(data, schema)

    def test_envelope_structure(self):
        """Test that output has correct envelope structure."""
        output_dir = Path(__file__).parent.parent.parent / "output" / "runs"
        output_files = list(output_dir.glob("*.json"))

        if not output_files:
            pytest.skip("No output files to validate")

        for output_file in output_files:
            data = json.loads(output_file.read_text())

            # Check top-level structure
            assert "metadata" in data
            assert "data" in data

            # Check metadata fields
            metadata = data["metadata"]
            assert metadata["tool_name"] == "trivy"
            assert "tool_version" in metadata
            assert "run_id" in metadata
            assert "schema_version" in metadata

            # Check data fields
            output_data = data["data"]
            assert output_data["tool"] == "trivy"
            assert "targets" in output_data
            assert "vulnerabilities" in output_data
