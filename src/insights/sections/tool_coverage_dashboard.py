"""
Tool coverage dashboard section - shows runtime tool execution status for a collection.

This section queries the database to show which tools ran for a given collection
and how many files each tool analyzed. It complements tool_readiness.py (which
checks evaluation scorecards) by showing runtime execution status.

Key distinction:
- tool_readiness.py = Did tools PASS evaluation? (reads scorecard files)
- tool_coverage_dashboard.py = Did tools RUN for this collection? What did they analyze?
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class ToolCoverageDashboardSection(BaseSection):
    """Runtime tool execution status for a collection run."""

    config = SectionConfig(
        name="tool_coverage_dashboard",
        title="Tool Coverage Dashboard",
        description="Shows which analysis tools ran for this collection and files analyzed.",
        priority=1,  # After tool_readiness (0), before executive_summary (2)
    )

    # Critical tools that should always run for basic analysis
    CRITICAL_TOOLS = {"layout-scanner", "scc", "lizard"}

    # Security-focused tools
    SECURITY_TOOLS = {"semgrep", "gitleaks", "trivy", "devskim"}

    # Tool purposes for display (same as tool_readiness for consistency)
    TOOL_PURPOSES = {
        "layout-scanner": "File structure & language classification",
        "scc": "Lines of code & COCOMO estimation",
        "lizard": "Function-level CCN complexity",
        "semgrep": "Security vulnerability detection",
        "roslyn-analyzers": ".NET code quality violations",
        "sonarqube": "SonarQube issue and metric analysis",
        "trivy": "Container/IaC vulnerability scanning",
        "gitleaks": "Secret detection in git history",
        "symbol-scanner": "Code symbol extraction",
        "scancode": "License and copyright detection",
        "pmd-cpd": "Copy-paste detection",
        "devskim": "Security linting rules",
        "dotcover": ".NET code coverage (Coverlet)",
        "git-fame": "Git contributor statistics",
        "git-sizer": "Git repository size analysis",
        "dependensee": "Dependency visualization",
    }

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch tool coverage data from the database.

        Returns data including:
        - tools: List of all tools with run status and file counts
        - summary: Coverage statistics
        - confidence_level: Assessment of analysis completeness
        - missing_critical: List of missing critical tools
        """
        try:
            tools = fetcher.fetch("tool_coverage_summary", run_pk)
        except Exception:
            tools = []

        # Enrich tools with purpose
        for tool in tools:
            tool["purpose"] = self.TOOL_PURPOSES.get(tool["tool_name"], "Unknown")

        # Categorize tools
        ran = [t for t in tools if t["status"] == "ran"]
        missing = [t for t in tools if t["status"] == "missing"]

        # Calculate confidence level
        critical_ran = sum(1 for t in ran if t["tool_name"] in self.CRITICAL_TOOLS)
        security_ran = sum(1 for t in ran if t["tool_name"] in self.SECURITY_TOOLS)

        if len(missing) == 0:
            confidence = "complete"
        elif critical_ran == len(self.CRITICAL_TOOLS):
            confidence = "high" if security_ran >= 2 else "medium"
        else:
            confidence = "low"

        # Identify missing critical and security tools
        missing_critical = [t for t in missing if t["tool_name"] in self.CRITICAL_TOOLS]
        missing_security = [t for t in missing if t["tool_name"] in self.SECURITY_TOOLS]

        # Calculate total files analyzed (use max across tools as approximation)
        total_files_analyzed = max((t.get("files_analyzed", 0) for t in ran), default=0)

        return {
            "tools": tools,
            "tools_ran": ran,
            "tools_missing": missing,
            "summary": {
                "total": len(tools),
                "ran": len(ran),
                "missing": len(missing),
                "coverage_pct": round(len(ran) / len(tools) * 100, 1) if tools else 0,
                "total_files_analyzed": total_files_analyzed,
            },
            "confidence_level": confidence,
            "missing_critical": missing_critical,
            "missing_security": missing_security,
            "critical_tools": list(self.CRITICAL_TOOLS),
            "security_tools": list(self.SECURITY_TOOLS),
            "has_data": len(tools) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "tool_coverage_dashboard.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if not data.get("has_data"):
            errors.append("No tool coverage data available")

        # Warn if critical tools are missing
        missing_critical = data.get("missing_critical", [])
        if missing_critical:
            tool_names = ", ".join(t["tool_name"] for t in missing_critical)
            errors.append(f"Critical tools missing: {tool_names}")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "tools": [],
            "tools_ran": [],
            "tools_missing": [],
            "summary": {
                "total": 0,
                "ran": 0,
                "missing": 0,
                "coverage_pct": 0,
                "total_files_analyzed": 0,
            },
            "confidence_level": "unknown",
            "missing_critical": [],
            "missing_security": [],
            "critical_tools": list(self.CRITICAL_TOOLS),
            "security_tools": list(self.SECURITY_TOOLS),
            "has_data": False,
        }
