"""``caldera dbt`` — run dbt transformations."""

from __future__ import annotations

import typer

from caldera_cli._shared import run_make

app = typer.Typer(no_args_is_help=True)


@app.command("run")
def dbt_run() -> None:
    """Execute dbt models."""
    rc = run_make("dbt-run")
    raise typer.Exit(rc)


@app.command("test")
def dbt_test() -> None:
    """Run dbt tests."""
    rc = run_make("dbt-test")
    raise typer.Exit(rc)
