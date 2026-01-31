from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts import analyze
from scripts import function_analyzer


def test_analyze_commit_fallback_hash(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')\n")
    commit = analyze._resolve_commit(repo, "", None)
    assert len(commit) == 40
    assert commit == analyze._resolve_commit(repo, "", None)


def test_function_analyzer_commit_fallback_hash(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.js").write_text("function demo() { return 1; }\n")
    commit = function_analyzer._resolve_commit(repo, None, None)
    assert len(commit) == 40
    assert commit == function_analyzer._resolve_commit(repo, None, None)
