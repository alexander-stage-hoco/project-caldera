from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT_SRC = Path(__file__).resolve().parents[2]
if str(ROOT_SRC) not in sys.path:
    sys.path.append(str(ROOT_SRC))

from explorer.report_runner import ANALYSIS_MAP, _dbt_compile, _resolve_run_pk


def _seed_tables(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        create table unified_run_summary (
            run_pk integer,
            repo_id varchar,
            run_id varchar,
            total_files integer
        )
        """
    )
    conn.execute(
        """
        create table lz_tool_runs (
            run_pk integer,
            repo_id varchar,
            run_id varchar,
            created_at timestamp,
            "timestamp" timestamp
        )
        """
    )


def test_resolve_run_pk_prefers_latest_created_at() -> None:
    conn = duckdb.connect(":memory:")
    try:
        _seed_tables(conn)
        conn.execute(
            """
            insert into unified_run_summary values
                (1, 'demo', 'run-1', 10),
                (2, 'demo', 'run-2', 12)
            """
        )
        conn.execute(
            """
            insert into lz_tool_runs values
                (1, 'demo', 'run-1', '2026-01-01 00:00:00', null),
                (2, 'demo', 'run-2', '2026-01-02 00:00:00', null)
            """
        )
        assert _resolve_run_pk(conn, "demo", None) == 2
    finally:
        conn.close()


def test_resolve_run_pk_uses_timestamp_fallback() -> None:
    conn = duckdb.connect(":memory:")
    try:
        _seed_tables(conn)
        conn.execute(
            """
            insert into unified_run_summary values
                (10, 'demo', 'run-a', 10),
                (11, 'demo', 'run-b', 12)
            """
        )
        conn.execute(
            """
            insert into lz_tool_runs values
                (10, 'demo', 'run-a', null, '2026-01-03 00:00:00'),
                (11, 'demo', 'run-b', null, '2026-01-02 00:00:00')
            """
        )
        assert _resolve_run_pk(conn, "demo", None) == 10
    finally:
        conn.close()


def test_resolve_run_pk_with_run_id() -> None:
    conn = duckdb.connect(":memory:")
    try:
        _seed_tables(conn)
        conn.execute(
            """
            insert into unified_run_summary values
                (20, 'demo', 'run-a', 2),
                (21, 'demo', 'run-b', 3)
            """
        )
        conn.execute(
            """
            insert into lz_tool_runs values
                (20, 'demo', 'run-a', '2026-01-01 00:00:00', null),
                (21, 'demo', 'run-b', '2026-01-02 00:00:00', null)
            """
        )
        assert _resolve_run_pk(conn, "demo", "run-a") == 20
    finally:
        conn.close()


def test_dbt_compile_falls_back_to_module(monkeypatch, tmp_path) -> None:
    calls = {}

    def fake_run(cmd, cwd, check, **_kwargs):  # noqa: ANN001
        calls["cmd"] = cmd
        calls["cwd"] = cwd
        calls["check"] = check

    monkeypatch.setattr("subprocess.run", fake_run)
    _dbt_compile("/missing/dbt", tmp_path, "report_repo_health_snapshot", {"run_pk": 1}, tmp_path)
    assert calls["cmd"][:3] == [sys.executable, "-m", "dbt.cli.main"]
    assert "path:analysis/report_repo_health_snapshot.sql" in calls["cmd"]


def test_dbt_compile_resolves_relative_path(monkeypatch, tmp_path) -> None:
    calls = {}
    project_dir = tmp_path / "src" / "sot-engine" / "dbt"
    project_dir.mkdir(parents=True)
    dbt_bin = tmp_path / ".venv" / "bin" / "dbt"
    dbt_bin.parent.mkdir(parents=True)
    dbt_bin.write_text("#!/bin/sh\n")

    def fake_run(cmd, cwd, check, **_kwargs):  # noqa: ANN001
        calls["cmd"] = cmd
        calls["cwd"] = cwd
        calls["check"] = check

    monkeypatch.setattr("subprocess.run", fake_run)
    _dbt_compile(".venv/bin/dbt", project_dir, "report_repo_health_snapshot", {"run_pk": 1}, tmp_path)
    assert calls["cmd"][0] == str(dbt_bin)
    assert "path:analysis/report_repo_health_snapshot.sql" in calls["cmd"]


def test_analysis_map_contains_new_reports() -> None:
    expected = {
        "atlas",
        "category-severity",
        "cross-tool",
        "file-hotspots",
        "hotspots-full",
        "language-coverage",
    }
    assert expected.issubset(set(ANALYSIS_MAP))


def test_atlas_runs_all_sections(monkeypatch, tmp_path, capsys) -> None:
    calls = []

    def fake_compile(dbt_bin, project_dir, analysis_name, vars_payload, repo_root):  # noqa: ANN001
        calls.append(("compile", analysis_name, vars_payload))
        path = tmp_path / f"{analysis_name}.sql"
        path.write_text("select 1 as ok;")
        return path

    def fake_run_query(db_path, sql_path, output_format):  # noqa: ANN001
        calls.append(("run", sql_path.name, output_format))
        return "ok"

    monkeypatch.setattr("explorer.report_runner._dbt_compile", fake_compile)
    monkeypatch.setattr("explorer.report_runner._run_query", fake_run_query)
    monkeypatch.setattr(
        "explorer.report_runner._resolve_run_pk",
        lambda *_args, **_kwargs: 1,
    )
    monkeypatch.setattr("sys.argv", ["report_runner.py", "atlas", "--repo-id", "demo"])

    from explorer.report_runner import main

    assert main() == 0
    assert any(call[1] == "report_repo_health_snapshot" for call in calls if call[0] == "compile")
    assert any(call[1] == "report_directory_hotspots_full" for call in calls if call[0] == "compile")
    assert any(call[1] == "report_file_hotspots" for call in calls if call[0] == "compile")
    assert any(call[1] == "report_cross_tool_insights" for call in calls if call[0] == "compile")
    assert any(call[1] == "report_language_coverage" for call in calls if call[0] == "compile")
    assert any(call[1] == "report_category_severity" for call in calls if call[0] == "compile")
