"""
License compliance section - License detection and copyleft risk analysis.

Uses mart_scancode_license_hotspots to identify license types, copyleft risks,
and compliance status.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class LicenseComplianceSection(BaseSection):
    """License compliance analysis using scancode license detection."""

    config = SectionConfig(
        name="license_compliance",
        title="License Compliance",
        description="License detection and copyleft risk analysis for compliance review.",
        priority=9.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch license compliance data.

        Returns data including:
        - licenses: All license detections with metadata
        - by_category: Licenses grouped by category (permissive/copyleft/etc.)
        - copyleft_licenses: Only copyleft licenses
        - summary: Counts by category
        - compliance_status: OK or REVIEW NEEDED
        """
        try:
            licenses = fetcher.fetch("license_compliance_summary", run_pk)
        except Exception:
            licenses = []

        # Organize by category
        by_category: dict[str, list[dict[str, Any]]] = {
            "permissive": [],
            "copyleft": [],
            "weak_copyleft": [],
            "unknown": [],
        }

        for lic in licenses:
            category = lic.get("category", "unknown")
            if category in by_category:
                by_category[category].append(lic)
            else:
                by_category["unknown"].append(lic)

        # Extract copyleft licenses
        copyleft_licenses = by_category["copyleft"]
        weak_copyleft_licenses = by_category["weak_copyleft"]

        # Build summary
        summary = {
            "total_licenses": len(licenses),
            "permissive_count": len(by_category["permissive"]),
            "copyleft_count": len(copyleft_licenses),
            "weak_copyleft_count": len(weak_copyleft_licenses),
            "unknown_count": len(by_category["unknown"]),
            "total_files_affected": sum(lic.get("files_affected", 0) for lic in licenses),
            "total_detections": sum(lic.get("detection_count", 0) for lic in licenses),
        }

        # Determine compliance status
        has_copyleft = len(copyleft_licenses) > 0
        has_weak_copyleft = len(weak_copyleft_licenses) > 0

        if has_copyleft:
            compliance_status = "REVIEW NEEDED"
            compliance_risk = "high"
        elif has_weak_copyleft:
            compliance_status = "REVIEW RECOMMENDED"
            compliance_risk = "medium"
        else:
            compliance_status = "OK"
            compliance_risk = "low"

        # Calculate average confidence
        if licenses:
            avg_confidence = sum(lic.get("avg_confidence", 0) for lic in licenses) / len(licenses)
        else:
            avg_confidence = 0

        return {
            "licenses": licenses,
            "by_category": by_category,
            "copyleft_licenses": copyleft_licenses,
            "weak_copyleft_licenses": weak_copyleft_licenses,
            "permissive_licenses": by_category["permissive"],
            "summary": summary,
            "compliance_status": compliance_status,
            "compliance_risk": compliance_risk,
            "avg_confidence": round(avg_confidence, 2),
            "has_data": len(licenses) > 0,
            "has_copyleft": has_copyleft,
            "has_weak_copyleft": has_weak_copyleft,
            "needs_review": has_copyleft or has_weak_copyleft,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "license_compliance.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No license data available - scancode tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "licenses": [],
            "by_category": {
                "permissive": [],
                "copyleft": [],
                "weak_copyleft": [],
                "unknown": [],
            },
            "copyleft_licenses": [],
            "weak_copyleft_licenses": [],
            "permissive_licenses": [],
            "summary": {
                "total_licenses": 0,
                "permissive_count": 0,
                "copyleft_count": 0,
                "weak_copyleft_count": 0,
                "unknown_count": 0,
                "total_files_affected": 0,
                "total_detections": 0,
            },
            "compliance_status": "UNKNOWN",
            "compliance_risk": "unknown",
            "avg_confidence": 0,
            "has_data": False,
            "has_copyleft": False,
            "has_weak_copyleft": False,
            "needs_review": False,
        }
