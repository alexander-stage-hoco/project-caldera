from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import SemgrepSmell
from ..repositories import LayoutRepository, SemgrepRepository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_required,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "semgrep" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_semgrep_smells": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "rule_id": "VARCHAR",
        "dd_smell_id": "VARCHAR",
        "dd_category": "VARCHAR",
        "severity": "VARCHAR",
        "line_start": "INTEGER",
        "line_end": "INTEGER",
        "column_start": "INTEGER",
        "column_end": "INTEGER",
        "message": "VARCHAR",
        "code_snippet": "VARCHAR",
    }
}
TABLE_DDL = {
    "lz_semgrep_smells": """
        CREATE TABLE IF NOT EXISTS lz_semgrep_smells (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR,
            relative_path VARCHAR NOT NULL,
            rule_id VARCHAR NOT NULL,
            dd_smell_id VARCHAR,
            dd_category VARCHAR,
            severity VARCHAR,
            line_start INTEGER,
            line_end INTEGER,
            column_start INTEGER,
            column_end INTEGER,
            message TEXT,
            code_snippet TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, rule_id, line_start)
        )
    """,
}
QUALITY_RULES = ["paths", "line_numbers", "required_fields"]


class SemgrepAdapter(BaseAdapter):
    """Adapter for persisting semgrep smell analysis output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "semgrep"

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
        semgrep_repo: SemgrepRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._semgrep_repo = semgrep_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist semgrep output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        files = data.get("files", [])
        self.validate_quality(files)
        smells = list(self._map_smells(run_pk, layout_run_pk, files))
        self._semgrep_repo.insert_smells(smells)
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for semgrep files."""
        errors = []
        for file_idx, file_entry in enumerate(files):
            raw_path = file_entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"semgrep file[{file_idx}] path invalid: {raw_path} -> {normalized}")

            for smell_idx, smell in enumerate(file_entry.get("smells", [])):
                errors.extend(
                    check_required(smell.get("rule_id"), f"file[{file_idx}].smells[{smell_idx}].rule_id")
                )
                errors.extend(
                    self.check_line_range(
                        smell.get("line_start"),
                        smell.get("line_end"),
                        f"file[{file_idx}].smells[{smell_idx}]",
                    )
                )

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"semgrep data quality validation failed ({len(errors)} errors)")

    def _map_smells(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[SemgrepSmell]:
        """Map file entries with smells to SemgrepSmell entities."""
        seen: set[tuple[str, str, int | None]] = set()
        for file_entry in files:
            relative_path = self._normalize_path(file_entry.get("path", ""))

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError as exc:
                self._log(f"DATA_QUALITY_ERROR: file not in layout: {relative_path}")
                raise ValueError(f"semgrep file not in layout: {relative_path}") from exc

            for smell in file_entry.get("smells", []):
                key = (file_id, smell.get("rule_id", ""), smell.get("line_start"))
                if key in seen:
                    self._log(
                        f"WARN: skipping duplicate smell {key[1]} at {relative_path}:{key[2]}"
                    )
                    continue
                seen.add(key)
                yield SemgrepSmell(
                    run_pk=run_pk,
                    file_id=file_id,
                    directory_id=directory_id,
                    relative_path=relative_path,
                    rule_id=smell.get("rule_id", ""),
                    dd_smell_id=smell.get("dd_smell_id"),
                    dd_category=smell.get("dd_category"),
                    severity=smell.get("severity"),
                    line_start=smell.get("line_start"),
                    line_end=smell.get("line_end"),
                    column_start=smell.get("column_start"),
                    column_end=smell.get("column_end"),
                    message=smell.get("message"),
                    code_snippet=smell.get("code_snippet"),
                )
