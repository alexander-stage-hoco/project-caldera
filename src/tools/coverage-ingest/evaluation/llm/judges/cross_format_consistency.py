"""Cross-Format Consistency Judge - Evaluates consistency across coverage format parsers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class CrossFormatConsistencyJudge(BaseJudge):
    """Evaluates consistency across the 4 coverage format parsers.

    Validates that:
    - LCOV, Cobertura, JaCoCo, and Istanbul parsers produce consistent output
    - Equivalent coverage data results in matching normalized metrics
    - Path normalization is consistent across formats
    - Branch coverage handling is uniform
    """

    SUPPORTED_FORMATS = ["lcov", "cobertura", "jacoco", "istanbul"]

    @property
    def dimension_name(self) -> str:
        return "cross_format_consistency"

    @property
    def weight(self) -> float:
        return 0.30  # 30% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load cross-format equivalence tests and analyze consistency."""
        ground_truth = self.load_ground_truth_by_format()
        prog_results = self.load_programmatic_results()

        # Load cross-format equivalence test cases
        cross_format_gt = ground_truth.get("cross-format", {})
        equivalence_data = cross_format_gt.get("equivalence", {})

        test_cases = equivalence_data.get("test_cases", [])
        validation_rules = equivalence_data.get("validation_rules", [])

        # Analyze each test case for consistency
        consistency_results: list[dict[str, Any]] = []

        for test_case in test_cases:
            test_name = test_case.get("name", "unknown")
            scenarios = test_case.get("scenarios", {})
            expected_common = test_case.get("expected_common", {})

            # Collect format-specific results
            format_results: dict[str, dict[str, Any]] = {}

            for format_name, scenario_file in scenarios.items():
                scenario_name = scenario_file.replace(".lcov", "").replace(".xml", "").replace(".json", "")
                format_gt = ground_truth.get(format_name, {})
                scenario_data = format_gt.get(scenario_name, {})
                expected = scenario_data.get("expected", {})

                if expected:
                    format_results[format_name] = {
                        "file_count": expected.get("file_count"),
                        "files": expected.get("files", []),
                    }

            # Check consistency across formats
            inconsistencies: list[str] = []

            if len(format_results) > 1:
                # Check expected common values
                for key, expected_value in expected_common.items():
                    for format_name, result in format_results.items():
                        if key == "file_count":
                            actual = result.get("file_count")
                        else:
                            # Check in first file of each format
                            files = result.get("files", [])
                            if files:
                                actual = files[0].get(key)
                            else:
                                actual = None

                        if actual is not None and actual != expected_value:
                            inconsistencies.append(
                                f"{format_name}: {key} is {actual}, expected {expected_value}"
                            )

            consistency_results.append({
                "test_name": test_name,
                "description": test_case.get("description", ""),
                "formats_tested": list(format_results.keys()),
                "expected_common": expected_common,
                "inconsistencies": inconsistencies,
                "is_consistent": len(inconsistencies) == 0,
            })

        # Calculate overall consistency score
        total_tests = len(consistency_results)
        consistent_tests = sum(1 for r in consistency_results if r["is_consistent"])
        consistency_rate = (consistent_tests / total_tests * 100) if total_tests > 0 else 0

        # Analyze path normalization consistency
        path_issues: list[dict[str, Any]] = []
        for format_name in self.SUPPORTED_FORMATS:
            format_gt = ground_truth.get(format_name, {})
            for scenario, data in format_gt.items():
                expected = data.get("expected", {})
                for file_data in expected.get("files", []):
                    path = file_data.get("relative_path", "")
                    if path.startswith("/"):
                        path_issues.append({
                            "format": format_name,
                            "scenario": scenario,
                            "path": path,
                            "issue": "Leading slash (not repo-relative)"
                        })
                    if "\\" in path:
                        path_issues.append({
                            "format": format_name,
                            "scenario": scenario,
                            "path": path,
                            "issue": "Backslash separator (not POSIX)"
                        })

        # Get programmatic check results
        prog_summary = "N/A"
        if prog_results:
            passed = prog_results.get("passed", 0)
            total = prog_results.get("total", 0)
            score = prog_results.get("score", 0)
            prog_summary = f"{passed}/{total} checks passed ({score}%)"

        evidence = {
            "consistency_results": consistency_results,
            "validation_rules": validation_rules,
            "consistency_rate": round(consistency_rate, 1),
            "total_tests": total_tests,
            "consistent_tests": consistent_tests,
            "path_normalization_issues": path_issues,
            "formats_evaluated": self.SUPPORTED_FORMATS,
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
                    "Evaluate based on format parser output consistency"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate cross-format consistency requirements."""
        failures: list[str] = []

        ground_truth = self.load_ground_truth_by_format()

        # Check that we have cross-format test data
        cross_format_gt = ground_truth.get("cross-format", {})
        if not cross_format_gt:
            failures.append("No cross-format ground truth data found")
            return False, failures

        equivalence_data = cross_format_gt.get("equivalence", {})
        test_cases = equivalence_data.get("test_cases", [])

        if not test_cases:
            failures.append("No equivalence test cases defined")

        # Check that validation rules are defined
        validation_rules = equivalence_data.get("validation_rules", [])
        if not validation_rules:
            failures.append("No validation rules defined for cross-format checks")

        # Check all formats have at least some data
        for format_name in self.SUPPORTED_FORMATS:
            if not ground_truth.get(format_name):
                failures.append(f"No ground truth data for format: {format_name}")

        return len(failures) == 0, failures

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            JudgeResult with heuristic-based scoring
        """
        consistency_rate = evidence.get("consistency_rate", 0)
        path_issues = evidence.get("path_normalization_issues", [])
        total_tests = evidence.get("total_tests", 0)

        if total_tests == 0:
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.7,
                reasoning="No cross-format tests found to evaluate",
                evidence_cited=["total_tests: 0"],
                recommendations=["Add cross-format equivalence tests"],
                raw_response="",
            )

        # Start with consistency rate score
        if consistency_rate >= 95:
            score = 5
        elif consistency_rate >= 85:
            score = 4
        elif consistency_rate >= 70:
            score = 3
        elif consistency_rate >= 50:
            score = 2
        else:
            score = 1

        # Deduct for path normalization issues
        if len(path_issues) > 0:
            score = max(1, score - 1)

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.8,
            reasoning=f"Cross-format consistency rate: {consistency_rate}%, path issues: {len(path_issues)}",
            evidence_cited=[
                f"consistency_rate: {consistency_rate}%",
                f"path_issues: {len(path_issues)}",
            ],
            recommendations=[] if score >= 4 else ["Resolve format-specific inconsistencies"],
            raw_response="",
        )

    def get_default_prompt(self) -> str:
        return '''# Cross-Format Consistency Judge

You are evaluating the **cross-format consistency** of coverage-ingest's parsers.

## Evaluation Dimension
**Cross-Format Consistency (30% weight)**: Do all 4 format parsers produce consistent output?

## Background
coverage-ingest supports 4 coverage formats:
- LCOV: Line-based text format (gcov, Python coverage)
- Cobertura: XML format (Java, Python pytest-cov)
- JaCoCo: XML format (Java/JVM)
- Istanbul: JSON format (JavaScript/TypeScript)

Consistency is critical because:
- Same coverage data should produce identical normalized metrics
- Path normalization must be uniform (repo-relative, POSIX separators)
- Branch coverage handling should be equivalent across formats
- Aggregations should match regardless of source format

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Perfect consistency across all formats and test cases |
| 4 | Minor format-specific variations that don't affect usability |
| 3 | Mostly consistent with some explainable differences |
| 2 | Significant inconsistencies that affect data reliability |
| 1 | Inconsistent output that cannot be trusted across formats |

## Sub-Dimensions
1. **Metric Consistency (40%)**: Same coverage data = same metrics
2. **Path Normalization (30%)**: Paths normalized consistently across formats
3. **Branch Handling (30%)**: Branch coverage treated uniformly

## Evidence to Evaluate

### Cross-Format Test Results
```json
{{ consistency_results }}
```

### Validation Rules
```json
{{ validation_rules }}
```

### Path Normalization Issues
```json
{{ path_normalization_issues }}
```

### Summary
- Formats evaluated: {{ formats_evaluated }}
- Total tests: {{ total_tests }}
- Consistent tests: {{ consistent_tests }}
- Consistency rate: {{ consistency_rate }}%
- Programmatic results: {{ programmatic_results }}

## Evaluation Questions
1. Do equivalent coverage files produce identical normalized metrics?
2. Are file paths normalized consistently (no leading /, POSIX separators)?
3. Is branch coverage handled uniformly across formats?
4. Are there format-specific edge cases causing inconsistencies?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "cross_format_consistency",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of cross-format consistency assessment",
  "evidence_cited": ["specific test results and comparisons"],
  "recommendations": ["improvements for format consistency"],
  "sub_scores": {
    "metric_consistency": <1-5>,
    "path_normalization": <1-5>,
    "branch_handling": <1-5>
  }
}
```
'''
