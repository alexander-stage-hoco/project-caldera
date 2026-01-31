"""Tests for output quality checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.output_quality import run_output_quality_checks


def test_output_quality_checks_pass_for_minimal_payload():
    analysis = {
        "tool": "semgrep",
        "tool_version": "1.0.0",
        "metadata": {"schema_version": "1.0.0"},
        "summary": {},
        "directories": [],
        "files": [
            {"path": "src/app.py", "language": "python", "lines": 10, "smell_count": 0, "smells": []},
        ],
        "by_language": {},
        "statistics": {},
        "_root": {
            "metadata": {
                "tool_name": "semgrep",
                "tool_version": "1.0.0",
                "run_id": "11111111-1111-1111-1111-111111111111",
                "repo_id": "22222222-2222-2222-2222-222222222222",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "2026-01-21T00:00:00Z",
                "schema_version": "1.0.0",
            },
            "data": {
                "tool": "semgrep",
                "tool_version": "1.0.0",
                "summary": {},
                "directories": [],
                "files": [],
                "by_language": {},
                "statistics": {},
            },
        },
    }

    results = run_output_quality_checks(analysis)

    assert all(r.passed for r in results)
