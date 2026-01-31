#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import duckdb


@dataclass
class TableColumn:
    name: str
    type: str
    not_null: bool
    default: str | None
    is_pk: bool


def _connect(db_path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path)


def list_tables(conn: duckdb.DuckDBPyConnection, schema: str | None) -> list[tuple[str, str, str]]:
    where_clause = "WHERE table_schema = ?" if schema else ""
    params = [schema] if schema else []
    rows = conn.execute(
        f"""
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        {where_clause}
        ORDER BY table_schema, table_name
        """,
        params,
    ).fetchall()
    return [(row[0], row[1], row[2]) for row in rows]


def describe_table(conn: duckdb.DuckDBPyConnection, table: str) -> list[TableColumn]:
    rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
    columns = []
    for _, name, col_type, not_null, default, pk in rows:
        columns.append(
            TableColumn(
                name=name,
                type=col_type,
                not_null=bool(not_null),
                default=default,
                is_pk=bool(pk),
            )
        )
    return columns


def _primary_keys(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    return {col.name for col in describe_table(conn, table) if col.is_pk}


def _column_names(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    return {col.name for col in describe_table(conn, table)}


def infer_relationships(
    conn: duckdb.DuckDBPyConnection, tables: Iterable[str]
) -> dict[str, list[str]]:
    table_list = list(tables)
    pk_map = {table: _primary_keys(conn, table) for table in table_list}
    col_map = {table: _column_names(conn, table) for table in table_list}
    relationships: dict[str, list[str]] = {}

    for table in table_list:
        for column in col_map[table]:
            targets = []
            for other_table, pk_cols in pk_map.items():
                if table == other_table:
                    continue
                if column in pk_cols:
                    targets.append(f"{other_table}.{column}")
            if targets:
                relationships.setdefault(table, []).append(
                    f"{table}.{column} -> {', '.join(sorted(targets))}"
                )
    return relationships


def run_query(conn: duckdb.DuckDBPyConnection, sql: str) -> tuple[list[str], list[tuple]]:
    result = conn.execute(sql)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()
    return columns, rows


def print_table(rows: list[tuple], headers: list[str]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(str(value)))
    fmt = " | ".join("{:<" + str(width) + "}" for width in widths)
    print(fmt.format(*headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(fmt.format(*row))


def main() -> int:
    parser = argparse.ArgumentParser(description="DuckDB explorer CLI.")
    parser.add_argument("--db", default="/tmp/caldera_sot.duckdb", help="DuckDB database path")
    parser.add_argument("--schema", default="main", help="Schema to inspect")

    subparsers = parser.add_subparsers(dest="command", required=False)

    subparsers.add_parser("list", help="List tables in the database")

    describe_parser = subparsers.add_parser("describe", help="Describe a table")
    describe_parser.add_argument("table", help="Table name to describe")

    subparsers.add_parser("relations", help="Infer relationships between tables")

    query_parser = subparsers.add_parser("query", help="Run an arbitrary SQL query")
    query_parser.add_argument("sql", help="SQL query to execute")

    args = parser.parse_args()
    command = args.command or "list"

    conn = _connect(args.db)
    try:
        if command == "list":
            tables = list_tables(conn, args.schema)
            print_table(tables, ["schema", "table", "type"])
        elif command == "describe":
            columns = describe_table(conn, args.table)
            rows = [
                (col.name, col.type, "YES" if col.not_null else "NO", col.default or "", "YES" if col.is_pk else "NO")
                for col in columns
            ]
            print_table(rows, ["column", "type", "not_null", "default", "pk"])
        elif command == "relations":
            tables = [t[1] for t in list_tables(conn, args.schema)]
            relations = infer_relationships(conn, tables)
            if not relations:
                print("No relationships inferred.")
            else:
                for table in sorted(relations):
                    print(f"{table}:")
                    for line in sorted(relations[table]):
                        print(f"  {line}")
        elif command == "query":
            if not args.sql or not args.sql.strip():
                raise SystemExit("Provide a SQL query.")
            columns, rows = run_query(conn, args.sql)
            print_table(rows, columns)
        else:
            raise SystemExit(f"Unknown command: {command}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
