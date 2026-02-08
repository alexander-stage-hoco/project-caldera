"""Coverage gap section - identifies high-complexity files with low test coverage."""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CoverageGapSection(BaseSection):
    """Coverage gap analysis combining complexity and test coverage metrics."""

    config = SectionConfig(
        name="coverage_gap",
        title="Coverage Gap Analysis",
        description="Identifies high-complexity files with insufficient test coverage.",
        priority=3.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """Fetch coverage gap data."""
        try:
            hotspots = fetcher.fetch("coverage_gap_hotspots", run_pk, limit=30)
        except Exception:
            hotspots = []

        # Calculate summary
        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        total_statements_at_risk = 0
        total_gap = 0.0

        for h in hotspots:
            level = h.get("gap_risk_level", "low")
            if level in risk_levels:
                risk_levels[level] += 1
            total_statements_at_risk += (
                h.get("coverage_total_statements", 0) - h.get("coverage_covered_statements", 0)
            )
            total_gap += h.get("gap_to_target", 0) or 0

        critical_hotspots = [h for h in hotspots if h.get("gap_risk_level") == "critical"]
        high_hotspots = [h for h in hotspots if h.get("gap_risk_level") == "high"]

        avg_coverage = (
            sum(h.get("coverage_statement_pct", 0) or 0 for h in hotspots) / len(hotspots)
            if hotspots
            else 0
        )
        avg_complexity = (
            sum(h.get("complexity_max", 0) or 0 for h in hotspots) / len(hotspots)
            if hotspots
            else 0
        )

        return {
            "hotspots": hotspots,
            "critical_hotspots": critical_hotspots[:10],
            "high_hotspots": high_hotspots[:10],
            "summary": {
                "critical_count": risk_levels["critical"],
                "high_count": risk_levels["high"],
                "medium_count": risk_levels["medium"],
                "total_files": len(hotspots),
                "total_statements_at_risk": total_statements_at_risk,
                "avg_coverage": round(avg_coverage, 1),
                "avg_complexity": round(avg_complexity, 1),
            },
            "has_data": len(hotspots) > 0,
            "has_critical": risk_levels["critical"] > 0,
            "has_high": risk_levels["high"] > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "coverage_gap.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append(
                "No coverage gap data available - requires both lizard (complexity) and dotcover (coverage) data"
            )
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
                "total_files": 0,
                "total_statements_at_risk": 0,
                "avg_coverage": 0,
                "avg_complexity": 0,
            },
            "has_data": False,
            "has_critical": False,
            "has_high": False,
        }
