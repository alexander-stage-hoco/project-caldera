"""Ensure semgrep outputs validate against the JSON schema."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from scripts.analyze import to_envelope_format


def test_output_matches_schema() -> None:
    data = {
        "tool": "semgrep",
        "tool_version": "1.0.0",
        "summary": {"total_files": 1, "total_smells": 0},
        "files": [
            {
                "path": "src/app.py",
                "language": "python",
                "smell_count": 0,
                "smells": [],
            }
        ],
    }
    output = to_envelope_format(
        data=data,
        run_id="11111111-1111-1111-1111-111111111111",
        repo_id="22222222-2222-2222-2222-222222222222",
        branch="main",
        commit="a" * 40,
        timestamp="2026-01-01T00:00:00Z",
        semgrep_version="1.0.0",
    )
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())
    jsonschema.validate(output, schema)


def test_finding_with_invalid_severity_fails_validation() -> None:
    """A smell entry with an invalid severity value should fail schema validation."""
    data = {
        "tool": "semgrep",
        "tool_version": "1.0.0",
        "summary": {"total_files": 1, "total_smells": 1},
        "files": [
            {
                "path": "src/app.py",
                "language": "python",
                "smell_count": 1,
                "smells": [
                    {
                        "rule_id": "test-rule",
                        "line_start": 10,
                        "severity": "INVALID_SEVERITY",
                        "message": "Test smell",
                    }
                ],
            }
        ],
    }
    output = to_envelope_format(
        data=data,
        run_id="11111111-1111-1111-1111-111111111111",
        repo_id="22222222-2222-2222-2222-222222222222",
        branch="main",
        commit="a" * 40,
        timestamp="2026-01-01T00:00:00Z",
        semgrep_version="1.0.0",
    )
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    with pytest.raises(jsonschema.ValidationError, match="INVALID_SEVERITY"):
        jsonschema.validate(output, schema)


def test_envelope_missing_metadata_commit_fails_validation() -> None:
    """Envelope missing required metadata.commit should fail validation."""
    data = {
        "tool": "semgrep",
        "tool_version": "1.0.0",
        "summary": {"total_files": 0, "total_smells": 0},
        "files": [],
    }
    output = to_envelope_format(
        data=data,
        run_id="11111111-1111-1111-1111-111111111111",
        repo_id="22222222-2222-2222-2222-222222222222",
        branch="main",
        commit="a" * 40,
        timestamp="2026-01-01T00:00:00Z",
        semgrep_version="1.0.0",
    )
    # Remove the commit field from metadata
    del output["metadata"]["commit"]

    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    with pytest.raises(jsonschema.ValidationError, match="commit"):
        jsonschema.validate(output, schema)
