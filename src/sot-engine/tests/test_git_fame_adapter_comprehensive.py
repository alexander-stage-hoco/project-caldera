from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import GitFameAdapter
from persistence.repositories import GitFameRepository, LayoutRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _load_git_fame_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "git_fame_output.json"
    return json.loads(fixture_path.read_text())


class TestGitFameAdapter:
    """Comprehensive tests for the git-fame adapter (no layout dependency, 2 tables)."""

    def test_persist_summary_and_authors(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()

        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        summary_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_fame_summary WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert summary_count == 1

        author_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_fame_authors WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert author_count == 2

        conn.close()

    def test_summary_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT repo_id, author_count, total_loc, hhi_index, bus_factor,
                      top_author_pct, top_two_pct
               FROM lz_git_fame_summary WHERE run_pk = ?""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == 2
        assert row[2] == 1000
        assert abs(row[3] - 0.52) < 0.01
        assert row[4] == 2
        assert abs(row[5] - 60.0) < 0.01
        assert abs(row[6] - 100.0) < 0.01

        conn.close()

    def test_author_field_aliasing(self, tmp_path: Path) -> None:
        """Test that author→name and loc→surviving_loc aliasing works."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT author_name, author_email, surviving_loc, ownership_pct,
                      insertions_total, deletions_total, commit_count, files_touched
               FROM lz_git_fame_authors WHERE run_pk = ? AND author_name = 'Alice Developer'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == "alice@example.com"
        assert row[2] == 600   # loc → surviving_loc
        assert abs(row[3] - 60.0) < 0.01
        assert row[4] == 800   # insertions → insertions_total
        assert row[5] == 200   # deletions → deletions_total
        assert row[6] == 45    # commits → commit_count
        assert row[7] == 25    # files → files_touched

        conn.close()

    def test_skips_schema_validation(self, tmp_path: Path) -> None:
        """Test that schema validation is skipped (overridden to no-op)."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        # Should not raise even if schema file doesn't match
        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    def test_rejects_invalid_hhi_index(self, tmp_path: Path) -> None:
        """Test that hhi_index outside [0, 1] is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        payload["data"]["summary"]["hhi_index"] = 1.5

        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_bus_factor_exceeds_author_count(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        payload["data"]["summary"]["bus_factor"] = 10
        payload["data"]["summary"]["author_count"] = 2

        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_ownership_not_summing_to_100(self, tmp_path: Path) -> None:
        """Test that ownership_pct values not summing to ~100% are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        payload["data"]["authors"][0]["ownership_pct"] = 30.0
        payload["data"]["authors"][1]["ownership_pct"] = 30.0

        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_negative_metrics(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        payload["data"]["authors"][0]["loc"] = -100

        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_empty_authors(self, tmp_path: Path) -> None:
        """Test that empty authors list still persists summary."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_git_fame_fixture()
        payload["data"]["authors"] = []
        payload["data"]["summary"]["author_count"] = 0
        payload["data"]["summary"]["bus_factor"] = 0
        payload["data"]["summary"]["total_loc"] = 0
        payload["data"]["summary"]["hhi_index"] = 0.0
        payload["data"]["summary"]["top_author_pct"] = 0.0
        payload["data"]["summary"]["top_two_pct"] = 0.0

        run_repo = ToolRunRepository(conn)
        git_fame_repo = GitFameRepository(conn)

        adapter = GitFameAdapter(run_repo, None, git_fame_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        summary_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_fame_summary WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert summary_count == 1

        author_count = conn.execute(
            "SELECT COUNT(*) FROM lz_git_fame_authors WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert author_count == 0

        conn.close()
