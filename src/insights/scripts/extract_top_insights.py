#!/usr/bin/env python3
"""
Extract and display top 3 insights from evaluation results.

This script parses evaluation JSON files that include InsightQualityJudge
results and extracts the recommended top 3 insights along with improvement
proposals and missed issues.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

app = typer.Typer(name="extract-top-insights", help="Extract top 3 insights from evaluation results")
console = Console()


@dataclass
class TopInsight:
    """A single top insight with evidence and rationale."""

    rank: int
    insight: str
    evidence: str
    rationale: str


@dataclass
class ImprovementProposal:
    """A proposal to improve a stated insight."""

    current_insight: str
    issue: str
    proposed_improvement: str


@dataclass
class Top3InsightsResult:
    """Complete top 3 insights extraction result."""

    verdict: str  # PASS, WEAK_PASS, FAIL
    score: float
    sub_scores: dict[str, float]
    recommended_top_3: list[TopInsight]
    improvement_proposals: list[ImprovementProposal]
    missed_critical_issues: list[str]
    reasoning: str = ""

    @classmethod
    def from_evaluation_json(cls, data: dict[str, Any]) -> "Top3InsightsResult":
        """Parse from evaluation JSON output."""
        # Find the insight_quality judge result
        insight_judge = None
        for jr in data.get("llm_results", []):
            if jr.get("judge") == "insight_quality":
                insight_judge = jr
                break

        if not insight_judge:
            raise ValueError("No insight_quality judge found in evaluation results")

        # Determine verdict from score
        score = insight_judge.get("score", 0.0)
        if score >= 4.0:
            verdict = "STRONG_PASS"
        elif score >= 3.5:
            verdict = "PASS"
        elif score >= 3.0:
            verdict = "WEAK_PASS"
        else:
            verdict = "FAIL"

        # Parse top 3 insights
        top_3 = []
        for item in insight_judge.get("recommended_top_3", []):
            top_3.append(TopInsight(
                rank=item.get("rank", 0),
                insight=item.get("insight", ""),
                evidence=item.get("evidence", ""),
                rationale=item.get("rationale", ""),
            ))

        # Parse improvement proposals
        proposals = []
        for item in insight_judge.get("improvement_proposals", []):
            proposals.append(ImprovementProposal(
                current_insight=item.get("current_insight", ""),
                issue=item.get("issue", ""),
                proposed_improvement=item.get("proposed_improvement", ""),
            ))

        return cls(
            verdict=verdict,
            score=score,
            sub_scores=insight_judge.get("sub_scores", {}),
            recommended_top_3=sorted(top_3, key=lambda x: x.rank),
            improvement_proposals=proposals,
            missed_critical_issues=insight_judge.get("missed_critical_issues", []),
            reasoning=insight_judge.get("reasoning", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "verdict": self.verdict,
            "score": self.score,
            "sub_scores": self.sub_scores,
            "recommended_top_3": [
                {
                    "rank": i.rank,
                    "insight": i.insight,
                    "evidence": i.evidence,
                    "rationale": i.rationale,
                }
                for i in self.recommended_top_3
            ],
            "improvement_proposals": [
                {
                    "current_insight": p.current_insight,
                    "issue": p.issue,
                    "proposed_improvement": p.proposed_improvement,
                }
                for p in self.improvement_proposals
            ],
            "missed_critical_issues": self.missed_critical_issues,
            "reasoning": self.reasoning,
        }


def display_rich(result: Top3InsightsResult) -> None:
    """Display results using rich formatting."""
    # Verdict banner
    if result.verdict in ("STRONG_PASS", "PASS"):
        verdict_style = "green"
    elif result.verdict == "WEAK_PASS":
        verdict_style = "yellow"
    else:
        verdict_style = "red"

    console.print()
    console.print(Panel(
        Text(f"{result.verdict} - Score: {result.score:.1f}/5.0", style=f"bold {verdict_style}"),
        title="Insight Quality Verdict",
        border_style=verdict_style,
    ))

    # Sub-scores table
    if result.sub_scores:
        console.print()
        scores_table = Table(title="Sub-dimension Scores", show_header=True)
        scores_table.add_column("Dimension", style="cyan")
        scores_table.add_column("Score", justify="right")

        for dim, score in result.sub_scores.items():
            score_style = "green" if score >= 4.0 else "yellow" if score >= 3.0 else "red"
            scores_table.add_row(dim.replace("_", " ").title(), f"[{score_style}]{score:.1f}[/{score_style}]")

        console.print(scores_table)

    # Top 3 insights
    console.print()
    console.print("[bold]Top 3 Critical Insights[/bold]")
    console.print()

    for insight in result.recommended_top_3:
        rank_style = "bold yellow" if insight.rank == 1 else "cyan"
        console.print(f"[{rank_style}]#{insight.rank}[/{rank_style}] {insight.insight}")
        console.print(f"   [dim]Evidence:[/dim] {insight.evidence}")
        console.print(f"   [dim]Rationale:[/dim] {insight.rationale}")
        console.print()

    # Improvement proposals
    if result.improvement_proposals:
        console.print()
        console.print("[bold]Improvement Proposals[/bold]")
        console.print()

        for i, proposal in enumerate(result.improvement_proposals, 1):
            console.print(f"[yellow]{i}.[/yellow] Current: {proposal.current_insight[:80]}...")
            console.print(f"   [red]Issue:[/red] {proposal.issue}")
            console.print(f"   [green]Improvement:[/green] {proposal.proposed_improvement}")
            console.print()

    # Missed issues
    if result.missed_critical_issues:
        console.print()
        console.print("[bold red]Missed Critical Issues[/bold red]")
        for issue in result.missed_critical_issues:
            console.print(f"  [red]-[/red] {issue}")


def display_text(result: Top3InsightsResult) -> None:
    """Display results as plain text."""
    print(f"\n{'='*60}")
    print(f"INSIGHT QUALITY VERDICT: {result.verdict}")
    print(f"Score: {result.score:.1f}/5.0")
    print(f"{'='*60}\n")

    print("Sub-scores:")
    for dim, score in result.sub_scores.items():
        print(f"  {dim}: {score:.1f}")

    print(f"\n{'='*60}")
    print("TOP 3 CRITICAL INSIGHTS")
    print(f"{'='*60}\n")

    for insight in result.recommended_top_3:
        print(f"#{insight.rank}: {insight.insight}")
        print(f"  Evidence: {insight.evidence}")
        print(f"  Rationale: {insight.rationale}")
        print()

    if result.improvement_proposals:
        print(f"\n{'='*60}")
        print("IMPROVEMENT PROPOSALS")
        print(f"{'='*60}\n")

        for i, proposal in enumerate(result.improvement_proposals, 1):
            print(f"{i}. Current: {proposal.current_insight}")
            print(f"   Issue: {proposal.issue}")
            print(f"   Improvement: {proposal.proposed_improvement}")
            print()

    if result.missed_critical_issues:
        print(f"\n{'='*60}")
        print("MISSED CRITICAL ISSUES")
        print(f"{'='*60}\n")

        for issue in result.missed_critical_issues:
            print(f"  - {issue}")


@app.command()
def extract(
    evaluation_file: Path = typer.Argument(..., help="Path to evaluation JSON file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file for extracted insights"),
    format: str = typer.Option("rich", "--format", "-f", help="Output format: json, text, rich"),
) -> None:
    """Extract top 3 insights from an evaluation JSON file."""
    if not evaluation_file.exists():
        console.print(f"[red]Error:[/red] Evaluation file not found: {evaluation_file}")
        raise typer.Exit(1)

    try:
        data = json.loads(evaluation_file.read_text())
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1)

    try:
        result = Top3InsightsResult.from_evaluation_json(data)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("[dim]Hint: Make sure the evaluation was run with --include-insight-quality[/dim]")
        raise typer.Exit(1)

    # Output based on format
    if format == "json":
        output_json = json.dumps(result.to_dict(), indent=2)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(output_json)
            console.print(f"[green]Results written to:[/green] {output}")
        else:
            print(output_json)
    elif format == "text":
        display_text(result)
    else:  # rich
        display_rich(result)

    # Write output file if specified and format is not json
    if output and format != "json":
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result.to_dict(), indent=2))
        console.print(f"\n[green]JSON results also written to:[/green] {output}")

    # Exit with error code if FAIL
    if result.verdict == "FAIL":
        raise typer.Exit(1)


@app.command()
def validate(
    evaluation_file: Path = typer.Argument(..., help="Path to evaluation JSON file"),
) -> None:
    """Validate that an evaluation file contains insight quality results."""
    if not evaluation_file.exists():
        console.print(f"[red]Error:[/red] Evaluation file not found: {evaluation_file}")
        raise typer.Exit(1)

    try:
        data = json.loads(evaluation_file.read_text())
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1)

    # Check for insight_quality judge
    has_insight_quality = False
    for jr in data.get("llm_results", []):
        if jr.get("judge") == "insight_quality":
            has_insight_quality = True
            break

    if has_insight_quality:
        console.print("[green]Valid:[/green] Evaluation file contains insight_quality results")

        # Show brief summary
        try:
            result = Top3InsightsResult.from_evaluation_json(data)
            console.print(f"  Verdict: {result.verdict}")
            console.print(f"  Score: {result.score:.1f}/5.0")
            console.print(f"  Top 3 insights: {len(result.recommended_top_3)}")
            console.print(f"  Improvement proposals: {len(result.improvement_proposals)}")
            console.print(f"  Missed issues: {len(result.missed_critical_issues)}")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not parse full results: {e}")
    else:
        console.print("[red]Invalid:[/red] No insight_quality judge found")
        console.print("[dim]Hint: Run evaluation with --include-insight-quality flag[/dim]")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
