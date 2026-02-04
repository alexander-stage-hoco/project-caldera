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
