#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def _markdown_table(rows: list[tuple], headers: list[str]) -> str:
    if not rows:
        return ""
    cols = len(headers)
    widths = [len(h) for h in headers]
    str_rows: list[list[str]] = []
    for r in rows:
        rr = []
        for i in range(cols):
            v = r[i]
            s = "" if v is None else str(v)
            rr.append(s)
            widths[i] = max(widths[i], len(s))
        str_rows.append(rr)

    def fmt_row(cells: list[str]) -> str:
        return "| " + " | ".join(cells[i].ljust(widths[i]) for i in range(cols)) + " |"

    header = fmt_row(headers)
    sep = "| " + " | ".join("-" * widths[i] for i in range(cols)) + " |"
    body = "\n".join(fmt_row(r) for r in str_rows)
    return "\n".join([header, sep, body])


def main() -> int:
    parser = argparse.ArgumentParser(description="List Caldera analysis runs from DuckDB.")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        print(f"No database found at {db_path}. Run 'make analyze' first.")
        return 0

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = conn.execute(
            """
            SELECT
              cr.collection_run_id,
              cr.repo_id,
              cr.commit,
              cr.status,
              cr.started_at,
              cr.completed_at,
              count(tr.run_pk) as tool_count
            FROM lz_collection_runs cr
            LEFT JOIN lz_tool_runs tr
              ON tr.collection_run_id = cr.collection_run_id
            GROUP BY 1,2,3,4,5,6
            ORDER BY cr.started_at DESC
            LIMIT ?
            """,
            [args.limit],
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No runs found in database. Run 'make analyze' first.")
        return 0

    headers = [
        "collection_run_id",
        "repo_id",
        "commit",
        "status",
        "started_at",
        "completed_at",
        "tools",
    ]
    print(_markdown_table(rows, headers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

