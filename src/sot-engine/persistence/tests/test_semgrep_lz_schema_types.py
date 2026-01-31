from __future__ import annotations

import duckdb

from pathlib import Path

from persistence.adapters.semgrep_adapter import LZ_TABLES


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    conn.execute(schema_path.read_text())


def test_semgrep_lz_schema_matches_expected_types() -> None:
    conn = duckdb.connect(":memory:")
    try:
        _load_schema(conn)
        columns = conn.execute("PRAGMA table_info('lz_semgrep_smells')").fetchall()
        type_map = {name: col_type.upper() for _, name, col_type, *_ in columns}
        expected = LZ_TABLES["lz_semgrep_smells"]
        for column, col_type in expected.items():
            assert column in type_map
            assert type_map[column] == col_type
    finally:
        conn.close()
