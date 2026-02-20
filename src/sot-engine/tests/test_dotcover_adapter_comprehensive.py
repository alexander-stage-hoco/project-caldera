from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutAdapter, DotcoverAdapter
from persistence.repositories import DotcoverRepository, LayoutRepository, ToolRunRepository


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


def _load_dotcover_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "dotcover_output.json"
    return json.loads(fixture_path.read_text())


class TestDotcoverAdapter:
    """Comprehensive tests for the dotcover adapter (3 tables, optional layout)."""

    def test_persist_all_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        asm_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dotcover_assembly_coverage WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert asm_count == 2

        type_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dotcover_type_coverage WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert type_count == 3

        method_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dotcover_method_coverage WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert method_count == 5

        conn.close()

    def test_assembly_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT assembly_name, covered_statements, total_statements, statement_coverage_pct
               FROM lz_dotcover_assembly_coverage
               WHERE run_pk = ? AND assembly_name = 'MyApp.Services'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == 100
        assert row[2] == 120
        assert abs(row[3] - 83.33) < 0.01

        conn.close()

    def test_type_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT assembly_name, namespace, type_name,
                      covered_statements, total_statements, statement_coverage_pct
               FROM lz_dotcover_type_coverage
               WHERE run_pk = ? AND type_name = 'UserService'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "MyApp.Services"
        assert row[1] == "MyApp.Services.Users"
        assert row[2] == "UserService"
        assert row[3] == 60
        assert row[4] == 80
        assert abs(row[5] - 75.0) < 0.01

        conn.close()

    def test_method_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT assembly_name, type_name, method_name,
                      covered_statements, total_statements, statement_coverage_pct
               FROM lz_dotcover_method_coverage
               WHERE run_pk = ? AND method_name = 'GetUser(int)'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "MyApp.Services"
        assert row[1] == "UserService"
        assert row[3] == 20
        assert row[4] == 20
        assert abs(row[5] - 100.0) < 0.01

        conn.close()

    def test_layout_optional_no_error(self, tmp_path: Path) -> None:
        """Test that missing layout doesn't cause an error (layout is optional)."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)
        assert run_pk > 0

        conn.close()

    def test_type_file_id_null_without_layout(self, tmp_path: Path) -> None:
        """Test that file_id is null when layout is not available."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT file_id, directory_id FROM lz_dotcover_type_coverage WHERE run_pk = ? LIMIT 1",
            [run_pk],
        ).fetchone()

        assert row[0] is None
        assert row[1] is None

        conn.close()

    def test_rejects_covered_exceeds_total(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        payload["data"]["assemblies"][0]["covered_statements"] = 200
        payload["data"]["assemblies"][0]["total_statements"] = 100

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_negative_statements(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        payload["data"]["assemblies"][0]["covered_statements"] = -5

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_coverage_pct_out_of_range(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        payload["data"]["types"][0]["statement_coverage_pct"] = 150.0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_assembly_name(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        del payload["data"]["assemblies"][0]["name"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_method_name(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        del payload["data"]["methods"][0]["name"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_empty_collections(self, tmp_path: Path) -> None:
        """Test that empty assemblies/types/methods lists persist without error."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dotcover_fixture()
        payload["data"]["assemblies"] = []
        payload["data"]["types"] = []
        payload["data"]["methods"] = []

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        dotcover_repo = DotcoverRepository(conn)

        adapter = DotcoverAdapter(run_repo, layout_repo, dotcover_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        asm_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dotcover_assembly_coverage WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert asm_count == 0

        type_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dotcover_type_coverage WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert type_count == 0

        method_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dotcover_method_coverage WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert method_count == 0

        conn.close()
