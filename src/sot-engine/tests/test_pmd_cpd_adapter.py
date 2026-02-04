from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutAdapter, PmdCpdAdapter
from persistence.repositories import LayoutRepository, PmdCpdRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _create_layout_run(conn: duckdb.DuckDBPyConnection, run_id: str, repo_id: str) -> int:
    """Create a layout run for testing with required files.

    The layout fixture includes pmd-cpd test files:
    - src/app.py
    - src/utils/helpers.py
    """
    layout_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    layout_payload = json.loads(layout_fixture.read_text())
    layout_payload["metadata"]["repo_id"] = repo_id
    layout_payload["metadata"]["run_id"] = run_id

    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    LayoutAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None).persist(layout_payload)
    return run_repo.get_run_pk(run_id, "layout-scanner")


def _create_pmd_cpd_fixture_payload(repo_id: str, run_id: str) -> dict:
    """Create a PMD-CPD fixture payload matching the layout fixture files."""
    return {
        "metadata": {
            "tool_name": "pmd-cpd",
            "tool_version": "7.0.0",
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": "main",
            "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "timestamp": "2026-01-25T10:00:00+00:00",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "pmd-cpd",
            "config": {
                "min_tokens": 50,
                "ignore_identifiers": False,
                "ignore_literals": False,
            },
            "elapsed_seconds": 1.5,
            "summary": {
                "total_files": 2,
                "total_clones": 1,
                "duplication_percentage": 20.0,
                "cross_file_clones": 1,
            },
            "files": [
                {
                    "path": "src/app.py",
                    "total_lines": 100,
                    "duplicate_lines": 20,
                    "duplicate_blocks": 1,
                    "duplication_percentage": 20.0,
                    "language": "python",
                },
                {
                    "path": "src/utils/helpers.py",
                    "total_lines": 80,
                    "duplicate_lines": 20,
                    "duplicate_blocks": 1,
                    "duplication_percentage": 25.0,
                    "language": "python",
                },
            ],
            "duplications": [
                {
                    "clone_id": "CPD-0001",
                    "lines": 20,
                    "tokens": 100,
                    "code_fragment": "def process_data(items):\n    results = []\n    for item in items:\n        results.append(item * 2)\n    return results",
                    "occurrences": [
                        {
                            "file": "src/app.py",
                            "line_start": 10,
                            "line_end": 29,
                            "column_start": 1,
                            "column_end": 20,
                        },
                        {
                            "file": "src/utils/helpers.py",
                            "line_start": 5,
                            "line_end": 24,
                            "column_start": 1,
                            "column_end": 20,
                        },
                    ],
                },
            ],
        },
    }


class TestPmdCpdAdapter:
    """Test the PMD-CPD adapter for persisting duplication data."""

    def test_persist_file_metrics(self, tmp_path: Path) -> None:
        """Test persisting PMD-CPD file metrics to database."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        # Create layout run first
        _create_layout_run(conn, run_id, repo_id)

        # Create PMD-CPD payload
        cpd_payload = _create_pmd_cpd_fixture_payload(repo_id, run_id)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        pmd_cpd_repo = PmdCpdRepository(conn)

        adapter = PmdCpdAdapter(
            run_repo,
            layout_repo,
            pmd_cpd_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(cpd_payload)

        assert run_pk > 0

        # Verify file metrics were inserted
        file_count = conn.execute(
            "SELECT COUNT(*) FROM lz_pmd_cpd_file_metrics WHERE run_pk = ?",
            [run_pk],
        ).fetchone()[0]
        assert file_count == 2  # 2 files in fixture

        # Verify duplications were inserted
        dup_count = conn.execute(
            "SELECT COUNT(*) FROM lz_pmd_cpd_duplications WHERE run_pk = ?",
            [run_pk],
        ).fetchone()[0]
        assert dup_count == 1  # 1 duplication in fixture

        # Verify occurrences were inserted
        occ_count = conn.execute(
            "SELECT COUNT(*) FROM lz_pmd_cpd_occurrences WHERE run_pk = ?",
            [run_pk],
        ).fetchone()[0]
        assert occ_count == 2  # 2 occurrences in fixture

        conn.close()

    def test_persist_duplication_details(self, tmp_path: Path) -> None:
        """Test that duplication details are correctly persisted."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        cpd_payload = _create_pmd_cpd_fixture_payload(repo_id, run_id)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        pmd_cpd_repo = PmdCpdRepository(conn)

        adapter = PmdCpdAdapter(
            run_repo,
            layout_repo,
            pmd_cpd_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(cpd_payload)

        # Query duplication details
        dup = conn.execute(
            """
            SELECT clone_id, lines, tokens, occurrence_count, is_cross_file
            FROM lz_pmd_cpd_duplications
            WHERE run_pk = ?
            """,
            [run_pk],
        ).fetchone()

        assert dup is not None
        assert dup[0] == "CPD-0001"  # clone_id
        assert dup[1] == 20  # lines
        assert dup[2] == 100  # tokens
        assert dup[3] == 2  # occurrence_count
        assert dup[4] is True  # is_cross_file (2 different files)

        conn.close()

    def test_validate_quality_invalid_path(self, tmp_path: Path) -> None:
        """Test that paths starting with 'private/' are rejected as invalid.

        Note: Absolute paths like '/absolute/path/file.py' are normalized to
        'absolute/path/file.py' by the path normalization layer. However,
        paths starting with 'private/' (which can result from /private/... macOS paths)
        are explicitly rejected by is_repo_relative_path().
        """
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        cpd_payload = _create_pmd_cpd_fixture_payload(repo_id, run_id)

        # Modify to have a path that starts with 'private/' - this is rejected
        cpd_payload["data"]["files"][0]["path"] = "private/var/file.py"

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        pmd_cpd_repo = PmdCpdRepository(conn)

        adapter = PmdCpdAdapter(
            run_repo,
            layout_repo,
            pmd_cpd_repo,
            Path("/tmp/test-repo"),
            None,
        )

        with pytest.raises(ValueError, match="data quality validation failed"):
            adapter.persist(cpd_payload)

        conn.close()

    def test_validate_quality_invalid_line_range(self, tmp_path: Path) -> None:
        """Test that invalid line ranges in occurrences are rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        cpd_payload = _create_pmd_cpd_fixture_payload(repo_id, run_id)

        # Modify to have invalid line range (end < start)
        cpd_payload["data"]["duplications"][0]["occurrences"][0]["line_start"] = 30
        cpd_payload["data"]["duplications"][0]["occurrences"][0]["line_end"] = 10

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        pmd_cpd_repo = PmdCpdRepository(conn)

        adapter = PmdCpdAdapter(
            run_repo,
            layout_repo,
            pmd_cpd_repo,
            Path("/tmp/test-repo"),
            None,
        )

        with pytest.raises(ValueError, match="data quality validation failed"):
            adapter.persist(cpd_payload)

        conn.close()

    def test_validate_quality_missing_clone_id(self, tmp_path: Path) -> None:
        """Test that missing clone_id is rejected.

        Note: JSON schema validation catches this before data quality validation
        because the schema defines clone_id as a required field with minLength.
        """
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        cpd_payload = _create_pmd_cpd_fixture_payload(repo_id, run_id)

        # Set clone_id to empty string - schema validation catches this
        cpd_payload["data"]["duplications"][0]["clone_id"] = ""

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        pmd_cpd_repo = PmdCpdRepository(conn)

        adapter = PmdCpdAdapter(
            run_repo,
            layout_repo,
            pmd_cpd_repo,
            Path("/tmp/test-repo"),
            None,
        )

        # Schema validation catches empty clone_id (minLength constraint)
        with pytest.raises(ValueError, match="(schema validation failed|data quality validation failed)"):
            adapter.persist(cpd_payload)

        conn.close()

    def test_file_id_linkage(self, tmp_path: Path) -> None:
        """Test that file metrics correctly link to layout files via file_id."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        cpd_payload = _create_pmd_cpd_fixture_payload(repo_id, run_id)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        pmd_cpd_repo = PmdCpdRepository(conn)

        adapter = PmdCpdAdapter(
            run_repo,
            layout_repo,
            pmd_cpd_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(cpd_payload)

        # Verify file metrics can join with layout files
        joined_rows = conn.execute(
            """
            SELECT cm.relative_path, lf.relative_path, cm.duplication_percentage
            FROM lz_pmd_cpd_file_metrics cm
            JOIN lz_tool_runs tr_cpd
              ON tr_cpd.run_pk = cm.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr_cpd.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk
             AND lf.file_id = cm.file_id
            WHERE cm.run_pk = ?
            ORDER BY cm.relative_path
            """,
            [run_pk],
        ).fetchall()

        # Both files should join
        assert len(joined_rows) == 2
        paths = [row[0] for row in joined_rows]
        assert "src/app.py" in paths
        assert "src/utils/helpers.py" in paths

        conn.close()

    def test_occurrence_file_linkage(self, tmp_path: Path) -> None:
        """Test that occurrences correctly link to layout files."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        _create_layout_run(conn, run_id, repo_id)

        cpd_payload = _create_pmd_cpd_fixture_payload(repo_id, run_id)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        pmd_cpd_repo = PmdCpdRepository(conn)

        adapter = PmdCpdAdapter(
            run_repo,
            layout_repo,
            pmd_cpd_repo,
            Path("/tmp/test-repo"),
            None,
        )
        run_pk = adapter.persist(cpd_payload)

        # Verify occurrences can join with layout files
        joined_rows = conn.execute(
            """
            SELECT o.relative_path, lf.relative_path, o.line_start, o.line_end
            FROM lz_pmd_cpd_occurrences o
            JOIN lz_tool_runs tr_cpd
              ON tr_cpd.run_pk = o.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr_cpd.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk
             AND lf.file_id = o.file_id
            WHERE o.run_pk = ?
            ORDER BY o.relative_path, o.line_start
            """,
            [run_pk],
        ).fetchall()

        # Both occurrences should join
        assert len(joined_rows) == 2
        paths = [row[0] for row in joined_rows]
        assert "src/app.py" in paths
        assert "src/utils/helpers.py" in paths

        conn.close()
