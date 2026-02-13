"""
DevSkim security findings section.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class DevskimSecuritySection(BaseSection):
    """Security linting findings from DevSkim."""

    config = SectionConfig(
        name="devskim_security",
        title="DevSkim Security Findings",
        description="Security linting findings (SQL injection, XSS, etc.) from DevSkim analysis.",
        priority=8.3,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch DevSkim security data.

        Returns data including:
        - summary: Severity breakdown and totals
        - by_category: Security category breakdown
        - top_rules: Top rules by severity score
        - hotspot_files: Files with most findings
        """
        try:
            summary_rows = fetcher.fetch("devskim_summary", run_pk)
        except Exception:
            summary_rows = []

        try:
            by_category = fetcher.fetch("devskim_by_category", run_pk)
        except Exception:
            by_category = []

        try:
            top_rules = fetcher.fetch("devskim_top_rules", run_pk, limit=20)
        except Exception:
            top_rules = []

        try:
            hotspot_files = fetcher.fetch("devskim_hotspot_files", run_pk, limit=15)
        except Exception:
            hotspot_files = []

        # Extract summary (single row)
        row = summary_rows[0] if summary_rows else {}
        total_files = row.get("total_files", 0) or 0
        total_issues = row.get("total_issues", 0) or 0
        critical = row.get("severity_critical", 0) or 0
        high = row.get("severity_high", 0) or 0
        medium = row.get("severity_medium", 0) or 0
        low = row.get("severity_low", 0) or 0

        return {
            "summary": {
                "total_files": total_files,
                "total_issues": total_issues,
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            },
            "by_category": by_category,
            "top_rules": top_rules,
            "hotspot_files": hotspot_files,
            "has_data": total_issues > 0,
            "has_critical": critical > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "devskim_security.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {
                "total_files": 0,
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "by_category": [],
            "top_rules": [],
            "hotspot_files": [],
            "has_data": False,
            "has_critical": False,
        }
