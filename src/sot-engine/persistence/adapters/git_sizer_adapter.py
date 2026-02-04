"""Adapter for git-sizer output persistence."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .base_adapter import BaseAdapter
from ..entities import GitSizerLfsCandidate, GitSizerMetric, GitSizerViolation
from ..repositories import GitSizerRepository, LayoutRepository, ToolRunRepository

# Schema path points to the local git-sizer tool directory
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "tools" / "git-sizer" / "schemas" / "output.schema.json"

LZ_TABLES = {
    "lz_git_sizer_metrics": {
        "run_pk": "BIGINT",
        "repo_id": "VARCHAR",
        "health_grade": "VARCHAR",
        "duration_ms": "INTEGER",
        "commit_count": "INTEGER",
        "commit_total_size": "BIGINT",
        "max_commit_size": "BIGINT",
        "max_history_depth": "INTEGER",
        "max_parent_count": "INTEGER",
        "tree_count": "INTEGER",
        "tree_total_size": "BIGINT",
        "tree_total_entries": "INTEGER",
        "max_tree_entries": "INTEGER",
        "blob_count": "INTEGER",
        "blob_total_size": "BIGINT",
        "max_blob_size": "BIGINT",
        "tag_count": "INTEGER",
        "max_tag_depth": "INTEGER",
        "reference_count": "INTEGER",
        "branch_count": "INTEGER",
        "max_path_depth": "INTEGER",
        "max_path_length": "INTEGER",
        "expanded_tree_count": "INTEGER",
        "expanded_blob_count": "INTEGER",
        "expanded_blob_size": "BIGINT",
    },
    "lz_git_sizer_violations": {
        "run_pk": "BIGINT",
        "metric": "VARCHAR",
        "value_display": "VARCHAR",
        "raw_value": "BIGINT",
        "level": "INTEGER",
        "object_ref": "VARCHAR",
    },
    "lz_git_sizer_lfs_candidates": {
        "run_pk": "BIGINT",
        "file_path": "VARCHAR",
    },
}

TABLE_DDL = {
    "lz_git_sizer_metrics": """
        CREATE TABLE IF NOT EXISTS lz_git_sizer_metrics (
            run_pk BIGINT NOT NULL PRIMARY KEY,
            repo_id VARCHAR NOT NULL,
            health_grade VARCHAR NOT NULL,
            duration_ms INTEGER,
            commit_count INTEGER,
            commit_total_size BIGINT,
            max_commit_size BIGINT,
            max_history_depth INTEGER,
            max_parent_count INTEGER,
            tree_count INTEGER,
            tree_total_size BIGINT,
            tree_total_entries INTEGER,
            max_tree_entries INTEGER,
            blob_count INTEGER,
            blob_total_size BIGINT,
            max_blob_size BIGINT,
            tag_count INTEGER,
            max_tag_depth INTEGER,
            reference_count INTEGER,
            branch_count INTEGER,
            max_path_depth INTEGER,
            max_path_length INTEGER,
            expanded_tree_count INTEGER,
            expanded_blob_count INTEGER,
            expanded_blob_size BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "lz_git_sizer_violations": """
        CREATE TABLE IF NOT EXISTS lz_git_sizer_violations (
            run_pk BIGINT NOT NULL,
            metric VARCHAR NOT NULL,
            value_display VARCHAR,
            raw_value BIGINT,
            level INTEGER NOT NULL,
            object_ref VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, metric)
        )
    """,
    "lz_git_sizer_lfs_candidates": """
        CREATE TABLE IF NOT EXISTS lz_git_sizer_lfs_candidates (
            run_pk BIGINT NOT NULL,
            file_path VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (run_pk, file_path)
        )
    """,
}

QUALITY_RULES = ["health_grade_valid", "metrics_non_negative", "violation_levels"]


class GitSizerAdapter(BaseAdapter):
    """Adapter for persisting git-sizer repository health analysis to the landing zone.

    git-sizer provides repository-level metrics (not per-file), so this adapter
    handles a single metrics record per run, plus violations and LFS candidates.
    """

    @property
    def tool_name(self) -> str:
        return "git-sizer"

    @property
    def schema_path(self) -> Path | None:
        return SCHEMA_PATH if SCHEMA_PATH.exists() else None

    def validate_schema(self, payload: dict) -> None:
        """Validate payload against JSON schema if available.

        git-sizer schema may not be available when running from a different project.
        In that case, skip JSON schema validation but still apply data quality rules.
        """
        if self.schema_path is None:
            self._log("WARN: git-sizer schema not available, skipping JSON schema validation")
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
        layout_repo: LayoutRepository | None = None,
        git_sizer_repo: GitSizerRepository | None = None,
        repo_root: Path | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(run_repo, layout_repo, repo_root=repo_root, logger=logger)
        self._git_sizer_repo = git_sizer_repo or GitSizerRepository(self._conn)

    def _do_persist(self, payload: dict) -> int:
        """Persist git-sizer output to landing zone.

        git-sizer output follows Caldera envelope format:
        - metadata: run_id, repo_id, branch, commit, timestamp, etc.
        - data: health_grade, metrics, violations, lfs_candidates, raw_output
        """
        metadata = payload.get("metadata", {})
        data = payload.get("data", {})

        # Validate data quality before persisting
        self.validate_quality(data)

        # Create tool run
        run_pk = self._create_tool_run(metadata)

        # Extract and validate metrics
        metrics_data = data.get("metrics", {})
        metric = GitSizerMetric(
            run_pk=run_pk,
            repo_id=metadata["repo_id"],
            health_grade=data["health_grade"],
            duration_ms=data.get("duration_ms", 0),
            # Commit metrics
            commit_count=metrics_data.get("commit_count", 0),
            commit_total_size=metrics_data.get("commit_total_size", 0),
            max_commit_size=metrics_data.get("max_commit_size", 0),
            max_history_depth=metrics_data.get("max_history_depth", 0),
            max_parent_count=metrics_data.get("max_parent_count", 0),
            # Tree metrics
            tree_count=metrics_data.get("tree_count", 0),
            tree_total_size=metrics_data.get("tree_total_size", 0),
            tree_total_entries=metrics_data.get("tree_total_entries", 0),
            max_tree_entries=metrics_data.get("max_tree_entries", 0),
            # Blob metrics
            blob_count=metrics_data.get("blob_count", 0),
            blob_total_size=metrics_data.get("blob_total_size", 0),
            max_blob_size=metrics_data.get("max_blob_size", 0),
            # Tag metrics
            tag_count=metrics_data.get("tag_count", 0),
            max_tag_depth=metrics_data.get("max_tag_depth", 0),
            # Reference metrics
            reference_count=metrics_data.get("reference_count", 0),
            branch_count=metrics_data.get("branch_count", 0),
            # Path metrics
            max_path_depth=metrics_data.get("max_path_depth", 0),
            max_path_length=metrics_data.get("max_path_length", 0),
            # Expanded checkout metrics
            expanded_tree_count=metrics_data.get("expanded_tree_count", 0),
            expanded_blob_count=metrics_data.get("expanded_blob_count", 0),
            expanded_blob_size=metrics_data.get("expanded_blob_size", 0),
        )
        self._git_sizer_repo.insert_metrics([metric])

        # Persist violations
        violations = [
            GitSizerViolation(
                run_pk=run_pk,
                metric=v["metric"],
                value_display=v.get("value", ""),
                raw_value=v.get("raw_value", 0),
                level=v["level"],
                object_ref=v.get("object_ref"),
            )
            for v in data.get("violations", [])
        ]
        if violations:
            self._git_sizer_repo.insert_violations(violations)

        # Persist LFS candidates
        lfs_candidates = [
            GitSizerLfsCandidate(run_pk=run_pk, file_path=path)
            for path in data.get("lfs_candidates", [])
        ]
        if lfs_candidates:
            self._git_sizer_repo.insert_lfs_candidates(lfs_candidates)

        self._log(
            f"Persisted git-sizer metrics (grade={data['health_grade']}, "
            f"{len(violations)} violations, {len(lfs_candidates)} LFS candidates)"
        )

        return run_pk

    def validate_quality(self, data: Any) -> None:
        """Validate git-sizer data quality."""
        errors = []

        # Health grade validation
        grade = data.get("health_grade", "")
        valid_grades = ("A", "A+", "B", "B+", "C", "C+", "D", "D+", "F")
        if grade not in valid_grades:
            errors.append(f"Invalid health_grade: {grade}, must be one of {valid_grades}")

        # Metrics validation - all should be non-negative
        metrics = data.get("metrics", {})
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and value < 0:
                errors.append(f"Negative metric {key}: {value}")

        # Violation level validation
        for i, v in enumerate(data.get("violations", [])):
            level = v.get("level", 0)
            if not 1 <= level <= 4:
                errors.append(f"violations[{i}].level must be 1-4, got {level}")
            if not v.get("metric"):
                errors.append(f"violations[{i}].metric is required")

        if errors:
            for error in errors:
                self._log(f"DATA_QUALITY_ERROR: {error}")
            raise ValueError(f"git-sizer data quality validation failed ({len(errors)} errors)")
