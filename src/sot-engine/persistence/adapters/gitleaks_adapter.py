from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import GitleaksSecret
from ..repositories import GitleaksRepository, LayoutRepository, ToolRunRepository
from shared.path_utils import is_repo_relative_path, normalize_file_path
from ..validation import (
    check_required,
)

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "gitleaks" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_gitleaks_secrets": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "rule_id": "VARCHAR",
        "secret_type": "VARCHAR",
        "severity": "VARCHAR",
        "line_number": "INTEGER",
        "commit_hash": "VARCHAR",
        "commit_author": "VARCHAR",
        "commit_date": "VARCHAR",
        "fingerprint": "VARCHAR",
        "in_current_head": "BOOLEAN",
        "entropy": "DOUBLE",
        "description": "VARCHAR",
    }
}
TABLE_DDL = {
    "lz_gitleaks_secrets": """
        CREATE TABLE IF NOT EXISTS lz_gitleaks_secrets (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR,
            relative_path VARCHAR NOT NULL,
            rule_id VARCHAR NOT NULL,
            secret_type VARCHAR,
            severity VARCHAR,
            line_number INTEGER,
            commit_hash VARCHAR,
            commit_author VARCHAR,
            commit_date VARCHAR,
            fingerprint VARCHAR,
            in_current_head BOOLEAN,
            entropy DOUBLE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, rule_id, line_number, fingerprint)
        )
    """,
}
QUALITY_RULES = ["paths", "line_numbers", "required_fields"]


class GitleaksAdapter(BaseAdapter):
    """Adapter for persisting gitleaks secret detection output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "gitleaks"

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
        gitleaks_repo: GitleaksRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._gitleaks_repo = gitleaks_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist gitleaks output to landing zone."""
        metadata = payload.get("metadata") or {}
        data = payload.get("data") or {}

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        findings = data.get("findings", [])
        self.validate_quality(findings)
        secrets = list(self._map_secrets(run_pk, layout_run_pk, findings))
        self._gitleaks_repo.insert_secrets(secrets)
        return run_pk

    def validate_quality(self, findings: Any) -> None:
        """Validate data quality rules for gitleaks findings."""
        errors = []
        for idx, finding in enumerate(findings):
            raw_path = finding.get("file_path", "")
            normalized = normalize_file_path(raw_path, self._repo_root)
            if not is_repo_relative_path(normalized):
                errors.append(f"gitleaks finding[{idx}] path invalid: {raw_path} -> {normalized}")

            errors.extend(
                check_required(finding.get("rule_id"), f"finding[{idx}].rule_id")
            )
            errors.extend(
                check_required(finding.get("severity"), f"finding[{idx}].severity")
            )

            line_num = finding.get("line_number")
            if line_num is not None and not line_num >= 1:
                errors.append(f"finding[{idx}].line_number must be >= 1: {line_num}")

        self._raise_quality_errors(errors)

    def _map_secrets(
        self, run_pk: int, layout_run_pk: int, findings: Iterable[dict]
    ) -> Iterable[GitleaksSecret]:
        """Map findings to GitleaksSecret entities."""
        seen: set[tuple[str, str, int | None, str | None]] = set()
        for finding in findings:
            relative_path = self._normalize_path(finding.get("file_path", ""))

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                in_head = finding.get("in_current_head", False)
                if in_head:
                    # Current secret but file not in layout (gitignored, binary, etc.)
                    self._log(f"WARN: skipping secret in file not in layout: {relative_path}")
                else:
                    # Historical secret in deleted file
                    self._log(f"WARN: skipping historical secret in deleted file: {relative_path}")
                continue

            key = (file_id, finding.get("rule_id", ""), finding.get("line_number"), finding.get("fingerprint"))
            if key in seen:
                self._log(
                    f"WARN: skipping duplicate secret {key[1]} at {relative_path}:{key[2]}"
                )
                continue
            seen.add(key)
            yield GitleaksSecret(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                rule_id=finding.get("rule_id", ""),
                secret_type=finding.get("secret_type"),
                severity=finding.get("severity"),
                line_number=finding.get("line_number"),
                commit_hash=finding.get("commit_hash"),
                commit_author=finding.get("commit_author"),
                commit_date=finding.get("commit_date"),
                fingerprint=finding.get("fingerprint"),
                in_current_head=finding.get("in_current_head"),
                entropy=finding.get("entropy"),
                description=finding.get("description"),
            )
