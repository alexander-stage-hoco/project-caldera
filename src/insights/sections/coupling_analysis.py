"""
Coupling analysis section - Symbol-level fan-in/fan-out analysis.

Uses mart_symbol_coupling_hotspots to identify architectural coupling patterns
including god objects, octopus patterns, and unstable dependencies.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CouplingAnalysisSection(BaseSection):
    """Symbol coupling analysis using fan-in/fan-out metrics."""

    config = SectionConfig(
        name="coupling_analysis",
        title="Coupling Analysis",
        description="Symbol-level coupling analysis identifying architectural patterns and dependency hotspots.",
        priority=6.5,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch coupling data.

        Returns data including:
        - symbols: Top 25 symbols by coupling
        - summary: Avg fan-in/out, instability distribution
        - patterns: Count of coupling patterns
        - instability_analysis: Symbols by instability zone
        """
        try:
            symbols = fetcher.fetch("coupling_hotspots", run_pk, limit=25)
        except Exception:
            symbols = []

        # Calculate summary statistics
        risk_levels = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        patterns: dict[str, int] = {}
        instability_zones: dict[str, int] = {"stable": 0, "balanced": 0, "unstable": 0}
        fan_in_values = []
        fan_out_values = []
        coupling_values = []

        for s in symbols:
            level = s.get("coupling_risk", "low")
            if level in risk_levels:
                risk_levels[level] += 1

            pattern = s.get("coupling_pattern", "normal")
            patterns[pattern] = patterns.get(pattern, 0) + 1

            zone = s.get("instability_zone", "balanced")
            if zone in instability_zones:
                instability_zones[zone] += 1

            if s.get("fan_in") is not None:
                fan_in_values.append(s["fan_in"])
            if s.get("fan_out") is not None:
                fan_out_values.append(s["fan_out"])
            if s.get("total_coupling") is not None:
                coupling_values.append(s["total_coupling"])

        # Extract run statistics from first symbol
        run_stats = {}
        if symbols:
            first = symbols[0]
            run_stats = {
                "coupling_avg": first.get("run_coupling_avg"),
                "coupling_stddev": first.get("run_coupling_stddev"),
                "coupling_p90": first.get("run_coupling_p90"),
                "fan_in_avg": first.get("run_fan_in_avg"),
                "fan_out_avg": first.get("run_fan_out_avg"),
                "total_symbols": first.get("run_total_symbols"),
            }

        summary = {
            "critical_count": risk_levels["critical"],
            "high_count": risk_levels["high"],
            "medium_count": risk_levels["medium"],
            "low_count": risk_levels["low"],
            "total_symbols": len(symbols),
            "avg_fan_in": round(sum(fan_in_values) / len(fan_in_values), 1) if fan_in_values else 0,
            "avg_fan_out": round(sum(fan_out_values) / len(fan_out_values), 1) if fan_out_values else 0,
            "max_coupling": max(coupling_values) if coupling_values else 0,
        }

        # Sort patterns by count
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)

        # Filter by pattern type
        high_coupling = [s for s in symbols if s.get("coupling_risk") in ("critical", "high")]
        god_objects = [s for s in symbols if s.get("coupling_pattern") == "god_object"]
        octopus = [s for s in symbols if s.get("coupling_pattern") == "octopus"]

        return {
            "symbols": symbols,
            "high_coupling_symbols": high_coupling[:10],
            "god_objects": god_objects,
            "octopus_patterns": octopus,
            "summary": summary,
            "run_statistics": run_stats,
            "patterns": sorted_patterns,
            "instability_zones": instability_zones,
            "has_data": len(symbols) > 0,
            "has_critical": risk_levels["critical"] > 0,
            "has_patterns": len(god_objects) > 0 or len(octopus) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "coupling_analysis.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No coupling data available - symbol-scanner tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "symbols": [],
            "high_coupling_symbols": [],
            "god_objects": [],
            "octopus_patterns": [],
            "summary": {
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "total_symbols": 0,
                "avg_fan_in": 0,
                "avg_fan_out": 0,
                "max_coupling": 0,
            },
            "run_statistics": {},
            "patterns": [],
            "instability_zones": {"stable": 0, "balanced": 0, "unstable": 0},
            "has_data": False,
            "has_critical": False,
            "has_patterns": False,
        }
