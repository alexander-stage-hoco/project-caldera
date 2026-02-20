from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import DependenseeAdapter
from persistence.repositories import DependenseeRepository, LayoutRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _load_dependensee_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "dependensee_output.json"
    return json.loads(fixture_path.read_text())


class TestDependenseeAdapter:
    """Comprehensive tests for the dependensee adapter (no layout, 3 tables)."""

    def test_persist_all_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        project_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dependensee_projects WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert project_count == 2

        proj_ref_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dependensee_project_refs WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert proj_ref_count == 1

        pkg_ref_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dependensee_package_refs WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert pkg_ref_count == 3

        conn.close()

    def test_project_field_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT project_path, project_name, target_framework,
                      project_reference_count, package_reference_count
               FROM lz_dependensee_projects WHERE run_pk = ? AND project_name = 'MyApp'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "src/MyApp/MyApp.csproj"
        assert row[1] == "MyApp"
        assert row[2] == "net8.0"
        assert row[3] == 1   # 1 project reference
        assert row[4] == 2   # 2 package references

        conn.close()

    def test_project_ref_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT source_project_path, target_project_path
               FROM lz_dependensee_project_refs WHERE run_pk = ?""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "src/MyApp/MyApp.csproj"
        assert row[1] == "src/MyApp.Core/MyApp.Core.csproj"

        conn.close()

    def test_package_ref_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT project_path, package_name, package_version
               FROM lz_dependensee_package_refs
               WHERE run_pk = ? AND package_name = 'Serilog'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "src/MyApp/MyApp.csproj"
        assert row[1] == "Serilog"
        assert row[2] == "3.1.1"

        conn.close()

    def test_rejects_mismatched_project_reference_count(self, tmp_path: Path) -> None:
        """Test that stated project_reference_count != actual list length is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        payload["data"]["projects"][0]["project_reference_count"] = 5

        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_mismatched_package_reference_count(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        payload["data"]["projects"][0]["package_reference_count"] = 99

        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_project_name(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        del payload["data"]["projects"][0]["name"]

        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_missing_package_name(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        del payload["data"]["projects"][0]["package_references"][0]["name"]

        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_no_references(self, tmp_path: Path) -> None:
        """Test project with zero project and package references."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        # MyApp.Core already has 0 project refs; clear its package refs too
        payload["data"]["projects"] = [payload["data"]["projects"][1]]
        payload["data"]["projects"][0]["package_references"] = []

        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        project_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dependensee_projects WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert project_count == 1

        ref_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dependensee_project_refs WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert ref_count == 0

        pkg_count = conn.execute(
            "SELECT COUNT(*) FROM lz_dependensee_package_refs WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert pkg_count == 0

        conn.close()

    def test_null_target_framework(self, tmp_path: Path) -> None:
        """Test that null target_framework is handled correctly."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_dependensee_fixture()
        payload["data"]["projects"][0]["target_framework"] = None

        run_repo = ToolRunRepository(conn)
        dep_repo = DependenseeRepository(conn)

        adapter = DependenseeAdapter(run_repo, None, dep_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT target_framework FROM lz_dependensee_projects WHERE run_pk = ? AND project_name = 'MyApp'",
            [run_pk],
        ).fetchone()
        assert row[0] is None

        conn.close()
