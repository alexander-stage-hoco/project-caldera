"""
Exposed secrets section for gitleaks findings.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class SecretsSection(BaseSection):
    """Report section for exposed secrets from gitleaks."""

    config = SectionConfig(
        name="secrets",
        title="Exposed Secrets",
        description="Detected secrets and credentials from gitleaks scanning.",
        priority=5,  # After vulnerabilities (4), before cross_tool (6)
    )

    # Severity ordering
    SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch secrets data.

        Returns data including:
        - summary: Counts by severity level
        - by_rule: Breakdown by rule/secret type
        - hotspot_files: Files with most secrets
        - total_count: Total secret count
        """
        try:
            summary = fetcher.fetch("gitleaks_summary", run_pk)
        except Exception:
            summary = []

        try:
            by_rule = fetcher.fetch("gitleaks_by_rule", run_pk, limit=15)
        except Exception:
            by_rule = []

        try:
            hotspot_files = fetcher.fetch("gitleaks_hotspot_files", run_pk, limit=10)
        except Exception:
            hotspot_files = []

        # Calculate totals
        total_count = sum(row.get("count", 0) for row in summary)
        critical_count = sum(
            row.get("count", 0) for row in summary if row.get("severity") == "CRITICAL"
        )
        high_count = sum(
            row.get("count", 0) for row in summary if row.get("severity") == "HIGH"
        )
        in_head_count = sum(row.get("in_head_count", 0) for row in summary)

        # Sort summary by severity order
        severity_rank = {s: i for i, s in enumerate(self.SEVERITY_ORDER)}
        summary_sorted = sorted(
            summary, key=lambda r: severity_rank.get(r.get("severity", ""), 99)
        )

        return {
            "summary": summary_sorted,
            "by_rule": by_rule,
            "hotspot_files": hotspot_files,
            "total_count": total_count,
            "critical_count": critical_count,
            "high_count": high_count,
            "in_head_count": in_head_count,
            "in_history_count": total_count - in_head_count,
            "has_secrets": total_count > 0,
            "has_critical": critical_count > 0,
            "risk_level": self._calculate_risk_level(critical_count, high_count),
        }

    def _calculate_risk_level(self, critical: int, high: int) -> str:
        """Calculate overall risk level based on secret counts."""
        if critical > 0:
            return "critical"
        elif high > 5:
            return "high"
        elif high > 0:
            return "medium"
        else:
            return "low"

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "secrets.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        # Summary should be present (even if empty)
        if data.get("summary") is None:
            errors.append("Missing secrets summary")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": [],
            "by_rule": [],
            "hotspot_files": [],
            "total_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "in_head_count": 0,
            "in_history_count": 0,
            "has_secrets": False,
            "has_critical": False,
            "risk_level": "low",
        }
