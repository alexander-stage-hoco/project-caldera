"""Shared validation utilities for adapters."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import duckdb
import jsonschema


# Core landing zone table DDL (required by all adapters)
CORE_TABLE_DDL = {
    "lz_run_pk_seq": "CREATE SEQUENCE IF NOT EXISTS lz_run_pk_seq START 1",
    "lz_collection_runs": """
        CREATE TABLE IF NOT EXISTS lz_collection_runs (
            collection_run_id VARCHAR NOT NULL,
            repo_id VARCHAR NOT NULL,
            run_id VARCHAR NOT NULL,
            branch VARCHAR NOT NULL,
            commit VARCHAR NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            status VARCHAR NOT NULL,
            PRIMARY KEY (collection_run_id),
            UNIQUE (repo_id, commit)
        )
    """,
    "lz_tool_runs": """
        CREATE TABLE IF NOT EXISTS lz_tool_runs (
            run_pk BIGINT DEFAULT nextval('lz_run_pk_seq'),
            collection_run_id VARCHAR NOT NULL,
            repo_id VARCHAR NOT NULL,
            run_id VARCHAR NOT NULL,
            tool_name VARCHAR NOT NULL,
            tool_version VARCHAR NOT NULL,
            schema_version VARCHAR NOT NULL,
            branch VARCHAR NOT NULL,
            commit VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk),
            UNIQUE (collection_run_id, tool_name)
        )
    """,
}


def ensure_lz_tables(
    conn: duckdb.DuckDBPyConnection,
    table_ddl: dict[str, str],
    include_core: bool = True,
) -> list[str]:
    """Ensure landing zone tables exist, creating if necessary.

    Args:
        conn: DuckDB connection
        table_ddl: Map of table_name -> CREATE TABLE/SEQUENCE DDL statement
        include_core: Whether to also ensure core tables (lz_tool_runs, etc.)

    Returns:
        List of tables/sequences that were created (empty if all existed)
    """
    created = []

    # Ensure core tables first if requested
    all_ddl = {}
    if include_core:
        all_ddl.update(CORE_TABLE_DDL)
    all_ddl.update(table_ddl)

    for name, ddl in all_ddl.items():
        # Check if it's a sequence or table
        is_sequence = "CREATE SEQUENCE" in ddl.upper()

        if is_sequence:
            # For sequences, use duckdb_sequences() function
            exists = conn.execute(
                "SELECT 1 FROM duckdb_sequences() WHERE sequence_name = ?",
                [name],
            ).fetchone()
        else:
            exists = conn.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = ?",
                [name],
            ).fetchone()

        if not exists:
            conn.execute(ddl)
            created.append(name)

    return created


def validate_json_schema(payload: dict, schema_path: Path) -> list[str]:
    """Validate payload against a JSON schema, returning error messages."""
    schema = json.loads(schema_path.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(payload), key=str):
        location = "/".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def validate_lz_schema(
    conn: duckdb.DuckDBPyConnection,
    expected: dict[str, dict[str, str]],
) -> list[str]:
    """Validate landing zone tables/columns exist with expected types."""
    errors: list[str] = []
    for table, columns in expected.items():
        exists = conn.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()
        if not exists:
            errors.append(f"missing table: {table}")
            continue
        rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
        type_map = {name: col_type.upper() for _, name, col_type, *_ in rows}
        for column, expected_type in columns.items():
            actual = type_map.get(column)
            if actual is None:
                errors.append(f"{table}.{column} missing")
                continue
            if not actual.startswith(expected_type.upper()):
                errors.append(
                    f"{table}.{column} type mismatch: {actual} != {expected_type}"
                )
    return errors


def check_non_negative(value: int | float | None, field: str) -> Iterable[str]:
    if value is None:
        return []
    if value < 0:
        return [f"{field} must be >= 0 (got {value})"]
    return []


def check_ratio(value: float | None, field: str) -> Iterable[str]:
    if value is None:
        return []
    if value < 0 or value > 1:
        return [f"{field} must be between 0 and 1 (got {value})"]
    return []


def check_required(value: object, field: str) -> Iterable[str]:
    if value in (None, ""):
        return [f"{field} is required"]
    return []


def check_enum(value: object, allowed: set, field: str) -> Iterable[str]:
    """Validate that value is one of the allowed enum values.

    Args:
        value: The value to check
        allowed: Set of allowed values
        field: Field name for error messages

    Returns:
        List of error messages (empty if valid)
    """
    if value is None:
        return []
    if value not in allowed:
        return [f"{field} must be one of {sorted(allowed)}, got {value!r}"]
    return []


def check_bounded(
    value: int | float | None,
    min_val: int | float,
    max_val: int | float,
    field: str,
) -> Iterable[str]:
    """Validate that value is within bounds [min_val, max_val].

    Args:
        value: The numeric value to check
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        field: Field name for error messages

    Returns:
        List of error messages (empty if valid)
    """
    if value is None:
        return []
    if value < min_val or value > max_val:
        return [f"{field} must be between {min_val} and {max_val}, got {value}"]
    return []


def check_positive(value: int | float | None, field: str) -> Iterable[str]:
    """Validate that value is strictly positive (> 0).

    Args:
        value: The numeric value to check
        field: Field name for error messages

    Returns:
        List of error messages (empty if valid)
    """
    if value is None:
        return []
    if value <= 0:
        return [f"{field} must be > 0, got {value}"]
    return []
