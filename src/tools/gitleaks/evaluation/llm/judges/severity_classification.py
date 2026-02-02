"""Severity classification judge for Gitleaks secret detection."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class SeverityClassificationJudge(BaseJudge):
    """Evaluates the severity classification of detected secrets.

    Assesses:
    - Correct severity assignment (critical, high, medium, low)
    - Risk-based classification (production vs test secrets)
    - Context-aware severity (commit history, file location)
    - Prioritization quality
    """

    @property
    def dimension_name(self) -> str:
        return "severity_classification"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def get_default_prompt(self) -> str:
        return """# Severity Classification Evaluation

You are evaluating the severity classification of secrets detected by Gitleaks.

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the severity classification from 1-5 based on:

1. **Classification Accuracy** (40% of score)
   - Are critical secrets (production keys, passwords) marked critical?
   - Are test/example secrets correctly de-prioritized?

2. **Risk Assessment** (30% of score)
   - Does classification consider secret type risk?
   - Are high-value targets (AWS root, admin passwords) prioritized?

3. **Context Awareness** (30% of score)
   - Does severity consider file location? (config vs test files)
   - Is commit recency considered?

## Scoring Guide
- 5: Perfect severity classification matching ground truth
- 4: Minor severity misclassifications
- 3: Some important misclassifications
- 2: Significant misclassifications affecting triage
- 1: Severity classification is unreliable

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<severity assignments>"],
    "recommendations": ["<classification improvements>"],
    "sub_scores": {
        "classification_accuracy": <1-5>,
        "risk_assessment": <1-5>,
        "context_awareness": <1-5>
    }
}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect analysis output and ground truth for evaluation.

        Loads ALL ground truth files and analysis results, aggregating
        evidence from multiple scenarios for comprehensive evaluation.
        """
        evidence = {
            "analysis_outputs": {},
            "ground_truth": {},
            "severity_analysis": {
                "severity_distribution": {},
                "expected_severities": [],
                "severity_mismatches": [],
            },
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()
        if all_results:
            evidence["analysis_outputs"] = all_results

        # Load ALL ground truth files (not just the first one)
        all_ground_truth = self.load_all_ground_truth()
        if all_ground_truth:
            evidence["ground_truth"] = all_ground_truth

        # Aggregate severity information across all scenarios
        total_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for scenario, analysis in all_results.items():
            severity_dist = analysis.get("secrets_by_severity", {})
            for sev, count in severity_dist.items():
                if sev in total_by_severity:
                    total_by_severity[sev] += count

            # Check for expected severities in ground truth
            gt = all_ground_truth.get(scenario, {})
            expected = gt.get("expected", {})
            expected_findings = expected.get("findings", [])

            for ef in expected_findings:
                if "expected_severity" in ef:
                    evidence["severity_analysis"]["expected_severities"].append({
                        "scenario": scenario,
                        "file_path": ef.get("file_path"),
                        "rule_id": ef.get("rule_id"),
                        "expected_severity": ef.get("expected_severity"),
                    })

        evidence["severity_analysis"]["severity_distribution"] = total_by_severity

        return evidence
