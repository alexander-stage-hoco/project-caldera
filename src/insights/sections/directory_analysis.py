"""
Directory analysis section with rollups and hotspots.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class DirectoryAnalysisSection(BaseSection):
    """Directory-level analysis with rollups."""

    config = SectionConfig(
        name="directory_analysis",
        title="Directory Analysis",
        description="Directory-level metrics including LOC, complexity, and code smell rollups.",
        priority=3,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch directory analysis data.

        Returns data including:
        - hotspots: Top directories by complexity
        - largest: Top directories by LOC
        - smelliest: Top directories by code smell density
        - tree: Directory tree structure with metrics
        """
        try:
            hotspots = fetcher.fetch("directory_hotspots", run_pk, limit=15)
        except Exception:
            hotspots = []

        try:
            largest = fetcher.fetch("directory_largest", run_pk, limit=15)
        except Exception:
            largest = []

        try:
            smelliest = fetcher.fetch("directory_smelliest", run_pk, limit=15)
        except Exception:
            smelliest = []

        # Calculate directory tree depth stats
        tree_stats = self._calculate_tree_stats(hotspots + largest)

        return {
            "hotspots": hotspots,
            "largest": largest,
            "smelliest": smelliest,
            "tree_stats": tree_stats,
            "has_hotspots": len(hotspots) > 0,
            "has_largest": len(largest) > 0,
            "has_smelliest": len(smelliest) > 0,
        }

    def _calculate_tree_stats(self, directories: list[dict]) -> dict[str, Any]:
        """Calculate statistics about directory tree structure."""
        if not directories:
            return {
                "max_depth": 0,
                "avg_depth": 0,
                "total_dirs": 0,
            }

        depths = []
        for d in directories:
            path = d.get("directory_path", "")
            # Count path separators as proxy for depth
            depth = path.count("/") if path else 0
            depths.append(depth)

        return {
            "max_depth": max(depths) if depths else 0,
            "avg_depth": sum(depths) / len(depths) if depths else 0,
            "total_dirs": len(set(d.get("directory_path") for d in directories)),
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "directory_analysis.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if not data.get("has_hotspots") and not data.get("has_largest"):
            errors.append("No directory data available")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "hotspots": [],
            "largest": [],
            "smelliest": [],
            "tree_stats": {
                "max_depth": 0,
                "avg_depth": 0,
                "total_dirs": 0,
            },
            "has_hotspots": False,
            "has_largest": False,
            "has_smelliest": False,
        }
