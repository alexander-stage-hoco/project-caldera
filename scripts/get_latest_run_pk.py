#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def main() -> int:
    parser = argparse.ArgumentParser(description="Get the latest run_pk from DuckDB.")
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        row = conn.execute(
            "SELECT run_pk FROM lz_tool_runs ORDER BY run_pk DESC LIMIT 1"
        ).fetchone()
        if not row:
            raise SystemExit("No runs found in database")
        print(int(row[0]))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

