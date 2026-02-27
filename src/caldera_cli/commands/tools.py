"""``caldera tools`` — manage analysis tools."""

from __future__ import annotations

import typer

from caldera_cli._shared import run_make, run_script

app = typer.Typer(no_args_is_help=True)


@app.command()
def setup(
    tool: str | None = typer.Option(None, "--tool", "-t", help="Single tool to set up"),
) -> None:
    """Set up tool virtual environments and binaries."""
    if tool:
        from caldera_cli._shared import find_project_root
        import subprocess

        root = find_project_root()
        result = subprocess.run(["make", "-C", str(root / "src" / "tools" / tool), "setup"])
        raise typer.Exit(result.returncode)

    rc = run_make("tools-setup")
    raise typer.Exit(rc)


@app.command()
def analyze(
    tool: str | None = typer.Option(None, "--tool", "-t", help="Single tool to run"),
) -> None:
    """Run analysis for tools."""
    if tool:
        from caldera_cli._shared import find_project_root
        import subprocess

        root = find_project_root()
        result = subprocess.run(["make", "-C", str(root / "src" / "tools" / tool), "analyze"])
        raise typer.Exit(result.returncode)

    rc = run_make("tools-analyze")
    raise typer.Exit(rc)


@app.command()
def test(
    tool: str | None = typer.Option(None, "--tool", "-t", help="Single tool to test"),
) -> None:
    """Run tool tests."""
    if tool:
        from caldera_cli._shared import find_project_root
        import subprocess

        root = find_project_root()
        result = subprocess.run(["make", "-C", str(root / "src" / "tools" / tool), "test"])
        raise typer.Exit(result.returncode)

    rc = run_make("tools-test")
    raise typer.Exit(rc)


@app.command()
def create(
    name: str = typer.Argument(..., help="Tool name"),
    sot_integration: bool = typer.Option(False, "--sot-integration", help="Generate SoT adapter files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating files"),
) -> None:
    """Create a new tool scaffold."""
    args = [name]
    if sot_integration:
        args.append("--sot-integration")
    if dry_run:
        args.append("--dry-run")

    rc = run_script("create-tool.py", args)
    raise typer.Exit(rc)
