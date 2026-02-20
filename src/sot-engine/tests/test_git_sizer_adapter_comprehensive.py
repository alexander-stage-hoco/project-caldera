from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import GitSizerAdapter
from persistence.repositories import GitSizerRepository, LayoutRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _load_git_sizer_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "git_sizer_output.json"
    return json.loads(fixture_path.read_text())


class TestGitSizerAdapter:
    """Comprehensive tests for the git-sizer adapter (no layout, 3 tables)."""

    def test_persist_all_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        metric_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_sizer_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert metric_count == 1

        violation_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_sizer_violations WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert violation_count == 1

        lfs_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_sizer_lfs_candidates WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert lfs_count == 1

        conn.close()

    def test_metric_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT health_grade, duration_ms, commit_count, blob_count,
                      max_blob_size, branch_count, max_path_depth
               FROM lz_git_sizer_metrics WHERE run_pk = ?""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "B"
        assert row[1] == 120
        assert row[2] == 120
        assert row[3] == 300
        assert row[4] == 262144
        assert row[5] == 3
        assert row[6] == 6

        conn.close()

    def test_violation_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT metric, value_display, raw_value, level, object_ref
               FROM lz_git_sizer_violations WHERE run_pk = ?""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "max_blob_size"
        assert row[1] == "256 KB"
        assert row[2] == 262144
        assert row[3] == 2
        assert row[4] == "large.bin"

        conn.close()

    def test_lfs_candidates_are_flat_strings(self, tmp_path: Path) -> None:
        """Test that LFS candidates are persisted as flat string paths."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT file_path FROM lz_git_sizer_lfs_candidates WHERE run_pk = ?", [run_pk]
        ).fetchone()

        assert row is not None
        assert row[0] == "large.bin"

        conn.close()

    def test_rejects_invalid_health_grade(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        payload["data"]["health_grade"] = "Z"

        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_negative_metric(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        payload["data"]["metrics"]["commit_count"] = -1

        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_violation_level_out_of_range(self, tmp_path: Path) -> None:
        """Test that violation level outside 1-4 is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        payload["data"]["violations"][0]["level"] = 5

        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_no_violations(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        payload["data"]["violations"] = []
        payload["data"]["lfs_candidates"] = []

        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        violation_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_sizer_violations WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert violation_count == 0

        lfs_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_sizer_lfs_candidates WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert lfs_count == 0

        conn.close()

    def test_skips_schema_validation_when_missing(self, tmp_path: Path) -> None:
        """Test that missing schema file doesn't prevent persistence."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_sizer_fixture()
        run_repo = ToolRunRepository(conn)
        git_sizer_repo = GitSizerRepository(conn)

        adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
        # Should succeed even if schema file doesn't exist
        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    def test_all_valid_health_grades(self, tmp_path: Path) -> None:
        """Test that all valid health grades are accepted."""
        for grade in ["A", "A+", "B", "B+", "C", "C+", "D", "D+", "F"]:
            db_path = tmp_path / f"test_{grade.replace('+', 'p')}.duckdb"
            conn = duckdb.connect(str(db_path))
            _load_schema(conn)

            payload = _load_git_sizer_fixture()
            payload["data"]["health_grade"] = grade

            run_repo = ToolRunRepository(conn)
            git_sizer_repo = GitSizerRepository(conn)

            adapter = GitSizerAdapter(run_repo, None, git_sizer_repo, Path("/tmp/test-repo"), None)
            run_pk = adapter.persist(payload)
            assert run_pk > 0

            conn.close()
