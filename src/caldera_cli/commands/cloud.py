"""``caldera cloud`` — cloud analysis operations."""

from __future__ import annotations

import typer

from caldera_cli._shared import run_make

app = typer.Typer(no_args_is_help=True)


@app.command()
def setup() -> None:
    """One-time cloud infrastructure setup (terraform init)."""
    rc = run_make("cloud-setup")
    raise typer.Exit(rc)


@app.command("run")
def cloud_run(
    repo: str = typer.Argument(..., help="GitHub URL of repository to analyze"),
    server: str | None = typer.Option(None, "--server", "-s", help="Hetzner server type (e.g., cx33)"),
    keep: bool = typer.Option(False, "--keep", help="Keep VM alive after run"),
) -> None:
    """Run analysis on a cloud VM."""
    variables: dict[str, str] = {"REPO": repo}
    if server:
        variables["CLOUD_SERVER"] = server
    if keep:
        variables["KEEP_SERVER"] = "1"

    rc = run_make("cloud-run", variables)
    raise typer.Exit(rc)


@app.command()
def status() -> None:
    """Show cloud infrastructure status."""
    rc = run_make("cloud-status")
    raise typer.Exit(rc)


@app.command()
def destroy() -> None:
    """Destroy cloud server."""
    rc = run_make("cloud-destroy")
    raise typer.Exit(rc)
