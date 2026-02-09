"""Ownership Accuracy Judge - Evaluates accuracy of ownership percentages."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult
from .utils import validate_ownership_percentages, compare_files


class OwnershipAccuracyJudge(BaseJudge):
    """Evaluates the accuracy of file ownership percentages.

    Validates that:
    - Ownership percentages are within valid bounds (0-100%)
    - Top author percentages accurately reflect git blame data
    - unique_authors counts match actual contributor counts
    """

    @property
    def dimension_name(self) -> str:
        return "ownership_accuracy"

    @property
    def weight(self) -> float:
        return 0.30  # 30% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess ownership accuracy."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate file data from all repos
        total_files = 0
        all_file_data: list[dict] = []
        validation_issues: list[str] = []
        repo_summaries: list[dict] = []

        for repo_name, repo_data in all_results.items():
            files = self.extract_files(repo_data)
            summary = self.extract_summary(repo_data)

            total_files += len(files)

            # Validate ownership percentages
            validation = validate_ownership_percentages(files)
            if not validation["valid"]:
                validation_issues.extend(
                    [f"{repo_name}: {issue}" for issue in validation["issues"]]
                )

            # Sample files for evidence
            sorted_files = sorted(
                files,
                key=lambda f: f.get("top_author_pct", 0),
                reverse=True
            )
            all_file_data.extend(sorted_files[:10])

            repo_summaries.append({
                "repo": repo_name,
                "file_count": len(files),
                "avg_top_author_pct": summary.get("avg_top_author_pct", 0),
                "single_author_count": sum(
                    1 for f in files if f.get("unique_authors", 0) == 1
                ),
                "ownership_valid": validation["valid"],
            })

        evidence = {
            "total_repos": len(all_results),
            "total_files": total_files,
            "sample_files": all_file_data[:20],
            "repo_summaries": repo_summaries,
            "validation_issues": validation_issues,
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for repo_name, gt in ground_truth.items():
                if repo_name not in all_results:
                    continue

                expected_files = gt.get("expected", {}).get("files", [])
                actual_files = self.extract_files(all_results[repo_name])

                comparison = compare_files(actual_files, expected_files)
                gt_comparison.append({
                    "repo": repo_name,
                    "accuracy": comparison["accuracy"],
                    "matches": len(comparison["matches"]),
                    "mismatches": len(comparison["mismatches"]),
                    "missing": len(comparison["missing"]),
                })
            evidence["ground_truth_comparison"] = gt_comparison

        # Add synthetic context if available
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "Not available"
            evidence["interpretation_guidance"] = (
                "Evaluate against ground truth expectations."
            )

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Ownership Accuracy Evaluation

You are an expert in code analysis evaluating git-blame-scanner's accuracy in calculating file ownership.

## Task

Evaluate the accuracy of ownership percentage calculations in the git-blame-scanner output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Ownership Bounds (40%)**: Are percentages within valid bounds?
   - 5: All percentages between 0-100%
   - 4: Minor edge case issues (<1%)
   - 3: Some boundary violations (1-5%)
   - 2: Multiple violations (5-15%)
   - 1: Major data integrity issues (>15%)

2. **Author Count Accuracy (35%)**: Are unique_authors counts correct?
   - 5: All counts match expected
   - 4: Minor discrepancies (<5% files)
   - 3: Some issues (5-15% files)
   - 2: Significant issues (15-30% files)
   - 1: Major inaccuracies (>30% files)

3. **Concentration Detection (25%)**: Are high-concentration files identified?
   - 5: All high-concentration files correctly identified
   - 4: Most identified (>95%)
   - 3: Majority identified (85-95%)
   - 2: Some missed (70-85%)
   - 1: Many missed (<70%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "ownership_bounds": <1-5>,
    "author_count_accuracy": <1-5>,
    "concentration_detection": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        failures = []
        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not ground_truth:
            return True, []

        for repo_name, gt in ground_truth.items():
            if repo_name not in all_results:
                continue

            expected = gt.get("expected", {})
            files = self.extract_files(all_results[repo_name])

            # Validate ownership percentages are in bounds
            validation = validate_ownership_percentages(files)
            if not validation["valid"]:
                failures.extend(validation["issues"])

            # Check expected file count
            expected_count = expected.get("file_count")
            if expected_count is not None:
                actual_count = len(files)
                if actual_count != expected_count:
                    failures.append(
                        f"{repo_name}: expected {expected_count} files, found {actual_count}"
                    )

        return len(failures) == 0, failures
