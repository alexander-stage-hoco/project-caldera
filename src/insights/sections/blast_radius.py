"""
Blast radius section - Symbol-level change impact analysis.

Uses mart_blast_radius_symbol to identify which functions/methods
affect the most code when modified, helping with refactoring risk
assessment and change management planning.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class BlastRadiusSection(BaseSection):
    """Symbol-level blast radius analysis using symbol-scanner data."""

    config = SectionConfig(
        name="blast_radius",
        title="Symbol Blast Radius",
        description="Symbol-level change impact analysis identifying high-impact functions and methods.",
        priority=2.7,  # After function_complexity (2.5), before directory_structure (2.8)
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch symbol blast radius data.

        Returns data including:
        - symbols: Top 30 symbols by blast radius
        - high_impact_symbols: Medium+ risk only
        - summary: Count by risk level, max/avg blast radius
        - risk_distribution: Count per risk level
        - files_with_high_impact: Files containing high-impact symbols
        """
        try:
            symbols = fetcher.fetch("symbol_blast_radius", run_pk, limit=30)
        except Exception:
            symbols = []

        # Calculate summary statistics
        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        blast_radii = []
        files_affected: set[str] = set()
        max_affected_files = 0

        for s in symbols:
            level = s.get("blast_radius_risk", "low")
            if level in risk_levels:
                risk_levels[level] += 1

            radius = s.get("blast_radius_symbols", 0)
            if radius:
                blast_radii.append(radius)

            file_path = s.get("target_file_path", "")
            if file_path:
                files_affected.add(file_path)

            affected_files = s.get("blast_radius_files", 0)
            if affected_files > max_affected_files:
                max_affected_files = affected_files

        # High impact symbols (medium+ risk)
        high_impact_symbols = [
            s for s in symbols
            if s.get("blast_radius_risk") in ("critical", "high", "medium")
        ]

        # Group by file
        files_with_symbols: dict[str, list] = {}
        for s in symbols:
            path = s.get("target_file_path") or "(builtin/external)"
            if path not in files_with_symbols:
                files_with_symbols[path] = []
            files_with_symbols[path].append(s)

        # Sort files by max blast radius in file
        sorted_files = sorted(
            files_with_symbols.items(),
            key=lambda x: max(s.get("blast_radius_symbols", 0) for s in x[1]),
            reverse=True,
        )[:10]

        summary = {
            "total_symbols": len(symbols),
            "critical_count": risk_levels["critical"],
            "high_count": risk_levels["high"],
            "medium_count": risk_levels["medium"],
            "low_count": risk_levels["low"],
            "max_blast_radius": max(blast_radii) if blast_radii else 0,
            "avg_blast_radius": round(sum(blast_radii) / len(blast_radii), 1) if blast_radii else 0,
            "max_affected_files": max_affected_files,
            "files_with_high_impact": len([f for f in files_affected if f]),
        }

        return {
            "symbols": symbols,
            "high_impact_symbols": high_impact_symbols,
            "summary": summary,
            "risk_distribution": risk_levels,
            "files_with_high_impact_symbols": sorted_files,
            "has_data": len(symbols) > 0,
            "has_critical": risk_levels["critical"] > 0,
            "has_high_impact": len(high_impact_symbols) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "blast_radius.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No blast radius data available - symbol-scanner tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "symbols": [],
            "high_impact_symbols": [],
            "summary": {
                "total_symbols": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "max_blast_radius": 0,
                "avg_blast_radius": 0,
                "max_affected_files": 0,
                "files_with_high_impact": 0,
            },
            "risk_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "files_with_high_impact_symbols": [],
            "has_data": False,
            "has_critical": False,
            "has_high_impact": False,
        }
