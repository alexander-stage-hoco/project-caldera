import json
from pathlib import Path

from scripts.checks import load_all_results


def test_load_all_results_reads_root_output(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    root_output = {
        "metadata": {
            "tool_name": "git-sizer",
            "tool_version": "1.5.0",
            "run_id": "run-1",
            "repo_id": "repo-1",
            "repo_name": "bloated",
            "branch": "main",
            "commit": "0" * 40,
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "git-sizer",
            "tool_version": "1.5.0",
            "repo_name": "bloated",
            "health_grade": "D",
            "duration_ms": 10,
            "metrics": {
                "max_blob_size": 10_485_760,
                "blob_total_size": 23_068_736,
                "commit_count": 1,
                "max_tree_entries": 0,
                "max_path_depth": 1,
            },
            "violations": [],
            "lfs_candidates": [{"path": "assets/large.bin", "size_bytes": 10_485_760}],
            "raw_output": {},
        },
    }

    (results_dir / "output.json").write_text(json.dumps(root_output))

    analysis = load_all_results(results_dir)
    repos = analysis.get("repositories", [])
    assert len(repos) == 1
    assert repos[0]["repository"] == "bloated"
