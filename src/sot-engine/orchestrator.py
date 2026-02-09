from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import CoverageAdapter, DependenseeAdapter, DevskimAdapter, DotcoverAdapter, GitBlameScannerAdapter, GitFameAdapter, GitSizerAdapter, GitleaksAdapter, LayoutAdapter, LizardAdapter, PmdCpdAdapter, RoslynAdapter, ScancodeAdapter, SccAdapter, SemgrepAdapter, SonarqubeAdapter, SymbolScannerAdapter, TrivyAdapter
from persistence.adapters.base_adapter import BaseAdapter
from persistence.entities import CollectionRun, ToolRun
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


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_payload(metadata: dict, repo_id: str, run_id: str) -> None:
    if metadata.get("repo_id") != repo_id:
        raise ValueError("repo_id mismatch between orchestrator and payload")
    if metadata.get("run_id") != run_id:
        raise ValueError("run_id mismatch between orchestrator and payload")


def _format_duration(seconds: float) -> str:
    return f"{seconds:.2f}s"


class OrchestratorLogger:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
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


def _is_fallback_commit(commit: str) -> bool:
    """Check if commit is a fallback value (all zeros or empty)."""
    return not commit or commit == "0" * 40


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
    # Only set COMMIT if it's a real git commit (not fallback all-zeros)
    # This allows tools to compute their own fallback hash for non-git repos
    if not _is_fallback_commit(commit):
        env["COMMIT"] = commit
    if extra_env:
        env.update(extra_env)
    subprocess.run(
        ["make", "analyze"],
        cwd=tool_root,
        env=env,
        stdout=logger.log_pipe(),
        stderr=logger.log_pipe(),
        check=True,
    )


def _default_output_path(tool: ToolConfig, run_id: str, output_root: Path | None) -> Path:
    if output_root:
        return (output_root / tool.name / run_id / "output.json").resolve()
    return (Path(tool.path) / "outputs" / run_id / "output.json").resolve()


# Tool configurations for the orchestrator
TOOL_CONFIGS = [
    ToolConfig("layout-scanner", "src/tools/layout-scanner", {"NO_GITIGNORE": "1"}),
    ToolConfig("scc", "src/tools/scc"),
    ToolConfig("lizard", "src/tools/lizard"),
    ToolConfig("roslyn-analyzers", "src/tools/roslyn-analyzers"),
    ToolConfig("semgrep", "src/tools/semgrep"),
    ToolConfig(
        "sonarqube",
        "src/tools/sonarqube",
        {
            "SONARQUBE_SKIP_DOCKER": "1",
            "SONARQUBE_CONTAINER_RUNNING": "1",
            "SONARQUBE_URL": "http://localhost:9000",
            "NATIVE_SCANNER": "1",
        },
    ),
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
) -> dict[str, Path]:
    """Run all configured tools and return their output paths."""
    outputs: dict[str, Path] = {}
    for tool in tool_configs:
        output_path = _default_output_path(tool, run_id, output_root)
        run_tool_make(
            Path(tool.path),
            repo_path,
            repo_name,
            run_id,
            repo_id,
            branch,
            commit,
            output_path.parent,
            logger,
            extra_env=tool.extra_env,
        )
        outputs[tool.name] = output_path
    return outputs


# Tool ingestion configurations for tools with standard adapter pattern
TOOL_INGESTION_CONFIGS = [
    ToolIngestionConfig("scc", SccAdapter, SccRepository),
    ToolIngestionConfig("lizard", LizardAdapter, LizardRepository),
    ToolIngestionConfig("roslyn-analyzers", RoslynAdapter, RoslynRepository),
    ToolIngestionConfig("semgrep", SemgrepAdapter, SemgrepRepository),
    ToolIngestionConfig("sonarqube", SonarqubeAdapter, SonarqubeRepository, validate_metadata=False),
    ToolIngestionConfig("trivy", TrivyAdapter, TrivyRepository, validate_metadata=False),
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
    ToolIngestionConfig("coverage-ingest", CoverageAdapter, CoverageRepository),
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
) -> None:
    ensure_schema(conn, schema_path)
    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    log_fn = logger.info if logger else None

    # Layout must be ingested first (other tools depend on it)
    if not layout_output:
        raise ValueError("layout output is required for ingestion")
    payload = load_payload(layout_output)
    validate_payload(payload.get("metadata", {}), repo_id, run_id)
    LayoutAdapter(run_repo, layout_repo, repo_path, log_fn).persist(payload)

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
    for config in TOOL_INGESTION_CONFIGS:
        output_path = tool_outputs.get(config.name)
        if not output_path:
            continue

        payload = load_payload(output_path)
        if config.validate_metadata:
            validate_payload(payload.get("metadata", {}), repo_id, run_id)

        # Create adapter with appropriate repository
        tool_repo = config.repo_class(conn) if config.repo_class else None
        adapter = config.adapter_class(
            run_repo,
            layout_repo,
            tool_repo,
            repo_path,
            log_fn,
        )
        adapter.persist(payload)


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
    target_path: str = "/tmp/dbt_target",
    log_path: str = "/tmp/dbt_logs",
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    if not dbt_project_dir.is_absolute():
        dbt_project_dir = repo_root / dbt_project_dir
    if not profiles_dir.is_absolute():
        profiles_dir = repo_root / profiles_dir
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(profiles_dir)
    dbt_cmd = _resolve_dbt_cmd(dbt_bin, repo_root)
    subprocess.run(
        [*dbt_cmd, "run", "--target-path", target_path, "--log-path", log_path],
        cwd=str(dbt_project_dir),
        env=env,
        stdout=logger.log_pipe(),
        stderr=logger.log_pipe(),
        check=True,
    )
    subprocess.run(
        [*dbt_cmd, "test", "--target-path", target_path, "--log-path", log_path],
        cwd=str(dbt_project_dir),
        env=env,
        stdout=logger.log_pipe(),
        stderr=logger.log_pipe(),
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Caldera SoT orchestrator.")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--run-id", default=str(uuid.uuid4()))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", default="0" * 40)
    parser.add_argument("--db-path", default="/tmp/caldera_sot.duckdb")
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
    parser.add_argument("--dbt-bin", default="src/sot-engine/.venv-dbt/bin/dbt")
    parser.add_argument("--dbt-project-dir", default="src/sot-engine/dbt")
    parser.add_argument("--dbt-profiles-dir", default="src/sot-engine/dbt")
    parser.add_argument("--log-path", default=None)
    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    repo_name = args.repo_id
    schema_path = Path(args.schema_path)
    repo_root = Path(__file__).resolve().parents[2]
    log_path = Path(args.log_path) if args.log_path else Path("/tmp") / f"caldera_orchestrator_{args.run_id}.log"
    if not log_path.is_absolute():
        log_path = repo_root / log_path
    logger = OrchestratorLogger(log_path)

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
        conn = duckdb.connect(args.db_path)
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

        if args.run_tools:
            start = time.perf_counter()
            logger.info("Step 1/3: Run tools (layout, scc, lizard, roslyn-analyzers, semgrep, sonarqube, trivy, gitleaks)")
            skip_tools = {
                name.strip()
                for name in (args.skip_tools.split(",") if args.skip_tools else [])
                if name.strip()
            }
            outputs = _run_tools(
                [tool for tool in TOOL_CONFIGS if tool.name not in skip_tools],
                repo_path,
                repo_name,
                args.run_id,
                args.repo_id,
                args.branch,
                args.commit,
                logger,
                output_root,
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

        start = time.perf_counter()
        logger.info("Step 2/3: Ingest outputs into DuckDB")
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
        )
        logger.info(
            f"Ingested into {args.db_path} in {_format_duration(time.perf_counter() - start)}"
        )
        conn.close()
        conn = None

        if args.run_dbt:
            start = time.perf_counter()
            logger.info("Step 3/3: Build marts (dbt run/test)")
            run_dbt(
                Path(args.dbt_bin),
                Path(args.dbt_project_dir),
                Path(args.dbt_profiles_dir),
                logger,
            )
            logger.info(
                f"dbt completed in {_format_duration(time.perf_counter() - start)}"
            )

        conn = duckdb.connect(args.db_path)
        collection_repo = CollectionRunRepository(conn)
        collection_repo.mark_status(
            collection_run_id, "completed", datetime.now(timezone.utc)
        )
        logger.info("Done.")
        return 0
    except Exception:
        try:
            if "collection_run_id" in locals():
                conn = duckdb.connect(args.db_path)
                CollectionRunRepository(conn).mark_status(
                    collection_run_id, "failed", datetime.now(timezone.utc)
                )
        finally:
            raise
    finally:
        if "conn" in locals() and conn:
            conn.close()
        logger.close()


if __name__ == "__main__":
    raise SystemExit(main())
