"""``caldera docker`` — Docker image management."""

from __future__ import annotations

import typer

from caldera_cli._shared import run_make

app = typer.Typer(no_args_is_help=True)


@app.command()
def build(
    tool: str | None = typer.Option(None, "--tool", "-t", help="Single tool to build"),
    all_images: bool = typer.Option(False, "--all", help="Build all images (bases + tools + runner + orchestrator)"),
) -> None:
    """Build Docker images."""
    if all_images:
        rc = run_make("docker-build-all")
    elif tool:
        rc = run_make("docker-build-tool", {"TOOL": tool})
    else:
        rc = run_make("docker-build-base")
    raise typer.Exit(rc)


@app.command()
def pull() -> None:
    """Pull all pre-built images from GHCR."""
    rc = run_make("docker-pull-all")
    raise typer.Exit(rc)


@app.command()
def test(
    tool: str = typer.Option(..., "--tool", "-t", help="Tool name to test"),
    repo: str = typer.Option(..., "--repo", "-r", help="Path to repository for testing"),
) -> None:
    """Test Docker vs native output parity for a tool."""
    rc = run_make("docker-test-tool", {"TOOL": tool, "REPO": repo})
    raise typer.Exit(rc)
