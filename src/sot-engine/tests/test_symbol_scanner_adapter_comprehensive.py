from __future__ import annotations

import copy
import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import SymbolScannerAdapter
from persistence.entities import LayoutDirectory, LayoutFile, ToolRun
from persistence.repositories import LayoutRepository, SymbolScannerRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Load the database schema from schema.sql."""
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _load_fixture() -> dict:
    """Load the symbol-scanner test fixture."""
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "symbol_scanner_output.json"
    return json.loads(fixture_path.read_text())


def _create_layout_run(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    repo_id: str,
    files: list[tuple[str, str, str]] | None = None,
) -> int:
    """Create a layout run with specified files by directly inserting records.

    This bypasses the LayoutAdapter to avoid schema validation complexity,
    while still creating valid layout records for testing.

    Args:
        conn: Database connection
        run_id: The run ID for the layout run
        repo_id: The repository ID
        files: List of (file_id, directory_id, path) tuples for files to create.
               If None, creates files for the symbol-scanner fixture.

    Returns:
        run_pk: Primary key of the layout run
    """
    # Default files match the symbol-scanner fixture
    if files is None:
        files = [
            ("f-000000000001", "d-000000000001", "src/main.py"),
            ("f-000000000002", "d-000000000002", "src/utils/helpers.py"),
        ]

    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)

    # Create tool run record directly
    tool_run = ToolRun(
        collection_run_id=run_id,
        repo_id=repo_id,
        run_id=run_id,
        tool_name="layout-scanner",
        tool_version="1.0.0",
        schema_version="1.0.0",
        branch="main",
        commit="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        timestamp=datetime.now(),
    )
    run_pk = run_repo.insert(tool_run)

    # Build unique directories from files
    directories: dict[str, LayoutDirectory] = {}
    layout_files: list[LayoutFile] = []

    # Create root directory
    directories["."] = LayoutDirectory(
        run_pk=run_pk,
        directory_id="d-root",
        relative_path=".",
        parent_id=None,
        depth=0,
        file_count=len(files),
        total_size_bytes=100 * len(files),
    )

    for file_id, directory_id, path in files:
        parts = path.split("/")
        filename = parts[-1]
        dir_path = "/".join(parts[:-1]) if len(parts) > 1 else "."

        # Create file record
        layout_files.append(LayoutFile(
            run_pk=run_pk,
            file_id=file_id,
            relative_path=path,
            directory_id=directory_id,
            filename=filename,
            extension="." + filename.split(".")[-1] if "." in filename else None,
            language="Python" if filename.endswith(".py") else None,
            category="source",
            size_bytes=100,
            line_count=50,
            is_binary=False,
        ))

        # Create directory if not exists
        if dir_path != "." and dir_path not in directories:
            # Determine parent directory
            parent_parts = parts[:-2]
            parent_path = "/".join(parent_parts) if parent_parts else "."
            parent_id = directories.get(parent_path, directories["."]).directory_id

            directories[dir_path] = LayoutDirectory(
                run_pk=run_pk,
                directory_id=directory_id,
                relative_path=dir_path,
                parent_id=parent_id,
                depth=len(parts) - 1,
                file_count=1,
                total_size_bytes=100,
            )

    # Insert records
    layout_repo.insert_directories(directories.values())
    layout_repo.insert_files(layout_files)

    return run_pk


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def db_conn(tmp_path: Path):
    """Create a fresh database connection with schema loaded."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    _load_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def fixture_payload() -> dict:
    """Return a copy of the symbol-scanner fixture."""
    return _load_fixture()


@pytest.fixture
def repos(db_conn: duckdb.DuckDBPyConnection):
    """Return repository instances for testing."""
    return {
        "run": ToolRunRepository(db_conn),
        "layout": LayoutRepository(db_conn),
        "symbol": SymbolScannerRepository(db_conn),
    }


# =============================================================================
# 1. Basic Insertion Tests
# =============================================================================


class TestBasicInsertion:
    """Tests for verifying correct entity insertion into landing zone tables."""

    def test_adapter_inserts_symbols(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that CodeSymbol entities are correctly inserted into lz_code_symbols."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        # Query symbols
        rows = db_conn.execute(
            """
            SELECT symbol_name, symbol_type, relative_path, line_start, line_end,
                   is_exported, parameters, parent_symbol, docstring
            FROM lz_code_symbols WHERE run_pk = ?
            ORDER BY relative_path, line_start
            """,
            [run_pk],
        ).fetchall()

        assert len(rows) == 5, f"Expected 5 symbols, got {len(rows)}"

        # Check first symbol (parse_args in main.py, line 5)
        row = rows[0]
        assert row[0] == "parse_args"
        assert row[1] == "function"
        assert row[2] == "src/main.py"
        assert row[3] == 5  # line_start
        assert row[4] == 8  # line_end
        assert row[5] is True  # is_exported
        assert row[6] == 1  # parameters
        assert row[7] is None  # parent_symbol
        assert row[8] is None  # docstring

        # Check method with parent_symbol (process in helpers.py)
        method_rows = [r for r in rows if r[0] == "process"]
        assert len(method_rows) == 1
        assert method_rows[0][1] == "method"
        assert method_rows[0][7] == "Helper"  # parent_symbol

    def test_adapter_inserts_calls(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that SymbolCall entities are correctly inserted into lz_symbol_calls."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        rows = db_conn.execute(
            """
            SELECT caller_file_path, caller_symbol, callee_symbol,
                   callee_file_id, callee_file_path, line_number, call_type
            FROM lz_symbol_calls WHERE run_pk = ?
            ORDER BY caller_file_path, line_number
            """,
            [run_pk],
        ).fetchall()

        assert len(rows) == 5, f"Expected 5 calls, got {len(rows)}"

        # Check first call (main -> parse_args)
        row = rows[0]
        assert row[0] == "src/main.py"  # caller_file_path
        assert row[1] == "main"  # caller_symbol
        assert row[2] == "parse_args"  # callee_symbol
        assert row[4] == "src/main.py"  # callee_file_path (same file)
        assert row[5] == 12  # line_number
        assert row[6] == "direct"  # call_type

        # Check cross-file call (main -> Helper)
        helper_call = [r for r in rows if r[2] == "Helper"][0]
        assert helper_call[4] == "src/utils/helpers.py"  # callee_file_path

    def test_adapter_inserts_imports(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that FileImport entities are correctly inserted into lz_file_imports."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        rows = db_conn.execute(
            """
            SELECT relative_path, imported_path, imported_symbols, import_type, line_number
            FROM lz_file_imports WHERE run_pk = ?
            ORDER BY relative_path, line_number
            """,
            [run_pk],
        ).fetchall()

        assert len(rows) == 4, f"Expected 4 imports, got {len(rows)}"

        # Check main.py imports
        main_imports = [r for r in rows if r[0] == "src/main.py"]
        assert len(main_imports) == 2
        assert main_imports[0][1] == "argparse"  # imported_path
        assert main_imports[0][2] is None  # imported_symbols (module import)
        assert main_imports[0][3] == "static"  # import_type

        # Check helpers.py imports
        helper_imports = [r for r in rows if r[0] == "src/utils/helpers.py"]
        assert len(helper_imports) == 2
        assert any(r[2] == "Any, Dict" for r in helper_imports)  # imported_symbols


# =============================================================================
# 2. Layout Dependency Tests
# =============================================================================


class TestLayoutDependency:
    """Tests for layout run dependency handling."""

    def test_adapter_raises_on_missing_layout(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that adapter raises KeyError when no layout run exists."""
        # Don't create a layout run

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )

        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(fixture_payload)

    def test_adapter_skips_symbols_not_in_layout(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that symbols in files not tracked by layout are skipped with warning."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        # Create layout with only main.py (not helpers.py)
        _create_layout_run(db_conn, run_id, repo_id, files=[
            ("f-000000000001", "d-000000000001", "src/main.py"),
        ])

        log_messages = []
        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"),
            logger=lambda msg: log_messages.append(msg),
        )
        run_pk = adapter.persist(fixture_payload)

        # Should only have symbols from main.py (2 symbols)
        count = db_conn.execute(
            "SELECT COUNT(*) FROM lz_code_symbols WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2, f"Expected 2 symbols (from main.py only), got {count}"

        # Check warning was logged
        warns = [m for m in log_messages if "WARN" in m and "untracked" in m]
        assert len(warns) >= 1, "Expected warning for skipped files"

    def test_adapter_skips_calls_from_untracked_files(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that calls from files not in layout are skipped."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        # Create layout with only main.py
        _create_layout_run(db_conn, run_id, repo_id, files=[
            ("f-000000000001", "d-000000000001", "src/main.py"),
        ])

        log_messages = []
        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"),
            logger=lambda msg: log_messages.append(msg),
        )
        run_pk = adapter.persist(fixture_payload)

        # Count calls from main.py only (4 calls from main, 1 from helpers)
        count = db_conn.execute(
            "SELECT COUNT(*) FROM lz_symbol_calls WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 4, f"Expected 4 calls (from main.py only), got {count}"

    def test_adapter_skips_imports_not_in_layout(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that imports in files not in layout are skipped."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        # Create layout with only main.py
        _create_layout_run(db_conn, run_id, repo_id, files=[
            ("f-000000000001", "d-000000000001", "src/main.py"),
        ])

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        # Should only have imports from main.py (2 imports)
        count = db_conn.execute(
            "SELECT COUNT(*) FROM lz_file_imports WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2, f"Expected 2 imports (from main.py only), got {count}"


# =============================================================================
# 3. Data Quality Validation Tests
# =============================================================================


class TestDataQualityValidation:
    """Tests for data quality validation rules.

    Note: Some validations are caught at schema validation level (enum constraints,
    numeric ranges) while others are caught at data quality validation level.
    Tests match either error type since both are valid rejection mechanisms.
    """

    def test_adapter_rejects_invalid_symbol_type(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that invalid symbol_type values are rejected.

        Schema validation catches this because symbol_type is an enum constraint.
        """
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        # Modify fixture to have invalid symbol_type
        fixture_payload["data"]["symbols"][0]["symbol_type"] = "invalid_type"

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )

        # Schema or data quality validation catches invalid enum
        with pytest.raises(ValueError, match="(schema validation failed|data quality validation failed)"):
            adapter.persist(fixture_payload)

    def test_adapter_validates_symbol_line_ranges(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that line_start > line_end is rejected."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        # Modify fixture to have invalid line range
        fixture_payload["data"]["symbols"][0]["line_start"] = 100
        fixture_payload["data"]["symbols"][0]["line_end"] = 50

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )

        with pytest.raises(ValueError, match="(schema validation failed|data quality validation failed)"):
            adapter.persist(fixture_payload)

    def test_adapter_validates_parameters_nonnegative(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that negative parameters count is rejected.

        Schema validation catches this because parameters has minimum: 0 constraint.
        """
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        # Modify fixture to have negative parameters
        fixture_payload["data"]["symbols"][0]["parameters"] = -1

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )

        # Schema validation catches out-of-range values (minimum: 0)
        with pytest.raises(ValueError, match="(schema validation failed|data quality validation failed)"):
            adapter.persist(fixture_payload)

    def test_adapter_rejects_invalid_call_type(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that invalid call_type values are rejected.

        Schema validation catches this because call_type is an enum constraint.
        """
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        # Modify fixture to have invalid call_type
        fixture_payload["data"]["calls"][0]["call_type"] = "invalid_call"

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )

        # Schema validation catches invalid enum
        with pytest.raises(ValueError, match="(schema validation failed|data quality validation failed)"):
            adapter.persist(fixture_payload)

    def test_adapter_rejects_invalid_import_type(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that invalid import_type values are rejected.

        Schema validation catches this because import_type is an enum constraint.
        """
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        # Modify fixture to have invalid import_type
        fixture_payload["data"]["imports"][0]["import_type"] = "invalid_import"

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )

        # Schema validation catches invalid enum
        with pytest.raises(ValueError, match="(schema validation failed|data quality validation failed)"):
            adapter.persist(fixture_payload)

    def test_adapter_validates_line_numbers_positive(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that line numbers must be >= 1.

        Schema validation catches this because line_start has minimum: 1 constraint.
        """
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        # Modify fixture to have zero line_start
        fixture_payload["data"]["symbols"][0]["line_start"] = 0

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )

        # Schema or entity validation should catch line_start < 1
        with pytest.raises(ValueError):
            adapter.persist(fixture_payload)


# =============================================================================
# 4. Optional Field Handling Tests
# =============================================================================


class TestOptionalFieldHandling:
    """Tests for handling of optional/nullable fields."""

    def test_adapter_handles_null_parent_symbol(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that symbols without parent_symbol (functions vs methods) are handled."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        # Query symbols with and without parent
        rows = db_conn.execute(
            """
            SELECT symbol_name, symbol_type, parent_symbol
            FROM lz_code_symbols WHERE run_pk = ?
            ORDER BY symbol_name
            """,
            [run_pk],
        ).fetchall()

        # Find function (no parent) and method (has parent)
        functions = [r for r in rows if r[2] is None]
        methods = [r for r in rows if r[2] is not None]

        assert len(functions) >= 1, "Expected at least one function without parent"
        assert len(methods) >= 1, "Expected at least one method with parent"

        # Verify the method's parent
        process_method = [r for r in rows if r[0] == "process"][0]
        assert process_method[2] == "Helper"

    def test_adapter_handles_null_docstring(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that symbols with null docstrings are handled correctly."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        rows = db_conn.execute(
            """
            SELECT symbol_name, docstring
            FROM lz_code_symbols WHERE run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        # Check mix of null and non-null docstrings
        with_doc = [r for r in rows if r[1] is not None]
        without_doc = [r for r in rows if r[1] is None]

        assert len(with_doc) >= 1, "Expected at least one symbol with docstring"
        assert len(without_doc) >= 1, "Expected at least one symbol without docstring"

        # Verify specific docstring
        main_func = [r for r in rows if r[0] == "main"][0]
        assert main_func[1] == "Main entry point for the application."

    def test_adapter_handles_null_callee_file(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that calls to external/unresolved targets have null callee_file."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        # The fixture has a call to "print" with callee_file: null
        rows = db_conn.execute(
            """
            SELECT callee_symbol, callee_file_id, callee_file_path
            FROM lz_symbol_calls WHERE run_pk = ? AND callee_symbol = 'print'
            """,
            [run_pk],
        ).fetchall()

        assert len(rows) == 1, "Expected one call to print"
        assert rows[0][1] is None, "callee_file_id should be NULL for external call"
        assert rows[0][2] is None, "callee_file_path should be NULL for external call"

    def test_adapter_handles_null_imported_symbols(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that module imports (no specific symbols) have null imported_symbols."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        rows = db_conn.execute(
            """
            SELECT imported_path, imported_symbols
            FROM lz_file_imports WHERE run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        # argparse import has null imported_symbols (module import)
        argparse_import = [r for r in rows if r[0] == "argparse"][0]
        assert argparse_import[1] is None, "Module import should have NULL imported_symbols"

        # typing import has specific symbols
        typing_import = [r for r in rows if r[0] == "typing"][0]
        assert typing_import[1] == "Any, Dict", "Named import should have imported_symbols"


# =============================================================================
# 5. Integration Tests
# =============================================================================


class TestIntegration:
    """End-to-end integration tests."""

    def test_adapter_persists_full_fixture(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that the full fixture is persisted with correct counts."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        # Verify tool run was created
        assert run_pk > 0

        # Verify symbol counts match fixture summary
        symbol_count = db_conn.execute(
            "SELECT COUNT(*) FROM lz_code_symbols WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert symbol_count == 5, f"Expected 5 symbols, got {symbol_count}"

        # Verify call counts match fixture summary
        call_count = db_conn.execute(
            "SELECT COUNT(*) FROM lz_symbol_calls WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert call_count == 5, f"Expected 5 calls, got {call_count}"

        # Verify import counts match fixture summary
        import_count = db_conn.execute(
            "SELECT COUNT(*) FROM lz_file_imports WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert import_count == 4, f"Expected 4 imports, got {import_count}"

        # Verify symbol types distribution
        type_dist = dict(db_conn.execute(
            """
            SELECT symbol_type, COUNT(*) FROM lz_code_symbols
            WHERE run_pk = ? GROUP BY symbol_type
            """,
            [run_pk],
        ).fetchall())
        assert type_dist.get("function", 0) == 3, "Expected 3 functions"
        assert type_dist.get("class", 0) == 1, "Expected 1 class"
        assert type_dist.get("method", 0) == 1, "Expected 1 method"

    def test_adapter_joins_with_layout_files(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that persisted data can be joined with layout files."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        # Join symbols with layout files
        joined_rows = db_conn.execute(
            """
            SELECT cs.symbol_name, cs.relative_path, lf.relative_path AS layout_path
            FROM lz_code_symbols cs
            JOIN lz_tool_runs tr_ss
              ON tr_ss.run_pk = cs.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr_ss.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk
             AND lf.file_id = cs.file_id
            WHERE cs.run_pk = ?
            ORDER BY cs.symbol_name
            """,
            [run_pk],
        ).fetchall()

        # All 5 symbols should join with layout files
        assert len(joined_rows) == 5, f"Expected 5 joined rows, got {len(joined_rows)}"

        # Paths should match
        for row in joined_rows:
            assert row[1] == row[2], f"Symbol path {row[1]} should match layout path {row[2]}"

    def test_adapter_call_deduplication(self, db_conn: duckdb.DuckDBPyConnection, fixture_payload: dict, repos: dict) -> None:
        """Test that duplicate calls (same PK) are deduplicated."""
        run_id = fixture_payload["metadata"]["run_id"]
        repo_id = fixture_payload["metadata"]["repo_id"]

        _create_layout_run(db_conn, run_id, repo_id)

        # Add a duplicate call entry
        duplicate_call = copy.deepcopy(fixture_payload["data"]["calls"][0])
        fixture_payload["data"]["calls"].append(duplicate_call)

        adapter = SymbolScannerAdapter(
            repos["run"], repos["layout"], repos["symbol"], Path("/tmp/test-repo"), None
        )
        run_pk = adapter.persist(fixture_payload)

        # Count should still be 5 (deduped)
        call_count = db_conn.execute(
            "SELECT COUNT(*) FROM lz_symbol_calls WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert call_count == 5, f"Expected 5 calls (deduped), got {call_count}"
