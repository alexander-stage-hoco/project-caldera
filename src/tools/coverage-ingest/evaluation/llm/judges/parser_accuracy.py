"""Parser Accuracy Judge - Evaluates accuracy of coverage metric parsing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ParserAccuracyJudge(BaseJudge):
    """Evaluates the accuracy of coverage metric parsing.

    Validates that:
    - Line counts are correctly extracted from each format
    - Branch counts are correctly extracted when present
    - Coverage percentages are calculated accurately
    - All 4 formats produce consistent FileCoverage structures
    """

    @property
    def dimension_name(self) -> str:
        return "parser_accuracy"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load ground truth and actual results for comparison."""
        ground_truth = self.load_ground_truth_by_format()
        prog_results = self.load_programmatic_results()

        # Collect parser accuracy metrics
        format_accuracy: dict[str, dict[str, Any]] = {}
        total_checks = 0
        passed_checks = 0

        for format_name in ["lcov", "cobertura", "jacoco", "istanbul"]:
            format_gt = ground_truth.get(format_name, {})
            format_checks = 0
            format_passed = 0

            for scenario, data in format_gt.items():
                expected = data.get("expected", {})
                files = expected.get("files", [])

                for file_data in files:
                    # Check line metrics
                    if file_data.get("lines_total") is not None:
                        format_checks += 1
                        total_checks += 1
                        lines_valid = (
                            file_data.get("lines_covered", 0) <= file_data.get("lines_total", 0)
                        )
                        if lines_valid:
                            format_passed += 1
                            passed_checks += 1

                    # Check branch metrics
                    if file_data.get("branches_total") is not None:
                        format_checks += 1
                        total_checks += 1
                        branches_valid = (
                            file_data.get("branches_covered", 0) <= file_data.get("branches_total", 0)
                        )
                        if branches_valid:
                            format_passed += 1
                            passed_checks += 1

                    # Check percentage calculation
                    if file_data.get("line_coverage_pct") is not None:
                        format_checks += 1
                        total_checks += 1
                        lines_total = file_data.get("lines_total", 0)
                        lines_covered = file_data.get("lines_covered", 0)
                        if lines_total > 0:
                            expected_pct = round((lines_covered / lines_total) * 100, 2)
                            actual_pct = file_data.get("line_coverage_pct", 0)
                            if abs(expected_pct - actual_pct) < 0.01:
                                format_passed += 1
                                passed_checks += 1

            if format_checks > 0:
                format_accuracy[format_name] = {
                    "checks": format_checks,
                    "passed": format_passed,
                    "accuracy": round(format_passed / format_checks * 100, 1),
                }

        # Sample file data for evidence
        sample_files: list[dict[str, Any]] = []
        for format_name in ["lcov", "cobertura", "jacoco", "istanbul"]:
            format_gt = ground_truth.get(format_name, {})
            for scenario, data in format_gt.items():
                files = data.get("expected", {}).get("files", [])
                if files:
                    sample = files[0].copy()
                    sample["format"] = format_name
                    sample["scenario"] = scenario
                    sample_files.append(sample)
                    break

        # Get programmatic check summary
        prog_summary = "N/A"
        if prog_results:
            passed = prog_results.get("passed", 0)
            total = prog_results.get("total", 0)
            score = prog_results.get("score", 0)
            prog_summary = f"{passed}/{total} checks passed ({score}%)"

        overall_accuracy = round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0

        evidence = {
            "format_accuracy": format_accuracy,
            "sample_files": sample_files[:10],
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "overall_accuracy": overall_accuracy,
            "programmatic_results": prog_summary,
            "evaluation_mode": self.evaluation_mode,
        }

        # Add synthetic baseline for real-world evaluation
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
                    "Evaluate based on metric consistency and format coverage"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate parser accuracy requirements."""
        failures: list[str] = []

        ground_truth = self.load_ground_truth_by_format()

        # Check that we have ground truth for each format
        formats_with_data = 0
        for format_name in ["lcov", "cobertura", "jacoco", "istanbul"]:
            if ground_truth.get(format_name):
                formats_with_data += 1
            else:
                failures.append(f"No ground truth data for {format_name} format")

        if formats_with_data < 4:
            failures.append(f"Only {formats_with_data}/4 formats have ground truth")

        # Validate metric consistency
        for format_name, scenarios in ground_truth.items():
            if format_name == "cross-format":
                continue
            for scenario, data in scenarios.items():
                expected = data.get("expected", {})
                for file_data in expected.get("files", []):
                    # Check for negative values
                    for field in ["lines_total", "lines_covered", "branches_total", "branches_covered"]:
                        value = file_data.get(field)
                        if value is not None and value < 0:
                            failures.append(f"{format_name}/{scenario}: negative {field}={value}")

        return len(failures) == 0, failures

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            JudgeResult with heuristic-based scoring
        """
        overall_accuracy = evidence.get("overall_accuracy", 0)
        format_accuracy = evidence.get("format_accuracy", {})

        # Check format coverage
        formats_covered = len(format_accuracy)

        if overall_accuracy >= 99 and formats_covered == 4:
            score = 5
        elif overall_accuracy >= 95 and formats_covered >= 3:
            score = 4
        elif overall_accuracy >= 85 and formats_covered >= 2:
            score = 3
        elif overall_accuracy >= 70:
            score = 2
        else:
            score = 1

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.85,
            reasoning=f"Parser accuracy: {overall_accuracy}% across {formats_covered} formats",
            evidence_cited=[
                f"overall_accuracy: {overall_accuracy}%",
                f"formats_covered: {formats_covered}/4",
            ],
            recommendations=[] if score >= 4 else ["Improve parser accuracy for failing formats"],
            raw_response="",
        )

    def get_default_prompt(self) -> str:
        return '''# Parser Accuracy Judge

You are evaluating the **parser accuracy** of coverage-ingest's format parsers.

## Evaluation Dimension
**Parser Accuracy (35% weight)**: Are coverage metrics parsed correctly from each format?

## Background
coverage-ingest parses coverage data from 4 formats:
- LCOV: Line-oriented text format (SF:, LF:, LH:, BRF:, BRH:)
- Cobertura: XML format with line-rate/branch-rate attributes
- JaCoCo: XML format with LINE/BRANCH counters
- Istanbul: JSON format with statement/branch maps

Accurate parsing is critical for:
- Correct coverage percentage calculations
- Reliable risk tier classification
- Cross-format consistency
- CI/CD quality gates

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | >= 99% accuracy across all 4 formats, all metrics correct |
| 4 | >= 95% accuracy, minor discrepancies in edge cases |
| 3 | >= 85% accuracy, some systematic errors in one format |
| 2 | >= 70% accuracy, significant parsing issues |
| 1 | < 70% accuracy, fundamental parsing problems |

## Sub-Dimensions
1. **Line Metric Accuracy (40%)**: Are line counts extracted correctly?
2. **Branch Metric Accuracy (30%)**: Are branch counts extracted correctly?
3. **Percentage Calculation (30%)**: Are percentages computed accurately?

## Evidence to Evaluate

### Format Accuracy Breakdown
```json
{{ format_accuracy }}
```

### Sample File Data
```json
{{ sample_files }}
```

### Summary
- Total checks: {{ total_checks }}
- Passed checks: {{ passed_checks }}
- Overall accuracy: {{ overall_accuracy }}%
- Programmatic results: {{ programmatic_results }}

### Evaluation Context
{{ interpretation_guidance }}

## Evaluation Questions
1. Are line counts (total/covered) extracted correctly from each format?
2. Are branch counts (when present) extracted correctly?
3. Are coverage percentages calculated accurately (within 0.01%)?
4. Is there consistency across formats for equivalent data?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "parser_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of parser accuracy assessment",
  "evidence_cited": ["specific metrics examined"],
  "recommendations": ["improvements for parsing accuracy"],
  "sub_scores": {
    "line_metric_accuracy": <1-5>,
    "branch_metric_accuracy": <1-5>,
    "percentage_calculation": <1-5>
  }
}
```
'''
