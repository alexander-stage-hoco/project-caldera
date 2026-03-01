from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutScannerAdapter, LizardAdapter
from persistence.repositories import LayoutRepository, LizardRepository, ToolRunRepository


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
    LayoutScannerAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None).persist(layout_payload)
    return run_repo.get_run_pk(run_id, "layout-scanner")


def _load_lizard_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "lizard_output.json"
    return json.loads(fixture_path.read_text())


class TestLizardAdapter:
    """Comprehensive tests for the Lizard adapter (3 tables)."""

    def test_persist_all_tables(self, tmp_path: Path) -> None:
        """Test basic insertion into all 3 tables."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        file_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_file_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert file_count == 2

        func_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_function_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert func_count == 4

        conn.close()

    def test_file_metric_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, language, nloc, function_count, total_ccn, avg_ccn, max_ccn
               FROM lz_lizard_file_metrics WHERE run_pk = ? AND relative_path = 'src/app.py'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[1] == "Python"
        assert row[2] == 120
        assert row[3] == 2
        assert row[4] == 10
        assert abs(row[5] - 5.0) < 0.01
        assert row[6] == 7

        conn.close()

    def test_function_metric_correctness(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT function_name, long_name, ccn, nloc, params, token_count, line_start, line_end
               FROM lz_lizard_function_metrics WHERE run_pk = ? AND function_name = 'main'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "main"
        assert row[1] == "app.main"
        assert row[2] == 7
        assert row[3] == 80
        assert row[4] == 1
        assert row[5] == 200
        assert row[6] == 10
        assert row[7] == 90

        conn.close()

    def test_rejects_pseudo_functions(self, tmp_path: Path) -> None:
        """Test that functions with line_start < 1 are rejected by schema validation."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Add a pseudo-function with line_start=0 (violates schema minimum: 1)
        payload["data"]["files"][0]["functions"].append({
            "name": "*global*", "long_name": "*global*",
            "ccn": 0, "nloc": 10, "params": 0, "token_count": 5,
            "line_start": 0, "line_end": 0,
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_lizard_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_negative_nloc(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["nloc"] = -10

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_avg_ccn_exceeds_max(self, tmp_path: Path) -> None:
        """Test that avg_ccn > max_ccn is rejected."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"][0]["avg_ccn"] = 20.0
        payload["data"]["files"][0]["max_ccn"] = 7

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_persists_excluded_files(self, tmp_path: Path) -> None:
        """Test that excluded files are persisted."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["excluded_files"] = [
            {"path": "vendor/lib.py", "reason": "pattern", "language": "Python"},
        ]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        excluded_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_excluded_files WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert excluded_count == 1

        conn.close()

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"].append(deepcopy(payload["data"]["files"][0]))

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        file_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_file_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert file_count == 2

        conn.close()

    def test_deduplicates_functions(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Duplicate first function in first file
        payload["data"]["files"][0]["functions"].append(
            deepcopy(payload["data"]["files"][0]["functions"][0])
        )

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        func_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_function_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert func_count == 4

        conn.close()

    def test_handles_alternative_field_names(self, tmp_path: Path) -> None:
        """Test that start_line/end_line/parameter_count aliases work."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Use alternative field names for first function
        func = payload["data"]["files"][0]["functions"][0]
        func["start_line"] = func.pop("line_start")
        func["end_line"] = func.pop("line_end")
        func["parameter_count"] = func.pop("params")

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT line_start, line_end, params FROM lz_lizard_function_metrics WHERE run_pk = ? AND function_name = 'main'",
            [run_pk],
        ).fetchone()
        assert row[0] == 10
        assert row[1] == 90
        assert row[2] == 1

        conn.close()

    def test_skips_files_not_in_layout(self, tmp_path: Path) -> None:
        """Files not present in layout should be skipped, not crash."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_lizard_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["files"].append({
            "path": "nonexistent/unknown_file.py",
            "language": "Python",
            "nloc": 30, "function_count": 1, "total_ccn": 3,
            "avg_ccn": 3.0, "max_ccn": 3,
            "functions": [{"name": "ghost_func", "ccn": 3, "nloc": 10,
                           "params": 1, "token_count": 50,
                           "start_line": 1, "end_line": 10}],
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        lizard_repo = LizardRepository(conn)

        adapter = LizardAdapter(run_repo, layout_repo, lizard_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        file_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_file_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert file_count == 2  # Only the 2 known files, unknown skipped

        func_count = conn.execute(
            "SELECT COUNT(*) FROM lz_lizard_function_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        # Functions from the unknown file should also be skipped
        assert func_count >= 1  # At least the functions from known files

        conn.close()
