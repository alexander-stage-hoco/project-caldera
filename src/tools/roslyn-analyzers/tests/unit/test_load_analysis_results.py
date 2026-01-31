import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import load_analysis_results


def test_load_analysis_results_unwraps_results(tmp_path):
    analysis = {
        "schema_version": "1.0.0",
        "generated_at": "2026-01-22T10:00:00Z",
        "repo_name": "synthetic",
        "repo_path": "/tmp/synthetic",
        "results": {
            "tool": "roslyn-analyzers",
            "tool_version": "1.0.0",
            "analysis_duration_ms": 1234,
            "summary": {"total_files_analyzed": 1},
            "files": [],
            "statistics": {},
            "directory_rollup": {},
        },
    }
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(analysis))

    loaded = load_analysis_results(str(analysis_path))

    assert loaded["summary"]["total_files_analyzed"] == 1
    assert loaded["files"] == []
    assert loaded["metadata"]["analysis_duration_ms"] == 1234
    assert loaded["metadata"]["timestamp"] == "2026-01-22T10:00:00Z"
    assert "_root" in loaded
