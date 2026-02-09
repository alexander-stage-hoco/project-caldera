"""Adapter for symbol-scanner tool output."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import CodeSymbol, SymbolCall, FileImport
from ..repositories import LayoutRepository, SymbolScannerRepository, ToolRunRepository
from ..validation import (
    check_non_negative,
    check_required,
    validate_file_paths_in_entries,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "symbol-scanner" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_code_symbols": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "symbol_name": "VARCHAR",
        "symbol_type": "VARCHAR",
        "line_start": "INTEGER",
    },
    "lz_symbol_calls": {
        "run_pk": "BIGINT",
        "caller_file_id": "VARCHAR",
        "caller_file_path": "VARCHAR",
        "caller_symbol": "VARCHAR",
        "callee_symbol": "VARCHAR",
        "line_number": "INTEGER",
    },
    "lz_file_imports": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "imported_path": "VARCHAR",
        "line_number": "INTEGER",
    },
}
TABLE_DDL = {
    "lz_code_symbols": """
        CREATE TABLE IF NOT EXISTS lz_code_symbols (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            symbol_name VARCHAR NOT NULL,
            symbol_type VARCHAR NOT NULL,
            line_start INTEGER,
            line_end INTEGER,
            is_exported BOOLEAN DEFAULT FALSE,
            parameters INTEGER,
            parent_symbol VARCHAR,
            docstring TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, symbol_name, line_start)
        )
    """,
    "lz_symbol_calls": """
        CREATE TABLE IF NOT EXISTS lz_symbol_calls (
            run_pk BIGINT NOT NULL,
            caller_file_id VARCHAR NOT NULL,
            caller_directory_id VARCHAR NOT NULL,
            caller_file_path VARCHAR NOT NULL,
            caller_symbol VARCHAR NOT NULL,
            callee_symbol VARCHAR NOT NULL,
            callee_file_id VARCHAR,
            callee_file_path VARCHAR,
            line_number INTEGER,
            call_type VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, caller_file_id, caller_symbol, callee_symbol, line_number)
        )
    """,
    "lz_file_imports": """
        CREATE TABLE IF NOT EXISTS lz_file_imports (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            imported_path VARCHAR NOT NULL,
            imported_symbols VARCHAR,
            import_type VARCHAR,
            line_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, imported_path, line_number)
        )
    """,
}
QUALITY_RULES = ["paths", "ranges", "required_fields"]


class SymbolScannerAdapter(BaseAdapter):
    """Adapter for persisting symbol-scanner output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "symbol-scanner"

    @property
    def schema_path(self) -> Path:
        return SCHEMA_PATH

    @property
    def lz_tables(self) -> dict[str, dict[str, str]]:
        return LZ_TABLES

    @property
    def table_ddl(self) -> dict[str, str]:
        return TABLE_DDL

    def __init__(
        self,
        run_repo: ToolRunRepository,
        layout_repo: LayoutRepository,
        symbol_repo: SymbolScannerRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._symbol_repo = symbol_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist symbol-scanner output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        # Validate quality
        self.validate_quality(data)

        # Map and persist symbols
        symbols = self._map_symbols(run_pk, layout_run_pk, data.get("symbols", []))
        self._symbol_repo.insert_symbols(symbols)

        # Map and persist calls
        calls = self._map_calls(run_pk, layout_run_pk, data.get("calls", []))
        self._symbol_repo.insert_calls(calls)

        # Map and persist imports
        imports = self._map_imports(run_pk, layout_run_pk, data.get("imports", []))
        self._symbol_repo.insert_imports(imports)

        return run_pk

    def validate_quality(self, data: dict) -> None:
        """Validate data quality rules for symbol-scanner output."""
        errors: list[str] = []

        # Validate symbol paths using shared helper
        errors.extend(validate_file_paths_in_entries(
            data.get("symbols", []),
            path_field="path",
            repo_root=self._repo_root,
            entry_prefix="symbol",
        ))

        # Validate symbol-specific fields
        for idx, symbol in enumerate(data.get("symbols", [])):
            errors.extend(check_required(symbol.get("symbol_name"), f"symbol[{idx}].symbol_name"))
            errors.extend(check_required(symbol.get("symbol_type"), f"symbol[{idx}].symbol_type"))
            if symbol.get("symbol_type") not in ("function", "class", "method", "variable"):
                errors.append(f"symbol[{idx}].symbol_type invalid: {symbol.get('symbol_type')}")
            if symbol.get("line_start") and symbol.get("line_end"):
                if symbol.get("line_start") > symbol.get("line_end"):
                    errors.append(f"symbol[{idx}] line_start > line_end")
            errors.extend(check_non_negative(symbol.get("parameters"), f"symbol[{idx}].parameters"))

        # Validate call paths using shared helper
        errors.extend(validate_file_paths_in_entries(
            data.get("calls", []),
            path_field="caller_file",
            repo_root=self._repo_root,
            entry_prefix="call",
        ))

        # Validate call-specific fields
        for idx, call in enumerate(data.get("calls", [])):
            errors.extend(check_required(call.get("caller_symbol"), f"call[{idx}].caller_symbol"))
            errors.extend(check_required(call.get("callee_symbol"), f"call[{idx}].callee_symbol"))
            if call.get("call_type") and call.get("call_type") not in ("direct", "dynamic", "async"):
                errors.append(f"call[{idx}].call_type invalid: {call.get('call_type')}")

        # Validate import paths using shared helper
        errors.extend(validate_file_paths_in_entries(
            data.get("imports", []),
            path_field="file",
            repo_root=self._repo_root,
            entry_prefix="import",
        ))

        # Validate import-specific fields
        for idx, imp in enumerate(data.get("imports", [])):
            errors.extend(check_required(imp.get("imported_path"), f"import[{idx}].imported_path"))
            if imp.get("import_type") and imp.get("import_type") not in ("static", "dynamic", "type_checking", "side_effect"):
                errors.append(f"import[{idx}].import_type invalid: {imp.get('import_type')}")

        self._raise_quality_errors(errors)

    def _map_symbols(
        self, run_pk: int, layout_run_pk: int, symbols: Iterable[dict]
    ) -> list[CodeSymbol]:
        """Map symbol entries to CodeSymbol entities."""
        result: list[CodeSymbol] = []

        for symbol in symbols:
            relative_path = self._normalize_path(symbol.get("path", ""))
            try:
                file_id, directory_id = self._layout_repo.get_file_record(layout_run_pk, relative_path)
            except KeyError:
                self._log(f"WARN: skipping symbol in untracked file: {relative_path}")
                continue

            result.append(
                CodeSymbol(
                    run_pk=run_pk,
                    file_id=file_id,
                    directory_id=directory_id,
                    relative_path=relative_path,
                    symbol_name=symbol.get("symbol_name", ""),
                    symbol_type=symbol.get("symbol_type", "function"),
                    line_start=symbol.get("line_start"),
                    line_end=symbol.get("line_end"),
                    is_exported=symbol.get("is_exported", False),
                    parameters=symbol.get("parameters"),
                    parent_symbol=symbol.get("parent_symbol"),
                    docstring=symbol.get("docstring"),
                )
            )

        return result

    def _map_calls(
        self, run_pk: int, layout_run_pk: int, calls: Iterable[dict]
    ) -> list[SymbolCall]:
        """Map call entries to SymbolCall entities, deduplicating by primary key."""
        # Use dict to deduplicate by PK (caller_file_id, caller_symbol, callee_symbol, line_number)
        unique_calls: dict[tuple, SymbolCall] = {}

        for call in calls:
            caller_path = self._normalize_path(call.get("caller_file", ""))
            try:
                caller_file_id, caller_directory_id = self._layout_repo.get_file_record(layout_run_pk, caller_path)
            except KeyError:
                self._log(f"WARN: skipping call from untracked file: {caller_path}")
                continue

            # Handle optional callee_file
            callee_file_id = None
            callee_file_path = None
            if call.get("callee_file"):
                callee_path = self._normalize_path(call.get("callee_file", ""))
                try:
                    callee_file_id, _ = self._layout_repo.get_file_record(layout_run_pk, callee_path)
                    callee_file_path = callee_path
                except KeyError:
                    self._log(f"WARN: callee file not in layout (external): {callee_path}")
                    # External/unresolved - keep callee_file_id as None

            caller_symbol = call.get("caller_symbol", "")
            callee_symbol = call.get("callee_symbol", "")
            line_number = call.get("line_number")

            # Deduplicate by primary key columns
            pk = (caller_file_id, caller_symbol, callee_symbol, line_number)
            if pk not in unique_calls:
                unique_calls[pk] = SymbolCall(
                    run_pk=run_pk,
                    caller_file_id=caller_file_id,
                    caller_directory_id=caller_directory_id,
                    caller_file_path=caller_path,
                    caller_symbol=caller_symbol,
                    callee_symbol=callee_symbol,
                    callee_file_id=callee_file_id,
                    callee_file_path=callee_file_path,
                    line_number=line_number,
                    call_type=call.get("call_type"),
                )

        return list(unique_calls.values())

    def _map_imports(
        self, run_pk: int, layout_run_pk: int, imports: Iterable[dict]
    ) -> list[FileImport]:
        """Map import entries to FileImport entities."""
        result: list[FileImport] = []

        for imp in imports:
            relative_path = self._normalize_path(imp.get("file", ""))
            try:
                file_id, directory_id = self._layout_repo.get_file_record(layout_run_pk, relative_path)
            except KeyError:
                self._log(f"WARN: skipping import in untracked file: {relative_path}")
                continue

            result.append(
                FileImport(
                    run_pk=run_pk,
                    file_id=file_id,
                    directory_id=directory_id,
                    relative_path=relative_path,
                    imported_path=imp.get("imported_path", ""),
                    imported_symbols=imp.get("imported_symbols"),
                    import_type=imp.get("import_type"),
                    line_number=imp.get("line_number"),
                )
            )

        return result
