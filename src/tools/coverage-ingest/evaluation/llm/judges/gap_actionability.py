"""Gap Analysis Actionability Judge - Evaluates if coverage gap findings enable developer action."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


def _coverage_value(f: dict[str, Any]) -> float:
    """Get coverage percentage, defaulting to 100 for missing values (not 0)."""
    val = f.get("line_coverage_pct")
    return val if val is not None else 100.0


def _branch_value(f: dict[str, Any]) -> float:
    """Get branch coverage percentage, defaulting to 100 for missing values."""
    val = f.get("branch_coverage_pct")
    return val if val is not None else 100.0


class GapActionabilityJudge(BaseJudge):
    """Evaluates the actionability of coverage gap analysis.

    Validates that:
    - Coverage gaps are clearly identified
    - Files with lowest coverage are prioritized
    - File paths are specific and locatable
    - Coverage metrics are precise enough for action
    - Recommendations can be acted upon immediately
    """

    @property
    def dimension_name(self) -> str:
        return "gap_actionability"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load coverage data and extract actionability indicators."""
        ground_truth = self.load_ground_truth_by_format()
        prog_results = self.load_programmatic_results()

        # Collect all files with coverage data across formats
        all_files: list[dict[str, Any]] = []

        for format_name in ["lcov", "cobertura", "jacoco", "istanbul"]:
            format_gt = ground_truth.get(format_name, {})
            for scenario, data in format_gt.items():
                expected = data.get("expected", {})
                files = expected.get("files", [])

                for file_data in files:
                    coverage_pct = file_data.get("line_coverage_pct")
                    if coverage_pct is not None:
                        all_files.append({
                            "format": format_name,
                            "scenario": scenario,
                            "file_path": file_data.get("relative_path", "unknown"),
                            "line_coverage_pct": coverage_pct,
                            "lines_total": file_data.get("lines_total", 0),
                            "lines_covered": file_data.get("lines_covered", 0),
                            "lines_missed": file_data.get("lines_missed", 0),
                            "branch_coverage_pct": file_data.get("branch_coverage_pct"),
                            "branches_total": file_data.get("branches_total"),
                            "branches_covered": file_data.get("branches_covered"),
                        })

        # Sort by coverage to find gaps (lowest coverage first)
        sorted_files = sorted(all_files, key=lambda f: f.get("line_coverage_pct", 100))
        top_gaps = sorted_files[:10]  # Top 10 lowest coverage files

        # Analyze actionability characteristics
        actionability_metrics = {
            "has_file_paths": all(f.get("file_path") != "unknown" for f in all_files),
            # Empty files (0 lines with null coverage) are valid edge cases
            "has_line_counts": all(
                f.get("lines_total", 0) > 0 or f.get("line_coverage_pct") is None
                for f in all_files
            ),
            "has_coverage_pct": all(f.get("line_coverage_pct") is not None for f in all_files),
            "paths_are_specific": all(
                "/" in f.get("file_path", "") or "." in f.get("file_path", "")
                for f in all_files
            ),
            "files_prioritized": len(top_gaps) > 0,
        }

        # Calculate actionability score indicators
        actionability_score = sum(1 for v in actionability_metrics.values() if v) / len(
            actionability_metrics
        )

        # Analyze coverage gap distribution
        gap_distribution = {
            "critical_gaps": len([f for f in all_files if _coverage_value(f) < 25]),
            "high_gaps": len([f for f in all_files if 25 <= _coverage_value(f) < 50]),
            "medium_gaps": len([f for f in all_files if 50 <= _coverage_value(f) < 75]),
            "low_gaps": len([f for f in all_files if _coverage_value(f) >= 75]),
        }

        # Check for branch coverage gaps
        files_with_branches = [f for f in all_files if f.get("branches_total") is not None]
        branch_gap_analysis = {
            "files_with_branch_data": len(files_with_branches),
            "branch_gaps": [
                f for f in files_with_branches
                if _branch_value(f) < 75
            ][:5],  # Top 5 branch gaps
        }

        # Get programmatic check results
        prog_summary = "N/A"
        if prog_results:
            passed = prog_results.get("passed", 0)
            total = prog_results.get("total", 0)
            score = prog_results.get("score", 0)
            prog_summary = f"{passed}/{total} checks passed ({score}%)"

        evidence = {
            "top_coverage_gaps": top_gaps,
            "actionability_metrics": actionability_metrics,
            "actionability_score": round(actionability_score * 100, 1),
            "gap_distribution": gap_distribution,
            "branch_gap_analysis": branch_gap_analysis,
            "total_files_analyzed": len(all_files),
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
                    "Evaluate based on gap clarity and specificity"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate actionability requirements."""
        failures: list[str] = []

        ground_truth = self.load_ground_truth_by_format()

        # Check that files have required actionability fields
        for format_name in ["lcov", "cobertura", "jacoco", "istanbul"]:
            format_gt = ground_truth.get(format_name, {})
            for scenario, data in format_gt.items():
                expected = data.get("expected", {})
                for file_data in expected.get("files", []):
                    path = file_data.get("relative_path", "")
                    if not path:
                        failures.append(f"{format_name}/{scenario}: Missing file path")

                    lines_total = file_data.get("lines_total", 0)
                    coverage_pct = file_data.get("line_coverage_pct")
                    # Empty files (0 lines with null coverage) are valid edge cases
                    if lines_total == 0 and coverage_pct is not None:
                        failures.append(
                            f"{format_name}/{scenario}/{path}: Zero total lines but has coverage percentage"
                        )

                    # Validate coverage percentage consistency
                    lines_covered = file_data.get("lines_covered", 0)
                    if coverage_pct is not None and lines_total > 0:
                        expected_pct = round(lines_covered / lines_total * 100, 1)
                        if abs(coverage_pct - expected_pct) > 1:
                            failures.append(
                                f"{format_name}/{scenario}/{path}: Coverage mismatch "
                                f"({coverage_pct}% vs calculated {expected_pct}%)"
                            )

        return len(failures) == 0, failures

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            JudgeResult with heuristic-based scoring
        """
        actionability_score = evidence.get("actionability_score", 0)
        total_files = evidence.get("total_files_analyzed", 0)

        if total_files == 0:
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.7,
                reasoning="No files found to evaluate actionability",
                evidence_cited=["total_files_analyzed: 0"],
                recommendations=["Ensure coverage data is available for evaluation"],
                raw_response="",
            )

        # Score based on actionability metrics
        if actionability_score >= 95:
            score = 5
        elif actionability_score >= 80:
            score = 4
        elif actionability_score >= 60:
            score = 3
        elif actionability_score >= 40:
            score = 2
        else:
            score = 1

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.75,
            reasoning=f"Gap actionability score: {actionability_score}% based on {total_files} files",
            evidence_cited=[
                f"actionability_score: {actionability_score}%",
                f"total_files: {total_files}",
            ],
            recommendations=[] if score >= 4 else ["Improve file path specificity and metrics"],
            raw_response="",
        )

    def get_default_prompt(self) -> str:
        return '''# Gap Analysis Actionability Judge

You are evaluating the **actionability** of coverage-ingest's gap analysis output.

## Evaluation Dimension
**Gap Actionability (35% weight)**: Do coverage gap findings enable immediate developer action?

## Background
Actionable coverage gap analysis should:
- Clearly identify files with lowest coverage
- Provide specific, locatable file paths
- Include precise line/branch counts
- Prioritize gaps by severity
- Enable developers to take immediate action

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Highly actionable with clear priorities, specific paths, precise metrics |
| 4 | Actionable with minor gaps in detail or prioritization |
| 3 | Somewhat actionable but requires additional investigation |
| 2 | Limited actionability due to vague paths or missing metrics |
| 1 | Not actionable - cannot determine where to add tests |

## Sub-Dimensions
1. **Gap Clarity (40%)**: Are coverage gaps clearly identified?
2. **Path Specificity (30%)**: Are file paths specific enough to locate?
3. **Metric Precision (30%)**: Are line/branch counts precise?

## Evidence to Evaluate

### Top Coverage Gaps (Lowest Coverage Files)
```json
{{ top_coverage_gaps }}
```

### Actionability Metrics
```json
{{ actionability_metrics }}
```

### Gap Distribution
```json
{{ gap_distribution }}
```

### Branch Coverage Gaps
```json
{{ branch_gap_analysis }}
```

### Summary
- Total files analyzed: {{ total_files_analyzed }}
- Actionability score: {{ actionability_score }}%
- Programmatic results: {{ programmatic_results }}

## Evaluation Questions
1. Can a developer immediately locate the files with lowest coverage?
2. Are the line counts specific enough to know where to add tests?
3. Are files prioritized by coverage gap severity?
4. Is branch coverage tracked where relevant?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "gap_actionability",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of gap actionability assessment",
  "evidence_cited": ["specific gaps and paths examined"],
  "recommendations": ["improvements for actionability"],
  "sub_scores": {
    "gap_clarity": <1-5>,
    "path_specificity": <1-5>,
    "metric_precision": <1-5>
  }
}
```
'''
