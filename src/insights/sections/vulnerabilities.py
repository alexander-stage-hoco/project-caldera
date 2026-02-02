"""
Vulnerability summary section.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class VulnerabilitiesSection(BaseSection):
    """Security vulnerability summary section."""

    config = SectionConfig(
        name="vulnerabilities",
        title="Security Vulnerabilities",
        description="Security vulnerability findings from Trivy and other scanners.",
        priority=4,
    )

    # Severity ordering
    SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch vulnerability data.

        Returns data including:
        - summary: Counts by severity level
        - top_cves: Most severe CVEs
        - affected_packages: Packages with vulnerabilities
        - total_count: Total vulnerability count
        """
        try:
            summary = fetcher.fetch("vulnerability_summary", run_pk)
        except Exception:
            summary = []

        try:
            top_cves = fetcher.fetch("vulnerability_top_cves", run_pk, limit=20)
        except Exception:
            top_cves = []

        try:
            affected_packages = fetcher.fetch("vulnerability_packages", run_pk, limit=15)
        except Exception:
            affected_packages = []

        # Calculate totals
        total_count = sum(s.get("count", 0) for s in summary)
        critical_count = next(
            (s.get("count", 0) for s in summary if s.get("severity") == "CRITICAL"),
            0,
        )
        high_count = next(
            (s.get("count", 0) for s in summary if s.get("severity") == "HIGH"),
            0,
        )

        # Sort summary by severity
        summary_sorted = sorted(
            summary,
            key=lambda x: self.SEVERITY_ORDER.index(x.get("severity", "UNKNOWN"))
            if x.get("severity") in self.SEVERITY_ORDER
            else 999,
        )

        return {
            "summary": summary_sorted,
            "top_cves": top_cves,
            "affected_packages": affected_packages,
            "total_count": total_count,
            "critical_count": critical_count,
            "high_count": high_count,
            "has_vulnerabilities": total_count > 0,
            "has_critical": critical_count > 0,
            "risk_level": self._calculate_risk_level(critical_count, high_count),
        }

    def _calculate_risk_level(self, critical: int, high: int) -> str:
        """Calculate overall risk level based on vulnerability counts."""
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
        return "vulnerabilities.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        # Summary should be present (even if empty)
        if data.get("summary") is None:
            errors.append("Missing vulnerability summary")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": [],
            "top_cves": [],
            "affected_packages": [],
            "total_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "has_vulnerabilities": False,
            "has_critical": False,
            "risk_level": "low",
        }
