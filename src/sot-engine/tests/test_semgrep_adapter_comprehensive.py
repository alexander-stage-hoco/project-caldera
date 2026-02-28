from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutScannerAdapter, SemgrepAdapter
from persistence.repositories import LayoutRepository, SemgrepRepository, ToolRunRepository


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
    LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None).persist(layout_payload)
    return run_repo.get_run_pk(run_id, "layout-scanner")


def _load_semgrep_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "semgrep_output.json"
    return json.loads(fixture_path.read_text())


class TestSemgrepAdapter:
    """Comprehensive tests for the Semgrep adapter."""

    def test_persist_smells(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0
        count = conn.execute(
            "SELECT COUNT(*) FROM lz_semgrep_smells WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2

        conn.close()

    def test_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, rule_id, dd_smell_id, dd_category, severity,
                      line_start, line_end, message
               FROM lz_semgrep_smells WHERE run_pk = ? AND relative_path = 'src/app.py'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == "DD-E2-ASYNC-VOID-python"
        assert row[2] == "E2_ASYNC_VOID"
        assert row[3] == "async_concurrency"
        assert row[4] == "HIGH"
        assert row[5] == 10
        assert row[6] == 12

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_semgrep_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_skips_files_not_in_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"].append({
            "path": "nonexistent/file.py", "language": "python", "lines": 10,
            "smell_count": 1,
            "smells": [{"rule_id": "DD-TEST", "severity": "LOW", "line_start": 1, "line_end": 1, "message": "Test smell"}],
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_semgrep_smells WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2

        conn.close()

    def test_rejects_invalid_line_range(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["smells"][0]["line_start"] = 20
        payload["data"]["files"][0]["smells"][0]["line_end"] = 5

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_rule_id(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        del payload["data"]["files"][0]["smells"][0]["rule_id"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_null_optional_fields(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["smells"][0].pop("dd_smell_id", None)
        payload["data"]["files"][0]["smells"][0].pop("code_snippet", None)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT dd_smell_id, code_snippet FROM lz_semgrep_smells WHERE run_pk = ? AND relative_path = 'src/app.py'",
            [run_pk],
        ).fetchone()
        assert row[0] is None
        assert row[1] is None

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT s.relative_path, lf.relative_path
            FROM lz_semgrep_smells s
            JOIN lz_tool_runs tr ON tr.run_pk = s.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = s.file_id
            WHERE s.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 2

        conn.close()

    def test_deduplicates_smells(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_semgrep_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["smells"].append(
            deepcopy(payload["data"]["files"][0]["smells"][0])
        )

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        semgrep_repo = SemgrepRepository(conn)

        adapter = SemgrepAdapter(run_repo, layout_repo, semgrep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_semgrep_smells WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2

        conn.close()
