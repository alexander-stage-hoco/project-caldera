"""False positive rate judge for Gitleaks secret detection."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class FalsePositiveJudge(BaseJudge):
    """Evaluates the false positive rate of Gitleaks detection.

    Assesses:
    - False positive count and rate
    - Types of false positives (patterns that shouldn't match)
    - Context-awareness (understanding of test/example code)
    - Noise level in output
    """

    @property
    def dimension_name(self) -> str:
        return "false_positive"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total score

    def get_default_prompt(self) -> str:
        return """# False Positive Rate Evaluation

You are evaluating the false positive rate of Gitleaks secret detection output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the false positive rate from 1-5 based on:

1. **False Positive Count** (40% of score)
   - How many false positives were reported?
   - What percentage of total findings are false positives?

2. **Pattern Quality** (30% of score)
   - Are false positives from overly broad patterns?
   - Are test/example secrets correctly handled?

3. **Noise Level** (30% of score)
   - Is the signal-to-noise ratio acceptable?
   - Are findings actionable or overwhelmed by noise?

## Scoring Guide
- 5: No false positives, all findings are true secrets
- 4: < 5% false positive rate
- 3: 5-15% false positive rate
- 2: 15-30% false positive rate
- 1: > 30% false positive rate

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific false positives found>"],
    "recommendations": ["<pattern improvements>"],
    "sub_scores": {
        "false_positive_count": <1-5>,
        "pattern_quality": <1-5>,
        "noise_level": <1-5>
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
            "false_positive_analysis": {},
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()
        if all_results:
            evidence["analysis_outputs"] = all_results

        # Load ALL ground truth files (not just the first one)
        all_ground_truth = self.load_all_ground_truth()
        if all_ground_truth:
            evidence["ground_truth"] = all_ground_truth

        # Analyze potential false positives for each scenario
        for scenario, gt in all_ground_truth.items():
            expected = gt.get("expected", {})
            analysis = all_results.get(scenario, {})
            if analysis:
                expected_count = expected.get("total_secrets", 0)
                actual_count = analysis.get("total_secrets", 0)
                potential_fps = max(0, actual_count - expected_count)

                # Check for clean repos that should have zero secrets
                is_clean_repo = expected_count == 0

                evidence["false_positive_analysis"][scenario] = {
                    "expected_secrets": expected_count,
                    "actual_secrets": actual_count,
                    "potential_false_positives": potential_fps,
                    "is_clean_repo": is_clean_repo,
                    "clean_repo_passed": is_clean_repo and actual_count == 0,
                }

        return evidence
