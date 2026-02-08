"""
Composite risk analysis section - Multi-dimensional file risk assessment.

Uses mart_composite_file_hotspots to identify files with combined risk from
complexity, coverage gaps, code smells, and coupling.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CompositeRiskSection(BaseSection):
    """Composite risk analysis using multi-dimensional file metrics."""

    config = SectionConfig(
        name="composite_risk",
        title="Composite Risk Analysis",
        description="Multi-dimensional file risk assessment combining complexity, coverage, code smells, and coupling.",
        priority=2.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch composite risk data.

        Returns data including:
        - hotspots: Top 25 files by composite score
        - summary: Count by risk level (critical/high/medium/low)
        - risk_patterns: Distribution of risk patterns
        - dimension_coverage: Which dimensions have data
        """
        try:
            hotspots = fetcher.fetch("composite_risk_hotspots", run_pk, limit=25)
        except Exception:
            hotspots = []

        # Calculate summary statistics
        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        risk_patterns: dict[str, int] = {}
        dimensions_with_data = {
            "complexity": False,
            "size": False,
            "issues": False,
            "coverage": False,
            "coupling": False,
        }

        for h in hotspots:
            level = h.get("composite_risk_level", "low")
            if level in risk_levels:
                risk_levels[level] += 1

            pattern = h.get("risk_pattern", "unknown")
            risk_patterns[pattern] = risk_patterns.get(pattern, 0) + 1

            if h.get("has_complexity_data"):
                dimensions_with_data["complexity"] = True
            if h.get("has_size_data"):
                dimensions_with_data["size"] = True
            if h.get("has_issues_data"):
                dimensions_with_data["issues"] = True
            if h.get("has_coverage_data"):
                dimensions_with_data["coverage"] = True
            if h.get("has_coupling_data"):
                dimensions_with_data["coupling"] = True

        # Top files by pattern
        critical_hotspots = [h for h in hotspots if h.get("composite_risk_level") == "critical"]
        high_hotspots = [h for h in hotspots if h.get("composite_risk_level") == "high"]

        summary = {
            "critical_count": risk_levels["critical"],
            "high_count": risk_levels["high"],
            "medium_count": risk_levels["medium"],
            "low_count": risk_levels["low"],
            "total_hotspots": len(hotspots),
            "dimensions_active": sum(1 for v in dimensions_with_data.values() if v),
        }

        # Sort patterns by count
        sorted_patterns = sorted(risk_patterns.items(), key=lambda x: x[1], reverse=True)

        return {
            "hotspots": hotspots,
            "critical_hotspots": critical_hotspots[:10],
            "high_hotspots": high_hotspots[:10],
            "summary": summary,
            "risk_patterns": sorted_patterns,
            "dimensions_with_data": dimensions_with_data,
            "has_data": len(hotspots) > 0,
            "has_critical": risk_levels["critical"] > 0,
            "has_high": risk_levels["high"] > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "composite_risk.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No composite risk data available - mart_composite_file_hotspots may be empty")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "hotspots": [],
            "critical_hotspots": [],
            "high_hotspots": [],
            "summary": {
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "total_hotspots": 0,
                "dimensions_active": 0,
            },
            "risk_patterns": [],
            "dimensions_with_data": {
                "complexity": False,
                "size": False,
                "issues": False,
                "coverage": False,
                "coupling": False,
            },
            "has_data": False,
            "has_critical": False,
            "has_high": False,
        }
