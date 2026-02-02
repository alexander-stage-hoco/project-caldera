"""
Executive summary section - top 3 prioritized insights with remediation guidance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


@dataclass
class Insight:
    """A prioritized insight with remediation guidance."""

    rank: int
    category: str  # security, stability, maintainability, code_quality
    title: str
    description: str
    severity: str  # critical, high, medium, low
    evidence: str  # specific metrics/files supporting this
    remediation: str  # what to do about it
    files: list[str]  # affected files (up to 5)


class ExecutiveSummarySection(BaseSection):
    """
    Executive summary section with prioritized insights.

    This section synthesizes data from all analysis tools to produce
    the top 3 actionable insights with clear remediation guidance.

    Priority hierarchy (per plan):
    1. Security issues (CRITICAL/HIGH CVEs, exposed secrets)
    2. Stability risks (high complexity, untested code)
    3. Maintainability issues (code duplication, tight coupling)
    4. Code quality (linting, style violations)
    """

    config = SectionConfig(
        name="executive_summary",
        title="Executive Summary",
        description="Top 3 prioritized insights with remediation guidance.",
        priority=0,  # Always render first
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch and synthesize data for executive summary.

        Returns:
        - insights: Top 3 prioritized Insight objects
        - risk_summary: Overall risk assessment
        - recommended_actions: List of prioritized actions
        """
        # Gather data from multiple sources
        vuln_data = self._fetch_vulnerability_data(fetcher, run_pk)
        complexity_data = self._fetch_complexity_data(fetcher, run_pk)
        size_data = self._fetch_size_data(fetcher, run_pk)
        health_data = self._fetch_health_data(fetcher, run_pk)
        smell_data = self._fetch_smell_data(fetcher, run_pk)

        # Generate prioritized insights
        all_insights = self._generate_insights(
            vuln_data, complexity_data, size_data, health_data, smell_data
        )

        # Take top 3
        top_insights = all_insights[:3]

        # Calculate risk summary
        risk_summary = self._calculate_risk_summary(
            vuln_data, complexity_data, health_data
        )

        # Generate recommended actions from top insights
        recommended_actions = [
            {"priority": i + 1, "action": ins.remediation, "category": ins.category}
            for i, ins in enumerate(top_insights)
        ]

        return {
            "insights": top_insights,
            "risk_summary": risk_summary,
            "recommended_actions": recommended_actions,
            "has_insights": len(top_insights) > 0,
            "total_files": health_data.get("total_files", 0),
            "total_loc": health_data.get("total_loc", 0),
            "vuln_count": vuln_data.get("total_count", 0),
            "critical_vuln_count": vuln_data.get("critical_count", 0),
            "high_complexity_files": complexity_data.get("total_high_complexity", 0),
            "security_scanned": vuln_data.get("scan_ran", False),
        }

    def _fetch_vulnerability_data(
        self, fetcher: DataFetcher, run_pk: int
    ) -> dict[str, Any]:
        """Fetch vulnerability summary data."""
        try:
            summary = fetcher.fetch("vulnerability_summary", run_pk)
            total = sum(s.get("count", 0) for s in summary)
            critical = next(
                (s.get("count", 0) for s in summary if s.get("severity") == "CRITICAL"),
                0,
            )
            high = next(
                (s.get("count", 0) for s in summary if s.get("severity") == "HIGH"),
                0,
            )

            # Get top CVEs for evidence
            top_cves = fetcher.fetch("vulnerability_top_cves", run_pk, limit=5)

            # Track if scan was actually run (vs just no vulnerabilities found)
            scan_ran = len(summary) > 0 or total > 0

            return {
                "summary": summary,
                "total_count": total,
                "critical_count": critical,
                "high_count": high,
                "top_cves": top_cves,
                "scan_ran": scan_ran,
            }
        except Exception:
            return {
                "summary": [],
                "total_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "top_cves": [],
                "scan_ran": False,
            }

    def _fetch_complexity_data(
        self, fetcher: DataFetcher, run_pk: int
    ) -> dict[str, Any]:
        """Fetch complexity hotspot data."""
        try:
            hotspots = fetcher.fetch(
                "file_hotspots", run_pk, order_by="complexity", limit=15
            )

            # Tier complexity by severity
            critical_complexity = [h for h in hotspots if (h.get("complexity") or 0) > 100]
            high_complexity = [h for h in hotspots if 50 < (h.get("complexity") or 0) <= 100]
            medium_complexity = [h for h in hotspots if 20 < (h.get("complexity") or 0) <= 50]

            # Find function-level hotspots (files with very high max_ccn)
            # These indicate single functions that are extremely complex
            function_hotspots = [
                h for h in hotspots
                if (h.get("max_ccn") or 0) > 30  # Single function with CCN > 30
            ]
            # Sort by max_ccn to find worst single-function complexity
            function_hotspots.sort(key=lambda x: x.get("max_ccn") or 0, reverse=True)

            return {
                "hotspots": hotspots,
                "critical_complexity_count": len(critical_complexity),
                "high_complexity_count": len(high_complexity),
                "medium_complexity_count": len(medium_complexity),
                "total_high_complexity": len(critical_complexity) + len(high_complexity) + len(medium_complexity),
                "max_complexity": hotspots[0].get("complexity") if hotspots else 0,
                "top_file": hotspots[0].get("relative_path") if hotspots else None,
                "critical_files": [h.get("relative_path", "") for h in critical_complexity],
                "high_files": [h.get("relative_path", "") for h in high_complexity],
                "function_hotspots": function_hotspots,
                "max_function_ccn": function_hotspots[0].get("max_ccn") if function_hotspots else 0,
                "max_function_file": function_hotspots[0].get("relative_path") if function_hotspots else None,
            }
        except Exception:
            return {
                "hotspots": [],
                "critical_complexity_count": 0,
                "high_complexity_count": 0,
                "medium_complexity_count": 0,
                "total_high_complexity": 0,
                "max_complexity": 0,
                "top_file": None,
                "critical_files": [],
                "high_files": [],
                "function_hotspots": [],
                "max_function_ccn": 0,
                "max_function_file": None,
            }

    # Patterns for auto-generated files that should be excluded from size analysis
    AUTO_GENERATED_PATTERNS = (
        ".Designer.cs",
        ".designer.cs",
        ".generated.cs",
        ".g.cs",
        ".g.i.cs",
        "AssemblyInfo.cs",
        "GlobalUsings.g.cs",
        ".min.js",
        ".min.css",
        "package-lock.json",
        "yarn.lock",
    )

    def _is_auto_generated(self, path: str) -> bool:
        """Check if a file path matches auto-generated file patterns."""
        return any(path.endswith(pattern) for pattern in self.AUTO_GENERATED_PATTERNS)

    def _fetch_size_data(
        self, fetcher: DataFetcher, run_pk: int
    ) -> dict[str, Any]:
        """Fetch file size hotspot data."""
        try:
            hotspots = fetcher.fetch(
                "file_hotspots", run_pk, order_by="loc", limit=20  # Fetch more to allow filtering
            )

            # Filter out auto-generated files
            hotspots = [h for h in hotspots if not self._is_auto_generated(h.get("relative_path", ""))]

            # Large files (> 1000 LOC)
            large_files = [h for h in hotspots if (h.get("loc_total") or 0) > 1000]
            very_large_files = [h for h in hotspots if (h.get("loc_total") or 0) > 2000]

            return {
                "hotspots": hotspots[:10],  # Limit to 10 after filtering
                "large_file_count": len(large_files),
                "very_large_file_count": len(very_large_files),
                "max_loc": hotspots[0].get("loc_total") if hotspots else 0,
                "top_file": hotspots[0].get("relative_path") if hotspots else None,
                "large_files": [h.get("relative_path", "") for h in large_files[:5]],
            }
        except Exception:
            return {
                "hotspots": [],
                "large_file_count": 0,
                "very_large_file_count": 0,
                "max_loc": 0,
                "top_file": None,
                "large_files": [],
            }

    def _fetch_health_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """Fetch overall repository health data."""
        try:
            health = fetcher.fetch("repo_health", run_pk)
            if health:
                return health[0]
            return {}
        except Exception:
            return {}

    def _fetch_smell_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """Fetch code smell data."""
        try:
            hotspots = fetcher.fetch("file_hotspots", run_pk, order_by="smells", limit=10)
            total_smells = sum(h.get("smell_count", 0) for h in hotspots)

            return {
                "hotspots": hotspots,
                "total_smells": total_smells,
                "top_file": hotspots[0].get("relative_path") if hotspots else None,
                "top_smell_count": hotspots[0].get("smell_count", 0) if hotspots else 0,
            }
        except Exception:
            return {
                "hotspots": [],
                "total_smells": 0,
                "top_file": None,
                "top_smell_count": 0,
            }

    def _generate_insights(
        self,
        vuln_data: dict[str, Any],
        complexity_data: dict[str, Any],
        size_data: dict[str, Any],
        health_data: dict[str, Any],
        smell_data: dict[str, Any],
    ) -> list[Insight]:
        """Generate prioritized insights from all data sources."""
        insights: list[Insight] = []

        # Priority 0: Security scanning not performed (highest priority warning)
        scan_ran = vuln_data.get("scan_ran", False)
        critical_count = vuln_data.get("critical_count", 0)
        high_vuln_count = vuln_data.get("high_count", 0)

        if not scan_ran and critical_count == 0 and high_vuln_count == 0:
            # No security scan was run - note as informational, not a code finding
            insights.append(
                Insight(
                    rank=0,
                    category="security",
                    title="Security Scanning Not Performed",
                    description=(
                        "No vulnerability scanning was performed in this analysis. "
                        "Dependency vulnerabilities and code security issues may exist but are undetected."
                    ),
                    severity="medium",  # Lower severity - this is a process gap, not a code finding
                    evidence="No Trivy, Semgrep, or other security scan results found in this run",
                    remediation=(
                        "Run security scanning tools: Trivy for dependency vulnerabilities, "
                        "Semgrep for code-level security issues. "
                        "Consider adding security scans to CI/CD pipeline."
                    ),
                    files=[],
                )
            )

        # Priority 1: Security vulnerabilities (CRITICAL/HIGH CVEs)
        if critical_count > 0:
            top_cves = vuln_data.get("top_cves", [])
            cve_list = ", ".join(c.get("vulnerability_id", "")[:15] for c in top_cves[:3])
            affected = list({c.get("package_name", "") for c in top_cves[:5]})

            insights.append(
                Insight(
                    rank=0,
                    category="security",
                    title=f"{critical_count} Critical Vulnerabilities Detected",
                    description=(
                        f"Found {critical_count} CRITICAL severity vulnerabilities "
                        f"that require immediate attention."
                    ),
                    severity="critical",
                    evidence=f"CVEs: {cve_list}" if cve_list else "Critical CVEs found",
                    remediation=(
                        "Update affected packages immediately. "
                        "Review each CVE for available patches. "
                        "Consider temporary mitigations if patches unavailable."
                    ),
                    files=affected,
                )
            )

        if high_vuln_count > 0:
            top_cves = vuln_data.get("top_cves", [])
            affected = list({c.get("package_name", "") for c in top_cves[:5]})

            insights.append(
                Insight(
                    rank=0,
                    category="security",
                    title=f"{high_vuln_count} High-Severity Vulnerabilities",
                    description=(
                        f"Found {high_vuln_count} HIGH severity vulnerabilities "
                        f"that should be addressed promptly."
                    ),
                    severity="high",
                    evidence=f"Affecting packages: {', '.join(affected[:3])}",
                    remediation=(
                        "Prioritize updating packages with HIGH severity CVEs. "
                        "Check for breaking changes in updated versions."
                    ),
                    files=affected,
                )
            )

        # Priority 2: Tiered complexity insights
        critical_complexity_count = complexity_data.get("critical_complexity_count", 0)
        high_complexity_count = complexity_data.get("high_complexity_count", 0)
        medium_complexity_count = complexity_data.get("medium_complexity_count", 0)
        max_complexity = complexity_data.get("max_complexity", 0)
        hotspots = complexity_data.get("hotspots", [])

        # Critical complexity (CCN > 100)
        if critical_complexity_count > 0:
            critical_files = complexity_data.get("critical_files", [])
            top_critical = hotspots[0] if hotspots else {}

            insights.append(
                Insight(
                    rank=0,
                    category="stability",
                    title=f"{critical_complexity_count} Files Have Critical Complexity (CCN>100)",
                    description=(
                        f"Files with CCN > 100 are virtually untestable and represent "
                        f"severe stability risks. The highest is {top_critical.get('relative_path', 'unknown')} "
                        f"with CCN={max_complexity}."
                    ),
                    severity="critical",
                    evidence=(
                        f"Top file: {top_critical.get('relative_path', 'N/A')} (CCN={max_complexity}). "
                        f"These files need architectural redesign, not just refactoring."
                    ),
                    remediation=(
                        f"CRITICAL: {top_critical.get('relative_path', 'This file')} should be decomposed "
                        f"into 3-4 focused classes. Consider state machine or pipeline patterns. "
                        f"Target CCN<30 per class."
                    ),
                    files=critical_files[:5],
                )
            )

        # High complexity (CCN 50-100)
        if high_complexity_count > 0:
            high_files = complexity_data.get("high_files", [])
            insights.append(
                Insight(
                    rank=0,
                    category="stability",
                    title=f"{high_complexity_count} Files Have High Complexity (CCN 50-100)",
                    description=(
                        "Files with CCN 50-100 are difficult to maintain and test. "
                        "They require systematic refactoring with test coverage first."
                    ),
                    severity="high",
                    evidence=f"Files: {', '.join(high_files[:3])}",
                    remediation=(
                        "Add comprehensive unit tests before refactoring. "
                        "Extract complex methods into smaller functions. "
                        "Consider breaking into multiple classes if responsibilities overlap."
                    ),
                    files=high_files[:5],
                )
            )

        # Medium complexity (CCN 20-50) - only add if we don't have enough insights
        if medium_complexity_count > 3 and len(insights) < 2:
            insights.append(
                Insight(
                    rank=0,
                    category="stability",
                    title=f"{medium_complexity_count} Files Have Elevated Complexity (CCN 20-50)",
                    description=(
                        "These files are more complex than recommended and should "
                        "be monitored to prevent further complexity growth."
                    ),
                    severity="medium",
                    evidence=f"{medium_complexity_count} files exceed the recommended CCN threshold of 20",
                    remediation=(
                        "Refactor during regular development work. "
                        "Focus on extracting methods to reduce nesting and branching. "
                        "Use guard clauses and early returns."
                    ),
                    files=[h.get("relative_path", "") for h in hotspots[:5]],
                )
            )

        # Function-level hotspots (single functions with CCN > 30)
        function_hotspots = complexity_data.get("function_hotspots", [])
        max_function_ccn = complexity_data.get("max_function_ccn", 0)
        max_function_file = complexity_data.get("max_function_file")

        if max_function_ccn > 40 and len(function_hotspots) > 0:
            # Highlight extreme single-function complexity
            affected_files = [h.get("relative_path", "") for h in function_hotspots[:5]]
            insights.append(
                Insight(
                    rank=0,
                    category="stability",
                    title=f"Function-Level Hotspot: Single Function with CCN={max_function_ccn}",
                    description=(
                        f"The file {max_function_file} contains a single function with CCN={max_function_ccn}. "
                        f"Functions with CCN > 30 are extremely difficult to understand and test."
                    ),
                    severity="high",
                    evidence=(
                        f"{len(function_hotspots)} files have functions with CCN > 30. "
                        f"Highest: {max_function_file} (max function CCN={max_function_ccn})"
                    ),
                    remediation=(
                        f"Extract the complex function in {max_function_file} into smaller focused methods. "
                        "Use early returns to reduce nesting. "
                        "Consider the Strategy pattern for complex branching logic."
                    ),
                    files=affected_files,
                )
            )

        # Priority 3: Large file sizes
        large_file_count = size_data.get("large_file_count", 0)
        very_large_count = size_data.get("very_large_file_count", 0)
        max_loc = size_data.get("max_loc", 0)

        if very_large_count > 0:
            large_files = size_data.get("large_files", [])
            top_file = size_data.get("top_file", "unknown")
            insights.append(
                Insight(
                    rank=0,
                    category="maintainability",
                    title=f"{very_large_count} Files Exceed 2000 LOC",
                    description=(
                        f"Very large files are difficult to navigate and often violate "
                        f"single responsibility principle. Largest: {top_file} ({max_loc} LOC)."
                    ),
                    severity="high",
                    evidence=f"Top file: {top_file} with {max_loc} lines of code",
                    remediation=(
                        f"Split {top_file} into multiple focused modules. "
                        "Identify logical boundaries and extract cohesive sections. "
                        "Consider if file contains multiple classes that should be separated."
                    ),
                    files=large_files,
                )
            )
        elif large_file_count > 3:
            large_files = size_data.get("large_files", [])
            insights.append(
                Insight(
                    rank=0,
                    category="maintainability",
                    title=f"{large_file_count} Files Exceed 1000 LOC",
                    description=(
                        "Large files can be harder to navigate and maintain. "
                        "Consider splitting files with multiple responsibilities."
                    ),
                    severity="medium",
                    evidence=f"Largest file: {size_data.get('max_loc', 0)} LOC",
                    remediation=(
                        "Review large files for logical split points. "
                        "Extract utilities and constants into separate modules. "
                        "Move related classes to their own files."
                    ),
                    files=large_files,
                )
            )

        # Priority 4: Code smells
        total_smells = smell_data.get("total_smells", 0)

        if total_smells > 50:
            smell_hotspots = smell_data.get("hotspots", [])
            affected_files = [h.get("relative_path", "") for h in smell_hotspots[:5]]

            insights.append(
                Insight(
                    rank=0,
                    category="maintainability",
                    title=f"{total_smells} Code Smells Identified",
                    description=(
                        "Code smells indicate areas where code quality can be improved "
                        "to enhance maintainability."
                    ),
                    severity="medium",
                    evidence=f"Top file: {smell_data.get('top_file', 'N/A')} "
                    f"with {smell_data.get('top_smell_count', 0)} smells",
                    remediation=(
                        "Address code smells incrementally during regular development. "
                        "Focus on files with highest smell counts first. "
                        "Use IDE refactoring tools to safely transform code."
                    ),
                    files=affected_files,
                )
            )

        # Priority 5: Repository health grade
        health_grade = health_data.get("health_grade")

        if health_grade and health_grade in ("D", "F"):
            insights.append(
                Insight(
                    rank=0,
                    category="code_quality",
                    title=f"Repository Health Grade: {health_grade}",
                    description=(
                        "The repository has significant structural issues that "
                        "may impact development velocity and collaboration."
                    ),
                    severity="medium" if health_grade == "D" else "high",
                    evidence=f"Violations: {health_data.get('violation_count', 0)}",
                    remediation=(
                        "Review git-sizer violations and address largest issues. "
                        "Consider splitting large files or directories. "
                        "Evaluate if binary files should use Git LFS."
                    ),
                    files=[],
                )
            )

        # Sort by severity priority (critical > high > medium > low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda x: severity_order.get(x.severity, 4))

        # Re-assign ranks after sorting
        for i, insight in enumerate(insights):
            insight.rank = i + 1

        return insights

    def _calculate_risk_summary(
        self,
        vuln_data: dict[str, Any],
        complexity_data: dict[str, Any],
        health_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate overall risk summary."""
        critical_vulns = vuln_data.get("critical_count", 0)
        high_vulns = vuln_data.get("high_count", 0)
        scan_ran = vuln_data.get("scan_ran", False)
        critical_complexity = complexity_data.get("critical_complexity_count", 0)
        high_complexity = complexity_data.get("high_complexity_count", 0)
        total_high_complexity = complexity_data.get("total_high_complexity", 0)
        health_grade = health_data.get("health_grade", "N/A")

        # Determine overall risk level
        if critical_vulns > 0:
            overall_risk = "critical"
            risk_description = "Critical vulnerabilities require immediate attention"
        elif critical_complexity > 0:
            overall_risk = "high"
            risk_description = "Critical complexity issues threaten code stability"
        elif high_vulns > 5 or high_complexity > 5:
            overall_risk = "high"
            risk_description = "Significant issues that should be prioritized"
        elif high_vulns > 0 or total_high_complexity > 0:
            overall_risk = "medium"
            risk_description = "Issues present but manageable with scheduled work"
        else:
            overall_risk = "low"
            risk_description = "Repository is in good health"

        # Security status: distinguish between "scanned and clean" vs "not scanned"
        if critical_vulns > 0:
            security_status = "critical"
        elif high_vulns > 0:
            security_status = "warning"
        elif scan_ran:
            security_status = "good"
        else:
            security_status = "not_scanned"

        # Stability status based on complexity tiers
        if critical_complexity > 0:
            stability_status = "critical"
        elif high_complexity > 0 or total_high_complexity > 5:
            stability_status = "warning"
        else:
            stability_status = "good"

        return {
            "overall_risk": overall_risk,
            "risk_description": risk_description,
            "security_status": security_status,
            "stability_status": stability_status,
            "health_grade": health_grade,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "executive_summary.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []

        if data.get("insights") is None:
            errors.append("Missing insights data")

        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "insights": [],
            "risk_summary": {
                "overall_risk": "unknown",
                "risk_description": "Unable to calculate risk summary",
                "security_status": "unknown",
                "stability_status": "unknown",
                "health_grade": "N/A",
            },
            "recommended_actions": [],
            "has_insights": False,
            "total_files": 0,
            "total_loc": 0,
            "vuln_count": 0,
            "critical_vuln_count": 0,
            "high_complexity_files": 0,
        }
