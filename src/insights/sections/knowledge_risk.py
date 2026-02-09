"""
Knowledge risk section - File-level knowledge concentration risk analysis.

Uses mart_git_blame_knowledge_risk to identify files at risk due to:
- Single author ownership
- High concentration (top author >= 80%)
- Knowledge silos (single author + >100 LOC)
- Stale files (no commits in 90 days)

Answers PE due diligence question: "Which files need knowledge transfer before key developers leave?"
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class KnowledgeRiskSection(BaseSection):
    """File-level knowledge concentration risk analysis."""

    config = SectionConfig(
        name="knowledge_risk",
        title="Knowledge Risk",
        description="File-level knowledge concentration risks identifying single-author files, knowledge silos, and stale code requiring knowledge transfer.",
        priority=6.8,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch knowledge risk data.

        Returns data including:
        - summary: Risk distribution counts
        - hotspots: Top 30 at-risk files by risk score
        - knowledge_silos: Files with single author + >100 LOC
        - stale_critical: Files that are both stale AND critical risk
        - remediation_priorities: Actionable remediation targets
        """
        # Fetch hotspots from the mart
        try:
            hotspots = fetcher.fetch("knowledge_risk_hotspots", run_pk, limit=100)
        except Exception:
            # Mart may not exist if git-blame-scanner hasn't run
            return self.get_fallback_data()

        if not hotspots:
            return self.get_fallback_data()

        # Calculate risk distribution
        risk_distribution = self._calculate_risk_distribution(hotspots)

        # Filter special categories
        knowledge_silos = [h for h in hotspots if h.get("is_knowledge_silo")]
        stale_critical = [
            h for h in hotspots
            if h.get("is_stale") and h.get("risk_level") == "critical"
        ]

        # Build summary
        summary = {
            "total_files_analyzed": len(hotspots),
            "critical_count": risk_distribution["critical"]["count"],
            "high_count": risk_distribution["high"]["count"],
            "medium_count": risk_distribution["medium"]["count"],
            "low_count": risk_distribution["low"]["count"],
            "single_author_files": sum(1 for h in hotspots if h.get("is_single_author")),
            "knowledge_silo_count": len(knowledge_silos),
            "stale_file_count": sum(1 for h in hotspots if h.get("is_stale")),
        }

        # Generate remediation priorities
        remediation_priorities = self._identify_remediation_targets(hotspots)

        # Limit hotspots for display
        display_hotspots = hotspots[:30]

        return {
            "summary": summary,
            "risk_distribution": risk_distribution,
            "hotspots": display_hotspots,
            "knowledge_silos": knowledge_silos[:15],
            "stale_critical": stale_critical[:10],
            "remediation_priorities": remediation_priorities,
            "has_data": True,
            "has_risk": summary["critical_count"] > 0 or summary["high_count"] > 0,
            "is_critical": summary["critical_count"] > 0,
        }

    def _calculate_risk_distribution(
        self, hotspots: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Calculate risk level distribution from hotspots."""
        total = len(hotspots) if hotspots else 1  # Avoid division by zero

        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for h in hotspots:
            level = h.get("risk_level", "low")
            if level in counts:
                counts[level] += 1

        return {
            level: {
                "count": count,
                "pct": round(count / total * 100, 1) if total > 0 else 0,
            }
            for level, count in counts.items()
        }

    def _identify_remediation_targets(
        self, hotspots: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Identify prioritized remediation targets with actionable recommendations."""
        priorities: list[dict[str, str]] = []

        for h in hotspots:
            if h.get("risk_level") not in ("critical", "high"):
                continue

            reasons = []
            actions = []

            if h.get("is_knowledge_silo"):
                reasons.append("Knowledge silo")
                actions.append("Pair program or document")

            if h.get("is_single_author") and not h.get("is_knowledge_silo"):
                reasons.append("Single author")
                actions.append("Add second contributor")

            if h.get("is_stale"):
                reasons.append("Stale (90+ days)")
                actions.append("Schedule review")

            if h.get("is_high_concentration") and not h.get("is_single_author"):
                reasons.append(f"High concentration ({h.get('top_author_pct', 0):.0f}%)")
                actions.append("Distribute ownership")

            if reasons:
                priorities.append({
                    "path": h.get("relative_path", ""),
                    "reason": ", ".join(reasons),
                    "action": "; ".join(actions),
                })

            if len(priorities) >= 10:
                break

        return priorities

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "knowledge_risk.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No knowledge risk data available - git-blame-scanner tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {
                "total_files_analyzed": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "single_author_files": 0,
                "knowledge_silo_count": 0,
                "stale_file_count": 0,
            },
            "risk_distribution": {
                "critical": {"count": 0, "pct": 0},
                "high": {"count": 0, "pct": 0},
                "medium": {"count": 0, "pct": 0},
                "low": {"count": 0, "pct": 0},
            },
            "hotspots": [],
            "knowledge_silos": [],
            "stale_critical": [],
            "remediation_priorities": [],
            "has_data": False,
            "has_risk": False,
            "is_critical": False,
        }
