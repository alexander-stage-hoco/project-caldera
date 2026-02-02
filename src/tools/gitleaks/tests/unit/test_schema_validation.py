"""Schema validation tests for gitleaks output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")


def test_output_schema_validation_passes(tmp_path: Path) -> None:
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    payload = {
        "metadata": {
            "tool_name": "gitleaks",
            "tool_version": "8.18.4",
            "run_id": "00000000-0000-0000-0000-000000000000",
            "repo_id": "00000000-0000-0000-0000-000000000000",
            "branch": "main",
            "commit": "0" * 40,
            "timestamp": "2026-01-21T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "gitleaks",
            "tool_version": "8.18.4",
            "total_secrets": 0,
            "findings": [],
        },
    }

    jsonschema.validate(payload, schema)
