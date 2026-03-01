#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    """
    Write a run manifest JSON file from a DuckDB database for a specified collection_run_id.
    
    Reads metadata and tool runs from the provided DuckDB file, optionally enriches the manifest with a trust/quality summary (if present) and per-category warning details from a warnings.json file, and writes a structured manifest JSON to the specified output path.
    
    Returns:
        int: 0 on success.
    
    Raises:
        SystemExit: if the specified collection_run_id is not found in the database.
    """
    parser = argparse.ArgumentParser(description="Write a run manifest JSON from DuckDB.")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--collection-run-id", required=True, help="collection_run_id (usually run_id)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--report", default=None, help="Optional report.html path")
    parser.add_argument("--warnings-json", default=None, help="Optional warnings.json path")
    parser.add_argument(
        "--tool-outputs-included",
        action="store_true",
        default=False,
        help="Mark that raw tool outputs are included in the export",
    )
    parser.add_argument(
        "--dbt-artifacts-included",
        action="store_true",
        default=False,
        help="Mark that dbt artifacts are included in the export",
    )
    parser.add_argument(
        "--evidence-included",
        action="store_true",
        default=False,
        help="Mark that evidence JSON is included in the export",
    )
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        cr = conn.execute(
            """
            SELECT collection_run_id, repo_id, run_id, branch, commit, started_at, completed_at, status
            FROM lz_collection_runs
            WHERE collection_run_id = ?
            """,
            [args.collection_run_id],
        ).fetchone()
        if not cr:
            raise SystemExit(f"collection_run_id not found: {args.collection_run_id}")

        tool_rows = conn.execute(
            """
            SELECT run_pk, tool_name, tool_version, schema_version, timestamp
            FROM lz_tool_runs
            WHERE collection_run_id = ?
            ORDER BY tool_name
            """,
            [args.collection_run_id],
        ).fetchall()

        # Fetch trust / quality summary if available
        trust = None
        try:
            qs = conn.execute(
                """
                SELECT tools_expected, tools_completed, tools_skipped,
                       tools_failed, tools_empty, ingestion_errors,
                       warning_count, trust_score
                FROM lz_run_quality_summary
                WHERE collection_run_id = ?
                """,
                [args.collection_run_id],
            ).fetchone()
            if qs:
                trust = {
                    "tools_expected": qs[0],
                    "tools_completed": qs[1],
                    "tools_skipped": qs[2],
                    "tools_failed": qs[3],
                    "tools_empty": qs[4],
                    "ingestion_errors": qs[5],
                    "warning_count": qs[6],
                    "trust_score": qs[7],
                }
        except Exception:
            pass  # table may not exist in older databases

        # Enrich trust with per-category warning counts from warnings.json
        if trust and args.warnings_json:
            warnings_path = Path(args.warnings_json).expanduser()
            if warnings_path.exists():
                try:
                    wdata = json.loads(warnings_path.read_text(encoding="utf-8"))
                    trust["warning_counts"] = wdata.get("counts", {})
                    trust["warning_budgets"] = wdata.get("budgets", {})
                    trust["budget_passed"] = wdata.get("budget_passed", True)
                except Exception:
                    pass  # best-effort

        manifest = {
            "schema_version": 2,
            "generated_at": _utc_now_iso(),
            "db_path": str(db_path),
            "report_path": str(Path(args.report).expanduser()) if args.report else None,
            "tool_outputs_included": args.tool_outputs_included,
            "dbt_artifacts_included": args.dbt_artifacts_included,
            "evidence_included": args.evidence_included,
            "collection_run": {
                "collection_run_id": cr[0],
                "repo_id": cr[1],
                "run_id": cr[2],
                "branch": cr[3],
                "commit": cr[4],
                "started_at": str(cr[5]),
                "completed_at": str(cr[6]) if cr[6] is not None else None,
                "status": cr[7],
            },
            "trust": trust,
            "tools": [
                {
                    "run_pk": int(r[0]),
                    "tool_name": r[1],
                    "tool_version": r[2],
                    "schema_version": r[3],
                    "timestamp": str(r[4]),
                }
                for r in tool_rows
            ],
        }

        out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

