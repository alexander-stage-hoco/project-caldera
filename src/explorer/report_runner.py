#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import duckdb


ANALYSIS_MAP = {
    "atlas": "report_repo_health_snapshot",
    "category-severity": "report_category_severity",
    "cross-tool": "report_cross_tool_insights",
    "file-hotspots": "report_file_hotspots",
    "language-coverage": "report_language_coverage",
    "repo-health": "report_repo_health_snapshot",
    "hotspots": "report_hotspot_directories",
    "hotspots-full": "report_directory_hotspots_full",
    "runs": "report_collection_runs",
}

ATLAS_SECTIONS = [
    ("Repo Health Snapshot", "repo-health"),
    ("Directory Hotspots", "hotspots-full"),
    ("File Hotspots", "file-hotspots"),
    ("Cross-Tool Insights", "cross-tool"),
    ("Language Coverage", "language-coverage"),
    ("Category & Severity", "category-severity"),
]


def _dbt_compile(
    dbt_bin: str,
    project_dir: Path,
    analysis_name: str,
    vars_payload: dict,
    repo_root: Path | None = None,
) -> Path:
    vars_json = json.dumps(vars_payload)
    dbt_path = Path(dbt_bin)
    if not dbt_path.is_absolute():
        resolved_root = repo_root or project_dir.parent.parent.parent
        dbt_path = resolved_root / dbt_path
    if dbt_path.exists():
        dbt_cmd = [str(dbt_path)]
    else:
        dbt_cmd = [sys.executable, "-m", "dbt.cli.main"]
    target_path = Path("/tmp/dbt_target")
    subprocess.run(
        [
            *dbt_cmd,
            "compile",
            "--select",
            f"path:analysis/{analysis_name}.sql",
            "--vars",
            vars_json,
            "--target-path",
            str(target_path),
            "--log-path",
            "/tmp/dbt_logs",
        ],
        cwd=project_dir,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return target_path / "compiled" / "caldera_sot" / "analysis" / f"{analysis_name}.sql"


def _resolve_run_pk(conn: duckdb.DuckDBPyConnection, repo_id: str, run_id: str | None) -> int:
    if run_id:
        row = conn.execute(
            """
            select run_pk
            from unified_run_summary
            where repo_id = ? and run_id = ?
            order by run_pk desc
            limit 1
            """,
            [repo_id, run_id],
        ).fetchone()
    else:
        row = conn.execute(
            """
            select urs.run_pk
            from unified_run_summary urs
            left join lz_tool_runs tr
                on tr.run_pk = urs.run_pk
            where urs.repo_id = ?
            order by coalesce(tr.created_at, tr."timestamp") desc,
                     urs.total_files desc,
                     urs.run_pk desc
            limit 1
            """,
            [repo_id],
        ).fetchone()
    if not row:
        raise SystemExit("Unable to resolve run_pk from repo_id/run_id.")
    return int(row[0])


def _render_markdown(rows: list[tuple], headers: list[str]) -> str:
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def _render_table(rows: list[tuple], columns: list[str]) -> str:
    widths = [len(h) for h in columns]
    rendered_rows = [[str(value) if value is not None else "NULL" for value in row] for row in rows]
    for row in rendered_rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))
    fmt = " | ".join("{:<" + str(width) + "}" for width in widths)
    lines = [fmt.format(*columns), "-+-".join("-" * width for width in widths)]
    for row in rendered_rows:
        lines.append(fmt.format(*row))
    return "\n".join(lines)


def _run_query(db_path: Path, sql_path: Path, output_format: str) -> str:
    conn = duckdb.connect(str(db_path))
    try:
        sql = sql_path.read_text()
        result = conn.execute(sql)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
    finally:
        conn.close()

    if output_format == "md":
        return _render_markdown(rows, columns)
    return _render_table(rows, columns)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dbt report analyses against DuckDB.")
    parser.add_argument("report", choices=sorted(ANALYSIS_MAP), help="Report name")
    parser.add_argument("--db", default="/tmp/caldera_sot.duckdb", help="DuckDB database path")
    parser.add_argument("--dbt-bin", default=".venv/bin/dbt", help="dbt binary path")
    parser.add_argument("--project-dir", default="src/sot-engine/dbt", help="dbt project directory")
    parser.add_argument("--run-pk", type=int, help="Run primary key for the report")
    parser.add_argument("--repo-id", help="Repository id for run resolution")
    parser.add_argument("--run-id", help="Run id for run resolution")
    parser.add_argument("--limit", type=int, default=10, help="Hotspot limit (hotspots report)")
    parser.add_argument(
        "--format",
        choices=["table", "md"],
        default="table",
        help="Output format",
    )
    parser.add_argument("--out", help="Write report output to a file")

    args = parser.parse_args()
    db_path = Path(args.db)
    project_dir = Path(args.project_dir).resolve()
    repo_root = Path(__file__).resolve().parents[2]

    vars_payload = {}
    if args.report != "runs":
        conn = duckdb.connect(str(db_path))
        try:
            if args.run_pk is not None:
                run_pk = args.run_pk
            elif args.repo_id:
                run_pk = _resolve_run_pk(conn, args.repo_id, args.run_id)
            else:
                raise SystemExit("Provide --run-pk or --repo-id (optionally --run-id).")
        finally:
            conn.close()
        vars_payload["run_pk"] = run_pk
        if args.report in ("hotspots", "hotspots-full", "file-hotspots", "cross-tool"):
            vars_payload["limit"] = args.limit

    if args.report == "atlas":
        output_chunks = []
        for title, report_name in ATLAS_SECTIONS:
            section_vars = dict(vars_payload)
            analysis_name = ANALYSIS_MAP[report_name]
            if report_name in ("hotspots-full", "file-hotspots", "cross-tool"):
                section_vars["limit"] = args.limit
            output_chunks.append(f"\n== {title} ==\n")
            compiled_sql = _dbt_compile(args.dbt_bin, project_dir, analysis_name, section_vars, repo_root)
            output_chunks.append(_run_query(db_path, compiled_sql, args.format))
        output_text = "\n".join(output_chunks)
        print(output_text)
        if args.out:
            Path(args.out).write_text(output_text)
        return 0

    analysis_name = ANALYSIS_MAP[args.report]
    compiled_sql = _dbt_compile(args.dbt_bin, project_dir, analysis_name, vars_payload, repo_root)
    output_text = _run_query(db_path, compiled_sql, args.format)
    print(output_text)
    if args.out:
        Path(args.out).write_text(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
