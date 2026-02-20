"""Tests for persistence/validation.py — shared validation utilities."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from persistence.validation import (
    check_bounded,
    check_enum,
    check_non_negative,
    check_positive,
    check_ratio,
    check_required,
    ensure_lz_tables,
    validate_file_paths_in_entries,
    validate_json_schema,
    validate_lz_schema,
)


# ── check_required ───────────────────────────────────────────────────────────

class TestCheckRequired:
    def test_none_returns_error(self) -> None:
        errors = list(check_required(None, "name"))
        assert errors == ["name is required"]

    def test_empty_string_returns_error(self) -> None:
        errors = list(check_required("", "name"))
        assert errors == ["name is required"]

    def test_valid_value_returns_empty(self) -> None:
        assert list(check_required("hello", "name")) == []


# ── check_non_negative ──────────────────────────────────────────────────────

class TestCheckNonNegative:
    def test_none_skips(self) -> None:
        assert list(check_non_negative(None, "x")) == []

    def test_zero_passes(self) -> None:
        assert list(check_non_negative(0, "x")) == []

    def test_positive_passes(self) -> None:
        assert list(check_non_negative(42, "x")) == []

    def test_negative_fails(self) -> None:
        errors = list(check_non_negative(-1, "x"))
        assert len(errors) == 1
        assert "must be >= 0" in errors[0]


# ── check_ratio ─────────────────────────────────────────────────────────────

class TestCheckRatio:
    def test_none_skips(self) -> None:
        assert list(check_ratio(None, "r")) == []

    def test_zero_passes(self) -> None:
        assert list(check_ratio(0.0, "r")) == []

    def test_one_passes(self) -> None:
        assert list(check_ratio(1.0, "r")) == []

    def test_mid_passes(self) -> None:
        assert list(check_ratio(0.5, "r")) == []

    def test_out_of_range_fails(self) -> None:
        assert len(list(check_ratio(1.1, "r"))) == 1
        assert len(list(check_ratio(-0.1, "r"))) == 1


# ── check_enum ──────────────────────────────────────────────────────────────

class TestCheckEnum:
    def test_none_skips(self) -> None:
        assert list(check_enum(None, {"a", "b"}, "f")) == []

    def test_valid_value_passes(self) -> None:
        assert list(check_enum("a", {"a", "b"}, "f")) == []

    def test_invalid_value_fails(self) -> None:
        errors = list(check_enum("c", {"a", "b"}, "f"))
        assert len(errors) == 1
        assert "must be one of" in errors[0]

    def test_error_message_format(self) -> None:
        errors = list(check_enum("bad", {"x", "y"}, "myfield"))
        assert "myfield" in errors[0]
        assert "'bad'" in errors[0]


# ── check_bounded ───────────────────────────────────────────────────────────

class TestCheckBounded:
    def test_none_skips(self) -> None:
        assert list(check_bounded(None, 0, 10, "v")) == []

    def test_min_boundary_passes(self) -> None:
        assert list(check_bounded(0, 0, 10, "v")) == []

    def test_max_boundary_passes(self) -> None:
        assert list(check_bounded(10, 0, 10, "v")) == []

    def test_below_min_fails(self) -> None:
        errors = list(check_bounded(-1, 0, 10, "v"))
        assert len(errors) == 1
        assert "must be between" in errors[0]

    def test_above_max_fails(self) -> None:
        errors = list(check_bounded(11, 0, 10, "v"))
        assert len(errors) == 1


# ── check_positive ──────────────────────────────────────────────────────────

class TestCheckPositive:
    def test_none_skips(self) -> None:
        assert list(check_positive(None, "p")) == []

    def test_positive_passes(self) -> None:
        assert list(check_positive(1, "p")) == []

    def test_zero_rejected(self) -> None:
        errors = list(check_positive(0, "p"))
        assert len(errors) == 1
        assert "must be > 0" in errors[0]

    def test_negative_rejected(self) -> None:
        errors = list(check_positive(-5, "p"))
        assert len(errors) == 1


# ── validate_file_paths_in_entries ──────────────────────────────────────────

class TestValidateFilePathsInEntries:
    def test_valid_paths(self) -> None:
        entries = [{"path": "src/main.py"}, {"path": "lib/utils.py"}]
        assert validate_file_paths_in_entries(entries) == []

    def test_absolute_path_normalized_away(self) -> None:
        # normalize_file_path strips leading '/', so absolute paths become valid
        entries = [{"path": "/usr/local/src/main.py"}]
        errors = validate_file_paths_in_entries(entries)
        assert errors == []  # normalization makes it repo-relative

    def test_dotdot_rejected(self) -> None:
        entries = [{"path": "../escape/file.py"}]
        errors = validate_file_paths_in_entries(entries)
        assert len(errors) == 1

    def test_empty_entries(self) -> None:
        assert validate_file_paths_in_entries([]) == []

    def test_custom_prefix(self) -> None:
        entries = [{"path": "../escape/file.py"}]
        errors = validate_file_paths_in_entries(entries, entry_prefix="scc file")
        assert len(errors) == 1
        assert "scc file[0]" in errors[0]


# ── validate_json_schema ────────────────────────────────────────────────────

class TestValidateJsonSchema:
    @pytest.fixture
    def schema_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / "tools" / "scc" / "schemas" / "output.schema.json"

    def test_valid_payload(self, schema_path: Path) -> None:
        if not schema_path.exists():
            pytest.skip("scc output schema not found")
        payload = json.loads(
            (Path(__file__).resolve().parents[1] / "fixtures" / "scc_output.json").read_text()
        )
        errors = validate_json_schema(payload, schema_path)
        assert errors == []

    def test_invalid_payload(self, schema_path: Path) -> None:
        if not schema_path.exists():
            pytest.skip("scc output schema not found")
        errors = validate_json_schema({"wrong": "structure"}, schema_path)
        assert len(errors) > 0


# ── ensure_lz_tables ────────────────────────────────────────────────────────

class TestEnsureLzTables:
    def test_creates_new_tables(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        # Use a fresh connection without schema.sql loaded
        conn = duckdb.connect(":memory:")
        ddl = {
            "lz_test_table": "CREATE TABLE IF NOT EXISTS lz_test_table (id INTEGER PRIMARY KEY, name VARCHAR)"
        }
        created = ensure_lz_tables(conn, ddl, include_core=True)
        # Should have created core tables + our custom table
        assert "lz_test_table" in created
        assert "lz_collection_runs" in created
        assert "lz_tool_runs" in created

    def test_skips_existing(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        # duckdb_conn already has schema.sql loaded
        ddl = {
            "lz_scc_file_metrics": "CREATE TABLE IF NOT EXISTS lz_scc_file_metrics (id INTEGER)"
        }
        created = ensure_lz_tables(duckdb_conn, ddl, include_core=True)
        # Everything already exists; nothing should be created
        assert created == []

    def test_include_core_false(self) -> None:
        conn = duckdb.connect(":memory:")
        ddl = {
            "lz_custom": "CREATE TABLE IF NOT EXISTS lz_custom (id INTEGER)"
        }
        created = ensure_lz_tables(conn, ddl, include_core=False)
        assert "lz_custom" in created
        # Core tables should NOT be created
        assert "lz_collection_runs" not in created
        assert "lz_tool_runs" not in created


# ── validate_lz_schema ──────────────────────────────────────────────────────

class TestValidateLzSchema:
    def test_all_present(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        expected = {
            "lz_scc_file_metrics": {
                "run_pk": "BIGINT",
                "file_id": "VARCHAR",
                "relative_path": "VARCHAR",
            }
        }
        errors = validate_lz_schema(duckdb_conn, expected)
        assert errors == []

    def test_missing_table(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        expected = {"lz_nonexistent": {"col": "VARCHAR"}}
        errors = validate_lz_schema(duckdb_conn, expected)
        assert any("missing table" in e for e in errors)

    def test_column_type_mismatch(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        expected = {
            "lz_scc_file_metrics": {
                "run_pk": "VARCHAR",  # Actually BIGINT
            }
        }
        errors = validate_lz_schema(duckdb_conn, expected)
        assert any("type mismatch" in e for e in errors)
