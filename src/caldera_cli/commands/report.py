"""``caldera report`` — generate and manage reports."""

from __future__ import annotations

import warnings
from pathlib import Path

import typer
from rich.table import Table

from caldera_cli._shared import console, ensure_src_on_path, get_db_path

app = typer.Typer(no_args_is_help=True)


@app.command()
def generate(
    run_pk: int | None = typer.Argument(None, help="Tool run primary key"),
    collection_run_id: str | None = typer.Option(None, "--collection-run-id", "-c", help="Collection run ID (UUID)"),
    db: Path | None = typer.Option(None, "--db", "-d", help="Path to DuckDB database"),
    format: str = typer.Option("html", "--format", "-f", help="Output format: html, md"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    sections: str | None = typer.Option(None, "--sections", "-s", help="Comma-separated section names"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Stakeholder profile (cto, investor, ceo)"),
    title: str | None = typer.Option(None, "--title", "-t", help="Custom report title"),
) -> None:
    """Generate an insights report for a collection run."""
    ensure_src_on_path()
    from insights.generator import InsightsGenerator

    db_path = get_db_path(db)
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database not found: {db_path}")
        raise typer.Exit(1)

    if run_pk is None and collection_run_id is None:
        console.print("[red]Error:[/red] Must specify either run_pk argument or --collection-run-id option")
        raise typer.Exit(1)

    if run_pk is not None and collection_run_id is not None:
        console.print("[red]Error:[/red] Cannot specify both run_pk and --collection-run-id")
        raise typer.Exit(1)

    if profile is not None and sections is not None:
        console.print("[red]Error:[/red] Cannot specify both --profile and --sections")
        raise typer.Exit(1)

    generator = InsightsGenerator(db_path=db_path)

    validation = generator.validate_database()
    if not validation["valid"]:
        console.print(f"[red]Error:[/red] Missing required tables: {validation['missing_required']}")
        raise typer.Exit(1)

    if validation["missing_optional"]:
        console.print(f"[yellow]Warning:[/yellow] Missing optional tables: {validation['missing_optional']}")

    section_list = sections.split(",") if sections else None

    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always", UserWarning)

            if collection_run_id:
                console.print("[dim]Resolving collection_run_id...[/dim]")
                result = generator.generate_by_collection(
                    collection_run_id=collection_run_id,
                    format=format,
                    sections=section_list,
                    output_path=output,
                    title=title,
                    profile=profile,
                )
            else:
                result = generator.generate(
                    run_pk=run_pk,
                    format=format,
                    sections=section_list,
                    output_path=output,
                    title=title,
                    profile=profile,
                )

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
    ensure_src_on_path()
    from insights.generator import InsightsGenerator

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


@app.command("list-profiles")
def list_profiles_cmd() -> None:
    """List available stakeholder report profiles."""
    ensure_src_on_path()
    from insights.profiles import list_profiles

    table = Table(title="Stakeholder Report Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Audience", style="green")
    table.add_column("Sections", justify="right")
    table.add_column("Description")
    table.add_column("Gaps", style="yellow")

    for p in list_profiles():
        table.add_row(
            p.name,
            p.display_name,
            str(len(p.sections)),
            p.description,
            ", ".join(p.gaps) if p.gaps else "-",
        )

    console.print(table)


@app.command("tool-readiness")
def tool_readiness(
    format: str = typer.Option("md", "--format", "-f", help="Output format: html, md"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Generate a tool readiness report (no database required)."""
    ensure_src_on_path()
    from insights.sections.tool_readiness import ToolReadinessSection
    from insights.formatters.html import HtmlFormatter
    from insights.formatters.markdown import MarkdownFormatter

    section = ToolReadinessSection()
    data = section.fetch_data(None, 0)

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
