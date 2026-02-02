#!/usr/bin/env python3
"""
Evaluation orchestrator for Insights reports.

Combines programmatic checks (60% weight) with LLM judges (40% weight).
"""

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="evaluate", help="Evaluate Insights reports")
console = Console()


def configure_observability(verbose: bool = False, log_dir: Path | None = None) -> None:
    """Configure LLM observability logging."""
    from shared.observability import ObservabilityConfig, set_config

    config = ObservabilityConfig(
        enabled=True,
        log_dir=log_dir or Path("output/llm_logs"),
        log_to_console=verbose,
        log_to_file=True,
        include_prompts=True,
        include_responses=True,
    )
    set_config(config)

    if verbose:
        # Configure structlog for console output
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(min_level=20),  # INFO
        )


@dataclass
class EvaluationSummary:
    """Combined evaluation summary."""

    # Overall
    overall_score: float
    pass_status: str

    # Programmatic checks (60% weight)
    programmatic_score: float
    checks_passed: int
    checks_failed: int
    checks_skipped: int

    # LLM evaluation (40% weight)
    llm_score: float | None
    llm_provider: str | None
    llm_trace_id: str | None = None  # Trace ID for LLM observability

    # Details
    check_results: list[dict[str, Any]] = field(default_factory=list)
    llm_results: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    # Metadata
    evaluated_at: str = ""
    report_path: str = ""
    run_pk: int | None = None


def run_programmatic_checks(
    report_content: str,
    report_data: dict[str, Any],
    db_data: dict[str, Any],
    format: str,
) -> tuple[float, list[dict[str, Any]]]:
    """Run all programmatic checks and return score and results."""
    from ..scripts.checks import run_all_checks, CheckResult

    # Run checks
    results = run_all_checks(
        report_content=report_content,
        report_data=report_data,
        db_data=db_data,
        format=format,
    )

    # Calculate score
    total_score = 0.0
    total_weight = 0.0
    results_dicts = []

    for result in results:
        results_dicts.append({
            "check_id": result.check_id,
            "name": result.name,
            "result": result.result.value,
            "score": result.score,
            "message": result.message,
        })

        if result.result != CheckResult.SKIP:
            total_score += result.score
            total_weight += 1.0

    avg_score = total_score / total_weight if total_weight > 0 else 0.0
    # Convert 0-1 score to 1-5 scale
    scaled_score = 1.0 + (avg_score * 4.0)

    return scaled_score, results_dicts


def run_llm_evaluation(
    report_content: str,
    context: dict[str, Any],
    provider: str,
    model: str | None,
    include_insight_quality: bool = False,
) -> tuple[float, list[dict[str, Any]], list[str], str | None]:
    """Run LLM evaluation and return score, results, suggestions, and trace_id."""
    from ..evaluation.llm.orchestrator import LLMOrchestrator

    orchestrator = LLMOrchestrator(
        provider_name=provider,
        model=model,
        include_insight_quality=include_insight_quality,
    )
    result = orchestrator.evaluate(report_content, context)

    judge_results = []
    for jr in result.judge_results:
        jr_dict: dict[str, Any] = {
            "judge": jr.judge_name,
            "score": jr.overall_score,
            "sub_scores": jr.sub_scores,
            "reasoning": jr.reasoning,
        }
        # Include extended fields from InsightQualityResult if present
        if hasattr(jr, "recommended_top_3"):
            jr_dict["recommended_top_3"] = jr.recommended_top_3
        if hasattr(jr, "improvement_proposals"):
            jr_dict["improvement_proposals"] = jr.improvement_proposals
        if hasattr(jr, "missed_critical_issues"):
            jr_dict["missed_critical_issues"] = jr.missed_critical_issues
        judge_results.append(jr_dict)

    return result.overall_score, judge_results, result.combined_suggestions, result.trace_id


def extract_report_data(report_content: str, format: str) -> dict[str, Any]:
    """Extract structured data from report content for validation."""
    if format == "html":
        return _extract_from_html(report_content)
    elif format == "md":
        return _extract_from_markdown(report_content)
    return {}


def _extract_from_html(content: str) -> dict[str, Any]:
    """Parse HTML report to extract key metrics."""
    import re

    data: dict[str, Any] = {"repo_health": {}}

    # Extract total files: look for pattern like "317" after "Total Files"
    # The HTML structure is: <div class="label">Total Files</div><div class="value">317</div>
    total_files_match = re.search(
        r'Total Files</div>\s*<div[^>]*class="value"[^>]*>([0-9,]+)</div>',
        content,
        re.IGNORECASE,
    )
    if total_files_match:
        data["repo_health"]["total_files"] = int(
            total_files_match.group(1).replace(",", "")
        )

    # Extract total LOC
    total_loc_match = re.search(
        r'Total Lines[^<]*</div>\s*<div[^>]*class="value"[^>]*>([0-9,]+)</div>',
        content,
        re.IGNORECASE,
    )
    if total_loc_match:
        data["repo_health"]["total_loc"] = int(
            total_loc_match.group(1).replace(",", "")
        )

    # Extract total_code from sublabel: "64,718 code, 4,568 comments"
    total_code_match = re.search(
        r'<div[^>]*class="sublabel"[^>]*>([0-9,]+)\s*code',
        content,
        re.IGNORECASE,
    )
    if total_code_match:
        data["repo_health"]["total_code"] = int(
            total_code_match.group(1).replace(",", "")
        )

    # Extract average complexity - use key "avg_ccn" to match check expectations
    avg_ccn_match = re.search(
        r'Average Complexity[^<]*</div>\s*<div[^>]*class="value"[^>]*>([0-9.]+)</div>',
        content,
        re.IGNORECASE,
    )
    if avg_ccn_match:
        data["repo_health"]["avg_ccn"] = float(avg_ccn_match.group(1))

    # Detect section presence for completeness checks
    if 'id="file_hotspots"' in content:
        data["file_hotspots"] = {"present": True}

    if 'id="vulnerabilities"' in content:
        data["vulnerabilities"] = {"present": True}

    return data


def _extract_from_markdown(content: str) -> dict[str, Any]:
    """Parse Markdown report to extract key metrics."""
    import re

    data: dict[str, Any] = {"repo_health": {}}

    # Markdown table format: | Metric | Value |
    # Look for "Total Files" row
    total_files_match = re.search(
        r'\|\s*Total Files\s*\|\s*([0-9,]+)\s*\|',
        content,
        re.IGNORECASE,
    )
    if total_files_match:
        data["repo_health"]["total_files"] = int(
            total_files_match.group(1).replace(",", "")
        )

    # Look for "Total Lines" or "Total LOC" row
    total_loc_match = re.search(
        r'\|\s*Total (?:Lines|LOC)[^|]*\|\s*([0-9,]+)\s*\|',
        content,
        re.IGNORECASE,
    )
    if total_loc_match:
        data["repo_health"]["total_loc"] = int(
            total_loc_match.group(1).replace(",", "")
        )

    # Look for "Average Complexity" row - use key "avg_ccn" to match check expectations
    avg_ccn_match = re.search(
        r'\|\s*Average Complexity[^|]*\|\s*([0-9.]+)\s*\|',
        content,
        re.IGNORECASE,
    )
    if avg_ccn_match:
        data["repo_health"]["avg_ccn"] = float(avg_ccn_match.group(1))

    return data


def fetch_db_data(db_path: Path, run_pk: int) -> dict[str, Any]:
    """Fetch ground truth data from database."""
    from ..data_fetcher import DataFetcher

    fetcher = DataFetcher(db_path)

    data: dict[str, Any] = {}

    try:
        # Get repo health data
        health = fetcher.fetch("repo_health", run_pk)
        if health:
            data.update(health[0])

        # Get vulnerability count
        vulns = fetcher.fetch("vulnerability_summary", run_pk)
        data["total_vulnerabilities"] = sum(v.get("count", 0) for v in vulns)
        data["vulnerability_summary"] = vulns

    except Exception as e:
        console.print(f"[yellow]Warning: Could not fetch DB data: {e}[/yellow]")

    return data


@app.command()
def evaluate(
    report: Path = typer.Argument(..., help="Path to report file"),
    db: Path = typer.Option(None, "--db", "-d", help="Path to DuckDB database"),
    run_pk: int = typer.Option(None, "--run-pk", "-r", help="Run PK for ground truth comparison"),
    provider: str = typer.Option("claude_code", "--provider", "-p", help="LLM provider"),
    model: str = typer.Option(None, "--model", "-m", help="Model override"),
    skip_llm: bool = typer.Option(False, "--skip-llm", help="Skip LLM evaluation"),
    include_insight_quality: bool = typer.Option(
        False,
        "--include-insight-quality",
        help="Include InsightQualityJudge for top 3 insight extraction",
    ),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose LLM logging"),
    log_dir: Path = typer.Option(None, "--log-dir", help="Directory for LLM interaction logs"),
) -> None:
    """Evaluate an Insights report."""
    # Configure observability
    configure_observability(verbose=verbose, log_dir=log_dir)

    if not report.exists():
        console.print(f"[red]Error:[/red] Report not found: {report}")
        raise typer.Exit(1)

    # Determine format from extension
    format = "html" if report.suffix.lower() == ".html" else "md"

    # Read report
    report_content = report.read_text()

    # Extract data from report
    report_data = extract_report_data(report_content, format)

    # Fetch DB data if available
    db_data: dict[str, Any] = {}
    if db and db.exists() and run_pk:
        db_data = fetch_db_data(db, run_pk)

    # Run programmatic checks
    console.print("[bold]Running programmatic checks...[/bold]")
    prog_score, check_results = run_programmatic_checks(
        report_content=report_content,
        report_data=report_data,
        db_data=db_data,
        format=format,
    )

    passed = sum(1 for r in check_results if r["result"] == "pass")
    failed = sum(1 for r in check_results if r["result"] == "fail")
    skipped = sum(1 for r in check_results if r["result"] == "skip")

    console.print(f"  Programmatic: {prog_score:.2f}/5.0 ({passed} passed, {failed} failed, {skipped} skipped)")

    # Run LLM evaluation
    llm_score = None
    llm_results: list[dict[str, Any]] = []
    suggestions: list[str] = []
    llm_provider = None
    trace_id = None

    if not skip_llm:
        judge_info = f"({provider})"
        if include_insight_quality:
            judge_info = f"({provider}, with insight quality)"
        console.print(f"[bold]Running LLM evaluation {judge_info}...[/bold]")
        try:
            context = {"format": format, "run_pk": run_pk}
            llm_score, llm_results, suggestions, trace_id = run_llm_evaluation(
                report_content=report_content,
                context=context,
                provider=provider,
                model=model,
                include_insight_quality=include_insight_quality,
            )
            llm_provider = provider
            console.print(f"  LLM: {llm_score:.2f}/5.0")

            for jr in llm_results:
                console.print(f"    - {jr['judge']}: {jr['score']:.1f}/5.0")

            if trace_id:
                console.print(f"  [dim]Trace ID: {trace_id}[/dim]")

        except Exception as e:
            console.print(f"[yellow]LLM evaluation failed: {e}[/yellow]")

    # Calculate overall score (60% programmatic, 40% LLM)
    if llm_score is not None:
        overall_score = (prog_score * 0.6) + (llm_score * 0.4)
    else:
        overall_score = prog_score

    # Determine pass status
    if overall_score >= 4.0:
        pass_status = "STRONG_PASS"
        status_style = "green"
    elif overall_score >= 3.5:
        pass_status = "PASS"
        status_style = "green"
    elif overall_score >= 3.0:
        pass_status = "WEAK_PASS"
        status_style = "yellow"
    else:
        pass_status = "FAIL"
        status_style = "red"

    # Print summary
    console.print()
    console.print(f"[bold]Overall Score:[/bold] [{status_style}]{overall_score:.2f}/5.0 ({pass_status})[/{status_style}]")

    if suggestions:
        console.print()
        console.print("[bold]Suggestions:[/bold]")
        for s in suggestions[:5]:
            console.print(f"  • {s}")

    # Create summary
    summary = EvaluationSummary(
        overall_score=overall_score,
        pass_status=pass_status,
        programmatic_score=prog_score,
        checks_passed=passed,
        checks_failed=failed,
        checks_skipped=skipped,
        llm_score=llm_score,
        llm_provider=llm_provider,
        llm_trace_id=trace_id,
        check_results=check_results,
        llm_results=llm_results,
        suggestions=suggestions,
        evaluated_at=datetime.now().isoformat(),
        report_path=str(report),
        run_pk=run_pk,
    )

    # Write output
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(asdict(summary), indent=2))
        console.print(f"\n[green]Results written to:[/green] {output}")

    # Exit with appropriate code
    if pass_status == "FAIL":
        raise typer.Exit(1)


@app.command("list-checks")
def list_checks() -> None:
    """List available evaluation checks."""
    from ..scripts.checks import get_all_checks

    table = Table(title="Evaluation Checks")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Dimension")
    table.add_column("Weight", justify="right")

    for check in get_all_checks():
        table.add_row(
            check.check_id,
            check.name,
            check.dimension,
            f"{check.weight:.1f}",
        )

    console.print(table)


@app.command("list-judges")
def list_judges() -> None:
    """List available LLM judges."""
    from ..evaluation.llm.orchestrator import LLMOrchestrator

    orchestrator = LLMOrchestrator()
    judges = orchestrator.list_judges()

    table = Table(title="LLM Judges")
    table.add_column("Name", style="cyan")
    table.add_column("Weight", justify="right")
    table.add_column("Sub-dimensions")

    for judge in judges:
        dims = ", ".join(f"{k}({v:.0%})" for k, v in judge["sub_dimensions"].items())
        table.add_row(
            judge["name"],
            f"{judge['weight']:.0%}",
            dims,
        )

    console.print(table)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
