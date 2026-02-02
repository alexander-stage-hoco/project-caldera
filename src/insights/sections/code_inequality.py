"""
Code inequality analysis section - Gini, Palma, and concentration metrics.

Identifies directories with uneven code distribution using inequality metrics
from Caldera's distribution rollups.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CodeInequalitySection(BaseSection):
    """Code inequality analysis using Gini, Palma, and concentration metrics."""

    config = SectionConfig(
        name="code_inequality",
        title="Code Inequality Analysis",
        description="Identifies directories with uneven code distribution using Gini coefficient, Palma ratio, and concentration metrics.",
        priority=11,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch code inequality data.

        Returns data including:
        - high_gini_directories: Top directories by Gini coefficient (>= 0.3)
        - high_palma_directories: Top directories by Palma ratio (>= 2.0)
        - concentration_analysis: Directories where top 20% >= 50% of total
        - cross_tool_correlation: LOC Gini vs CCN Gini comparison
        - summary: Aggregate statistics
        """
        # Fetch high Gini directories
        try:
            high_gini = fetcher.fetch("inequality_by_gini", run_pk)
        except Exception:
            high_gini = []

        # Fetch high Palma directories
        try:
            high_palma = fetcher.fetch("inequality_by_palma", run_pk)
        except Exception:
            high_palma = []

        # Fetch concentration analysis
        try:
            concentration = fetcher.fetch("inequality_concentration", run_pk)
        except Exception:
            concentration = []

        # Fetch cross-tool correlation
        try:
            cross_tool = fetcher.fetch("inequality_cross_tool", run_pk)
        except Exception:
            cross_tool = []

        # Classify directories by severity
        critical_dirs = [d for d in high_gini if d.get("classification") == "critical"]
        warning_dirs = [d for d in high_gini if d.get("classification") == "warning"]
        healthy_dirs = [d for d in high_gini if d.get("classification") == "healthy"]

        # Calculate summary statistics
        all_gini_values = [d.get("gini", 0) for d in high_gini if d.get("gini")]
        all_palma_values = [d.get("palma_ratio", 0) for d in high_palma if d.get("palma_ratio")]

        summary = {
            "critical_count": len(critical_dirs),
            "warning_count": len(warning_dirs),
            "healthy_count": len(healthy_dirs),
            "total_flagged": len(high_gini),
            "avg_gini": round(sum(all_gini_values) / len(all_gini_values), 3) if all_gini_values else 0,
            "max_gini": max(all_gini_values) if all_gini_values else 0,
            "max_palma": max(all_palma_values) if all_palma_values else 0,
            "concentration_count": len(concentration),
            "cross_tool_count": len(cross_tool),
        }

        # Count cross-tool patterns
        pattern_counts = {}
        for item in cross_tool:
            pattern = item.get("pattern", "unknown")
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        return {
            "high_gini_directories": high_gini,
            "high_palma_directories": high_palma,
            "concentration_analysis": concentration,
            "cross_tool_correlation": cross_tool,
            "critical_directories": critical_dirs,
            "warning_directories": warning_dirs,
            "summary": summary,
            "pattern_counts": pattern_counts,
            "has_gini": len(high_gini) > 0,
            "has_palma": len(high_palma) > 0,
            "has_concentration": len(concentration) > 0,
            "has_cross_tool": len(cross_tool) > 0,
            "has_data": len(high_gini) > 0 or len(concentration) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "code_inequality.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if not data.get("has_data"):
            errors.append("No inequality data available - distribution tables may be empty")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "high_gini_directories": [],
            "high_palma_directories": [],
            "concentration_analysis": [],
            "cross_tool_correlation": [],
            "critical_directories": [],
            "warning_directories": [],
            "summary": {
                "critical_count": 0,
                "warning_count": 0,
                "healthy_count": 0,
                "total_flagged": 0,
                "avg_gini": 0,
                "max_gini": 0,
                "max_palma": 0,
                "concentration_count": 0,
                "cross_tool_count": 0,
            },
            "pattern_counts": {},
            "has_gini": False,
            "has_palma": False,
            "has_concentration": False,
            "has_cross_tool": False,
            "has_data": False,
        }
