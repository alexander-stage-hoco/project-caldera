from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutAdapter, GitleaksAdapter
from persistence.repositories import GitleaksRepository, LayoutRepository, ToolRunRepository


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


def _load_gitleaks_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "gitleaks_output.json"
    return json.loads(fixture_path.read_text())


class TestGitleaksAdapter:
    """Comprehensive tests for the Gitleaks adapter."""

    def test_persist_secrets(self, tmp_path: Path) -> None:
        """Test basic insertion of gitleaks secrets."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_gitleaks_secrets WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2  # 2 findings in fixture

        conn.close()

    def test_field_correctness(self, tmp_path: Path) -> None:
        """Test that secret fields are correctly mapped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, rule_id, secret_type, severity, line_number,
                      commit_author, in_current_head, entropy
               FROM lz_gitleaks_secrets WHERE run_pk = ? AND rule_id = 'github-pat'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == ".env"
        assert row[1] == "github-pat"
        assert row[2] == "github-pat"
        assert row[3] == "HIGH"
        assert row[4] == 3
        assert row[5] == "Test User"
        assert row[6] is True
        assert abs(row[7] - 0.6689956) < 0.001

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        """Test that persist raises when layout run is missing."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_gitleaks_fixture()

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_skips_files_not_in_layout(self, tmp_path: Path) -> None:
        """Test that secrets in files not in layout are skipped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Add a finding in a file not in layout
        payload["data"]["findings"].append({
            "file_path": "nonexistent/secret.yml",
            "line_number": 1, "rule_id": "test-rule",
            "secret_type": "test", "severity": "HIGH",
            "fingerprint": "abc123", "in_current_head": True,
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_gitleaks_secrets WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2  # Only original 2, not the one in missing file

        conn.close()

    def test_rejects_invalid_line_number(self, tmp_path: Path) -> None:
        """Test that line_number < 1 is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["findings"][0]["line_number"] = 0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_null_optional_fields(self, tmp_path: Path) -> None:
        """Test that null optional fields (entropy, commit_date) are handled."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        del payload["data"]["findings"][0]["entropy"]
        del payload["data"]["findings"][0]["commit_date"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT entropy, commit_date FROM lz_gitleaks_secrets WHERE run_pk = ? AND rule_id = 'github-pat'",
            [run_pk],
        ).fetchone()
        assert row[0] is None
        assert row[1] is None

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        """Test that secrets join with layout files via file_id."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT g.relative_path, lf.relative_path
            FROM lz_gitleaks_secrets g
            JOIN lz_tool_runs tr ON tr.run_pk = g.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = g.file_id
            WHERE g.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 2
        paths = {r[0] for r in joined}
        assert ".env" in paths
        assert "config/api.py" in paths

        conn.close()

    def test_deduplicates_secrets(self, tmp_path: Path) -> None:
        """Test compound dedup key (file_id, rule_id, line_number, fingerprint)."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Duplicate the first finding
        payload["data"]["findings"].append(deepcopy(payload["data"]["findings"][0]))

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        count = conn.execute(
            "SELECT COUNT(*) FROM lz_gitleaks_secrets WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert count == 2  # Duplicate should be skipped

        conn.close()

    def test_rejects_missing_rule_id(self, tmp_path: Path) -> None:
        """Test that missing rule_id is rejected by quality validation."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_gitleaks_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        del payload["data"]["findings"][0]["rule_id"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        gitleaks_repo = GitleaksRepository(conn)

        adapter = GitleaksAdapter(run_repo, layout_repo, gitleaks_repo, Path("/tmp/test-repo"), None)

        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()
