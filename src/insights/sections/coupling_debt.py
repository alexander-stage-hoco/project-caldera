"""Coupling-weighted technical debt section.

Weights technical debt by coupling impact to identify high-blast-radius debt.
Files with high debt AND high coupling are prioritized as they pose greater
business risk when modified.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CouplingDebtSection(BaseSection):
    """Coupling-weighted technical debt analysis.

    Key insight: debt in high fan-in files is higher business risk because
    changes there affect many callers. This section answers the PE due diligence
    question: "Which technical debt would have the largest blast radius if we
    try to fix it?"
    """

    config = SectionConfig(
        name="coupling_debt",
        title="Coupling-Weighted Technical Debt",
        description="Technical debt analysis weighted by architectural coupling impact.",
        priority=2.5,  # After technical_debt_summary (2), before composite_risk (3)
    )

    # Quadrant definitions for classification
    QUADRANTS = {
        "critical-coupled": {
            "label": "Critical Coupled",
            "priority": "P0",
            "action": "Fix immediately - high blast radius",
        },
        "high-isolated": {
            "label": "High Isolated",
            "priority": "P1",
            "action": "Fix when convenient - limited impact",
        },
        "medium-coupled": {
            "label": "Medium Coupled",
            "priority": "P2",
            "action": "Monitor - could become critical",
        },
        "medium-isolated": {
            "label": "Medium Isolated",
            "priority": "P3",
            "action": "Backlog",
        },
        "low": {
            "label": "Low",
            "priority": "P4",
            "action": "No action needed",
        },
    }

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """Fetch coupling-weighted debt data."""
        # Fetch hotspots with coupling weights
        try:
            hotspots = fetcher.fetch("coupling_weighted_debt", run_pk, limit=30)
        except Exception:
            hotspots = []

        # Check if we have coupling data at all
        has_coupling_data = any(
            h.get("coupling_fan_in") is not None and h.get("coupling_fan_in") > 0
            for h in hotspots
        )

        # Calculate quadrant distribution
        quadrant_distribution = self._calculate_quadrant_distribution(hotspots)

        # Calculate summary statistics
        summary = self._calculate_summary(hotspots, quadrant_distribution)

        # Generate remediation priorities
        remediation_priorities = self._generate_remediation_priorities(
            hotspots, quadrant_distribution
        )

        return {
            "summary": summary,
            "quadrant_distribution": quadrant_distribution,
            "hotspots": hotspots[:15],  # Top 15 for display
            "all_hotspots": hotspots,  # Full list for analysis
            "remediation_priorities": remediation_priorities,
            "quadrant_definitions": self.QUADRANTS,
            "has_data": len(hotspots) > 0,
            "has_coupling_data": has_coupling_data,
        }

    def _calculate_quadrant_distribution(
        self, hotspots: list[dict]
    ) -> dict[str, dict[str, Any]]:
        """Calculate distribution of files across quadrants."""
        distribution: dict[str, dict[str, Any]] = {
            quadrant: {"count": 0, "total_impact": 0.0, "files": []}
            for quadrant in self.QUADRANTS
        }

        for h in hotspots:
            quadrant = h.get("debt_quadrant", "low")
            if quadrant in distribution:
                distribution[quadrant]["count"] += 1
                distribution[quadrant]["total_impact"] += h.get("debt_impact_score", 0)
                if len(distribution[quadrant]["files"]) < 5:
                    distribution[quadrant]["files"].append(h.get("relative_path", ""))

        return distribution

    def _calculate_summary(
        self,
        hotspots: list[dict],
        quadrant_distribution: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate summary statistics."""
        if not hotspots:
            return {
                "total_files_with_debt": 0,
                "critical_coupled_count": 0,
                "high_isolated_count": 0,
                "total_debt_impact": 0.0,
                "avg_coupling_factor": 0.0,
                "max_impact_score": 0.0,
                "run_avg_fan_in": 0.0,
            }

        # Extract coupling factors (default to 1.0 if not present)
        coupling_factors = [h.get("coupling_factor", 1.0) for h in hotspots]
        impact_scores = [h.get("debt_impact_score", 0) for h in hotspots]

        # Get run statistics from first hotspot
        first = hotspots[0]
        run_avg_fan_in = first.get("run_avg_fan_in", 0) or 0

        return {
            "total_files_with_debt": len(hotspots),
            "critical_coupled_count": quadrant_distribution["critical-coupled"]["count"],
            "high_isolated_count": quadrant_distribution["high-isolated"]["count"],
            "total_debt_impact": round(sum(impact_scores), 1),
            "avg_coupling_factor": round(
                sum(coupling_factors) / len(coupling_factors), 2
            ) if coupling_factors else 0.0,
            "max_impact_score": max(impact_scores) if impact_scores else 0.0,
            "run_avg_fan_in": round(run_avg_fan_in, 1),
        }

    def _generate_remediation_priorities(
        self,
        hotspots: list[dict],
        quadrant_distribution: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate prioritized remediation recommendations."""
        priorities = []

        # Priority 1: Critical-coupled files (highest blast radius)
        critical_coupled = [
            h for h in hotspots if h.get("debt_quadrant") == "critical-coupled"
        ]
        if critical_coupled:
            top_critical = critical_coupled[0]
            priorities.append({
                "path": top_critical.get("relative_path", ""),
                "reason": f"Critical debt (score={top_critical.get('debt_score', 0)}) with high coupling (fan-in={top_critical.get('coupling_fan_in', 0)})",
                "impact_reduction": round(top_critical.get("debt_impact_score", 0), 1),
                "quadrant": "critical-coupled",
            })

        # Priority 2: High-isolated files (high debt but safe to fix)
        high_isolated = [
            h for h in hotspots if h.get("debt_quadrant") == "high-isolated"
        ]
        if high_isolated:
            top_isolated = high_isolated[0]
            priorities.append({
                "path": top_isolated.get("relative_path", ""),
                "reason": f"High debt (score={top_isolated.get('debt_score', 0)}) but low coupling - safe to refactor",
                "impact_reduction": round(top_isolated.get("debt_impact_score", 0), 1),
                "quadrant": "high-isolated",
            })

        # Priority 3: Medium-coupled files at risk of becoming critical
        medium_coupled = [
            h for h in hotspots if h.get("debt_quadrant") == "medium-coupled"
        ]
        if medium_coupled:
            top_medium = medium_coupled[0]
            priorities.append({
                "path": top_medium.get("relative_path", ""),
                "reason": f"Medium debt with growing coupling (fan-in={top_medium.get('coupling_fan_in', 0)}) - prevent escalation",
                "impact_reduction": round(top_medium.get("debt_impact_score", 0), 1),
                "quadrant": "medium-coupled",
            })

        # Add summary recommendation based on quadrant distribution
        if quadrant_distribution["critical-coupled"]["count"] > 3:
            priorities.append({
                "path": "(systemic)",
                "reason": f"Multiple critical-coupled files ({quadrant_distribution['critical-coupled']['count']}) indicate architectural debt",
                "impact_reduction": round(
                    quadrant_distribution["critical-coupled"]["total_impact"], 1
                ),
                "quadrant": "systemic",
            })

        return priorities[:5]  # Top 5 priorities

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "coupling_debt.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append(
                "No coupling-weighted debt data available - requires file metrics data"
            )
        elif not data.get("has_coupling_data"):
            errors.append(
                "No coupling data available - symbol-scanner tool may not have run. "
                "Debt scores shown without coupling weights."
            )
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {
                "total_files_with_debt": 0,
                "critical_coupled_count": 0,
                "high_isolated_count": 0,
                "total_debt_impact": 0.0,
                "avg_coupling_factor": 0.0,
                "max_impact_score": 0.0,
                "run_avg_fan_in": 0.0,
            },
            "quadrant_distribution": {
                quadrant: {"count": 0, "total_impact": 0.0, "files": []}
                for quadrant in self.QUADRANTS
            },
            "hotspots": [],
            "all_hotspots": [],
            "remediation_priorities": [],
            "quadrant_definitions": self.QUADRANTS,
            "has_data": False,
            "has_coupling_data": False,
        }
