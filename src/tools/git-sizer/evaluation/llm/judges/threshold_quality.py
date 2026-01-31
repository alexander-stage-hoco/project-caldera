"""Threshold Quality Judge - Evaluates appropriateness of threshold levels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ThresholdQualityJudge(BaseJudge):
    """Evaluates quality of threshold-based violation detection.

    Validates that:
    - Threshold levels (1-4) are appropriate
    - Healthy repos don't trigger false positives
    - Problematic repos correctly trigger violations
    - Health grades reflect actual repository health
    """

    @property
    def dimension_name(self) -> str:
        return "threshold_quality"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and evaluate threshold appropriateness."""
        analysis = self.load_analysis()
        if "error" in analysis:
            return analysis

        repositories = analysis.get("repositories", [])

        # Extract violations per repo
        violation_summary = []
        total_violations = 0
        for repo in repositories:
            violations = repo.get("violations", [])
            total_violations += len(violations)
            violation_summary.append({
                "repository": repo.get("repository", "unknown"),
                "health_grade": repo.get("health_grade", ""),
                "violation_count": len(violations),
                "violations": [
                    {
                        "metric": v.get("metric", ""),
                        "value": v.get("value", ""),
                        "level": v.get("level", 0),
                        "raw_value": v.get("raw_value", 0),
                    }
                    for v in violations
                ],
            })

        # Analyze grade distribution
        grade_distribution = {}
        for repo in repositories:
            grade = repo.get("health_grade", "Unknown")
            grade_letter = grade[0] if grade else "?"
            grade_distribution[grade_letter] = grade_distribution.get(grade_letter, 0) + 1

        # Expected outcomes based on synthetic repos
        expected_outcomes = {
            "healthy": {
                "expected_violations": 0,
                "expected_grade_range": ["A", "A+"],
                "description": "Clean repo with no size issues",
            },
            "bloated": {
                "expected_violations_min": 1,
                "expected_grade_range": ["B", "C", "C+", "D"],
                "description": "Large binary files should trigger blob size violations",
            },
            "wide-tree": {
                "expected_violations_min": 2,
                "expected_grade_range": ["C", "C+", "D", "D+", "F"],
                "description": "Wide tree + deep paths should trigger violations",
            },
            "deep-history": {
                "expected_violations": 0,
                "expected_grade_range": ["A", "A+", "B"],
                "description": "Many commits but within normal range",
            },
        }

        # Evaluate threshold quality
        quality_results = []
        for summary in violation_summary:
            repo_name = summary["repository"]
            grade = summary["health_grade"]
            violations = summary["violation_count"]

            expected = None
            for key in expected_outcomes:
                if key in repo_name.lower():
                    expected = expected_outcomes[key]
                    break

            if expected:
                if "expected_violations" in expected:
                    exp_violations = expected["expected_violations"]
                    passed = violations == exp_violations
                else:
                    exp_min = expected.get("expected_violations_min", 0)
                    passed = violations >= exp_min
                    exp_violations = f">= {exp_min}"

                exp_grades = expected["expected_grade_range"]
                grade_letter = grade[0] if grade else "?"
                grade_ok = grade_letter in exp_grades

                quality_results.append({
                    "repository": repo_name,
                    "actual_violations": violations,
                    "expected_violations": exp_violations,
                    "violations_ok": passed,
                    "actual_grade": grade,
                    "expected_grades": exp_grades,
                    "grade_ok": grade_ok,
                    "overall_ok": passed and grade_ok,
                })

        # Calculate pass rate
        passed_tests = sum(1 for r in quality_results if r["overall_ok"])
        total_tests = len(quality_results)
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Analyze violation levels
        level_distribution = {}
        for summary in violation_summary:
            for v in summary["violations"]:
                level = v.get("level", "unknown")
                level_distribution[level] = level_distribution.get(level, 0) + 1

        return {
            "violation_summary": violation_summary,
            "grade_distribution": grade_distribution,
            "expected_outcomes": expected_outcomes,
            "quality_results": quality_results,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "pass_rate": round(pass_rate, 1),
            "total_violations": total_violations,
            "level_distribution": level_distribution,
            "total_repositories": len(repositories),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate threshold quality requirements."""
        failures = []

        analysis = self.load_analysis()
        if "error" in analysis:
            failures.append(analysis["error"])
            return False, failures

        # Check healthy repo has no violations
        for repo in analysis.get("repositories", []):
            name = repo.get("repository", "")
            if "healthy" in name.lower():
                violations = repo.get("violations", [])
                if len(violations) > 0:
                    failures.append(
                        f"Healthy repo has {len(violations)} unexpected violations"
                    )

        # Check bloated repo has violations
        for repo in analysis.get("repositories", []):
            name = repo.get("repository", "")
            if "bloated" in name.lower():
                violations = repo.get("violations", [])
                if len(violations) < 1:
                    failures.append(
                        f"Bloated repo should have violations for large blobs"
                    )

        # Check all repos have health grades
        for repo in analysis.get("repositories", []):
            if not repo.get("health_grade"):
                failures.append(
                    f"Repository {repo.get('repository')} missing health grade"
                )

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Threshold Quality Judge

You are evaluating the **threshold quality** of git-sizer's violation detection.

## Evaluation Dimension
**Threshold Quality (25% weight)**: Do threshold levels accurately identify problematic repositories?

## Background
git-sizer uses threshold levels (1-4) to indicate severity:
- Level 1: Acceptable (minor concern)
- Level 2: Somewhat concerning
- Level 3: Very concerning
- Level 4: Alarm bells

Good thresholds should:
- Not trigger on healthy repositories (low false positives)
- Correctly flag problematic repositories (high true positives)
- Use appropriate severity levels (not over/under-alarming)
- Result in meaningful health grades (A-F)

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Perfect threshold accuracy, no false positives/negatives |
| 4 | Excellent thresholds, rare edge case misses |
| 3 | Good thresholds, some calibration issues |
| 2 | Thresholds too aggressive or too lenient |
| 1 | Thresholds unreliable, many misclassifications |

## Sub-Dimensions
1. **True Positive Rate (40%)**: Problematic repos correctly flagged
2. **False Positive Rate (30%)**: Healthy repos not incorrectly flagged
3. **Severity Calibration (30%)**: Levels match actual severity

## Evidence to Evaluate

### Violation Summary
```json
{{ violation_summary }}
```

### Grade Distribution
```json
{{ grade_distribution }}
```

### Expected Outcomes
```json
{{ expected_outcomes }}
```

### Quality Test Results
```json
{{ quality_results }}
```

### Summary
- Tests passed: {{ passed_tests }}/{{ total_tests }}
- Pass rate: {{ pass_rate }}%
- Total violations: {{ total_violations }}

### Violation Level Distribution
```json
{{ level_distribution }}
```

## Evaluation Questions
1. Do healthy repositories correctly have no (or minimal) violations?
2. Are problematic repositories correctly flagged with violations?
3. Are severity levels appropriate for the issues detected?
4. Do health grades accurately reflect repository health?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "threshold_quality",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of threshold quality assessment",
  "evidence_cited": ["specific threshold behaviors examined"],
  "recommendations": ["threshold calibration improvements"],
  "sub_scores": {
    "true_positive_rate": <1-5>,
    "false_positive_rate": <1-5>,
    "severity_calibration": <1-5>
  }
}
```
'''

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
