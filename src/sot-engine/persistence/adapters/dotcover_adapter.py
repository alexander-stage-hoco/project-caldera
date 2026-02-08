"""Adapter for persisting dotcover output to the landing zone.

For implementation examples, see:
- persistence/adapters/scc_adapter.py - File metrics adapter
- persistence/adapters/lizard_adapter.py - Multi-table adapter

Documentation:
- docs/TOOL_REQUIREMENTS.md - Adapter requirements
- docs/DEVELOPMENT.md - Integration tutorial
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import (
    DotcoverAssemblyCoverage,
    DotcoverMethodCoverage,
    DotcoverTypeCoverage,
)
from ..repositories import DotcoverRepository, LayoutRepository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_non_negative,
    check_required,
)

# Path to the tool's JSON schema for validation
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "dotcover" / "schemas" / "output.schema.json"

# Landing zone table column definitions (used for validation)
LZ_TABLES = {
    "lz_dotcover_assembly_coverage": {
        "run_pk": "BIGINT",
        "assembly_name": "VARCHAR",
        "covered_statements": "INTEGER",
        "total_statements": "INTEGER",
        "statement_coverage_pct": "DOUBLE",
    },
    "lz_dotcover_type_coverage": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "assembly_name": "VARCHAR",
        "namespace": "VARCHAR",
        "type_name": "VARCHAR",
        "covered_statements": "INTEGER",
        "total_statements": "INTEGER",
        "statement_coverage_pct": "DOUBLE",
    },
    "lz_dotcover_method_coverage": {
        "run_pk": "BIGINT",
        "assembly_name": "VARCHAR",
        "type_name": "VARCHAR",
        "method_name": "VARCHAR",
        "covered_statements": "INTEGER",
        "total_statements": "INTEGER",
        "statement_coverage_pct": "DOUBLE",
    },
}

# DDL statements for creating landing zone tables
TABLE_DDL = {
    "lz_dotcover_assembly_coverage": """
        CREATE TABLE IF NOT EXISTS lz_dotcover_assembly_coverage (
            run_pk BIGINT NOT NULL,
            assembly_name VARCHAR NOT NULL,
            covered_statements INTEGER NOT NULL,
            total_statements INTEGER NOT NULL,
            statement_coverage_pct DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, assembly_name)
        )
    """,
    "lz_dotcover_type_coverage": """
        CREATE TABLE IF NOT EXISTS lz_dotcover_type_coverage (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR,
            directory_id VARCHAR,
            relative_path VARCHAR,
            assembly_name VARCHAR NOT NULL,
            namespace VARCHAR,
            type_name VARCHAR NOT NULL,
            covered_statements INTEGER NOT NULL,
            total_statements INTEGER NOT NULL,
            statement_coverage_pct DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, assembly_name, type_name)
        )
    """,
    "lz_dotcover_method_coverage": """
        CREATE TABLE IF NOT EXISTS lz_dotcover_method_coverage (
            run_pk BIGINT NOT NULL,
            assembly_name VARCHAR NOT NULL,
            type_name VARCHAR NOT NULL,
            method_name VARCHAR NOT NULL,
            covered_statements INTEGER NOT NULL,
            total_statements INTEGER NOT NULL,
            statement_coverage_pct DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, assembly_name, type_name, method_name)
        )
    """,
}

# Quality rules that this adapter validates
QUALITY_RULES = ["coverage_bounds", "statement_invariants", "required_fields"]


def _check_coverage_pct(value: float | None, field_name: str) -> list[str]:
    """Validate coverage percentage is between 0 and 100."""
    if value is None:
        return []
    if value < 0 or value > 100:
        return [f"{field_name} must be between 0 and 100, got {value}"]
    return []


def _check_coverage_invariant(
    covered: int | None,
    total: int | None,
    field_prefix: str,
) -> list[str]:
    """Validate that covered <= total."""
    if covered is None or total is None:
        return []
    if covered > total:
        return [f"{field_prefix}.covered_statements ({covered}) exceeds total_statements ({total})"]
    return []


class DotcoverAdapter(BaseAdapter):
    """Adapter for persisting dotcover output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "dotcover"

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
        dotcover_repo: DotcoverRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._dotcover_repo = dotcover_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist dotcover output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)

        # Get layout run for file lookups (may not be needed if no file paths)
        layout_run_pk = None
        try:
            layout_run_pk = self._get_layout_run_pk(metadata["run_id"])
        except KeyError:
            self._log("Warning: layout run not found, file IDs will be null")

        # Validate and persist assemblies
        assemblies = data.get("assemblies", [])
        self.validate_quality(assemblies, "assembly")
        assembly_entities = list(self._map_assembly_coverage(run_pk, assemblies))
        self._dotcover_repo.insert_assembly_coverage(assembly_entities)

        # Validate and persist types
        types = data.get("types", [])
        self.validate_quality(types, "type")
        type_entities = list(self._map_type_coverage(run_pk, layout_run_pk, types))
        self._dotcover_repo.insert_type_coverage(type_entities)

        # Validate and persist methods
        methods = data.get("methods", [])
        self.validate_quality(methods, "method")
        method_entities = list(self._map_method_coverage(run_pk, methods))
        self._dotcover_repo.insert_method_coverage(method_entities)

        return run_pk

    def validate_quality(self, entries: Any, entry_type: str = "entry") -> None:
        """Validate data quality rules for dotcover entries.

        Args:
            entries: List of coverage entries to validate
            entry_type: Type name for error messages (assembly, type, method)
        """
        errors = []
        for idx, entry in enumerate(entries):
            prefix = f"{entry_type}[{idx}]"

            # Validate required fields based on entry type
            if entry_type == "assembly":
                errors.extend(check_required(entry.get("name"), f"{prefix}.name"))
            elif entry_type == "type":
                errors.extend(check_required(entry.get("assembly"), f"{prefix}.assembly"))
                errors.extend(check_required(entry.get("name"), f"{prefix}.name"))
                # Validate file path if present
                file_path = entry.get("file_path")
                if file_path:
                    normalized = normalize_file_path(file_path, self._repo_root)
                    if not is_repo_relative_path(normalized):
                        errors.append(f"{prefix}.file_path invalid: {file_path} -> {normalized}")
            elif entry_type == "method":
                errors.extend(check_required(entry.get("assembly"), f"{prefix}.assembly"))
                errors.extend(check_required(entry.get("type_name"), f"{prefix}.type_name"))
                errors.extend(check_required(entry.get("name"), f"{prefix}.name"))

            # Validate coverage metrics (common to all types)
            errors.extend(check_non_negative(
                entry.get("covered_statements", 0),
                f"{prefix}.covered_statements",
            ))
            errors.extend(check_non_negative(
                entry.get("total_statements", 0),
                f"{prefix}.total_statements",
            ))
            errors.extend(_check_coverage_pct(
                entry.get("statement_coverage_pct"),
                f"{prefix}.statement_coverage_pct",
            ))
            errors.extend(_check_coverage_invariant(
                entry.get("covered_statements"),
                entry.get("total_statements"),
                prefix,
            ))

        self._raise_quality_errors(errors)

    def _map_assembly_coverage(
        self,
        run_pk: int,
        assemblies: Iterable[dict],
    ) -> Iterable[DotcoverAssemblyCoverage]:
        """Map raw assembly entries to entity objects."""
        for entry in assemblies:
            yield DotcoverAssemblyCoverage(
                run_pk=run_pk,
                assembly_name=entry.get("name", ""),
                covered_statements=entry.get("covered_statements", 0),
                total_statements=entry.get("total_statements", 0),
                statement_coverage_pct=entry.get("statement_coverage_pct", 0.0),
            )

    def _map_type_coverage(
        self,
        run_pk: int,
        layout_run_pk: int | None,
        types: Iterable[dict],
    ) -> Iterable[DotcoverTypeCoverage]:
        """Map raw type entries to entity objects."""
        for entry in types:
            file_id = None
            directory_id = None
            relative_path = None

            # Try to look up file IDs if we have a file path
            raw_path = entry.get("file_path")
            if raw_path and layout_run_pk:
                relative_path = self._normalize_path(raw_path)
                try:
                    file_id, directory_id = self._layout_repo.get_file_record(
                        layout_run_pk, relative_path
                    )
                except KeyError:
                    self._log(f"WARN: type file not in layout: {relative_path}")
                    # Continue with null file_id - valid for generated/external files

            yield DotcoverTypeCoverage(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                assembly_name=entry.get("assembly", ""),
                namespace=entry.get("namespace"),
                type_name=entry.get("name", ""),
                covered_statements=entry.get("covered_statements", 0),
                total_statements=entry.get("total_statements", 0),
                statement_coverage_pct=entry.get("statement_coverage_pct", 0.0),
            )

    def _map_method_coverage(
        self,
        run_pk: int,
        methods: Iterable[dict],
    ) -> Iterable[DotcoverMethodCoverage]:
        """Map raw method entries to entity objects."""
        for entry in methods:
            yield DotcoverMethodCoverage(
                run_pk=run_pk,
                assembly_name=entry.get("assembly", ""),
                type_name=entry.get("type_name", ""),
                method_name=entry.get("name", ""),
                covered_statements=entry.get("covered_statements", 0),
                total_statements=entry.get("total_statements", 0),
                statement_coverage_pct=entry.get("statement_coverage_pct", 0.0),
            )
