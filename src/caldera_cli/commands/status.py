"""``caldera status`` — top-level health check."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer
from rich.table import Table

from caldera_cli._shared import console, find_project_root, get_db_path


def status_cmd(
    db: Path | None = typer.Option(None, "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """Show system health: Python, venv, database, tools, dbt."""
    root = find_project_root()
    db_path = get_db_path(db)

    table = Table(title="Caldera Status")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Detail")

    # Python version
    v = sys.version_info
    ok = v >= (3, 12)
    table.add_row(
        "Python",
        "[green]ok[/green]" if ok else "[red]fail[/red]",
        f"{v.major}.{v.minor}.{v.micro}",
    )

    # Project venv
    venv_exists = (root / ".venv" / "bin" / "python").is_file()
    table.add_row(
        "Project venv",
        "[green]ok[/green]" if venv_exists else "[red]missing[/red]",
        str(root / ".venv"),
    )

    # Database
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        table.add_row("Database", "[green]ok[/green]", f"{db_path} ({size_mb:.1f} MB)")
    else:
        table.add_row("Database", "[yellow]not found[/yellow]", str(db_path))

    # Database tables (if DB exists)
    if db_path.exists():
        try:
            import duckdb

            conn = duckdb.connect(str(db_path), read_only=True)
            try:
                count = conn.execute("SELECT count(*) FROM lz_collection_runs").fetchone()[0]
                table.add_row("Collection runs", "[green]ok[/green]", str(count))
            except duckdb.CatalogException:
                table.add_row("Collection runs", "[yellow]no table[/yellow]", "")
            finally:
                conn.close()
        except Exception as e:
            table.add_row("Collection runs", "[red]error[/red]", str(e))

    # Tools count
    tools_dir = root / "src" / "tools"
    tool_count = sum(1 for d in tools_dir.iterdir() if d.is_dir() and (d / "Makefile").exists())
    table.add_row("Tools", "[green]ok[/green]", f"{tool_count} tools in src/tools/")

    # dbt
    dbt_available = shutil.which("dbt") is not None or (root / ".venv" / "bin" / "dbt").is_file()
    table.add_row(
        "dbt",
        "[green]ok[/green]" if dbt_available else "[yellow]not installed[/yellow]",
        "",
    )

    console.print(table)
