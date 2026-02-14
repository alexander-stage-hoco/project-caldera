from __future__ import annotations

from pathlib import Path

import os

from scripts import analyze
from scripts import evaluate


def test_resolve_results_dir_env_override(tmp_path: Path) -> None:
    os.environ["EVAL_OUTPUT_DIR"] = str(tmp_path)
    try:
        resolved = evaluate._resolve_results_dir(Path("/tmp/base"))
    finally:
        os.environ.pop("EVAL_OUTPUT_DIR", None)
    assert resolved == tmp_path


def test_resolve_commit_fallback_hash(tmp_path: Path) -> None:
    """Non-git directory returns the standard fallback commit (all zeros)."""
    from common.git_utilities import resolve_commit, FALLBACK_COMMIT
    target = tmp_path / "repo"
    target.mkdir()
    (target / "file.txt").write_text("alpha")
    commit = resolve_commit(target, None)
    assert commit == FALLBACK_COMMIT
    assert len(commit) == 40
