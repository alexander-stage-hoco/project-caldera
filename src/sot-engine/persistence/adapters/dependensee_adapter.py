"""Adapter for persisting dependensee output to the landing zone.

DependenSee analyzes .NET project dependencies including:
- Project-to-project references
- NuGet package dependencies
- Target framework information
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import DependenseeProject, DependenseeProjectReference, DependenseePackageReference
from ..repositories import DependenseeRepository, LayoutRepository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_non_negative,
    check_required,
)

# Path to the tool's JSON schema for validation
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "dependensee" / "schemas" / "output.schema.json"

# Landing zone table column definitions (used for validation)
LZ_TABLES = {
    "lz_dependensee_projects": {
        "run_pk": "BIGINT",
        "project_path": "VARCHAR",
        "project_name": "VARCHAR",
        "target_framework": "VARCHAR",
        "project_reference_count": "INTEGER",
        "package_reference_count": "INTEGER",
    },
    "lz_dependensee_project_refs": {
        "run_pk": "BIGINT",
        "source_project_path": "VARCHAR",
        "target_project_path": "VARCHAR",
    },
    "lz_dependensee_package_refs": {
        "run_pk": "BIGINT",
        "project_path": "VARCHAR",
        "package_name": "VARCHAR",
        "package_version": "VARCHAR",
    },
}

# DDL statements for creating landing zone tables
TABLE_DDL = {
    "lz_dependensee_projects": """
        CREATE TABLE IF NOT EXISTS lz_dependensee_projects (
            run_pk BIGINT NOT NULL,
            project_path VARCHAR NOT NULL,
            project_name VARCHAR NOT NULL,
            target_framework VARCHAR,
            project_reference_count INTEGER NOT NULL,
            package_reference_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, project_path)
        )
    """,
    "lz_dependensee_project_refs": """
        CREATE TABLE IF NOT EXISTS lz_dependensee_project_refs (
            run_pk BIGINT NOT NULL,
            source_project_path VARCHAR NOT NULL,
            target_project_path VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, source_project_path, target_project_path)
        )
    """,
    "lz_dependensee_package_refs": """
        CREATE TABLE IF NOT EXISTS lz_dependensee_package_refs (
            run_pk BIGINT NOT NULL,
            project_path VARCHAR NOT NULL,
            package_name VARCHAR NOT NULL,
            package_version VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, project_path, package_name)
        )
    """,
}

# Quality rules that this adapter validates
QUALITY_RULES = ["paths", "required_fields"]


class DependenseeAdapter(BaseAdapter):
    """Adapter for persisting dependensee output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "dependensee"

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
        dependensee_repo: DependenseeRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._dependensee_repo = dependensee_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist dependensee output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)

        projects = data.get("projects", [])
        self.validate_quality(projects)

        # Persist projects
        project_entities = list(self._map_projects(run_pk, projects))
        self._dependensee_repo.insert_projects(project_entities)

        # Persist project references
        project_refs = list(self._map_project_refs(run_pk, projects))
        self._dependensee_repo.insert_project_references(project_refs)

        # Persist package references
        package_refs = list(self._map_package_refs(run_pk, projects))
        self._dependensee_repo.insert_package_references(package_refs)

        return run_pk

    def validate_quality(self, projects: Any) -> None:
        """Validate data quality rules for dependensee output."""
        errors = []
        for idx, entry in enumerate(projects):
            # Path validation
            raw_path = entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"project[{idx}] path invalid: {raw_path} -> {normalized}")

            # Required fields
            errors.extend(check_required(entry.get("name"), f"project[{idx}].name"))

            # Validate project references are repo-relative
            for ref_idx, ref in enumerate(entry.get("project_references", [])):
                ref_normalized = normalize_file_path(ref, self._repo_root)
                if not is_repo_relative_path(ref_normalized):
                    errors.append(f"project[{idx}].project_references[{ref_idx}] invalid path: {ref}")

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"dependensee data quality validation failed ({len(errors)} errors)")

    def _map_projects(
        self, run_pk: int, projects: Iterable[dict]
    ) -> Iterable[DependenseeProject]:
        """Map raw project entries to entity objects."""
        for entry in projects:
            yield DependenseeProject(
                run_pk=run_pk,
                project_path=self._normalize_path(entry.get("path", "")),
                project_name=entry.get("name", ""),
                target_framework=entry.get("target_framework"),
                project_reference_count=len(entry.get("project_references", [])),
                package_reference_count=len(entry.get("package_references", [])),
            )

    def _map_project_refs(
        self, run_pk: int, projects: Iterable[dict]
    ) -> Iterable[DependenseeProjectReference]:
        """Map project references to entity objects."""
        for entry in projects:
            source_path = self._normalize_path(entry.get("path", ""))
            for ref in entry.get("project_references", []):
                yield DependenseeProjectReference(
                    run_pk=run_pk,
                    source_project_path=source_path,
                    target_project_path=self._normalize_path(ref),
                )

    def _map_package_refs(
        self, run_pk: int, projects: Iterable[dict]
    ) -> Iterable[DependenseePackageReference]:
        """Map package references to entity objects."""
        for entry in projects:
            project_path = self._normalize_path(entry.get("path", ""))
            for pkg in entry.get("package_references", []):
                yield DependenseePackageReference(
                    run_pk=run_pk,
                    project_path=project_path,
                    package_name=pkg.get("name", ""),
                    package_version=pkg.get("version"),
                )
