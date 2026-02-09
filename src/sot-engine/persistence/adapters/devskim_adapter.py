from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import DevskimFinding
from ..repositories import DevskimRepository, LayoutRepository, ToolRunRepository
from shared.path_utils import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_required,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "devskim" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_devskim_findings": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "rule_id": "VARCHAR",
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
    "lz_devskim_findings": """
        CREATE TABLE IF NOT EXISTS lz_devskim_findings (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            rule_id VARCHAR NOT NULL,
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


class DevskimAdapter(BaseAdapter):
    """Adapter for persisting devskim security analysis output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "devskim"

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
        devskim_repo: DevskimRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._devskim_repo = devskim_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist devskim output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        files = data.get("files", [])
        self.validate_quality(files)
        findings = list(self._map_findings(run_pk, layout_run_pk, files))
        self._devskim_repo.insert_findings(findings)
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for devskim files."""
        errors = []
        for file_idx, file_entry in enumerate(files):
            raw_path = file_entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"devskim file[{file_idx}] path invalid: {raw_path} -> {normalized}")

            for issue_idx, issue in enumerate(file_entry.get("issues", [])):
                errors.extend(
                    check_required(issue.get("rule_id"), f"file[{file_idx}].issues[{issue_idx}].rule_id")
                )
                errors.extend(
                    self.check_line_range(
                        issue.get("line_start"),
                        issue.get("line_end"),
                        f"file[{file_idx}].issues[{issue_idx}]",
                    )
                )

        self._raise_quality_errors(errors)

    def _map_findings(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[DevskimFinding]:
        """Map file entries with issues to DevskimFinding entities."""
        seen: set[tuple[str, str, int | None]] = set()
        for file_entry in files:
            relative_path = self._normalize_path(file_entry.get("path", ""))

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                # Skip files not in layout (external dependencies, generated files, etc.)
                self._log(f"WARN: skipping file not in layout: {relative_path}")
                continue

            for issue in file_entry.get("issues", []):
                key = (file_id, issue.get("rule_id", ""), issue.get("line_start"))
                if key in seen:
                    self._log(
                        f"WARN: skipping duplicate issue {key[1]} at {relative_path}:{key[2]}"
                    )
                    continue
                seen.add(key)
                yield DevskimFinding(
                    run_pk=run_pk,
                    file_id=file_id,
                    directory_id=directory_id,
                    relative_path=relative_path,
                    rule_id=issue.get("rule_id", ""),
                    dd_category=issue.get("dd_category"),
                    severity=issue.get("severity"),
                    line_start=issue.get("line_start"),
                    line_end=issue.get("line_end"),
                    column_start=issue.get("column_start"),
                    column_end=issue.get("column_end"),
                    message=issue.get("message"),
                    code_snippet=issue.get("code_snippet"),
                )
