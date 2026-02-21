#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve run_pk from DuckDB for a given run_id.")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--run-id", required=True, help="run_id to look up")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        row = conn.execute(
            "SELECT run_pk FROM lz_tool_runs WHERE run_id = ? AND tool_name = 'scc' ORDER BY run_pk DESC LIMIT 1",
            [args.run_id],
        ).fetchone()
        if not row:
            # Fallback: any tool (SCC may have been skipped)
            row = conn.execute(
                "SELECT run_pk FROM lz_tool_runs WHERE run_id = ? ORDER BY run_pk DESC LIMIT 1",
                [args.run_id],
            ).fetchone()
            if not row:
                raise SystemExit(f"run_id not found in DB: {args.run_id}")
            print(f"Warning: SCC tool run not found for run_id={args.run_id}; using fallback run_pk", file=sys.stderr)
        print(int(row[0]))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

