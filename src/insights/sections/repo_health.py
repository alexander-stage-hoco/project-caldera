"""
Repository health overview section.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class RepoHealthSection(BaseSection):
    """Repository health overview section."""

    config = SectionConfig(
        name="repo_health",
        title="Repository Health Overview",
        description="Overall repository health metrics including file count, LOC, complexity, and health grade.",
        priority=1,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch repository health data.

        Returns data including:
        - total_files: Total number of files
        - total_loc: Total lines of code
        - total_code: Total code lines (excluding blanks/comments)
        - total_comment: Total comment lines
        - avg_ccn: Average cyclomatic complexity
        - max_ccn: Maximum cyclomatic complexity
        - health_grade: Repository health grade (A-F)
        - violation_count: Number of git-sizer violations
        - lfs_candidate_count: Files that should use LFS
        - languages: Language breakdown
        """
        try:
            health_data = fetcher.fetch("repo_health", run_pk)
            if health_data:
                result = health_data[0]
            else:
                result = self.get_fallback_data()
        except Exception:
            result = self.get_fallback_data()

        # Fetch language breakdown
        try:
            languages = fetcher.fetch("language_summary", run_pk, limit=10)
        except Exception:
            languages = []

        result["languages"] = languages
        result["has_health_grade"] = result.get("health_grade") is not None

        return result

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "repo_health.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if data.get("total_files") is None:
            errors.append("Missing total_files metric")

        if data.get("total_loc") is None:
            errors.append("Missing total_loc metric")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "total_files": 0,
            "total_loc": 0,
            "total_code": 0,
            "total_comment": 0,
            "avg_ccn": None,
            "max_ccn": None,
            "health_grade": None,
            "violation_count": 0,
            "lfs_candidate_count": 0,
            "languages": [],
            "has_health_grade": False,
        }
