from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutAdapter, RoslynAdapter
from persistence.repositories import LayoutRepository, RoslynRepository, ToolRunRepository


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


def _load_roslyn_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "roslyn_output.json"
    return json.loads(fixture_path.read_text())


class TestRoslynAdapter:
    """Comprehensive tests for the Roslyn adapter."""

    def test_persist_violations(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0
        count = conn.execute(
            "SELECT COUNT(*) FROM lz_roslyn_violations WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3

        conn.close()

    def test_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, rule_id, dd_category, severity, message,
                      line_start, line_end, column_start, column_end
               FROM lz_roslyn_violations WHERE run_pk = ? AND rule_id = 'CS0219'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "src/app.py"
        assert row[2] == "dead_code"
        assert row[3] == "HIGH"
        assert row[5] == 15
        assert row[7] == 12
        assert row[8] == 18

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_roslyn_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_skips_external_paths(self, tmp_path: Path) -> None:
        """Test that files with .nuget/node_modules paths are skipped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"].append({
            "path": ".nuget/packages/Foo/Bar.cs", "language": "csharp",
            "lines_of_code": 10, "violation_count": 1,
            "violations": [{"rule_id": "CS0001", "dd_category": "design",
                            "severity": "LOW", "line_start": 1, "line_end": 1,
                            "column_start": 1, "column_end": 5}],
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_roslyn_violations WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3  # External file skipped

        conn.close()

    def test_skips_files_not_in_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"].append({
            "path": "nonexistent/file.cs", "language": "csharp",
            "lines_of_code": 10, "violation_count": 1,
            "violations": [{"rule_id": "CS0001", "dd_category": "design",
                            "severity": "LOW", "line_start": 1, "line_end": 1,
                            "column_start": 1, "column_end": 5}],
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_roslyn_violations WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3

        conn.close()

    def test_rejects_invalid_line_range(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["violations"][0]["line_start"] = 30
        payload["data"]["files"][0]["violations"][0]["line_end"] = 10

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_required_fields(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        del payload["data"]["files"][0]["violations"][0]["rule_id"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_deduplicates_violations(self, tmp_path: Path) -> None:
        """Test dedup by (run_pk, file_id, rule_id, line_start, column_start)."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["violations"].append(
            deepcopy(payload["data"]["files"][0]["violations"][0])
        )

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_roslyn_violations WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_roslyn_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        roslyn_repo = RoslynRepository(conn)

        adapter = RoslynAdapter(run_repo, layout_repo, roslyn_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT r.relative_path, lf.relative_path
            FROM lz_roslyn_violations r
            JOIN lz_tool_runs tr ON tr.run_pk = r.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = r.file_id
            WHERE r.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 3
        paths = {r[0] for r in joined}
        assert "src/app.py" in paths
        assert "src/utils/helpers.py" in paths

        conn.close()
