"""Technical debt summary section - aggregates all debt indicators."""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class TechnicalDebtSummarySection(BaseSection):
    """Technical debt summary combining complexity, duplication, smells, coverage, and size."""

    config = SectionConfig(
        name="technical_debt_summary",
        title="Technical Debt Summary",
        description="Aggregated view of all technical debt indicators with remediation priorities.",
        priority=2,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """Fetch technical debt summary data."""
        # Get summary statistics
        try:
            summary_results = fetcher.fetch("technical_debt_summary", run_pk)
            summary = summary_results[0] if summary_results else {}
        except Exception:
            summary = {}

        # Get debt hotspots
        try:
            hotspots = fetcher.fetch("technical_debt_hotspots", run_pk, limit=25)
        except Exception:
            hotspots = []

        # Calculate category scores (0-100 scale)
        categories = self._calculate_category_scores(summary)

        # Overall debt score
        overall_score = self._calculate_overall_score(categories)

        # Remediation priorities
        priorities = self._get_remediation_priorities(summary, categories)

        # Group hotspots by debt type
        hotspots_by_type: dict[str, list[dict]] = {}
        for h in hotspots:
            dtype = h.get("primary_debt_type", "mixed")
            if dtype not in hotspots_by_type:
                hotspots_by_type[dtype] = []
            hotspots_by_type[dtype].append(h)

        return {
            "summary": summary,
            "categories": categories,
            "overall_score": overall_score,
            "overall_grade": self._score_to_grade(overall_score),
            "hotspots": hotspots[:15],
            "hotspots_by_type": hotspots_by_type,
            "priorities": priorities,
            "has_data": bool(summary.get("total_files")),
        }

    def _calculate_category_scores(self, summary: dict) -> dict[str, dict]:
        """Calculate debt score for each category (0-100, higher = more debt)."""
        total = summary.get("total_files", 1) or 1

        return {
            "complexity": {
                "score": min(100, (
                    summary.get("complexity_critical", 0) * 30 +
                    summary.get("complexity_high", 0) * 15 +
                    summary.get("complexity_medium", 0) * 5
                ) / total * 10),
                "critical": summary.get("complexity_critical", 0),
                "high": summary.get("complexity_high", 0),
                "medium": summary.get("complexity_medium", 0),
            },
            "duplication": {
                "score": min(100, summary.get("total_duplicate_lines", 0) / max(summary.get("total_loc", 1), 1) * 500),
                "critical": summary.get("duplication_critical", 0),
                "high": summary.get("duplication_high", 0),
                "medium": summary.get("duplication_medium", 0),
                "total_lines": summary.get("total_duplicate_lines", 0),
            },
            "code_smells": {
                "score": min(100, (summary.get("total_high_plus_issues", 0) * 5 + summary.get("total_sonarqube_smells", 0)) / total * 10),
                "high_plus": summary.get("total_high_plus_issues", 0),
                "sonarqube": summary.get("total_sonarqube_smells", 0),
            },
            "coverage_gaps": {
                "score": min(100, (
                    summary.get("coverage_critical", 0) * 30 +
                    summary.get("coverage_high", 0) * 15 +
                    summary.get("coverage_medium", 0) * 5
                ) / max(summary.get("coverage_analyzed", 1), 1) * 10),
                "critical": summary.get("coverage_critical", 0),
                "high": summary.get("coverage_high", 0),
                "avg_coverage": summary.get("avg_coverage"),
            },
            "size": {
                "score": min(100, (
                    summary.get("size_critical", 0) * 20 +
                    summary.get("size_high", 0) * 10 +
                    summary.get("size_medium", 0) * 3
                ) / total * 10),
                "critical": summary.get("size_critical", 0),
                "high": summary.get("size_high", 0),
            },
        }

    def _calculate_overall_score(self, categories: dict) -> int:
        """Calculate weighted overall debt score."""
        weights = {
            "complexity": 0.30,
            "duplication": 0.20,
            "code_smells": 0.25,
            "coverage_gaps": 0.15,
            "size": 0.10,
        }
        return round(sum(
            categories[cat]["score"] * weight
            for cat, weight in weights.items()
        ))

    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade (lower score = better grade)."""
        if score >= 80:
            return "F"
        if score >= 60:
            return "D"
        if score >= 40:
            return "C"
        if score >= 20:
            return "B"
        return "A"

    def _get_remediation_priorities(self, summary: dict, categories: dict) -> list[dict]:
        """Generate prioritized remediation recommendations."""
        priorities = []

        # Sort categories by score
        sorted_cats = sorted(categories.items(), key=lambda x: x[1]["score"], reverse=True)

        for cat_name, cat_data in sorted_cats:
            if cat_data["score"] < 20:
                continue
            priorities.append({
                "category": cat_name,
                "score": round(cat_data["score"], 1),
                "action": self._get_remediation_action(cat_name, cat_data),
            })

        return priorities[:5]

    def _get_remediation_action(self, category: str, data: dict) -> str:
        """Get remediation action for a category."""
        actions = {
            "complexity": f"Refactor {data.get('critical', 0)} critical and {data.get('high', 0)} high complexity files",
            "duplication": f"Eliminate {data.get('total_lines', 0):,} duplicate lines across codebase",
            "code_smells": f"Address {data.get('high_plus', 0)} high-severity issues",
            "coverage_gaps": f"Add tests for {data.get('critical', 0)} critical coverage gaps",
            "size": f"Split {data.get('critical', 0)} oversized files (>1000 LOC)",
        }
        return actions.get(category, "Review and address issues")

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "technical_debt_summary.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No technical debt data available - requires file metrics data")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {},
            "categories": {
                "complexity": {"score": 0, "critical": 0, "high": 0, "medium": 0},
                "duplication": {"score": 0, "critical": 0, "high": 0, "medium": 0, "total_lines": 0},
                "code_smells": {"score": 0, "high_plus": 0, "sonarqube": 0},
                "coverage_gaps": {"score": 0, "critical": 0, "high": 0, "avg_coverage": None},
                "size": {"score": 0, "critical": 0, "high": 0},
            },
            "overall_score": 0,
            "overall_grade": "A",
            "hotspots": [],
            "hotspots_by_type": {},
            "priorities": [],
            "has_data": False,
        }
