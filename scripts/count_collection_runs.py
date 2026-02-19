#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def main() -> int:
    parser = argparse.ArgumentParser(description="Count collection runs in DuckDB.")
    parser.add_argument("--db", required=True)
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        print("0")
        return 0

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        row = conn.execute("SELECT count(*) FROM lz_collection_runs").fetchone()
        print(int(row[0]) if row else 0)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

