"""Tests for output quality checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.output_quality import run_output_quality_checks


def test_output_quality_schema_validation_passes(tmp_path: Path):
    root_payload = {
        "schema_version": "2.0.0",
        "generated_at": "2026-01-21T00:00:00Z",
        "repo_name": "synthetic",
        "repo_path": "/tmp/synthetic",
        "results": {
            "tool": "gitleaks",
            "tool_version": "1.0.0",
            "total_secrets": 0,
            "findings": [],
        },
    }
    analysis = {"_root": root_payload}

    results = run_output_quality_checks(analysis)

    assert results[0].passed
