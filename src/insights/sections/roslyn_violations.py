"""
Roslyn violations section - C#/.NET specific analyzer findings.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class RoslynViolationsSection(BaseSection):
    """Roslyn analyzer violations for C#/.NET codebases."""

    config = SectionConfig(
        name="roslyn_violations",
        title="Roslyn Analyzer Findings",
        description="Code analysis findings from Roslyn analyzers for C#/.NET projects.",
        priority=8,
    )

    # Severity ordering
    SEVERITY_ORDER = ["Error", "Warning", "Info", "Hidden"]

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch Roslyn violation data.

        Returns data including:
        - summary: Counts by severity level
        - top_violations: Most common violations
        - by_category: Violations grouped by category
        - hotspot_files: Files with most violations
        """
        summary = self._safe_fetch(fetcher, "roslyn_summary", run_pk)
        top_violations = self._safe_fetch(fetcher, "roslyn_top_violations", run_pk, limit=20)
        by_category = self._safe_fetch(fetcher, "roslyn_by_category", run_pk)
        hotspot_files = self._safe_fetch(fetcher, "roslyn_hotspot_files", run_pk, limit=15)

        # Calculate totals
        total_count = sum(s.get("count", 0) for s in summary)
        error_count = next(
            (s.get("count", 0) for s in summary if s.get("severity") == "Error"),
            0,
        )
        warning_count = next(
            (s.get("count", 0) for s in summary if s.get("severity") == "Warning"),
            0,
        )

        # Sort summary by severity
        summary_sorted = sorted(
            summary,
            key=lambda x: self.SEVERITY_ORDER.index(x.get("severity", "Hidden"))
            if x.get("severity") in self.SEVERITY_ORDER
            else 999,
        )

        return {
            "summary": summary_sorted,
            "top_violations": top_violations,
            "by_category": by_category,
            "hotspot_files": hotspot_files,
            "total_count": total_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "has_violations": total_count > 0,
            "has_errors": error_count > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "roslyn_violations.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        # Roslyn data is optional - no validation errors
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": [],
            "top_violations": [],
            "by_category": [],
            "hotspot_files": [],
            "total_count": 0,
            "error_count": 0,
            "warning_count": 0,
            "has_violations": False,
            "has_errors": False,
        }
