"""Tests for output quality checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.output_quality import run_output_quality_checks


def test_output_quality_schema_validation_passes():
    analysis = {
        "_root": {
            "schema_version": "2.0.0",
            "generated_at": "2026-01-21T00:00:00Z",
            "repo_name": "synthetic",
            "repo_path": "/tmp/synthetic",
            "results": {
                "tool": "devskim",
                "tool_version": "1.0.0",
                "metadata": {},
                "summary": {},
            },
        }
    }

    results = run_output_quality_checks(analysis)

    assert results[0].passed
