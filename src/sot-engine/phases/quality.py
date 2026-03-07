from __future__ import annotations

from typing import Any

import duckdb

from phases.utilities import OrchestratorLogger


def compute_run_quality(
    conn: duckdb.DuckDBPyConnection,
    collection_run_id: str,
    tool_summaries: list[dict[str, Any]],
    all_tool_names: list[str],
    ingestion_errors: int = 0,
    warning_count: int = 0,
    warning_counts: dict[str, int] | None = None,
    budget_passed: bool = True,
    logger: OrchestratorLogger | None = None,
) -> dict[str, Any]:
    """Compute and persist a quality summary for the collection run.

    Returns a dict with the trust metrics suitable for inclusion in manifests.
    """
    tools_expected = len(all_tool_names)

    # Classify tool outcomes from summaries
    completed_names: set[str] = set()
    failed_names: set[str] = set()
    empty_names: set[str] = set()

    for ts in tool_summaries:
        name = ts.get("tool_name", "")
        status = ts.get("status", "")
        if status == "success":
            output_bytes = ts.get("output_bytes", 0) or 0
            if output_bytes < 10:  # essentially empty output
                empty_names.add(name)
            else:
                completed_names.add(name)
        elif status == "provided":
            # Bundle/discover mode — count as completed
            completed_names.add(name)
        else:
            failed_names.add(name)

    # Check for tools that produced output but had zero data rows
    for name in list(completed_names):
        row_count = _count_tool_rows(conn, collection_run_id, name)
        if row_count <= 0:
            completed_names.discard(name)
            empty_names.add(name)
        # row_count < 0 means indeterminate/error — don't penalize

    summarized_names = completed_names | failed_names | empty_names
    skipped_names = {n for n in all_tool_names if n not in summarized_names}

    tools_completed = len(completed_names)
    tools_failed = len(failed_names)
    tools_empty = len(empty_names)
    tools_skipped = len(skipped_names)

    # Compute trust score (0-100)
    # Base: completeness ratio. Penalties for failures and empty outputs.
    if tools_expected == 0:
        trust_score = 0
    else:
        completeness = tools_completed / tools_expected
        failure_penalty = (tools_failed * 10 + tools_empty * 5) / max(tools_expected, 1)
        ingestion_penalty = min(ingestion_errors * 5, 20)
        trust_score = max(0, min(100, round(completeness * 100 - failure_penalty - ingestion_penalty)))

    wc = warning_counts or {}
    quality = {
        "tools_expected": tools_expected,
        "tools_completed": tools_completed,
        "tools_skipped": tools_skipped,
        "tools_failed": tools_failed,
        "tools_empty": tools_empty,
        "ingestion_errors": ingestion_errors,
        "warning_count": warning_count,
        "warnings_expected_missing": wc.get("expected_missing", 0),
        "warnings_regression": wc.get("regression", 0),
        "warnings_degraded": wc.get("degraded", 0),
        "budget_passed": budget_passed,
        "trust_score": trust_score,
        "completed_tools": sorted(completed_names),
        "failed_tools": sorted(failed_names),
        "empty_tools": sorted(empty_names),
        "skipped_tools": sorted(skipped_names),
    }

    # Persist to lz_run_quality_summary
    try:
        conn.execute(
            "DELETE FROM lz_run_quality_summary WHERE collection_run_id = ?",
            [collection_run_id],
        )
        conn.execute(
            """
            INSERT INTO lz_run_quality_summary (
                collection_run_id, tools_expected, tools_completed,
                tools_skipped, tools_failed, tools_empty,
                ingestion_errors, warning_count,
                warnings_expected_missing, warnings_regression,
                warnings_degraded, budget_passed, trust_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                collection_run_id, tools_expected, tools_completed,
                tools_skipped, tools_failed, tools_empty,
                ingestion_errors, warning_count,
                wc.get("expected_missing", 0), wc.get("regression", 0),
                wc.get("degraded", 0), budget_passed, trust_score,
            ],
        )
    except Exception as exc:
        if logger:
            logger.info(f"WARNING: Failed to persist run quality summary: {exc}")

    return quality


def _count_tool_rows(
    conn: duckdb.DuckDBPyConnection,
    collection_run_id: str,
    tool_name: str,
) -> int:
    """Count data rows for a tool in its LZ tables."""
    try:
        row = conn.execute(
            "SELECT run_pk FROM lz_tool_runs WHERE collection_run_id = ? AND tool_name = ?",
            [collection_run_id, tool_name],
        ).fetchone()
        if not row:
            return 0
        run_pk = row[0]
        # Check the first matching data table
        _tool_table_map = {
            "scc": "lz_scc_file_metrics",
            "lizard": "lz_lizard_file_metrics",
            "roslyn-analyzers": "lz_roslyn_violations",
            "semgrep": "lz_semgrep_smells",
            "sonarqube": "lz_sonarqube_issues",
            "trivy": "lz_trivy_targets",
            "gitleaks": "lz_gitleaks_secrets",
            "symbol-scanner": "lz_code_symbols",
            "scancode": "lz_scancode_file_licenses",
            "pmd-cpd": "lz_pmd_cpd_file_metrics",
            "devskim": "lz_devskim_findings",
            "dotcover": "lz_dotcover_assembly_coverage",
            "git-fame": "lz_git_fame_authors",
            "git-sizer": "lz_git_sizer_metrics",
            "git-blame-scanner": "lz_git_blame_summary",
            "dependensee": "lz_dependensee_projects",
            "coverage-ingest": "lz_coverage_summary",
            "layout-scanner": "lz_layout_files",
        }
        table = _tool_table_map.get(tool_name)
        if not table:
            return 1  # unknown tool, assume non-empty
        result = conn.execute(
            f"SELECT count(*) FROM {table} WHERE run_pk = ?", [run_pk]
        ).fetchone()
        return result[0] if result else 0
    except Exception:
        return -1  # can't determine, don't penalize
