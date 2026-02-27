"""``caldera analyze`` — run analysis pipelines."""

from __future__ import annotations

import typer

from caldera_cli._shared import run_make

app = typer.Typer(no_args_is_help=True)


@app.command("run")
def analyze_run(
    repo: str = typer.Argument(..., help="Path or GitHub URL of repository to analyze"),
    replace: bool = typer.Option(False, "--replace", help="Replace existing collection run"),
    skip_tools: str | None = typer.Option(None, "--skip-tools", help="Comma-separated tool names to skip"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM evaluation"),
    db: str | None = typer.Option(None, "--db", help="Path to DuckDB database"),
) -> None:
    """Run the full analysis pipeline on a repository."""
    variables: dict[str, str] = {"REPO": repo}
    if replace:
        variables["REPLACE"] = "1"
    if skip_tools:
        variables["SKIP_TOOLS"] = skip_tools
    if no_llm:
        variables["PIPELINE_LLM"] = "0"
    if db:
        variables["DB_PATH"] = db

    rc = run_make("analyze", variables)
    raise typer.Exit(rc)


@app.command()
def bundle(
    repo: str = typer.Argument(..., help="Path or GitHub URL of repository"),
    bundle_path: str = typer.Option(..., "--bundle", "-b", help="Path to artifact bundle"),
    db: str | None = typer.Option(None, "--db", help="Path to DuckDB database"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM evaluation"),
) -> None:
    """Ingest an artifact bundle and generate a report."""
    variables: dict[str, str] = {"REPO": repo, "BUNDLE": bundle_path}
    if db:
        variables["DB_PATH"] = db
    if no_llm:
        variables["PIPELINE_LLM"] = "0"

    rc = run_make("analyze-bundle", variables)
    raise typer.Exit(rc)


@app.command()
def collect(
    repo: str = typer.Argument(..., help="Path or GitHub URL of repository"),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Bundle output directory"),
    skip_tools: str | None = typer.Option(None, "--skip-tools", help="Comma-separated tool names to skip"),
    no_tar: bool = typer.Option(False, "--no-tar", help="Skip tar.gz creation"),
) -> None:
    """Collect tool artifacts into a portable bundle."""
    variables: dict[str, str] = {"REPO": repo}
    if output_dir:
        variables["BUNDLE_DIR"] = output_dir
    if skip_tools:
        variables["SKIP_TOOLS"] = skip_tools
    if no_tar:
        variables["BUNDLE_TAR"] = "0"

    rc = run_make("collect", variables)
    raise typer.Exit(rc)
