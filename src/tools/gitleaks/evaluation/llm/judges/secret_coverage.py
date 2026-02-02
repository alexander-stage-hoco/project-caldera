"""Secret type coverage judge for Gitleaks secret detection."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class SecretCoverageJudge(BaseJudge):
    """Evaluates the coverage of different secret types.

    Assesses:
    - Coverage of common secret types (API keys, tokens, passwords)
    - Platform-specific detection (AWS, GCP, Azure, GitHub, etc.)
    - Format handling (base64, hex, plain text)
    - Historical detection (secrets in git history)
    """

    @property
    def dimension_name(self) -> str:
        return "secret_coverage"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def get_default_prompt(self) -> str:
        return """# Secret Type Coverage Evaluation

You are evaluating the coverage of secret types detected by Gitleaks.

## Evidence

{{ evidence }}

## Evaluation Criteria

Score the secret type coverage from 1-5 based on:

1. **Type Breadth** (40% of score)
   - Are common secret types detected? (API keys, tokens, passwords)
   - Are platform-specific secrets detected? (AWS, GCP, GitHub, etc.)

2. **Format Handling** (30% of score)
   - Are different encodings handled? (base64, hex, URL-encoded)
   - Are various formats recognized? (JSON, YAML, env files)

3. **Historical Coverage** (30% of score)
   - Are secrets in git history detected?
   - Are deleted but committed secrets found?

## Scoring Guide
- 5: Comprehensive coverage of all expected secret types
- 4: Good coverage with minor gaps
- 3: Basic coverage of common types
- 2: Limited coverage, many types missed
- 1: Poor coverage, most secrets not detected

## Response Format

Respond with ONLY a JSON object:
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<secret types detected>"],
    "recommendations": ["<coverage improvements>"],
    "sub_scores": {
        "type_breadth": <1-5>,
        "format_handling": <1-5>,
        "historical_coverage": <1-5>
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
            "coverage_summary": {
                "rule_types_detected": set(),
                "expected_rule_types": set(),
                "scenarios_with_historical": [],
                "historical_detection_results": {},
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

        # Aggregate coverage information across all scenarios
        rule_types_detected = set()
        expected_rule_types = set()

        for scenario, gt in all_ground_truth.items():
            expected = gt.get("expected", {})

            # Track expected rule types
            for rule_id in expected.get("rule_ids", []):
                expected_rule_types.add(rule_id)

            # Check for historical secrets
            if expected.get("secrets_in_history", 0) > 0:
                evidence["coverage_summary"]["scenarios_with_historical"].append(scenario)

                analysis = all_results.get(scenario, {})
                if analysis:
                    evidence["coverage_summary"]["historical_detection_results"][scenario] = {
                        "expected_historical": expected.get("secrets_in_history", 0),
                        "actual_historical": analysis.get("secrets_in_history", 0),
                    }

            # Track detected rule types
            analysis = all_results.get(scenario, {})
            if analysis:
                for rule_id in analysis.get("secrets_by_rule", {}).keys():
                    rule_types_detected.add(rule_id)

        # Convert sets to lists for JSON serialization
        evidence["coverage_summary"]["rule_types_detected"] = list(rule_types_detected)
        evidence["coverage_summary"]["expected_rule_types"] = list(expected_rule_types)

        return evidence
