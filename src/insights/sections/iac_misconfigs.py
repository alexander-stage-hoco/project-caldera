"""
IaC Misconfigurations section - Infrastructure-as-Code security findings from Trivy.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class IacMisconfigsSection(BaseSection):
    """Infrastructure-as-Code misconfiguration findings from Trivy."""

    config = SectionConfig(
        name="iac_misconfigs",
        title="IaC Misconfigurations",
        description="Infrastructure-as-Code security findings from Trivy for Terraform, Kubernetes, Docker, etc.",
        priority=9,
    )

    # Severity ordering
    SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch IaC misconfiguration data.

        Returns data including:
        - summary: Counts by severity level
        - top_misconfigs: Most critical misconfigurations
        - by_type: Misconfigs grouped by IaC type (terraform, k8s, docker)
        - affected_files: Files with misconfigurations
        """
        try:
            summary = fetcher.fetch("iac_summary", run_pk)
        except Exception:
            summary = []

        try:
            top_misconfigs = fetcher.fetch("iac_top_misconfigs", run_pk, limit=20)
        except Exception:
            top_misconfigs = []

        try:
            by_type = fetcher.fetch("iac_by_type", run_pk)
        except Exception:
            by_type = []

        try:
            affected_files = fetcher.fetch("iac_affected_files", run_pk, limit=15)
        except Exception:
            affected_files = []

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
            "top_misconfigs": top_misconfigs,
            "by_type": by_type,
            "affected_files": affected_files,
            "total_count": total_count,
            "critical_count": critical_count,
            "high_count": high_count,
            "has_misconfigs": total_count > 0,
            "has_critical": critical_count > 0,
            "risk_level": self._calculate_risk_level(critical_count, high_count),
        }

    def _calculate_risk_level(self, critical: int, high: int) -> str:
        """Calculate overall risk level based on misconfiguration counts."""
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
        return "iac_misconfigs.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        # IaC data is optional - no validation errors
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": [],
            "top_misconfigs": [],
            "by_type": [],
            "affected_files": [],
            "total_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "has_misconfigs": False,
            "has_critical": False,
            "risk_level": "low",
        }
