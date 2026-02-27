"""Tests for DataQualityChecker."""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from persistence.quality import (
    CheckLevel,
    CheckResult,
    CheckSeverity,
    DataQualityChecker,
    QualityReport,
    QualityScore,
)


# ---------------------------------------------------------------------------
# QualityScore
# ---------------------------------------------------------------------------

class TestQualityScore:
    def test_valid_score(self):
        s = QualityScore(1.0, 0.8, 0.9, 1.0)
        assert s.completeness == 1.0
        assert s.validity == 0.8
        assert s.overall == round(1.0 * 0.30 + 0.8 * 0.30 + 0.9 * 0.25 + 1.0 * 0.15, 4)

    def test_perfect_score(self):
        s = QualityScore(1.0, 1.0, 1.0, 1.0)
        assert s.overall == 1.0

    def test_zero_score(self):
        s = QualityScore(0.0, 0.0, 0.0, 0.0)
        assert s.overall == 0.0

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="completeness"):
            QualityScore(-0.1, 1.0, 1.0, 1.0)

    def test_rejects_above_one(self):
        with pytest.raises(ValueError, match="validity"):
            QualityScore(1.0, 1.1, 1.0, 1.0)



# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------

class TestCheckResult:
    def test_creation(self):
        r = CheckResult(
            check_name="metadata_completeness",
            level=CheckLevel.L1,
            passed=True,
            severity=CheckSeverity.INFO,
            message="all good",
        )
        assert r.passed is True
        assert r.details == {}


# ---------------------------------------------------------------------------
# QualityReport
# ---------------------------------------------------------------------------

class TestQualityReport:
    def test_passed_all_good(self):
        checks = (
            CheckResult("a", CheckLevel.L1, True, CheckSeverity.INFO, "ok"),
            CheckResult("b", CheckLevel.L2, True, CheckSeverity.INFO, "ok"),
        )
        report = QualityReport("scc", checks, QualityScore(1.0, 1.0, 1.0, 1.0))
        assert report.passed is True
        assert report.warnings == []
        assert report.errors == []

    def test_passed_with_warnings(self):
        checks = (
            CheckResult("a", CheckLevel.L1, False, CheckSeverity.WARNING, "warn"),
        )
        report = QualityReport("scc", checks, QualityScore(0.5, 1.0, 1.0, 1.0))
        assert report.passed is True  # warnings don't block
        assert len(report.warnings) == 1

    def test_failed_with_errors(self):
        checks = (
            CheckResult("a", CheckLevel.L1, False, CheckSeverity.ERROR, "bad"),
        )
        report = QualityReport("scc", checks, QualityScore(0.0, 0.0, 1.0, 1.0))
        assert report.passed is False
        assert len(report.errors) == 1


# ---------------------------------------------------------------------------
# DataQualityChecker
# ---------------------------------------------------------------------------

class TestDataQualityChecker:
    @pytest.fixture()
    def conn(self):
        c = duckdb.connect(":memory:")
        yield c
        c.close()

    def test_check_metadata_complete(self, conn: duckdb.DuckDBPyConnection):
        checker = DataQualityChecker(conn)
        metadata = {
            "tool_name": "scc",
            "tool_version": "3.0.0",
            "schema_version": "1.0.0",
            "repo_id": "repo-1",
            "run_id": "run-1",
            "branch": "main",
            "commit": "abc123",
            "timestamp": "2025-01-01T00:00:00Z",
        }
        result = checker.check_metadata(metadata, "scc")
        assert result.passed is True
        assert result.severity == CheckSeverity.INFO

    def test_check_metadata_missing_fields(self, conn: duckdb.DuckDBPyConnection):
        checker = DataQualityChecker(conn)
        metadata = {"tool_name": "scc", "tool_version": "3.0.0"}
        result = checker.check_metadata(metadata, "scc")
        assert result.passed is False
        assert result.severity == CheckSeverity.WARNING
        assert len(result.details["missing"]) > 0

    def test_check_metadata_empty_fields(self, conn: duckdb.DuckDBPyConnection):
        checker = DataQualityChecker(conn)
        metadata = {
            "tool_name": "scc",
            "tool_version": "",
            "schema_version": "1.0.0",
            "repo_id": "repo-1",
            "run_id": "run-1",
            "branch": "main",
            "commit": "abc123",
            "timestamp": "2025-01-01T00:00:00Z",
        }
        result = checker.check_metadata(metadata, "scc")
        assert result.passed is False
        assert "tool_version" in result.details["empty"]

    def test_check_fk_integrity_all_valid(self, conn: duckdb.DuckDBPyConnection):
        conn.execute("CREATE TABLE lz_layout_files (file_id VARCHAR, run_pk BIGINT)")
        conn.execute("INSERT INTO lz_layout_files VALUES ('f-1', 1), ('f-2', 1)")
        conn.execute("CREATE TABLE lz_scc_file_metrics (file_id VARCHAR, run_pk BIGINT)")
        conn.execute("INSERT INTO lz_scc_file_metrics VALUES ('f-1', 2), ('f-2', 2)")

        checker = DataQualityChecker(conn)
        result = checker.check_fk_integrity("lz_scc_file_metrics", "file_id", 2, "scc")
        assert result.passed is True

    def test_check_fk_integrity_orphans(self, conn: duckdb.DuckDBPyConnection):
        conn.execute("CREATE TABLE lz_layout_files (file_id VARCHAR, run_pk BIGINT)")
        conn.execute("INSERT INTO lz_layout_files VALUES ('f-1', 1)")
        conn.execute("CREATE TABLE lz_scc_file_metrics (file_id VARCHAR, run_pk BIGINT)")
        conn.execute("INSERT INTO lz_scc_file_metrics VALUES ('f-1', 2), ('f-999', 2)")

        checker = DataQualityChecker(conn)
        result = checker.check_fk_integrity("lz_scc_file_metrics", "file_id", 2, "scc")
        assert result.passed is False
        assert result.details["orphan_count"] == 1

    def test_check_fk_integrity_missing_table(self, conn: duckdb.DuckDBPyConnection):
        checker = DataQualityChecker(conn)
        result = checker.check_fk_integrity("nonexistent_table", "file_id", 1, "scc")
        assert result.passed is True
        assert result.details.get("skipped") is True

    def test_check_uniqueness_no_duplicates(self, conn: duckdb.DuckDBPyConnection):
        conn.execute("CREATE TABLE lz_scc (run_pk BIGINT, file_id VARCHAR)")
        conn.execute("INSERT INTO lz_scc VALUES (1, 'f-1'), (1, 'f-2')")

        checker = DataQualityChecker(conn)
        result = checker.check_uniqueness("lz_scc", ["run_pk", "file_id"], "scc")
        assert result.passed is True
        assert result.details["duplicates"] == 0

    def test_check_uniqueness_with_duplicates(self, conn: duckdb.DuckDBPyConnection):
        conn.execute("CREATE TABLE lz_scc (run_pk BIGINT, file_id VARCHAR)")
        conn.execute("INSERT INTO lz_scc VALUES (1, 'f-1'), (1, 'f-1'), (1, 'f-2')")

        checker = DataQualityChecker(conn)
        result = checker.check_uniqueness("lz_scc", ["run_pk", "file_id"], "scc")
        assert result.passed is False
        assert result.details["duplicates"] == 1

    def test_check_uniqueness_missing_table(self, conn: duckdb.DuckDBPyConnection):
        checker = DataQualityChecker(conn)
        result = checker.check_uniqueness("nonexistent", ["id"], "scc")
        assert result.passed is True
        assert result.details.get("skipped") is True

    def test_build_report(self, conn: duckdb.DuckDBPyConnection):
        checker = DataQualityChecker(conn)
        checks = [
            CheckResult("metadata", CheckLevel.L1, True, CheckSeverity.INFO, "ok"),
            CheckResult("fk", CheckLevel.L2, True, CheckSeverity.INFO, "ok"),
            CheckResult("unique", CheckLevel.L2, False, CheckSeverity.WARNING, "dups"),
        ]
        report = checker.build_report("scc", checks, schema_valid=True, metadata_complete=True)
        assert report.tool_name == "scc"
        assert report.score.completeness == 1.0
        assert report.score.validity == 1.0
        assert report.score.consistency == 0.5  # 1 of 2 L2 checks passed
        assert report.passed is True  # only warnings

    def test_build_report_schema_invalid(self, conn: duckdb.DuckDBPyConnection):
        checker = DataQualityChecker(conn)
        report = checker.build_report(
            "scc", [], schema_valid=False, metadata_complete=False,
        )
        assert report.score.validity == 0.0
        assert report.score.completeness == 0.5

    def test_logger_called(self, conn: duckdb.DuckDBPyConnection):
        messages: list[str] = []
        checker = DataQualityChecker(conn, logger=messages.append)

        metadata = {"tool_name": "scc"}
        checker.check_metadata(metadata, "scc")

        assert any("QUALITY_WARNING" in m for m in messages)

    def test_build_report_logs_summary(self, conn: duckdb.DuckDBPyConnection):
        messages: list[str] = []
        checker = DataQualityChecker(conn, logger=messages.append)
        checker.build_report("scc", [], schema_valid=True, metadata_complete=True)
        assert any("QUALITY_REPORT" in m for m in messages)

    def test_check_fk_integrity_custom_ref_table(self, conn: duckdb.DuckDBPyConnection):
        """FK check with a custom ref_table and ref_column instead of defaults."""
        conn.execute("CREATE TABLE lz_custom_ref (custom_id VARCHAR)")
        conn.execute("INSERT INTO lz_custom_ref VALUES ('c-1'), ('c-2')")
        conn.execute("CREATE TABLE lz_tool_data (ref_id VARCHAR, run_pk BIGINT)")
        conn.execute("INSERT INTO lz_tool_data VALUES ('c-1', 1), ('c-3', 1)")

        checker = DataQualityChecker(conn)
        result = checker.check_fk_integrity(
            "lz_tool_data", "ref_id", 1, "test-tool",
            ref_table="lz_custom_ref", ref_column="custom_id",
        )
        assert result.passed is False
        assert result.details["orphan_count"] == 1

    def test_check_fk_integrity_custom_ref_all_valid(self, conn: duckdb.DuckDBPyConnection):
        """FK check with custom ref passes when all references exist."""
        conn.execute("CREATE TABLE lz_ref (rid VARCHAR)")
        conn.execute("INSERT INTO lz_ref VALUES ('r-1'), ('r-2')")
        conn.execute("CREATE TABLE lz_child (fk_col VARCHAR, run_pk BIGINT)")
        conn.execute("INSERT INTO lz_child VALUES ('r-1', 1), ('r-2', 1)")

        checker = DataQualityChecker(conn)
        result = checker.check_fk_integrity(
            "lz_child", "fk_col", 1, "test-tool",
            ref_table="lz_ref", ref_column="rid",
        )
        assert result.passed is True

    def test_check_uniqueness_empty_table(self, conn: duckdb.DuckDBPyConnection):
        """Uniqueness check on an empty table should pass with 0 duplicates."""
        conn.execute("CREATE TABLE lz_empty (run_pk BIGINT, file_id VARCHAR)")

        checker = DataQualityChecker(conn)
        result = checker.check_uniqueness("lz_empty", ["run_pk", "file_id"], "test-tool")
        assert result.passed is True
        assert result.details["duplicates"] == 0
        assert result.details["total"] == 0
        assert result.details["distinct"] == 0


class TestQualityReportMixed:
    """Tests for QualityReport with both warnings and errors simultaneously."""

    def test_warnings_and_errors_together(self):
        """A report can have both warnings and errors; passed should be False."""
        checks = (
            CheckResult("check_a", CheckLevel.L1, True, CheckSeverity.INFO, "ok"),
            CheckResult("check_b", CheckLevel.L2, False, CheckSeverity.WARNING, "warn msg"),
            CheckResult("check_c", CheckLevel.L2, False, CheckSeverity.ERROR, "error msg"),
        )
        report = QualityReport("mixed-tool", checks, QualityScore(0.5, 0.5, 0.5, 1.0))
        assert report.passed is False
        assert len(report.warnings) == 1
        assert len(report.errors) == 1
        assert report.warnings[0].check_name == "check_b"
        assert report.errors[0].check_name == "check_c"

    def test_multiple_warnings_no_errors_passes(self):
        """Multiple warnings but no errors should still pass."""
        checks = (
            CheckResult("w1", CheckLevel.L2, False, CheckSeverity.WARNING, "warn 1"),
            CheckResult("w2", CheckLevel.L2, False, CheckSeverity.WARNING, "warn 2"),
        )
        report = QualityReport("tool", checks, QualityScore(0.5, 0.5, 0.5, 1.0))
        assert report.passed is True
        assert len(report.warnings) == 2
        assert len(report.errors) == 0
