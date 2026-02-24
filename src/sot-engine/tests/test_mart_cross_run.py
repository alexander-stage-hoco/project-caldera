"""Cross-run mart tests for mart_file_identity_map and mart_directory_trend_signals.

These tests verify the complex multi-CTE SQL logic for file lifecycle
classification (unchanged, modified, moved, new, deleted, unknown) and
directory trend detection (growing, stable, shrinking, new_directory, deleted).

Requires dbt binary; skipped otherwise.  Marked ``@pytest.mark.slow``.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _pipeline_helpers import (
    DBT_PROJECT_DIR,
    SCHEMA_PATH,
    find_dbt_binary,
    write_dbt_profile,
)
from orchestrator import OrchestratorLogger, run_dbt


# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------
REPO_ID = "test-repo"
COMMIT_1 = "a" * 40
COMMIT_2 = "b" * 40
COMMIT_3 = "c" * 40
RUN_ID_1 = "run-1"
RUN_ID_2 = "run-2"
RUN_ID_3 = "run-3"


def _insert_collection_run(
    conn: duckdb.DuckDBPyConnection,
    collection_run_id: str,
    repo_id: str,
    commit: str,
    started_at: str,
    status: str = "completed",
) -> None:
    conn.execute(
        """
        INSERT INTO lz_collection_runs
            (collection_run_id, repo_id, run_id, branch, commit, started_at, status)
        VALUES (?, ?, ?, 'main', ?, ?, ?)
        """,
        [collection_run_id, repo_id, collection_run_id, commit, started_at, status],
    )


def _insert_tool_run(
    conn: duckdb.DuckDBPyConnection,
    collection_run_id: str,
    repo_id: str,
    commit: str,
) -> int:
    """Insert a layout tool run and return its run_pk."""
    conn.execute(
        """
        INSERT INTO lz_tool_runs
            (collection_run_id, repo_id, run_id, tool_name, tool_version,
             schema_version, branch, commit, timestamp)
        VALUES (?, ?, ?, 'layout', '1.0.0', '1.0.0', 'main', ?, CURRENT_TIMESTAMP)
        """,
        [collection_run_id, repo_id, collection_run_id, commit],
    )
    return conn.execute("SELECT MAX(run_pk) FROM lz_tool_runs").fetchone()[0]


def _insert_file(
    conn: duckdb.DuckDBPyConnection,
    run_pk: int,
    file_id: str,
    relative_path: str,
    stable_fingerprint: str | None,
    size_bytes: int,
) -> None:
    conn.execute(
        """
        INSERT INTO lz_layout_files
            (run_pk, file_id, relative_path, directory_id, filename,
             extension, language, category, size_bytes, line_count,
             is_binary, stable_fingerprint)
        VALUES (?, ?, ?, 'd-xxx', ?, '.py', 'Python', 'source', ?, 10, false, ?)
        """,
        [run_pk, file_id, relative_path, relative_path.split("/")[-1],
         size_bytes, stable_fingerprint],
    )


def _insert_directory(
    conn: duckdb.DuckDBPyConnection,
    run_pk: int,
    directory_id: str,
    relative_path: str,
    depth: int,
    file_count: int,
    total_size_bytes: int,
) -> None:
    conn.execute(
        """
        INSERT INTO lz_layout_directories
            (run_pk, directory_id, relative_path, parent_id, depth,
             file_count, total_size_bytes)
        VALUES (?, ?, ?, NULL, ?, ?, ?)
        """,
        [run_pk, directory_id, relative_path, depth, file_count, total_size_bytes],
    )


def _setup_two_run_db(tmp_path: Path) -> Path:
    """Create a DuckDB with two consecutive runs and run dbt."""
    dbt_bin = find_dbt_binary()
    if dbt_bin is None:
        pytest.skip("dbt binary not available")

    db_path = tmp_path / "cross_run.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute(SCHEMA_PATH.read_text())

    # -- Run 1 --
    _insert_collection_run(conn, RUN_ID_1, REPO_ID, COMMIT_1, "2026-01-01 00:00:00")
    pk1 = _insert_tool_run(conn, RUN_ID_1, REPO_ID, COMMIT_1)

    # Files: app.py (unchanged), main.py (will be modified), old_name.py (will be moved),
    #        removed.py (will be deleted), no_hash.py (null fingerprint)
    _insert_file(conn, pk1, "f-001", "src/app.py", "a" * 64, 100)
    _insert_file(conn, pk1, "f-002", "src/main.py", "b" * 64, 200)
    _insert_file(conn, pk1, "f-003", "src/old_name.py", "d" * 64, 150)
    _insert_file(conn, pk1, "f-004", "src/removed.py", "f" * 64, 80)
    _insert_file(conn, pk1, "f-005", "src/no_hash.py", None, 50)

    # Directories
    _insert_directory(conn, pk1, "d-root", ".", 0, 5, 580)
    _insert_directory(conn, pk1, "d-src", "src", 1, 5, 580)
    _insert_directory(conn, pk1, "d-docs", "docs", 1, 3, 300)

    # -- Run 2 --
    _insert_collection_run(conn, RUN_ID_2, REPO_ID, COMMIT_2, "2026-01-02 00:00:00")
    pk2 = _insert_tool_run(conn, RUN_ID_2, REPO_ID, COMMIT_2)

    # app.py: same fingerprint → unchanged
    _insert_file(conn, pk2, "f-101", "src/app.py", "a" * 64, 100)
    # main.py: different fingerprint → modified
    _insert_file(conn, pk2, "f-102", "src/main.py", "c" * 64, 250)
    # new_name.py: same fingerprint as old_name.py → moved
    _insert_file(conn, pk2, "f-103", "src/new_name.py", "d" * 64, 150)
    # brand_new.py: new fingerprint, never seen → new
    _insert_file(conn, pk2, "f-104", "src/brand_new.py", "e" * 64, 120)
    # no_hash.py: still null fingerprint → unknown
    _insert_file(conn, pk2, "f-105", "src/no_hash.py", None, 50)
    # removed.py is ABSENT → deleted

    # Directories
    _insert_directory(conn, pk2, "d-root2", ".", 0, 7, 780)   # growing
    _insert_directory(conn, pk2, "d-src2", "src", 1, 5, 670)   # stable (same count)
    _insert_directory(conn, pk2, "d-tests", "tests", 1, 2, 100)  # new_directory
    # docs is ABSENT → deleted

    conn.close()

    # Run dbt
    profiles_dir = write_dbt_profile(tmp_path, db_path)
    logger = OrchestratorLogger(tmp_path / "dbt.log")
    try:
        run_dbt(
            dbt_bin=dbt_bin,
            dbt_project_dir=DBT_PROJECT_DIR,
            profiles_dir=profiles_dir,
            logger=logger,
            target_path=str(tmp_path / "dbt_target"),
            log_path=str(tmp_path / "dbt_logs"),
        )
    finally:
        logger.close()

    return db_path


# ===========================================================================
# Session-scoped fixture: two-run database
# ===========================================================================
@pytest.fixture(scope="session")
def cross_run_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    base = tmp_path_factory.mktemp("cross_run")
    return _setup_two_run_db(base)


@pytest.fixture()
def db(cross_run_db: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(cross_run_db), read_only=True)
    yield conn
    conn.close()


# ===========================================================================
# TestFileIdentityMap
# ===========================================================================
@pytest.mark.slow
class TestFileIdentityMap:
    """Tests for mart_file_identity_map lifecycle classification."""

    def test_mart_has_rows(self, db: duckdb.DuckDBPyConnection) -> None:
        count = db.execute("SELECT COUNT(*) FROM mart_file_identity_map").fetchone()[0]
        assert count > 0

    def test_unchanged_file(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT lifecycle_status FROM mart_file_identity_map "
            "WHERE relative_path = 'src/app.py'"
        ).fetchone()
        assert row is not None
        assert row[0] == "unchanged"

    def test_modified_file(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT lifecycle_status FROM mart_file_identity_map "
            "WHERE relative_path = 'src/main.py'"
        ).fetchone()
        assert row is not None
        assert row[0] == "modified"

    def test_moved_file(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT lifecycle_status, prev_path FROM mart_file_identity_map "
            "WHERE relative_path = 'src/new_name.py'"
        ).fetchone()
        assert row is not None
        assert row[0] == "moved"
        assert row[1] == "src/old_name.py"

    def test_new_file(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT lifecycle_status, prev_path FROM mart_file_identity_map "
            "WHERE relative_path = 'src/brand_new.py'"
        ).fetchone()
        assert row is not None
        assert row[0] == "new"
        assert row[1] is None

    def test_deleted_file(self, db: duckdb.DuckDBPyConnection) -> None:
        rows = db.execute(
            "SELECT relative_path FROM mart_file_identity_map "
            "WHERE lifecycle_status = 'deleted'"
        ).fetchall()
        deleted_paths = {r[0] for r in rows}
        assert "src/removed.py" in deleted_paths

    def test_null_fingerprint(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT lifecycle_status FROM mart_file_identity_map "
            "WHERE relative_path = 'src/no_hash.py'"
        ).fetchone()
        assert row is not None
        assert row[0] == "unknown"

    def test_all_statuses_present(self, db: duckdb.DuckDBPyConnection) -> None:
        rows = db.execute(
            "SELECT DISTINCT lifecycle_status FROM mart_file_identity_map"
        ).fetchall()
        statuses = {r[0] for r in rows}
        expected = {"unchanged", "modified", "moved", "new", "deleted", "unknown"}
        assert statuses == expected

    def test_repo_id_correct(self, db: duckdb.DuckDBPyConnection) -> None:
        rows = db.execute(
            "SELECT DISTINCT repo_id FROM mart_file_identity_map"
        ).fetchall()
        repo_ids = {r[0] for r in rows}
        assert repo_ids == {REPO_ID}

    def test_collection_run_is_current(self, db: duckdb.DuckDBPyConnection) -> None:
        rows = db.execute(
            "SELECT DISTINCT collection_run_id FROM mart_file_identity_map"
        ).fetchall()
        run_ids = {r[0] for r in rows}
        assert run_ids == {RUN_ID_2}

    def test_moved_prev_path_differs(self, db: duckdb.DuckDBPyConnection) -> None:
        rows = db.execute(
            "SELECT relative_path, prev_path FROM mart_file_identity_map "
            "WHERE lifecycle_status = 'moved'"
        ).fetchall()
        assert len(rows) > 0
        for row in rows:
            assert row[0] != row[1], "moved file prev_path should differ from relative_path"

    def test_no_duplicate_entries(self, db: duckdb.DuckDBPyConnection) -> None:
        dupes = db.execute(
            """
            SELECT collection_run_id, file_id, COUNT(*) as cnt
            FROM mart_file_identity_map
            WHERE file_id IS NOT NULL
            GROUP BY collection_run_id, file_id
            HAVING COUNT(*) > 1
            """
        ).fetchall()
        assert len(dupes) == 0, f"Duplicate entries found: {dupes}"


# ===========================================================================
# TestDirectoryTrendSignals
# ===========================================================================
@pytest.mark.slow
class TestDirectoryTrendSignals:
    """Tests for mart_directory_trend_signals trend classification."""

    def test_mart_has_rows(self, db: duckdb.DuckDBPyConnection) -> None:
        count = db.execute(
            "SELECT COUNT(*) FROM mart_directory_trend_signals"
        ).fetchone()[0]
        assert count > 0

    def test_growing_directory(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT structure_trend, file_count_delta FROM mart_directory_trend_signals "
            "WHERE relative_path = '.'"
        ).fetchone()
        assert row is not None
        assert row[0] == "growing"
        assert row[1] > 0

    def test_stable_directory(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT structure_trend, file_count_delta FROM mart_directory_trend_signals "
            "WHERE relative_path = 'src'"
        ).fetchone()
        assert row is not None
        assert row[0] == "stable"
        assert row[1] == 0

    def test_new_directory(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT structure_trend, prev_file_count FROM mart_directory_trend_signals "
            "WHERE relative_path = 'tests'"
        ).fetchone()
        assert row is not None
        assert row[0] == "new_directory"
        assert row[1] is None

    def test_deleted_directory(self, db: duckdb.DuckDBPyConnection) -> None:
        row = db.execute(
            "SELECT structure_trend, current_file_count FROM mart_directory_trend_signals "
            "WHERE relative_path = 'docs'"
        ).fetchone()
        assert row is not None
        assert row[0] == "deleted"
        assert row[1] is None

    def test_all_trends_present(self, db: duckdb.DuckDBPyConnection) -> None:
        rows = db.execute(
            "SELECT DISTINCT structure_trend FROM mart_directory_trend_signals"
        ).fetchall()
        trends = {r[0] for r in rows}
        expected = {"growing", "stable", "new_directory", "deleted"}
        assert trends == expected

    def test_deleted_has_negative_delta(self, db: duckdb.DuckDBPyConnection) -> None:
        rows = db.execute(
            "SELECT file_count_delta FROM mart_directory_trend_signals "
            "WHERE structure_trend = 'deleted'"
        ).fetchall()
        assert len(rows) > 0
        for row in rows:
            assert row[0] < 0

    def test_size_delta_computed(self, db: duckdb.DuckDBPyConnection) -> None:
        """Growing directory size_delta = current_size - prev_size."""
        row = db.execute(
            "SELECT current_size, prev_size, size_delta FROM mart_directory_trend_signals "
            "WHERE relative_path = '.'"
        ).fetchone()
        assert row is not None
        assert row[2] == row[0] - row[1]


# ===========================================================================
# TestCrossRunEdgeCases
# ===========================================================================
@pytest.mark.slow
class TestCrossRunEdgeCases:
    """Edge cases: single run, failed runs, multi-repo isolation."""

    @pytest.fixture()
    def single_run_db(self, tmp_path: Path) -> duckdb.DuckDBPyConnection:
        """Database with only one completed collection run."""
        dbt_bin = find_dbt_binary()
        if dbt_bin is None:
            pytest.skip("dbt binary not available")

        db_path = tmp_path / "single_run.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute(SCHEMA_PATH.read_text())

        _insert_collection_run(conn, "only-run", REPO_ID, COMMIT_1, "2026-01-01 00:00:00")
        pk = _insert_tool_run(conn, "only-run", REPO_ID, COMMIT_1)
        _insert_file(conn, pk, "f-001", "src/app.py", "a" * 64, 100)
        _insert_directory(conn, pk, "d-root", ".", 0, 1, 100)
        conn.close()

        profiles_dir = write_dbt_profile(tmp_path, db_path)
        logger = OrchestratorLogger(tmp_path / "dbt.log")
        try:
            run_dbt(
                dbt_bin=dbt_bin,
                dbt_project_dir=DBT_PROJECT_DIR,
                profiles_dir=profiles_dir,
                logger=logger,
                target_path=str(tmp_path / "dbt_target"),
                log_path=str(tmp_path / "dbt_logs"),
            )
        finally:
            logger.close()

        conn = duckdb.connect(str(db_path), read_only=True)
        yield conn
        conn.close()

    def test_single_run_identity_map_empty(
        self, single_run_db: duckdb.DuckDBPyConnection
    ) -> None:
        count = single_run_db.execute(
            "SELECT COUNT(*) FROM mart_file_identity_map"
        ).fetchone()[0]
        assert count == 0

    def test_single_run_trends_empty(
        self, single_run_db: duckdb.DuckDBPyConnection
    ) -> None:
        count = single_run_db.execute(
            "SELECT COUNT(*) FROM mart_directory_trend_signals"
        ).fetchone()[0]
        assert count == 0

    @pytest.fixture()
    def failed_run_db(self, tmp_path: Path) -> duckdb.DuckDBPyConnection:
        """Run 1 completed, run 2 failed, run 3 completed → compare 3 vs 1."""
        dbt_bin = find_dbt_binary()
        if dbt_bin is None:
            pytest.skip("dbt binary not available")

        db_path = tmp_path / "failed_run.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute(SCHEMA_PATH.read_text())

        # Run 1: completed
        _insert_collection_run(conn, RUN_ID_1, REPO_ID, COMMIT_1, "2026-01-01 00:00:00")
        pk1 = _insert_tool_run(conn, RUN_ID_1, REPO_ID, COMMIT_1)
        _insert_file(conn, pk1, "f-001", "src/app.py", "a" * 64, 100)
        _insert_directory(conn, pk1, "d-root", ".", 0, 1, 100)

        # Run 2: failed (should be skipped by mart)
        _insert_collection_run(conn, RUN_ID_2, REPO_ID, COMMIT_2, "2026-01-02 00:00:00", status="failed")
        pk2 = _insert_tool_run(conn, RUN_ID_2, REPO_ID, COMMIT_2)
        _insert_file(conn, pk2, "f-101", "src/app.py", "x" * 64, 999)
        _insert_directory(conn, pk2, "d-root2", ".", 0, 1, 999)

        # Run 3: completed — should compare against run 1
        _insert_collection_run(conn, RUN_ID_3, REPO_ID, COMMIT_3, "2026-01-03 00:00:00")
        pk3 = _insert_tool_run(conn, RUN_ID_3, REPO_ID, COMMIT_3)
        _insert_file(conn, pk3, "f-201", "src/app.py", "a" * 64, 100)  # unchanged vs run 1
        _insert_directory(conn, pk3, "d-root3", ".", 0, 1, 100)
        conn.close()

        profiles_dir = write_dbt_profile(tmp_path, db_path)
        logger = OrchestratorLogger(tmp_path / "dbt.log")
        try:
            run_dbt(
                dbt_bin=dbt_bin,
                dbt_project_dir=DBT_PROJECT_DIR,
                profiles_dir=profiles_dir,
                logger=logger,
                target_path=str(tmp_path / "dbt_target"),
                log_path=str(tmp_path / "dbt_logs"),
            )
        finally:
            logger.close()

        conn = duckdb.connect(str(db_path), read_only=True)
        yield conn
        conn.close()

    def test_failed_run_skipped(
        self, failed_run_db: duckdb.DuckDBPyConnection
    ) -> None:
        """Mart should compare run 3 vs run 1 (skipping failed run 2)."""
        row = failed_run_db.execute(
            "SELECT lifecycle_status FROM mart_file_identity_map "
            "WHERE relative_path = 'src/app.py'"
        ).fetchone()
        assert row is not None
        # app.py has same fingerprint in run 1 and run 3 → unchanged
        assert row[0] == "unchanged"

    @pytest.fixture()
    def multi_repo_db(self, tmp_path: Path) -> duckdb.DuckDBPyConnection:
        """Two repos with overlapping paths → each isolated."""
        dbt_bin = find_dbt_binary()
        if dbt_bin is None:
            pytest.skip("dbt binary not available")

        db_path = tmp_path / "multi_repo.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute(SCHEMA_PATH.read_text())

        for repo_id, fp_suffix in [("repo-alpha", "a"), ("repo-beta", "b")]:
            commit_a = fp_suffix * 40
            commit_b = chr(ord(fp_suffix) + 2) * 40  # 'c' or 'd'

            _insert_collection_run(conn, f"{repo_id}-run1", repo_id, commit_a, "2026-01-01 00:00:00")
            pk1 = _insert_tool_run(conn, f"{repo_id}-run1", repo_id, commit_a)
            _insert_file(conn, pk1, f"{repo_id}-f1", "src/app.py", fp_suffix * 64, 100)

            _insert_collection_run(conn, f"{repo_id}-run2", repo_id, commit_b, "2026-01-02 00:00:00")
            pk2 = _insert_tool_run(conn, f"{repo_id}-run2", repo_id, commit_b)
            # Different fingerprint → modified within each repo
            _insert_file(conn, pk2, f"{repo_id}-f2", "src/app.py", (fp_suffix + "1") * 32, 100)

        conn.close()

        profiles_dir = write_dbt_profile(tmp_path, db_path)
        logger = OrchestratorLogger(tmp_path / "dbt.log")
        try:
            run_dbt(
                dbt_bin=dbt_bin,
                dbt_project_dir=DBT_PROJECT_DIR,
                profiles_dir=profiles_dir,
                logger=logger,
                target_path=str(tmp_path / "dbt_target"),
                log_path=str(tmp_path / "dbt_logs"),
            )
        finally:
            logger.close()

        conn = duckdb.connect(str(db_path), read_only=True)
        yield conn
        conn.close()

    def test_different_repos_isolated(
        self, multi_repo_db: duckdb.DuckDBPyConnection
    ) -> None:
        """Each repo's files compared only within that repo."""
        rows = multi_repo_db.execute(
            "SELECT repo_id, lifecycle_status FROM mart_file_identity_map "
            "WHERE relative_path = 'src/app.py'"
        ).fetchall()
        repo_statuses = {r[0]: r[1] for r in rows}
        # Both repos should show modified (different fingerprint between runs)
        assert repo_statuses.get("repo-alpha") == "modified"
        assert repo_statuses.get("repo-beta") == "modified"
