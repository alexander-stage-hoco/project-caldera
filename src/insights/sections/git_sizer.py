"""
Git-sizer repository size health section.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class GitSizerSection(BaseSection):
    """Repository size health from git-sizer (violations, LFS candidates, structure metrics)."""

    config = SectionConfig(
        name="git_sizer",
        title="Repository Size Health",
        description="Repository size health analysis including violations, LFS candidates, and structure metrics from git-sizer.",
        priority=1.2,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch git-sizer data.

        Returns data including:
        - summary: Health grade, violation/LFS counts, structure metrics
        - violations: Violation details by metric
        - lfs_candidates: Files recommended for LFS
        """
        try:
            summary_rows = fetcher.fetch("git_sizer_summary", run_pk)
        except Exception:
            summary_rows = []

        try:
            violations = fetcher.fetch("git_sizer_violations", run_pk, limit=20)
        except Exception:
            violations = []

        try:
            lfs_candidates = fetcher.fetch("git_sizer_lfs_candidates", run_pk, limit=20)
        except Exception:
            lfs_candidates = []

        # Extract summary (single row)
        row = summary_rows[0] if summary_rows else {}
        violation_count = row.get("violation_count", 0) or 0
        lfs_candidate_count = row.get("lfs_candidate_count", 0) or 0

        # Check for level 3+ violations
        has_serious_violations = any(
            (v.get("level_3_plus", 0) or 0) > 0 for v in violations
        )

        return {
            "summary": row,
            "violations": violations,
            "lfs_candidates": lfs_candidates,
            "has_data": bool(row),
            "has_violations": violation_count > 0,
            "has_lfs_candidates": lfs_candidate_count > 0,
            "has_serious_violations": has_serious_violations,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "git_sizer.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {},
            "violations": [],
            "lfs_candidates": [],
            "has_data": False,
            "has_violations": False,
            "has_lfs_candidates": False,
            "has_serious_violations": False,
        }
