from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutAdapter, CoverageAdapter
from persistence.repositories import CoverageRepository, LayoutRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _create_layout_run(conn: duckdb.DuckDBPyConnection, run_id: str, repo_id: str) -> int:
    layout_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    layout_payload = json.loads(layout_fixture.read_text())
    layout_payload["metadata"]["repo_id"] = repo_id
    layout_payload["metadata"]["run_id"] = run_id

    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    LayoutAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None).persist(layout_payload)
    return run_repo.get_run_pk(run_id, "layout-scanner")


def _load_coverage_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "coverage_output.json"
    return json.loads(fixture_path.read_text())


class TestCoverageAdapter:
    """Comprehensive tests for the Coverage adapter."""

    def test_persist_summaries(self, tmp_path: Path) -> None:
        """Test basic insertion of coverage summaries."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_coverage_summary WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2  # 2 files in fixture

        conn.close()

    def test_field_correctness(self, tmp_path: Path) -> None:
        """Test that coverage fields are correctly mapped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, line_coverage_pct, branch_coverage_pct,
                      lines_total, lines_covered, lines_missed,
                      branches_total, branches_covered, source_format
               FROM lz_coverage_summary WHERE run_pk = ? AND relative_path = 'src/main.py'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "src/main.py"
        assert row[1] == 80.0
        assert row[2] is None  # branch_coverage_pct is null
        assert row[3] == 10
        assert row[4] == 8
        assert row[5] == 2
        assert row[6] is None  # branches_total is null
        assert row[7] is None  # branches_covered is null
        assert row[8] == "lcov"

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        """Test that persist raises when layout run is missing."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_coverage_fixture()

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_skips_files_not_in_layout(self, tmp_path: Path) -> None:
        """Test that files not in layout are skipped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"].append({
            "relative_path": "nonexistent/file.py",
            "lines_total": 10, "lines_covered": 5, "lines_missed": 5,
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_coverage_summary WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2  # Only original 2

        conn.close()

    def test_rejects_lines_missed_invariant(self, tmp_path: Path) -> None:
        """Test that lines_missed != total - covered is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Break the invariant: missed should be 2 but we set it to 5
        payload["data"]["files"][0]["lines_missed"] = 5

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_covered_exceeds_total(self, tmp_path: Path) -> None:
        """Test that lines_covered > lines_total is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["lines_covered"] = 20
        payload["data"]["files"][0]["lines_total"] = 10
        payload["data"]["files"][0]["lines_missed"] = -10

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_invalid_coverage_pct(self, tmp_path: Path) -> None:
        """Test that coverage percentage outside 0-100 is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["line_coverage_pct"] = 150.0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_null_branch_coverage(self, tmp_path: Path) -> None:
        """Test that null branch coverage fields are handled."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        # First file has null branch coverage
        row = conn.execute(
            "SELECT branches_total, branches_covered FROM lz_coverage_summary WHERE run_pk = ? AND relative_path = 'src/main.py'",
            [run_pk],
        ).fetchone()
        assert row[0] is None
        assert row[1] is None

        conn.close()

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        """Test that duplicate files are deduplicated."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"].append(deepcopy(payload["data"]["files"][0]))

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_coverage_summary WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        """Test that coverage summaries join with layout files."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_coverage_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        coverage_repo = CoverageRepository(conn)

        adapter = CoverageAdapter(run_repo, layout_repo, coverage_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT c.relative_path, lf.relative_path
            FROM lz_coverage_summary c
            JOIN lz_tool_runs tr ON tr.run_pk = c.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = c.file_id
            WHERE c.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 2

        conn.close()
