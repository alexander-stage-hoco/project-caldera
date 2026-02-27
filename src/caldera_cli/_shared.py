"""Shared utilities for all Caldera CLI commands."""

from __future__ import annotations

import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from rich.console import Console

console = Console()

DEFAULT_DB_PATH = Path.home() / ".caldera" / "caldera_sot.duckdb"


@lru_cache(maxsize=1)
def find_project_root() -> Path:
    """Walk up from cwd to find the Caldera project root.

    Identified by having both ``CLAUDE.md`` and ``src/tools/`` present.
    """
    candidate = Path.cwd().resolve()
    for _ in range(20):  # safety limit
        if (candidate / "CLAUDE.md").is_file() and (candidate / "src" / "tools").is_dir():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    console.print("[red]Error:[/red] Could not locate Caldera project root (need CLAUDE.md + src/tools/)")
    raise SystemExit(1)


def get_db_path(db: Path | None = None) -> Path:
    """Resolve database path from explicit arg, env vars, or default."""
    if db is not None:
        return db
    env = os.environ.get("CALDERA_DB_PATH") or os.environ.get("DB_PATH")
    if env:
        return Path(env)
    return DEFAULT_DB_PATH


def run_make(target: str, variables: dict[str, str] | None = None) -> int:
    """Run a Make target from the project root. Returns exit code."""
    root = find_project_root()
    cmd = ["make", "-C", str(root), target]
    for key, value in (variables or {}).items():
        cmd.append(f"{key}={value}")
    result = subprocess.run(cmd)
    return result.returncode


def run_script(name: str, args: list[str] | None = None) -> int:
    """Run a script from the project's scripts/ directory. Returns exit code."""
    root = find_project_root()
    python = str(root / ".venv" / "bin" / "python")
    script = str(root / "scripts" / name)
    cmd = [python, script] + (args or [])
    result = subprocess.run(cmd)
    return result.returncode


def get_venv_python() -> str:
    """Return path to the project venv Python interpreter."""
    root = find_project_root()
    return str(root / ".venv" / "bin" / "python")


def ensure_src_on_path() -> None:
    """Add src/ to sys.path so insights and other packages are importable."""
    root = find_project_root()
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
