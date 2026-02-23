"""Centralized data quality framework for the SoT engine.

Provides FK pre-validation, uniqueness checks, metadata completeness,
and quality scoring. Wraps existing validation and adds advisory quality
reports without replacing per-adapter QUALITY_RULES.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import duckdb

_log = logging.getLogger(__name__)

# Required metadata fields per the Caldera envelope spec
_REQUIRED_METADATA_FIELDS = frozenset({
    "tool_name",
    "tool_version",
    "schema_version",
    "repo_id",
    "run_id",
    "branch",
    "commit",
    "timestamp",
})


class CheckLevel(Enum):
    """Quality check level."""
    L1 = "L1"  # Pre-insert (schema, metadata)
    L2 = "L2"  # Post-insert (FK, uniqueness)


class CheckSeverity(Enum):
    """Severity of a quality check result."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class CheckResult:
    """Result of a single quality check."""
    check_name: str
    level: CheckLevel
    passed: bool
    severity: CheckSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityScore:
    """Quality score with four dimensions, each in [0.0, 1.0].

    The overall score is a weighted average:
    - completeness: 0.30
    - validity: 0.30
    - consistency: 0.25
    - timeliness: 0.15
    """
    completeness: float
    validity: float
    consistency: float
    timeliness: float

    def __post_init__(self) -> None:
        for name in ("completeness", "validity", "consistency", "timeliness"):
            val = getattr(self, name)
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")

    @property
    def overall(self) -> float:
        """Weighted overall score."""
        return round(
            self.completeness * 0.30
            + self.validity * 0.30
            + self.consistency * 0.25
            + self.timeliness * 0.15,
            4,
        )


@dataclass(frozen=True)
class QualityReport:
    """Aggregated quality report for a tool's ingestion."""
    tool_name: str
    checks: tuple[CheckResult, ...]
    score: QualityScore

    @property
    def passed(self) -> bool:
        """True if no checks have ERROR severity and failed."""
        return all(
            c.passed or c.severity != CheckSeverity.ERROR
            for c in self.checks
        )

    @property
    def warnings(self) -> list[CheckResult]:
        """Return failed checks with WARNING severity."""
        return [c for c in self.checks if not c.passed and c.severity == CheckSeverity.WARNING]

    @property
    def errors(self) -> list[CheckResult]:
        """Return failed checks with ERROR severity."""
        return [c for c in self.checks if not c.passed and c.severity == CheckSeverity.ERROR]


class DataQualityChecker:
    """Centralized quality checker for tool data ingestion.

    Usage:
        checker = DataQualityChecker(conn)
        report = checker.check_metadata(payload.get("metadata", {}), "scc")
        report = checker.check_fk_integrity("lz_scc_file_metrics", "file_id", run_pk, "scc")
        report = checker.check_uniqueness("lz_scc_file_metrics", ["run_pk", "file_id"], "scc")
    """

    def __init__(
        self,
        conn: duckdb.DuckDBPyConnection,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._conn = conn
        self._logger = logger

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger(message)

    def check_metadata(self, metadata: dict[str, Any], tool_name: str) -> CheckResult:
        """Check that all 8 required envelope metadata fields are present.

        Args:
            metadata: The metadata dict from the tool output payload.
            tool_name: Tool name for reporting.

        Returns:
            CheckResult with pass/fail and missing field details.
        """
        missing = _REQUIRED_METADATA_FIELDS - set(metadata.keys())
        empty = {
            k for k in _REQUIRED_METADATA_FIELDS & set(metadata.keys())
            if metadata[k] in (None, "")
        }
        all_issues = missing | empty
        passed = len(all_issues) == 0
        severity = CheckSeverity.WARNING if all_issues else CheckSeverity.INFO
        message = (
            f"{tool_name}: all metadata fields present"
            if passed
            else f"{tool_name}: missing/empty metadata fields: {sorted(all_issues)}"
        )
        result = CheckResult(
            check_name="metadata_completeness",
            level=CheckLevel.L1,
            passed=passed,
            severity=severity,
            message=message,
            details={"missing": sorted(missing), "empty": sorted(empty)},
        )
        if not passed:
            self._log(f"QUALITY_WARNING: {message}")
        return result

    def check_fk_integrity(
        self,
        table: str,
        fk_column: str,
        run_pk: int,
        tool_name: str,
        ref_table: str = "lz_layout_files",
        ref_column: str = "file_id",
    ) -> CheckResult:
        """Check that FK references in a table exist in the reference table.

        Args:
            table: Table containing the FK column.
            fk_column: Column name in the source table.
            run_pk: Run primary key to scope the check.
            tool_name: Tool name for reporting.
            ref_table: Reference table (default: lz_layout_files).
            ref_column: Reference column (default: file_id).

        Returns:
            CheckResult with orphan count details.
        """
        query = f"""
            SELECT COUNT(*) FROM {table} t
            WHERE t.run_pk = ?
              AND t.{fk_column} IS NOT NULL
              AND t.{fk_column} NOT IN (
                  SELECT {ref_column} FROM {ref_table}
              )
        """
        try:
            row = self._conn.execute(query, [run_pk]).fetchone()
            orphan_count = row[0] if row else 0
        except duckdb.CatalogException:
            # Table doesn't exist yet — skip check
            return CheckResult(
                check_name="fk_integrity",
                level=CheckLevel.L2,
                passed=True,
                severity=CheckSeverity.INFO,
                message=f"{tool_name}: FK check skipped (table not found)",
                details={"table": table, "skipped": True},
            )

        passed = orphan_count == 0
        severity = CheckSeverity.WARNING if not passed else CheckSeverity.INFO
        message = (
            f"{tool_name}: all {fk_column} references valid"
            if passed
            else f"{tool_name}: {orphan_count} orphan {fk_column} reference(s) in {table}"
        )
        result = CheckResult(
            check_name="fk_integrity",
            level=CheckLevel.L2,
            passed=passed,
            severity=severity,
            message=message,
            details={"table": table, "fk_column": fk_column, "orphan_count": orphan_count},
        )
        if not passed:
            self._log(f"QUALITY_WARNING: {message}")
        return result

    def check_uniqueness(
        self,
        table: str,
        key_columns: list[str],
        tool_name: str,
    ) -> CheckResult:
        """Check for duplicate rows based on key columns.

        Args:
            table: Table to check.
            key_columns: Columns that should be unique together.
            tool_name: Tool name for reporting.

        Returns:
            CheckResult with total vs distinct counts.
        """
        cols = ", ".join(key_columns)
        try:
            row = self._conn.execute(
                f"SELECT COUNT(*), COUNT(DISTINCT ({cols})) FROM {table}"
            ).fetchone()
            total, distinct = (row[0], row[1]) if row else (0, 0)
        except duckdb.CatalogException:
            return CheckResult(
                check_name="uniqueness",
                level=CheckLevel.L2,
                passed=True,
                severity=CheckSeverity.INFO,
                message=f"{tool_name}: uniqueness check skipped (table not found)",
                details={"table": table, "skipped": True},
            )

        duplicate_count = total - distinct
        passed = duplicate_count == 0
        severity = CheckSeverity.WARNING if not passed else CheckSeverity.INFO
        message = (
            f"{tool_name}: {table} has unique {cols}"
            if passed
            else f"{tool_name}: {duplicate_count} duplicate(s) in {table} on ({cols})"
        )
        result = CheckResult(
            check_name="uniqueness",
            level=CheckLevel.L2,
            passed=passed,
            severity=severity,
            message=message,
            details={
                "table": table,
                "key_columns": key_columns,
                "total": total,
                "distinct": distinct,
                "duplicates": duplicate_count,
            },
        )
        if not passed:
            self._log(f"QUALITY_WARNING: {message}")
        return result

    def build_report(
        self,
        tool_name: str,
        checks: list[CheckResult],
        *,
        schema_valid: bool = True,
        metadata_complete: bool = True,
    ) -> QualityReport:
        """Build a QualityReport from collected check results.

        Args:
            tool_name: Tool name for the report.
            checks: List of CheckResult instances.
            schema_valid: Whether JSON schema validation passed.
            metadata_complete: Whether metadata completeness passed.

        Returns:
            QualityReport with computed score.
        """
        # Compute score dimensions
        completeness = 1.0 if metadata_complete else 0.5
        validity = 1.0 if schema_valid else 0.0

        # Consistency: ratio of passed L2 checks
        l2_checks = [c for c in checks if c.level == CheckLevel.L2]
        if l2_checks:
            consistency = sum(1 for c in l2_checks if c.passed) / len(l2_checks)
        else:
            consistency = 1.0

        # Timeliness: always 1.0 (real-time ingestion)
        timeliness = 1.0

        score = QualityScore(
            completeness=round(completeness, 4),
            validity=round(validity, 4),
            consistency=round(consistency, 4),
            timeliness=round(timeliness, 4),
        )

        report = QualityReport(
            tool_name=tool_name,
            checks=tuple(checks),
            score=score,
        )

        self._log(
            f"QUALITY_REPORT: {tool_name} — overall={score.overall:.2f} "
            f"(completeness={score.completeness}, validity={score.validity}, "
            f"consistency={score.consistency}, timeliness={score.timeliness})"
        )

        return report
