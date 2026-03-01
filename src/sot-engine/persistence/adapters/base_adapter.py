"""Base adapter class for tool output persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import duckdb

from ..entities import ToolRun
from ..repositories import LayoutRepository, ToolRunRepository
from shared.path_utils import normalize_file_path
from ..validation import (
    ensure_lz_tables,
    validate_json_schema,
    validate_lz_schema,
)

if TYPE_CHECKING:
    from ..quality import DataQualityChecker


LAYOUT_TOOL_NAMES = ["layout-scanner", "layout"]


class _DedupTracker:
    """Tracks seen keys and logs duplicate warnings."""

    def __init__(self, entity_type: str, log_fn: Callable[[str], None]) -> None:
        self._seen: set[Hashable] = set()
        self._entity_type = entity_type
        self._log = log_fn

    def is_duplicate(self, key: Hashable, label: str = "") -> bool:
        """Return True if key was already seen. Logs warning on duplicates."""
        if key in self._seen:
            display = label or str(key)
            self._log(f"WARN: skipping duplicate {self._entity_type}: {display}")
            return True
        self._seen.add(key)
        return False


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
        quality_checker: DataQualityChecker | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            run_repo: Repository for tool run records
            layout_repo: Repository for layout records (optional for LayoutScannerAdapter)
            repo_root: Root path of the repository for path normalization
            logger: Optional logging callback function
            quality_checker: Optional centralized quality checker for post-persist checks
        """
        self._run_repo = run_repo
        self._layout_repo = layout_repo
        self._repo_root = repo_root
        self._logger = logger
        self._quality_checker = quality_checker

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

    def _dedup_tracker(self, entity_type: str) -> _DedupTracker:
        """Create a dedup tracker for use in mapping loops."""
        return _DedupTracker(entity_type, self._log)

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
                LAYOUT_TOOL_NAMES,
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
        """
        Validate and persist a tool's JSON payload to the landing zone and record a tool run.
        
        Performs schema validation, ensures landing-zone tables exist and match expected schema, delegates tool-specific persistence to `_do_persist`, and (if a quality checker is configured) runs post-persist quality checks. Post-persist quality check failures are logged as quality warnings and do not raise.
        
        Parameters:
            payload (dict): Tool output containing at least `metadata` and tool-specific data.
        
        Returns:
            int: Primary key (`run_pk`) of the inserted tool run.
        """
        # Pre-persist: check metadata completeness if quality checker is set
        metadata_complete = True
        if self._quality_checker:
            meta_result = self._quality_checker.check_metadata(
                payload.get("metadata", {}), self.tool_name,
            )
            metadata_complete = meta_result.passed

        self.validate_schema(payload)
        self.ensure_lz_tables()
        self.validate_lz_schema()
        run_pk = self._do_persist(payload)

        # Post-persist: advisory quality report (never raises)
        if self._quality_checker:
            try:
                collection_run_id = payload.get("metadata", {}).get("run_id", "")
                self._run_post_persist_quality(run_pk, metadata_complete, collection_run_id)
            except Exception as exc:
                self._log(f"QUALITY_WARNING: post-persist checks failed: {exc}")

        return run_pk

    def _run_post_persist_quality(
        self, run_pk: int, metadata_complete: bool, collection_run_id: str = "",
    ) -> None:
        """
        Run post-persist data quality checks for landing-zone tables and persist a quality report when a collection_run_id is provided.
        
        Performs foreign-key integrity checks for any landing-zone table that includes a `file_id` column and uniqueness checks on a minimal set of key columns for each table, then builds an aggregated quality report. This operation is advisory only: it does nothing if no quality checker is configured and does not raise exceptions.
        
        Parameters:
            run_pk (int): Primary key of the tool run to scope FK and uniqueness checks.
            metadata_complete (bool): Whether the run's metadata was determined to be complete.
            collection_run_id (str): Optional collection-wide run identifier; if provided the quality report is persisted.
        """
        if not self._quality_checker:
            return

        checks = []

        # FK integrity check for tables that have file_id
        for table_name in self.lz_tables:
            if "file_id" in self.lz_tables[table_name]:
                result = self._quality_checker.check_fk_integrity(
                    table_name, "file_id", run_pk, self.tool_name,
                )
                checks.append(result)

        # Uniqueness check on key columns
        for table_name, columns in self.lz_tables.items():
            key_cols = ["run_pk"] + [c for c in columns if c != "run_pk"][:1]
            if len(key_cols) >= 2:
                result = self._quality_checker.check_uniqueness(
                    table_name, key_cols, self.tool_name,
                )
                checks.append(result)

        report = self._quality_checker.build_report(
            self.tool_name,
            checks,
            schema_valid=True,
            metadata_complete=metadata_complete,
        )

        # Persist the quality report to lz_quality_checks (advisory, never blocks)
        if collection_run_id:
            self._quality_checker.persist_report(report, collection_run_id)

    @abstractmethod
    def _do_persist(self, payload: dict) -> int:
        """
        Persist tool-specific data from the validated payload and return the inserted tool run primary key.
        
        Parameters:
            payload (dict): Validated JSON payload containing tool run data to persist.
        
        Returns:
            run_pk (int): Primary key of the newly inserted tool run.
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
