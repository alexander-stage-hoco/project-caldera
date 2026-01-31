"""Tests for adapter ensure_lz_tables() functionality."""
from __future__ import annotations

import duckdb
import pytest

from persistence.adapters.scc_adapter import SccAdapter, TABLE_DDL as SCC_TABLE_DDL
from persistence.adapters.lizard_adapter import LizardAdapter, TABLE_DDL as LIZARD_TABLE_DDL
from persistence.adapters.layout_adapter import LayoutAdapter, TABLE_DDL as LAYOUT_TABLE_DDL
from persistence.adapters.semgrep_adapter import SemgrepAdapter, TABLE_DDL as SEMGREP_TABLE_DDL
from persistence.adapters.roslyn_adapter import RoslynAdapter, TABLE_DDL as ROSLYN_TABLE_DDL
from persistence.repositories import (
    ToolRunRepository,
    LayoutRepository,
    SccRepository,
    LizardRepository,
    SemgrepRepository,
    RoslynRepository,
)
from persistence.validation import ensure_lz_tables, CORE_TABLE_DDL


def _table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    return conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ?",
        [table_name],
    ).fetchone() is not None


def _sequence_exists(conn: duckdb.DuckDBPyConnection, sequence_name: str) -> bool:
    """Check if a sequence exists in the database."""
    return conn.execute(
        "SELECT 1 FROM duckdb_sequences() WHERE sequence_name = ?",
        [sequence_name],
    ).fetchone() is not None


class TestEnsureLzTables:
    """Tests for the ensure_lz_tables() utility function."""

    def test_creates_missing_tables(self) -> None:
        """ensure_lz_tables should create tables that don't exist."""
        conn = duckdb.connect(":memory:")
        ddl = {
            "test_table": "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)"
        }

        created = ensure_lz_tables(conn, ddl, include_core=False)

        assert "test_table" in created
        assert _table_exists(conn, "test_table")

    def test_skips_existing_tables(self) -> None:
        """ensure_lz_tables should not recreate existing tables."""
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY)")
        ddl = {
            "test_table": "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)"
        }

        created = ensure_lz_tables(conn, ddl, include_core=False)

        assert "test_table" not in created
        assert _table_exists(conn, "test_table")

    def test_creates_core_tables_by_default(self) -> None:
        """ensure_lz_tables should create core tables when include_core=True."""
        conn = duckdb.connect(":memory:")

        created = ensure_lz_tables(conn, {}, include_core=True)

        assert "lz_run_pk_seq" in created
        assert "lz_collection_runs" in created
        assert "lz_tool_runs" in created
        assert _sequence_exists(conn, "lz_run_pk_seq")
        assert _table_exists(conn, "lz_collection_runs")
        assert _table_exists(conn, "lz_tool_runs")

    def test_idempotent_calls(self) -> None:
        """Calling ensure_lz_tables twice should not error."""
        conn = duckdb.connect(":memory:")
        ddl = {
            "test_table": "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)"
        }

        # First call creates
        created1 = ensure_lz_tables(conn, ddl, include_core=False)
        # Second call should return empty list
        created2 = ensure_lz_tables(conn, ddl, include_core=False)

        assert "test_table" in created1
        assert "test_table" not in created2


class TestSccAdapterEnsureLzTables:
    """Tests for SccAdapter.ensure_lz_tables()."""

    def test_creates_missing_tables(self) -> None:
        """SccAdapter should create lz_scc_file_metrics if missing."""
        conn = duckdb.connect(":memory:")
        adapter = SccAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            SccRepository(conn),
        )

        # Table doesn't exist yet
        assert not _table_exists(conn, "lz_scc_file_metrics")

        # ensure_lz_tables creates it
        created = adapter.ensure_lz_tables()

        assert "lz_scc_file_metrics" in created
        assert _table_exists(conn, "lz_scc_file_metrics")
        # Core tables should also be created
        assert _table_exists(conn, "lz_tool_runs")
        assert _table_exists(conn, "lz_collection_runs")

    def test_idempotent(self) -> None:
        """Calling ensure_lz_tables twice should not error."""
        conn = duckdb.connect(":memory:")
        adapter = SccAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            SccRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.ensure_lz_tables()  # Should not raise

    def test_logs_created_tables(self) -> None:
        """ensure_lz_tables should log when tables are created."""
        conn = duckdb.connect(":memory:")
        log_messages = []
        adapter = SccAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            SccRepository(conn),
            logger=log_messages.append,
        )

        adapter.ensure_lz_tables()

        assert any("lz_scc_file_metrics" in msg for msg in log_messages)


class TestLizardAdapterEnsureLzTables:
    """Tests for LizardAdapter.ensure_lz_tables()."""

    def test_creates_missing_tables(self) -> None:
        """LizardAdapter should create lz_lizard_* tables if missing."""
        conn = duckdb.connect(":memory:")
        adapter = LizardAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            LizardRepository(conn),
        )

        # Tables don't exist yet
        assert not _table_exists(conn, "lz_lizard_file_metrics")
        assert not _table_exists(conn, "lz_lizard_function_metrics")

        # ensure_lz_tables creates them
        created = adapter.ensure_lz_tables()

        assert "lz_lizard_file_metrics" in created
        assert "lz_lizard_function_metrics" in created
        assert _table_exists(conn, "lz_lizard_file_metrics")
        assert _table_exists(conn, "lz_lizard_function_metrics")

    def test_idempotent(self) -> None:
        """Calling ensure_lz_tables twice should not error."""
        conn = duckdb.connect(":memory:")
        adapter = LizardAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            LizardRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.ensure_lz_tables()  # Should not raise


class TestLayoutAdapterEnsureLzTables:
    """Tests for LayoutAdapter.ensure_lz_tables()."""

    def test_creates_missing_tables(self) -> None:
        """LayoutAdapter should create lz_layout_* tables if missing."""
        conn = duckdb.connect(":memory:")
        adapter = LayoutAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
        )

        # Tables don't exist yet
        assert not _table_exists(conn, "lz_layout_files")
        assert not _table_exists(conn, "lz_layout_directories")

        # ensure_lz_tables creates them
        created = adapter.ensure_lz_tables()

        assert "lz_layout_files" in created
        assert "lz_layout_directories" in created
        assert _table_exists(conn, "lz_layout_files")
        assert _table_exists(conn, "lz_layout_directories")

    def test_idempotent(self) -> None:
        """Calling ensure_lz_tables twice should not error."""
        conn = duckdb.connect(":memory:")
        adapter = LayoutAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.ensure_lz_tables()  # Should not raise


class TestSemgrepAdapterEnsureLzTables:
    """Tests for SemgrepAdapter.ensure_lz_tables()."""

    def test_creates_missing_tables(self) -> None:
        """SemgrepAdapter should create lz_semgrep_smells if missing."""
        conn = duckdb.connect(":memory:")
        adapter = SemgrepAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            SemgrepRepository(conn),
        )

        # Table doesn't exist yet
        assert not _table_exists(conn, "lz_semgrep_smells")

        # ensure_lz_tables creates it
        created = adapter.ensure_lz_tables()

        assert "lz_semgrep_smells" in created
        assert _table_exists(conn, "lz_semgrep_smells")

    def test_idempotent(self) -> None:
        """Calling ensure_lz_tables twice should not error."""
        conn = duckdb.connect(":memory:")
        adapter = SemgrepAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            SemgrepRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.ensure_lz_tables()  # Should not raise


class TestValidateLzSchemaAfterEnsure:
    """Tests that validate_lz_schema passes after ensure_lz_tables."""

    def test_scc_validate_passes_after_ensure(self) -> None:
        """SccAdapter.validate_lz_schema should pass after ensure_lz_tables."""
        conn = duckdb.connect(":memory:")
        adapter = SccAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            SccRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.validate_lz_schema()  # Should not raise

    def test_lizard_validate_passes_after_ensure(self) -> None:
        """LizardAdapter.validate_lz_schema should pass after ensure_lz_tables."""
        conn = duckdb.connect(":memory:")
        adapter = LizardAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            LizardRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.validate_lz_schema()  # Should not raise

    def test_layout_validate_passes_after_ensure(self) -> None:
        """LayoutAdapter.validate_lz_schema should pass after ensure_lz_tables."""
        conn = duckdb.connect(":memory:")
        adapter = LayoutAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.validate_lz_schema()  # Should not raise

    def test_semgrep_validate_passes_after_ensure(self) -> None:
        """SemgrepAdapter.validate_lz_schema should pass after ensure_lz_tables."""
        conn = duckdb.connect(":memory:")
        adapter = SemgrepAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            SemgrepRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.validate_lz_schema()  # Should not raise

    def test_roslyn_validate_passes_after_ensure(self) -> None:
        """RoslynAdapter.validate_lz_schema should pass after ensure_lz_tables."""
        conn = duckdb.connect(":memory:")
        adapter = RoslynAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            RoslynRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.validate_lz_schema()  # Should not raise


class TestRoslynAdapterEnsureLzTables:
    """Tests for RoslynAdapter.ensure_lz_tables()."""

    def test_creates_missing_tables(self) -> None:
        """RoslynAdapter should create lz_roslyn_violations if missing."""
        conn = duckdb.connect(":memory:")
        adapter = RoslynAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            RoslynRepository(conn),
        )

        # Table doesn't exist yet
        assert not _table_exists(conn, "lz_roslyn_violations")

        # ensure_lz_tables creates it
        created = adapter.ensure_lz_tables()

        assert "lz_roslyn_violations" in created
        assert _table_exists(conn, "lz_roslyn_violations")
        # Core tables should also be created
        assert _table_exists(conn, "lz_tool_runs")
        assert _table_exists(conn, "lz_collection_runs")

    def test_idempotent(self) -> None:
        """Calling ensure_lz_tables twice should not error."""
        conn = duckdb.connect(":memory:")
        adapter = RoslynAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            RoslynRepository(conn),
        )

        adapter.ensure_lz_tables()
        adapter.ensure_lz_tables()  # Should not raise

    def test_logs_created_tables(self) -> None:
        """ensure_lz_tables should log when tables are created."""
        conn = duckdb.connect(":memory:")
        log_messages = []
        adapter = RoslynAdapter(
            ToolRunRepository(conn),
            LayoutRepository(conn),
            RoslynRepository(conn),
            logger=log_messages.append,
        )

        adapter.ensure_lz_tables()

        assert any("lz_roslyn_violations" in msg for msg in log_messages)
