"""Tests for scripts/build_results_index.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from build_results_index import build_index  # noqa: E402


class TestBuildIndex:
    def test_empty_results_dir(self, tmp_path: Path) -> None:
        index = build_index(tmp_path)
        assert index["total_runs"] == 0
        assert index["runs"] == []
        assert index["schema_version"] == 1
        assert "updated_at" in index

    def test_single_run(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "runs" / "cr-1"
        run_dir.mkdir(parents=True)
        manifest = {
            "collection_run": {
                "repo_id": "my-repo",
                "collection_run_id": "cr-1",
                "run_id": "run-1",
                "commit": "abc123",
                "branch": "main",
                "status": "completed",
                "started_at": "2026-01-01T00:00:00",
                "completed_at": "2026-01-01T00:05:00",
            },
            "tools": [{"tool_name": "scc"}, {"tool_name": "lizard"}],
        }
        (run_dir / "run_manifest.json").write_text(json.dumps(manifest))

        index = build_index(tmp_path)
        assert index["total_runs"] == 1
        entry = index["runs"][0]
        assert entry["repo_id"] == "my-repo"
        assert entry["commit"] == "abc123"
        assert entry["tool_count"] == 2
        assert entry["path"] == "runs/cr-1/"

    def test_multiple_runs_sorted_desc(self, tmp_path: Path) -> None:
        for i, ts in enumerate(["2026-01-01T00:00:00", "2026-02-01T00:00:00"]):
            run_dir = tmp_path / "runs" / f"cr-{i}"
            run_dir.mkdir(parents=True)
            manifest = {
                "collection_run": {
                    "repo_id": "my-repo",
                    "collection_run_id": f"cr-{i}",
                    "run_id": f"run-{i}",
                    "commit": "abc",
                    "branch": "main",
                    "status": "completed",
                    "started_at": ts,
                    "completed_at": ts,
                },
                "tools": [],
            }
            (run_dir / "run_manifest.json").write_text(json.dumps(manifest))

        index = build_index(tmp_path)
        assert index["total_runs"] == 2
        # Most recent first
        assert index["runs"][0]["started_at"] == "2026-02-01T00:00:00"
        assert index["runs"][1]["started_at"] == "2026-01-01T00:00:00"

    def test_malformed_manifest_skipped(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "runs" / "bad"
        run_dir.mkdir(parents=True)
        (run_dir / "run_manifest.json").write_text("not json{{{")

        index = build_index(tmp_path)
        assert index["total_runs"] == 0

    def test_index_schema_version(self, tmp_path: Path) -> None:
        index = build_index(tmp_path)
        assert index["schema_version"] == 1
        assert "updated_at" in index
        assert "total_runs" in index
        assert "runs" in index
