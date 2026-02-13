"""Integration tests for the CLI reviewer orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

# Import reviewer from parent directory
from reviewer import run_review


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "results"


class TestReviewerIntegration:
    def test_review_scc_produces_valid_output(
        self, project_root: Path, output_dir: Path,
    ) -> None:
        result = run_review(
            target="scc",
            review_type="tool_implementation",
            project_root=project_root,
            output_dir=output_dir,
        )
        assert result.target == "scc"
        assert result.review_type == "tool_implementation"
        assert result.summary.dimensions_reviewed == 5

        # Validate output file was written
        files = list(output_dir.glob("scc-programmatic-*.json"))
        assert len(files) == 1

        # Validate against schema
        schema_path = Path(__file__).parent.parent / "schemas" / "review_result.schema.json"
        schema = json.loads(schema_path.read_text())
        output = json.loads(files[0].read_text())
        jsonschema.validate(output, schema)

    def test_review_nonexistent_tool_graceful(
        self, project_root: Path, output_dir: Path,
    ) -> None:
        result = run_review(
            target="nonexistent-tool-xyz",
            review_type="tool_implementation",
            project_root=project_root,
            output_dir=output_dir,
        )
        # Should still produce a result, not crash
        assert result.target == "nonexistent-tool-xyz"
        assert result.summary.dimensions_reviewed == 5
        # Nonexistent tool should have findings
        assert result.summary.total_findings > 0

    def test_cross_tool_review_runs(
        self, project_root: Path, output_dir: Path,
    ) -> None:
        result = run_review(
            target="cross-tool",
            review_type="cross_tool",
            project_root=project_root,
            output_dir=output_dir,
        )
        assert result.review_type == "cross_tool"
        assert result.summary.dimensions_reviewed == 1

    def test_blueprint_alignment_review(
        self, project_root: Path, output_dir: Path,
    ) -> None:
        result = run_review(
            target="lizard",
            review_type="blueprint_alignment",
            project_root=project_root,
            output_dir=output_dir,
        )
        assert result.review_type == "blueprint_alignment"
        assert result.summary.dimensions_reviewed == 1
