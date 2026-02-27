"""Execution backend abstraction for running tool analysis.

Provides a clean interface for executing tools with different backends.
LocalBackend runs tools via ``make analyze``; DockerBackend runs each tool
in its pre-built container.  Both support parallel execution via
``_execute_parallel`` when ``ExecutionConfig.max_parallel > 1``.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class ExecutionMode(Enum):
    """Available execution modes."""
    LOCAL = "local"
    DOCKER = "docker"
    # VM = "vm"  # Deferred — existing Terraform flow works


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
    max_parallel: int = 1


@dataclass(frozen=True)
class DockerConfig:
    """Docker-specific configuration for DockerBackend."""
    image_prefix: str = "caldera-tool-"
    network: str = "caldera_default"
    repo_volume: str = "caldera-repo"
    artifacts_volume: str = "caldera-artifacts"
    container_repo_path: str = "/repo"
    container_artifacts_path: str = "/artifacts"


# Callback invoked after each tool completes: (tool_name, status, duration_seconds)
ProgressCallback = Callable[[str, str, float], None]


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


def _execute_parallel(
    tasks: list[ToolTask],
    config: ExecutionConfig,
    execute_one: Callable[[ToolTask], ExecutionResult],
    on_complete: ProgressCallback | None = None,
) -> list[ExecutionResult]:
    """Execute tasks sequentially or in parallel, preserving original order.

    When ``config.max_parallel <= 1``, tasks run sequentially in a simple loop.
    Otherwise a :class:`~concurrent.futures.ThreadPoolExecutor` is used with
    ``max_workers=config.max_parallel``.

    Args:
        tasks: Tool tasks to execute.
        config: Execution config (``max_parallel`` controls concurrency).
        execute_one: Callable that runs a single task and returns its result.
        on_complete: Optional callback invoked after each task finishes.

    Returns:
        List of :class:`ExecutionResult` in the same order as *tasks*.
    """
    if config.max_parallel <= 1:
        # Sequential path
        results: list[ExecutionResult] = []
        for task in tasks:
            try:
                result = execute_one(task)
            except Exception as exc:
                result = ExecutionResult(
                    tool_name=task.name,
                    status="failed",
                    duration_seconds=0.0,
                    output_path=_default_output_path(task, config.run_id, config.output_root),
                    output_exists=False,
                    output_bytes=None,
                    error=repr(exc),
                )
            results.append(result)
            if on_complete:
                on_complete(result.tool_name, result.status, result.duration_seconds)
        return results

    # Parallel path
    result_map: dict[str, ExecutionResult] = {}
    with ThreadPoolExecutor(max_workers=config.max_parallel) as pool:
        future_to_task = {
            pool.submit(execute_one, task): task
            for task in tasks
        }
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
            except Exception as exc:
                result = ExecutionResult(
                    tool_name=task.name,
                    status="failed",
                    duration_seconds=0.0,
                    output_path=_default_output_path(task, config.run_id, config.output_root),
                    output_exists=False,
                    output_bytes=None,
                    error=repr(exc),
                )
            result_map[task.name] = result
            if on_complete:
                on_complete(result.tool_name, result.status, result.duration_seconds)

    # Preserve original task order
    return [result_map[task.name] for task in tasks]


class ExecutionBackend(ABC):
    """Abstract base for tool execution backends."""

    @abstractmethod
    def execute_batch(
        self,
        tasks: list[ToolTask],
        config: ExecutionConfig,
        log_sink: Any,
        on_complete: ProgressCallback | None = None,
    ) -> list[ExecutionResult]:
        """Execute a batch of tool tasks.

        Args:
            tasks: List of tool tasks to execute.
            config: Execution configuration.
            log_sink: File-like object for log output.
            on_complete: Optional progress callback per task.

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
        on_complete: ProgressCallback | None = None,
    ) -> list[ExecutionResult]:
        """Execute all tasks on the local machine.

        When ``config.max_parallel > 1``, tasks run in parallel threads.
        A threading lock protects *log_sink* writes.
        """
        lock = threading.Lock() if config.max_parallel > 1 else None

        def execute_one(task: ToolTask) -> ExecutionResult:
            return self._execute_one(task, config, log_sink, lock)

        return _execute_parallel(tasks, config, execute_one, on_complete)

    @staticmethod
    def _execute_one(
        task: ToolTask,
        config: ExecutionConfig,
        log_sink: Any,
        lock: threading.Lock | None = None,
    ) -> ExecutionResult:
        """Run a single tool task via ``make analyze``."""
        output_path = _default_output_path(task, config.run_id, config.output_root)
        start = time.perf_counter()

        try:
            sink = log_sink
            if lock is not None:
                # In parallel mode, redirect to DEVNULL to avoid interleaved output.
                # Per-tool logs are written by the tools themselves.
                sink = subprocess.DEVNULL

            run_tool_make(
                task.tool_root,
                config.repo_path,
                config.repo_name,
                config.run_id,
                config.repo_id,
                config.branch,
                config.commit,
                output_path.parent,
                sink,
                extra_env=task.extra_env or None,
            )
            duration = time.perf_counter() - start

            if not output_path.exists():
                raise FileNotFoundError(
                    f"{task.name} did not write output at {output_path}"
                )

            return ExecutionResult(
                tool_name=task.name,
                status="success",
                duration_seconds=round(duration, 3),
                output_path=output_path,
                output_exists=True,
                output_bytes=output_path.stat().st_size,
            )
        except Exception as exc:
            duration = time.perf_counter() - start
            return ExecutionResult(
                tool_name=task.name,
                status="failed",
                duration_seconds=round(duration, 3),
                output_path=output_path,
                output_exists=output_path.exists(),
                output_bytes=output_path.stat().st_size if output_path.exists() else None,
                error=repr(exc),
                returncode=getattr(exc, "returncode", None),
            )


class DockerBackend(ExecutionBackend):
    """Execute tools inside pre-built Docker containers.

    Mirrors the container invocation pattern from ``scripts/docker_runner.py``
    but returns :class:`ExecutionResult` objects and delegates parallel
    scheduling to :func:`_execute_parallel`.
    """

    def __init__(self, docker_config: DockerConfig | None = None) -> None:
        self._dc = docker_config or DockerConfig()

    def execute_batch(
        self,
        tasks: list[ToolTask],
        config: ExecutionConfig,
        log_sink: Any,
        on_complete: ProgressCallback | None = None,
    ) -> list[ExecutionResult]:
        """Execute all tasks as Docker containers."""
        def execute_one(task: ToolTask) -> ExecutionResult:
            return self._run_container(task, config)

        return _execute_parallel(tasks, config, execute_one, on_complete)

    def _run_container(self, task: ToolTask, config: ExecutionConfig) -> ExecutionResult:
        """Run a single tool in its Docker container."""
        output_path = _default_output_path(task, config.run_id, config.output_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # The tool container sees the artifacts volume at /artifacts.
        # OUTPUT_DIR tells the tool where to write inside the container.
        artifacts_subdir = str(
            Path(self._dc.container_artifacts_path) / config.repo_id / config.run_id / task.name
        )

        cmd: list[str] = [
            "docker", "run", "--rm",
            "--network", self._dc.network,
            "-v", f"{self._dc.repo_volume}:{self._dc.container_repo_path}:ro",
            "-v", f"{self._dc.artifacts_volume}:{self._dc.container_artifacts_path}",
            f"{self._dc.image_prefix}{task.name}",
            f"RUN_ID={config.run_id}",
            f"REPO_ID={config.repo_id}",
            f"REPO_NAME={config.repo_name}",
            f"BRANCH={config.branch}",
            f"COMMIT={config.commit}",
            f"OUTPUT_DIR={artifacts_subdir}",
        ]

        start = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, check=False)
        duration = time.perf_counter() - start

        # Write execution log
        log_path = output_path.parent / "execution.log"
        with log_path.open("w", encoding="utf-8") as log:
            log.write(proc.stdout.decode("utf-8", errors="replace"))
            log.write(proc.stderr.decode("utf-8", errors="replace"))

        if proc.returncode != 0:
            return ExecutionResult(
                tool_name=task.name,
                status="failed",
                duration_seconds=round(duration, 3),
                output_path=output_path,
                output_exists=output_path.exists(),
                output_bytes=output_path.stat().st_size if output_path.exists() else None,
                error=f"Container exited with code {proc.returncode}",
                returncode=proc.returncode,
            )

        if not output_path.exists():
            return ExecutionResult(
                tool_name=task.name,
                status="failed",
                duration_seconds=round(duration, 3),
                output_path=output_path,
                output_exists=False,
                output_bytes=None,
                error=f"{task.name} container did not produce output at {output_path}",
                returncode=proc.returncode,
            )

        return ExecutionResult(
            tool_name=task.name,
            status="success",
            duration_seconds=round(duration, 3),
            output_path=output_path,
            output_exists=True,
            output_bytes=output_path.stat().st_size,
        )


def get_backend(
    mode: ExecutionMode,
    docker_config: DockerConfig | None = None,
) -> ExecutionBackend:
    """Factory function returning the appropriate backend.

    Args:
        mode: Execution mode to use.
        docker_config: Docker-specific config (required for DOCKER mode).

    Returns:
        An ExecutionBackend instance.

    Raises:
        ValueError: If mode is not supported.
    """
    if mode == ExecutionMode.LOCAL:
        return LocalBackend()
    if mode == ExecutionMode.DOCKER:
        return DockerBackend(docker_config)
    raise ValueError(f"Unsupported execution mode: {mode.value}")
