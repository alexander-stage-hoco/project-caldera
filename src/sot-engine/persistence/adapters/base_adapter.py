"""Base adapter class for tool output persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import duckdb

from ..entities import ToolRun
from ..repositories import LayoutRepository, ToolRunRepository
from shared.path_utils import normalize_file_path
from ..validation import (
    ensure_lz_tables,
    validate_json_schema,
    validate_lz_schema,
)


class BaseAdapter(ABC):
    """Abstract base class for tool adapters.

    Provides common functionality for:
    - JSON schema validation
    - Landing zone table creation and validation
    - Path normalization
    - Logging

    Subclasses must implement:
    - tool_name property
    - schema_path property
    - lz_tables property
    - table_ddl property
    - _do_persist() method
    - validate_quality() method
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the tool name for logging and error messages."""
        ...

    @property
    @abstractmethod
    def schema_path(self) -> Path:
        """Return the path to the JSON schema file."""
        ...

    @property
    @abstractmethod
    def lz_tables(self) -> dict[str, dict[str, str]]:
        """Return the landing zone table definitions for validation.

        Format: {table_name: {column_name: column_type}}
        """
        ...

    @property
    @abstractmethod
    def table_ddl(self) -> dict[str, str]:
        """Return the DDL statements for creating landing zone tables.

        Format: {table_name: CREATE TABLE statement}
        """
        ...

    def __init__(
        self,
        run_repo: ToolRunRepository,
        layout_repo: LayoutRepository | None = None,
        *,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            run_repo: Repository for tool run records
            layout_repo: Repository for layout records (optional for LayoutAdapter)
            repo_root: Root path of the repository for path normalization
            logger: Optional logging callback function
        """
        self._run_repo = run_repo
        self._layout_repo = layout_repo
        self._repo_root = repo_root
        self._logger = logger

    @property
    def _conn(self) -> duckdb.DuckDBPyConnection:
        """Centralized connection accessor.

        This provides a single point for the type:ignore comment instead of
        duplicating it across all adapter methods.
        """
        return self._run_repo._conn  # type: ignore[return-value]

    def _log(self, message: str) -> None:
        """Log a message if logger is configured."""
        if self._logger:
            self._logger(message)

    def _normalize_path(self, raw_path: str) -> str:
        """Normalize file path to repo-relative format."""
        return normalize_file_path(raw_path, self._repo_root)

    def _create_tool_run(self, metadata: dict) -> int:
        """Create a ToolRun entity from metadata and insert it.

        Args:
            metadata: The metadata dict from the tool output payload

        Returns:
            run_pk: Primary key of the inserted tool run
        """
        # Handle both ISO format with Z suffix and standard format
        timestamp_str = metadata["timestamp"]
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"
        run = ToolRun(
            collection_run_id=metadata["run_id"],
            repo_id=metadata["repo_id"],
            run_id=metadata["run_id"],
            tool_name=metadata["tool_name"],
            tool_version=metadata["tool_version"],
            schema_version=metadata["schema_version"],
            branch=metadata["branch"],
            commit=metadata["commit"],
            timestamp=datetime.fromisoformat(timestamp_str),
        )
        return self._run_repo.insert(run)

    def _get_layout_run_pk(self, run_id: str) -> int:
        """Look up the layout tool run primary key for this collection.

        Args:
            run_id: The run_id to look up layout for

        Returns:
            run_pk: Primary key of the layout tool run

        Raises:
            KeyError: If layout run not found
        """
        try:
            return self._run_repo.get_run_pk_any(
                run_id,
                ["layout-scanner", "layout"],
            )
        except KeyError as exc:
            raise KeyError("layout run not found") from exc

    @staticmethod
    def check_line_range(
        line_start: int | None,
        line_end: int | None,
        field_prefix: str,
    ) -> list[str]:
        """Validate line number range and return any errors.

        Args:
            line_start: Starting line number (must be >= 1 if provided)
            line_end: Ending line number (must be >= 1 if provided)
            field_prefix: Prefix for error messages (e.g., "file[0].smells[1]")

        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        if line_start is not None and line_start < 1:
            errors.append(f"{field_prefix}.line_start must be >= 1")
        if line_end is not None and line_end < 1:
            errors.append(f"{field_prefix}.line_end must be >= 1")
        if line_start is not None and line_end is not None and line_end < line_start:
            errors.append(f"{field_prefix}.line_end must be >= line_start")
        return errors

    def _raise_quality_errors(self, errors: list[str]) -> None:
        """Log and raise quality validation errors.

        Common helper to reduce duplication in validate_quality() implementations.

        Args:
            errors: List of error messages to log and raise

        Raises:
            ValueError: If errors list is non-empty
        """
        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"{self.tool_name} data quality validation failed ({len(errors)} errors)")

    def validate_schema(self, payload: dict) -> None:
        """Validate payload against JSON schema.

        Args:
            payload: The JSON payload to validate

        Raises:
            ValueError: If schema validation fails
        """
        errors = validate_json_schema(payload, self.schema_path)
        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {self.tool_name} schema {error}")
            raise ValueError(f"{self.tool_name} schema validation failed ({len(errors)} errors)")

    def ensure_lz_tables(self) -> list[str]:
        """Create landing zone tables if they don't exist.

        Returns:
            List of table names that were created
        """
        created = ensure_lz_tables(self._conn, self.table_ddl)
        if created:
            for table in created:
                self._log(f"Created landing zone table: {table}")
        return created

    def validate_lz_schema(self) -> None:
        """Validate landing zone tables exist with expected columns.

        Raises:
            ValueError: If schema validation fails
        """
        errors = validate_lz_schema(self._conn, self.lz_tables)
        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {self.tool_name} lz schema {error}")
            raise ValueError(f"{self.tool_name} landing zone schema invalid ({len(errors)} errors)")

    def persist(self, payload: dict) -> int:
        """Validate and persist tool output to database.

        This is a template method that:
        1. Validates the JSON schema
        2. Ensures landing zone tables exist
        3. Validates the landing zone schema
        4. Delegates to _do_persist() for tool-specific persistence

        Args:
            payload: The JSON payload to persist

        Returns:
            run_pk: Primary key of the inserted tool run
        """
        self.validate_schema(payload)
        self.ensure_lz_tables()
        self.validate_lz_schema()
        return self._do_persist(payload)

    @abstractmethod
    def _do_persist(self, payload: dict) -> int:
        """Perform tool-specific persistence logic.

        Called by persist() after schema and table validation.

        Args:
            payload: The validated JSON payload

        Returns:
            run_pk: Primary key of the inserted tool run
        """
        ...

    @abstractmethod
    def validate_quality(self, data: Any) -> None:
        """Validate data quality rules specific to this tool.

        Args:
            data: The data to validate (format varies by tool)

        Raises:
            ValueError: If quality validation fails
        """
        ...
