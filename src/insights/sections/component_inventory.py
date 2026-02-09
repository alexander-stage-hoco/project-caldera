"""
Component inventory section - Module-by-module analysis with dependencies and health.

Provides a comprehensive view of each component (depth 1-2 directories) including:
- Size and complexity metrics
- Dependencies (inbound/outbound)
- Health grade (A-F)
- Hotspots and risk signals
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class ComponentInventorySection(BaseSection):
    """Component inventory with health grades and dependency analysis."""

    config = SectionConfig(
        name="component_inventory",
        title="Component Inventory",
        description="Module-by-module analysis with dependencies, health grades, and hotspots.",
        priority=5,  # After coupling_analysis (6.5), before file_hotspots (4)
    )

    # Thresholds for risk signal identification
    HIGH_COUPLING_THRESHOLD = 50
    HIGH_FAN_OUT_THRESHOLD = 30
    HIGH_CCN_THRESHOLD = 15
    KNOWLEDGE_CONCENTRATION_THRESHOLD = 70  # % owned by top author

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch component inventory data.

        Returns data including:
        - components: All components with metrics and health grades
        - healthy_components: Components with grade A/B
        - at_risk_components: Components with grade C/D
        - critical_components: Components with grade F
        - summary: Aggregate statistics
        - has_data: Whether any components were found
        """
        # 1. Fetch component list with metrics
        try:
            components = fetcher.fetch("component_inventory", run_pk)
        except Exception:
            components = []

        # 2. Fetch inter-component dependencies
        try:
            dependencies = fetcher.fetch("component_dependencies", run_pk)
        except Exception:
            dependencies = []

        # 3. Fetch component hotspots
        try:
            hotspots = fetcher.fetch("component_hotspots", run_pk)
        except Exception:
            hotspots = []

        # 4. Build dependency maps and hotspot maps
        outbound_deps: dict[str, list[dict]] = {}
        inbound_deps: dict[str, list[dict]] = {}
        for dep in dependencies:
            comp_path = dep.get("component_path", "")
            direction = dep.get("direction", "")
            dep_info = {
                "related_component": dep.get("related_component", ""),
                "call_type": dep.get("call_type", "direct"),
                "call_count": dep.get("call_count", 0),
                "unique_callers": dep.get("unique_callers", 0),
                "unique_callees": dep.get("unique_callees", 0),
            }
            if direction == "outbound":
                if comp_path not in outbound_deps:
                    outbound_deps[comp_path] = []
                outbound_deps[comp_path].append(dep_info)
            elif direction == "inbound":
                if comp_path not in inbound_deps:
                    inbound_deps[comp_path] = []
                inbound_deps[comp_path].append(dep_info)

        hotspot_map: dict[str, list[dict]] = {}
        for hs in hotspots:
            comp_path = hs.get("component_path", "")
            if comp_path not in hotspot_map:
                hotspot_map[comp_path] = []
            hotspot_map[comp_path].append({
                "file_path": hs.get("file_path", ""),
                "total_ccn": hs.get("total_ccn", 0),
                "max_ccn": hs.get("max_ccn", 0),
                "hotspot_type": hs.get("hotspot_type", ""),
            })

        # 5. Enrich components with dependencies, hotspots, and risk signals
        for comp in components:
            comp_path = comp.get("directory_path", "")

            # Add dependencies
            comp["outbound_dependencies"] = outbound_deps.get(comp_path, [])
            comp["inbound_dependencies"] = inbound_deps.get(comp_path, [])

            # Add hotspots
            comp["hotspots"] = hotspot_map.get(comp_path, [])

            # Calculate risk signals
            comp["risk_signals"] = self._identify_risks(comp)

        # 6. Categorize by health grade
        healthy = [c for c in components if c.get("health_grade") in ("A", "B")]
        at_risk = [c for c in components if c.get("health_grade") in ("C", "D")]
        critical = [c for c in components if c.get("health_grade") == "F"]

        # 7. Build summary
        summary = self._build_summary(components)

        # 8. Calculate grade distribution
        grade_distribution = {
            "A": sum(1 for c in components if c.get("health_grade") == "A"),
            "B": sum(1 for c in components if c.get("health_grade") == "B"),
            "C": sum(1 for c in components if c.get("health_grade") == "C"),
            "D": sum(1 for c in components if c.get("health_grade") == "D"),
            "F": sum(1 for c in components if c.get("health_grade") == "F"),
        }

        return {
            "components": components,
            "healthy_components": healthy,
            "at_risk_components": at_risk,
            "critical_components": critical,
            "summary": summary,
            "grade_distribution": grade_distribution,
            "has_data": len(components) > 0,
            "has_critical": len(critical) > 0,
            "has_dependencies": len(dependencies) > 0,
        }

    def _identify_risks(self, comp: dict[str, Any]) -> list[str]:
        """Identify risk signals for a component."""
        risks = []

        # High coupling
        total_coupling = comp.get("total_coupling", 0)
        if total_coupling > self.HIGH_COUPLING_THRESHOLD:
            risks.append(f"High coupling ({total_coupling} dependencies)")

        # High fan-out (depends on many things)
        fan_out = comp.get("fan_out", 0)
        if fan_out > self.HIGH_FAN_OUT_THRESHOLD:
            risks.append(f"High outbound coupling (fan_out = {fan_out})")

        # High complexity
        avg_ccn = comp.get("avg_ccn", 0)
        if avg_ccn > self.HIGH_CCN_THRESHOLD:
            risks.append(f"High avg complexity (CCN = {avg_ccn})")

        # Knowledge concentration
        top_author_pct = comp.get("avg_top_author_pct", 0)
        if top_author_pct > self.KNOWLEDGE_CONCENTRATION_THRESHOLD:
            risks.append(f"Knowledge concentration (top author = {top_author_pct:.0f}%)")

        # Instability concerns (very high or very low)
        instability = comp.get("instability", 0.5)
        if instability > 0.8:
            risks.append(f"Highly unstable (I = {instability:.2f})")
        elif instability < 0.2 and total_coupling > 20:
            risks.append(f"Highly rigid/stable with coupling (I = {instability:.2f})")

        # Has complexity hotspots
        hotspots = comp.get("hotspots", [])
        critical_hotspots = [h for h in hotspots if h.get("hotspot_type") == "critical_complexity"]
        if critical_hotspots:
            risks.append(f"{len(critical_hotspots)} critical complexity hotspot(s)")

        return risks

    def _build_summary(self, components: list[dict]) -> dict[str, Any]:
        """Build summary statistics."""
        if not components:
            return {
                "total_components": 0,
                "healthy_count": 0,
                "at_risk_count": 0,
                "critical_count": 0,
                "avg_health_score": 0,
                "total_loc": 0,
                "total_files": 0,
                "avg_coupling": 0,
            }

        grades = [c.get("health_grade", "F") for c in components]
        scores = [c.get("health_score", 0) for c in components]
        coupling = [c.get("total_coupling", 0) for c in components]

        return {
            "total_components": len(components),
            "healthy_count": sum(1 for g in grades if g in ("A", "B")),
            "at_risk_count": sum(1 for g in grades if g in ("C", "D")),
            "critical_count": sum(1 for g in grades if g == "F"),
            "avg_health_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "total_loc": sum(c.get("loc", 0) for c in components),
            "total_files": sum(c.get("file_count", 0) for c in components),
            "avg_coupling": round(sum(coupling) / len(coupling), 1) if coupling else 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "component_inventory.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append(
                "No component data available - layout-scanner or SCC tools may not have run"
            )
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "components": [],
            "healthy_components": [],
            "at_risk_components": [],
            "critical_components": [],
            "summary": {
                "total_components": 0,
                "healthy_count": 0,
                "at_risk_count": 0,
                "critical_count": 0,
                "avg_health_score": 0,
                "total_loc": 0,
                "total_files": 0,
                "avg_coupling": 0,
            },
            "grade_distribution": {
                "A": 0,
                "B": 0,
                "C": 0,
                "D": 0,
                "F": 0,
            },
            "has_data": False,
            "has_critical": False,
            "has_dependencies": False,
        }
