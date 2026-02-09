from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import ScancodeFileLicense, ScancodeSummary
from ..repositories import ScancodeRepository, LayoutRepository, ToolRunRepository
from ..validation import check_required, validate_file_paths_in_entries

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "scancode" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_scancode_file_licenses": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "spdx_id": "VARCHAR",
        "category": "VARCHAR",
        "confidence": "DOUBLE",
        "match_type": "VARCHAR",
        "line_number": "INTEGER",
    },
    "lz_scancode_summary": {
        "run_pk": "BIGINT",
        "total_files_scanned": "INTEGER",
        "files_with_licenses": "INTEGER",
        "overall_risk": "VARCHAR",
        "has_permissive": "BOOLEAN",
        "has_weak_copyleft": "BOOLEAN",
        "has_copyleft": "BOOLEAN",
        "has_unknown": "BOOLEAN",
    },
}
TABLE_DDL = {
    "lz_scancode_file_licenses": """
        CREATE TABLE IF NOT EXISTS lz_scancode_file_licenses (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            spdx_id VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            confidence DOUBLE NOT NULL,
            match_type VARCHAR NOT NULL,
            line_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, spdx_id, line_number)
        )
    """,
    "lz_scancode_summary": """
        CREATE TABLE IF NOT EXISTS lz_scancode_summary (
            run_pk BIGINT NOT NULL PRIMARY KEY,
            total_files_scanned INTEGER NOT NULL,
            files_with_licenses INTEGER NOT NULL,
            overall_risk VARCHAR NOT NULL,
            has_permissive BOOLEAN NOT NULL,
            has_weak_copyleft BOOLEAN NOT NULL,
            has_copyleft BOOLEAN NOT NULL,
            has_unknown BOOLEAN NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}
QUALITY_RULES = ["paths", "confidence", "required_fields"]


class ScancodeAdapter(BaseAdapter):
    """Adapter for persisting scancode license analysis output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "scancode"

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
        scancode_repo: ScancodeRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._scancode_repo = scancode_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist scancode output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        findings = data.get("findings", [])
        self.validate_quality(findings)

        # Map and insert file licenses
        licenses = list(self._map_file_licenses(run_pk, layout_run_pk, findings))
        self._scancode_repo.insert_file_licenses(licenses)

        # Create and insert summary
        summary = ScancodeSummary(
            run_pk=run_pk,
            total_files_scanned=data.get("total_files_scanned", 0),
            files_with_licenses=data.get("files_with_licenses", 0),
            overall_risk=data.get("overall_risk", "unknown"),
            has_permissive=data.get("has_permissive", False),
            has_weak_copyleft=data.get("has_weak_copyleft", False),
            has_copyleft=data.get("has_copyleft", False),
            has_unknown=data.get("has_unknown", True),
        )
        self._scancode_repo.insert_summary([summary])

        return run_pk

    def validate_quality(self, findings: Any) -> None:
        """Validate data quality rules for scancode findings."""
        errors: list[str] = []
        # Use shared path validation helper
        errors.extend(validate_file_paths_in_entries(
            findings,
            path_field="file_path",
            repo_root=self._repo_root,
            entry_prefix="scancode finding",
        ))
        for idx, finding in enumerate(findings):
            errors.extend(
                check_required(finding.get("spdx_id"), f"finding[{idx}].spdx_id")
            )
            errors.extend(
                check_required(finding.get("category"), f"finding[{idx}].category")
            )

            confidence = finding.get("confidence")
            if confidence is not None and (confidence < 0 or confidence > 1):
                errors.append(f"finding[{idx}].confidence must be 0-1: {confidence}")

            line_num = finding.get("line_number")
            if line_num is not None and line_num < 1:
                errors.append(f"finding[{idx}].line_number must be >= 1: {line_num}")

        self._raise_quality_errors(errors)

    def _map_file_licenses(
        self, run_pk: int, layout_run_pk: int, findings: Iterable[dict]
    ) -> Iterable[ScancodeFileLicense]:
        """Map findings to ScancodeFileLicense entities."""
        seen: set[tuple[str, str, int | None]] = set()
        for finding in findings:
            relative_path = self._normalize_path(finding.get("file_path", ""))

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                self._log(f"WARN: skipping license in file not in layout: {relative_path}")
                continue

            line_number = finding.get("line_number")
            key = (file_id, finding.get("spdx_id", ""), line_number)
            if key in seen:
                self._log(
                    f"WARN: skipping duplicate license {key[1]} at {relative_path}:{line_number}"
                )
                continue
            seen.add(key)

            yield ScancodeFileLicense(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                spdx_id=finding.get("spdx_id", ""),
                category=finding.get("category", "unknown"),
                confidence=finding.get("confidence", 0.0),
                match_type=finding.get("match_type", "file"),
                line_number=line_number,
            )
