from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from .base_adapter import BaseAdapter
from ..entities import SonarqubeIssue, SonarqubeMetric
from ..repositories import LayoutRepository, SonarqubeRepository, ToolRunRepository
from common.path_normalization import is_repo_relative_path, normalize_file_path
from ..validation import check_required

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "sonarqube" / "schemas" / "output.schema.json"
LZ_TABLES = {
    "lz_sonarqube_issues": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "issue_key": "VARCHAR",
        "rule_id": "VARCHAR",
        "issue_type": "VARCHAR",
        "severity": "VARCHAR",
        "message": "VARCHAR",
        "line_start": "INTEGER",
        "line_end": "INTEGER",
        "effort": "VARCHAR",
        "status": "VARCHAR",
        "tags": "VARCHAR",
    },
    "lz_sonarqube_metrics": {
        "run_pk": "BIGINT",
        "file_id": "VARCHAR",
        "directory_id": "VARCHAR",
        "relative_path": "VARCHAR",
        "ncloc": "INTEGER",
        "complexity": "INTEGER",
        "cognitive_complexity": "INTEGER",
        "duplicated_lines": "INTEGER",
        "duplicated_lines_density": "DOUBLE",
        "code_smells": "INTEGER",
        "bugs": "INTEGER",
        "vulnerabilities": "INTEGER",
    },
}
TABLE_DDL = {
    "lz_sonarqube_issues": """
        CREATE TABLE IF NOT EXISTS lz_sonarqube_issues (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            issue_key VARCHAR NOT NULL,
            rule_id VARCHAR NOT NULL,
            issue_type VARCHAR,
            severity VARCHAR,
            message TEXT,
            line_start INTEGER,
            line_end INTEGER,
            effort VARCHAR,
            status VARCHAR,
            tags VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id, issue_key)
        )
    """,
    "lz_sonarqube_metrics": """
        CREATE TABLE IF NOT EXISTS lz_sonarqube_metrics (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            directory_id VARCHAR NOT NULL,
            relative_path VARCHAR NOT NULL,
            ncloc INTEGER,
            complexity INTEGER,
            cognitive_complexity INTEGER,
            duplicated_lines INTEGER,
            duplicated_lines_density DOUBLE,
            code_smells INTEGER,
            bugs INTEGER,
            vulnerabilities INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_id)
        )
    """,
}
QUALITY_RULES = ["paths", "line_numbers", "required_fields"]


class SonarqubeAdapter(BaseAdapter):
    """Adapter for persisting SonarQube analysis output to the landing zone."""

    @property
    def tool_name(self) -> str:
        return "sonarqube"

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
        sonarqube_repo: SonarqubeRepository,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._sonarqube_repo = sonarqube_repo

    def _do_persist(self, payload: dict) -> int:
        """Persist SonarQube output to landing zone.

        SonarQube uses a different payload structure than other tools.
        """
        metadata = payload.get("metadata", {})
        data = payload.get("data", {})
        results = data.get("results", {})

        run_pk = self._create_tool_run(metadata)
        layout_run_pk = self._get_layout_run_pk(metadata["run_id"])

        # Extract issues and metrics from SonarQube output
        issues_data = results.get("issues", {}).get("items", [])
        components = results.get("components", {}).get("by_key", {})
        measures = results.get("measures", {}).get("by_component_key", {})

        self.validate_quality(issues_data, components)

        # Map and insert issues
        issues = list(self._map_issues(run_pk, layout_run_pk, issues_data, components))
        self._sonarqube_repo.insert_issues(issues)

        # Map and insert metrics
        metrics = list(self._map_metrics(run_pk, layout_run_pk, measures, components))
        self._sonarqube_repo.insert_metrics(metrics)

        self._log(f"Persisted {len(issues)} issues and {len(metrics)} file metrics for SonarQube")

        return run_pk

    def validate_quality(self, issues: Any, components: Any = None) -> None:
        """Validate data quality rules for SonarQube issues."""
        errors = []
        for issue_idx, issue in enumerate(issues):
            errors.extend(check_required(issue.get("key"), f"issues[{issue_idx}].key"))
            errors.extend(check_required(issue.get("rule"), f"issues[{issue_idx}].rule"))
            component_key = issue.get("component", "")
            if components:
                component = components.get(component_key, {})
                raw_path = component.get("path", "")
                if raw_path:
                    normalized = normalize_file_path(raw_path, self._repo_root)
                    if not is_repo_relative_path(normalized):
                        errors.append(f"issues[{issue_idx}].path is not repo-relative: {raw_path}")
            line = issue.get("line")
            if line is not None and line < 1:
                errors.append(f"issues[{issue_idx}].line must be >= 1")
            text_range = issue.get("text_range", {})
            errors.extend(
                self.check_line_range(
                    text_range.get("start_line"),
                    text_range.get("end_line"),
                    f"issues[{issue_idx}].text_range",
                )
            )

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"sonarqube data quality validation failed ({len(errors)} errors)")

    def _map_issues(
        self,
        run_pk: int,
        layout_run_pk: int,
        issues: list[dict],
        components: dict,
    ) -> Iterable[SonarqubeIssue]:
        """Map SonarQube issues to SonarqubeIssue entities."""
        for issue in issues:
            component_key = issue.get("component", "")
            component = components.get(component_key, {})
            raw_path = component.get("path", "")

            if not raw_path:
                # Skip issues without a file path (e.g., project-level issues)
                continue

            relative_path = self._normalize_path(raw_path)

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError as exc:
                self._log(f"DATA_QUALITY_ERROR: file not in layout: {relative_path}")
                raise ValueError(f"sonarqube file not in layout: {relative_path}") from exc

            text_range = issue.get("text_range", {})
            line_start = text_range.get("start_line") or issue.get("line")
            line_end = text_range.get("end_line") or line_start

            tags = issue.get("tags", [])
            tags_str = ",".join(tags) if tags else None

            yield SonarqubeIssue(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                issue_key=issue.get("key", ""),
                rule_id=issue.get("rule", ""),
                issue_type=issue.get("type"),
                severity=issue.get("severity"),
                message=issue.get("message"),
                line_start=line_start,
                line_end=line_end,
                effort=issue.get("effort"),
                status=issue.get("status"),
                tags=tags_str,
            )

    def _map_metrics(
        self,
        run_pk: int,
        layout_run_pk: int,
        measures: dict,
        components: dict,
    ) -> Iterable[SonarqubeMetric]:
        """Map SonarQube measures to SonarqubeMetric entities."""
        for component_key, measure_data in measures.items():
            component = components.get(component_key, {})
            qualifier = component.get("qualifier", "")

            # Only process file-level components (FIL)
            if qualifier != "FIL":
                continue

            raw_path = component.get("path", "")
            if not raw_path:
                continue

            relative_path = self._normalize_path(raw_path)

            try:
                file_id, directory_id = self._layout_repo.get_file_record(
                    layout_run_pk, relative_path
                )
            except KeyError as exc:
                self._log(f"DATA_QUALITY_ERROR: file not in layout for metrics: {relative_path}")
                raise ValueError(f"sonarqube file not in layout: {relative_path}") from exc

            # Extract measures into a dict for easier access
            measure_values = {}
            for m in measure_data.get("measures", []):
                metric_key = m.get("metric")
                value = m.get("value")
                if metric_key and value is not None:
                    measure_values[metric_key] = value

            yield SonarqubeMetric(
                run_pk=run_pk,
                file_id=file_id,
                directory_id=directory_id,
                relative_path=relative_path,
                ncloc=self._parse_int(measure_values.get("ncloc")),
                complexity=self._parse_int(measure_values.get("complexity")),
                cognitive_complexity=self._parse_int(measure_values.get("cognitive_complexity")),
                duplicated_lines=self._parse_int(measure_values.get("duplicated_lines")),
                duplicated_lines_density=self._parse_float(measure_values.get("duplicated_lines_density")),
                code_smells=self._parse_int(measure_values.get("code_smells")),
                bugs=self._parse_int(measure_values.get("bugs")),
                vulnerabilities=self._parse_int(measure_values.get("vulnerabilities")),
            )

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        """Parse string value to int, returning None if not parseable."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        """Parse string value to float, returning None if not parseable."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
