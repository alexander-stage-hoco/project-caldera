from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

_log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from execution import (
    DockerConfig,
    ExecutionMode,
    get_backend,
)
from persistence.entities import CollectionRun
from persistence.repositories import CollectionRunRepository

# ---------------------------------------------------------------------------
# Re-exports: every symbol previously importable from ``orchestrator`` remains
# available here so that existing test files and external callers keep working.
# ---------------------------------------------------------------------------

from phases.schema import ensure_schema  # noqa: F401
from phases.utilities import (  # noqa: F401
    OrchestratorLogger,
    _commit_is_git_commit,
    _compute_content_hash,
    _default_output_path,
    _discover_outputs,
    _format_duration,
    _is_fallback_commit,
    _safe_write_json,
    _subprocess_run_with_retry,
    run_tool_make,
)
from phases.validation import load_payload, validate_payload  # noqa: F401
from phases.quality import compute_run_quality  # noqa: F401
from phases.tool_execution import (  # noqa: F401
    ToolConfig,
    ToolPhaseError,
    TOOL_CONFIGS,
    _run_tools,
)
from phases.ingestion import (  # noqa: F401
    ToolIngestionConfig,
    TOOL_INGESTION_CONFIGS,
    ingest_outputs,
)
from phases.dbt_phase import _resolve_dbt_cmd, run_dbt  # noqa: F401


# ---------------------------------------------------------------------------
# Helper used only by main()
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

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
            discovered = _discover_outputs(output_root, {t.name for t in TOOL_CONFIGS})
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

        # Compute and persist run quality / trust score
        # Exclude explicitly skipped tools so the trust score denominator
        # reflects only the tools that were expected to run.
        _skip = {
            n.strip()
            for n in (args.skip_tools.split(",") if args.skip_tools else [])
            if n.strip()
        }
        all_tool_names = [
            t.name for t in TOOL_CONFIGS if t.name not in _skip
        ] + (["coverage-ingest"] if "coverage-ingest" not in _skip else [])
        tool_sums = summary["steps"]["tools"].get("tools", [])
        ingestion_err_count = len([
            e for e in tool_sums if e.get("status") == "failed"
        ]) if not tool_sums else 0
        quality = compute_run_quality(
            conn, collection_run_id, tool_sums, all_tool_names,
            ingestion_errors=ingestion_err_count, logger=logger,
        )
        summary["trust"] = quality
        logger.info(
            f"Trust score: {quality['trust_score']}/100 "
            f"({quality['tools_completed']}/{quality['tools_expected']} tools completed)"
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
