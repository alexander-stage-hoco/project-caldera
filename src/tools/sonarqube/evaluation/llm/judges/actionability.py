"""Actionability LLM Judge for SonarQube evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class ActionabilityJudge(BaseJudge):
    """Evaluates whether SonarQube output is actionable for remediation."""

    @property
    def dimension_name(self) -> str:
        return "actionability"

    @property
    def weight(self) -> float:
        return 0.20

    def get_default_prompt(self) -> str:
        return """You are evaluating whether the SonarQube analysis output is actionable.

Assess:
1. Report clarity (40%): Is the output understandable?
2. Prioritization (30%): Are issues ranked by severity?
3. Remediation guidance (30%): Are fix suggestions present?

Evidence:
{{ evidence }}

Consider:
- Can a developer use this output to fix issues?
- Is severity information clear and consistent?
- Are issue locations (file, line) provided?
- Do rules include remediation information?

Respond with JSON:
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>",
  "evidence_cited": ["<evidence item 1>", ...],
  "recommendations": ["<recommendation 1>", ...],
  "sub_scores": {
    "report_clarity": <1-5>,
    "prioritization": <1-5>,
    "remediation_guidance": <1-5>
  }
}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect actionability data for evaluation."""
        data = self.analysis_results

        issues = data.get("issues", {}).get("items", [])
        rules = data.get("rules", {}).get("by_key", {})
        qg = data.get("quality_gate", {})
        hotspots = data.get("derived_insights", {}).get("hotspots", [])

        # Sample issues for evidence
        sample_issues = issues[:5]

        return {
            "quality_gate_status": qg.get("status"),
            "quality_gate_conditions": len(qg.get("conditions", [])),
            "total_issues": len(issues),
            "issues_with_line": sum(1 for i in issues if i.get("line")),
            "issues_with_severity": sum(1 for i in issues if i.get("severity")),
            "rules_count": len(rules),
            "rules_with_description": sum(1 for r in rules.values() if r.get("html_desc")),
            "hotspots_count": len(hotspots),
            "sample_issues": sample_issues,
        }

    def evaluate(self) -> JudgeResult:
        """Evaluate output actionability."""
        data = self.analysis_results

        clarity_score = self._evaluate_clarity(data)
        prioritization_score = self._evaluate_prioritization(data)
        remediation_score = self._evaluate_remediation(data)

        # Weighted average
        total_score = round(clarity_score * 0.40 + prioritization_score * 0.30 + remediation_score * 0.30)
        total_score = max(1, min(5, total_score))

        evidence = []
        recommendations = []

        # Check quality gate
        qg = data.get("quality_gate", {})
        evidence.append(f"Quality gate status: {qg.get('status', 'N/A')}")

        # Check hotspots
        hotspots = data.get("derived_insights", {}).get("hotspots", [])
        evidence.append(f"Hotspots identified: {len(hotspots)}")

        # Check issue locations
        issues = data.get("issues", {}).get("items", [])
        issues_with_line = sum(1 for i in issues if i.get("line"))
        evidence.append(f"Issues with line numbers: {issues_with_line}/{len(issues)}")

        if clarity_score < 4:
            recommendations.append("Consider adding summary statistics to output")
        if prioritization_score < 4:
            recommendations.append("Ensure all issues have severity ratings")
        if remediation_score < 4:
            recommendations.append("Add remediation effort estimates where available")

        return self._create_result(
            score=total_score,
            confidence=0.75,
            reasoning="Evaluated clarity, prioritization, and remediation guidance",
            evidence=evidence,
            recommendations=recommendations,
            sub_scores={
                "report_clarity": clarity_score,
                "prioritization": prioritization_score,
                "remediation_guidance": remediation_score,
            },
        )

    def _evaluate_clarity(self, data: dict) -> int:
        """Evaluate report clarity."""
        score = 1

        # Check for schema version
        if data.get("schema_version"):
            score += 1

        # Check for derived insights
        if data.get("derived_insights", {}).get("hotspots"):
            score += 1

        # Check for directory rollups
        if data.get("derived_insights", {}).get("directory_rollups"):
            score += 1

        # Check for quality gate with conditions
        qg = data.get("quality_gate", {})
        if qg.get("conditions"):
            score += 1

        return min(5, score)

    def _evaluate_prioritization(self, data: dict) -> int:
        """Evaluate issue prioritization."""
        issues = data.get("issues", {}).get("items", [])

        if not issues:
            return 3  # Neutral if no issues

        # Check if all issues have severity
        with_severity = sum(1 for i in issues if i.get("severity"))
        ratio = with_severity / len(issues)

        if ratio < 0.5:
            return 2
        elif ratio < 0.9:
            return 3
        elif ratio < 1.0:
            return 4
        else:
            return 5

    def _evaluate_remediation(self, data: dict) -> int:
        """Evaluate remediation guidance availability."""
        rules = data.get("rules", {}).get("by_key", {})

        if not rules:
            return 2

        # Check for rules with remediation info
        with_remediation = sum(
            1 for r in rules.values()
            if r.get("html_desc") or r.get("remediation_effort")
        )

        if len(rules) == 0:
            return 3

        ratio = with_remediation / len(rules)

        if ratio < 0.5:
            return 2
        elif ratio < 0.8:
            return 3
        elif ratio < 0.95:
            return 4
        else:
            return 5
