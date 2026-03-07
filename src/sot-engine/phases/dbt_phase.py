from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from phases.utilities import OrchestratorLogger, _subprocess_run_with_retry


def _resolve_dbt_cmd(dbt_bin: Path, repo_root: Path) -> list[str]:
    if not dbt_bin.is_absolute():
        dbt_bin = repo_root / dbt_bin
    if dbt_bin.exists():
        return [str(dbt_bin)]
    return [sys.executable, "-m", "dbt.cli.main"]


def run_dbt(
    dbt_bin: Path,
    dbt_project_dir: Path,
    profiles_dir: Path,
    logger: OrchestratorLogger,
    target_path: str = "~/.caldera/dbt_target",
    log_path: str = "~/.caldera/dbt_logs",
    dbt_summary: dict[str, Any] | None = None,
    db_path: Path | None = None,
    continue_on_test_failure: bool = False,
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    if not dbt_project_dir.is_absolute():
        dbt_project_dir = repo_root / dbt_project_dir
    if not profiles_dir.is_absolute():
        profiles_dir = repo_root / profiles_dir
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(profiles_dir)
    if db_path is not None:
        env["CALDERA_DB_PATH"] = str(db_path)
    dbt_cmd = _resolve_dbt_cmd(dbt_bin, repo_root)
    phases = [
        ("run", [*dbt_cmd, "run", "--target-path", target_path, "--log-path", log_path]),
        ("test", [*dbt_cmd, "test", "--target-path", target_path, "--log-path", log_path]),
    ]
    for phase_name, cmd in phases:
        start = time.perf_counter()
        if dbt_summary is not None:
            dbt_summary.setdefault("phases", [])
            dbt_summary["phases"].append(
                {
                    "phase": phase_name,
                    "status": "running",
                    "duration_seconds": None,
                    "returncode": None,
                    "cmd": cmd,
                }
            )
        try:
            _subprocess_run_with_retry(
                cmd,
                cwd=str(dbt_project_dir),
                env=env,
                stdout=logger.log_pipe(),
                stderr=logger.log_pipe(),
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            duration = time.perf_counter() - start
            if dbt_summary is not None:
                dbt_summary["phases"][-1].update(
                    {
                        "status": "failed",
                        "duration_seconds": round(duration, 3),
                        "returncode": exc.returncode,
                    }
                )
            if continue_on_test_failure and phase_name == "test":
                logger.info(f"WARNING: dbt test failed (exit {exc.returncode}) but continuing (continue_on_test_failure=True)")
            else:
                raise
        else:
            duration = time.perf_counter() - start
            if dbt_summary is not None:
                dbt_summary["phases"][-1].update(
                    {
                        "status": "success",
                        "duration_seconds": round(duration, 3),
                        "returncode": 0,
                    }
                )
