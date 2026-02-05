from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import analyze


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("test")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True)
    env = {
        **dict(
            GIT_AUTHOR_NAME="Test",
            GIT_AUTHOR_EMAIL="test@example.com",
            GIT_COMMITTER_NAME="Test",
            GIT_COMMITTER_EMAIL="test@example.com",
        ),
        **dict(os.environ),
    }
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True, env=env)


def test_analyze_directory_with_subrepos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "root"
    repo_a = repo_root / "repo-a"
    repo_b = repo_root / "repo-b"
    _init_repo(repo_a)
    _init_repo(repo_b)

    out_dir = tmp_path / "out"

    def fake_analyze_repository(_: Path) -> analyze.RepositoryAnalysis:
        return analyze.RepositoryAnalysis(
            git_sizer_version="1.0.0",
            duration_ms=1,
            metrics=analyze.RepositoryMetrics(),
            violations=[],
            health_grade="A",
            lfs_candidates=[],
            raw_output={},
        )

    def fake_build_analysis_data(*, analysis: analyze.RepositoryAnalysis, repo_name: str) -> dict:
        return {
            "tool": "git-sizer",
            "repo_name": repo_name,
            "health_grade": analysis.health_grade,
        }

    monkeypatch.setattr(analyze, "analyze_repository", fake_analyze_repository)
    monkeypatch.setattr(analyze, "build_analysis_data", fake_build_analysis_data)

    argv = [
        "analyze.py",
        "--repo-path",
        str(repo_root),
        "--repo-name",
        "root",
        "--output-dir",
        str(out_dir),
        "--run-id",
        "run-1",
        "--repo-id",
        "repo-1",
        "--branch",
        "main",
        "--commit",
        "0" * 40,
        "--exit-zero",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as exc_info:
        analyze.main()
    assert exc_info.value.code == 0

    primary = out_dir / "output.json"
    assert primary.exists()
    payload = json.loads(primary.read_text())
    assert payload["metadata"]["tool_name"] == "git-sizer"

    assert (out_dir / "repo-a" / "output.json").exists()
    assert (out_dir / "repo-b" / "output.json").exists()
