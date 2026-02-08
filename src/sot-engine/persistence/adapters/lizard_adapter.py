from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import LizardFileMetric, LizardFunctionMetric
from ..repositories import LayoutRepository, LizardRepository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_non_negative,
    check_required,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "lizard" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_lizard_file_metrics": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "relative_path": "VARCHAR",
    },
    "lz_lizard_function_metrics": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "function_name": "VARCHAR",
        "line_start": "INTEGER",
    },
}
TABLE_DDL = {
    "lz_lizard_file_metrics": """
        CREATE TABLE IF NOT EXISTS lz_lizard_file_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            language VARCHAR,
            nloc INTEGER,
            function_count INTEGER,
            total_ccn INTEGER,
            avg_ccn DOUBLE,
            max_ccn INTEGER,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
    "lz_lizard_function_metrics": """
        CREATE TABLE IF NOT EXISTS lz_lizard_function_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            function_name VARCHAR NOT NULL,
            long_name VARCHAR,
            ccn INTEGER,
            nloc INTEGER,
            params INTEGER,
            token_count INTEGER,
            line_start INTEGER,
            line_end INTEGER,
            PRIMARY KEY (run_pk, file_id, function_name, line_start)
        )
    """,
}
QUALITY_RULES = ["paths", "ranges", "required_fields"]


class LizardAdapter(BaseAdapter):
    """Adapter for persisting lizard output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "lizard"

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
        lizard_repo: LizardRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._lizard_repo = lizard_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist lizard output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        self.validate_quality(data.get("files", []))
        file_metrics, function_metrics = self._map_metrics(
            run_pk, layout_run_pk, data.get("files", [])
        )
        self._lizard_repo.insert_file_metrics(file_metrics)
        self._lizard_repo.insert_function_metrics(function_metrics)
        return run_pk

    def validate_quality(self, files: Any) -> None:
        """Validate data quality rules for lizard files."""
        errors = []
        for idx, entry in enumerate(files):
            raw_path = entry.get("path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"lizard file[{idx}] path invalid: {raw_path} -> {normalized}")
            errors.extend(check_required(entry.get("language"), f"file[{idx}].language"))
            errors.extend(check_non_negative(entry.get("nloc", 0), f"file[{idx}].nloc"))
            errors.extend(check_non_negative(entry.get("function_count", 0), f"file[{idx}].function_count"))
            errors.extend(check_non_negative(entry.get("total_ccn", 0), f"file[{idx}].total_ccn"))
            errors.extend(check_non_negative(entry.get("max_ccn", 0), f"file[{idx}].max_ccn"))
            if entry.get("avg_ccn") is not None and entry.get("max_ccn") is not None:
                if entry.get("avg_ccn") > entry.get("max_ccn"):
                    errors.append(f"file[{idx}] avg_ccn exceeds max_ccn")
            for fidx, func in enumerate(entry.get("functions", []) or []):
                errors.extend(check_required(func.get("name"), f"file[{idx}].functions[{fidx}].name"))
                errors.extend(check_non_negative(func.get("ccn", 0), f"file[{idx}].functions[{fidx}].ccn"))
                errors.extend(check_non_negative(func.get("nloc", 0), f"file[{idx}].functions[{fidx}].nloc"))
                if func.get("start_line") and func.get("end_line"):
                    if func.get("start_line") > func.get("end_line"):
                        errors.append(f"file[{idx}].functions[{fidx}] start_line > end_line")
        self._raise_quality_errors(errors)

    def _map_metrics(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> tuple[list[LizardFileMetric], list[LizardFunctionMetric]]:
        """Map file and function entries to entities with deduplication.

        Deduplicates files by (file_id) and functions by (file_id, function_name, line_start).
        """
        file_metrics: list[LizardFileMetric] = []
        function_metrics: list[LizardFunctionMetric] = []
        seen_files: set[str] = set()
        seen_functions: set[tuple[str, str, int | None]] = set()

        for entry in files:
            relative_path = self._normalize_path(entry.get("path", ""))
            file_id, _ = self._layout_repo.get_file_record(layout_run_pk, relative_path)

            # Deduplicate files by file_id
            if file_id in seen_files:
                self._log(f"WARN: skipping duplicate file: {relative_path}")
                continue
            seen_files.add(file_id)

            file_metrics.append(
                LizardFileMetric(
                    run_pk=run_pk,
                    file_id=file_id,
                    relative_path=relative_path,
                    language=entry.get("language"),
                    nloc=entry.get("nloc"),
                    function_count=entry.get("function_count"),
                    total_ccn=entry.get("total_ccn"),
                    avg_ccn=entry.get("avg_ccn"),
                    max_ccn=entry.get("max_ccn"),
                )
            )

            for func in entry.get("functions", []) or []:
                # Use 'or' fallback since JSON may have explicit None values alongside valid keys
                line_start = func.get("line_start") if func.get("line_start") is not None else func.get("start_line")
                line_end = func.get("line_end") if func.get("line_end") is not None else func.get("end_line")
                params = func.get("params") if func.get("params") is not None else func.get("parameter_count")

                # Skip pseudo-functions like *global* with invalid line numbers
                # These are lizard artifacts for global scope, not real functions
                if line_start is not None and line_start < 1:
                    self._log(f"WARN: skipping pseudo-function {func.get('name')} with line_start={line_start}")
                    continue

                # Deduplicate functions by (file_id, function_name, line_start)
                func_key = (file_id, func.get("name", ""), line_start)
                if func_key in seen_functions:
                    self._log(
                        f"WARN: skipping duplicate function {func_key[1]} at {relative_path}:{line_start}"
                    )
                    continue
                seen_functions.add(func_key)

                function_metrics.append(
                    LizardFunctionMetric(
                        run_pk=run_pk,
                        file_id=file_id,
                        function_name=func.get("name", ""),
                        long_name=func.get("long_name"),
                        ccn=func.get("ccn"),
                        nloc=func.get("nloc"),
                        params=params,
                        token_count=func.get("token_count"),
                        line_start=line_start,
                        line_end=line_end,
                    )
                )

        return file_metrics, function_metrics
