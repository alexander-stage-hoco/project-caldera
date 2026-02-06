"""Rule Coverage Judge for DevSkim security linting evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class RuleCoverageJudge(BaseJudge):
    """Evaluates the coverage of DevSkim's security rule set.

    Assesses whether DevSkim activates appropriate security rules
    for comprehensive .NET/C# security analysis.
    """

    @property
    def dimension_name(self) -> str:
        return "rule_coverage"

    @property
    def weight(self) -> float:
        return 0.25  # Rule coverage ensures comprehensive scanning

    def collect_evidence(self) -> dict[str, Any]:
        """Collect rule coverage evidence."""
        all_results = self.load_all_analysis_results()

        # Load ground truth
        gt_path = self.working_dir / "evaluation" / "ground-truth" / "csharp.json"
        ground_truth = {}
        if gt_path.exists():
            ground_truth = json.loads(gt_path.read_text())

        # Rule statistics
        rules_triggered = {}
        rule_categories = {}

        for repo_name, data in all_results.items():
            for file_info in data.get("files", data.get("results", [])):
                for finding in file_info.get("issues", file_info.get("findings", [])):
                    rule = finding.get("rule_id", finding.get("ruleId", "unknown"))
                    rules_triggered[rule] = rules_triggered.get(rule, 0) + 1

                    # Use dd_category (DevSkim's category field) with fallback
                    category = finding.get("dd_category", finding.get("category", "unknown"))
                    rule_categories[category] = rule_categories.get(category, 0) + 1

        # Expected categories from ground truth
        expected_categories = ground_truth.get("aggregate_expectations", {}).get("required_categories", [])

        # Calculate coverage
        covered_categories = set(rule_categories.keys())
        expected_set = set(expected_categories)
        category_coverage = len(covered_categories & expected_set) / len(expected_set) if expected_set else 1.0

        return {
            "unique_rules_triggered": len(rules_triggered),
            "rules_by_frequency": dict(sorted(rules_triggered.items(), key=lambda x: -x[1])[:20]),
            "rule_categories": rule_categories,
            "ground_truth_comparison": {
                "expected_categories": expected_categories,
                "covered_categories": sorted(covered_categories),
                "coverage_rate": f"{category_coverage:.1%}",
            },
            "security_domains": {
                "owasp_top_10_coverage": "Check if major OWASP categories are covered",
                "expected_domains": [
                    "Injection",
                    "Broken Authentication",
                    "Sensitive Data Exposure",
                    "Security Misconfiguration",
                    "Cross-Site Scripting",
                ],
            },
            "repos_analyzed": list(all_results.keys()),
        }

    def get_default_prompt(self) -> str:
        return """# DevSkim Rule Coverage Evaluation

You are an expert security evaluator assessing the rule coverage of DevSkim.

## Evidence
{{ evidence }}

## Evaluation Criteria

Evaluate the following aspects:

1. **Rule Breadth** (weight: 35%)
   - How many unique security rules are triggered?
   - Is the rule set comprehensive for .NET/C# security?

2. **Category Coverage** (weight: 35%)
   - Are all major security categories represented?
   - Is OWASP Top 10 coverage adequate?

3. **Ground Truth Alignment** (weight: 30%)
   - Are expected security patterns being detected?
   - Are required categories covered?

## OWASP Top 10 Categories (2021)
1. Broken Access Control
2. Cryptographic Failures
3. Injection
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Auth Failures
8. Software/Data Integrity
9. Logging/Monitoring
10. SSRF

## Scoring Rubric

- **5 (Excellent)**: >15 rules, all major categories, >90% ground truth coverage
- **4 (Good)**: 10-15 rules, most categories, 70-90% coverage
- **3 (Acceptable)**: 5-10 rules, key categories present, 50-70% coverage
- **2 (Poor)**: 3-5 rules, missing important categories, 30-50% coverage
- **1 (Failing)**: <3 rules or major security gaps, <30% coverage

## Required Output

Provide your evaluation as a JSON object:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "rule_breadth": <1-5>,
    "category_coverage": <1-5>,
    "ground_truth_alignment": <1-5>
  }
}
```
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify minimum rule coverage for security scanning."""
        failures = []
        all_results = self.load_all_analysis_results()

        rules_triggered = set()
        for data in all_results.values():
            for file_info in data.get("files", data.get("results", [])):
                for finding in file_info.get("issues", file_info.get("findings", [])):
                    rule = finding.get("rule_id", finding.get("ruleId", ""))
                    if rule:
                        rules_triggered.add(rule)

        if len(rules_triggered) < 2 and all_results:
            failures.append(f"Only {len(rules_triggered)} rules triggered - expected at least 2 for security scanning")

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
