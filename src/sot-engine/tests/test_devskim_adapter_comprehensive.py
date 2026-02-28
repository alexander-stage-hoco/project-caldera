from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutScannerAdapter, DevskimAdapter
from persistence.repositories import DevskimRepository, LayoutRepository, ToolRunRepository


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


def _load_devskim_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "devskim_output.json"
    return json.loads(fixture_path.read_text())


class TestDevskimAdapter:
    """Comprehensive tests for the DevSkim adapter."""

    def test_persist_findings(self, tmp_path: Path) -> None:
        """Test basic insertion of devskim findings."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_devskim_findings WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3  # 3 issues across 2 files (third file has 0 issues)

        conn.close()

    def test_field_correctness(self, tmp_path: Path) -> None:
        """Test that finding fields are correctly mapped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, rule_id, dd_category, severity, line_start, message
               FROM lz_devskim_findings
               WHERE run_pk = ? AND relative_path = 'src/crypto.cs' AND line_start = 15""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "src/crypto.cs"
        assert row[1] == "DS126858"
        assert row[2] == "insecure_crypto"
        assert row[3] == "HIGH"
        assert row[4] == 15
        assert "MD5" in row[5]

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        """Test that persist raises when layout run is missing."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_devskim_fixture()

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_skips_files_not_in_layout(self, tmp_path: Path) -> None:
        """Test that findings in files not in layout are skipped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Add a file not in layout
        payload["data"]["files"].append({
            "path": "nonexistent/file.cs", "language": "csharp",
            "lines": 10, "issue_count": 1, "issue_density": 10.0,
            "by_category": {"insecure_crypto": 1}, "by_severity": {"LOW": 1},
            "issues": [{"rule_id": "DS999", "dd_category": "insecure_crypto", "severity": "LOW", "line_start": 1, "line_end": 1, "message": "Test issue"}],
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_devskim_findings WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3  # Only the original 3 findings

        conn.close()

    def test_rejects_invalid_line_range(self, tmp_path: Path) -> None:
        """Test that invalid line ranges (end < start) are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["issues"][0]["line_start"] = 20
        payload["data"]["files"][0]["issues"][0]["line_end"] = 10

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_rule_id(self, tmp_path: Path) -> None:
        """Test that missing rule_id is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        del payload["data"]["files"][0]["issues"][0]["rule_id"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_file_with_no_issues(self, tmp_path: Path) -> None:
        """Test that files with zero issues produce no findings."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Keep only the file with no issues
        payload["data"]["files"] = [payload["data"]["files"][2]]  # src/safe.cs

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_devskim_findings WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 0

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        """Test that findings join with layout files via file_id."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT d.relative_path, lf.relative_path
            FROM lz_devskim_findings d
            JOIN lz_tool_runs tr ON tr.run_pk = d.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = d.file_id
            WHERE d.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 3

        conn.close()

    def test_deduplicates_findings(self, tmp_path: Path) -> None:
        """Test dedup key (file_id, rule_id, line_start)."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_devskim_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Duplicate an issue in the first file
        payload["data"]["files"][0]["issues"].append(
            deepcopy(payload["data"]["files"][0]["issues"][0])
        )

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        devskim_repo = DevskimRepository(conn)

        adapter = DevskimAdapter(run_repo, layout_repo, devskim_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_devskim_findings WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3  # Duplicate should be skipped

        conn.close()
