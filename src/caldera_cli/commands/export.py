"""``caldera export`` — export results to a git repository."""

from __future__ import annotations

from pathlib import Path

import typer

from caldera_cli._shared import run_make

app = typer.Typer()


def export_cmd(
    collection_run_id: str | None = typer.Option(None, "--collection-run-id", "-c", help="Collection run ID to export"),
    results_repo: str | None = typer.Option(None, "--results-repo", help="Git URL for results repository"),
    push: bool = typer.Option(False, "--push", help="Push after export"),
    db: str | None = typer.Option(None, "--db", help="Path to DuckDB database"),
) -> None:
    """Export latest run to a git results repository."""
    variables: dict[str, str] = {}
    if collection_run_id:
        variables["COLLECTION_RUN_ID"] = collection_run_id
    if results_repo:
        variables["RESULTS_REPO_URL"] = results_repo
    if push:
        variables["PUSH"] = "1"
    if db:
        variables["DB_PATH"] = db

    rc = run_make("export-results", variables)
    raise typer.Exit(rc)
