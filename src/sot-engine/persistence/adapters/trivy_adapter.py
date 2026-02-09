from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable
import hashlib

from .base_adapter import BaseAdapter
from ..entities import TrivyIacMisconfig, TrivyTarget, TrivyVulnerability, ToolRun
from ..repositories import LayoutRepository, ToolRunRepository, TrivyRepository
from ..validation import (
    check_required,
    validate_file_paths_in_entries,
)
from shared.path_utils import is_repo_relative_path, normalize_file_path

# Schema path points to the local trivy tool directory
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "trivy" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_trivy_vulnerabilities": {
        "run_pk": "BIGINT",
        "target_key": "VARCHAR",
        "vulnerability_id": "VARCHAR",
        "package_name": "VARCHAR",
        "installed_version": "VARCHAR",
        "fixed_version": "VARCHAR",
        "severity": "VARCHAR",
        "cvss_score": "DOUBLE",
        "title": "VARCHAR",
        "published_date": "VARCHAR",
        "age_days": "INTEGER",
        "fix_available": "BOOLEAN",
    },
    "lz_trivy_targets": {
        "run_pk": "BIGINT",
        "target_key": "VARCHAR",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "target_type": "VARCHAR",
        "vulnerability_count": "INTEGER",
        "critical_count": "INTEGER",
        "high_count": "INTEGER",
        "medium_count": "INTEGER",
        "low_count": "INTEGER",
    },
    "lz_trivy_iac_misconfigs": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "misconfig_id": "VARCHAR",
        "severity": "VARCHAR",
        "title": "VARCHAR",
        "description": "VARCHAR",
        "resolution": "VARCHAR",
        "target_type": "VARCHAR",
        "start_line": "INTEGER",
        "end_line": "INTEGER",
    },
}
TABLE_DDL = {
    "lz_trivy_vulnerabilities": """
        CREATE TABLE IF NOT EXISTS lz_trivy_vulnerabilities (
            run_pk BIGINT NOT NULL,
            target_key VARCHAR NOT NULL,
            vulnerability_id VARCHAR NOT NULL,
            package_name VARCHAR NOT NULL,
            installed_version VARCHAR,
            fixed_version VARCHAR,
            severity VARCHAR,
            cvss_score DOUBLE,
            title VARCHAR,
            published_date VARCHAR,
            age_days INTEGER,
            fix_available BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, target_key, vulnerability_id, package_name)
        )
    """,
    "lz_trivy_targets": """
        CREATE TABLE IF NOT EXISTS lz_trivy_targets (
            run_pk BIGINT NOT NULL,
            target_key VARCHAR NOT NULL,
            file_id VARCHAR,
            directory_id VARCHAR,
            relative_path VARCHAR NOT NULL,
            target_type VARCHAR,
            vulnerability_count INTEGER DEFAULT 0,
            critical_count INTEGER DEFAULT 0,
            high_count INTEGER DEFAULT 0,
            medium_count INTEGER DEFAULT 0,
            low_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, target_key)
        )
    """,
    "lz_trivy_iac_misconfigs": """
        CREATE TABLE IF NOT EXISTS lz_trivy_iac_misconfigs (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR,
            directory_id VARCHAR,
            relative_path VARCHAR NOT NULL,
            misconfig_id VARCHAR NOT NULL,
            severity VARCHAR,
            title VARCHAR,
            description TEXT,
            resolution TEXT,
            target_type VARCHAR,
            start_line INTEGER,
            end_line INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, relative_path, misconfig_id, start_line)
        )
    """,
}

QUALITY_RULES = ["paths", "line_numbers", "required_fields"]


class TrivyAdapter(BaseAdapter):
    """Adapter for persisting Trivy vulnerability analysis output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "trivy"

    @property
    def schema_path(self) -> Path | None:
        return SCHEMA_PATH

    def validate_schema(self, payload: dict) -> None:
        """Validate payload against JSON schema if available.

        Trivy schema may not be available when running from a different project.
        In that case, skip JSON schema validation but still apply data quality rules.
        """
        if self.schema_path is None:
            self._log("WARN: trivy schema not available, skipping JSON schema validation")
            return
        super().validate_schema(payload)

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
        trivy_repo: TrivyRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._trivy_repo = trivy_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist Trivy output to landing zone.

        Trivy supports two payload structures:
        - Envelope format (preferred): metadata + data
        - Legacy format: metadata + results

        Data section contains:
        - vulnerabilities: array of vulnerability findings
        - targets: array of scan targets (lockfiles, etc.)
        - iac_misconfigurations: IaC issues (optional)
        """
        # Support both envelope format (data) and legacy format (results)
        results = payload.get("data") or payload.get("results", {})
        metadata = payload.get("metadata", {})

        # Build ToolRun from available fields
        # Timestamp can be in metadata.timestamp (envelope) or top-level generated_at (legacy)
        timestamp_str = metadata.get("timestamp") or payload.get("generated_at") or datetime.now().isoformat()
        run = ToolRun(
            collection_run_id=metadata.get("run_id", payload.get("repo_name", "unknown")),
            repo_id=metadata.get("repo_id", payload.get("repo_name", "unknown")),
            run_id=metadata.get("run_id", payload.get("repo_name", "unknown")),
            tool_name="trivy",
            tool_version=results.get("tool_version") or metadata.get("tool_version", "unknown"),
            schema_version=metadata.get("schema_version") or payload.get("schema_version", "1.0.0"),
            branch=metadata.get("branch", "main"),
            commit=metadata.get("commit", "0" * 40),
            timestamp=datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")),
        )
        run_pk = self._run_repo.insert(run)

        layout_run_pk = self._get_layout_run_pk(run.collection_run_id)

        # Extract data from Trivy output
        vulnerabilities_data = results.get("vulnerabilities", [])
        targets_data = results.get("targets", [])
        iac_data = results.get("iac_misconfigurations", {}).get("misconfigurations", [])

        self.validate_quality(vulnerabilities_data, targets_data, iac_data)

        # Map and insert targets first (for target_key linkage)
        targets = list(self._map_targets(run_pk, layout_run_pk, targets_data))
        self._trivy_repo.insert_targets(targets)

        # Map and insert vulnerabilities
        vulns = list(self._map_vulnerabilities(run_pk, vulnerabilities_data))
        self._trivy_repo.insert_vulnerabilities(vulns)

        # Map and insert IaC misconfigurations if present
        if iac_data:
            misconfigs = list(self._map_iac_misconfigs(run_pk, layout_run_pk, iac_data))
            self._trivy_repo.insert_iac_misconfigs(misconfigs)
            self._log(f"Persisted {len(misconfigs)} IaC misconfigurations for Trivy")

        self._log(f"Persisted {len(targets)} targets and {len(vulns)} vulnerabilities for Trivy")

        return run_pk

    def validate_quality(self, vulnerabilities: Any, targets: Any = None, iac_misconfigs: Any = None) -> None:
        """Validate data quality rules for Trivy vulnerabilities and IaC misconfigs."""
        errors: list[str] = []

        for vuln_idx, vuln in enumerate(vulnerabilities):
            errors.extend(
                check_required(vuln.get("id"), f"vulnerabilities[{vuln_idx}].id")
            )
            errors.extend(
                check_required(vuln.get("package"), f"vulnerabilities[{vuln_idx}].package")
            )

            severity = vuln.get("severity")
            if severity is not None:
                valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"}
                if severity not in valid_severities:
                    errors.append(
                        f"vulnerabilities[{vuln_idx}].severity must be one of {valid_severities}"
                    )

            cvss = vuln.get("cvss_score")
            if cvss is not None:
                try:
                    cvss_float = float(cvss)
                    if cvss_float < 0 or cvss_float > 10:
                        errors.append(
                            f"vulnerabilities[{vuln_idx}].cvss_score must be between 0 and 10"
                        )
                except (ValueError, TypeError):
                    errors.append(
                        f"vulnerabilities[{vuln_idx}].cvss_score must be a number"
                    )

        if targets:
            # Use shared path validation helper for targets
            errors.extend(validate_file_paths_in_entries(
                targets,
                path_field="path",
                repo_root=self._repo_root,
                entry_prefix="targets",
            ))
            # Also check required field
            for target_idx, target in enumerate(targets):
                errors.extend(
                    check_required(target.get("path", ""), f"targets[{target_idx}].path")
                )

        if iac_misconfigs:
            # Use shared path validation helper for IaC misconfigs (uses "target" field)
            errors.extend(validate_file_paths_in_entries(
                iac_misconfigs,
                path_field="target",
                repo_root=self._repo_root,
                entry_prefix="iac_misconfigs",
            ))
            for iac_idx, iac in enumerate(iac_misconfigs):
                # IaC misconfigs use "target" field for file path
                errors.extend(
                    check_required(iac.get("target", ""), f"iac_misconfigs[{iac_idx}].target")
                )
                # Validate line_start and line_end: both must be >= 1 if present
                line_start = iac.get("start_line")
                line_end = iac.get("end_line")
                if line_start is not None and line_start < 1:
                    errors.append(f"iac_misconfigs[{iac_idx}].line_start must be >= 1")
                if line_end is not None and line_end < 1:
                    errors.append(f"iac_misconfigs[{iac_idx}].line_end must be >= 1")

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"trivy data quality validation failed ({len(errors)} errors)")

    def _generate_target_key(self, path: str, target_type: str | None) -> str:
        """Generate a unique target key from path and type."""
        key_input = f"{path}:{target_type or 'unknown'}"
        return hashlib.sha256(key_input.encode()).hexdigest()[:16]

    def _map_targets(
        self,
        run_pk: int,
        layout_run_pk: int,
        targets: list[dict],
    ) -> Iterable[TrivyTarget]:
        """Map Trivy targets to TrivyTarget entities with deduplication.

        Deduplicates by target_key to match primary key constraint.
        """
        seen: set[str] = set()
        for target in targets:
            raw_path = target.get("path", "")
            if not raw_path:
                continue

            relative_path = self._normalize_path(raw_path)
            target_type = target.get("type")
            target_key = self._generate_target_key(relative_path, target_type)

            # Deduplicate by target_key
            if target_key in seen:
                self._log(f"WARN: skipping duplicate target: {relative_path}")
                continue
            seen.add(target_key)

            # Try to link to layout for file_id resolution (best-effort)
            file_id = None
            directory_id = None
            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                # Lockfiles may not be in layout (e.g., node_modules)
                self._log(f"WARN: target not in layout: {relative_path}")

            yield TrivyTarget(
                run_pk=run_pk,
                target_key=target_key,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                target_type=target_type,
                vulnerability_count=target.get("vulnerability_count", 0),
                critical_count=target.get("critical_count", 0),
                high_count=target.get("high_count", 0),
                medium_count=target.get("medium_count", 0),
                low_count=target.get("low_count", 0),
            )

    def _map_vulnerabilities(
        self,
        run_pk: int,
        vulnerabilities: list[dict],
    ) -> Iterable[TrivyVulnerability]:
        """Map Trivy vulnerabilities to TrivyVulnerability entities with deduplication.

        Deduplicates by (target_key, vulnerability_id, package_name) to match primary key.
        """
        seen: set[tuple[str, str, str]] = set()
        for vuln in vulnerabilities:
            # Generate target_key from the vulnerability's target path
            target_path = vuln.get("target", "")
            target_type = vuln.get("target_type")
            target_key = self._generate_target_key(
                self._normalize_path(target_path) if target_path else "unknown",
                target_type,
            )

            vuln_id = vuln.get("id", "")
            package_name = vuln.get("package", "")

            # Deduplicate by (target_key, vulnerability_id, package_name)
            key = (target_key, vuln_id, package_name)
            if key in seen:
                self._log(f"WARN: skipping duplicate vulnerability: {vuln_id} in {package_name}")
                continue
            seen.add(key)

            yield TrivyVulnerability(
                run_pk=run_pk,
                target_key=target_key,
                vulnerability_id=vuln_id,
                package_name=package_name,
                installed_version=vuln.get("installed_version"),
                fixed_version=vuln.get("fixed_version"),
                severity=vuln.get("severity"),
                cvss_score=self._parse_float(vuln.get("cvss_score")),
                title=vuln.get("title"),
                published_date=vuln.get("published_date"),
                age_days=vuln.get("age_days"),
                fix_available=vuln.get("fix_available"),
            )

    def _map_iac_misconfigs(
        self,
        run_pk: int,
        layout_run_pk: int,
        misconfigs: list[dict],
    ) -> Iterable[TrivyIacMisconfig]:
        """Map Trivy IaC misconfigurations to TrivyIacMisconfig entities with deduplication.

        Deduplicates by (relative_path, misconfig_id, start_line) to match primary key.
        """
        seen: set[tuple[str, str, int]] = set()
        for misconfig in misconfigs:
            raw_path = misconfig.get("target", "")
            if not raw_path:
                continue

            relative_path = self._normalize_path(raw_path)

            # Trivy uses 0 for file-level issues; convert to -1 for primary key compatibility
            # (DuckDB doesn't allow NULL in primary key columns)
            start_line = misconfig.get("start_line")
            end_line = misconfig.get("end_line")
            if start_line is None or start_line == 0:
                start_line = -1
            if end_line is None or end_line == 0:
                end_line = -1

            misconfig_id = misconfig.get("id", "")

            # Deduplicate by (relative_path, misconfig_id, start_line)
            key = (relative_path, misconfig_id, start_line)
            if key in seen:
                self._log(f"WARN: skipping duplicate IaC misconfig: {misconfig_id} at {relative_path}:{start_line}")
                continue
            seen.add(key)

            # Try to link to layout for file_id resolution
            file_id = None
            directory_id = None
            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError:
                self._log(f"WARN: IaC file not in layout: {relative_path}")

            yield TrivyIacMisconfig(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                misconfig_id=misconfig_id,
                severity=misconfig.get("severity"),
                title=misconfig.get("title"),
                description=misconfig.get("description"),
                resolution=misconfig.get("resolution"),
                target_type=misconfig.get("target_type"),
                start_line=start_line,
                end_line=end_line,
            )

    @staticmethod
    def _parse_float(value: str | float | None) -> float | None:
        """Parse string/float value to float, returning None if not parseable."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
