"""Tests for DataQualityChecker.persist_report() method."""
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


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """
    Load and execute the SQL schema used by tests into the provided DuckDB connection.
    
    Parameters:
    	conn (duckdb.DuckDBPyConnection): Open DuckDB connection on which the persistence/schema.sql file will be executed.
    """
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


COLLECTION_RUN_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


@pytest.mark.unit
class TestQualityPersist:
    """Tests for persisting quality reports to lz_quality_checks."""

    def test_persist_report_writes_rows(self, tmp_path: Path) -> None:
        """persist_report inserts one row per check."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)

        checks = [
            CheckResult(
                check_name="metadata_completeness",
                level=CheckLevel.L1,
                passed=True,
                severity=CheckSeverity.INFO,
                message="scc: all metadata fields present",
            ),
            CheckResult(
                check_name="fk_integrity",
                level=CheckLevel.L2,
                passed=False,
                severity=CheckSeverity.WARNING,
                message="scc: 2 orphan file_id reference(s)",
            ),
        ]
        score = QualityScore(completeness=1.0, validity=1.0, consistency=0.5, timeliness=1.0)
        report = QualityReport(tool_name="scc", checks=tuple(checks), score=score)

        checker = DataQualityChecker(conn)
        checker.persist_report(report, COLLECTION_RUN_ID)

        rows = conn.execute(
            "SELECT tool_name, check_name, level, passed, severity, message, overall_score "
            "FROM lz_quality_checks WHERE collection_run_id = ? ORDER BY check_name",
            [COLLECTION_RUN_ID],
        ).fetchall()

        assert len(rows) == 2
        # fk_integrity row
        assert rows[0][0] == "scc"
        assert rows[0][1] == "fk_integrity"
        assert rows[0][2] == "L2"
        assert rows[0][3] is False
        assert rows[0][4] == "warning"
        assert rows[0][6] == pytest.approx(score.overall, abs=0.001)
        # metadata_completeness row
        assert rows[1][3] is True

        conn.close()

    def test_persist_report_is_idempotent(self, tmp_path: Path) -> None:
        """Re-persisting the same report replaces previous rows."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)

        score = QualityScore(completeness=1.0, validity=1.0, consistency=1.0, timeliness=1.0)
        report = QualityReport(
            tool_name="lizard",
            checks=(
                CheckResult(
                    check_name="uniqueness",
                    level=CheckLevel.L2,
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message="lizard: unique",
                ),
            ),
            score=score,
        )

        checker = DataQualityChecker(conn)
        checker.persist_report(report, COLLECTION_RUN_ID)
        checker.persist_report(report, COLLECTION_RUN_ID)

        count = conn.execute(
            "SELECT count(*) FROM lz_quality_checks WHERE collection_run_id = ? AND tool_name = 'lizard'",
            [COLLECTION_RUN_ID],
        ).fetchone()[0]

        assert count == 1
        conn.close()

    def test_persist_report_empty_checks(self, tmp_path: Path) -> None:
        """Persisting a report with no checks is a no-op."""
        conn = duckdb.connect(str(tmp_path / "test.duckdb"))
        _load_schema(conn)

        score = QualityScore(completeness=1.0, validity=1.0, consistency=1.0, timeliness=1.0)
        report = QualityReport(tool_name="trivy", checks=(), score=score)

        checker = DataQualityChecker(conn)
        checker.persist_report(report, COLLECTION_RUN_ID)

        count = conn.execute(
            "SELECT count(*) FROM lz_quality_checks WHERE collection_run_id = ?",
            [COLLECTION_RUN_ID],
        ).fetchone()[0]

        assert count == 0
        conn.close()
