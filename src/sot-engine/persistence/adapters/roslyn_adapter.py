from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import RoslynViolation
from ..repositories import LayoutRepository, RoslynRepository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_required,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "roslyn-analyzers" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_roslyn_violations": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "rule_id": "VARCHAR",
        "dd_category": "VARCHAR",
        "severity": "VARCHAR",
        "message": "VARCHAR",
        "line_start": "INTEGER",
        "line_end": "INTEGER",
        "column_start": "INTEGER",
        "column_end": "INTEGER",
    }
}
TABLE_DDL = {
    "lz_roslyn_violations": """
        CREATE TABLE IF NOT EXISTS lz_roslyn_violations (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            rule_id VARCHAR NOT NULL,
            dd_category VARCHAR NOT NULL,
            severity VARCHAR NOT NULL,
            message TEXT,
            line_start INTEGER,
            line_end INTEGER,
            column_start INTEGER,
            column_end INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, rule_id, line_start, column_start)
        )
    """,
}
QUALITY_RULES = ["paths", "line_numbers", "required_fields"]


class RoslynAdapter(BaseAdapter):
    """Adapter for persisting roslyn-analyzers violation output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "roslyn-analyzers"

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
        roslyn_repo: RoslynRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._roslyn_repo = roslyn_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist roslyn output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        files = data.get("files", [])
        self.validate_quality(files)
        violations = list(self._map_violations(run_pk, layout_run_pk, files))

        # De-duplicate by primary key (run_pk, file_id, rule_id, line_start, column_start)
        seen_keys: set[tuple] = set()
        unique_violations = []
        for v in violations:
            key = (v.run_pk, v.file_id, v.rule_id, v.line_start, v.column_start)
            if key not in seen_keys:
                seen_keys.add(key)
                unique_violations.append(v)
            else:
                self._log(f"WARN: skipping duplicate violation {v.rule_id} at {v.relative_path}:{v.line_start}")

        self._roslyn_repo.insert_violations(unique_violations)
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for roslyn files."""
        errors = []
        for file_idx, file_entry in enumerate(files):
            raw_path = file_entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"roslyn file[{file_idx}] path invalid: {raw_path} -> {normalized}")

            for violation_idx, violation in enumerate(file_entry.get("violations", [])):
                prefix = f"file[{file_idx}].violations[{violation_idx}]"
                errors.extend(check_required(violation.get("rule_id"), f"{prefix}.rule_id"))
                errors.extend(check_required(violation.get("dd_category"), f"{prefix}.dd_category"))
                errors.extend(check_required(violation.get("severity"), f"{prefix}.severity"))
                errors.extend(
                    self.check_line_range(
                        violation.get("line_start"),
                        violation.get("line_end"),
                        prefix,
                    )
                )

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"roslyn data quality validation failed ({len(errors)} errors)")

    def _map_violations(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[RoslynViolation]:
        """Map file entries with violations to RoslynViolation entities."""
        for file_entry in files:
            relative_path = self._normalize_path(file_entry.get("path", ""))

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError as exc:
                self._log(f"DATA_QUALITY_ERROR: file not in layout: {relative_path}")
                raise ValueError(f"roslyn file not in layout: {relative_path}") from exc

            for violation in file_entry.get("violations", []):
                yield RoslynViolation(
                    run_pk=run_pk,
                    file_id=file_id,
                    directory_id=directory_id,
                    relative_path=relative_path,
                    rule_id=violation.get("rule_id", ""),
                    dd_category=violation.get("dd_category", "other"),
                    severity=violation.get("severity", "MEDIUM"),
                    message=violation.get("message"),
                    line_start=violation.get("line_start"),
                    line_end=violation.get("line_end"),
                    column_start=violation.get("column_start"),
                    column_end=violation.get("column_end"),
                )
