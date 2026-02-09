from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Sequence, TypeVar
import duckdb

from .entities import (
    CodeSymbol,
    CollectionRun,
    DependenseePackageReference,
    DependenseeProject,
    DependenseeProjectReference,
    DevskimFinding,
    DotcoverAssemblyCoverage,
    DotcoverMethodCoverage,
    DotcoverTypeCoverage,
    FileImport,
    GitBlameAuthorStats,
    GitBlameFileSummary,
    GitFameAuthor,
    GitFameSummary,
    GitSizerLfsCandidate,
    GitSizerMetric,
    GitSizerViolation,
    GitleaksSecret,
    LayoutDirectory,
    LayoutFile,
    LizardFileMetric,
    LizardFunctionMetric,
    PmdCpdDuplication,
    PmdCpdFileMetric,
    PmdCpdOccurrence,
    RoslynViolation,
    ScancodeFileLicense,
    ScancodeSummary,
    SccFileMetric,
    SemgrepSmell,
    SonarqubeIssue,
    SonarqubeMetric,
    SymbolCall,
    ToolRun,
    TrivyIacMisconfig,
    TrivyTarget,
    TrivyVulnerability,
)

T = TypeVar("T")

# Whitelist of valid landing zone table names that contain run_pk column.
# This prevents SQL injection when table names are used in dynamic SQL.
_VALID_LZ_TABLES = frozenset([
    "lz_tool_runs",
    "lz_layout_files",
    "lz_layout_directories",
    "lz_scc_file_metrics",
    "lz_lizard_file_metrics",
    "lz_lizard_function_metrics",
    "lz_semgrep_smells",
    "lz_gitleaks_secrets",
    "lz_roslyn_violations",
    "lz_devskim_findings",
    "lz_sonarqube_issues",
    "lz_sonarqube_metrics",
    "lz_trivy_targets",
    "lz_trivy_vulnerabilities",
    "lz_trivy_iac_misconfigs",
    "lz_git_sizer_metrics",
    "lz_git_sizer_violations",
    "lz_git_sizer_lfs_candidates",
    "lz_code_symbols",
    "lz_symbol_calls",
    "lz_file_imports",
    "lz_scancode_file_licenses",
    "lz_scancode_summary",
    "lz_pmd_cpd_file_metrics",
    "lz_pmd_cpd_duplications",
    "lz_pmd_cpd_occurrences",
    "lz_dotcover_assembly_coverage",
    "lz_dotcover_type_coverage",
    "lz_dotcover_method_coverage",
    "lz_dependensee_projects",
    "lz_dependensee_project_refs",
    "lz_dependensee_package_refs",
    "lz_git_fame_authors",
    "lz_git_fame_summary",
    "lz_git_blame_summary",
    "lz_git_blame_author_stats",
])


def _validate_table_name(table: str) -> None:
    """Validate that a table name is in the allowed whitelist.

    Raises:
        ValueError: If the table name is not whitelisted.
    """
    if table not in _VALID_LZ_TABLES:
        raise ValueError(f"Invalid table name: {table}")


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
                    SELECT DISTINCT c.table_name
                    FROM information_schema.columns c
                    JOIN information_schema.tables t
                      ON c.table_name = t.table_name
                     AND c.table_schema = t.table_schema
                    WHERE c.column_name = 'run_pk'
                      AND t.table_type = 'BASE TABLE'
                      AND c.table_name LIKE 'lz_%'
                    """
                ).fetchall()
            ]
            for table in sorted(set(tables)):
                if table == "lz_tool_runs":
                    continue
                # Validate table name against whitelist to prevent SQL injection
                _validate_table_name(table)
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


class GitleaksRepository(BaseRepository):
    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "rule_id",
        "secret_type", "severity", "line_number", "commit_hash", "commit_author",
        "commit_date", "fingerprint", "in_current_head", "entropy", "description",
    )

    def insert_secrets(self, rows: Iterable[GitleaksSecret]) -> None:
        self._insert_bulk(
            "lz_gitleaks_secrets",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.rule_id,
                r.secret_type, r.severity, r.line_number, r.commit_hash, r.commit_author,
                r.commit_date, r.fingerprint, r.in_current_head, r.entropy, r.description,
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


class DevskimRepository(BaseRepository):
    _COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "rule_id",
        "dd_category", "severity", "line_start", "line_end",
        "column_start", "column_end", "message", "code_snippet",
    )

    def insert_findings(self, rows: Iterable[DevskimFinding]) -> None:
        self._insert_bulk(
            "lz_devskim_findings",
            self._COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.rule_id,
                r.dd_category, r.severity, r.line_start, r.line_end,
                r.column_start, r.column_end, r.message, r.code_snippet,
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

    def insert_metrics(self, rows: Iterable[GitSizerMetric]) -> None:
        """Insert repository-level metrics."""
        self._insert_bulk(
            "lz_git_sizer_metrics",
            self._METRIC_COLUMNS,
            rows,
            lambda m: (
                m.run_pk, m.repo_id, m.health_grade, m.duration_ms,
                m.commit_count, m.commit_total_size, m.max_commit_size,
                m.max_history_depth, m.max_parent_count,
                m.tree_count, m.tree_total_size, m.tree_total_entries,
                m.max_tree_entries,
                m.blob_count, m.blob_total_size, m.max_blob_size,
                m.tag_count, m.max_tag_depth,
                m.reference_count, m.branch_count,
                m.max_path_depth, m.max_path_length,
                m.expanded_tree_count, m.expanded_blob_count,
                m.expanded_blob_size,
            ),
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


class SymbolScannerRepository(BaseRepository):
    """Repository for symbol-scanner analysis data."""

    _SYMBOL_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "symbol_name",
        "symbol_type", "line_start", "line_end", "is_exported", "parameters",
        "parent_symbol", "docstring",
    )
    _CALL_COLUMNS = (
        "run_pk", "caller_file_id", "caller_directory_id", "caller_file_path",
        "caller_symbol", "callee_symbol", "callee_file_id", "callee_file_path",
        "line_number", "call_type",
    )
    _IMPORT_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "imported_path",
        "imported_symbols", "import_type", "line_number",
    )

    def insert_symbols(self, rows: Iterable[CodeSymbol]) -> None:
        """Insert code symbol records."""
        self._insert_bulk(
            "lz_code_symbols",
            self._SYMBOL_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.symbol_name,
                r.symbol_type, r.line_start, r.line_end, r.is_exported, r.parameters,
                r.parent_symbol, r.docstring,
            ),
        )

    def insert_calls(self, rows: Iterable[SymbolCall]) -> None:
        """Insert symbol call records."""
        self._insert_bulk(
            "lz_symbol_calls",
            self._CALL_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.caller_file_id, r.caller_directory_id, r.caller_file_path,
                r.caller_symbol, r.callee_symbol, r.callee_file_id, r.callee_file_path,
                r.line_number, r.call_type,
            ),
        )

    def insert_imports(self, rows: Iterable[FileImport]) -> None:
        """Insert file import records."""
        self._insert_bulk(
            "lz_file_imports",
            self._IMPORT_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.imported_path,
                r.imported_symbols, r.import_type, r.line_number,
            ),
        )


class ScancodeRepository(BaseRepository):
    """Repository for scancode license analysis data."""

    _LICENSE_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "spdx_id",
        "category", "confidence", "match_type", "line_number",
    )
    _SUMMARY_COLUMNS = (
        "run_pk", "total_files_scanned", "files_with_licenses", "overall_risk",
        "has_permissive", "has_weak_copyleft", "has_copyleft", "has_unknown",
    )

    def insert_file_licenses(self, rows: Iterable[ScancodeFileLicense]) -> None:
        """Insert file license records."""
        self._insert_bulk(
            "lz_scancode_file_licenses",
            self._LICENSE_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.spdx_id,
                r.category, r.confidence, r.match_type, r.line_number,
            ),
        )

    def insert_summary(self, rows: Iterable[ScancodeSummary]) -> None:
        """Insert summary record."""
        self._insert_bulk(
            "lz_scancode_summary",
            self._SUMMARY_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.total_files_scanned, r.files_with_licenses, r.overall_risk,
                r.has_permissive, r.has_weak_copyleft, r.has_copyleft, r.has_unknown,
            ),
        )


class PmdCpdRepository(BaseRepository):
    """Repository for pmd-cpd duplication analysis data."""

    _FILE_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path", "language",
        "total_lines", "duplicate_lines", "duplicate_blocks", "duplication_percentage",
    )
    _DUPLICATION_COLUMNS = (
        "run_pk", "clone_id", "lines", "tokens", "occurrence_count",
        "is_cross_file", "code_fragment",
    )
    _OCCURRENCE_COLUMNS = (
        "run_pk", "clone_id", "file_id", "directory_id", "relative_path",
        "line_start", "line_end", "column_start", "column_end",
    )

    def insert_file_metrics(self, rows: Iterable[PmdCpdFileMetric]) -> None:
        """Insert per-file duplication metrics."""
        self._insert_bulk(
            "lz_pmd_cpd_file_metrics",
            self._FILE_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path, r.language,
                r.total_lines, r.duplicate_lines, r.duplicate_blocks, r.duplication_percentage,
            ),
        )

    def insert_duplications(self, rows: Iterable[PmdCpdDuplication]) -> None:
        """Insert clone group records."""
        self._insert_bulk(
            "lz_pmd_cpd_duplications",
            self._DUPLICATION_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.clone_id, r.lines, r.tokens, r.occurrence_count,
                r.is_cross_file, r.code_fragment,
            ),
        )

    def insert_occurrences(self, rows: Iterable[PmdCpdOccurrence]) -> None:
        """Insert individual clone locations."""
        self._insert_bulk(
            "lz_pmd_cpd_occurrences",
            self._OCCURRENCE_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.clone_id, r.file_id, r.directory_id, r.relative_path,
                r.line_start, r.line_end, r.column_start, r.column_end,
            ),
        )


class DotcoverRepository(BaseRepository):
    """Repository for dotcover code coverage data."""

    _ASSEMBLY_COLUMNS = (
        "run_pk", "assembly_name", "covered_statements",
        "total_statements", "statement_coverage_pct",
    )
    _TYPE_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path",
        "assembly_name", "namespace", "type_name",
        "covered_statements", "total_statements", "statement_coverage_pct",
    )
    _METHOD_COLUMNS = (
        "run_pk", "assembly_name", "type_name", "method_name",
        "covered_statements", "total_statements", "statement_coverage_pct",
    )

    def insert_assembly_coverage(self, rows: Iterable[DotcoverAssemblyCoverage]) -> None:
        """Insert assembly-level coverage metrics."""
        self._insert_bulk(
            "lz_dotcover_assembly_coverage",
            self._ASSEMBLY_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.assembly_name, r.covered_statements,
                r.total_statements, r.statement_coverage_pct,
            ),
        )

    def insert_type_coverage(self, rows: Iterable[DotcoverTypeCoverage]) -> None:
        """Insert type (class) level coverage metrics."""
        self._insert_bulk(
            "lz_dotcover_type_coverage",
            self._TYPE_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path,
                r.assembly_name, r.namespace, r.type_name,
                r.covered_statements, r.total_statements, r.statement_coverage_pct,
            ),
        )

    def insert_method_coverage(self, rows: Iterable[DotcoverMethodCoverage]) -> None:
        """Insert method-level coverage metrics."""
        self._insert_bulk(
            "lz_dotcover_method_coverage",
            self._METHOD_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.assembly_name, r.type_name, r.method_name,
                r.covered_statements, r.total_statements, r.statement_coverage_pct,
            ),
        )


class DependenseeRepository(BaseRepository):
    """Repository for dependensee analysis data."""

    _PROJECT_COLUMNS = (
        "run_pk", "project_path", "project_name", "target_framework",
        "project_reference_count", "package_reference_count",
    )

    _PROJECT_REF_COLUMNS = (
        "run_pk", "source_project_path", "target_project_path",
    )

    _PACKAGE_REF_COLUMNS = (
        "run_pk", "project_path", "package_name", "package_version",
    )

    def insert_projects(self, rows: Iterable[DependenseeProject]) -> None:
        self._insert_bulk(
            "lz_dependensee_projects",
            self._PROJECT_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.project_path, r.project_name, r.target_framework,
                r.project_reference_count, r.package_reference_count,
            ),
        )

    def insert_project_references(self, rows: Iterable[DependenseeProjectReference]) -> None:
        self._insert_bulk(
            "lz_dependensee_project_refs",
            self._PROJECT_REF_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.source_project_path, r.target_project_path,
            ),
        )

    def insert_package_references(self, rows: Iterable[DependenseePackageReference]) -> None:
        self._insert_bulk(
            "lz_dependensee_package_refs",
            self._PACKAGE_REF_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.project_path, r.package_name, r.package_version,
            ),
        )


class GitFameRepository(BaseRepository):
    """Repository for git-fame authorship analysis data."""

    _AUTHOR_COLUMNS = (
        "run_pk", "author_name", "author_email", "surviving_loc",
        "ownership_pct", "insertions_total", "deletions_total",
        "commit_count", "files_touched",
    )

    _SUMMARY_COLUMNS = (
        "run_pk", "repo_id", "author_count", "total_loc",
        "hhi_index", "bus_factor", "top_author_pct", "top_two_pct",
    )

    def insert_authors(self, rows: Iterable[GitFameAuthor]) -> None:
        """Insert per-author authorship metrics."""
        self._insert_bulk(
            "lz_git_fame_authors",
            self._AUTHOR_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.author_name, r.author_email, r.surviving_loc,
                r.ownership_pct, r.insertions_total, r.deletions_total,
                r.commit_count, r.files_touched,
            ),
        )

    def insert_summary(self, rows: Iterable[GitFameSummary]) -> None:
        """Insert repository-level summary metrics."""
        self._insert_bulk(
            "lz_git_fame_summary",
            self._SUMMARY_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.repo_id, r.author_count, r.total_loc,
                r.hhi_index, r.bus_factor, r.top_author_pct, r.top_two_pct,
            ),
        )


class GitBlameRepository(BaseRepository):
    """Repository for git-blame-scanner analysis data."""

    _SUMMARY_COLUMNS = (
        "run_pk", "file_id", "directory_id", "relative_path",
        "total_lines", "unique_authors", "top_author", "top_author_lines",
        "top_author_pct", "last_modified", "churn_30d", "churn_90d",
    )

    _AUTHOR_COLUMNS = (
        "run_pk", "author_email", "total_files", "total_lines",
        "exclusive_files", "avg_ownership_pct",
    )

    def insert_file_summaries(self, rows: Iterable[GitBlameFileSummary]) -> None:
        self._insert_bulk(
            "lz_git_blame_summary",
            self._SUMMARY_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.file_id, r.directory_id, r.relative_path,
                r.total_lines, r.unique_authors, r.top_author, r.top_author_lines,
                r.top_author_pct, r.last_modified, r.churn_30d, r.churn_90d,
            ),
        )

    def insert_author_stats(self, rows: Iterable[GitBlameAuthorStats]) -> None:
        self._insert_bulk(
            "lz_git_blame_author_stats",
            self._AUTHOR_COLUMNS,
            rows,
            lambda r: (
                r.run_pk, r.author_email, r.total_files, r.total_lines,
                r.exclusive_files, r.avg_ownership_pct,
            ),
        )
