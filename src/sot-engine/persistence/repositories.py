from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Sequence, TypeVar
import duckdb

from .entities import (
    CollectionRun,
    GitSizerLfsCandidate,
    GitSizerMetric,
    GitSizerViolation,
    LayoutDirectory,
    LayoutFile,
    LizardFileMetric,
    LizardFunctionMetric,
    RoslynViolation,
    SccFileMetric,
    SemgrepSmell,
    SonarqubeIssue,
    SonarqubeMetric,
    ToolRun,
    TrivyIacMisconfig,
    TrivyTarget,
    TrivyVulnerability,
)

T = TypeVar("T")


class BaseRepository:
    """Base class for repositories with common bulk insert functionality."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _insert_bulk(
        self,
        table: str,
        columns: Sequence[str],
        entities: Iterable[T],
        to_tuple: Callable[[T], tuple[Any, ...]],
    ) -> None:
        """Generic bulk insert method.

        Args:
            table: Target table name
            columns: Column names to insert into
            entities: Iterable of entity objects
            to_tuple: Function to convert entity to tuple of values
        """
        records = [to_tuple(e) for e in entities]
        if not records:
            return
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)
        self._conn.executemany(
            f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})",
            records,
        )


class CollectionRunRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get_by_repo_commit(self, repo_id: str, commit: str) -> CollectionRun | None:
        row = self._conn.execute(
            """
            SELECT collection_run_id, repo_id, run_id, branch, commit,
                   started_at, completed_at, status
            FROM lz_collection_runs
            WHERE repo_id = ? AND commit = ?
            """,
            [repo_id, commit],
        ).fetchone()
        if not row:
            return None
        return CollectionRun(
            collection_run_id=row[0],
            repo_id=row[1],
            run_id=row[2],
            branch=row[3],
            commit=row[4],
            started_at=row[5],
            completed_at=row[6],
            status=row[7],
        )

    def insert(self, run: CollectionRun) -> None:
        self._conn.execute(
            """
            INSERT INTO lz_collection_runs (
                collection_run_id, repo_id, run_id, branch, commit,
                started_at, completed_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run.collection_run_id,
                run.repo_id,
                run.run_id,
                run.branch,
                run.commit,
                run.started_at,
                run.completed_at,
                run.status,
            ],
        )

    def mark_status(
        self, collection_run_id: str, status: str, completed_at: datetime | None
    ) -> None:
        self._conn.execute(
            """
            UPDATE lz_collection_runs
            SET status = ?, completed_at = ?
            WHERE collection_run_id = ?
            """,
            [status, completed_at, collection_run_id],
        )

    def reset_run(self, collection_run_id: str, started_at: datetime) -> None:
        self._conn.execute(
            """
            UPDATE lz_collection_runs
            SET started_at = ?, completed_at = NULL, status = 'running'
            WHERE collection_run_id = ?
            """,
            [started_at, collection_run_id],
        )

    def delete_collection_data(self, collection_run_id: str) -> None:
        run_pks = [
            row[0]
            for row in self._conn.execute(
                "SELECT run_pk FROM lz_tool_runs WHERE collection_run_id = ?",
                [collection_run_id],
            ).fetchall()
        ]
        if run_pks:
            placeholders = ",".join(["?"] * len(run_pks))
            tables = [
                row[0]
                for row in self._conn.execute(
                    """
                    SELECT table_name
                    FROM information_schema.columns
                    WHERE column_name = 'run_pk'
                    """
                ).fetchall()
            ]
            for table in sorted(set(tables)):
                if table == "lz_tool_runs":
                    continue
                self._conn.execute(
                    f"DELETE FROM {table} WHERE run_pk IN ({placeholders})",
                    run_pks,
                )
            self._conn.execute(
                f"DELETE FROM lz_tool_runs WHERE run_pk IN ({placeholders})",
                run_pks,
            )


class ToolRunRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def insert(self, run: ToolRun) -> int:
        result = self._conn.execute(
            """
            INSERT INTO lz_tool_runs (
                collection_run_id, repo_id, run_id, tool_name, tool_version, schema_version,
                branch, commit, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING run_pk
            """,
            [
                run.collection_run_id,
                run.repo_id,
                run.run_id,
                run.tool_name,
                run.tool_version,
                run.schema_version,
                run.branch,
                run.commit,
                run.timestamp,
            ],
        ).fetchone()
        if not result:
            raise RuntimeError("Failed to insert tool run")
        return int(result[0])

    def get_run_pk(self, collection_run_id: str, tool_name: str) -> int:
        row = self._conn.execute(
            """
            SELECT run_pk FROM lz_tool_runs
            WHERE collection_run_id = ? AND tool_name = ?
            """,
            [collection_run_id, tool_name],
        ).fetchone()
        if not row:
            raise KeyError("tool run not found")
        return int(row[0])

    def get_run_pk_any(self, collection_run_id: str, tool_names: Iterable[str]) -> int:
        names = list(tool_names)
        if not names:
            raise KeyError("tool run not found")
        placeholders = ", ".join(["?"] * len(names))
        row = self._conn.execute(
            f"""
            SELECT run_pk FROM lz_tool_runs
            WHERE collection_run_id = ? AND tool_name IN ({placeholders})
            """,
            [collection_run_id, *names],
        ).fetchone()
        if not row:
            raise KeyError("tool run not found")
        return int(row[0])


class LayoutRepository(BaseRepository):
    _FILE_COLUMNS = (
        "run_pk", "file_id", "relative_path", "directory_id", "filename",
        "extension", "language", "category", "size_bytes", "line_count", "is_binary",
    )
    _DIR_COLUMNS = (
        "run_pk", "directory_id", "relative_path", "parent_id", "depth",
        "file_count", "total_size_bytes",
    )

    def insert_files(self, files: Iterable[LayoutFile]) -> None:
        self._insert_bulk(
            "lz_layout_files",
            self._FILE_COLUMNS,
            files,
            lambda f: (
                f.run_pk, f.file_id, f.relative_path, f.directory_id, f.filename,
                f.extension, f.language, f.category, f.size_bytes, f.line_count, f.is_binary,
            ),
        )

    def insert_directories(self, directories: Iterable[LayoutDirectory]) -> None:
        self._insert_bulk(
            "lz_layout_directories",
            self._DIR_COLUMNS,
            directories,
            lambda d: (
                d.run_pk, d.directory_id, d.relative_path, d.parent_id, d.depth,
                d.file_count, d.total_size_bytes,
            ),
        )

    def get_file_record(self, run_pk: int, relative_path: str) -> tuple[str, str]:
        row = self._conn.execute(
            """
            SELECT file_id, directory_id FROM lz_layout_files
            WHERE run_pk = ? AND relative_path = ?
            """,
            [run_pk, relative_path],
        ).fetchone()
        if not row:
            raise KeyError(f"layout file not found: {relative_path}")
        return str(row[0]), str(row[1])


class SccRepository(BaseRepository):
    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "filename",
        "extension", "language", "lines_total", "code_lines", "comment_lines",
        "blank_lines", "bytes", "complexity", "uloc", "comment_ratio", "blank_ratio",
        "code_ratio", "complexity_density", "dryness", "bytes_per_loc",
        "is_minified", "is_generated", "is_binary", "classification",
    )

    def insert_file_metrics(self, rows: Iterable[SccFileMetric]) -> None:
        self._insert_bulk(
            "lz_scc_file_metrics",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.filename,
                r.extension, r.language, r.lines_total, r.code_lines, r.comment_lines,
                r.blank_lines, r.bytes, r.complexity, r.uloc, r.comment_ratio, r.blank_ratio,
                r.code_ratio, r.complexity_density, r.dryness, r.bytes_per_loc,
                r.is_minified, r.is_generated, r.is_binary, r.classification,
            ),
        )


class LizardRepository(BaseRepository):
    _FILE_COLUMNS = (
        "run_pk", "file_id", "relative_path", "language", "nloc",
        "function_count", "total_ccn", "avg_ccn", "max_ccn",
    )
    _FUNC_COLUMNS = (
        "run_pk", "file_id", "function_name", "long_name", "ccn", "nloc",
        "params", "token_count", "line_start", "line_end",
    )

    def insert_file_metrics(self, rows: Iterable[LizardFileMetric]) -> None:
        self._insert_bulk(
            "lz_lizard_file_metrics",
            self._FILE_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.relative_path, r.language, r.nloc,
                r.function_count, r.total_ccn, r.avg_ccn, r.max_ccn,
            ),
        )

    def insert_function_metrics(self, rows: Iterable[LizardFunctionMetric]) -> None:
        self._insert_bulk(
            "lz_lizard_function_metrics",
            self._FUNC_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.function_name, r.long_name, r.ccn, r.nloc,
                r.params, r.token_count, r.line_start, r.line_end,
            ),
        )


class SemgrepRepository(BaseRepository):
    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "rule_id",
        "dd_smell_id", "dd_category", "severity", "line_start", "line_end",
        "column_start", "column_end", "message", "code_snippet",
    )

    def insert_smells(self, rows: Iterable[SemgrepSmell]) -> None:
        self._insert_bulk(
            "lz_semgrep_smells",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.rule_id,
                r.dd_smell_id, r.dd_category, r.severity, r.line_start, r.line_end,
                r.column_start, r.column_end, r.message, r.code_snippet,
            ),
        )


class RoslynRepository(BaseRepository):
    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "rule_id",
        "dd_category", "severity", "message", "line_start", "line_end",
        "column_start", "column_end",
    )

    def insert_violations(self, rows: Iterable[RoslynViolation]) -> None:
        self._insert_bulk(
            "lz_roslyn_violations",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.rule_id,
                r.dd_category, r.severity, r.message, r.line_start, r.line_end,
                r.column_start, r.column_end,
            ),
        )



class SonarqubeRepository(BaseRepository):
    _ISSUE_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "issue_key",
        "rule_id", "issue_type", "severity", "message", "line_start", "line_end",
        "effort", "status", "tags",
    )
    _METRIC_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "ncloc",
        "complexity", "cognitive_complexity", "duplicated_lines",
        "duplicated_lines_density", "code_smells", "bugs", "vulnerabilities",
    )

    def insert_issues(self, rows: Iterable[SonarqubeIssue]) -> None:
        self._insert_bulk(
            "lz_sonarqube_issues",
            self._ISSUE_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.issue_key,
                r.rule_id, r.issue_type, r.severity, r.message, r.line_start, r.line_end,
                r.effort, r.status, r.tags,
            ),
        )

    def insert_metrics(self, rows: Iterable[SonarqubeMetric]) -> None:
        self._insert_bulk(
            "lz_sonarqube_metrics",
            self._METRIC_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.ncloc,
                r.complexity, r.cognitive_complexity, r.duplicated_lines,
                r.duplicated_lines_density, r.code_smells, r.bugs, r.vulnerabilities,
            ),
        )


class TrivyRepository(BaseRepository):
    _VULN_COLUMNS = (
        "run_pk", "target_key", "vulnerability_id", "package_name",
        "installed_version", "fixed_version", "severity", "cvss_score",
        "title", "published_date", "age_days", "fix_available",
    )
    _TARGET_COLUMNS = (
        "run_pk", "target_key", "file_id", "directory_id", "relative_path",
        "target_type", "vulnerability_count", "critical_count",
        "high_count", "medium_count", "low_count",
    )
    _IAC_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "misconfig_id",
        "severity", "title", "description", "resolution", "target_type",
        "start_line", "end_line",
    )

    def insert_vulnerabilities(self, rows: Iterable[TrivyVulnerability]) -> None:
        self._insert_bulk(
            "lz_trivy_vulnerabilities",
            self._VULN_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.target_key, r.vulnerability_id, r.package_name,
                r.installed_version, r.fixed_version, r.severity, r.cvss_score,
                r.title, r.published_date, r.age_days, r.fix_available,
            ),
        )

    def insert_targets(self, rows: Iterable[TrivyTarget]) -> None:
        self._insert_bulk(
            "lz_trivy_targets",
            self._TARGET_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.target_key, r.file_id, r.directory_id, r.relative_path,
                r.target_type, r.vulnerability_count, r.critical_count,
                r.high_count, r.medium_count, r.low_count,
            ),
        )

    def insert_iac_misconfigs(self, rows: Iterable[TrivyIacMisconfig]) -> None:
        self._insert_bulk(
            "lz_trivy_iac_misconfigs",
            self._IAC_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.misconfig_id,
                r.severity, r.title, r.description, r.resolution, r.target_type,
                r.start_line, r.end_line,
            ),
        )


class GitSizerRepository(BaseRepository):
    """Repository for git-sizer analysis data."""

    _METRIC_COLUMNS = (
        "run_pk", "repo_id", "health_grade", "duration_ms",
        "commit_count", "commit_total_size", "max_commit_size",
        "max_history_depth", "max_parent_count",
        "tree_count", "tree_total_size", "tree_total_entries", "max_tree_entries",
        "blob_count", "blob_total_size", "max_blob_size",
        "tag_count", "max_tag_depth",
        "reference_count", "branch_count",
        "max_path_depth", "max_path_length",
        "expanded_tree_count", "expanded_blob_count", "expanded_blob_size",
    )
    _VIOLATION_COLUMNS = (
        "run_pk", "metric", "value_display", "raw_value", "level", "object_ref",
    )
    _LFS_COLUMNS = (
        "run_pk", "file_path",
    )

    def insert_metrics(self, metric: GitSizerMetric) -> None:
        """Insert repository-level metrics."""
        self._conn.execute(
            f"""
            INSERT INTO lz_git_sizer_metrics ({', '.join(self._METRIC_COLUMNS)})
            VALUES ({', '.join(['?'] * len(self._METRIC_COLUMNS))})
            """,
            [
                metric.run_pk, metric.repo_id, metric.health_grade, metric.duration_ms,
                metric.commit_count, metric.commit_total_size, metric.max_commit_size,
                metric.max_history_depth, metric.max_parent_count,
                metric.tree_count, metric.tree_total_size, metric.tree_total_entries,
                metric.max_tree_entries,
                metric.blob_count, metric.blob_total_size, metric.max_blob_size,
                metric.tag_count, metric.max_tag_depth,
                metric.reference_count, metric.branch_count,
                metric.max_path_depth, metric.max_path_length,
                metric.expanded_tree_count, metric.expanded_blob_count,
                metric.expanded_blob_size,
            ],
        )

    def insert_violations(self, rows: Iterable[GitSizerViolation]) -> None:
        """Insert threshold violations."""
        self._insert_bulk(
            "lz_git_sizer_violations",
            self._VIOLATION_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.metric, r.value_display, r.raw_value, r.level, r.object_ref,
            ),
        )

    def insert_lfs_candidates(self, rows: Iterable[GitSizerLfsCandidate]) -> None:
        """Insert LFS migration candidates."""
        self._insert_bulk(
            "lz_git_sizer_lfs_candidates",
            self._LFS_COLUMNS,
            rows,
            lambda r: (r.run_pk, r.file_path),
        )
