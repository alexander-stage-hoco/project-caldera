"""``caldera db`` — query the analysis database."""

from __future__ import annotations

from pathlib import Path

import duckdb
import typer
from rich.table import Table

from caldera_cli._shared import console, get_db_path

app = typer.Typer(no_args_is_help=True)


def _connect(db: Path | None) -> duckdb.DuckDBPyConnection:
    """Open a read-only DuckDB connection, exiting on error."""
    db_path = get_db_path(db)
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database not found: {db_path}")
        raise typer.Exit(1)
    return duckdb.connect(str(db_path), read_only=True)


@app.command()
def runs(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of runs to show"),
    db: Path | None = typer.Option(None, "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """List tool runs."""
    conn = _connect(db)
    try:
        rows = conn.execute(
            """
            SELECT run_pk, repo_id, tool_name, branch, timestamp
            FROM stg_lz_tool_runs
            ORDER BY run_pk DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
    except duckdb.CatalogException:
        console.print("[red]Error:[/red] Table stg_lz_tool_runs not found. Run dbt first.")
        raise typer.Exit(1)
    finally:
        conn.close()

    table = Table(title="Tool Runs")
    table.add_column("Run PK", style="cyan", justify="right")
    table.add_column("Repository")
    table.add_column("Tool")
    table.add_column("Branch")
    table.add_column("Timestamp")

    for row in rows:
        table.add_row(str(row[0]), row[1] or "", row[2] or "", row[3] or "", str(row[4])[:19])

    console.print(table)


@app.command()
def collections(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of collections to show"),
    db: Path | None = typer.Option(None, "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """List collection runs."""
    conn = _connect(db)
    try:
        rows = conn.execute(
            """
            SELECT collection_run_id, repo_id, branch, status, started_at
            FROM lz_collection_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
    except duckdb.CatalogException:
        console.print("[red]Error:[/red] Table lz_collection_runs not found.")
        raise typer.Exit(1)
    finally:
        conn.close()

    table = Table(title="Collection Runs")
    table.add_column("Collection Run ID", style="cyan")
    table.add_column("Repository")
    table.add_column("Branch")
    table.add_column("Status")
    table.add_column("Started")

    for row in rows:
        cid = row[0] or ""
        table.add_row(cid[:12] + "..." if len(cid) > 12 else cid, row[1] or "", row[2] or "", row[3] or "", str(row[4])[:19])

    console.print(table)


@app.command()
def status(
    db: Path | None = typer.Option(None, "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """Show database summary statistics."""
    conn = _connect(db)

    table = Table(title="Database Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    try:
        for label, sql in [
            ("Collection runs", "SELECT count(*) FROM lz_collection_runs"),
            ("Tool runs", "SELECT count(*) FROM lz_tool_runs"),
            ("Completed", "SELECT count(*) FROM lz_collection_runs WHERE status = 'completed'"),
            ("Failed", "SELECT count(*) FROM lz_collection_runs WHERE status = 'failed'"),
        ]:
            try:
                val = conn.execute(sql).fetchone()[0]
                table.add_row(label, str(val))
            except duckdb.CatalogException:
                table.add_row(label, "[dim]n/a[/dim]")
    finally:
        conn.close()

    console.print(table)
