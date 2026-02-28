from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutScannerAdapter, SccAdapter
from persistence.repositories import LayoutRepository, SccRepository, ToolRunRepository


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


def _load_scc_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "scc_output.json"
    return json.loads(fixture_path.read_text())


class TestSccAdapter:
    """Comprehensive tests for the SCC adapter."""

    def test_persist_file_metrics(self, tmp_path: Path) -> None:
        """Test basic insertion of scc file metrics."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_scc_file_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2  # 2 files in fixture

        conn.close()

    def test_field_correctness(self, tmp_path: Path) -> None:
        """Test that fields are correctly mapped including coalesced names."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        # First file uses old field names (lines, code, comment, blank)
        row = conn.execute(
            """SELECT relative_path, language, lines_total, code_lines, comment_lines,
                      blank_lines, bytes, complexity, classification
               FROM lz_scc_file_metrics WHERE run_pk = ? AND relative_path = 'src/app.py'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == "Python"
        assert row[2] == 120  # lines_total coalesced from 'lines'
        assert row[3] == 90   # code_lines coalesced from 'code'
        assert row[4] == 20   # comment_lines coalesced from 'comment'
        assert row[5] == 10   # blank_lines coalesced from 'blank'
        assert row[6] == 2048
        assert row[7] == 12
        assert row[8] == "source"

        # Second file uses new field names (lines_total, lines_code, etc.)
        row2 = conn.execute(
            """SELECT lines_total, code_lines, comment_lines, blank_lines
               FROM lz_scc_file_metrics WHERE run_pk = ? AND relative_path = 'src/utils/helpers.py'""",
            [run_pk],
        ).fetchone()

        assert row2[0] == 80   # lines_total
        assert row2[1] == 60   # lines_code
        assert row2[2] == 10   # lines_comment
        assert row2[3] == 10   # lines_blank

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        """Test that persist raises when layout run is missing."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_scc_fixture()

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_skips_files_not_in_layout(self, tmp_path: Path) -> None:
        """Test that files not in layout are skipped (KeyError from get_file_record)."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Add a file that's not in layout
        payload["data"]["files"].append({
            "path": "nonexistent/file.py",
            "filename": "file.py",
            "extension": ".py",
            "language": "Python",
            "lines": 10, "code": 8, "comment": 1, "blank": 1,
            "bytes": 100, "complexity": 1,
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)
        # File not in layout causes KeyError in get_file_record, which propagates
        with pytest.raises(KeyError):
            adapter.persist(payload)

        conn.close()

    def test_rejects_negative_lines(self, tmp_path: Path) -> None:
        """Test that negative line counts are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["lines"] = -5

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_invalid_ratio(self, tmp_path: Path) -> None:
        """Test that ratio values outside [0, 1] are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["comment_ratio"] = 2.5

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_components_exceeding_total(self, tmp_path: Path) -> None:
        """Test that line components exceeding total are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # code + comment + blank > lines
        payload["data"]["files"][0]["lines"] = 10
        payload["data"]["files"][0]["code"] = 90
        payload["data"]["files"][0]["comment"] = 20
        payload["data"]["files"][0]["blank"] = 10

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_null_optional_fields(self, tmp_path: Path) -> None:
        """Test that null optional fields (uloc, dryness, etc.) are handled."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Remove optional fields
        for f in payload["data"]["files"]:
            f.pop("uloc", None)
            f.pop("dryness", None)
            f.pop("complexity_density", None)
            f.pop("bytes_per_loc", None)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT uloc, dryness FROM lz_scc_file_metrics WHERE run_pk = ? LIMIT 1",
            [run_pk],
        ).fetchone()
        assert row[0] is None
        assert row[1] is None

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        """Test that scc metrics join with layout files via file_id."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT s.relative_path, lf.relative_path
            FROM lz_scc_file_metrics s
            JOIN lz_tool_runs tr_scc ON tr_scc.run_pk = s.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr_scc.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = s.file_id
            WHERE s.run_pk = ?
            ORDER BY s.relative_path
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 2
        paths = [r[0] for r in joined]
        assert "src/app.py" in paths
        assert "src/utils/helpers.py" in paths

        conn.close()

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        """Test that duplicate files are deduplicated by file_id."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_scc_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Duplicate the first file
        payload["data"]["files"].append(deepcopy(payload["data"]["files"][0]))

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        scc_repo = SccRepository(conn)

        adapter = SccAdapter(run_repo, layout_repo, scc_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_scc_file_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2  # Duplicate should be skipped

        conn.close()
