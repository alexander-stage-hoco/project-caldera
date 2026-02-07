"""
Tool readiness section - shows data mart readiness status for all analysis tools.

This section reads scorecard.json files from each tool's evaluation directory
and presents a unified view of tool data quality and readiness for reporting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


# Default tools directory relative to this file
# Path: src/insights/sections/tool_readiness.py -> src/tools
DEFAULT_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"


class ToolReadinessSection(BaseSection):
    """Tool readiness status for data marts and reporting."""

    config = SectionConfig(
        name="tool_readiness",
        title="Tool Readiness Report",
        description="Data quality and readiness status for all analysis tools.",
        priority=0,  # Show first as meta-report
    )

    # Decision thresholds based on normalized score (0-5 scale)
    DECISION_THRESHOLDS = {
        "STRONG_PASS": 4.0,  # >= 80%
        "PASS": 3.5,  # >= 70%
        "WEAK_PASS": 3.0,  # >= 60%
        "FAIL": 0.0,  # < 60%
    }

    # Tool purposes for display
    TOOL_PURPOSES = {
        "gitleaks": "Secret detection in git history",
        "trivy": "Vulnerability & IaC misconfiguration scanning",
        "scancode": "License inventory & IP risk analysis",
        "lizard": "Function-level CCN complexity analysis",
        "scc": "Lines of code & COCOMO estimation",
        "roslyn-analyzers": ".NET code quality violations",
        "git-sizer": "Repository health metrics",
        "semgrep": "Security vulnerability detection",
        "pmd-cpd": "Code duplication detection",
        "devskim": "Security rule pattern matching",
        "layout-scanner": "File structure & language classification",
        "sonarqube": "SonarQube issue and metric analysis",
        "symbol-scanner": "Code symbol and call graph analysis",
        "dependensee": ".NET dependency graph analysis",
        "dotcover": "Code coverage analysis",
        "git-fame": "Git authorship/ownership metrics",
    }

    def __init__(self, tools_dir: Path | None = None):
        """
        Initialize the section.

        Args:
            tools_dir: Path to the tools directory. Defaults to src/tools.
        """
        self.tools_dir = tools_dir or DEFAULT_TOOLS_DIR

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch tool readiness data from scorecard.json files.

        Unlike other sections, this doesn't query the database but reads
        scorecard files directly from the filesystem.

        Returns data including:
        - tools: List of tool readiness entries
        - summary: Counts by readiness category
        - ready_for_reports: Tools ready for production use
        - needs_investigation: Tools needing review
        - not_ready: Tools not ready for reports
        """
        tools = self._scan_scorecards()

        # Categorize tools
        ready_for_reports = [t for t in tools if t["category"] == "ready"]
        needs_investigation = [t for t in tools if t["category"] == "investigate"]
        not_ready = [t for t in tools if t["category"] == "not_ready"]
        no_scorecard = [t for t in tools if t["category"] == "no_scorecard"]

        return {
            "tools": tools,
            "ready_for_reports": ready_for_reports,
            "needs_investigation": needs_investigation,
            "not_ready": not_ready,
            "no_scorecard": no_scorecard,
            "summary": {
                "total": len(tools),
                "ready": len(ready_for_reports),
                "investigate": len(needs_investigation),
                "not_ready": len(not_ready),
                "no_scorecard": len(no_scorecard),
            },
            "has_tools": len(tools) > 0,
        }

    def _scan_scorecards(self) -> list[dict[str, Any]]:
        """Scan all tool directories for scorecard.json files."""
        tools = []

        if not self.tools_dir.exists():
            return tools

        for tool_dir in sorted(self.tools_dir.iterdir()):
            if not tool_dir.is_dir():
                continue

            tool_name = tool_dir.name

            # Skip hidden directories and common non-tool directories
            if tool_name.startswith(".") or tool_name in ("__pycache__", "evaluation"):
                continue

            # Skip Makefile.common (it's a file, not a tool)
            if not tool_dir.is_dir():
                continue

            scorecard_path = tool_dir / "evaluation" / "scorecard.json"

            tool_entry = {
                "name": tool_name,
                "purpose": self.TOOL_PURPOSES.get(tool_name, "Unknown"),
            }

            # Try scorecard.json first, then evaluation_report.json as fallback
            eval_report_path = tool_dir / "evaluation" / "results" / "evaluation_report.json"

            if scorecard_path.exists():
                try:
                    scorecard = json.loads(scorecard_path.read_text())
                    parsed = self._parse_scorecard(scorecard)
                    # If scorecard is empty, try evaluation_report.json
                    if parsed.get("decision") == "EMPTY" and eval_report_path.exists():
                        eval_report = json.loads(eval_report_path.read_text())
                        tool_entry.update(self._parse_evaluation_report(eval_report))
                    else:
                        tool_entry.update(parsed)
                except (json.JSONDecodeError, KeyError) as e:
                    tool_entry.update({
                        "category": "no_scorecard",
                        "decision": "ERROR",
                        "score_percent": 0,
                        "total_checks": 0,
                        "passed_checks": 0,
                        "failed_checks": 0,
                        "error": str(e),
                        "dimensions": [],
                        "critical_failures": [],
                    })
            elif eval_report_path.exists():
                # Use evaluation_report.json if scorecard.json doesn't exist
                try:
                    eval_report = json.loads(eval_report_path.read_text())
                    tool_entry.update(self._parse_evaluation_report(eval_report))
                except (json.JSONDecodeError, KeyError) as e:
                    tool_entry.update({
                        "category": "no_scorecard",
                        "decision": "ERROR",
                        "score_percent": 0,
                        "total_checks": 0,
                        "passed_checks": 0,
                        "failed_checks": 0,
                        "error": str(e),
                        "dimensions": [],
                        "critical_failures": [],
                    })
            else:
                # Check for scorecard.md (evaluation exists but JSON missing)
                scorecard_md = tool_dir / "evaluation" / "scorecard.md"
                if scorecard_md.exists():
                    tool_entry.update({
                        "category": "investigate",
                        "decision": "MISSING_JSON",
                        "score_percent": None,
                        "total_checks": None,
                        "passed_checks": None,
                        "failed_checks": None,
                        "has_md_only": True,
                        "dimensions": [],
                        "critical_failures": [],
                    })
                else:
                    tool_entry.update({
                        "category": "no_scorecard",
                        "decision": "NO_EVAL",
                        "score_percent": None,
                        "total_checks": None,
                        "passed_checks": None,
                        "failed_checks": None,
                        "dimensions": [],
                        "critical_failures": [],
                    })

            tools.append(tool_entry)

        return tools

    def _parse_scorecard(self, scorecard: dict[str, Any]) -> dict[str, Any]:
        """Parse a scorecard.json into a tool readiness entry."""
        summary = scorecard.get("summary", {})

        # Handle empty or minimal scorecards
        if not summary:
            return {
                "category": "no_scorecard",
                "decision": "EMPTY",
                "score_percent": None,
                "total_checks": None,
                "passed_checks": None,
                "failed_checks": None,
                "dimensions": [],
                "critical_failures": [],
                "failed_check_details": [],
            }

        decision = summary.get("decision", "UNKNOWN")
        score_percent = summary.get("score_percent", 0)
        total_checks = summary.get("total_checks", 0)
        passed_checks = summary.get("passed", 0)
        failed_checks = summary.get("failed", 0)

        # Categorize based on decision
        if decision == "STRONG_PASS":
            category = "ready"
        elif decision == "PASS":
            category = "ready"
        elif decision == "WEAK_PASS":
            category = "not_ready"
        elif decision == "UNKNOWN":
            category = "no_scorecard"
        else:
            category = "not_ready"

        # Extract dimension summaries
        dimensions = []
        for dim in scorecard.get("dimensions", []):
            dim_entry = {
                "id": dim.get("id", ""),
                "name": dim.get("name", ""),
                "total": dim.get("total_checks", 0),
                "passed": dim.get("passed", 0),
                "failed": dim.get("failed", 0),
                "score": dim.get("score", 0),
            }
            dimensions.append(dim_entry)

        # Extract critical failures
        critical_failures = scorecard.get("critical_failures", [])

        # Find failed checks for display
        failed_check_details = []
        for dim in scorecard.get("dimensions", []):
            for check in dim.get("checks", []):
                if not check.get("passed", True):
                    failed_check_details.append({
                        "check_id": check.get("check_id", check.get("name", "")),
                        "dimension": dim.get("name", ""),
                        "message": check.get("message", ""),
                    })

        return {
            "category": category,
            "decision": decision,
            "score_percent": score_percent,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "dimensions": dimensions,
            "critical_failures": critical_failures,
            "failed_check_details": failed_check_details[:5],  # Limit to top 5
        }

    def _parse_evaluation_report(self, report: dict[str, Any]) -> dict[str, Any]:
        """Parse an evaluation_report.json into a tool readiness entry."""
        summary = report.get("summary", {})
        decision = report.get("decision", summary.get("decision", "UNKNOWN"))
        score = report.get("score", summary.get("score", 0))
        score_percent = score * 100 if score <= 1 else score

        total_checks = summary.get("total", 0)
        passed_checks = summary.get("passed", 0)
        failed_checks = summary.get("failed", 0)

        # Categorize based on decision
        if decision == "STRONG_PASS":
            category = "ready"
        elif decision == "PASS":
            category = "ready"
        elif decision == "WEAK_PASS":
            category = "not_ready"
        else:
            category = "not_ready"

        # Extract dimension summaries from score_by_category
        dimensions = []
        score_by_category = summary.get("score_by_category", {})
        passed_by_category = summary.get("passed_by_category", {})

        for cat_name, cat_score in score_by_category.items():
            passed_info = passed_by_category.get(cat_name, [0, 0])
            dim_entry = {
                "id": cat_name[:2].upper(),
                "name": cat_name.replace("_", " ").title(),
                "total": passed_info[1] if len(passed_info) > 1 else 0,
                "passed": passed_info[0] if len(passed_info) > 0 else 0,
                "failed": (passed_info[1] - passed_info[0]) if len(passed_info) > 1 else 0,
                "score": cat_score,
            }
            dimensions.append(dim_entry)

        # Find failed checks for display
        failed_check_details = []
        for check in report.get("checks", []):
            if not check.get("passed", True):
                failed_check_details.append({
                    "check_id": check.get("check_id", ""),
                    "dimension": check.get("category", "").replace("_", " ").title(),
                    "message": check.get("message", ""),
                })

        return {
            "category": category,
            "decision": decision,
            "score_percent": round(score_percent, 2),
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "dimensions": dimensions,
            "critical_failures": [],
            "failed_check_details": failed_check_details[:5],
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "tool_readiness.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        # Tool readiness data is optional - no validation errors
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "tools": [],
            "ready_for_reports": [],
            "needs_investigation": [],
            "not_ready": [],
            "no_scorecard": [],
            "summary": {
                "total": 0,
                "ready": 0,
                "investigate": 0,
                "not_ready": 0,
                "no_scorecard": 0,
            },
            "has_tools": False,
        }
