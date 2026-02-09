"""Adapter for persisting coverage-ingest output to the landing zone."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import CoverageSummary
from ..repositories import CoverageRepository, LayoutRepository, ToolRunRepository
from ..validation import (
    check_non_negative,
    check_required,
    validate_file_paths_in_entries,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "coverage-ingest" / "schemas" / "output.schema.json"

LZ_TABLES = {
    "lz_coverage_summary": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "line_coverage_pct": "DOUBLE",
        "branch_coverage_pct": "DOUBLE",
        "lines_total": "INTEGER",
        "lines_covered": "INTEGER",
        "lines_missed": "INTEGER",
        "branches_total": "INTEGER",
        "branches_covered": "INTEGER",
        "source_format": "VARCHAR",
    }
}

TABLE_DDL = {
    "lz_coverage_summary": """
        CREATE TABLE IF NOT EXISTS lz_coverage_summary (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            line_coverage_pct DOUBLE,
            branch_coverage_pct DOUBLE,
            lines_total INTEGER NOT NULL,
            lines_covered INTEGER NOT NULL,
            lines_missed INTEGER NOT NULL,
            branches_total INTEGER,
            branches_covered INTEGER,
            source_format VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
}

QUALITY_RULES = ["paths", "ranges", "coverage_invariants", "required_fields"]


class CoverageAdapter(BaseAdapter):
    """Adapter for persisting coverage-ingest output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "coverage-ingest"

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
        coverage_repo: CoverageRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._coverage_repo = coverage_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist coverage-ingest output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        source_format = data.get("source_format", "unknown")
        files = data.get("files", [])

        self.validate_quality(files)
        summaries = list(self._map_coverage_summaries(
            run_pk, layout_run_pk, files, source_format
        ))
        self._coverage_repo.insert_summaries(summaries)
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for coverage files."""
        errors: list[str] = []
        # Use shared path validation helper
        errors.extend(validate_file_paths_in_entries(
            files,
            path_field="relative_path",
            repo_root=self._repo_root,
            entry_prefix="coverage file",
        ))
        for idx, entry in enumerate(files):
            # Required fields
            errors.extend(check_required(entry.get("lines_total"), f"file[{idx}].lines_total"))
            errors.extend(check_required(entry.get("lines_covered"), f"file[{idx}].lines_covered"))
            errors.extend(check_required(entry.get("lines_missed"), f"file[{idx}].lines_missed"))

            # Non-negative checks
            errors.extend(check_non_negative(entry.get("lines_total", 0), f"file[{idx}].lines_total"))
            errors.extend(check_non_negative(entry.get("lines_covered", 0), f"file[{idx}].lines_covered"))
            errors.extend(check_non_negative(entry.get("lines_missed", 0), f"file[{idx}].lines_missed"))

            if entry.get("branches_total") is not None:
                errors.extend(check_non_negative(entry.get("branches_total"), f"file[{idx}].branches_total"))
            if entry.get("branches_covered") is not None:
                errors.extend(check_non_negative(entry.get("branches_covered"), f"file[{idx}].branches_covered"))

            # Coverage invariants
            lines_total = entry.get("lines_total", 0) or 0
            lines_covered = entry.get("lines_covered", 0) or 0
            lines_missed = entry.get("lines_missed", 0) or 0

            if lines_covered > lines_total:
                errors.append(f"file[{idx}] lines_covered ({lines_covered}) > lines_total ({lines_total})")
            if lines_missed != lines_total - lines_covered:
                errors.append(
                    f"file[{idx}] lines_missed ({lines_missed}) != "
                    f"lines_total - lines_covered ({lines_total - lines_covered})"
                )

            branches_total = entry.get("branches_total")
            branches_covered = entry.get("branches_covered")
            if branches_total is not None and branches_covered is not None:
                if branches_covered > branches_total:
                    errors.append(
                        f"file[{idx}] branches_covered ({branches_covered}) > "
                        f"branches_total ({branches_total})"
                    )

            # Percentage range checks
            line_pct = entry.get("line_coverage_pct")
            if line_pct is not None and (line_pct < 0 or line_pct > 100):
                errors.append(f"file[{idx}] line_coverage_pct ({line_pct}) must be 0-100")

            branch_pct = entry.get("branch_coverage_pct")
            if branch_pct is not None and (branch_pct < 0 or branch_pct > 100):
                errors.append(f"file[{idx}] branch_coverage_pct ({branch_pct}) must be 0-100")

        self._raise_quality_errors(errors)

    def _map_coverage_summaries(
        self,
        run_pk: int,
        layout_run_pk: int,
        files: Iterable[dict],
        source_format: str,
    ) -> Iterable[CoverageSummary]:
        """Map file entries to CoverageSummary entities.

        Files not found in layout are skipped with a warning.
        """
        seen: set[str] = set()
        for entry in files:
            relative_path = self._normalize_path(entry.get("relative_path", ""))

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                self._log(f"WARN: skipping file not in layout: {relative_path}")
                continue

            # Deduplicate by file_id
            if file_id in seen:
                self._log(f"WARN: skipping duplicate file: {relative_path}")
                continue
            seen.add(file_id)

            yield CoverageSummary(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                line_coverage_pct=entry.get("line_coverage_pct"),
                branch_coverage_pct=entry.get("branch_coverage_pct"),
                lines_total=entry.get("lines_total", 0),
                lines_covered=entry.get("lines_covered", 0),
                lines_missed=entry.get("lines_missed", 0),
                branches_total=entry.get("branches_total"),
                branches_covered=entry.get("branches_covered"),
                source_format=source_format,
            )
