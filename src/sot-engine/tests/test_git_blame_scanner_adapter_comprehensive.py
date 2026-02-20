from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutAdapter, GitBlameScannerAdapter
from persistence.repositories import GitBlameRepository, LayoutRepository, ToolRunRepository


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


def _load_git_blame_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "git_blame_scanner_output.json"
    return json.loads(fixture_path.read_text())


class TestGitBlameScannerAdapter:
    """Comprehensive tests for the git-blame-scanner adapter (2 tables)."""

    def test_persist_summaries_and_authors(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        file_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_blame_summary WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert file_count == 3

        author_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_blame_author_stats WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert author_count == 2

        conn.close()

    def test_file_summary_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, total_lines, unique_authors, top_author,
                      top_author_lines, top_author_pct, last_modified, churn_30d, churn_90d
               FROM lz_git_blame_summary WHERE run_pk = ? AND relative_path = 'src/main.py'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == 150
        assert row[2] == 1
        assert row[3] == "alice@example.com"
        assert row[4] == 150
        assert abs(row[5] - 100.0) < 0.01
        assert row[6] is not None  # last_modified is a date
        assert row[7] == 3
        assert row[8] == 8

        conn.close()

    def test_author_stats_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT author_email, total_files, total_lines, exclusive_files, avg_ownership_pct
               FROM lz_git_blame_author_stats WHERE run_pk = ? AND author_email = 'alice@example.com'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == 2
        assert row[2] == 310
        assert row[3] == 1
        assert abs(row[4] - 90.0) < 0.01

        conn.close()

    def test_last_modified_unknown_to_null(self, tmp_path: Path) -> None:
        """Test that last_modified='unknown' is converted to NULL."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["last_modified"] = "unknown"

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT last_modified FROM lz_git_blame_summary WHERE run_pk = ? AND relative_path = 'src/main.py'",
            [run_pk],
        ).fetchone()
        assert row[0] is None

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_blame_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_churn_invariant_violation(self, tmp_path: Path) -> None:
        """Test that churn_30d > churn_90d is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["churn_30d"] = 10
        payload["data"]["files"][0]["churn_90d"] = 5

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_unique_authors_zero(self, tmp_path: Path) -> None:
        """Test that unique_authors < 1 is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["unique_authors"] = 0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_exclusive_files_exceeds_total(self, tmp_path: Path) -> None:
        """Test that exclusive_files > total_files is rejected for authors."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["authors"][0]["exclusive_files"] = 10
        payload["data"]["authors"][0]["total_files"] = 2

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_git_blame_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        git_blame_repo = GitBlameRepository(conn)

        adapter = GitBlameScannerAdapter(run_repo, layout_repo, git_blame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT gb.relative_path, lf.relative_path
            FROM lz_git_blame_summary gb
            JOIN lz_tool_runs tr ON tr.run_pk = gb.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = gb.file_id
            WHERE gb.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 3

        conn.close()
