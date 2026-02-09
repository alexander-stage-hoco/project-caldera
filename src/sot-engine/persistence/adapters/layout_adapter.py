"""Adapter for layout-scanner output persistence."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import LayoutDirectory, LayoutFile
from ..repositories import LayoutRepository, ToolRunRepository
from shared.path_utils import is_repo_relative_path, normalize_dir_path, normalize_file_path
from ..validation import (
    check_non_negative,
    check_required,
    validate_file_paths_in_entries,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "layout-scanner" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_layout_files": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "directory_id": "VARCHAR",
    },
    "lz_layout_directories": {
        "run_pk": "BIGINT",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "depth": "INTEGER",
    },
}
TABLE_DDL = {
    "lz_layout_files": """
        CREATE TABLE IF NOT EXISTS lz_layout_files (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            filename VARCHAR NOT NULL,
            extension VARCHAR,
            language VARCHAR,
            category VARCHAR,
            size_bytes BIGINT,
            line_count INTEGER,
            is_binary BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
    "lz_layout_directories": """
        CREATE TABLE IF NOT EXISTS lz_layout_directories (
            run_pk BIGINT NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            parent_id VARCHAR,
            depth INTEGER NOT NULL,
            file_count INTEGER,
            total_size_bytes BIGINT,
            PRIMARY KEY (run_pk, directory_id)
        )
    """,
}
QUALITY_RULES = ["paths", "ranges", "required_fields"]


class LayoutAdapter(BaseAdapter):
    """Adapts layout-scanner JSON output to entity objects for persistence.

    Unlike other adapters, LayoutAdapter writes TO the layout repository
    rather than reading from it to resolve file IDs.
    """

    @property
    def tool_name(self) -> str:
        return "layout"

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
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)

    def _do_persist(self, payload: dict) -> int:
        """Persist layout-scanner output to landing zone.

        Args:
            payload: Envelope-formatted JSON with metadata and data sections

        Returns:
            run_pk: The primary key of the inserted tool run
        """
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)

        # Extract files and directories from data section
        # layout-scanner uses a map structure: {"files": {"path": {...}, ...}}
        files_map = data.get("files", {})
        directories_map = data.get("directories", {})

        self.validate_quality(files_map, directories_map)

        # Map files to LayoutFile entities
        files = list(self._map_files(run_pk, files_map))
        self._layout_repo.insert_files(files)

        # Map directories to LayoutDirectory entities
        directories = list(self._map_directories(run_pk, directories_map))
        self._layout_repo.insert_directories(directories)

        return run_pk

    def validate_quality(self, files_map: Any, directories_map: Any = None) -> None:
        """Validate data quality rules for layout files and directories."""
        if directories_map is None:
            directories_map = {}

        errors: list[str] = []

        # Flatten files map to list for shared helper
        flattened_files = [
            {"path": entry.get("path", key)}
            for key, entry in files_map.items()
        ]
        errors.extend(validate_file_paths_in_entries(
            flattened_files,
            path_field="path",
            repo_root=self._repo_root,
            entry_prefix="layout file",
        ))

        # Validate file-specific fields
        for idx, (path, entry) in enumerate(files_map.items()):
            errors.extend(check_required(entry.get("id"), f"file[{idx}].id"))
            errors.extend(check_non_negative(entry.get("size_bytes", 0), f"file[{idx}].size_bytes"))
            errors.extend(check_non_negative(entry.get("line_count", 0), f"file[{idx}].line_count"))

        # Keep inline validation for directories (uses normalize_dir_path and special root handling)
        for idx, (path, entry) in enumerate(directories_map.items()):
            raw_path = entry.get("path", path)
            normalized = normalize_dir_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized) and normalized != ".":
                errors.append(f"layout dir[{idx}] path invalid: {raw_path} -> {normalized}")
            errors.extend(check_required(entry.get("id"), f"dir[{idx}].id"))
            errors.extend(check_non_negative(entry.get("depth", 0), f"dir[{idx}].depth"))
            errors.extend(check_non_negative(entry.get("recursive_file_count", 0), f"dir[{idx}].recursive_file_count"))
            errors.extend(check_non_negative(entry.get("recursive_size_bytes", 0), f"dir[{idx}].recursive_size_bytes"))

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"layout data quality validation failed ({len(errors)} errors)")

    def _map_files(
        self, run_pk: int, files_map: dict
    ) -> Iterable[LayoutFile]:
        """Map layout-scanner file entries to LayoutFile entities."""
        for path, entry in files_map.items():
            relative_path = normalize_file_path(entry.get("path", path), self._repo_root)

            # Skip root path which is empty or "."
            if not relative_path or relative_path == ".":
                continue

            # Extract directory ID from parent_directory_id
            directory_id = entry.get("parent_directory_id", "")

            yield LayoutFile(
                run_pk=run_pk,
                file_id=entry.get("id", ""),
                relative_path=relative_path,
                directory_id=directory_id,
                filename=entry.get("name", ""),
                extension=entry.get("extension"),
                language=entry.get("language"),
                category=entry.get("classification"),
                size_bytes=entry.get("size_bytes"),
                line_count=entry.get("line_count"),
                is_binary=entry.get("is_binary"),
            )

    def _map_directories(
        self, run_pk: int, directories_map: dict
    ) -> Iterable[LayoutDirectory]:
        """Map layout-scanner directory entries to LayoutDirectory entities."""
        for path, entry in directories_map.items():
            relative_path = normalize_dir_path(entry.get("path", path), self._repo_root)

            # Handle root directory specially - use "." as path
            if not relative_path:
                relative_path = "."

            yield LayoutDirectory(
                run_pk=run_pk,
                directory_id=entry.get("id", ""),
                relative_path=relative_path,
                parent_id=entry.get("parent_directory_id"),
                depth=entry.get("depth", 0),
                file_count=entry.get("recursive_file_count"),
                total_size_bytes=entry.get("recursive_size_bytes"),
            )
