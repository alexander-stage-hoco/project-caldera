"""
Function complexity hotspots section - Function-level CCN analysis.

Uses mart_complexity_hotspots to identify functions with high cyclomatic
complexity, providing more granular insights than file-level metrics.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class FunctionComplexitySection(BaseSection):
    """Function-level complexity analysis using CCN metrics."""

    config = SectionConfig(
        name="function_complexity",
        title="Function Complexity Hotspots",
        description="Function-level cyclomatic complexity analysis identifying the most complex individual functions.",
        priority=2.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch function complexity data.

        Returns data including:
        - functions: Top 30 functions by CCN
        - summary: Count by risk level, avg CCN, files affected
        - files_with_complex_functions: Grouped by file
        - run_statistics: Repository-wide CCN statistics
        """
        try:
            functions = fetcher.fetch("function_complexity_hotspots", run_pk, limit=30)
        except Exception:
            functions = []

        # Calculate summary statistics
        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        files_affected: set[str] = set()
        ccn_values = []

        for f in functions:
            level = f.get("risk_level", "low")
            if level in risk_levels:
                risk_levels[level] += 1

            files_affected.add(f.get("relative_path", ""))
            if f.get("ccn"):
                ccn_values.append(f["ccn"])

        # Group by file
        files_with_functions: dict[str, list] = {}
        for f in functions:
            path = f.get("relative_path", "unknown")
            if path not in files_with_functions:
                files_with_functions[path] = []
            files_with_functions[path].append(f)

        # Sort files by max CCN in file
        sorted_files = sorted(
            files_with_functions.items(),
            key=lambda x: max(f.get("ccn", 0) for f in x[1]),
            reverse=True,
        )[:10]

        # Extract run statistics from first function (all have same run stats)
        run_stats = {}
        if functions:
            first = functions[0]
            run_stats = {
                "avg_ccn": first.get("run_ccn_avg"),
                "stddev": first.get("run_ccn_stddev"),
                "p50": first.get("run_ccn_p50"),
                "p75": first.get("run_ccn_p75"),
                "p90": first.get("run_ccn_p90"),
                "p95": first.get("run_ccn_p95"),
                "p99": first.get("run_ccn_p99"),
                "total_functions": first.get("run_total_functions"),
            }

        summary = {
            "critical_count": risk_levels["critical"],
            "high_count": risk_levels["high"],
            "medium_count": risk_levels["medium"],
            "low_count": risk_levels["low"],
            "total_functions": len(functions),
            "files_affected": len(files_affected),
            "avg_ccn": round(sum(ccn_values) / len(ccn_values), 1) if ccn_values else 0,
            "max_ccn": max(ccn_values) if ccn_values else 0,
        }

        # Critical functions (CCN >= 50)
        critical_functions = [f for f in functions if f.get("risk_level") == "critical"]
        high_functions = [f for f in functions if f.get("risk_level") == "high"]

        return {
            "functions": functions,
            "critical_functions": critical_functions,
            "high_functions": high_functions,
            "summary": summary,
            "run_statistics": run_stats,
            "files_with_complex_functions": sorted_files,
            "has_data": len(functions) > 0,
            "has_critical": risk_levels["critical"] > 0,
            "has_high": risk_levels["high"] > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "function_complexity.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No function complexity data available - lizard tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "functions": [],
            "critical_functions": [],
            "high_functions": [],
            "summary": {
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "total_functions": 0,
                "files_affected": 0,
                "avg_ccn": 0,
                "max_ccn": 0,
            },
            "run_statistics": {},
            "files_with_complex_functions": [],
            "has_data": False,
            "has_critical": False,
            "has_high": False,
        }
