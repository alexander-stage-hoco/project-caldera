"""Coverage Completeness LLM Judge for SonarQube evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class CoverageCompletenessJudge(BaseJudge):
    """Evaluates whether all expected data was extracted from SonarQube."""

    @property
    def dimension_name(self) -> str:
        return "coverage_completeness"

    @property
    def weight(self) -> float:
        return 0.25

    def get_default_prompt(self) -> str:
        return """You are evaluating the completeness of data extracted from SonarQube.

Assess:
1. Metric extraction (40%): Are all relevant metrics captured?
2. Component coverage (30%): Are all files represented in the output?
3. Rule hydration (30%): Is rule metadata complete for all triggered rules?

Evidence:
{{ evidence }}

Consider:
- Are there gaps in the metric catalog?
- Do components have measures attached?
- Are rule descriptions and remediation info present?

Respond with JSON:
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>",
  "evidence_cited": ["<evidence item 1>", ...],
  "recommendations": ["<recommendation 1>", ...],
  "sub_scores": {
    "metric_extraction": <1-5>,
    "component_coverage": <1-5>,
    "rule_hydration": <1-5>
  }
}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect coverage data for evaluation."""
        data = self.analysis_results

        metrics = data.get("metric_catalog", [])
        components = data.get("components", {}).get("by_key", {})
        measures = data.get("measures", {}).get("by_component_key", {})
        rules = data.get("rules", {}).get("by_key", {})
        issues = data.get("issues", {}).get("items", [])

        return {
            "metric_count": len(metrics),
            "metric_keys": [m.get("key") for m in metrics[:20]],
            "component_count": len(components),
            "measures_count": len(measures),
            "rules_count": len(rules),
            "issues_count": len(issues),
            "triggered_rules": list({i.get("rule") for i in issues if i.get("rule")})[:20],
        }

    def evaluate(self) -> JudgeResult:
        """Evaluate data extraction completeness."""
        data = self.analysis_results

        metric_score = self._evaluate_metrics(data)
        component_score = self._evaluate_components(data)
        rule_score = self._evaluate_rules(data)

        # Weighted average
        total_score = round(metric_score * 0.40 + component_score * 0.30 + rule_score * 0.30)
        total_score = max(1, min(5, total_score))

        evidence = []
        recommendations = []

        # Collect evidence
        metrics = data.get("metric_catalog", [])
        evidence.append(f"Metrics in catalog: {len(metrics)}")

        components = data.get("components", {}).get("by_key", {})
        evidence.append(f"Components extracted: {len(components)}")

        rules = data.get("rules", {}).get("by_key", {})
        evidence.append(f"Rules hydrated: {len(rules)}")

        if metric_score < 4:
            recommendations.append("Consider requesting additional metrics from the API")
        if component_score < 4:
            recommendations.append("Some components may not have measures attached")
        if rule_score < 4:
            recommendations.append("Some triggered rules are missing detailed metadata")

        return self._create_result(
            score=total_score,
            confidence=0.85,
            reasoning=f"Evaluated {len(metrics)} metrics, {len(components)} components, {len(rules)} rules",
            evidence=evidence,
            recommendations=recommendations,
            sub_scores={
                "metric_extraction": metric_score,
                "component_coverage": component_score,
                "rule_hydration": rule_score,
            },
        )

    def _evaluate_metrics(self, data: dict) -> int:
        """Evaluate metric extraction completeness."""
        catalog = data.get("metric_catalog", [])
        measures = data.get("measures", {}).get("by_component_key", {})

        if not catalog:
            return 1

        # Check if key metrics are present
        key_metrics = {"ncloc", "complexity", "cognitive_complexity", "bugs", "vulnerabilities", "code_smells"}
        metric_keys = {m.get("key") for m in catalog}
        present = len(key_metrics & metric_keys)

        # Check if measures are actually populated
        if not measures:
            return max(1, present)

        return max(1, min(5, present + 1))

    def _evaluate_components(self, data: dict) -> int:
        """Evaluate component coverage."""
        components = data.get("components", {})
        by_key = components.get("by_key", {})
        measures = data.get("measures", {}).get("by_component_key", {})

        if not by_key:
            return 1

        # Count files with measures
        files = [k for k, v in by_key.items() if v.get("qualifier") == "FIL"]
        files_with_measures = [f for f in files if f in measures]

        if not files:
            return 3  # No files, neutral

        ratio = len(files_with_measures) / len(files)
        return max(1, min(5, round(1 + ratio * 4)))

    def _evaluate_rules(self, data: dict) -> int:
        """Evaluate rule hydration completeness."""
        rules = data.get("rules", {}).get("by_key", {})
        issues = data.get("issues", {}).get("items", [])

        if not issues:
            return 3  # No issues, neutral

        # Get unique rules from issues
        triggered_rules = {i.get("rule") for i in issues if i.get("rule")}
        hydrated = triggered_rules & set(rules.keys())

        if not triggered_rules:
            return 3

        ratio = len(hydrated) / len(triggered_rules)
        return max(1, min(5, round(1 + ratio * 4)))
