"""Risk Tier Quality Judge - Evaluates correctness of risk tier classifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class RiskTierQualityJudge(BaseJudge):
    """Evaluates the quality of risk tier classifications.

    Validates that:
    - Coverage percentages are correctly classified into risk tiers
    - CRITICAL tier (0-25% coverage) is correctly identified
    - HIGH tier (25-50% coverage) is correctly identified
    - MEDIUM tier (50-75% coverage) is correctly identified
    - LOW tier (75-100% coverage) is correctly identified
    """

    # Risk tier thresholds (coverage percentage)
    RISK_TIERS = {
        "CRITICAL": (0, 25),
        "HIGH": (25, 50),
        "MEDIUM": (50, 75),
        "LOW": (75, 100),
    }

    @property
    def dimension_name(self) -> str:
        return "risk_tier_quality"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of total score

    def _classify_risk_tier(self, coverage_pct: float | None) -> str:
        """Classify a coverage percentage into a risk tier.

        Args:
            coverage_pct: Coverage percentage (0-100) or None

        Returns:
            Risk tier name (CRITICAL, HIGH, MEDIUM, LOW)
        """
        if coverage_pct is None:
            return "UNKNOWN"

        for tier, (low, high) in self.RISK_TIERS.items():
            if low <= coverage_pct < high:
                return tier
            if tier == "LOW" and coverage_pct == 100:
                return tier

        return "UNKNOWN"

    def collect_evidence(self) -> dict[str, Any]:
        """Load coverage data and extract risk tier classifications."""
        ground_truth = self.load_ground_truth_by_format()
        prog_results = self.load_programmatic_results()

        # Analyze risk tier distribution across all formats
        tier_distribution: dict[str, list[dict[str, Any]]] = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
        }

        file_classifications: list[dict[str, Any]] = []

        for format_name in ["lcov", "cobertura", "jacoco", "istanbul"]:
            format_gt = ground_truth.get(format_name, {})
            for scenario, data in format_gt.items():
                expected = data.get("expected", {})
                files = expected.get("files", [])

                for file_data in files:
                    coverage_pct = file_data.get("line_coverage_pct")
                    if coverage_pct is not None:
                        tier = self._classify_risk_tier(coverage_pct)
                        classification = {
                            "format": format_name,
                            "scenario": scenario,
                            "file": file_data.get("relative_path", "unknown"),
                            "coverage_pct": coverage_pct,
                            "assigned_tier": tier,
                        }
                        file_classifications.append(classification)
                        if tier in tier_distribution:
                            tier_distribution[tier].append(classification)

        # Calculate tier statistics
        tier_stats = {}
        total_files = len(file_classifications)
        for tier, files in tier_distribution.items():
            tier_stats[tier] = {
                "count": len(files),
                "percentage": round(len(files) / total_files * 100, 1) if total_files > 0 else 0,
                "coverage_range": f"{self.RISK_TIERS[tier][0]}-{self.RISK_TIERS[tier][1]}%",
            }

        # Identify potential misclassifications
        misclassifications: list[dict[str, Any]] = []
        for classification in file_classifications:
            expected_tier = self._classify_risk_tier(classification["coverage_pct"])
            if classification["assigned_tier"] != expected_tier:
                misclassifications.append({
                    **classification,
                    "expected_tier": expected_tier,
                })

        # Get programmatic check results
        prog_summary = "N/A"
        if prog_results:
            passed = prog_results.get("passed", 0)
            total = prog_results.get("total", 0)
            score = prog_results.get("score", 0)
            prog_summary = f"{passed}/{total} checks passed ({score}%)"

        evidence = {
            "file_classifications": file_classifications[:20],  # Limit for prompt size
            "tier_distribution": tier_stats,
            "tier_definitions": self.RISK_TIERS,
            "total_files_analyzed": total_files,
            "misclassifications": misclassifications,
            "misclassification_count": len(misclassifications),
            "programmatic_results": prog_summary,
            "evaluation_mode": self.evaluation_mode,
        }

        # Inject synthetic baseline context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["synthetic_baseline"] = "No synthetic baseline available"
                evidence["interpretation_guidance"] = (
                    "Evaluate based on tier distribution reasonableness"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate risk tier classification requirements."""
        failures: list[str] = []

        ground_truth = self.load_ground_truth_by_format()

        # Check that we have ground truth for each format
        formats_with_data = 0
        for format_name in ["lcov", "cobertura", "jacoco", "istanbul"]:
            if ground_truth.get(format_name):
                formats_with_data += 1

        if formats_with_data == 0:
            failures.append("No ground truth data found for any format")

        # Validate that coverage percentages are in valid range
        for format_name, scenarios in ground_truth.items():
            if format_name == "cross-format":
                continue
            for scenario, data in scenarios.items():
                expected = data.get("expected", {})
                for file_data in expected.get("files", []):
                    coverage_pct = file_data.get("line_coverage_pct")
                    if coverage_pct is not None:
                        if not 0 <= coverage_pct <= 100:
                            failures.append(
                                f"{format_name}/{scenario}: Invalid coverage {coverage_pct}%"
                            )

        return len(failures) == 0, failures

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            JudgeResult with heuristic-based scoring
        """
        misclassification_count = evidence.get("misclassification_count", 0)
        total_files = evidence.get("total_files_analyzed", 0)

        if total_files == 0:
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.7,
                reasoning="No files found to evaluate risk tiers",
                evidence_cited=["total_files_analyzed: 0"],
                recommendations=["Ensure coverage data is available for evaluation"],
                raw_response="",
            )

        # Calculate accuracy rate
        accuracy = (total_files - misclassification_count) / total_files * 100

        if accuracy >= 95:
            score = 5
        elif accuracy >= 85:
            score = 4
        elif accuracy >= 70:
            score = 3
        elif accuracy >= 50:
            score = 2
        else:
            score = 1

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.8,
            reasoning=f"Risk tier classification accuracy: {accuracy:.1f}% ({misclassification_count} misclassifications out of {total_files} files)",
            evidence_cited=[
                f"total_files: {total_files}",
                f"misclassifications: {misclassification_count}",
            ],
            recommendations=[] if score >= 4 else ["Review tier boundary classifications"],
            raw_response="",
        )

    def get_default_prompt(self) -> str:
        return '''# Risk Tier Quality Judge

You are evaluating the **risk tier quality** of coverage-ingest's risk classification system.

## Evaluation Dimension
**Risk Tier Quality (35% weight)**: Are coverage percentages correctly classified into risk tiers?

## Background
coverage-ingest classifies files into risk tiers based on coverage percentage:
- CRITICAL: 0-25% coverage (requires immediate attention)
- HIGH: 25-50% coverage (significant risk)
- MEDIUM: 50-75% coverage (moderate risk)
- LOW: 75-100% coverage (acceptable risk)

Accurate risk tier classification is critical for:
- Prioritizing testing efforts
- Identifying high-risk code areas
- CI/CD quality gates
- Technical debt assessment

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Perfect match to severity thresholds, all tiers correctly assigned |
| 4 | Minor discrepancies at tier boundaries (within 1% of threshold) |
| 3 | Generally appropriate classifications, few edge case errors |
| 2 | Significant misclassifications affecting prioritization |
| 1 | No correlation between coverage and tier assignment |

## Sub-Dimensions
1. **Tier Accuracy (50%)**: Are files assigned to the correct tier?
2. **Boundary Handling (30%)**: Are edge cases at tier boundaries handled correctly?
3. **Distribution Reasonableness (20%)**: Is the tier distribution realistic?

## Evidence to Evaluate

### Tier Definitions
```json
{{ tier_definitions }}
```

### Sample File Classifications
```json
{{ file_classifications }}
```

### Tier Distribution
```json
{{ tier_distribution }}
```

### Misclassifications Found
```json
{{ misclassifications }}
```

### Summary
- Total files analyzed: {{ total_files_analyzed }}
- Misclassification count: {{ misclassification_count }}
- Programmatic results: {{ programmatic_results }}

## Evaluation Questions
1. Are files with <25% coverage correctly classified as CRITICAL?
2. Are tier boundaries handled consistently?
3. Does the overall distribution seem reasonable for a codebase?
4. Are there any systematic misclassification patterns?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "risk_tier_quality",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of risk tier quality assessment",
  "evidence_cited": ["specific classifications examined"],
  "recommendations": ["improvements for tier classification"],
  "sub_scores": {
    "tier_accuracy": <1-5>,
    "boundary_handling": <1-5>,
    "distribution_reasonableness": <1-5>
  }
}
```
'''
