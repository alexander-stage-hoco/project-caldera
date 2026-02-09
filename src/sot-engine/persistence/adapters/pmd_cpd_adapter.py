from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import PmdCpdDuplication, PmdCpdFileMetric, PmdCpdOccurrence
from ..repositories import LayoutRepository, PmdCpdRepository, ToolRunRepository
from shared.path_utils import is_repo_relative_path, normalize_file_path
from ..validation import check_required, validate_file_paths_in_entries


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "pmd-cpd" / "schemas" / "output.schema.json"

LZ_TABLES = {
    "lz_pmd_cpd_file_metrics": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "language": "VARCHAR",
        "total_lines": "INTEGER",
        "duplicate_lines": "INTEGER",
        "duplicate_blocks": "INTEGER",
        "duplication_percentage": "DOUBLE",
    },
    "lz_pmd_cpd_duplications": {
        "run_pk": "BIGINT",
        "clone_id": "VARCHAR",
        "lines": "INTEGER",
        "tokens": "INTEGER",
        "occurrence_count": "INTEGER",
        "is_cross_file": "BOOLEAN",
        "code_fragment": "VARCHAR",
    },
    "lz_pmd_cpd_occurrences": {
        "run_pk": "BIGINT",
        "clone_id": "VARCHAR",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "line_start": "INTEGER",
        "line_end": "INTEGER",
        "column_start": "INTEGER",
        "column_end": "INTEGER",
    },
}

TABLE_DDL = {
    "lz_pmd_cpd_file_metrics": """
        CREATE TABLE IF NOT EXISTS lz_pmd_cpd_file_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            language VARCHAR,
            total_lines INTEGER NOT NULL,
            duplicate_lines INTEGER NOT NULL,
            duplicate_blocks INTEGER NOT NULL,
            duplication_percentage DOUBLE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
    "lz_pmd_cpd_duplications": """
        CREATE TABLE IF NOT EXISTS lz_pmd_cpd_duplications (
            run_pk BIGINT NOT NULL,
            clone_id VARCHAR NOT NULL,
            lines INTEGER NOT NULL,
            tokens INTEGER NOT NULL,
            occurrence_count INTEGER NOT NULL,
            is_cross_file BOOLEAN NOT NULL,
            code_fragment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, clone_id)
        )
    """,
    "lz_pmd_cpd_occurrences": """
        CREATE TABLE IF NOT EXISTS lz_pmd_cpd_occurrences (
            run_pk BIGINT NOT NULL,
            clone_id VARCHAR NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            line_start INTEGER NOT NULL,
            line_end INTEGER NOT NULL,
            column_start INTEGER,
            column_end INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, clone_id, file_id, line_start)
        )
    """,
}

QUALITY_RULES = ["paths", "line_numbers", "required_fields"]


class PmdCpdAdapter(BaseAdapter):
    """Adapter for persisting pmd-cpd duplication analysis output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "pmd-cpd"

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
        pmd_cpd_repo: PmdCpdRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._pmd_cpd_repo = pmd_cpd_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist pmd-cpd output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        files = data.get("files", [])
        duplications = data.get("duplications", [])

        self.validate_quality({"files": files, "duplications": duplications})

        # Map and insert file metrics
        file_metrics = list(self._map_file_metrics(run_pk, layout_run_pk, files))
        self._pmd_cpd_repo.insert_file_metrics(file_metrics)

        # Map and insert duplications and occurrences
        dup_entities, occ_entities = self._map_duplications(run_pk, layout_run_pk, duplications)
        self._pmd_cpd_repo.insert_duplications(dup_entities)
        self._pmd_cpd_repo.insert_occurrences(occ_entities)

        return run_pk

    def validate_quality(self, data: Any) -> None:
        """Validate data quality rules for pmd-cpd output."""
        errors: list[str] = []
        files = data.get("files", [])
        duplications = data.get("duplications", [])

        # Validate file paths using shared helper
        errors.extend(validate_file_paths_in_entries(
            files,
            path_field="path",
            repo_root=self._repo_root,
            entry_prefix="pmd-cpd file",
        ))

        # Validate duplications
        for dup_idx, dup in enumerate(duplications):
            errors.extend(
                check_required(dup.get("clone_id"), f"duplications[{dup_idx}].clone_id")
            )
            occurrences = dup.get("occurrences", [])
            if len(occurrences) < 2:
                errors.append(f"duplications[{dup_idx}] must have at least 2 occurrences")

            # Keep inline validation for nested occurrences (too complex to flatten)
            for occ_idx, occ in enumerate(occurrences):
                raw_path = occ.get("file", "")
                normalized = normalize_file_path(raw_path, self._repo_root)
                if not is_repo_relative_path(normalized):
                    errors.append(
                        f"duplications[{dup_idx}].occurrences[{occ_idx}] path invalid: {raw_path}"
                    )
                errors.extend(
                    self.check_line_range(
                        occ.get("line_start"),
                        occ.get("line_end"),
                        f"duplications[{dup_idx}].occurrences[{occ_idx}]",
                    )
                )

        self._raise_quality_errors(errors)

    def _map_file_metrics(
        self, run_pk: int, layout_run_pk: int, files: Iterable[dict]
    ) -> Iterable[PmdCpdFileMetric]:
        """Map file entries to PmdCpdFileMetric entities with deduplication.

        Deduplicates by file_id to match primary key constraint.
        """
        seen: set[str] = set()
        for file_entry in files:
            relative_path = self._normalize_path(file_entry.get("path", ""))

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

            yield PmdCpdFileMetric(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                language=file_entry.get("language"),
                total_lines=file_entry.get("total_lines", 0),
                duplicate_lines=file_entry.get("duplicate_lines", 0),
                duplicate_blocks=file_entry.get("duplicate_blocks", 0),
                duplication_percentage=file_entry.get("duplication_percentage", 0.0),
            )

    def _map_duplications(
        self, run_pk: int, layout_run_pk: int, duplications: Iterable[dict]
    ) -> tuple[list[PmdCpdDuplication], list[PmdCpdOccurrence]]:
        """Map duplication entries to PmdCpdDuplication and PmdCpdOccurrence entities.

        Deduplicates duplications by clone_id and occurrences by (clone_id, file_id, line_start).
        """
        dup_entities: list[PmdCpdDuplication] = []
        occ_entities: list[PmdCpdOccurrence] = []
        seen_dups: set[str] = set()
        seen_occs: set[tuple[str, str, int]] = set()

        for dup in duplications:
            clone_id = dup.get("clone_id", "")

            # Deduplicate duplications by clone_id
            if clone_id in seen_dups:
                self._log(f"WARN: skipping duplicate clone_id: {clone_id}")
                continue
            seen_dups.add(clone_id)

            occurrences = dup.get("occurrences", [])

            # Determine if cross-file
            files_in_dup = {occ.get("file", "") for occ in occurrences}
            is_cross_file = len(files_in_dup) > 1

            dup_entities.append(
                PmdCpdDuplication(
                    run_pk=run_pk,
                    clone_id=clone_id,
                    lines=dup.get("lines", 0),
                    tokens=dup.get("tokens", 0),
                    occurrence_count=len(occurrences),
                    is_cross_file=is_cross_file,
                    code_fragment=dup.get("code_fragment"),
                )
            )

            # Map occurrences
            for occ in occurrences:
                relative_path = self._normalize_path(occ.get("file", ""))

                try:
                    file_id, directory_id = self._layout_repo.get_file_record(
                        layout_run_pk, relative_path
                    )
                except KeyError:
                    self._log(f"WARN: skipping occurrence in file not in layout: {relative_path}")
                    continue

                line_start = occ.get("line_start", 1)

                # Deduplicate occurrences by (clone_id, file_id, line_start)
                occ_key = (clone_id, file_id, line_start)
                if occ_key in seen_occs:
                    self._log(f"WARN: skipping duplicate occurrence: {clone_id} at {relative_path}:{line_start}")
                    continue
                seen_occs.add(occ_key)

                occ_entities.append(
                    PmdCpdOccurrence(
                        run_pk=run_pk,
                        clone_id=clone_id,
                        file_id=file_id,
                        directory_id=directory_id,
                        relative_path=relative_path,
                        line_start=line_start,
                        line_end=occ.get("line_end", 1),
                        column_start=occ.get("column_start"),
                        column_end=occ.get("column_end"),
                    )
                )

        return dup_entities, occ_entities
