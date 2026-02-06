"""Severity Calibration Judge for DevSkim security linting evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult

# Map DevSkim severity names to expected evaluation severity names
SEVERITY_MAP = {
    "critical": "critical",
    "high": "important",
    "medium": "moderate",
    "low": "low",
}


class SeverityCalibrationJudge(BaseJudge):
    """Evaluates the calibration of DevSkim's severity ratings.

    Assesses whether DevSkim assigns appropriate severity levels
    to different types of security vulnerabilities.
    """

    @property
    def dimension_name(self) -> str:
        return "severity_calibration"

    @property
    def weight(self) -> float:
        return 0.20  # Severity accuracy is important for triage

    def collect_evidence(self) -> dict[str, Any]:
        """Collect severity calibration evidence."""
        all_results = self.load_all_analysis_results()

        # Load ground truth
        gt_path = self.working_dir / "evaluation" / "ground-truth" / "csharp.json"
        ground_truth = {}
        if gt_path.exists():
            ground_truth = json.loads(gt_path.read_text())

        # Severity distribution
        severity_counts = {"critical": 0, "important": 0, "moderate": 0, "low": 0}
        severity_by_category = {}
        severity_samples = []

        for repo_name, data in all_results.items():
            for file_info in data.get("files", data.get("results", [])):
                for finding in file_info.get("issues", file_info.get("findings", [])):
                    # Map DevSkim severity to expected severity names
                    severity = finding.get("severity", "moderate").lower()
                    mapped_severity = SEVERITY_MAP.get(severity, severity)
                    rule_id = finding.get("rule_id", finding.get("ruleId", "unknown"))
                    # Use dd_category (DevSkim's category field) with fallback
                    category = finding.get("dd_category", finding.get("category", "unknown"))

                    if mapped_severity in severity_counts:
                        severity_counts[mapped_severity] += 1
                    else:
                        severity_counts["moderate"] += 1

                    # Track by category
                    if category not in severity_by_category:
                        severity_by_category[category] = {"critical": 0, "important": 0, "moderate": 0, "low": 0}
                    if mapped_severity in severity_by_category[category]:
                        severity_by_category[category][mapped_severity] += 1

                    # Collect samples
                    if len(severity_samples) < 15:
                        severity_samples.append({
                            "rule": rule_id,
                            "severity": severity,
                            "category": category,
                            "message": finding.get("message", "")[:80],
                        })

        # Expected severity guidelines
        severity_guidelines = {
            "critical": "Remote code execution, authentication bypass, data breach",
            "important": "SQL injection, XSS, privilege escalation",
            "moderate": "Information disclosure, weak crypto, CSRF",
            "low": "Best practice violations, deprecated APIs",
        }

        return {
            "severity_distribution": severity_counts,
            "severity_by_category": dict(list(severity_by_category.items())[:10]),
            "severity_samples": severity_samples,
            "severity_guidelines": severity_guidelines,
            "ground_truth_expectations": {
                "files": list(ground_truth.get("files", {}).keys()),
            },
            "repos_analyzed": list(all_results.keys()),
        }

    def get_default_prompt(self) -> str:
        return """# DevSkim Severity Calibration Evaluation

You are an expert security evaluator assessing the severity calibration of DevSkim.

## Evidence
{{ evidence }}

## Evaluation Criteria

Evaluate the following aspects:

1. **Severity Appropriateness** (weight: 40%)
   - Are critical findings truly critical (RCE, auth bypass)?
   - Are important findings correctly escalated?
   - Are low severity findings appropriately downgraded?

2. **Consistency** (weight: 35%)
   - Is the same vulnerability type assigned consistent severity?
   - Is the distribution reasonable (not all critical or all low)?

3. **Industry Alignment** (weight: 25%)
   - Does severity align with CVSS-like scoring principles?
   - Would a security team trust these severity ratings?

## Expected Severity Guidelines
- **Critical**: Remote code execution, authentication bypass, data breach
- **Important**: SQL injection, XSS, privilege escalation
- **Moderate**: Information disclosure, weak crypto, CSRF
- **Low**: Best practice violations, deprecated APIs

## Scoring Rubric

- **5 (Excellent)**: All severities appropriate, consistent, industry-aligned
- **4 (Good)**: Minor calibration issues, mostly correct
- **3 (Acceptable)**: Some severity misclassification, reasonable distribution
- **2 (Poor)**: Frequent severity errors, inconsistent ratings
- **1 (Failing)**: Unreliable severity ratings, inverted priorities

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
    "severity_appropriateness": <1-5>,
    "consistency": <1-5>,
    "industry_alignment": <1-5>
  }
}
```
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify severity distribution is reasonable for DevSkim.

        DevSkim is specialized in crypto issues (which are appropriately critical)
        so a high critical ratio is expected and acceptable.
        """
        failures = []
        all_results = self.load_all_analysis_results()

        severity_counts = {"critical": 0, "important": 0, "moderate": 0, "low": 0}
        severity_by_category = {}

        for data in all_results.values():
            for file_info in data.get("files", data.get("results", [])):
                for finding in file_info.get("issues", file_info.get("findings", [])):
                    severity = finding.get("severity", "moderate").lower()
                    mapped_severity = SEVERITY_MAP.get(severity, severity)
                    category = finding.get("dd_category", finding.get("category", "unknown"))

                    if mapped_severity in severity_counts:
                        severity_counts[mapped_severity] += 1

                    # Track consistency within categories
                    if category not in severity_by_category:
                        severity_by_category[category] = set()
                    severity_by_category[category].add(mapped_severity)

        # Check for severity consistency within categories (more meaningful than ratio)
        # Each category should have consistent severity assignments
        for category, severities in severity_by_category.items():
            if len(severities) > 2:  # Allow some variance, but not all 4 levels
                failures.append(
                    f"Category '{category}' has inconsistent severity ({len(severities)} levels)"
                )

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
