from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import duckdb

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

_log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from execution import (
    DockerConfig,
    ExecutionBackend,
    ExecutionConfig,
    ExecutionMode,
    LocalBackend,
    ToolTask,
    get_backend,
)
from persistence.adapters import CoverageIngestAdapter, DependenseeAdapter, DevskimAdapter, DotcoverAdapter, GitBlameScannerAdapter, GitFameAdapter, GitSizerAdapter, GitleaksAdapter, LayoutScannerAdapter, LizardAdapter, PmdCpdAdapter, RoslynAnalyzersAdapter, ScancodeAdapter, SccAdapter, SemgrepAdapter, SonarqubeAdapter, SymbolScannerAdapter, TrivyAdapter
from persistence.adapters.base_adapter import BaseAdapter
from persistence.entities import CollectionRun, ToolRun
from persistence.quality import DataQualityChecker
from persistence.repositories import (
    BaseRepository,
    CollectionRunRepository,
    CoverageRepository,
    DependenseeRepository,
    DevskimRepository,
    DotcoverRepository,
    GitBlameRepository,
    GitFameRepository,
    GitSizerRepository,
    GitleaksRepository,
    LayoutRepository,
    LizardRepository,
    PmdCpdRepository,
    RoslynRepository,
    ScancodeRepository,
    SccRepository,
    SemgrepRepository,
    SonarqubeRepository,
    SymbolScannerRepository,
    ToolRunRepository,
    TrivyRepository,
)


@dataclass
class ToolConfig:
    """Configuration for a tool to be run by the orchestrator."""
    name: str
    path: str
    extra_env: dict[str, str] | None = None


@dataclass
class ToolIngestionConfig:
    """Configuration for ingesting a tool's output."""
    name: str
    adapter_class: type[BaseAdapter]
    repo_class: type[BaseRepository] | None  # None for layout adapter
    validate_metadata: bool = True  # Whether to validate standard metadata structure


def ensure_schema(conn: duckdb.DuckDBPyConnection, schema_path: Path) -> None:
    exists = conn.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'lz_tool_runs'
        """
    ).fetchone()
    if not exists:
        conn.execute(schema_path.read_text())
        return

    collection_exists = conn.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'lz_collection_runs'
        """
    ).fetchone()
    if not collection_exists:
        raise RuntimeError(
            "lz_collection_runs missing. Apply schema.sql before running orchestrator."
        )

    _apply_migrations(conn)


# -- Schema migrations --------------------------------------------------------
# Each entry is an idempotent ALTER TABLE statement for columns added after the
# initial schema.sql release.  DuckDB supports ADD COLUMN IF NOT EXISTS.

_MIGRATIONS: tuple[str, ...] = (
    "ALTER TABLE lz_layout_files ADD COLUMN IF NOT EXISTS stable_fingerprint VARCHAR",
)


def _apply_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Run idempotent schema migrations on an existing database."""
    for stmt in _MIGRATIONS:
        try:
            conn.execute(stmt)
        except Exception as exc:
            _log.warning("Migration skipped (%s): %s", stmt.split()[:5], exc)


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_payload(
    metadata: dict,
    repo_id: str,
    run_id: str,
    *,
    expected_commit: str | None = None,
    expected_tool: str | None = None,
) -> None:
    if metadata.get("repo_id") != repo_id:
        raise ValueError("repo_id mismatch between orchestrator and payload")
    if metadata.get("run_id") != run_id:
        raise ValueError("run_id mismatch between orchestrator and payload")
    if expected_commit and not _is_fallback_commit(expected_commit):
        payload_commit = metadata.get("commit", "")
        if payload_commit and not _is_fallback_commit(payload_commit):
            if payload_commit != expected_commit:
                raise ValueError(
                    f"commit mismatch: orchestrator={expected_commit[:8]}… "
                    f"payload={payload_commit[:8]}…"
                )
    if expected_tool:
        payload_tool = metadata.get("tool_name", "")
        if payload_tool and payload_tool != expected_tool:
            raise ValueError(
                f"tool_name mismatch: expected={expected_tool} "
                f"payload={payload_tool}"
            )


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
    #
    # When analyzing a non-git directory, the orchestrator may compute a
    # deterministic "content hash" commit for run grouping. Many tool Makefiles
    # otherwise fall back to using the Project Caldera repo's git SHA, which
    # then causes ingest commit mismatches. Setting COMMIT to the standard
    # all-zeros sentinel prevents those Makefile fallbacks while still allowing
    # tools to resolve HEAD/fallback internally.
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


def _default_output_path(tool: ToolConfig, run_id: str, output_root: Path | None) -> Path:
    if output_root:
        return (output_root / tool.name / "output.json").resolve()
    return (Path(tool.path) / "outputs" / run_id / "output.json").resolve()


def _discover_outputs(output_root: Path) -> dict[str, Path]:
    """Discover tool output.json files under a standard output_root layout."""
    known_tools = {t.name for t in TOOL_CONFIGS} | {"coverage-ingest"}
    outputs: dict[str, Path] = {}
    for tool_name in sorted(known_tools):
        candidate = (output_root / tool_name / "output.json").resolve()
        if candidate.exists():
            outputs[tool_name] = candidate
    return outputs


def _safe_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


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


# Tool configurations for the orchestrator
TOOL_CONFIGS = [
    ToolConfig("layout-scanner", "src/tools/layout-scanner", {"NO_GITIGNORE": "1"}),
    ToolConfig("scc", "src/tools/scc"),
    ToolConfig("lizard", "src/tools/lizard"),
    ToolConfig("roslyn-analyzers", "src/tools/roslyn-analyzers"),
    ToolConfig("semgrep", "src/tools/semgrep"),
    ToolConfig("sonarqube", "src/tools/sonarqube"),
    ToolConfig("trivy", "src/tools/trivy"),
    ToolConfig("gitleaks", "src/tools/gitleaks"),
    ToolConfig("symbol-scanner", "src/tools/symbol-scanner"),
    ToolConfig("scancode", "src/tools/scancode"),
    ToolConfig("pmd-cpd", "src/tools/pmd-cpd"),
    ToolConfig("devskim", "src/tools/devskim"),
    ToolConfig("dotcover", "src/tools/dotcover"),
    ToolConfig("git-fame", "src/tools/git-fame"),
    ToolConfig("git-sizer", "src/tools/git-sizer"),
    ToolConfig("git-blame-scanner", "src/tools/git-blame-scanner"),
    ToolConfig("dependensee", "src/tools/dependensee"),
]


def _get_or_create_collection_run(
    collection_repo: CollectionRunRepository,
    args: argparse.Namespace,
    logger: OrchestratorLogger,
) -> tuple[str, str]:
    """Get existing or create new collection run. Returns (collection_run_id, run_id)."""
    existing = collection_repo.get_by_repo_commit(args.repo_id, args.commit)
    if existing:
        if not args.replace:
            raise SystemExit("Collection run exists for repo+commit. Use --replace to overwrite.")
        if existing.run_id != args.run_id:
            logger.info(f"Replacing existing run_id {existing.run_id} (overrides {args.run_id})")
        collection_repo.delete_collection_data(existing.collection_run_id)
        collection_repo.reset_run(existing.collection_run_id, datetime.now(timezone.utc))
        return existing.collection_run_id, existing.run_id

    collection_repo.insert(
        CollectionRun(
            collection_run_id=args.run_id,
            repo_id=args.repo_id,
            run_id=args.run_id,
            branch=args.branch,
            commit=args.commit,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            status="running",
        )
    )
    return args.run_id, args.run_id


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


# Tool ingestion configurations for tools with standard adapter pattern
TOOL_INGESTION_CONFIGS = [
    ToolIngestionConfig("scc", SccAdapter, SccRepository),
    ToolIngestionConfig("lizard", LizardAdapter, LizardRepository),
    ToolIngestionConfig("roslyn-analyzers", RoslynAnalyzersAdapter, RoslynRepository),
    ToolIngestionConfig("semgrep", SemgrepAdapter, SemgrepRepository),
    ToolIngestionConfig("sonarqube", SonarqubeAdapter, SonarqubeRepository, validate_metadata=False),
    ToolIngestionConfig("trivy", TrivyAdapter, TrivyRepository),
    ToolIngestionConfig("git-sizer", GitSizerAdapter, GitSizerRepository),
    ToolIngestionConfig("git-fame", GitFameAdapter, GitFameRepository),
    ToolIngestionConfig("git-blame-scanner", GitBlameScannerAdapter, GitBlameRepository),
    ToolIngestionConfig("gitleaks", GitleaksAdapter, GitleaksRepository),
    ToolIngestionConfig("symbol-scanner", SymbolScannerAdapter, SymbolScannerRepository),
    ToolIngestionConfig("scancode", ScancodeAdapter, ScancodeRepository),
    ToolIngestionConfig("pmd-cpd", PmdCpdAdapter, PmdCpdRepository),
    ToolIngestionConfig("devskim", DevskimAdapter, DevskimRepository),
    ToolIngestionConfig("dotcover", DotcoverAdapter, DotcoverRepository),
    ToolIngestionConfig("dependensee", DependenseeAdapter, DependenseeRepository),
    ToolIngestionConfig("coverage-ingest", CoverageIngestAdapter, CoverageRepository),
]


def ingest_outputs(
    conn: duckdb.DuckDBPyConnection,
    repo_id: str,
    collection_run_id: str,
    run_id: str,
    branch: str,
    commit: str,
    repo_path: Path,
    layout_output: Path | None,
    scc_output: Path | None,
    lizard_output: Path | None,
    roslyn_output: Path | None,
    semgrep_output: Path | None = None,
    sonarqube_output: Path | None = None,
    trivy_output: Path | None = None,
    gitleaks_output: Path | None = None,
    symbol_scanner_output: Path | None = None,
    scancode_output: Path | None = None,
    pmd_cpd_output: Path | None = None,
    devskim_output: Path | None = None,
    dotcover_output: Path | None = None,
    git_fame_output: Path | None = None,
    git_sizer_output: Path | None = None,
    git_blame_scanner_output: Path | None = None,
    dependensee_output: Path | None = None,
    coverage_output: Path | None = None,
    schema_path: Path = None,
    logger: OrchestratorLogger | None = None,
    continue_on_failure: bool = False,
) -> None:
    ensure_schema(conn, schema_path)
    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    log_fn = logger.info if logger else None
    quality_checker = DataQualityChecker(conn, logger=log_fn)

    # Layout must be ingested first (other tools depend on it)
    if not layout_output:
        raise ValueError("layout output is required for ingestion")
    payload = load_payload(layout_output)
    validate_payload(
        payload.get("metadata", {}), repo_id, run_id,
        expected_commit=commit,
    )
    LayoutScannerAdapter(run_repo, layout_repo, repo_path, log_fn).persist(payload)

    # Map tool names to output paths
    tool_outputs: dict[str, Path | None] = {
        "scc": scc_output,
        "lizard": lizard_output,
        "roslyn-analyzers": roslyn_output,
        "semgrep": semgrep_output,
        "sonarqube": sonarqube_output,
        "trivy": trivy_output,
        "gitleaks": gitleaks_output,
        "symbol-scanner": symbol_scanner_output,
        "scancode": scancode_output,
        "pmd-cpd": pmd_cpd_output,
        "devskim": devskim_output,
        "dotcover": dotcover_output,
        "git-fame": git_fame_output,
        "git-blame-scanner": git_blame_scanner_output,
        "dependensee": dependensee_output,
        "git-sizer": git_sizer_output,
        "coverage-ingest": coverage_output,
    }

    # Ingest each tool using its configuration
    ingest_errors: list[str] = []
    for config in TOOL_INGESTION_CONFIGS:
        output_path = tool_outputs.get(config.name)
        if not output_path:
            continue

        try:
            payload = load_payload(output_path)
            if config.validate_metadata:
                validate_payload(
                    payload.get("metadata", {}),
                    repo_id,
                    run_id,
                    expected_commit=commit,
                    expected_tool=config.name,
                )
            else:
                # Best-effort validation: do not fail the run, but surface contract drift.
                try:
                    validate_payload(
                        payload.get("metadata", {}),
                        repo_id,
                        run_id,
                        expected_commit=commit,
                        expected_tool=config.name,
                    )
                except Exception as exc:
                    if log_fn:
                        log_fn(f"WARNING: metadata validation skipped for {config.name}: {exc}")

            # Create adapter with appropriate repository
            tool_repo = config.repo_class(conn) if config.repo_class else None
            adapter = config.adapter_class(
                run_repo,
                layout_repo,
                tool_repo,
                repo_path,
                log_fn,
            )
            adapter._quality_checker = quality_checker
            adapter.persist(payload)
        except Exception as exc:
            if continue_on_failure:
                msg = f"WARNING: {config.name} ingestion failed: {exc}"
                if log_fn:
                    log_fn(msg)
                ingest_errors.append(config.name)
            else:
                raise

    if ingest_errors and log_fn:
        log_fn(f"Ingestion completed with {len(ingest_errors)} error(s): {', '.join(ingest_errors)}")


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
    repo_root = Path(__file__).resolve().parents[2]
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Caldera SoT orchestrator.")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--run-id", default=str(uuid.uuid4()))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", default="0" * 40)
    parser.add_argument("--db-path", default="~/.caldera/caldera_sot.duckdb")
    parser.add_argument("--output-root", help="Override tool output root directory")
    parser.add_argument("--skip-tools", help="Comma-separated tool names to skip")
    parser.add_argument("--schema-path", default="src/sot-engine/persistence/schema.sql")
    parser.add_argument("--layout-output", type=str)
    parser.add_argument("--scc-output", type=str)
    parser.add_argument("--lizard-output", type=str)
    parser.add_argument("--roslyn-output", type=str)
    parser.add_argument("--semgrep-output", type=str)
    parser.add_argument("--sonarqube-output", type=str)
    parser.add_argument("--trivy-output", type=str)
    parser.add_argument("--gitleaks-output", type=str)
    parser.add_argument("--symbol-scanner-output", type=str)
    parser.add_argument("--scancode-output", type=str)
    parser.add_argument("--pmd-cpd-output", type=str)
    parser.add_argument("--devskim-output", type=str)
    parser.add_argument("--dotcover-output", type=str)
    parser.add_argument("--git-fame-output", type=str)
    parser.add_argument("--git-sizer-output", type=str)
    parser.add_argument("--git-blame-scanner-output", type=str)
    parser.add_argument("--dependensee-output", type=str)
    parser.add_argument("--coverage-output", type=str)
    parser.add_argument("--run-tools", action="store_true")
    parser.add_argument("--run-dbt", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--no-progress", action="store_true", help="Disable rich progress display")
    parser.add_argument("--mode", default="local", choices=["local", "docker"], help="Execution mode")
    parser.add_argument("--max-parallel", type=int, default=1, help="Max parallel tool executions (default: 1 = sequential)")
    parser.add_argument("--docker-image-prefix", default=None, help="Docker image prefix (env: CALDERA_TOOL_IMAGE_PREFIX)")
    parser.add_argument("--docker-network", default=None, help="Docker network name (env: DOCKER_NETWORK)")
    parser.add_argument("--docker-repo-volume", default=None, help="Docker repo volume (env: CALDERA_REPO_VOLUME)")
    parser.add_argument("--docker-artifacts-volume", default=None, help="Docker artifacts volume (env: CALDERA_ARTIFACTS_VOLUME)")
    parser.add_argument("--dbt-bin", default="src/sot-engine/.venv-dbt/bin/dbt")
    parser.add_argument("--dbt-project-dir", default="src/sot-engine/dbt")
    parser.add_argument("--dbt-profiles-dir", default="src/sot-engine/dbt")
    parser.add_argument("--dbt-target-path", default="~/.caldera/dbt_target")
    parser.add_argument("--dbt-log-path", default="~/.caldera/dbt_logs")
    parser.add_argument("--log-path", default=None)
    parser.add_argument("--summary-path", default=None, help="Write a JSON run summary for debugging")
    parser.add_argument("--dbt-summary-path", default=None, help="Write a JSON dbt summary for debugging")
    parser.add_argument(
        "--continue-on-tool-failure",
        action="store_true",
        help="Run remaining tools even if one fails (ingest/dbt still run; status becomes partial_success)",
    )
    args = parser.parse_args()

    # Validate identifiers to prevent path traversal via --run-id / --repo-id
    _safe_id_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    for _field_name, _value in [("run_id", args.run_id), ("repo_id", args.repo_id)]:
        if not _safe_id_re.match(_value) or ".." in _value:
            parser.error(f"Unsafe {_field_name}: {_value!r}")

    repo_path = Path(args.repo_path)
    if _is_fallback_commit(args.commit):
        args.commit = _compute_content_hash(repo_path)
        _log.info("Non-git repo: computed content hash %s…", args.commit[:12])
    repo_name = args.repo_id
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = Path(args.schema_path)
    if not schema_path.is_absolute():
        schema_path = repo_root / schema_path
    schema_path = schema_path.resolve()
    db_path = Path(args.db_path).expanduser()
    if not db_path.is_absolute():
        db_path = (repo_root / db_path).resolve()
    else:
        db_path = db_path.resolve()
    args.dbt_target_path = str(Path(args.dbt_target_path).expanduser())
    args.dbt_log_path = str(Path(args.dbt_log_path).expanduser())
    log_path = Path(args.log_path) if args.log_path else Path("~/.caldera").expanduser() / f"caldera_orchestrator_{args.run_id}.log"
    if not log_path.is_absolute():
        log_path = repo_root / log_path
    logger = OrchestratorLogger(log_path)
    summary_path = Path(args.summary_path) if args.summary_path else logger.log_path.parent / "tool_run_summary.json"
    if not summary_path.is_absolute():
        summary_path = repo_root / summary_path
    dbt_summary_path = (
        Path(args.dbt_summary_path)
        if args.dbt_summary_path
        else logger.log_path.parent / "dbt_summary.json"
    )
    if not dbt_summary_path.is_absolute():
        dbt_summary_path = repo_root / dbt_summary_path
    dbt_summary_path = dbt_summary_path.resolve()

    summary: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": {
            "repo_path": str(repo_path.resolve()),
            "repo_id": args.repo_id,
            "branch": args.branch,
            "commit": args.commit,
        },
        "run_id": args.run_id,
        "db_path": str(db_path),
        "log_path": str(logger.log_path),
        "summary_path": str(summary_path),
        "status": "running",
        "error": None,
        "steps": {
            "tools": {"status": "pending", "duration_seconds": None, "error": None, "tools": []},
            "ingest": {"status": "pending", "duration_seconds": None, "error": None},
            "dbt": {"status": "pending", "duration_seconds": None, "error": None},
        },
    }
    dbt_summary: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "dbt": {
            "status": "pending",
            "project_dir": str(Path(args.dbt_project_dir)),
            "profiles_dir": str(Path(args.dbt_profiles_dir)),
            "target_path": str(Path(args.dbt_target_path)),
            "log_path": str(Path(args.dbt_log_path)),
        },
        "phases": [],
        "error": None,
    }

    layout_output = Path(args.layout_output) if args.layout_output else None
    scc_output = Path(args.scc_output) if args.scc_output else None
    lizard_output = Path(args.lizard_output) if args.lizard_output else None
    roslyn_output = Path(args.roslyn_output) if args.roslyn_output else None
    semgrep_output = Path(args.semgrep_output) if args.semgrep_output else None
    sonarqube_output = Path(args.sonarqube_output) if args.sonarqube_output else None
    trivy_output = Path(args.trivy_output) if args.trivy_output else None
    gitleaks_output = Path(args.gitleaks_output) if args.gitleaks_output else None
    symbol_scanner_output = Path(args.symbol_scanner_output) if args.symbol_scanner_output else None
    scancode_output = Path(args.scancode_output) if args.scancode_output else None
    pmd_cpd_output = Path(args.pmd_cpd_output) if args.pmd_cpd_output else None
    devskim_output = Path(args.devskim_output) if args.devskim_output else None
    dotcover_output = Path(args.dotcover_output) if args.dotcover_output else None
    git_fame_output = Path(args.git_fame_output) if args.git_fame_output else None
    git_sizer_output = Path(args.git_sizer_output) if args.git_sizer_output else None
    git_blame_scanner_output = Path(args.git_blame_scanner_output) if args.git_blame_scanner_output else None
    dependensee_output = Path(args.dependensee_output) if args.dependensee_output else None
    coverage_output = Path(args.coverage_output) if args.coverage_output else None

    try:
        logger.info(f"Log file: {logger.log_path}")
        logger.info(f"Repo: {repo_path} (repo_id={args.repo_id})")
        conn = duckdb.connect(str(db_path))
        ensure_schema(conn, schema_path)
        collection_repo = CollectionRunRepository(conn)

        collection_run_id, args.run_id = _get_or_create_collection_run(
            collection_repo, args, logger
        )

        logger.info(f"Run: {args.run_id} @ {args.branch}:{args.commit}")

        output_root = Path(args.output_root).resolve() if args.output_root else None

        if not layout_output:
            layout_output = _default_output_path(
                ToolConfig("layout-scanner", "src/tools/layout-scanner"),
                args.run_id,
                output_root,
            )

        # Construct execution backend
        exec_mode = ExecutionMode(args.mode)
        docker_config = None
        if exec_mode == ExecutionMode.DOCKER:
            docker_config = DockerConfig(
                image_prefix=args.docker_image_prefix or os.environ.get("CALDERA_TOOL_IMAGE_PREFIX", "caldera-tool-"),
                network=args.docker_network or os.environ.get("DOCKER_NETWORK", "caldera_default"),
                repo_volume=args.docker_repo_volume or os.environ.get("CALDERA_REPO_VOLUME", "caldera-repo"),
                artifacts_volume=args.docker_artifacts_volume or os.environ.get("CALDERA_ARTIFACTS_VOLUME", "caldera-artifacts"),
            )
        backend = get_backend(exec_mode, docker_config=docker_config)

        if args.run_tools:
            summary["steps"]["tools"]["status"] = "running"
            start = time.perf_counter()
            logger.info("Step 1/3: Run tools (layout, scc, lizard, roslyn-analyzers, semgrep, sonarqube, trivy, gitleaks)")
            skip_tools = {
                name.strip()
                for name in (args.skip_tools.split(",") if args.skip_tools else [])
                if name.strip()
            }
            if skip_tools:
                known_tool_names = {t.name for t in TOOL_CONFIGS}
                for name in sorted(skip_tools):
                    if name not in known_tool_names:
                        _log.warning(f"Unknown tool in --skip-tools: '{name}' (known: {sorted(known_tool_names)})")
            try:
                outputs, tool_summaries = _run_tools(
                    [tool for tool in TOOL_CONFIGS if tool.name not in skip_tools],
                    repo_path,
                    repo_name,
                    args.run_id,
                    args.repo_id,
                    args.branch,
                    args.commit,
                    logger,
                    output_root,
                    continue_on_failure=args.continue_on_tool_failure,
                    show_progress=not args.no_progress,
                    backend=backend,
                    max_parallel=args.max_parallel,
                )
            except ToolPhaseError as exc:
                summary["steps"]["tools"]["status"] = "failed"
                summary["steps"]["tools"]["duration_seconds"] = round(
                    time.perf_counter() - start, 3
                )
                summary["steps"]["tools"]["error"] = str(exc)
                summary["steps"]["tools"]["tools"] = exc.tool_summaries
                raise
            else:
                summary["steps"]["tools"]["duration_seconds"] = round(
                    time.perf_counter() - start, 3
                )
                summary["steps"]["tools"]["tools"] = tool_summaries
                failed = [t for t in tool_summaries if t.get("status") != "success"]
                if failed:
                    summary["steps"]["tools"]["status"] = "failed"
                    summary["steps"]["tools"]["error"] = f"{len(failed)} tool(s) failed"
                else:
                    summary["steps"]["tools"]["status"] = "success"
                if "layout-scanner" not in outputs:
                    summary["steps"]["tools"]["status"] = "failed"
                    summary["steps"]["tools"]["error"] = "layout-scanner is required but failed"
                    raise ToolPhaseError(
                        "Required tool failed: layout-scanner",
                        outputs=outputs,
                        tool_summaries=tool_summaries,
                    )
            layout_output = outputs.get("layout-scanner", layout_output)
            scc_output = outputs.get("scc", scc_output)
            lizard_output = outputs.get("lizard", lizard_output)
            roslyn_output = outputs.get("roslyn-analyzers", roslyn_output)
            semgrep_output = outputs.get("semgrep", semgrep_output)
            sonarqube_output = outputs.get("sonarqube", sonarqube_output)
            trivy_output = outputs.get("trivy", trivy_output)
            gitleaks_output = outputs.get("gitleaks", gitleaks_output)
            symbol_scanner_output = outputs.get("symbol-scanner", symbol_scanner_output)
            scancode_output = outputs.get("scancode", scancode_output)
            pmd_cpd_output = outputs.get("pmd-cpd", pmd_cpd_output)
            devskim_output = outputs.get("devskim", devskim_output)
            dotcover_output = outputs.get("dotcover", dotcover_output)
            git_fame_output = outputs.get("git-fame", git_fame_output)
            git_sizer_output = outputs.get("git-sizer", git_sizer_output)
            git_blame_scanner_output = outputs.get("git-blame-scanner", git_blame_scanner_output)
            dependensee_output = outputs.get("dependensee", dependensee_output)
            logger.info(f"Completed tools in {_format_duration(time.perf_counter() - start)}")
            for name, path in outputs.items():
                logger.info(f"{name} output: {path}")
        elif output_root:
            # Bundle/ingest mode: discover outputs under output_root when tools
            # were executed elsewhere (e.g. another machine or container).
            discovered = _discover_outputs(output_root)
            if "layout-scanner" not in discovered:
                summary["steps"]["tools"]["status"] = "failed"
                summary["steps"]["tools"]["error"] = (
                    f"layout-scanner output missing under output_root={output_root}"
                )
                raise FileNotFoundError(summary["steps"]["tools"]["error"])
            layout_output = discovered.get("layout-scanner", layout_output)
            scc_output = discovered.get("scc", scc_output)
            lizard_output = discovered.get("lizard", lizard_output)
            roslyn_output = discovered.get("roslyn-analyzers", roslyn_output)
            semgrep_output = discovered.get("semgrep", semgrep_output)
            sonarqube_output = discovered.get("sonarqube", sonarqube_output)
            trivy_output = discovered.get("trivy", trivy_output)
            gitleaks_output = discovered.get("gitleaks", gitleaks_output)
            symbol_scanner_output = discovered.get("symbol-scanner", symbol_scanner_output)
            scancode_output = discovered.get("scancode", scancode_output)
            pmd_cpd_output = discovered.get("pmd-cpd", pmd_cpd_output)
            devskim_output = discovered.get("devskim", devskim_output)
            dotcover_output = discovered.get("dotcover", dotcover_output)
            git_fame_output = discovered.get("git-fame", git_fame_output)
            git_sizer_output = discovered.get("git-sizer", git_sizer_output)
            git_blame_scanner_output = discovered.get("git-blame-scanner", git_blame_scanner_output)
            dependensee_output = discovered.get("dependensee", dependensee_output)
            coverage_output = discovered.get("coverage-ingest", coverage_output)
            summary["steps"]["tools"]["status"] = "skipped"
            summary["steps"]["tools"]["tools"] = [
                {"tool_name": k, "status": "provided", "output_path": str(v)}
                for k, v in sorted(discovered.items())
            ]
        else:
            summary["steps"]["tools"]["status"] = "skipped"

        start = time.perf_counter()
        logger.info("Step 2/3: Ingest outputs into DuckDB")
        summary["steps"]["ingest"]["status"] = "running"
        ingest_outputs(
            conn,
            args.repo_id,
            collection_run_id,
            args.run_id,
            args.branch,
            args.commit,
            repo_path,
            layout_output,
            scc_output,
            lizard_output,
            roslyn_output,
            semgrep_output,
            sonarqube_output,
            trivy_output,
            gitleaks_output,
            symbol_scanner_output,
            scancode_output,
            pmd_cpd_output,
            devskim_output,
            dotcover_output,
            git_fame_output,
            git_sizer_output,
            git_blame_scanner_output,
            dependensee_output,
            coverage_output,
            schema_path,
            logger,
            continue_on_failure=args.continue_on_tool_failure,
        )
        summary["steps"]["ingest"]["status"] = "success"
        summary["steps"]["ingest"]["duration_seconds"] = round(time.perf_counter() - start, 3)
        logger.info(
            f"Ingested into {args.db_path} in {_format_duration(time.perf_counter() - start)}"
        )
        conn.close()
        conn = None

        if args.run_dbt:
            start = time.perf_counter()
            logger.info("Step 3/3: Build marts (dbt run/test)")
            summary["steps"]["dbt"]["status"] = "running"
            dbt_summary["dbt"]["status"] = "running"
            run_dbt(
                Path(args.dbt_bin),
                Path(args.dbt_project_dir),
                Path(args.dbt_profiles_dir),
                logger,
                target_path=args.dbt_target_path,
                log_path=args.dbt_log_path,
                dbt_summary=dbt_summary,
                db_path=db_path,
                continue_on_test_failure=args.continue_on_tool_failure,
            )
            summary["steps"]["dbt"]["status"] = "success"
            summary["steps"]["dbt"]["duration_seconds"] = round(time.perf_counter() - start, 3)
            dbt_summary["dbt"]["status"] = "success"
            logger.info(
                f"dbt completed in {_format_duration(time.perf_counter() - start)}"
            )
        else:
            summary["steps"]["dbt"]["status"] = "skipped"
            dbt_summary["dbt"]["status"] = "skipped"

        tools_failed = summary["steps"]["tools"]["status"] == "failed"
        db_status = "partial_success" if tools_failed and args.continue_on_tool_failure else "completed"
        summary["status"] = "partial_success" if tools_failed and args.continue_on_tool_failure else "success"
        conn = duckdb.connect(str(db_path))
        collection_repo = CollectionRunRepository(conn)
        collection_repo.mark_status(
            collection_run_id, db_status, datetime.now(timezone.utc)
        )
        summary["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("Done.")
        return 0
    except Exception:
        summary["status"] = "failed"
        summary["completed_at"] = datetime.now(timezone.utc).isoformat()
        summary["error"] = traceback.format_exc(limit=20)
        if summary["steps"]["tools"]["status"] == "running":
            summary["steps"]["tools"]["status"] = "failed"
            summary["steps"]["tools"]["error"] = "See error"
        if summary["steps"]["ingest"]["status"] == "running":
            summary["steps"]["ingest"]["status"] = "failed"
            summary["steps"]["ingest"]["error"] = "See error"
        if summary["steps"]["dbt"]["status"] == "running":
            summary["steps"]["dbt"]["status"] = "failed"
            summary["steps"]["dbt"]["error"] = "See error"
            dbt_summary["dbt"]["status"] = "failed"
            dbt_summary["error"] = summary["error"]
        try:
            if "collection_run_id" in locals():
                conn = duckdb.connect(str(db_path))
                CollectionRunRepository(conn).mark_status(
                    collection_run_id, "failed", datetime.now(timezone.utc)
                )
        finally:
            raise
    finally:
        try:
            _safe_write_json(summary_path, summary)
        except Exception:
            pass
        try:
            _safe_write_json(dbt_summary_path, dbt_summary)
        except Exception:
            pass
        if "conn" in locals() and conn:
            conn.close()
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
