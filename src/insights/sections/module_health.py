"""
Module health scoring section - Composite health scores per directory.

Combines multiple distribution metrics into a single health score (0-100)
with letter grades (A-F) for easy interpretation.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class ModuleHealthSection(BaseSection):
    """Module health scoring using composite distribution metrics."""

    config = SectionConfig(
        name="module_health",
        title="Module Health Scoring",
        description="Composite health scores per directory combining inequality, variability, distribution shape, concentration, and outlier metrics.",
        priority=10,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch module health data.

        Returns data including:
        - scored_directories: All directories with health_score and grade
        - healthy_directories: Top 10 by score (descending)
        - unhealthy_directories: Bottom 10 by score with risk_factors list
        - risk_breakdown: Directories with 2+ risk factors
        - summary: Aggregate health statistics
        - grade_distribution: {"A": n, "B": n, ...}
        """
        # Fetch all scored directories
        try:
            all_scores = fetcher.fetch("module_health_scores", run_pk)
        except Exception:
            all_scores = []

        # Fetch risk factors for unhealthy directories
        try:
            risk_factors = fetcher.fetch("module_risk_factors", run_pk)
        except Exception:
            risk_factors = []

        # Fetch aggregate summary
        try:
            summary_results = fetcher.fetch("module_health_summary", run_pk)
            summary = summary_results[0] if summary_results else {}
        except Exception:
            summary = {}

        # Sort for healthy (top) and unhealthy (bottom) directories
        sorted_by_score = sorted(all_scores, key=lambda x: x.get("health_score", 0), reverse=True)
        healthy_directories = sorted_by_score[:10] if sorted_by_score else []
        unhealthy_directories = sorted_by_score[-10:][::-1] if len(sorted_by_score) > 10 else sorted_by_score[::-1]

        # Add risk factors to unhealthy directories
        risk_by_dir = {}
        for rf in risk_factors:
            key = (rf.get("directory_path"), rf.get("metric"))
            risk_by_dir[key] = rf.get("risk_factors_list", "")

        for item in unhealthy_directories:
            key = (item.get("directory_path"), item.get("metric"))
            item["risk_factors"] = risk_by_dir.get(key, "")

        # Calculate grade distribution
        grade_distribution = {
            "A": summary.get("grade_a_count", 0),
            "B": summary.get("grade_b_count", 0),
            "C": summary.get("grade_c_count", 0),
            "D": summary.get("grade_d_count", 0),
            "F": summary.get("grade_f_count", 0),
        }

        # Build clean summary
        clean_summary = {
            "total_directories": summary.get("total_directories", 0),
            "unique_directories": summary.get("unique_directories", 0),
            "avg_health_score": summary.get("avg_health_score", 0),
            "min_health_score": summary.get("min_health_score", 0),
            "max_health_score": summary.get("max_health_score", 0),
            "pct_passing": summary.get("pct_passing", 0),
            "pct_failing": summary.get("pct_failing", 0),
            "risk_factor_count": len(risk_factors),
        }

        return {
            "scored_directories": all_scores,
            "healthy_directories": healthy_directories,
            "unhealthy_directories": unhealthy_directories,
            "risk_breakdown": risk_factors,
            "summary": clean_summary,
            "grade_distribution": grade_distribution,
            "has_scores": len(all_scores) > 0,
            "has_risk_factors": len(risk_factors) > 0,
            "has_data": len(all_scores) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "module_health.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if not data.get("has_data"):
            errors.append("No health score data available - distribution tables may be empty")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "scored_directories": [],
            "healthy_directories": [],
            "unhealthy_directories": [],
            "risk_breakdown": [],
            "summary": {
                "total_directories": 0,
                "unique_directories": 0,
                "avg_health_score": 0,
                "min_health_score": 0,
                "max_health_score": 0,
                "pct_passing": 0,
                "pct_failing": 0,
                "risk_factor_count": 0,
            },
            "grade_distribution": {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0,
                "F": 0,
            },
            "has_scores": False,
            "has_risk_factors": False,
            "has_data": False,
        }
