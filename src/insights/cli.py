"""
CLI entry point for Caldera Insights reporting.
"""

import warnings
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="insights",
    help="Generate repository insights reports from Caldera dbt marts.",
)
console = Console()


def _show_warnings_handler(message: warnings.WarningMessage | str, category: type, filename: str, lineno: int, file: object = None, line: str | None = None) -> None:
    """Custom warning handler to display warnings via rich console."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


@app.command()
def generate(
    run_pk: int | None = typer.Argument(None, help="Tool run primary key (use --collection-run-id instead for collection-level reports)"),
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    collection_run_id: str | None = typer.Option(
        None,
        "--collection-run-id",
        "-c",
        help="Collection run ID (auto-resolves to SCC tool's run_pk)",
    ),
    format: str = typer.Option("html", "--format", "-f", help="Output format: html, md"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    sections: str | None = typer.Option(None, "--sections", "-s", help="Comma-separated section names"),
    title: str | None = typer.Option(None, "--title", "-t", help="Custom report title"),
) -> None:
    """Generate an insights report for a collection run.

    You can specify either:
    - run_pk: A specific tool run primary key (e.g., 19)
    - --collection-run-id: A collection run ID (UUID), which auto-resolves to the SCC tool's run_pk

    Example:
        insights generate 19 --db /tmp/caldera.duckdb
        insights generate --collection-run-id abc123... --db /tmp/caldera.duckdb
    """
    from .generator import InsightsGenerator

    # Validate that exactly one of run_pk or collection_run_id is provided
    if run_pk is None and collection_run_id is None:
        console.print("[red]Error:[/red] Must specify either run_pk argument or --collection-run-id option")
        console.print("  Use 'insights runs --db <path>' to list available runs")
        raise typer.Exit(1)

    if run_pk is not None and collection_run_id is not None:
        console.print("[red]Error:[/red] Cannot specify both run_pk and --collection-run-id")
        raise typer.Exit(1)

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    generator = InsightsGenerator(db_path=db)

    # Validate database
    validation = generator.validate_database()
    if not validation["valid"]:
        console.print(f"[red]Error:[/red] Missing required tables: {validation['missing_required']}")
        raise typer.Exit(1)

    if validation["missing_optional"]:
        console.print(f"[yellow]Warning:[/yellow] Missing optional tables: {validation['missing_optional']}")

    # Parse sections
    section_list = sections.split(",") if sections else None

    # Generate report with warning capture
    try:
        # Capture warnings to display them via rich console
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always", UserWarning)

            if collection_run_id:
                console.print(f"[dim]Resolving collection_run_id to SCC tool's run_pk...[/dim]")
                result = generator.generate_by_collection(
                    collection_run_id=collection_run_id,
                    format=format,  # type: ignore
                    sections=section_list,
                    output_path=output,
                    title=title,
                )
            else:
                result = generator.generate(
                    run_pk=run_pk,  # type: ignore (we validated it's not None above)
                    format=format,  # type: ignore
                    sections=section_list,
                    output_path=output,
                    title=title,
                )

            # Display any captured warnings
            for w in caught_warnings:
                console.print(f"[yellow]Warning:[/yellow] {w.message}")

        if output:
            console.print(f"[green]Report written to:[/green] {output}")
        else:
            console.print(result)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error generating report:[/red] {e}")
        raise typer.Exit(1)


@app.command("list-sections")
def list_sections() -> None:
    """List available report sections."""
    from .generator import InsightsGenerator

    # Create a generator without a database (just for section listing)
    # We use a dummy path since we're only listing sections
    table = Table(title="Available Report Sections")
    table.add_column("Name", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Priority", justify="right")
    table.add_column("Description")

    for name, cls in InsightsGenerator.SECTIONS.items():
        section = cls()
        table.add_row(
            name,
            section.config.title,
            str(section.config.priority),
            section.config.description,
        )

    console.print(table)


@app.command("section")
def generate_section(
    section_name: str = typer.Argument(..., help="Section name to generate"),
    run_pk: int = typer.Argument(..., help="Collection run primary key"),
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    format: str = typer.Option("html", "--format", "-f", help="Output format: html, md"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Generate a single report section."""
    from .generator import InsightsGenerator

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    generator = InsightsGenerator(db_path=db)

    try:
        result = generator.generate_section(
            section_name=section_name,
            run_pk=run_pk,
            format=format,  # type: ignore
        )

        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result)
            console.print(f"[green]Section written to:[/green] {output}")
        else:
            console.print(result)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error generating section:[/red] {e}")
        raise typer.Exit(1)


@app.command("validate")
def validate_db(
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """Validate database has required tables."""
    from .generator import InsightsGenerator

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    generator = InsightsGenerator(db_path=db)
    validation = generator.validate_database()

    if validation["valid"]:
        console.print("[green]✓[/green] Database is valid")
    else:
        console.print("[red]✗[/red] Database validation failed")
        console.print(f"  Missing required tables: {validation['missing_required']}")

    if validation["missing_optional"]:
        console.print(f"[yellow]![/yellow] Missing optional tables: {validation['missing_optional']}")

    raise typer.Exit(0 if validation["valid"] else 1)


@app.command("runs")
def list_runs(
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of runs to show"),
) -> None:
    """List available tool runs from Caldera."""
    from .data_fetcher import DataFetcher

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    fetcher = DataFetcher(db_path=db)

    sql = f"""
    SELECT
        run_pk,
        repo_id AS repository_name,
        tool_name,
        branch,
        timestamp
    FROM stg_lz_tool_runs
    ORDER BY run_pk DESC
    LIMIT {limit}
    """

    try:
        results = fetcher.fetch_raw(sql)

        table = Table(title="Tool Runs")
        table.add_column("Run PK", style="cyan", justify="right")
        table.add_column("Repository")
        table.add_column("Tool")
        table.add_column("Branch")
        table.add_column("Timestamp")

        for row in results:
            table.add_row(
                str(row.get("run_pk", "")),
                row.get("repository_name", "Unknown"),
                row.get("tool_name", ""),
                row.get("branch", ""),
                str(row.get("timestamp", ""))[:19],
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing runs:[/red] {e}")
        raise typer.Exit(1)


@app.command("collections")
def list_collections(
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of collections to show"),
) -> None:
    """List available collection runs from Caldera.

    Collection runs group multiple tool runs for a single (repo, commit) pair.
    Use --collection-run-id with the 'generate' command for collection-level reports.
    """
    from .data_fetcher import DataFetcher

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    fetcher = DataFetcher(db_path=db)

    try:
        results = fetcher.list_collection_runs(limit=limit)

        table = Table(title="Collection Runs")
        table.add_column("Collection Run ID", style="cyan")
        table.add_column("Repository")
        table.add_column("Branch")
        table.add_column("Status")
        table.add_column("Started")

        for row in results:
            table.add_row(
                row.get("collection_run_id", "")[:12] + "...",  # Truncate UUID for display
                row.get("repo_id", "Unknown"),
                row.get("branch", ""),
                row.get("status", ""),
                str(row.get("started_at", ""))[:19],
            )

        console.print(table)
        console.print()
        console.print("[dim]Tip: Use 'insights generate --collection-run-id <id> --db <path>' for reports[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing collections:[/red] {e}")
        raise typer.Exit(1)


@app.command("tool-readiness")
def tool_readiness_report(
    format: str = typer.Option("md", "--format", "-f", help="Output format: html, md"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Generate a tool readiness report.

    This report scans all tools in src/tools/ and summarizes their evaluation
    status based on scorecard.json files. Unlike other reports, this does not
    require a database connection.

    Example:
        insights tool-readiness
        insights tool-readiness --format html -o readiness.html
    """
    from .sections.tool_readiness import ToolReadinessSection
    from .formatters.html import HtmlFormatter
    from .formatters.markdown import MarkdownFormatter

    section = ToolReadinessSection()
    data = section.fetch_data(None, 0)  # run_pk is ignored

    if format == "html":
        formatter = HtmlFormatter()
        template_name = section.get_template_name()
    else:
        formatter = MarkdownFormatter()
        template_name = section.get_markdown_template_name()

    try:
        content = formatter.format_section("tool_readiness", template_name, data)

        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content)
            console.print(f"[green]Report written to:[/green] {output}")
        else:
            console.print(content)

    except Exception as e:
        console.print(f"[red]Error generating report:[/red] {e}")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
