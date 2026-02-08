"""
Code quality rules section - Rule-level analysis of code smells from Semgrep.

Uses mart_semgrep_rule_hotspots to identify which code quality rules are most
frequently violated, helping prioritize technical debt remediation and identify
systemic code quality issues.
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CodeQualityRulesSection(BaseSection):
    """Rule-level analysis of code smells from Semgrep."""

    config = SectionConfig(
        name="code_quality_rules",
        title="Code Quality Rules",
        description="Rule-level analysis of code smells identifying systemic quality issues.",
        priority=5.1,  # After cross_tool (5.0), groups with code quality sections
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch code quality rule data.

        Returns data including:
        - rules: Top 30 rules by violation count
        - high_risk_rules: High/critical risk only
        - summary: Total rules, violations, files affected
        - category_breakdown: Rules grouped by category
        - severity_distribution: Violation counts by severity
        """
        try:
            rules = fetcher.fetch("semgrep_rule_hotspots", run_pk, limit=30)
        except Exception:
            rules = []

        # Calculate summary statistics
        risk_levels: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        categories: dict[str, dict[str, int]] = {}
        total_violations = 0
        total_files_affected = 0
        severity_distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        widespread_rules = 0

        for r in rules:
            level = r.get("risk_level", "medium")
            if level in risk_levels:
                risk_levels[level] += 1

            # Accumulate totals
            total_violations += r.get("smell_count", 0)
            total_files_affected += r.get("files_affected", 0)

            # Severity distribution
            severity_distribution["critical"] += r.get("severity_critical", 0)
            severity_distribution["high"] += r.get("severity_high", 0)
            severity_distribution["medium"] += r.get("severity_medium", 0)
            severity_distribution["low"] += r.get("severity_low", 0)
            severity_distribution["info"] += r.get("severity_info", 0)

            # Count widespread rules (affecting 5+ directories)
            if r.get("directories_affected", 0) >= 5:
                widespread_rules += 1

            # Category breakdown
            category = r.get("dd_category") or "unknown"
            if category not in categories:
                categories[category] = {"count": 0, "violations": 0}
            categories[category]["count"] += 1
            categories[category]["violations"] += r.get("smell_count", 0)

        # Filter by risk level
        high_risk_rules = [
            r for r in rules if r.get("risk_level") in ("critical", "high")
        ]

        # Category breakdown as sorted list
        category_breakdown = sorted(
            [
                {"category": cat, "count": data["count"], "violations": data["violations"]}
                for cat, data in categories.items()
            ],
            key=lambda x: x["violations"],
            reverse=True,
        )

        summary = {
            "total_rules": len(rules),
            "total_violations": total_violations,
            "total_files_affected": total_files_affected,
            "critical_count": risk_levels["critical"],
            "high_count": risk_levels["high"],
            "medium_count": risk_levels["medium"],
            "low_count": risk_levels["low"],
            "widespread_rules": widespread_rules,
            "critical_violations": severity_distribution["critical"],
            "high_violations": severity_distribution["high"],
            "medium_violations": severity_distribution["medium"],
        }

        return {
            "rules": rules,
            "high_risk_rules": high_risk_rules,
            "summary": summary,
            "category_breakdown": category_breakdown,
            "severity_distribution": severity_distribution,
            "has_data": len(rules) > 0,
            "has_high_risk": len(high_risk_rules) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "code_quality_rules.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No code quality rule data available - Semgrep tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "rules": [],
            "high_risk_rules": [],
            "summary": {
                "total_rules": 0,
                "total_violations": 0,
                "total_files_affected": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "widespread_rules": 0,
                "critical_violations": 0,
                "high_violations": 0,
                "medium_violations": 0,
            },
            "category_breakdown": [],
            "severity_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
            },
            "has_data": False,
            "has_high_risk": False,
        }
