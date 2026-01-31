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
    target = tmp_path / "repo"
    target.mkdir()
    (target / "file.txt").write_text("alpha")
    commit = analyze._resolve_commit(target, "", None)
    assert len(commit) == 40
    assert commit == analyze._resolve_commit(target, "", None)
