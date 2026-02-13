"""
Report Formatter for Layout Scanner Evaluation.

Provides multiple output formats for evaluation results:
- table: Colored terminal output with box-drawing characters
- summary: Compact text summary
- markdown: Markdown formatted report
- json: JSON output (default behavior)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .checks import CheckCategory, CheckResult, DimensionResult


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"


# Category display names
CATEGORY_NAMES = {
    CheckCategory.OUTPUT_QUALITY: "Output Quality",
    CheckCategory.ACCURACY: "Accuracy",
    CheckCategory.CLASSIFICATION: "Classification",
    CheckCategory.PERFORMANCE: "Performance",
    CheckCategory.EDGE_CASES: "Edge Cases",
    CheckCategory.GIT_METADATA: "Git Metadata",
    CheckCategory.CONTENT_METADATA: "Content Metadata",
}

# Recommendations based on check failures
RECOMMENDATIONS = {
    "OQ": "Review output structure and ensure all required fields are present",
    "AC": "Check file counting and path normalization logic",
    "CL": "Review classification rules and patterns",
    "PF": "Consider optimizing I/O operations or reducing file processing",
    "EC": "Test with edge case repositories (empty dirs, symlinks, unicode)",
    "GT": "Verify git metadata extraction and date parsing",
    "CT": "Check content analysis for binary detection and line counting",
}


@dataclass
class EvaluationResult:
    """Structured evaluation result for formatting."""

    repository: str
    timestamp: str
    overall_score: float
    decision: str
    dimensions: list[DimensionResult]
    total_checks: int
    passed_checks: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationResult":
        """Create from evaluation output dictionary."""
        dimensions = []
        for dim_data in data.get("dimensions", []):
            checks = [
                CheckResult(
                    check_id=c["check_id"],
                    name=c["name"],
                    category=CheckCategory(c["category"]),
                    passed=c["passed"],
                    score=c["score"],
                    message=c["message"],
                    evidence=c.get("evidence", {}),
                )
                for c in dim_data.get("checks", [])
            ]
            dimensions.append(
                DimensionResult(
                    category=CheckCategory(dim_data["category"]),
                    checks=checks,
                    passed_count=dim_data["passed_count"],
                    total_count=dim_data["total_count"],
                    score=dim_data["score"],
                )
            )

        summary = data.get("summary", {})
        return cls(
            repository=data.get("repository", "unknown"),
            timestamp=data.get("timestamp", ""),
            overall_score=data.get("overall_score", 0.0),
            decision=data.get("decision", "UNKNOWN"),
            dimensions=dimensions,
            total_checks=summary.get("total_checks", 0),
            passed_checks=summary.get("passed_checks", 0),
        )


class ReportFormatter:
    """Formats evaluation results in various output formats."""

    def __init__(self, use_color: bool = True):
        """
        Initialize formatter.

        Args:
            use_color: Whether to use ANSI colors in output
        """
        self.use_color = use_color

    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def _status_icon(self, passed: bool) -> str:
        """Get status icon for pass/fail."""
        if passed:
            return self._color("✓", Colors.GREEN)
        return self._color("✗", Colors.RED)

    def _score_color(self, score: float) -> str:
        """Get color based on score value."""
        if score >= 4.0:
            return Colors.GREEN
        elif score >= 3.0:
            return Colors.YELLOW
        return Colors.RED

    def _decision_color(self, decision: str) -> str:
        """Get color based on decision."""
        if decision == "STRONG_PASS":
            return Colors.GREEN
        elif decision == "PASS":
            return Colors.GREEN
        elif decision == "WEAK_PASS":
            return Colors.YELLOW
        return Colors.RED

    def format(
        self,
        result: EvaluationResult,
        format_type: str = "table",
        category_filter: str | None = None,
        status_filter: str = "all",
        verbose: bool = False,
    ) -> str:
        """
        Format evaluation result.

        Args:
            result: Evaluation result to format
            format_type: Output format (table, summary, markdown, json)
            category_filter: Filter to specific category
            status_filter: Filter by status (passed, failed, all)
            verbose: Show detailed evidence

        Returns:
            Formatted string
        """
        # Filter dimensions if category specified
        dimensions = result.dimensions
        if category_filter:
            dimensions = [
                d for d in dimensions if d.category.value == category_filter
            ]

        # Filter checks by status
        if status_filter != "all":
            filtered_dims = []
            for dim in dimensions:
                if status_filter == "passed":
                    checks = [c for c in dim.checks if c.passed]
                else:  # failed
                    checks = [c for c in dim.checks if not c.passed]
                if checks:
                    filtered_dims.append(
                        DimensionResult(
                            category=dim.category,
                            checks=checks,
                            passed_count=sum(1 for c in checks if c.passed),
                            total_count=len(checks),
                            score=dim.score,
                        )
                    )
            dimensions = filtered_dims

        # Create filtered result
        filtered_result = EvaluationResult(
            repository=result.repository,
            timestamp=result.timestamp,
            overall_score=result.overall_score,
            decision=result.decision,
            dimensions=dimensions,
            total_checks=result.total_checks,
            passed_checks=result.passed_checks,
        )

        if format_type == "table":
            return self._format_table(filtered_result, verbose)
        elif format_type == "summary":
            return self._format_summary(filtered_result, verbose)
        elif format_type == "markdown":
            return self._format_markdown(filtered_result, verbose)
        else:  # json
            return self._format_json(filtered_result)

    def _format_table(self, result: EvaluationResult, verbose: bool) -> str:
        """Format as colored terminal table."""
        lines = []
        width = 70

        # Header box
        lines.append(self._color("╔" + "═" * width + "╗", Colors.CYAN))
        title = "Layout Scanner Evaluation"
        lines.append(
            self._color("║", Colors.CYAN)
            + self._color(title.center(width), Colors.BOLD)
            + self._color("║", Colors.CYAN)
        )
        repo_line = f"Repository: {result.repository}"
        lines.append(
            self._color("║", Colors.CYAN)
            + repo_line.center(width)
            + self._color("║", Colors.CYAN)
        )
        lines.append(self._color("╠" + "═" * width + "╣", Colors.CYAN))

        # Score summary line
        score_str = f"Score: {result.overall_score:.1f}/5.0"
        decision_str = result.decision
        checks_str = f"{result.passed_checks}/{result.total_checks} passed"

        score_colored = self._color(score_str, self._score_color(result.overall_score))
        decision_colored = self._color(
            decision_str, self._decision_color(result.decision)
        )

        summary_line = f"  {score_colored}  │  {decision_colored}  │  {checks_str}  "
        # Calculate actual display width (excluding ANSI codes)
        lines.append(
            self._color("║", Colors.CYAN)
            + summary_line.ljust(width + 20)  # Extra for ANSI codes
            + self._color("║", Colors.CYAN)
        )
        lines.append(self._color("╚" + "═" * width + "╝", Colors.CYAN))
        lines.append("")

        # Dimension sections
        for dim in result.dimensions:
            lines.extend(self._format_dimension_table(dim, verbose))
            lines.append("")

        # Recommendations for failures
        failed_checks = []
        for dim in result.dimensions:
            failed_checks.extend([c for c in dim.checks if not c.passed])

        if failed_checks:
            lines.append(self._color("Recommendations:", Colors.BOLD))
            prefixes_seen = set()
            for check in failed_checks:
                prefix = check.check_id.split("-")[0]
                if prefix not in prefixes_seen:
                    prefixes_seen.add(prefix)
                    rec = RECOMMENDATIONS.get(prefix, "Review check documentation")
                    lines.append(f"  • {rec}")

        return "\n".join(lines)

    def _format_dimension_table(
        self, dim: DimensionResult, verbose: bool
    ) -> list[str]:
        """Format a single dimension as a table section."""
        lines = []
        width = 70
        name = CATEGORY_NAMES.get(dim.category, dim.category.value)

        # Header
        header_left = f"─ {name} ({dim.passed_count}/{dim.total_count} passed) "
        header_right = f" Score: {dim.score:.1f} ─"
        padding = width - len(header_left) - len(header_right)

        lines.append(
            self._color("┌" + header_left + "─" * padding + header_right + "┐", Colors.DIM)
        )

        # Check rows
        for check in dim.checks:
            icon = self._status_icon(check.passed)
            check_id = check.check_id.ljust(6)
            name = check.name[:22].ljust(22)
            message = check.message[:35]

            row = f"│ {icon} {check_id} {name} {message}"
            # Pad to width
            display_len = len(row) - (8 if self.use_color else 0)  # Adjust for ANSI
            padding = width - display_len + 1
            lines.append(row + " " * max(0, padding) + self._color("│", Colors.DIM))

            # Show evidence if verbose and check failed
            if verbose and not check.passed and check.evidence:
                evidence_str = json.dumps(check.evidence, indent=2)
                for ev_line in evidence_str.split("\n")[:5]:  # Limit lines
                    ev_row = f"│   {self._color(ev_line[:65], Colors.DIM)}"
                    lines.append(ev_row.ljust(width + 10) + self._color("│", Colors.DIM))

        # Footer
        lines.append(self._color("└" + "─" * width + "┘", Colors.DIM))

        return lines

    def _format_summary(self, result: EvaluationResult, verbose: bool) -> str:
        """Format as compact text summary."""
        lines = []

        lines.append("Layout Scanner Evaluation Summary")
        lines.append("=" * 35)
        lines.append(f"Repository: {result.repository}")
        if result.timestamp:
            lines.append(f"Timestamp:  {result.timestamp}")
        lines.append("")

        # Overall score
        score_str = f"{result.overall_score:.1f}/5.0 ({result.decision})"
        lines.append(f"Overall Score: {self._color(score_str, self._score_color(result.overall_score))}")
        lines.append("")

        # Dimension scores
        lines.append("Dimension Scores:")
        for dim in result.dimensions:
            name = CATEGORY_NAMES.get(dim.category, dim.category.value)
            dots = "." * (20 - len(name))
            score = f"{dim.score:.1f}  ({dim.passed_count}/{dim.total_count} checks)"
            lines.append(f"  {name} {dots} {score}")

        # Failed checks
        failed_checks = []
        for dim in result.dimensions:
            failed_checks.extend([c for c in dim.checks if not c.passed])

        if failed_checks:
            lines.append("")
            lines.append(f"Failed Checks: {len(failed_checks)}")
            for check in failed_checks:
                lines.append(f"  {self._status_icon(False)} {check.check_id}: {check.name}")
                lines.append(f"    {check.message}")
                if verbose and check.evidence:
                    for key, value in list(check.evidence.items())[:3]:
                        lines.append(f"    {key}: {value}")

        return "\n".join(lines)

    def _format_markdown(self, result: EvaluationResult, verbose: bool) -> str:
        """Format as markdown report."""
        lines = []

        lines.append(f"# Evaluation Report: {result.repository}")
        lines.append("")
        lines.append(
            f"**Score:** {result.overall_score:.1f}/5.0 | "
            f"**Decision:** {result.decision} | "
            f"**Date:** {result.timestamp[:10] if result.timestamp else 'N/A'}"
        )
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Dimension | Score | Passed | Total |")
        lines.append("|-----------|-------|--------|-------|")
        for dim in result.dimensions:
            name = CATEGORY_NAMES.get(dim.category, dim.category.value)
            lines.append(
                f"| {name} | {dim.score:.1f} | {dim.passed_count} | {dim.total_count} |"
            )
        lines.append("")

        # Failed checks detail
        failed_checks = []
        for dim in result.dimensions:
            failed_checks.extend([c for c in dim.checks if not c.passed])

        if failed_checks:
            lines.append("## Failed Checks")
            lines.append("")
            for check in failed_checks:
                lines.append(f"### {check.check_id}: {check.name}")
                lines.append("")
                lines.append(f"- **Status:** FAILED")
                lines.append(f"- **Message:** {check.message}")
                if verbose and check.evidence:
                    lines.append(f"- **Evidence:**")
                    lines.append("```json")
                    lines.append(json.dumps(check.evidence, indent=2))
                    lines.append("```")
                lines.append("")
        else:
            lines.append("## All Checks Passed")
            lines.append("")
            lines.append("No failures detected.")

        return "\n".join(lines)

    def _format_json(self, result: EvaluationResult) -> str:
        """Format as JSON."""
        data = {
            "repository": result.repository,
            "timestamp": result.timestamp,
            "overall_score": result.overall_score,
            "decision": result.decision,
            "summary": {
                "total_checks": result.total_checks,
                "passed_checks": result.passed_checks,
            },
            "dimensions": [
                {
                    "category": dim.category.value,
                    "score": dim.score,
                    "passed_count": dim.passed_count,
                    "total_count": dim.total_count,
                    "checks": [
                        {
                            "check_id": c.check_id,
                            "name": c.name,
                            "passed": c.passed,
                            "score": c.score,
                            "message": c.message,
                            "evidence": c.evidence,
                        }
                        for c in dim.checks
                    ],
                }
                for dim in result.dimensions
            ],
        }
        return json.dumps(data, indent=2)


def get_recommendations(failed_checks: list[CheckResult]) -> list[str]:
    """
    Generate recommendations based on failed checks.

    Args:
        failed_checks: List of failed check results

    Returns:
        List of recommendation strings
    """
    recommendations = []
    prefixes_seen = set()

    for check in failed_checks:
        prefix = check.check_id.split("-")[0]
        if prefix not in prefixes_seen:
            prefixes_seen.add(prefix)
            rec = RECOMMENDATIONS.get(prefix)
            if rec:
                recommendations.append(rec)

    return recommendations
