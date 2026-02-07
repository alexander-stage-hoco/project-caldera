from __future__ import annotations

from pathlib import Path
import sys

# Add src/ to path for common imports
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from common.git_utilities import resolve_commit


def test_analyze_commit_fallback_hash(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')\n")
    commit = resolve_commit(repo, "", None)
    assert len(commit) == 40
    assert commit == resolve_commit(repo, "", None)


def test_function_analyzer_commit_fallback_hash(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.js").write_text("function demo() { return 1; }\n")
    commit = resolve_commit(repo, None, None)
    assert len(commit) == 40
    assert commit == resolve_commit(repo, None, None)
