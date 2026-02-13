"""
Dotcover .NET coverage section.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class DotcoverCoverageSection(BaseSection):
    """.NET code coverage from dotCover at assembly/type/method granularity."""

    config = SectionConfig(
        name="dotcover_coverage",
        title=".NET Code Coverage",
        description=".NET code coverage at assembly, namespace, and file level from dotCover.",
        priority=3.6,
    )

    @staticmethod
    def _coverage_grade(pct: float | None) -> str:
        """Assign a letter grade based on coverage percentage."""
        if pct is None:
            return "N/A"
        if pct >= 90:
            return "A"
        if pct >= 80:
            return "B"
        if pct >= 70:
            return "C"
        if pct >= 60:
            return "D"
        return "F"

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch dotCover coverage data.

        Returns data including:
        - summary: Overall coverage stats
        - assemblies: Assembly-level coverage (worst first)
        - low_coverage_files: File hotspots with risk levels
        - namespaces: Namespace-level coverage
        """
        try:
            summary_rows = fetcher.fetch("dotcover_summary", run_pk)
        except Exception:
            summary_rows = []

        try:
            assemblies = fetcher.fetch("dotcover_assemblies", run_pk, limit=20)
        except Exception:
            assemblies = []

        try:
            low_coverage_files = fetcher.fetch("dotcover_low_coverage_files", run_pk, limit=15)
        except Exception:
            low_coverage_files = []

        try:
            namespaces = fetcher.fetch("dotcover_namespaces", run_pk, limit=15)
        except Exception:
            namespaces = []

        # Extract summary (single row)
        row = summary_rows[0] if summary_rows else {}
        assembly_count = row.get("assembly_count", 0) or 0
        total_covered = row.get("total_covered", 0) or 0
        total_statements = row.get("total_statements", 0) or 0
        overall_coverage_pct = row.get("overall_coverage_pct")

        return {
            "summary": {
                "assembly_count": assembly_count,
                "total_covered": total_covered,
                "total_statements": total_statements,
                "overall_coverage_pct": overall_coverage_pct,
            },
            "assemblies": assemblies,
            "low_coverage_files": low_coverage_files,
            "namespaces": namespaces,
            "has_data": assembly_count > 0,
            "coverage_grade": self._coverage_grade(overall_coverage_pct),
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "dotcover_coverage.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {
                "assembly_count": 0,
                "total_covered": 0,
                "total_statements": 0,
                "overall_coverage_pct": None,
            },
            "assemblies": [],
            "low_coverage_files": [],
            "namespaces": [],
            "has_data": False,
            "coverage_grade": "N/A",
        }
