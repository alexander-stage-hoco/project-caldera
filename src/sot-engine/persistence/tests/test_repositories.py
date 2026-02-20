"""Tests for persistence/repositories.py — repository edge cases and lifecycle."""
from __future__ import annotations

from datetime import datetime, timezone

import duckdb
import pytest

from persistence.entities import (
    CollectionRun,
    LayoutDirectory,
    LayoutFile,
    SccFileMetric,
    ToolRun,
)
from persistence.repositories import (
    BaseRepository,
    CollectionRunRepository,
    LayoutRepository,
    SccRepository,
    ToolRunRepository,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_collection_run(crid: str = "run-1", **overrides) -> CollectionRun:
    defaults = dict(
        collection_run_id=crid,
        repo_id="repo-1",
        run_id=crid,
        branch="main",
        commit="a" * 40,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        status="running",
    )
    defaults.update(overrides)
    return CollectionRun(**defaults)


def _make_tool_run(crid: str = "run-1", tool: str = "scc", **overrides) -> ToolRun:
    defaults = dict(
        collection_run_id=crid,
        repo_id="repo-1",
        run_id=crid,
        tool_name=tool,
        tool_version="1.0.0",
        schema_version="1.0.0",
        branch="main",
        commit="a" * 40,
        timestamp=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return ToolRun(**defaults)


# ── CollectionRunRepository ─────────────────────────────────────────────────

class TestCollectionRunRepository:
    def test_insert_and_get_round_trip(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = CollectionRunRepository(duckdb_conn)
        run = _make_collection_run()
        repo.insert(run)
        fetched = repo.get_by_repo_commit("repo-1", "a" * 40)
        assert fetched is not None
        assert fetched.collection_run_id == "run-1"
        assert fetched.status == "running"

    def test_get_nonexistent_returns_none(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = CollectionRunRepository(duckdb_conn)
        result = repo.get_by_repo_commit("no-repo", "b" * 40)
        assert result is None

    def test_mark_status_updates(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = CollectionRunRepository(duckdb_conn)
        run = _make_collection_run()
        repo.insert(run)
        now = datetime.now(timezone.utc)
        repo.mark_status("run-1", "completed", now)
        fetched = repo.get_by_repo_commit("repo-1", "a" * 40)
        assert fetched is not None
        assert fetched.status == "completed"
        assert fetched.completed_at is not None

    def test_reset_run(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = CollectionRunRepository(duckdb_conn)
        run = _make_collection_run()
        repo.insert(run)
        repo.mark_status("run-1", "completed", datetime.now(timezone.utc))
        new_start = datetime(2026, 2, 1, 0, 0, 0)
        repo.reset_run("run-1", new_start)
        fetched = repo.get_by_repo_commit("repo-1", "a" * 40)
        assert fetched is not None
        assert fetched.status == "running"
        assert fetched.completed_at is None

    def test_delete_collection_data_cascade(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        cr_repo = CollectionRunRepository(duckdb_conn)
        tr_repo = ToolRunRepository(duckdb_conn)
        layout_repo = LayoutRepository(duckdb_conn)

        cr_repo.insert(_make_collection_run())
        run_pk = tr_repo.insert(_make_tool_run(tool="layout"))
        layout_repo.insert_files([
            LayoutFile(
                run_pk=run_pk, file_id="f1", relative_path="src/main.py",
                directory_id="d1", filename="main.py", extension=".py",
                language=None, category=None, size_bytes=100,
                line_count=10, is_binary=False,
            )
        ])

        # Verify data exists
        count = duckdb_conn.execute(
            "SELECT COUNT(*) FROM lz_layout_files WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 1

        # Delete
        cr_repo.delete_collection_data("run-1")

        # Verify cascade
        count = duckdb_conn.execute(
            "SELECT COUNT(*) FROM lz_layout_files WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 0
        count = duckdb_conn.execute(
            "SELECT COUNT(*) FROM lz_tool_runs WHERE collection_run_id = ?", ["run-1"]
        ).fetchone()[0]
        assert count == 0

    def test_delete_collection_data_no_tool_runs(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        cr_repo = CollectionRunRepository(duckdb_conn)
        cr_repo.insert(_make_collection_run())
        # Should not raise even with no tool runs to delete
        cr_repo.delete_collection_data("run-1")

    def test_mark_status_to_failed(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = CollectionRunRepository(duckdb_conn)
        repo.insert(_make_collection_run())
        repo.mark_status("run-1", "failed", datetime.now(timezone.utc))
        fetched = repo.get_by_repo_commit("repo-1", "a" * 40)
        assert fetched is not None
        assert fetched.status == "failed"

    def test_insert_duplicate_raises(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = CollectionRunRepository(duckdb_conn)
        repo.insert(_make_collection_run())
        with pytest.raises(Exception):
            repo.insert(_make_collection_run())


# ── ToolRunRepository ──────────────────────────────────────────────────────

class TestToolRunRepository:
    def test_insert_returns_positive_pk(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = ToolRunRepository(duckdb_conn)
        pk = repo.insert(_make_tool_run())
        assert pk > 0

    def test_get_run_pk_success(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = ToolRunRepository(duckdb_conn)
        expected_pk = repo.insert(_make_tool_run())
        actual = repo.get_run_pk("run-1", "scc")
        assert actual == expected_pk

    def test_get_run_pk_not_found(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = ToolRunRepository(duckdb_conn)
        with pytest.raises(KeyError, match="tool run not found"):
            repo.get_run_pk("no-run", "scc")

    def test_get_run_pk_any_multi_name(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = ToolRunRepository(duckdb_conn)
        pk = repo.insert(_make_tool_run(tool="layout"))
        # Should find by first matching name
        actual = repo.get_run_pk_any("run-1", ["nonexistent", "layout"])
        assert actual == pk

    def test_get_run_pk_any_not_found(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = ToolRunRepository(duckdb_conn)
        with pytest.raises(KeyError, match="tool run not found"):
            repo.get_run_pk_any("run-1", ["nope", "also-nope"])


# ── LayoutRepository ───────────────────────────────────────────────────────

class TestLayoutRepository:
    def _seed_run(self, duckdb_conn: duckdb.DuckDBPyConnection) -> int:
        tr = ToolRunRepository(duckdb_conn)
        return tr.insert(_make_tool_run(tool="layout"))

    def test_insert_files_and_get_record(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        run_pk = self._seed_run(duckdb_conn)
        repo = LayoutRepository(duckdb_conn)
        repo.insert_files([
            LayoutFile(
                run_pk=run_pk, file_id="f1", relative_path="src/main.py",
                directory_id="d1", filename="main.py", extension=".py",
                language="Python", category="source", size_bytes=500,
                line_count=50, is_binary=False,
            ),
        ])
        file_id, dir_id = repo.get_file_record(run_pk, "src/main.py")
        assert file_id == "f1"
        assert dir_id == "d1"

    def test_get_file_record_missing(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        run_pk = self._seed_run(duckdb_conn)
        repo = LayoutRepository(duckdb_conn)
        with pytest.raises(KeyError, match="layout file not found"):
            repo.get_file_record(run_pk, "nonexistent.py")

    def test_insert_directories_with_null_parent(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        run_pk = self._seed_run(duckdb_conn)
        repo = LayoutRepository(duckdb_conn)
        repo.insert_directories([
            LayoutDirectory(
                run_pk=run_pk, directory_id="d-root",
                relative_path="src", parent_id=None, depth=1,
                file_count=5, total_size_bytes=2048,
            ),
        ])
        row = duckdb_conn.execute(
            "SELECT parent_id FROM lz_layout_directories WHERE directory_id = ?",
            ["d-root"],
        ).fetchone()
        assert row is not None
        assert row[0] is None

    def test_empty_inserts(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        run_pk = self._seed_run(duckdb_conn)
        repo = LayoutRepository(duckdb_conn)
        # Should not raise
        repo.insert_files([])
        repo.insert_directories([])

    def test_multiple_files(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        run_pk = self._seed_run(duckdb_conn)
        repo = LayoutRepository(duckdb_conn)
        files = [
            LayoutFile(
                run_pk=run_pk, file_id=f"f{i}", relative_path=f"src/file{i}.py",
                directory_id="d1", filename=f"file{i}.py", extension=".py",
                language="Python", category="source", size_bytes=100,
                line_count=10, is_binary=False,
            )
            for i in range(5)
        ]
        repo.insert_files(files)
        count = duckdb_conn.execute(
            "SELECT COUNT(*) FROM lz_layout_files WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 5


# ── SccRepository (representative) ─────────────────────────────────────────

class TestSccRepository:
    def _seed(self, duckdb_conn: duckdb.DuckDBPyConnection) -> int:
        tr = ToolRunRepository(duckdb_conn)
        return tr.insert(_make_tool_run(tool="scc"))

    def test_insert_and_verify(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        run_pk = self._seed(duckdb_conn)
        repo = SccRepository(duckdb_conn)
        repo.insert_file_metrics([
            SccFileMetric(
                run_pk=run_pk, file_id="f1", directory_id="d1",
                relative_path="src/main.py", filename="main.py",
                extension=".py", language="Python", lines_total=100,
                code_lines=80, comment_lines=10, blank_lines=10,
                bytes=2048, complexity=5, uloc=70,
                comment_ratio=0.1, blank_ratio=0.1, code_ratio=0.8,
                complexity_density=0.05, dryness=0.9, bytes_per_loc=20.48,
                is_minified=False, is_generated=False, is_binary=False,
                classification="source",
            ),
        ])
        rows = duckdb_conn.execute(
            "SELECT relative_path, lines_total FROM lz_scc_file_metrics WHERE run_pk = ?",
            [run_pk],
        ).fetchall()
        assert rows == [("src/main.py", 100)]

    def test_none_optional_fields(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        run_pk = self._seed(duckdb_conn)
        repo = SccRepository(duckdb_conn)
        repo.insert_file_metrics([
            SccFileMetric(
                run_pk=run_pk, file_id="f2", directory_id="d1",
                relative_path="src/empty.py", filename=None,
                extension=None, language=None, lines_total=None,
                code_lines=None, comment_lines=None, blank_lines=None,
                bytes=None, complexity=None, uloc=None,
                comment_ratio=None, blank_ratio=None, code_ratio=None,
                complexity_density=None, dryness=None, bytes_per_loc=None,
                is_minified=None, is_generated=None, is_binary=None,
                classification=None,
            ),
        ])
        row = duckdb_conn.execute(
            "SELECT lines_total FROM lz_scc_file_metrics WHERE file_id = 'f2'"
        ).fetchone()
        assert row is not None
        assert row[0] is None

    def test_empty_list(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = SccRepository(duckdb_conn)
        # Should not raise
        repo.insert_file_metrics([])


# ── BaseRepository._insert_bulk ────────────────────────────────────────────

class TestBaseRepositoryInsertBulk:
    def test_empty_iterable(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        repo = BaseRepository(duckdb_conn)
        # Should not raise or execute SQL
        repo._insert_bulk("lz_layout_files", ("run_pk",), [], lambda x: (x,))

    def test_single_entity(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        tr = ToolRunRepository(duckdb_conn)
        run_pk = tr.insert(_make_tool_run(tool="layout"))
        repo = BaseRepository(duckdb_conn)
        repo._insert_bulk(
            "lz_layout_files",
            ("run_pk", "file_id", "relative_path", "directory_id", "filename"),
            [{"run_pk": run_pk, "file_id": "f-test", "relative_path": "a.py", "directory_id": "d1", "filename": "a.py"}],
            lambda d: (d["run_pk"], d["file_id"], d["relative_path"], d["directory_id"], d["filename"]),
        )
        count = duckdb_conn.execute(
            "SELECT COUNT(*) FROM lz_layout_files WHERE file_id = 'f-test'"
        ).fetchone()[0]
        assert count == 1

    def test_multiple_entities(self, duckdb_conn: duckdb.DuckDBPyConnection) -> None:
        tr = ToolRunRepository(duckdb_conn)
        run_pk = tr.insert(_make_tool_run(tool="layout"))
        repo = BaseRepository(duckdb_conn)
        items = [
            {"run_pk": run_pk, "file_id": f"f-{i}", "relative_path": f"file{i}.py", "directory_id": "d1", "filename": f"file{i}.py"}
            for i in range(3)
        ]
        repo._insert_bulk(
            "lz_layout_files",
            ("run_pk", "file_id", "relative_path", "directory_id", "filename"),
            items,
            lambda d: (d["run_pk"], d["file_id"], d["relative_path"], d["directory_id"], d["filename"]),
        )
        count = duckdb_conn.execute(
            "SELECT COUNT(*) FROM lz_layout_files WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 3
