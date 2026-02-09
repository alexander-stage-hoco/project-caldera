"""Churn Validity Judge - Validates churn metrics match git history."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult
from .utils import validate_churn_metrics


class ChurnValidityJudge(BaseJudge):
    """Evaluates the validity of churn metrics.

    Validates that:
    - churn_30d <= churn_90d (30-day is a subset of 90-day)
    - Churn values are non-negative
    - Churn correlates reasonably with last_modified dates
    """

    @property
    def dimension_name(self) -> str:
        return "churn_validity"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess churn validity."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate churn data from all repos
        total_files = 0
        active_30d_files = 0
        active_90d_files = 0
        stale_files = 0
        validation_issues: list[str] = []
        repo_summaries: list[dict] = []
        sample_files: list[dict] = []

        for repo_name, repo_data in all_results.items():
            files = self.extract_files(repo_data)
            summary = self.extract_summary(repo_data)

            total_files += len(files)

            # Validate churn metrics
            validation = validate_churn_metrics(files)
            if not validation["valid"]:
                validation_issues.extend(
                    [f"{repo_name}: {issue}" for issue in validation["issues"]]
                )

            # Count activity levels
            repo_active_30d = 0
            repo_active_90d = 0
            repo_stale = 0

            for f in files:
                churn_30d = f.get("churn_30d", 0)
                churn_90d = f.get("churn_90d", 0)

                if churn_30d > 0:
                    repo_active_30d += 1
                if churn_90d > 0:
                    repo_active_90d += 1
                if churn_90d == 0:
                    repo_stale += 1

            active_30d_files += repo_active_30d
            active_90d_files += repo_active_90d
            stale_files += repo_stale

            # Sample files with high churn
            sorted_by_churn = sorted(
                files,
                key=lambda f: f.get("churn_90d", 0),
                reverse=True
            )
            sample_files.extend(sorted_by_churn[:5])

            # Calculate aggregated totals from file-level data
            # (summary doesn't include total_churn fields - they must be computed)
            total_churn_30d = sum(f.get("churn_30d", 0) for f in files)
            total_churn_90d = sum(f.get("churn_90d", 0) for f in files)

            repo_summaries.append({
                "repo": repo_name,
                "file_count": len(files),
                "active_30d_count": repo_active_30d,
                "active_90d_count": repo_active_90d,
                "stale_count": repo_stale,
                "total_churn_30d": total_churn_30d,
                "total_churn_90d": total_churn_90d,
                "churn_valid": validation["valid"],
            })

        evidence = {
            "total_repos": len(all_results),
            "total_files": total_files,
            "active_30d_files": active_30d_files,
            "active_90d_files": active_90d_files,
            "stale_files": stale_files,
            "sample_high_churn_files": sample_files[:15],
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

                expected = gt.get("expected", {})
                repo_data = all_results[repo_name]
                files = self.extract_files(repo_data)

                exp_churn_30d = expected.get("total_churn_30d")
                exp_churn_90d = expected.get("total_churn_90d")
                # Calculate actual totals from file-level data
                actual_churn_30d = sum(f.get("churn_30d", 0) for f in files)
                actual_churn_90d = sum(f.get("churn_90d", 0) for f in files)

                issues = []
                if exp_churn_30d is not None and actual_churn_30d != exp_churn_30d:
                    issues.append(
                        f"churn_30d: expected {exp_churn_30d}, got {actual_churn_30d}"
                    )
                if exp_churn_90d is not None and actual_churn_90d != exp_churn_90d:
                    issues.append(
                        f"churn_90d: expected {exp_churn_90d}, got {actual_churn_90d}"
                    )

                gt_comparison.append({
                    "repo": repo_name,
                    "match": len(issues) == 0,
                    "issues": issues,
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
                "Evaluate churn metrics for internal consistency."
            )

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Churn Validity Evaluation

You are an expert in code analysis evaluating git-blame-scanner's churn metrics validity.

## Task

Evaluate the validity and consistency of churn metrics (churn_30d, churn_90d) in the git-blame-scanner output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Metric Consistency (40%)**: Is churn_30d <= churn_90d for all files?
   - 5: All files satisfy the invariant
   - 4: Minor violations (<1% files)
   - 3: Some violations (1-5% files)
   - 2: Significant violations (5-15% files)
   - 1: Major data integrity issues (>15% files)

2. **Value Validity (30%)**: Are churn values non-negative and reasonable?
   - 5: All values valid and reasonable
   - 4: Minor edge cases (<1%)
   - 3: Some issues (1-5%)
   - 2: Multiple issues (5-15%)
   - 1: Major validity issues (>15%)

3. **Temporal Coherence (30%)**: Does churn correlate with last_modified dates?
   - 5: Perfect correlation (stale files have 0 churn, active files have > 0)
   - 4: High correlation (>95%)
   - 3: Moderate correlation (85-95%)
   - 2: Low correlation (70-85%)
   - 1: Poor correlation (<70%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "metric_consistency": <1-5>,
    "value_validity": <1-5>,
    "temporal_coherence": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        failures = []
        all_results = self.load_all_analysis_results()

        for repo_name, repo_data in all_results.items():
            files = self.extract_files(repo_data)

            # Validate churn consistency
            validation = validate_churn_metrics(files)
            if not validation["valid"]:
                failures.extend(
                    [f"{repo_name}: {issue}" for issue in validation["issues"]]
                )

        return len(failures) == 0, failures
