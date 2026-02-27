"""Root Typer app — registers all sub-commands and sub-apps."""

from __future__ import annotations

import typer

from caldera_cli.commands import (
    analyze,
    cloud,
    compliance,
    db,
    dbt_cmd,
    docker,
    export,
    report,
    status,
    tools,
)

app = typer.Typer(
    name="caldera",
    help="Caldera — Code Analysis Pipeline",
    no_args_is_help=True,
)

# Sub-apps (command groups)
app.add_typer(analyze.app, name="analyze", help="Run analysis pipelines")
app.add_typer(report.app, name="report", help="Generate and manage reports")
app.add_typer(db.app, name="db", help="Query the analysis database")
app.add_typer(compliance.app, name="compliance", help="Run compliance checks")
app.add_typer(tools.app, name="tools", help="Manage analysis tools")
app.add_typer(dbt_cmd.app, name="dbt", help="Run dbt transformations")
app.add_typer(cloud.app, name="cloud", help="Cloud analysis operations")
app.add_typer(docker.app, name="docker", help="Docker image management")

# Top-level commands
app.command("status")(status.status_cmd)
app.command("export")(export.export_cmd)


def main() -> None:
    """Entry point for ``caldera`` console script."""
    app()


if __name__ == "__main__":
    main()
