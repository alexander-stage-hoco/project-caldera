from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator import (
    OrchestratorLogger,
    ToolConfig,
    _default_output_path,
    _format_duration,
    _resolve_dbt_cmd,
    ingest_outputs,
    ensure_schema,
    run_dbt,
)
from persistence.adapters import LayoutAdapter
from persistence.repositories import LayoutRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def test_layout_adapter_persists_files(tmp_path: Path) -> None:
    conn = duckdb.connect(":memory:")
    _load_schema(conn)
    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)

    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = LayoutAdapter(run_repo, layout_repo)
    run_pk = adapter.persist(payload)

    rows = conn.execute(
        """
        SELECT file_id, directory_id, relative_path
        FROM lz_layout_files
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    # Fixture includes 14 files for various tool testing scenarios
    assert rows == [
        ("f-000000000006", "d-000000000001", ".env"),
        ("f-000000000005", "d-000000000001", "Dockerfile"),
        ("f-000000000009", "d-000000000001", "LICENSE"),
        ("f-000000000007", "d-000000000004", "config/api.py"),
        ("f-000000000003", "d-000000000001", "package-lock.json"),
        ("f-000000000004", "d-000000000001", "requirements.txt"),
        ("f-000000000001", "d-000000000002", "src/app.py"),
        ("f-000000000012", "d-000000000002", "src/crypto.cs"),
        ("f-000000000011", "d-000000000002", "src/helpers.py"),
        ("f-000000000008", "d-000000000002", "src/main.py"),
        ("f-000000000014", "d-000000000002", "src/safe.cs"),
        ("f-000000000013", "d-000000000002", "src/serializer.cs"),
        ("f-000000000010", "d-000000000002", "src/utils.py"),
        ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
    ]


def test_ingest_outputs_validates_run_id(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)
    (repo_root / "src" / "app.py").write_text("print('hi')\n")

    conn = duckdb.connect(":memory:")
    _load_schema(conn)

    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "scc_output.json"
    payload = json.loads(fixture_path.read_text())
    layout_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    layout_payload = json.loads(layout_fixture.read_text())
    layout_payload["metadata"]["repo_id"] = "22222222-2222-2222-2222-222222222222"
    layout_payload["metadata"]["run_id"] = "11111111-1111-1111-1111-111111111111"
    layout_path = tmp_path / "layout.json"
    layout_path.write_text(json.dumps(layout_payload))

    bad_payload_path = tmp_path / "scc_output.json"
    payload["metadata"]["run_id"] = "99999999-9999-9999-9999-999999999999"
    bad_payload_path.write_text(json.dumps(payload))

    try:
        ingest_outputs(
            conn,
            repo_id="22222222-2222-2222-2222-222222222222",
            collection_run_id="11111111-1111-1111-1111-111111111111",
            run_id="11111111-1111-1111-1111-111111111111",
            branch="main",
            commit="a" * 40,
            repo_path=repo_root,
            layout_output=layout_path,
            scc_output=bad_payload_path,
            lizard_output=None,
            roslyn_output=None,
            semgrep_output=None,
            schema_path=Path(__file__).resolve().parents[1] / "persistence" / "schema.sql",
        )
    except ValueError as exc:
        assert "run_id mismatch" in str(exc)
    else:
        raise AssertionError("Expected run_id mismatch error")


def test_ingest_outputs_writes_expected_rows(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "src" / "utils").mkdir(parents=True)
    (repo_root / "src" / "app.py").write_text("print('hi')\n")
    (repo_root / "src" / "utils" / "helpers.py").write_text("def helper():\n    pass\n")

    conn = duckdb.connect(":memory:")
    _load_schema(conn)

    layout_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    scc_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "scc_output.json"
    lizard_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "lizard_output.json"
    semgrep_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "semgrep_output.json"
    scc_payload = json.loads(scc_fixture.read_text())
    lizard_payload = json.loads(lizard_fixture.read_text())
    semgrep_payload = json.loads(semgrep_fixture.read_text())

    repo_id = "55555555-5555-5555-5555-555555555555"
    run_id = "66666666-6666-6666-6666-666666666666"
    for payload in (scc_payload, lizard_payload, semgrep_payload):
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
    lizard_payload["data"]["run_id"] = run_id
    layout_payload = json.loads(layout_fixture.read_text())
    layout_payload["metadata"]["repo_id"] = repo_id
    layout_payload["metadata"]["run_id"] = run_id

    scc_path = tmp_path / "scc.json"
    lizard_path = tmp_path / "lizard.json"
    semgrep_path = tmp_path / "semgrep.json"
    scc_path.write_text(json.dumps(scc_payload))
    lizard_path.write_text(json.dumps(lizard_payload))
    semgrep_path.write_text(json.dumps(semgrep_payload))
    layout_path = tmp_path / "layout.json"
    layout_path.write_text(json.dumps(layout_payload))

    ingest_outputs(
        conn,
        repo_id=repo_id,
        collection_run_id=run_id,
        run_id=run_id,
        branch="main",
        commit="a" * 40,
        repo_path=repo_root,
        layout_output=layout_path,
        scc_output=scc_path,
        lizard_output=lizard_path,
        roslyn_output=None,
        semgrep_output=semgrep_path,
        schema_path=Path(__file__).resolve().parents[1] / "persistence" / "schema.sql",
    )

    run_count = conn.execute(
        "SELECT count(*) FROM lz_tool_runs WHERE repo_id = ?",
        [repo_id],
    ).fetchone()[0]
    assert run_count == 4  # layout, scc, lizard, semgrep

    scc_rows = conn.execute(
        "SELECT count(*) FROM lz_scc_file_metrics",
    ).fetchone()[0]
    assert scc_rows == 2

    lizard_func_rows = conn.execute(
        "SELECT count(*) FROM lz_lizard_function_metrics",
    ).fetchone()[0]
    assert lizard_func_rows == 4

    semgrep_smell_rows = conn.execute(
        "SELECT count(*) FROM lz_semgrep_smells",
    ).fetchone()[0]
    assert semgrep_smell_rows == 2

    join_rows = conn.execute(
        """
        SELECT fm.relative_path, lf.relative_path
        FROM lz_scc_file_metrics fm
        JOIN lz_tool_runs tr_scc
          ON tr_scc.run_pk = fm.run_pk
        JOIN lz_tool_runs tr_layout
          ON tr_layout.collection_run_id = tr_scc.collection_run_id
         AND tr_layout.tool_name IN ('layout', 'layout-scanner')
        JOIN lz_layout_files lf
          ON lf.run_pk = tr_layout.run_pk
         AND lf.file_id = fm.file_id
        ORDER BY fm.relative_path
        """
    ).fetchall()
    assert join_rows == [
        ("src/app.py", "src/app.py"),
        ("src/utils/helpers.py", "src/utils/helpers.py"),
    ]


def test_ensure_schema_migrates_tool_run_ids() -> None:
    conn = duckdb.connect(":memory:")
    try:
        conn.execute(
            """
            create table lz_tool_runs (
                run_pk bigint,
                repo_id uuid,
                run_id uuid,
                tool_name varchar,
                tool_version varchar,
                schema_version varchar,
                branch varchar,
                commit varchar,
                timestamp timestamp
            )
            """
        )
        schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
        with pytest.raises(RuntimeError, match="lz_collection_runs missing"):
            ensure_schema(conn, schema_path)
    finally:
        conn.close()


def test_default_output_path_is_absolute(tmp_path: Path) -> None:
    tool_root = tmp_path / "tools" / "scc"
    tool = ToolConfig("scc", str(tool_root))
    output_path = _default_output_path(tool, "run-1", None)
    assert output_path.is_absolute()
    assert output_path.as_posix().endswith("/tools/scc/outputs/run-1/output.json")


def test_resolve_dbt_cmd_falls_back(tmp_path: Path) -> None:
    cmd = _resolve_dbt_cmd(Path(".venv/bin/dbt"), tmp_path)
    assert cmd[:3] == [sys.executable, "-m", "dbt.cli.main"]


def test_run_dbt_resolves_relative_paths(monkeypatch, tmp_path: Path) -> None:
    calls = []
    project_dir = tmp_path / "src" / "sot-engine" / "dbt"
    profiles_dir = tmp_path / "src" / "sot-engine" / "dbt"
    project_dir.mkdir(parents=True)

    def fake_run(cmd, cwd, env, check, stdout=None, stderr=None):  # noqa: ANN001
        calls.append((cmd, cwd, env["DBT_PROFILES_DIR"], stdout, stderr))

    monkeypatch.setattr("subprocess.run", fake_run)
    logger = OrchestratorLogger(tmp_path / "orchestrator.log")
    try:
        run_dbt(
            Path(".venv/bin/dbt"),
            Path("src/sot-engine/dbt"),
            Path("src/sot-engine/dbt"),
            logger,
        )
    finally:
        logger.close()
    assert calls
    assert str(calls[0][1]).endswith("src/sot-engine/dbt")
    assert str(calls[0][2]).endswith("src/sot-engine/dbt")


def test_format_duration() -> None:
    assert _format_duration(1.234) == "1.23s"


def test_orchestrator_closes_connection_before_dbt(monkeypatch, tmp_path: Path) -> None:
    closes = {"closed": False}
    dbt_ran = {"value": False}

    class DummyConn:
        def execute(self, *_args, **_kwargs):  # noqa: ANN001
            class DummyResult:
                def fetchone(self):
                    return (1,)

                def fetchall(self):
                    return []

            return DummyResult()

        def close(self):
            closes["closed"] = True

    def fake_connect(_path):  # noqa: ANN001
        return DummyConn()

    def fake_run_dbt(*_args, **_kwargs):  # noqa: ANN001
        dbt_ran["value"] = True
        assert closes["closed"] is True

    monkeypatch.setattr("duckdb.connect", fake_connect)
    monkeypatch.setattr("orchestrator.ingest_outputs", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("orchestrator.run_dbt", fake_run_dbt)
    monkeypatch.setattr("orchestrator.CollectionRunRepository", lambda *_args, **_kwargs: type("X", (), {
        "get_by_repo_commit": lambda *_a, **_k: None,
        "insert": lambda *_a, **_k: None,
        "mark_status": lambda *_a, **_k: None,
        "delete_collection_data": lambda *_a, **_k: None,
        "reset_run": lambda *_a, **_k: None,
    })())

    args = [
        "orchestrator.py",
        "--repo-path",
        str(tmp_path),
        "--repo-id",
        "repo-1",
        "--run-id",
        "run-1",
        "--branch",
        "main",
        "--commit",
        "a" * 40,
        "--db-path",
        str(tmp_path / "db.duckdb"),
        "--schema-path",
        "src/sot-engine/persistence/schema.sql",
        "--run-dbt",
    ]

    monkeypatch.setattr(sys, "argv", args)
    from orchestrator import main as orchestrator_main

    orchestrator_main()
    assert dbt_ran["value"] is True
