"""
SonarQube deep dive section - comprehensive analysis of SonarQube findings.

Focuses on SonarQube-unique capabilities not covered by other tools:
- Cognitive complexity (unique to SonarQube)
- Issue categorization (Bug/Vulnerability/Code Smell/Security Hotspot)
- Effort estimation (minutes/hours/days)
- Rule-level analysis with impact scoring
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class SonarQubeDeepDiveSection(BaseSection):
    """Comprehensive analysis of SonarQube findings with unique metrics."""

    config = SectionConfig(
        name="sonarqube_deep_dive",
        title="SonarQube Deep Dive",
        description="Comprehensive SonarQube analysis: cognitive complexity, issue types, effort estimation, and rule hotspots.",
        priority=6,  # Groups with code quality sections
    )

    # Cognitive complexity thresholds
    COGNITIVE_CRITICAL = 50
    COGNITIVE_HIGH = 25
    COGNITIVE_MEDIUM = 15

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch SonarQube deep dive data.

        Returns data including:
        - summary: Aggregate statistics
        - hotspot_files: Files with most issues
        - cognitive_hotspots: Highest cognitive complexity files
        - rule_hotspots: Most violated rules
        - type_breakdown: Issues by type
        - health_score: 0-100 composite score
        - cognitive_analysis: Cognitive complexity breakdown
        """
        # Fetch summary statistics
        try:
            summary_results = fetcher.fetch("sonarqube_summary", run_pk)
            summary = summary_results[0] if summary_results else {}
        except Exception:
            summary = {}

        # Fetch hotspot files
        try:
            hotspot_files = fetcher.fetch("sonarqube_hotspot_files", run_pk, limit=25)
        except Exception:
            hotspot_files = []

        # Fetch cognitive complexity hotspots
        try:
            cognitive_hotspots = fetcher.fetch("sonarqube_cognitive_hotspots", run_pk, limit=25)
        except Exception:
            cognitive_hotspots = []

        # Fetch rule hotspots
        try:
            rule_hotspots = fetcher.fetch("sonarqube_rule_hotspots", run_pk, limit=30)
        except Exception:
            rule_hotspots = []

        # Fetch type breakdown
        try:
            type_breakdown = fetcher.fetch("sonarqube_type_breakdown", run_pk)
        except Exception:
            type_breakdown = []

        # Calculate health score
        health_score = self._calculate_health_score(summary)

        # Build cognitive analysis
        cognitive_analysis = self._build_cognitive_analysis(summary, cognitive_hotspots)

        # Calculate severity distribution
        severity_distribution = {
            "blocker": summary.get("total_blocker", 0),
            "critical": summary.get("total_critical", 0),
            "major": summary.get("total_major", 0),
            "minor": summary.get("total_minor", 0),
            "info": summary.get("total_info", 0),
        }

        # Calculate rule statistics
        rule_stats = self._calculate_rule_stats(rule_hotspots)

        # Calculate effort metrics
        effort_metrics = self._calculate_effort_metrics(rule_hotspots)

        return {
            "summary": summary,
            "hotspot_files": hotspot_files,
            "cognitive_hotspots": cognitive_hotspots,
            "rule_hotspots": rule_hotspots,
            "type_breakdown": type_breakdown,
            "health_score": health_score,
            "health_grade": self._score_to_grade(health_score),
            "cognitive_analysis": cognitive_analysis,
            "severity_distribution": severity_distribution,
            "rule_stats": rule_stats,
            "effort_metrics": effort_metrics,
            "has_data": bool(summary.get("total_files")),
            "has_issues": summary.get("total_issues", 0) > 0,
            "has_cognitive_data": summary.get("total_cognitive_complexity", 0) > 0,
        }

    def _calculate_health_score(self, summary: dict) -> int:
        """
        Calculate overall SonarQube health score (0-100, higher = healthier).

        Factors considered:
        - Issue density (issues per KLOC)
        - Severity composition
        - Cognitive complexity distribution
        - Bug/vulnerability counts
        """
        if not summary.get("total_files"):
            return 100  # No data, assume healthy

        total_ncloc = max(summary.get("total_ncloc", 1), 1)
        total_files = max(summary.get("total_files", 1), 1)

        # Issue density penalty (max 30 points)
        issue_density = summary.get("total_issues", 0) / (total_ncloc / 1000)
        issue_penalty = min(30, issue_density * 3)

        # Severity penalty (max 30 points)
        blocker_critical = (
            summary.get("total_blocker", 0) * 5 +
            summary.get("total_critical", 0) * 3 +
            summary.get("total_major", 0) * 1
        )
        severity_penalty = min(30, blocker_critical / total_files * 10)

        # Bug/vulnerability penalty (max 20 points)
        bugs_vulns = summary.get("total_bugs", 0) + summary.get("total_vulnerabilities", 0)
        bug_penalty = min(20, bugs_vulns / total_files * 15)

        # Cognitive complexity penalty (max 20 points)
        files_critical = summary.get("files_critical_cognitive", 0)
        files_high = summary.get("files_high_cognitive", 0)
        cognitive_penalty = min(20, (files_critical * 4 + files_high * 2) / total_files * 10)

        score = max(0, 100 - issue_penalty - severity_penalty - bug_penalty - cognitive_penalty)
        return round(score)

    def _score_to_grade(self, score: int) -> str:
        """Convert health score to letter grade (higher = better)."""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def _build_cognitive_analysis(
        self, summary: dict, cognitive_hotspots: list[dict]
    ) -> dict[str, Any]:
        """Build cognitive complexity analysis breakdown."""
        total_files = max(summary.get("total_files", 1), 1)

        critical_files = summary.get("files_critical_cognitive", 0)
        high_files = summary.get("files_high_cognitive", 0)
        medium_files = summary.get("files_medium_cognitive", 0)

        return {
            "total": summary.get("total_cognitive_complexity", 0),
            "average": summary.get("avg_cognitive_complexity", 0),
            "max": summary.get("max_cognitive_complexity", 0),
            "critical_count": critical_files,
            "high_count": high_files,
            "medium_count": medium_files,
            "critical_pct": round(critical_files / total_files * 100, 1) if total_files else 0,
            "high_pct": round(high_files / total_files * 100, 1) if total_files else 0,
            "top_files": cognitive_hotspots[:10],
            "thresholds": {
                "critical": self.COGNITIVE_CRITICAL,
                "high": self.COGNITIVE_HIGH,
                "medium": self.COGNITIVE_MEDIUM,
            },
        }

    def _calculate_rule_stats(self, rule_hotspots: list[dict]) -> dict[str, Any]:
        """Calculate rule-level statistics."""
        if not rule_hotspots:
            return {
                "total_rules": 0,
                "critical_rules": 0,
                "high_rules": 0,
                "total_open": 0,
                "types": {},
            }

        types: dict[str, int] = {}
        critical_count = 0
        high_count = 0
        total_open = 0

        for rule in rule_hotspots:
            risk = rule.get("risk_level", "low")
            if risk == "critical":
                critical_count += 1
            elif risk == "high":
                high_count += 1

            issue_type = rule.get("issue_type", "UNKNOWN")
            types[issue_type] = types.get(issue_type, 0) + 1
            total_open += rule.get("open_count", 0)

        return {
            "total_rules": len(rule_hotspots),
            "critical_rules": critical_count,
            "high_rules": high_count,
            "total_open": total_open,
            "types": types,
        }

    def _calculate_effort_metrics(self, rule_hotspots: list[dict]) -> dict[str, Any]:
        """Calculate effort estimation metrics."""
        if not rule_hotspots:
            return {
                "total_minutes": 0,
                "total_hours": 0,
                "total_days": 0,
                "avg_per_rule": 0,
                "top_effort_rules": [],
            }

        total_minutes = sum(r.get("total_effort_minutes", 0) or 0 for r in rule_hotspots)

        # Sort by effort
        sorted_by_effort = sorted(
            rule_hotspots,
            key=lambda x: x.get("total_effort_minutes", 0) or 0,
            reverse=True,
        )

        return {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "total_days": round(total_minutes / 480, 1),  # 8-hour days
            "avg_per_rule": round(total_minutes / len(rule_hotspots), 1) if rule_hotspots else 0,
            "top_effort_rules": sorted_by_effort[:5],
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "sonarqube_deep_dive.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No SonarQube data available - SonarQube tool may not have run")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "summary": {},
            "hotspot_files": [],
            "cognitive_hotspots": [],
            "rule_hotspots": [],
            "type_breakdown": [],
            "health_score": 100,
            "health_grade": "A",
            "cognitive_analysis": {
                "total": 0,
                "average": 0,
                "max": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "critical_pct": 0,
                "high_pct": 0,
                "top_files": [],
                "thresholds": {
                    "critical": self.COGNITIVE_CRITICAL,
                    "high": self.COGNITIVE_HIGH,
                    "medium": self.COGNITIVE_MEDIUM,
                },
            },
            "severity_distribution": {
                "blocker": 0,
                "critical": 0,
                "major": 0,
                "minor": 0,
                "info": 0,
            },
            "rule_stats": {
                "total_rules": 0,
                "critical_rules": 0,
                "high_rules": 0,
                "total_open": 0,
                "types": {},
            },
            "effort_metrics": {
                "total_minutes": 0,
                "total_hours": 0,
                "total_days": 0,
                "avg_per_rule": 0,
                "top_effort_rules": [],
            },
            "has_data": False,
            "has_issues": False,
            "has_cognitive_data": False,
        }
