from __future__ import annotations

import json
from pathlib import Path

import pytest

from persistence.adapters import SymbolScannerAdapter
from persistence.repositories import (
    LayoutRepository,
    SymbolScannerRepository,
    ToolRunRepository,
)


def test_symbol_scanner_adapter_inserts_symbols(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists code symbol records."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "symbol_scanner_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced by symbol-scanner
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/main.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    symbol_repo = SymbolScannerRepository(duckdb_conn)
    adapter = SymbolScannerAdapter(
        tool_run_repo,
        layout_repo,
        symbol_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify symbols were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, symbol_name, symbol_type, is_exported
           FROM lz_code_symbols WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 5  # 5 symbols in fixture
    symbols_by_name = {row[1]: row for row in result}

    assert "main" in symbols_by_name
    assert symbols_by_name["main"][2] == "function"
    assert symbols_by_name["main"][3] is True

    assert "Helper" in symbols_by_name
    assert symbols_by_name["Helper"][2] == "class"

    assert "_internal_helper" in symbols_by_name
    assert symbols_by_name["_internal_helper"][3] is False


def test_symbol_scanner_adapter_inserts_calls(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists symbol call records."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "symbol_scanner_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/main.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    symbol_repo = SymbolScannerRepository(duckdb_conn)
    adapter = SymbolScannerAdapter(
        tool_run_repo,
        layout_repo,
        symbol_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify calls were inserted
    result = duckdb_conn.execute(
        """SELECT caller_file_path, caller_symbol, callee_symbol, callee_file_path
           FROM lz_symbol_calls WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 5  # 5 calls in fixture

    # Verify cross-file call from main -> Helper
    cross_file_calls = [r for r in result if r[1] == "main" and r[2] == "Helper"]
    assert len(cross_file_calls) == 1
    assert cross_file_calls[0][0] == "src/main.py"
    assert cross_file_calls[0][3] == "src/utils/helpers.py"


def test_symbol_scanner_adapter_inserts_imports(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists file import records."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "symbol_scanner_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/main.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    symbol_repo = SymbolScannerRepository(duckdb_conn)
    adapter = SymbolScannerAdapter(
        tool_run_repo,
        layout_repo,
        symbol_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify imports were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, imported_path, imported_symbols, import_type
           FROM lz_file_imports WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 4  # 4 imports in fixture

    imports_by_path = {}
    for row in result:
        key = (row[0], row[1])
        imports_by_path[key] = row

    # Verify argparse import in main.py
    assert ("src/main.py", "argparse") in imports_by_path
    assert imports_by_path[("src/main.py", "argparse")][3] == "static"

    # Verify typing import in helpers.py
    assert ("src/utils/helpers.py", "typing") in imports_by_path
    assert imports_by_path[("src/utils/helpers.py", "typing")][2] == "Any, Dict"


def test_symbol_scanner_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter raises KeyError when no layout run exists."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "symbol_scanner_output.json"
    payload = json.loads(fixture_path.read_text())

    symbol_repo = SymbolScannerRepository(duckdb_conn)
    adapter = SymbolScannerAdapter(
        tool_run_repo,
        layout_repo,
        symbol_repo,
    )

    with pytest.raises(KeyError):
        adapter.persist(payload)
