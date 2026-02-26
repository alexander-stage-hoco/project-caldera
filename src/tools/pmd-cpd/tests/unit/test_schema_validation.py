"""Schema validation tests for PMD CPD output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_output_schema_validation_passes() -> None:
    jsonschema = pytest.importorskip("jsonschema")

    tool_root = Path(__file__).parents[2]
    output_path = tool_root / "output" / "runs" / "synthetic.json"
    if not output_path.exists():
        pytest.skip("analysis output missing (run make analyze)")

    payload = json.loads(output_path.read_text())
    schema = json.loads((tool_root / "schemas" / "output.schema.json").read_text())

    jsonschema.validate(payload, schema)


def test_envelope_missing_commit_fails_validation() -> None:
    """Envelope missing required metadata.commit should fail schema validation."""
    jsonschema = pytest.importorskip("jsonschema")

    tool_root = Path(__file__).parents[2]
    schema = json.loads((tool_root / "schemas" / "output.schema.json").read_text())

    output = {
        "metadata": {
            "tool_name": "pmd-cpd",
            "tool_version": "7.0.0",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440000",
            "branch": "main",
            # "commit" deliberately omitted
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "pmd-cpd",
            "tool_version": "7.0.0",
            "summary": {"total_duplications": 0, "total_files_analyzed": 0},
            "duplications": [],
        },
    }

    with pytest.raises(jsonschema.ValidationError, match="commit"):
        jsonschema.validate(output, schema)


def test_envelope_invalid_commit_pattern_fails_validation() -> None:
    """Envelope with commit not matching ^[0-9a-f]{40}$ should fail."""
    jsonschema = pytest.importorskip("jsonschema")

    tool_root = Path(__file__).parents[2]
    schema = json.loads((tool_root / "schemas" / "output.schema.json").read_text())

    output = {
        "metadata": {
            "tool_name": "pmd-cpd",
            "tool_version": "7.0.0",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440000",
            "branch": "main",
            "commit": "short-sha",
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "pmd-cpd",
            "tool_version": "7.0.0",
        },
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(output, schema)
