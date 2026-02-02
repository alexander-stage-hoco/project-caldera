"""Tests for evaluation analysis loading."""

import json
import sys
from pathlib import Path

# Add scripts directory to path for importing checks
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import load_analysis


def test_load_analysis_unwraps_results(tmp_path: Path):
    """Ensure wrapper payloads are unwrapped to results."""
    payload = {
        "schema_version": "1.0.0",
        "generated_at": "2026-01-21T00:00:00Z",
        "repo_name": "synthetic",
        "repo_path": "/tmp/synthetic",
        "results": {
            "files": [{"path": "src/app.py", "smells": []}],
            "summary": {"total_files": 1},
        },
    }
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(payload))

    analysis = load_analysis(analysis_path)

    assert analysis["files"][0]["path"] == "src/app.py"
    assert analysis["_root"]["repo_name"] == "synthetic"


def test_load_analysis_passes_through_flat_payload(tmp_path: Path):
    """Ensure non-wrapped payloads are returned as-is."""
    payload = {"files": [{"path": "src/app.py", "smells": []}]}
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(payload))

    analysis = load_analysis(analysis_path)

    assert analysis["files"][0]["path"] == "src/app.py"


def test_load_analysis_unwraps_envelope(tmp_path: Path):
    payload = {
        "metadata": {"tool_name": "semgrep"},
        "data": {
            "files": [{"path": "src/app.py", "smells": []}],
            "summary": {"total_files": 1},
        },
    }
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(payload))

    analysis = load_analysis(analysis_path)

    assert analysis["files"][0]["path"] == "src/app.py"
    assert analysis["_root"]["metadata"]["tool_name"] == "semgrep"
