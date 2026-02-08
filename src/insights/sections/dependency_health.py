"""
Dependency health section - Repository-level dependency health analysis.

Uses mart_dependency_health_summary and mart_project_blast_radius to assess
overall health grade, blast radius, circular dependencies, and version conflicts.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class DependencyHealthSection(BaseSection):
    """Dependency health analysis using health grade and blast radius metrics."""

    config = SectionConfig(
        name="dependency_health",
        title="Dependency Health",
        description="Repository-level dependency health including blast radius, circular dependencies, and version conflicts.",
        priority=5.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch dependency health data.

        Returns data including:
        - summary: Health grade, total projects/packages, recommendations
        - blast_radius_items: Per-project blast radius metrics
        - high_blast_radius: Projects with medium+ blast radius
        """
        try:
            summary_results = fetcher.fetch("dependency_health_summary", run_pk)
            summary = summary_results[0] if summary_results else {}
        except Exception:
            summary = {}

        try:
            blast_radius_items = fetcher.fetch("blast_radius_hotspots", run_pk, limit=20)
        except Exception:
            blast_radius_items = []

        # Extract health grade and recommendations
        health_grade = summary.get("health_grade", "N/A")
        recommendations = summary.get("recommendations", "")

        # Classify health grade
        if health_grade in ("A", "B"):
            health_status = "good"
        elif health_grade == "C":
            health_status = "warning"
        else:
            health_status = "critical"

        # Build clean summary
        clean_summary = {
            "health_grade": health_grade,
            "total_projects": summary.get("total_projects", 0),
            "total_project_refs": summary.get("total_project_refs", 0),
            "total_package_refs": summary.get("total_package_refs", 0),
            "unique_packages": summary.get("unique_packages", 0),
            "avg_packages_per_project": round(summary.get("avg_packages_per_project", 0), 1),
            "circular_dependency_count": summary.get("circular_dependency_count", 0),
            "critical_cycles": summary.get("critical_cycles", 0),
            "high_cycles": summary.get("high_cycles", 0),
            "version_conflict_count": summary.get("version_conflict_count", 0),
            "critical_conflicts": summary.get("critical_conflicts", 0),
            "high_conflicts": summary.get("high_conflicts", 0),
            "max_blast_radius": summary.get("max_blast_radius", 0),
            "avg_blast_radius": round(summary.get("avg_blast_radius", 0), 1),
        }

        # Filter high blast radius items (medium or higher)
        high_blast_radius = [
            item for item in blast_radius_items
            if item.get("blast_radius_risk") in ("medium", "high", "critical")
        ]

        # Check for issues
        has_circular = clean_summary["circular_dependency_count"] > 0
        has_conflicts = clean_summary["version_conflict_count"] > 0
        has_high_blast_radius = len(high_blast_radius) > 0

        return {
            "summary": clean_summary,
            "health_grade": health_grade,
            "health_status": health_status,
            "recommendations": recommendations,
            "blast_radius_items": blast_radius_items,
            "high_blast_radius": high_blast_radius,
            "has_data": bool(summary) or len(blast_radius_items) > 0,
            "has_circular": has_circular,
            "has_conflicts": has_conflicts,
            "has_high_blast_radius": has_high_blast_radius,
            "has_issues": has_circular or has_conflicts or has_high_blast_radius,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "dependency_health.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No dependency data available - dependensee tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {
                "health_grade": "N/A",
                "total_projects": 0,
                "total_project_refs": 0,
                "total_package_refs": 0,
                "unique_packages": 0,
                "avg_packages_per_project": 0,
                "circular_dependency_count": 0,
                "critical_cycles": 0,
                "high_cycles": 0,
                "version_conflict_count": 0,
                "critical_conflicts": 0,
                "high_conflicts": 0,
                "max_blast_radius": 0,
                "avg_blast_radius": 0,
            },
            "health_grade": "N/A",
            "health_status": "unknown",
            "recommendations": "",
            "blast_radius_items": [],
            "high_blast_radius": [],
            "has_data": False,
            "has_circular": False,
            "has_conflicts": False,
            "has_high_blast_radius": False,
            "has_issues": False,
        }
