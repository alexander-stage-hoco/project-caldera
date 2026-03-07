from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from execution import (
    ExecutionBackend,
    ExecutionConfig,
    LocalBackend,
    ToolTask,
)
from tool_registry import get_execution_tools

from phases.utilities import OrchestratorLogger, _default_output_path


@dataclass
class ToolConfig:
    """Configuration for a tool to be run by the orchestrator."""
    name: str
    path: str
    extra_env: dict[str, str] | None = None


class ToolPhaseError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        outputs: dict[str, Path],
        tool_summaries: list[dict[str, Any]],
    ) -> None:
        super().__init__(message)
        self.outputs = outputs
        self.tool_summaries = tool_summaries


# Tool configurations derived from the unified tool registry
TOOL_CONFIGS = [
    ToolConfig(t.name, t.path, t.extra_env or None)
    for t in get_execution_tools()
]


def _run_tools(
    tool_configs: list[ToolConfig],
    repo_path: Path,
    repo_name: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    logger: OrchestratorLogger,
    output_root: Path | None,
    continue_on_failure: bool = False,
    show_progress: bool = True,
    backend: ExecutionBackend | None = None,
    max_parallel: int = 1,
) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    """Run all configured tools and return (outputs, per-tool summaries).

    Delegates execution to the provided backend (defaults to LocalBackend).
    Handles progress display, JSON validation, and failure semantics.

    When ``max_parallel > 1``, all tasks are dispatched as a single batch via
    the backend, which handles concurrency internally.  When ``max_parallel == 1``
    (default), tools run one at a time with per-tool progress spinners.
    """
    if backend is None:
        backend = LocalBackend()

    outputs: dict[str, Path] = {}
    tool_summaries: list[dict[str, Any]] = []
    total_tools = len(tool_configs)
    use_rich = show_progress and RICH_AVAILABLE and sys.stdout.isatty()
    console = Console() if use_rich else None

    # Convert ToolConfig list to ToolTask list for the backend
    tasks = [
        ToolTask(
            name=tc.name,
            tool_root=Path(tc.path),
            extra_env=tc.extra_env or {},
        )
        for tc in tool_configs
    ]
    exec_config = ExecutionConfig(
        repo_path=repo_path,
        repo_name=repo_name,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        output_root=output_root,
        max_parallel=max_parallel,
    )

    if max_parallel > 1:
        # ── Parallel mode: dispatch all tasks in one batch ──────────────
        import threading as _threading
        completed_count = 0
        _lock = _threading.Lock()

        def on_complete(name: str, status: str, dur: float) -> None:
            nonlocal completed_count
            with _lock:
                completed_count += 1
                logger.info(f"[{completed_count}/{total_tools}] {name}: {status} ({dur:.1f}s)")

        all_results = backend.execute_batch(
            tasks, exec_config, logger.log_pipe(), on_complete=on_complete,
        )

        # Post-process results: validate JSON, populate outputs/tool_summaries
        for result in all_results:
            if result.status == "success":
                output_path = result.output_path
                valid = True
                error = None
                if not output_path.exists():
                    valid = False
                    error = f"{result.tool_name} did not write expected output.json at {output_path}"
                else:
                    try:
                        json.loads(output_path.read_text(encoding="utf-8"))
                    except Exception as exc:
                        valid = False
                        error = f"{result.tool_name} wrote invalid JSON: {exc!r}"

                if valid:
                    outputs[result.tool_name] = output_path
                    tool_summaries.append({
                        "tool_name": result.tool_name,
                        "status": "success",
                        "duration_seconds": round(result.duration_seconds, 3),
                        "output_path": str(output_path),
                        "output_exists": True,
                        "output_bytes": output_path.stat().st_size,
                        "error": None,
                    })
                else:
                    tool_summaries.append({
                        "tool_name": result.tool_name,
                        "status": "failed",
                        "duration_seconds": round(result.duration_seconds, 3),
                        "output_path": str(output_path),
                        "output_exists": output_path.exists(),
                        "output_bytes": output_path.stat().st_size if output_path.exists() else None,
                        "error": error,
                    })
                    if not continue_on_failure:
                        raise ToolPhaseError(
                            f"Tool failed: {result.tool_name}",
                            outputs=outputs,
                            tool_summaries=tool_summaries,
                        )
            else:
                tool_summaries.append({
                    "tool_name": result.tool_name,
                    "status": "failed",
                    "duration_seconds": round(result.duration_seconds, 3),
                    "output_path": str(result.output_path),
                    "output_exists": result.output_exists,
                    "output_bytes": result.output_bytes,
                    "error": result.error,
                })
                if not continue_on_failure:
                    raise ToolPhaseError(
                        f"Tool failed: {result.tool_name}",
                        outputs=outputs,
                        tool_summaries=tool_summaries,
                    )

        return outputs, tool_summaries

    # ── Sequential mode (max_parallel == 1): original per-tool logic ────────
    for idx, (tool, task) in enumerate(zip(tool_configs, tasks), 1):
        tool_start = time.perf_counter()

        try:
            if use_rich and console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True,
                ) as progress:
                    progress.add_task(f"[{idx}/{total_tools}] {tool.name}...", total=None)
                    results = backend.execute_batch([task], exec_config, logger.log_pipe())
                duration = time.perf_counter() - tool_start
                console.print(f"[green]✓[/] [{idx}/{total_tools}] {tool.name} ({duration:.1f}s)")
            else:
                results = backend.execute_batch([task], exec_config, logger.log_pipe())
                duration = time.perf_counter() - tool_start
                logger.info(f"[{idx}/{total_tools}] {tool.name} ({duration:.1f}s)")

            result = results[0]

            if result.status == "failed":
                raise RuntimeError(result.error or f"{tool.name} failed")

            output_path = result.output_path
            if not output_path.exists():
                raise FileNotFoundError(
                    f"{tool.name} did not write expected output.json at {output_path}"
                )
            try:
                json.loads(output_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise ValueError(
                    f"{tool.name} wrote invalid JSON at {output_path}: {exc!r}"
                ) from exc

            outputs[tool.name] = output_path
            tool_summaries.append(
                {
                    "tool_name": tool.name,
                    "status": "success",
                    "duration_seconds": round(result.duration_seconds, 3),
                    "output_path": str(output_path),
                    "output_exists": True,
                    "output_bytes": output_path.stat().st_size,
                    "error": None,
                }
            )
        except Exception as exc:
            duration = time.perf_counter() - tool_start
            returncode = getattr(exc, "returncode", None)
            cmd = getattr(exc, "cmd", None)
            output_path = _default_output_path(tool, run_id, output_root)
            tool_summaries.append(
                {
                    "tool_name": tool.name,
                    "status": "failed",
                    "duration_seconds": round(duration, 3),
                    "output_path": str(output_path),
                    "output_exists": output_path.exists(),
                    "output_bytes": (output_path.stat().st_size if output_path.exists() else None),
                    "returncode": returncode,
                    "cmd": cmd,
                    "error": repr(exc),
                }
            )
            if not continue_on_failure:
                raise ToolPhaseError(
                    f"Tool failed: {tool.name}",
                    outputs=outputs,
                    tool_summaries=tool_summaries,
                ) from exc
            logger.info(f"[{idx}/{total_tools}] {tool.name} FAILED: {exc!r}")
            continue

    return outputs, tool_summaries
