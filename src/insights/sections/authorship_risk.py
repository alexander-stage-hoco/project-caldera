"""
Authorship risk section - Bus factor and contributor concentration analysis.

Uses mart_authorship_summary and mart_git_fame_contributor_hotspots to identify
knowledge concentration risks and single points of failure.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class AuthorshipRiskSection(BaseSection):
    """Authorship risk analysis using bus factor and concentration metrics."""

    config = SectionConfig(
        name="authorship_risk",
        title="Authorship Risk",
        description="Bus factor and contributor concentration analysis identifying knowledge silos and single points of failure.",
        priority=6.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch authorship risk data.

        Returns data including:
        - summary: Bus factor, concentration metrics
        - contributors: Top 15 contributors with metrics
        - risk_level: Based on bus factor
        - concentration_analysis: Ownership distribution
        """
        try:
            summary_results = fetcher.fetch("authorship_summary", run_pk)
            summary = summary_results[0] if summary_results else {}
        except Exception:
            summary = {}

        try:
            contributors = fetcher.fetch("contributor_hotspots", run_pk, limit=15)
        except Exception:
            contributors = []

        # Determine risk level from bus factor
        bus_factor = summary.get("bus_factor", 0)
        if bus_factor <= 1:
            bus_factor_risk = "critical"
        elif bus_factor <= 2:
            bus_factor_risk = "high"
        elif bus_factor <= 3:
            bus_factor_risk = "medium"
        else:
            bus_factor_risk = "low"

        # Calculate concentration metrics
        top_author_pct = summary.get("top_author_pct", 0)
        top_two_pct = summary.get("top_two_pct", 0)

        if top_author_pct >= 70:
            concentration_risk = "critical"
        elif top_author_pct >= 50:
            concentration_risk = "high"
        elif top_author_pct >= 30:
            concentration_risk = "medium"
        else:
            concentration_risk = "low"

        # Calculate contributor tiers
        bus_factor_members = [c for c in contributors if c.get("is_bus_factor_member")]
        significant_contributors = [c for c in contributors if c.get("is_significant_contributor")]
        critical_contributors = [c for c in contributors if c.get("risk_level") == "critical"]

        # Build clean summary
        clean_summary = {
            "author_count": summary.get("author_count", 0),
            "bus_factor": bus_factor,
            "top_author_pct": round(top_author_pct, 1) if top_author_pct else 0,
            "top_two_pct": round(top_two_pct, 1) if top_two_pct else 0,
            "hhi_index": round(summary.get("hhi_index", 0), 4) if summary.get("hhi_index") else 0,
            "total_loc": summary.get("total_loc", 0),
            "bus_factor_risk": summary.get("bus_factor_risk", bus_factor_risk),
            "concentration_risk": summary.get("concentration_risk", concentration_risk),
            "single_author_dominated": summary.get("single_author_dominated", False),
        }

        return {
            "summary": clean_summary,
            "contributors": contributors,
            "bus_factor_members": bus_factor_members,
            "significant_contributors": significant_contributors,
            "critical_contributors": critical_contributors,
            "bus_factor_risk": bus_factor_risk,
            "concentration_risk": concentration_risk,
            "has_data": len(contributors) > 0 or bool(summary),
            "has_risk": bus_factor_risk in ("critical", "high") or concentration_risk in ("critical", "high"),
            "is_critical": bus_factor_risk == "critical" or concentration_risk == "critical",
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "authorship_risk.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No authorship data available - git-fame tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {
                "author_count": 0,
                "bus_factor": 0,
                "top_author_pct": 0,
                "top_two_pct": 0,
                "hhi_index": 0,
                "total_loc": 0,
                "bus_factor_risk": "unknown",
                "concentration_risk": "unknown",
                "single_author_dominated": False,
            },
            "contributors": [],
            "bus_factor_members": [],
            "significant_contributors": [],
            "critical_contributors": [],
            "bus_factor_risk": "unknown",
            "concentration_risk": "unknown",
            "has_data": False,
            "has_risk": False,
            "is_critical": False,
        }
