"""``caldera cloud`` — cloud analysis operations."""

from __future__ import annotations

import typer

from caldera_cli._shared import run_make, run_script

app = typer.Typer(no_args_is_help=True)


@app.command()
def setup() -> None:
    """One-time cloud infrastructure setup (terraform init)."""
    rc = run_make("cloud-setup")
    raise typer.Exit(rc)


@app.command("run")
def cloud_run(
    repo: str = typer.Argument(..., help="GitHub URL of repository to analyze"),
    server: str | None = typer.Option(
        None,
        "--server",
        "-s",
        help="Server preset (small/medium/large/xlarge) or Hetzner type (cx23/cx33/cx43/cx53)",
    ),
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


@app.command()
def cleanup(
    ttl_hours: float = typer.Option(4.0, "--ttl-hours", help="Max VM age in hours before destruction"),
    dry_run: bool = typer.Option(False, "--dry-run", help="List orphaned VMs without destroying them"),
) -> None:
    """Destroy orphaned cloud VMs older than TTL."""
    args = []
    if ttl_hours != 4.0:
        args.extend(["--ttl-hours", str(ttl_hours)])
    if dry_run:
        args.append("--dry-run")
    rc = run_script("cloud_cleanup.py", args)
    raise typer.Exit(rc)
