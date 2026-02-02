"""Detection accuracy judge for Gitleaks secret detection."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class DetectionAccuracyJudge(BaseJudge):
    """Evaluates the accuracy of Gitleaks secret detection.

    Assesses:
    - True positive rate (secrets correctly identified)
    - Match accuracy (correct secret type identification)
    - Location accuracy (correct file and line information)
    - Rule matching (appropriate rules triggered)
    """

    @property
    def dimension_name(self) -> str:
        return "detection_accuracy"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of total score

    def get_default_prompt(self) -> str:
        return """# Detection Accuracy Evaluation

You are evaluating the detection accuracy of Gitleaks secret detection output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the detection accuracy from 1-5 based on:

1. **True Positive Rate** (40% of score)
   - Were all expected secrets detected?
   - Were secret types correctly identified?

2. **Location Accuracy** (30% of score)
   - Are file paths correct?
   - Are line numbers accurate?

3. **Rule Matching** (30% of score)
   - Were appropriate detection rules triggered?
   - Is the match quality good (no partial matches)?

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific findings>"],
    "recommendations": ["<improvements>"],
    "sub_scores": {
        "true_positive_rate": <1-5>,
        "location_accuracy": <1-5>,
        "rule_matching": <1-5>
    }
}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect analysis output and ground truth for evaluation.

        Loads ALL ground truth files and analysis results, aggregating
        evidence from multiple scenarios for comprehensive evaluation.

        For real-world evaluation mode, also injects synthetic evaluation
        context to help the LLM understand tool baseline capability.
        """
        evidence: dict[str, Any] = {
            "analysis_outputs": {},
            "ground_truth": {},
            "comparison_summary": {},
            "evaluation_mode": self.evaluation_mode,
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()
        if all_results:
            evidence["analysis_outputs"] = all_results

        # Load ALL ground truth files (not just the first one)
        all_ground_truth = self.load_all_ground_truth()
        if all_ground_truth:
            evidence["ground_truth"] = all_ground_truth

        # Create comparison summary for each scenario
        for scenario, gt in all_ground_truth.items():
            expected = gt.get("expected", {})
            # Find matching analysis result
            analysis = all_results.get(scenario, {})
            if analysis:
                evidence["comparison_summary"][scenario] = {
                    "expected_total_secrets": expected.get("total_secrets", 0),
                    "actual_total_secrets": analysis.get("total_secrets", 0),
                    "expected_rule_ids": expected.get("rule_ids", []),
                    "expected_files": expected.get("files_with_secrets_list", []),
                }

        # Inject synthetic context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["synthetic_baseline"] = "No synthetic baseline available"
                evidence["interpretation_guidance"] = "Evaluate based on ground truth comparison only"
        else:
            # For synthetic mode, provide default values to avoid unresolved placeholders
            evidence["synthetic_baseline"] = "N/A - synthetic mode uses direct ground truth comparison"
            evidence["interpretation_guidance"] = "Strict ground truth evaluation: Compare analysis outputs directly against expected values"

        return evidence
