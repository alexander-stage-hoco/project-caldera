"""
Code size hotspots section - File-level size and complexity analysis.

Uses mart_scc_size_hotspots to identify oversized files that may need
refactoring or splitting, helping with maintainability risk assessment
and technical debt tracking.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CodeSizeHotspotsSection(BaseSection):
    """File-level size and complexity analysis using SCC data."""

    config = SectionConfig(
        name="code_size_hotspots",
        title="Code Size Hotspots",
        description="File-level size and complexity analysis identifying oversized files for refactoring.",
        priority=2.8,  # After blast_radius (2.7), before directory_structure (2.9)
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch code size hotspot data.

        Returns data including:
        - files: Top 30 files by size
        - critical_files: Critical risk only
        - high_files: High risk only
        - summary: Count by risk level, max/avg lines
        - risk_distribution: Count per risk level
        - language_breakdown: Size distribution by language
        - run_statistics: Avg lines, percentiles across all files
        """
        try:
            files = fetcher.fetch("scc_size_hotspots", run_pk, limit=30)
        except Exception:
            files = []

        # Calculate summary statistics
        risk_levels = {"critical": 0, "high": 0, "medium": 0}
        languages: dict[str, int] = {}
        total_lines_list: list[int] = []
        files_over_1000 = 0
        files_over_500 = 0
        files_over_200 = 0
        max_lines = 0
        p99_outliers = 0
        p95_outliers = 0
        p90_outliers = 0

        # Run statistics (from first file with run-level data)
        run_statistics: dict[str, Any] = {}

        for f in files:
            level = f.get("risk_level", "medium")
            if level in risk_levels:
                risk_levels[level] += 1

            lines = f.get("lines_total", 0)
            if lines:
                total_lines_list.append(lines)
                if lines > max_lines:
                    max_lines = lines
                if lines > 1000:
                    files_over_1000 += 1
                if lines > 500:
                    files_over_500 += 1
                if lines > 200:
                    files_over_200 += 1

            lang = f.get("language", "Unknown")
            languages[lang] = languages.get(lang, 0) + 1

            # Count outliers by relative position
            pos = f.get("relative_position", "")
            if pos == "p99_outlier":
                p99_outliers += 1
            elif pos == "p95_outlier":
                p95_outliers += 1
            elif pos == "p90_outlier":
                p90_outliers += 1

            # Extract run statistics from first row
            if not run_statistics and f.get("run_lines_avg") is not None:
                run_statistics = {
                    "avg_lines": round(f.get("run_lines_avg", 0), 2),
                    "stddev_lines": round(f.get("run_lines_stddev", 0), 2),
                    "p50": round(f.get("run_lines_p50", 0), 0),
                    "p75": round(f.get("run_lines_p75", 0), 0),
                    "p90": round(f.get("run_lines_p90", 0), 0),
                    "p95": round(f.get("run_lines_p95", 0), 0),
                    "p99": round(f.get("run_lines_p99", 0), 0),
                    "total_files": f.get("run_total_files", 0),
                }

        # Filter by risk level
        critical_files = [f for f in files if f.get("risk_level") == "critical"]
        high_files = [f for f in files if f.get("risk_level") == "high"]

        # Language breakdown as sorted list
        language_breakdown = sorted(
            [{"language": lang, "count": count} for lang, count in languages.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        # Calculate average lines
        avg_lines = round(sum(total_lines_list) / len(total_lines_list), 2) if total_lines_list else 0

        summary = {
            "total_hotspots": len(files),
            "critical_count": risk_levels["critical"],
            "high_count": risk_levels["high"],
            "medium_count": risk_levels["medium"],
            "max_lines": max_lines,
            "avg_lines": avg_lines,
            "files_over_1000": files_over_1000,
            "files_over_500": files_over_500,
            "files_over_200": files_over_200,
            "p99_outliers": p99_outliers,
            "p95_outliers": p95_outliers,
            "p90_outliers": p90_outliers,
        }

        return {
            "files": files,
            "critical_files": critical_files,
            "high_files": high_files,
            "summary": summary,
            "risk_distribution": risk_levels,
            "language_breakdown": language_breakdown,
            "run_statistics": run_statistics,
            "has_data": len(files) > 0,
            "has_critical": risk_levels["critical"] > 0,
            "has_high": risk_levels["high"] > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "code_size_hotspots.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No code size hotspot data available - SCC tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "files": [],
            "critical_files": [],
            "high_files": [],
            "summary": {
                "total_hotspots": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "max_lines": 0,
                "avg_lines": 0,
                "files_over_1000": 0,
                "files_over_500": 0,
                "files_over_200": 0,
                "p99_outliers": 0,
                "p95_outliers": 0,
                "p90_outliers": 0,
            },
            "risk_distribution": {"critical": 0, "high": 0, "medium": 0},
            "language_breakdown": [],
            "run_statistics": {},
            "has_data": False,
            "has_critical": False,
            "has_high": False,
        }
