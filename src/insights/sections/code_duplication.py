"""
Code duplication section - Copy-paste detection analysis.

Uses mart_pmd_cpd_clone_hotspots to identify duplicated code blocks,
their impact, and affected files.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CodeDuplicationSection(BaseSection):
    """Code duplication analysis using PMD-CPD clone detection."""

    config = SectionConfig(
        name="code_duplication",
        title="Code Duplication",
        description="Copy-paste detection identifying duplicated code blocks and their impact on maintainability.",
        priority=8.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch code duplication data.

        Returns data including:
        - clones: Top 20 duplication instances
        - summary: Total duplicated lines, affected files, clone count
        - cross_file_clones: Clones spanning multiple files
        - risk_distribution: Clones by risk level
        """
        try:
            clones = fetcher.fetch("duplication_hotspots", run_pk, limit=20)
        except Exception:
            clones = []

        # Calculate summary statistics
        total_duplicated_lines = 0
        files_affected: set[str] = set()
        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        cross_file_clones = []

        for c in clones:
            total_duplicated_lines += c.get("total_duplicated_lines", 0)

            level = c.get("risk_level", "low")
            if level in risk_levels:
                risk_levels[level] += 1

            if c.get("is_cross_file"):
                cross_file_clones.append(c)

        # Get clone statistics from first clone
        total_clones = 0
        if clones:
            # Sum up occurrence counts
            total_clones = sum(c.get("occurrence_count", 0) for c in clones)

        summary = {
            "total_clones": len(clones),
            "total_occurrences": total_clones,
            "total_duplicated_lines": total_duplicated_lines,
            "cross_file_count": len(cross_file_clones),
            "critical_count": risk_levels["critical"],
            "high_count": risk_levels["high"],
            "medium_count": risk_levels["medium"],
            "low_count": risk_levels["low"],
        }

        # Largest clones by lines
        largest_clones = sorted(clones, key=lambda x: x.get("lines", 0), reverse=True)[:10]

        # Most impactful clones (by total duplicated lines)
        most_impactful = sorted(
            clones,
            key=lambda x: x.get("total_duplicated_lines", 0),
            reverse=True,
        )[:10]

        return {
            "clones": clones,
            "largest_clones": largest_clones,
            "most_impactful": most_impactful,
            "cross_file_clones": cross_file_clones[:10],
            "summary": summary,
            "has_data": len(clones) > 0,
            "has_critical": risk_levels["critical"] > 0,
            "has_cross_file": len(cross_file_clones) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "code_duplication.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        # Duplication data is optional - no errors if empty
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "clones": [],
            "largest_clones": [],
            "most_impactful": [],
            "cross_file_clones": [],
            "summary": {
                "total_clones": 0,
                "total_occurrences": 0,
                "total_duplicated_lines": 0,
                "cross_file_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            },
            "has_data": False,
            "has_critical": False,
            "has_cross_file": False,
        }
