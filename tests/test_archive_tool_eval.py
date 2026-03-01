"""Tests for scripts/archive_tool_eval.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from archive_tool_eval import archive_tool, _update_index


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tool_dir(tmp_path: Path) -> Path:
    """Bare tool directory with no evaluation results."""
    return tmp_path / "my-tool"


@pytest.fixture()
def tool_dir_with_results(tmp_path: Path) -> Path:
    """Tool directory with two JSON result files."""
    td = tmp_path / "my-tool"
    results = td / "evaluation" / "results"
    results.mkdir(parents=True)
    (results / "programmatic_results.json").write_text(
        json.dumps({"overall_score": 0.85, "checks": 10})
    )
    (results / "llm_results.json").write_text(
        json.dumps({"score": 0.72, "judges": 4})
    )
    return td


# ---------------------------------------------------------------------------
# archive_tool tests
# ---------------------------------------------------------------------------

class TestArchiveTool:
    def test_no_results_dir(self, tool_dir: Path) -> None:
        """No evaluation/results/ directory → returns None."""
        tool_dir.mkdir(parents=True)
        assert archive_tool(tool_dir, commit="abc123") is None

    def test_empty_results(self, tool_dir: Path) -> None:
        """Results dir exists but has no JSON files → returns None."""
        results = tool_dir / "evaluation" / "results"
        results.mkdir(parents=True)
        assert archive_tool(tool_dir, commit="abc123") is None

    def test_copies_files(self, tool_dir_with_results: Path) -> None:
        """JSON files are copied into history/<timestamp>/."""
        manifest = archive_tool(tool_dir_with_results, commit="abc123")
        assert manifest is not None

        ts = manifest["timestamp"]
        history = tool_dir_with_results / "evaluation" / "history" / ts
        assert history.is_dir()
        assert (history / "programmatic_results.json").exists()
        assert (history / "llm_results.json").exists()
        assert (history / "eval_manifest.json").exists()

    def test_manifest_structure(self, tool_dir_with_results: Path) -> None:
        """Manifest contains required keys."""
        manifest = archive_tool(tool_dir_with_results, commit="deadbeef")
        assert manifest is not None
        assert manifest["schema_version"] == 1
        assert manifest["tool"] == "my-tool"
        assert manifest["commit"] == "deadbeef"
        assert isinstance(manifest["timestamp"], str)
        assert set(manifest["files"]) == {
            "llm_results.json",
            "programmatic_results.json",
        }
        assert "archived_at" in manifest

    def test_extracts_overall_score(self, tool_dir_with_results: Path) -> None:
        """Result with `overall_score` key → appears in manifest scores."""
        manifest = archive_tool(tool_dir_with_results, commit="abc123")
        assert manifest is not None
        assert manifest["scores"]["programmatic_results"] == 0.85

    def test_extracts_score_key(self, tool_dir_with_results: Path) -> None:
        """Result with `score` key (no overall_score) → appears in manifest scores."""
        manifest = archive_tool(tool_dir_with_results, commit="abc123")
        assert manifest is not None
        assert manifest["scores"]["llm_results"] == 0.72

    def test_corrupted_json_resilient(self, tmp_path: Path) -> None:
        """Malformed JSON in results doesn't crash archive_tool."""
        td = tmp_path / "bad-tool"
        results = td / "evaluation" / "results"
        results.mkdir(parents=True)
        (results / "broken.json").write_text("{not valid json!!!")
        (results / "good.json").write_text(json.dumps({"score": 0.5}))

        manifest = archive_tool(td, commit="abc123")
        assert manifest is not None
        # The good file score is still extracted
        assert manifest["scores"]["good"] == 0.5
        # The broken file is still listed as copied
        assert "broken.json" in manifest["files"]


# ---------------------------------------------------------------------------
# _update_index tests
# ---------------------------------------------------------------------------

class TestUpdateIndex:
    def test_creates_and_appends(self, tmp_path: Path) -> None:
        """First call creates index, second call appends."""
        eval_dir = tmp_path / "evaluation"
        eval_dir.mkdir()

        m1 = {
            "timestamp": "20260301T120000Z",
            "commit": "aaa",
            "scores": {"prog": 0.9},
            "files": ["prog.json"],
        }
        _update_index(eval_dir, m1)

        index_path = eval_dir / "eval_index.json"
        assert index_path.exists()
        idx = json.loads(index_path.read_text())
        assert len(idx["entries"]) == 1
        assert idx["entries"][0]["commit"] == "aaa"
        assert "last_updated" in idx

        m2 = {
            "timestamp": "20260301T130000Z",
            "commit": "bbb",
            "files": ["prog.json"],
        }
        _update_index(eval_dir, m2)

        idx = json.loads(index_path.read_text())
        assert len(idx["entries"]) == 2
        assert idx["entries"][1]["commit"] == "bbb"
        # Missing scores key → empty dict
        assert idx["entries"][1]["scores"] == {}
