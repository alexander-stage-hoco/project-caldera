"""
CLI entry point for Caldera Insights reporting.
"""

from __future__ import annotations

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
    format: str = typer.Option("html", "--format", "-f", help="Output format: html, md, pack (LLM context directory)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file/directory path"),
    sections: str | None = typer.Option(None, "--sections", "-s", help="Comma-separated section names"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Stakeholder profile (cto, investor, ceo)"),
    title: str | None = typer.Option(None, "--title", "-t", help="Custom report title"),
    report_llm: bool = typer.Option(False, "--report-llm", help="Enable LLM narrative enrichment in reports"),
    parameter_set_name: str | None = typer.Option(None, "--parameter-set", help="Named parameter set for evidence thresholds"),
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

    if profile is not None and sections is not None:
        console.print("[red]Error:[/red] Cannot specify both --profile and --sections")
        raise typer.Exit(1)

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    generator = InsightsGenerator(db_path=db, report_llm=report_llm, parameter_set=parameter_set_name)

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

            if format == "pack":
                # Pack format produces a directory, not a single file
                pack_dir = output or Path("./caldera-context-pack")
                if collection_run_id:
                    console.print(f"[dim]Resolving collection_run_id to SCC tool's run_pk...[/dim]")
                    generator.generate_pack_by_collection(
                        collection_run_id=collection_run_id,
                        output_dir=pack_dir,
                        sections=section_list,
                        title=title,
                        profile=profile,
                    )
                else:
                    generator.generate_pack(
                        run_pk=run_pk,  # type: ignore
                        output_dir=pack_dir,
                        sections=section_list,
                        title=title,
                        profile=profile,
                    )

                # Display any captured warnings
                for w in caught_warnings:
                    console.print(f"[yellow]Warning:[/yellow] {w.message}")

                # List files written
                console.print(f"[green]Context pack written to:[/green] {pack_dir}/")
                for f in sorted(pack_dir.iterdir()):
                    size_kb = f.stat().st_size / 1024
                    console.print(f"  {f.name} ({size_kb:.1f} KB)")
            else:
                if collection_run_id:
                    console.print(f"[dim]Resolving collection_run_id to SCC tool's run_pk...[/dim]")
                    result = generator.generate_by_collection(
                        collection_run_id=collection_run_id,
                        format=format,  # type: ignore
                        sections=section_list,
                        output_path=output,
                        title=title,
                        profile=profile,
                    )
                else:
                    result = generator.generate(
                        run_pk=run_pk,  # type: ignore (we validated it's not None above)
                        format=format,  # type: ignore
                        sections=section_list,
                        output_path=output,
                        title=title,
                        profile=profile,
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


@app.command("list-profiles")
def list_profiles_cmd() -> None:
    """List available stakeholder report profiles."""
    from .profiles import list_profiles

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


# ---------------------------------------------------------------------------
# Evidence subcommand group
# ---------------------------------------------------------------------------

evidence_app = typer.Typer(
    name="evidence",
    help="Manage evidence sets: generate, review, accept, compare.",
)
app.add_typer(evidence_app, name="evidence")


@evidence_app.command("list-sets")
def evidence_list_sets(
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    collection_run_id: str | None = typer.Option(None, "--collection-run-id", "-c", help="Filter by collection run"),
) -> None:
    """List evidence sets."""
    import duckdb
    from .evidence.reviewer import EvidenceReviewer

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    with duckdb.connect(str(db)) as conn:
        reviewer = EvidenceReviewer(conn)
        sets = reviewer.list_sets(collection_run_id)

    if not sets:
        console.print("[yellow]No evidence sets found.[/yellow]")
        return

    table = Table(title="Evidence Sets")
    table.add_column("Set ID", style="cyan")
    table.add_column("Collection Run")
    table.add_column("Parameter Set")
    table.add_column("Status")
    table.add_column("Items", justify="right")
    table.add_column("Reviewed", justify="right")
    table.add_column("Accepted", justify="right")

    for s in sets:
        table.add_row(
            s.evidence_set_id[:12] + "...",
            s.collection_run_id[:12] + "...",
            s.parameter_set_name,
            s.status,
            str(s.total_items),
            str(s.reviewed_items),
            str(s.accepted_items),
        )

    console.print(table)


@evidence_app.command("generate")
def evidence_generate(
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    collection_run_id: str = typer.Option(..., "--collection-run-id", "-c", help="Collection run ID"),
    parameter_set: str = typer.Option("default", "--parameter-set", "-p", help="Parameter set name"),
) -> None:
    """Generate an evidence set with a specific parameter set."""
    import duckdb

    from .config import ConfigLoader
    from .data_fetcher import DataFetcher
    from .evidence.builder import EvidenceRegistryBuilder

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    try:
        ps = ConfigLoader.load_parameter_set(parameter_set)
        registry_cfg = ConfigLoader.load_categories()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    fetcher = DataFetcher(db_path=db)
    run_pk = fetcher.get_scc_run_pk_for_collection(collection_run_id)

    builder = EvidenceRegistryBuilder(
        parameter_set=ps,
        category_registry=registry_cfg,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        evidence_registry = builder.build(fetcher, run_pk)

    for w in caught:
        console.print(f"[yellow]Warning:[/yellow] {w.message}")

    with duckdb.connect(str(db)) as conn:
        # Persist evidence with auto-created evidence set + structured params
        evidence_set_id = EvidenceRegistryBuilder.persist(
            evidence_registry, conn, collection_run_id, parameter_set=ps,
        )

        if evidence_set_id is None:
            console.print("[red]Error:[/red] Failed to create evidence set")
            raise typer.Exit(1)

        # Create pending reviews for all items
        for e in evidence_registry.evidence:
            conn.execute(
                "INSERT INTO lz_evidence_reviews (evidence_set_id, evidence_id, verdict) VALUES (?, ?, ?)",
                [evidence_set_id, e.evidence_id, "pending"],
            )

    console.print(f"[green]Evidence set created:[/green] {evidence_set_id}")
    console.print(f"  Parameter set: {parameter_set}")
    console.print(f"  Evidence items: {len(evidence_registry.evidence)}")
    console.print(f"  Claims: {len(evidence_registry.claims)}")
    console.print(f"  Risks: {len(evidence_registry.risks)}")


@evidence_app.command("show")
def evidence_show(
    set_id: str = typer.Argument(..., help="Evidence set ID"),
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    category: str | None = typer.Option(None, "--category", help="Filter by category"),
    status: str | None = typer.Option(None, "--status", help="Filter by review status"),
) -> None:
    """Show evidence items in a set."""
    import duckdb

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    with duckdb.connect(str(db), read_only=True) as conn:
        sql = (
            "SELECT e.evidence_id, e.category, e.location, e.observation, "
            "e.confidence, COALESCE(r.verdict, 'pending') AS verdict "
            "FROM lz_evidence e "
            "LEFT JOIN lz_evidence_reviews r "
            "  ON r.evidence_set_id = e.evidence_set_id AND r.evidence_id = e.evidence_id "
            "WHERE e.evidence_set_id = ?"
        )
        params: list = [set_id]
        if category:
            sql += " AND e.category = ?"
            params.append(category)
        if status:
            sql += " AND COALESCE(r.verdict, 'pending') = ?"
            params.append(status)
        sql += " ORDER BY e.category, e.evidence_id"

        rows = conn.execute(sql, params).fetchall()
        cols = [d[0] for d in conn.execute(sql, params).description] if rows else []

    if not rows:
        console.print("[yellow]No evidence items found.[/yellow]")
        return

    table = Table(title=f"Evidence Set: {set_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Category")
    table.add_column("Location")
    table.add_column("Observation")
    table.add_column("Confidence")
    table.add_column("Verdict", style="bold")

    for row in rows:
        r = dict(zip(cols, row))
        verdict_style = {
            "accepted": "green",
            "rejected": "red",
            "enhanced": "blue",
            "pending": "yellow",
        }.get(r["verdict"], "")
        table.add_row(
            r["evidence_id"],
            r["category"],
            r["location"][:40],
            r["observation"][:60],
            r["confidence"],
            f"[{verdict_style}]{r['verdict']}[/{verdict_style}]" if verdict_style else r["verdict"],
        )

    console.print(table)


@evidence_app.command("review")
def evidence_review(
    set_id: str = typer.Argument(..., help="Evidence set ID"),
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
    batch_accept: bool = typer.Option(False, "--batch-accept", help="Accept all pending items"),
    reviewer_name: str = typer.Option("cli-user", "--reviewer", help="Reviewer name"),
) -> None:
    """Review evidence items in a set (batch-accept or interactive)."""
    import duckdb
    from .evidence.reviewer import EvidenceReviewer

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    with duckdb.connect(str(db)) as conn:
        rv = EvidenceReviewer(conn)
        es = rv.get_set(set_id)
        if es is None:
            console.print(f"[red]Error:[/red] Evidence set not found: {set_id}")
            raise typer.Exit(1)

        if batch_accept:
            count = rv.batch_accept(set_id, reviewer_name)
            console.print(f"[green]Batch-accepted {count} evidence items.[/green]")
            return

        # Interactive review
        pending = rv.get_pending(set_id)
        if not pending:
            console.print("[green]All items already reviewed.[/green]")
            return

        console.print(f"[bold]{len(pending)} items pending review.[/bold]")

        for eid in pending:
            row = conn.execute(
                "SELECT * FROM lz_evidence WHERE evidence_set_id = ? AND evidence_id = ?",
                [set_id, eid],
            ).fetchone()
            if not row:
                continue
            cols = [d[0] for d in conn.execute(
                "SELECT * FROM lz_evidence LIMIT 0"
            ).description]
            item = dict(zip(cols, row))

            from rich.panel import Panel
            panel_content = (
                f"[bold]Category:[/bold] {item['category']}\n"
                f"[bold]Location:[/bold] {item['location']}\n"
                f"[bold]Excerpt:[/bold] {item.get('excerpt', '')}\n"
                f"[bold]Observation:[/bold] {item.get('observation', '')}\n"
                f"[bold]Why it matters:[/bold] {item.get('why_it_matters', '')}\n"
                f"[bold]Tool:[/bold] {item['tool_source']}  [bold]Confidence:[/bold] {item['confidence']}"
            )
            console.print(Panel(panel_content, title=f"Evidence: {eid}", border_style="blue"))

            verdict = typer.prompt(
                "Verdict (a=accept, r=reject, e=enhance, s=skip)",
                default="a",
            )
            verdict_map = {"a": "accepted", "r": "rejected", "e": "enhanced", "s": None}
            mapped = verdict_map.get(verdict)
            if mapped is None:
                continue

            notes = None
            if mapped in ("enhanced", "rejected"):
                notes = typer.prompt("Notes (optional)", default="")

            rv.submit_review(set_id, eid, mapped, reviewer_name, notes=notes or None)
            console.print(f"  [{mapped}] {eid}")


@evidence_app.command("accept")
def evidence_accept(
    set_id: str = typer.Argument(..., help="Evidence set ID"),
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """Accept an evidence set (transition to accepted status)."""
    import duckdb
    from .evidence.reviewer import EvidenceReviewer

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    with duckdb.connect(str(db)) as conn:
        rv = EvidenceReviewer(conn)
        try:
            rv.transition_status(set_id, "accepted")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"[green]Evidence set accepted:[/green] {set_id}")


@evidence_app.command("compare")
def evidence_compare(
    set_id_1: str = typer.Argument(..., help="First evidence set ID"),
    set_id_2: str = typer.Argument(..., help="Second evidence set ID"),
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """Compare two evidence sets."""
    import duckdb

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    with duckdb.connect(str(db), read_only=True) as conn:
        def _get_items(sid: str) -> dict[str, dict]:
            rows = conn.execute(
                "SELECT evidence_id, category, location, observation FROM lz_evidence WHERE evidence_set_id = ?",
                [sid],
            ).fetchall()
            cols = ["evidence_id", "category", "location", "observation"]
            return {r[0]: dict(zip(cols, r)) for r in rows}

        items1 = _get_items(set_id_1)
        items2 = _get_items(set_id_2)

    locs1 = {v["location"] for v in items1.values()}
    locs2 = {v["location"] for v in items2.values()}
    only1 = locs1 - locs2
    only2 = locs2 - locs1
    shared = locs1 & locs2

    console.print(f"[bold]Set 1:[/bold] {set_id_1} ({len(items1)} items)")
    console.print(f"[bold]Set 2:[/bold] {set_id_2} ({len(items2)} items)")
    console.print()
    console.print(f"Shared locations: {len(shared)}")
    console.print(f"Only in set 1: {len(only1)}")
    console.print(f"Only in set 2: {len(only2)}")

    if only1:
        console.print("\n[bold]Locations only in set 1:[/bold]")
        for loc in sorted(only1)[:20]:
            console.print(f"  {loc}")

    if only2:
        console.print("\n[bold]Locations only in set 2:[/bold]")
        for loc in sorted(only2)[:20]:
            console.print(f"  {loc}")


# Claims subcommand group
claims_app = typer.Typer(
    name="claims",
    help="Manage claim generation from accepted evidence sets.",
)
app.add_typer(claims_app, name="claims")


@claims_app.command("generate")
def claims_generate(
    set_id: str = typer.Argument(..., help="Evidence set ID (must be accepted)"),
    db: Path = typer.Option(..., "--db", "-d", help="Path to DuckDB database"),
) -> None:
    """Generate claims from an accepted evidence set."""
    import duckdb
    from .evidence.reviewer import EvidenceReviewer

    if not db.exists():
        console.print(f"[red]Error:[/red] Database not found: {db}")
        raise typer.Exit(1)

    with duckdb.connect(str(db)) as conn:
        rv = EvidenceReviewer(conn)
        es = rv.get_set(set_id)
        if es is None:
            console.print(f"[red]Error:[/red] Evidence set not found: {set_id}")
            raise typer.Exit(1)
        if es.status != "accepted":
            console.print(f"[red]Error:[/red] Evidence set must be accepted (current: {es.status})")
            raise typer.Exit(1)

    console.print(f"[green]Claims can be generated from accepted set:[/green] {set_id}")
    console.print("[dim]Full claim generation will use the stored parameter set.[/dim]")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
