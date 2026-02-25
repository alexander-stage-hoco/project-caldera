"""Execution backend abstraction for running tool analysis.

Provides a clean interface for executing tools with different backends.
Currently only LocalBackend is implemented; Docker/VM backends deferred
per PRODUCTION_MODES.md.
"""
from __future__ import annotations

import os
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class ExecutionMode(Enum):
    """Available execution modes."""
    LOCAL = "local"
    # DOCKER = "docker"  # Deferred — bundle-first architecture handles this
    # VM = "vm"          # Deferred — existing Terraform flow works


@dataclass(frozen=True)
class ToolTask:
    """A single tool execution task."""
    name: str
    tool_root: Path
    extra_env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a single tool."""
    tool_name: str
    status: str  # "success" or "failed"
    duration_seconds: float
    output_path: Path
    output_exists: bool
    output_bytes: int | None
    error: str | None = None
    returncode: int | None = None


@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for a batch execution."""
    repo_path: Path
    repo_name: str
    run_id: str
    repo_id: str
    branch: str
    commit: str
    output_root: Path | None = None
    max_parallel: int = 1  # Reserved for future ThreadPoolExecutor support


def _is_git_commit(repo_path: Path, commit: str) -> bool:
    """Return True only if commit resolves as a git commit in repo_path."""
    if not commit or commit == "0" * 40:
        return False
    result = subprocess.run(
        ["git", "-C", str(repo_path), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _default_output_path(task: ToolTask, run_id: str, output_root: Path | None) -> Path:
    """Compute the expected output path for a tool task."""
    if output_root:
        return (output_root / task.name / "output.json").resolve()
    return (task.tool_root / "outputs" / run_id / "output.json").resolve()


def run_tool_make(
    tool_root: Path,
    repo_path: Path,
    repo_name: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    output_dir: Path,
    log_sink: Any,
    extra_env: dict[str, str] | None = None,
) -> None:
    """Run a tool's `make analyze` target.

    This is the extracted module-level function from the orchestrator.

    Args:
        tool_root: Path to the tool directory containing Makefile.
        repo_path: Path to the repository to analyze.
        repo_name: Repository name.
        run_id: Run identifier.
        repo_id: Repository identifier.
        branch: Branch name.
        commit: Commit SHA.
        output_dir: Directory for tool output.
        log_sink: File-like object for stdout/stderr.
        extra_env: Additional environment variables.
    """
    env = os.environ.copy()
    env.update({
        "REPO_PATH": str(repo_path),
        "REPO_NAME": repo_name,
        "RUN_ID": run_id,
        "REPO_ID": repo_id,
        "BRANCH": branch,
        "OUTPUT_DIR": str(output_dir),
    })
    env["COMMIT"] = commit if _is_git_commit(repo_path, commit) else ("0" * 40)
    if extra_env:
        env.update(extra_env)
    subprocess.run(
        ["make", "analyze"],
        cwd=tool_root,
        env=env,
        stdout=log_sink,
        stderr=log_sink,
        check=True,
    )


class ExecutionBackend(ABC):
    """Abstract base for tool execution backends."""

    @abstractmethod
    def execute_batch(
        self,
        tasks: list[ToolTask],
        config: ExecutionConfig,
        log_sink: Any,
    ) -> list[ExecutionResult]:
        """Execute a batch of tool tasks.

        Args:
            tasks: List of tool tasks to execute.
            config: Execution configuration.
            log_sink: File-like object for log output.

        Returns:
            List of ExecutionResult, one per task (in order).
        """
        ...


class LocalBackend(ExecutionBackend):
    """Execute tools locally via `make analyze`."""

    def execute_batch(
        self,
        tasks: list[ToolTask],
        config: ExecutionConfig,
        log_sink: Any,
    ) -> list[ExecutionResult]:
        """Execute all tasks sequentially on the local machine.

        Args:
            tasks: List of tool tasks to execute.
            config: Execution configuration.
            log_sink: File-like object for log output.

        Returns:
            List of ExecutionResult, one per task.
        """
        results: list[ExecutionResult] = []

        for task in tasks:
            output_path = _default_output_path(task, config.run_id, config.output_root)
            start = time.perf_counter()

            try:
                run_tool_make(
                    task.tool_root,
                    config.repo_path,
                    config.repo_name,
                    config.run_id,
                    config.repo_id,
                    config.branch,
                    config.commit,
                    output_path.parent,
                    log_sink,
                    extra_env=task.extra_env or None,
                )
                duration = time.perf_counter() - start

                if not output_path.exists():
                    raise FileNotFoundError(
                        f"{task.name} did not write output at {output_path}"
                    )

                results.append(ExecutionResult(
                    tool_name=task.name,
                    status="success",
                    duration_seconds=round(duration, 3),
                    output_path=output_path,
                    output_exists=True,
                    output_bytes=output_path.stat().st_size,
                ))
            except Exception as exc:
                duration = time.perf_counter() - start
                results.append(ExecutionResult(
                    tool_name=task.name,
                    status="failed",
                    duration_seconds=round(duration, 3),
                    output_path=output_path,
                    output_exists=output_path.exists(),
                    output_bytes=output_path.stat().st_size if output_path.exists() else None,
                    error=repr(exc),
                    returncode=getattr(exc, "returncode", None),
                ))

        return results


def get_backend(mode: ExecutionMode) -> ExecutionBackend:
    """Factory function returning the appropriate backend.

    Args:
        mode: Execution mode to use.

    Returns:
        An ExecutionBackend instance.

    Raises:
        ValueError: If mode is not supported.
    """
    if mode == ExecutionMode.LOCAL:
        return LocalBackend()
    raise ValueError(f"Unsupported execution mode: {mode.value}")
