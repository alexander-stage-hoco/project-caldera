"""Tests that all outputs validate against the JSON schema."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from reviewer import run_review


@pytest.fixture
def schema() -> dict:
    schema_path = Path(__file__).parent.parent / "schemas" / "review_result.schema.json"
    return json.loads(schema_path.read_text())


class TestOutputValidates:
    def test_existing_smoke_test_validates(self, schema: dict) -> None:
        """Validate the existing LLM-generated smoke test result."""
        results_dir = Path(__file__).parent.parent / "results"
        smoke_files = list(results_dir.glob("pmd-cpd-*.json"))
        if not smoke_files:
            pytest.skip("No pmd-cpd smoke test result found")
        for f in smoke_files:
            data = json.loads(f.read_text())
            jsonschema.validate(data, schema)

    def test_programmatic_output_validates(
        self, project_root: Path, schema: dict, tmp_path: Path,
    ) -> None:
        """Run reviewer and validate output against schema."""
        result = run_review(
            target="scc",
            review_type="tool_implementation",
            project_root=project_root,
            output_dir=tmp_path,
        )
        data = result.to_dict()
        jsonschema.validate(data, schema)

    def test_cross_tool_output_validates(
        self, project_root: Path, schema: dict, tmp_path: Path,
    ) -> None:
        result = run_review(
            target="cross-tool",
            review_type="cross_tool",
            project_root=project_root,
            output_dir=tmp_path,
        )
        data = result.to_dict()
        jsonschema.validate(data, schema)
