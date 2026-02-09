from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import SccFileMetric
from ..repositories import LayoutRepository, SccRepository, ToolRunRepository
from ..validation import (
    check_non_negative,
    check_ratio,
    check_required,
    validate_file_paths_in_entries,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "scc" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_scc_file_metrics": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
    }
}
TABLE_DDL = {
    "lz_scc_file_metrics": """
        CREATE TABLE IF NOT EXISTS lz_scc_file_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            filename VARCHAR,
            extension VARCHAR,
            language VARCHAR,
            lines_total INTEGER,
            code_lines INTEGER,
            comment_lines INTEGER,
            blank_lines INTEGER,
            bytes BIGINT,
            complexity INTEGER,
            uloc INTEGER,
            comment_ratio DOUBLE,
            blank_ratio DOUBLE,
            code_ratio DOUBLE,
            complexity_density DOUBLE,
            dryness DOUBLE,
            bytes_per_loc DOUBLE,
            is_minified BOOLEAN,
            is_generated BOOLEAN,
            is_binary BOOLEAN,
            classification VARCHAR,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
}
QUALITY_RULES = ["paths", "ranges", "ratios", "required_fields"]


def _coalesce(*values):
    for value in values:
        if value is not None:
            return value
    return None


class SccAdapter(BaseAdapter):
    """Adapter for persisting scc output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "scc"

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
        scc_repo: SccRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._scc_repo = scc_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist scc output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        self.validate_quality(data.get("files", []))
        metrics = list(self._map_file_metrics(run_pk, layout_run_pk, data.get("files", [])))
        self._scc_repo.insert_file_metrics(metrics)
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for scc files."""
        errors: list[str] = []
        # Use shared path validation helper
        errors.extend(validate_file_paths_in_entries(
            files,
            path_field="path",
            repo_root=self._repo_root,
            entry_prefix="scc file",
        ))
        for idx, entry in enumerate(files):
            errors.extend(check_required(entry.get("filename"), f"file[{idx}].filename"))
            errors.extend(check_non_negative(entry.get("lines", 0), f"file[{idx}].lines"))
            errors.extend(check_non_negative(entry.get("code", 0), f"file[{idx}].code"))
            errors.extend(check_non_negative(entry.get("comment", 0), f"file[{idx}].comment"))
            errors.extend(check_non_negative(entry.get("blank", 0), f"file[{idx}].blank"))
            errors.extend(check_non_negative(entry.get("bytes", 0), f"file[{idx}].bytes"))
            errors.extend(check_non_negative(entry.get("complexity", 0), f"file[{idx}].complexity"))
            errors.extend(check_ratio(entry.get("comment_ratio"), f"file[{idx}].comment_ratio"))
            errors.extend(check_ratio(entry.get("blank_ratio"), f"file[{idx}].blank_ratio"))
            errors.extend(check_ratio(entry.get("code_ratio"), f"file[{idx}].code_ratio"))
            lines = entry.get("lines", 0) or 0
            if (entry.get("code", 0) or 0) + (entry.get("comment", 0) or 0) + (entry.get("blank", 0) or 0) > lines:
                errors.append(f"file[{idx}] line components exceed total lines")
        self._raise_quality_errors(errors)

    def _map_file_metrics(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[SccFileMetric]:
        """Map file entries to SccFileMetric entities with deduplication.

        Deduplicates by (file_id) to match primary key constraint.
        """
        seen: set[str] = set()
        for entry in files:
            relative_path = self._normalize_path(entry.get("path", ""))
            file_id, directory_id = self._layout_repo.get_file_record(
                layout_run_pk, relative_path
            )

            # Deduplicate by file_id (primary key is run_pk, file_id)
            if file_id in seen:
                self._log(f"WARN: skipping duplicate file: {relative_path}")
                continue
            seen.add(file_id)

            yield SccFileMetric(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                filename=entry.get("filename"),
                extension=entry.get("extension"),
                language=entry.get("language"),
                lines_total=_coalesce(entry.get("lines_total"), entry.get("lines")),
                code_lines=_coalesce(entry.get("lines_code"), entry.get("code")),
                comment_lines=_coalesce(entry.get("lines_comment"), entry.get("comment")),
                blank_lines=_coalesce(entry.get("lines_blank"), entry.get("blank")),
                bytes=entry.get("bytes"),
                complexity=entry.get("complexity"),
                uloc=entry.get("uloc"),
                comment_ratio=entry.get("comment_ratio"),
                blank_ratio=entry.get("blank_ratio"),
                code_ratio=entry.get("code_ratio"),
                complexity_density=entry.get("complexity_density"),
                dryness=entry.get("dryness"),
                bytes_per_loc=entry.get("bytes_per_loc"),
                is_minified=_coalesce(entry.get("is_minified"), entry.get("minified")),
                is_generated=_coalesce(entry.get("is_generated"), entry.get("generated")),
                is_binary=entry.get("is_binary"),
                classification=entry.get("classification"),
            )
