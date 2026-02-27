"""``caldera compliance`` — run compliance checks."""

from __future__ import annotations

import typer

from caldera_cli._shared import run_make, run_script

app = typer.Typer(no_args_is_help=True)


@app.command()
def check(
    preflight: bool = typer.Option(False, "--preflight", help="Fast structure checks only"),
    full: bool = typer.Option(False, "--full", help="Full compliance with tool execution"),
    tool: str | None = typer.Option(None, "--tool", "-t", help="Single tool to check"),
) -> None:
    """Run structural compliance checks."""
    if tool:
        from caldera_cli._shared import find_project_root, get_venv_python
        import subprocess

        root = find_project_root()
        python = get_venv_python()
        cmd = [python, str(root / "src" / "tool-compliance" / "tool_compliance.py"), str(root / "src" / "tools" / tool)]
        if preflight:
            cmd.append("--preflight")
        result = subprocess.run(cmd)
        raise typer.Exit(result.returncode)

    if full:
        target = "compliance-full"
    elif preflight:
        target = "compliance-preflight"
    else:
        target = "compliance"

    rc = run_make(target)
    raise typer.Exit(rc)


@app.command()
def observability(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show per-file output"),
) -> None:
    """Check LLM observability compliance."""
    args = ["--verbose"] if verbose else []
    rc = run_script("check_observability_compliance.py", args)
    raise typer.Exit(rc)
