from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from dataclasses import dataclass


def _format_duration(seconds: float) -> str:
    return f"{seconds:.2f}s"


class OrchestratorLogger:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = log_path.open("a", encoding="utf-8")

    @property
    def log_path(self) -> Path:
        return self._log_path

    def close(self) -> None:
        self._handle.close()

    def info(self, message: str) -> None:
        print(message)
        self._handle.write(message + "\n")
        self._handle.flush()

    def log_pipe(self):
        return self._handle


def _subprocess_run_with_retry(
    *args: Any, retries: int = 3, delay: float = 1.0, **kwargs: Any,
) -> subprocess.CompletedProcess:
    """subprocess.run with retry on transient BlockingIOError (EAGAIN)."""
    for attempt in range(retries):
        try:
            return subprocess.run(*args, **kwargs)
        except BlockingIOError:
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))
    raise RuntimeError("unreachable")


def _is_fallback_commit(commit: str) -> bool:
    """Check if commit is a fallback value (all zeros or empty)."""
    return not commit or commit == "0" * 40


def _compute_content_hash(repo_path: Path) -> str:
    """Compute a deterministic 40-hex hash from repo file paths and contents."""
    h = hashlib.sha1(usedforsecurity=False)
    for f in sorted(repo_path.rglob("*")):
        if f.is_file():
            rel = f.relative_to(repo_path).as_posix()
            h.update(f"{rel}\n".encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def _commit_is_git_commit(repo_path: Path, commit: str) -> bool:
    """Return True only if commit resolves as a git commit in repo_path."""
    if _is_fallback_commit(commit):
        return False
    result = _subprocess_run_with_retry(
        ["git", "-C", str(repo_path), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def run_tool_make(
    tool_root: Path,
    repo_path: Path,
    repo_name: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    output_dir: Path,
    logger: OrchestratorLogger,
    extra_env: dict[str, str] | None = None,
) -> None:
    env = os.environ.copy()
    env.update(
        {
            "REPO_PATH": str(repo_path),
            "REPO_NAME": repo_name,
            "RUN_ID": run_id,
            "REPO_ID": repo_id,
            "BRANCH": branch,
            "OUTPUT_DIR": str(output_dir),
        }
    )
    # Export COMMIT only when it is a real git commit in the target repo.
    env["COMMIT"] = commit if _commit_is_git_commit(repo_path, commit) else ("0" * 40)
    if extra_env:
        env.update(extra_env)
    _subprocess_run_with_retry(
        ["make", "analyze"],
        cwd=tool_root,
        env=env,
        stdout=logger.log_pipe(),
        stderr=logger.log_pipe(),
        check=True,
    )


def _default_output_path(tool_config: Any, run_id: str, output_root: Path | None) -> Path:
    if output_root:
        return (output_root / tool_config.name / "output.json").resolve()
    return (Path(tool_config.path) / "outputs" / run_id / "output.json").resolve()


def _discover_outputs(output_root: Path, known_tool_names: set[str]) -> dict[str, Path]:
    """Discover tool output.json files under a standard output_root layout."""
    names = known_tool_names | {"coverage-ingest"}
    outputs: dict[str, Path] = {}
    for tool_name in sorted(names):
        candidate = (output_root / tool_name / "output.json").resolve()
        if candidate.exists():
            outputs[tool_name] = candidate
    return outputs


def _safe_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
