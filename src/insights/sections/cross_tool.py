"""
Cross-tool insights section for compound risk analysis.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CrossToolSection(BaseSection):
    """Cross-tool correlation and compound risk analysis."""

    config = SectionConfig(
        name="cross_tool",
        title="Cross-Tool Insights",
        description="Compound risks identified by correlating data across multiple analysis tools.",
        priority=5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch cross-tool insights.

        Returns data including:
        - complex_and_smelly: Files that are both complex AND have smells
        - complex_and_vulnerable: Files in packages with vulnerabilities
        - risk_summary: Summary of compound risks
        """
        try:
            complex_and_smelly = fetcher.fetch("cross_tool_complex_smelly", run_pk, limit=15)
        except Exception:
            complex_and_smelly = []

        try:
            complex_and_vulnerable = fetcher.fetch("cross_tool_complex_vulnerable", run_pk, limit=15)
        except Exception:
            complex_and_vulnerable = []

        # Calculate risk summary
        risk_summary = self._calculate_risk_summary(
            complex_and_smelly,
            complex_and_vulnerable,
        )

        return {
            "complex_and_smelly": complex_and_smelly,
            "complex_and_vulnerable": complex_and_vulnerable,
            "risk_summary": risk_summary,
            "has_complex_smelly": len(complex_and_smelly) > 0,
            "has_complex_vulnerable": len(complex_and_vulnerable) > 0,
            "has_insights": risk_summary["total_risks"] > 0,
        }

    def _calculate_risk_summary(
        self,
        complex_smelly: list[dict],
        complex_vulnerable: list[dict],
    ) -> dict[str, Any]:
        """Calculate summary of compound risks."""
        # Collect all unique files with compound risks
        all_risk_files = set()

        for item in complex_smelly:
            if item.get("relative_path"):
                all_risk_files.add(item["relative_path"])

        for item in complex_vulnerable:
            if item.get("relative_path"):
                all_risk_files.add(item["relative_path"])

        return {
            "total_risks": len(all_risk_files),
            "complex_smelly_count": len(complex_smelly),
            "complex_vulnerable_count": len(complex_vulnerable),
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "cross_tool.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        # Cross-tool data is optional - no validation errors
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "complex_and_smelly": [],
            "complex_and_vulnerable": [],
            "risk_summary": {
                "total_risks": 0,
                "complex_smelly_count": 0,
                "complex_vulnerable_count": 0,
            },
            "has_complex_smelly": False,
            "has_complex_vulnerable": False,
            "has_insights": False,
        }
