"""Tests for scripts/collect_artifacts.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
for p in [SCRIPTS_DIR, SRC_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from collect_artifacts import (  # noqa: E402
    ToolResult,
    _find_tools,
    _is_git_repo,
    _stable_repo_id_from_path,
)


class TestIsGitRepo:
    def test_is_git_repo_false_for_tmp(self, tmp_path: Path) -> None:
        assert _is_git_repo(tmp_path) is False

    def test_is_git_repo_true_for_git_dir(self, tmp_path: Path) -> None:
        subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
        assert _is_git_repo(tmp_path) is True

    def test_is_git_repo_handles_nonexistent_path(self) -> None:
        assert _is_git_repo(Path("/nonexistent/path/xyz")) is False


class TestStableRepoId:
    def test_stable_repo_id_deterministic(self, tmp_path: Path) -> None:
        id1 = _stable_repo_id_from_path(tmp_path)
        id2 = _stable_repo_id_from_path(tmp_path)
        assert id1 == id2

    def test_stable_repo_id_contains_dir_name(self, tmp_path: Path) -> None:
        repo_id = _stable_repo_id_from_path(tmp_path)
        assert tmp_path.resolve().name in repo_id

    def test_stable_repo_id_differs_for_different_paths(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "repo-a"
        dir_b = tmp_path / "repo-b"
        dir_a.mkdir()
        dir_b.mkdir()
        assert _stable_repo_id_from_path(dir_a) != _stable_repo_id_from_path(dir_b)


class TestFindTools:
    def test_find_tools_discovers_tool_dirs(self, tmp_path: Path) -> None:
        for name in ["scc", "lizard", "trivy"]:
            tool_dir = tmp_path / name
            tool_dir.mkdir()
            (tool_dir / "Makefile").touch()
        # A dir without Makefile should be skipped
        (tmp_path / "not-a-tool").mkdir()

        tools = _find_tools(tmp_path)
        assert tools == ["lizard", "scc", "trivy"]

    def test_find_tools_empty_dir(self, tmp_path: Path) -> None:
        assert _find_tools(tmp_path) == []

    def test_find_tools_ignores_files(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").touch()
        (tmp_path / "Makefile").touch()
        assert _find_tools(tmp_path) == []


class TestToolResult:
    def test_tool_result_frozen(self) -> None:
        r = ToolResult(name="scc", status="success", duration_seconds=1.5, output_json="scc/output.json", log_path="scc/execution.log")
        assert r.name == "scc"
        assert r.status == "success"
        assert r.duration_seconds == 1.5
