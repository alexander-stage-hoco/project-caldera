from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutScannerAdapter
from persistence.repositories import LayoutRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _load_layout_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    return json.loads(fixture_path.read_text())


class TestLayoutScannerAdapterFingerprint:
    """Tests for stable_fingerprint mapping through the layout adapter."""

    def test_content_hash_maps_to_stable_fingerprint(self, tmp_path: Path) -> None:
        """content_hash from JSON maps to stable_fingerprint in the database."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_layout_fixture()
        # Add content_hash to a file entry
        test_hash = "a" * 64
        files = payload["data"]["files"]
        first_key = next(iter(files))
        files[first_key]["content_hash"] = test_hash

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        adapter = LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None)
        adapter.persist(payload)

        row = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files WHERE relative_path = ?",
            [first_key],
        ).fetchone()
        assert row is not None
        assert row[0] == test_hash

    def test_missing_content_hash_maps_to_null(self, tmp_path: Path) -> None:
        """Missing content_hash maps to NULL stable_fingerprint."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_layout_fixture()
        # Ensure no content_hash on any file
        for entry in payload["data"]["files"].values():
            entry.pop("content_hash", None)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        adapter = LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None)
        adapter.persist(payload)

        rows = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files"
        ).fetchall()
        assert len(rows) > 0
        for row in rows:
            assert row[0] is None

    def test_multiple_files_different_fingerprints(self, tmp_path: Path) -> None:
        """Two files with distinct hashes are each persisted correctly."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_layout_fixture()
        files = payload["data"]["files"]
        keys = list(files.keys())
        hash_a = "a" * 64
        hash_b = "b" * 64
        files[keys[0]]["content_hash"] = hash_a
        files[keys[1]]["content_hash"] = hash_b

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        adapter = LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None)
        adapter.persist(payload)

        row_a = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files WHERE relative_path = ?",
            [keys[0]],
        ).fetchone()
        row_b = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files WHERE relative_path = ?",
            [keys[1]],
        ).fetchone()
        assert row_a[0] == hash_a
        assert row_b[0] == hash_b

    def test_mixed_fingerprint_and_null(self, tmp_path: Path) -> None:
        """File 1 has hash, file 2 doesn't → file 1 populated, file 2 NULL."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_layout_fixture()
        files = payload["data"]["files"]
        keys = list(files.keys())
        test_hash = "c" * 64
        files[keys[0]]["content_hash"] = test_hash
        files[keys[1]].pop("content_hash", None)

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        adapter = LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None)
        adapter.persist(payload)

        row_a = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files WHERE relative_path = ?",
            [keys[0]],
        ).fetchone()
        row_b = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files WHERE relative_path = ?",
            [keys[1]],
        ).fetchone()
        assert row_a[0] == test_hash
        assert row_b[0] is None

    def test_fingerprint_round_trip_exact(self, tmp_path: Path) -> None:
        """Set a specific hash, persist, SELECT back → exact match."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_layout_fixture()
        exact_hash = "deadbeef" * 8  # 64 chars
        files = payload["data"]["files"]
        first_key = next(iter(files))
        files[first_key]["content_hash"] = exact_hash

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        adapter = LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None)
        adapter.persist(payload)

        row = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files WHERE relative_path = ?",
            [first_key],
        ).fetchone()
        assert row[0] == exact_hash

    def test_fingerprint_column_exists_in_table(self, tmp_path: Path) -> None:
        """PRAGMA table_info shows stable_fingerprint as VARCHAR."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        cols = conn.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'lz_layout_files' AND column_name = 'stable_fingerprint'"
        ).fetchone()
        assert cols is not None
        assert cols[0] == "stable_fingerprint"
        assert cols[1] == "VARCHAR"

    def test_all_files_fingerprinted(self, tmp_path: Path) -> None:
        """When every file has content_hash, all rows have non-NULL fingerprint."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_layout_fixture()
        for i, entry in enumerate(payload["data"]["files"].values()):
            entry["content_hash"] = f"{i:064x}"

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        adapter = LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None)
        adapter.persist(payload)

        total = conn.execute("SELECT COUNT(*) FROM lz_layout_files").fetchone()[0]
        non_null = conn.execute(
            "SELECT COUNT(*) FROM lz_layout_files WHERE stable_fingerprint IS NOT NULL"
        ).fetchone()[0]
        assert total > 0
        assert non_null == total

    def test_migration_adds_column_to_existing_table(self, tmp_path: Path) -> None:
        """Migration adds stable_fingerprint column to pre-existing table."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))

        # Create table WITHOUT stable_fingerprint (simulating old schema)
        conn.execute("""
            CREATE SEQUENCE lz_run_pk_seq START 1;
            CREATE TABLE lz_tool_runs (
                run_pk BIGINT DEFAULT nextval('lz_run_pk_seq'),
                collection_run_id VARCHAR NOT NULL,
                repo_id VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                tool_name VARCHAR NOT NULL,
                tool_version VARCHAR NOT NULL,
                schema_version VARCHAR NOT NULL,
                branch VARCHAR NOT NULL,
                commit VARCHAR NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_pk),
                UNIQUE (collection_run_id, tool_name)
            );
            CREATE TABLE lz_collection_runs (
                collection_run_id VARCHAR NOT NULL,
                repo_id VARCHAR NOT NULL,
                run_id VARCHAR NOT NULL,
                branch VARCHAR NOT NULL,
                commit VARCHAR NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                status VARCHAR NOT NULL,
                PRIMARY KEY (collection_run_id),
                UNIQUE (repo_id, commit)
            );
            CREATE TABLE lz_layout_files (
                run_pk BIGINT NOT NULL,
                file_id VARCHAR NOT NULL,
                relative_path VARCHAR NOT NULL,
                directory_id VARCHAR NOT NULL,
                filename VARCHAR NOT NULL,
                extension VARCHAR,
                language VARCHAR,
                category VARCHAR,
                size_bytes BIGINT,
                line_count INTEGER,
                is_binary BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_pk, file_id)
            );
            CREATE TABLE lz_layout_directories (
                run_pk BIGINT NOT NULL,
                directory_id VARCHAR NOT NULL,
                relative_path VARCHAR NOT NULL,
                parent_id VARCHAR,
                depth INTEGER NOT NULL,
                file_count INTEGER,
                total_size_bytes BIGINT,
                PRIMARY KEY (run_pk, directory_id)
            );
        """)

        payload = _load_layout_fixture()
        test_hash = "b" * 64
        files = payload["data"]["files"]
        first_key = next(iter(files))
        files[first_key]["content_hash"] = test_hash

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        adapter = LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None)
        adapter.persist(payload)

        row = conn.execute(
            "SELECT stable_fingerprint FROM lz_layout_files WHERE relative_path = ?",
            [first_key],
        ).fetchone()
        assert row is not None
        assert row[0] == test_hash
