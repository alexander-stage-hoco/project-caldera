from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutScannerAdapter, ScancodeAdapter
from persistence.repositories import LayoutRepository, ScancodeRepository, ToolRunRepository


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


def _load_scancode_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "scancode_output.json"
    return json.loads(fixture_path.read_text())


class TestScancodeAdapter:
    """Comprehensive tests for the Scancode adapter (2 tables)."""

    def test_persist_licenses_and_summary(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        license_count = conn.execute(
            "SELECT COUNT(*) FROM lz_scancode_file_licenses WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert license_count == 2

        summary_count = conn.execute(
            "SELECT COUNT(*) FROM lz_scancode_summary WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert summary_count == 1  # Singleton per run

        conn.close()

    def test_license_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, spdx_id, category, confidence, match_type, line_number
               FROM lz_scancode_file_licenses WHERE run_pk = ? AND spdx_id = 'MIT'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "LICENSE"
        assert row[2] == "permissive"
        assert abs(row[3] - 0.95) < 0.01
        assert row[4] == "file"
        assert row[5] == 1

        conn.close()

    def test_summary_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT total_files_scanned, files_with_licenses, overall_risk,
                      has_permissive, has_weak_copyleft, has_copyleft, has_unknown
               FROM lz_scancode_summary WHERE run_pk = ?""",
            [run_pk],
        ).fetchone()

        assert row[0] == 3
        assert row[1] == 2
        assert row[2] == "low"
        assert row[3] is True
        assert row[4] is False
        assert row[5] is False
        assert row[6] is False

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_scancode_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
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

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["findings"].append({
            "file_path": "nonexistent/file.py", "spdx_id": "GPL-3.0",
            "category": "copyleft", "confidence": 0.99, "match_type": "file",
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_scancode_file_licenses WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2

        conn.close()

    def test_rejects_invalid_confidence(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["findings"][0]["confidence"] = 1.5

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_invalid_line_number(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["findings"][0]["line_number"] = 0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_spdx_id(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        del payload["data"]["findings"][0]["spdx_id"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_deduplicates_licenses(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["findings"].append(deepcopy(payload["data"]["findings"][0]))

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_scancode_file_licenses WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scancode_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scancode_repo = ScancodeRepository(conn)

        adapter = ScancodeAdapter(run_repo, layout_repo, scancode_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT sc.relative_path, lf.relative_path
            FROM lz_scancode_file_licenses sc
            JOIN lz_tool_runs tr ON tr.run_pk = sc.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = sc.file_id
            WHERE sc.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 2

        conn.close()
