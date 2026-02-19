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
    parser = argparse.ArgumentParser(description="Write a run manifest JSON from DuckDB.")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--collection-run-id", required=True, help="collection_run_id (usually run_id)")
    parser.add_argument("--out", required=True, help="Output JSON path")
    parser.add_argument("--report", default=None, help="Optional report.html path")
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

        manifest = {
            "schema_version": 1,
            "generated_at": _utc_now_iso(),
            "db_path": str(db_path),
            "report_path": str(Path(args.report).expanduser()) if args.report else None,
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

