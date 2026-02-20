"""
Distribution insights section - Gini, Hoover, P95 analysis from Caldera rollups.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class DistributionInsightsSection(BaseSection):
    """Distribution statistics from Caldera's rollup tables."""

    config = SectionConfig(
        name="distribution_insights",
        title="Distribution Insights",
        description="Statistical distribution analysis including Gini coefficient, Hoover index, and percentile metrics.",
        priority=7,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch distribution insights data.

        Returns data including:
        - complexity_distribution: Distribution stats for complexity
        - loc_distribution: Distribution stats for lines of code
        - smell_distribution: Distribution stats for code smells
        - concentration: Top 20% file concentration metrics
        """
        complexity_dist = self._safe_fetch(fetcher, "distribution_complexity", run_pk)
        loc_dist = self._safe_fetch(fetcher, "distribution_loc", run_pk)
        smell_dist = self._safe_fetch(fetcher, "distribution_smells", run_pk)
        concentration = self._safe_fetch(fetcher, "distribution_concentration", run_pk)

        return {
            "complexity_distribution": complexity_dist,
            "loc_distribution": loc_dist,
            "smell_distribution": smell_dist,
            "concentration": concentration,
            "has_complexity": len(complexity_dist) > 0,
            "has_loc": len(loc_dist) > 0,
            "has_smells": len(smell_dist) > 0,
            "has_concentration": len(concentration) > 0,
            "has_data": len(complexity_dist) > 0 or len(loc_dist) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "distribution_insights.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if not data.get("has_data"):
            errors.append("No distribution data available")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "complexity_distribution": [],
            "loc_distribution": [],
            "smell_distribution": [],
            "concentration": [],
            "has_complexity": False,
            "has_loc": False,
            "has_smells": False,
            "has_concentration": False,
            "has_data": False,
        }
