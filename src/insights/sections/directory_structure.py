"""
Directory structure quality section - Repository organization analysis.

Uses mart_layout_structure_hotspots to identify nesting depth issues,
file concentration, and size distribution problems.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class DirectoryStructureSection(BaseSection):
    """Directory structure quality analysis using layout-scanner metrics."""

    config = SectionConfig(
        name="directory_structure",
        title="Directory Structure Quality",
        description="Repository organization analysis including nesting depth, file concentration, and size distribution.",
        priority=7.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch directory structure data.

        Returns data including:
        - directories: All analyzed directories
        - deeply_nested: Directories with excessive depth
        - file_heavy: Directories with too many files
        - size_heavy: Directories with size concentration
        - summary: Overall statistics
        - risk_distribution: Count by risk level
        """
        try:
            directories = fetcher.fetch("layout_structure_hotspots", run_pk, limit=100)
        except Exception:
            directories = []

        # Filter by issues
        deeply_nested = [d for d in directories if d.get("is_deeply_nested")]
        file_heavy = [d for d in directories if d.get("is_file_heavy")]
        size_heavy = [d for d in directories if d.get("is_size_heavy")]
        has_concentration = [d for d in directories if d.get("has_size_concentration")]

        # Build risk distribution
        risk_distribution: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        for d in directories:
            level = d.get("risk_level", "low")
            if level in risk_distribution:
                risk_distribution[level] += 1

        # Calculate statistics
        if directories:
            depths = [d.get("depth", 0) for d in directories]
            avg_depth = sum(depths) / len(depths)
            max_depth = max(depths)
            total_dirs = directories[0].get("run_total_directories", len(directories))
        else:
            avg_depth = 0
            max_depth = 0
            total_dirs = 0

        summary = {
            "total_directories": total_dirs,
            "analyzed_directories": len(directories),
            "avg_depth": round(avg_depth, 1),
            "max_depth": max_depth,
            "deeply_nested_count": len(deeply_nested),
            "file_heavy_count": len(file_heavy),
            "size_heavy_count": len(size_heavy),
            "concentration_count": len(has_concentration),
        }

        # Determine overall health
        critical_count = risk_distribution["critical"]
        high_count = risk_distribution["high"]

        if critical_count > 5:
            structure_health = "poor"
        elif critical_count > 0 or high_count > 5:
            structure_health = "needs_attention"
        elif high_count > 0:
            structure_health = "moderate"
        else:
            structure_health = "good"

        # Top issues by type (limit to 10 each for display)
        top_deeply_nested = sorted(
            deeply_nested,
            key=lambda x: x.get("depth", 0),
            reverse=True
        )[:10]

        top_file_heavy = sorted(
            file_heavy,
            key=lambda x: x.get("file_count_direct", 0),
            reverse=True
        )[:10]

        top_size_heavy = sorted(
            size_heavy,
            key=lambda x: x.get("total_size_bytes_direct", 0),
            reverse=True
        )[:10]

        return {
            "directories": directories[:50],  # Limit for display
            "deeply_nested": top_deeply_nested,
            "file_heavy": top_file_heavy,
            "size_heavy": top_size_heavy,
            "summary": summary,
            "risk_distribution": risk_distribution,
            "structure_health": structure_health,
            "has_data": len(directories) > 0,
            "has_issues": critical_count > 0 or high_count > 0,
            "has_deep_nesting": len(deeply_nested) > 0,
            "has_file_concentration": len(file_heavy) > 0,
            "has_size_concentration": len(size_heavy) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "directory_structure.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No directory structure data available - layout-scanner tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "directories": [],
            "deeply_nested": [],
            "file_heavy": [],
            "size_heavy": [],
            "summary": {
                "total_directories": 0,
                "analyzed_directories": 0,
                "avg_depth": 0,
                "max_depth": 0,
                "deeply_nested_count": 0,
                "file_heavy_count": 0,
                "size_heavy_count": 0,
                "concentration_count": 0,
            },
            "risk_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "structure_health": "unknown",
            "has_data": False,
            "has_issues": False,
            "has_deep_nesting": False,
            "has_file_concentration": False,
            "has_size_concentration": False,
        }
