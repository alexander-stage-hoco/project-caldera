"""Size Accuracy Judge - Evaluates correctness of blob/tree/commit sizing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class SizeAccuracyJudge(BaseJudge):
    """Evaluates accuracy of size measurements.

    Validates that:
    - Blob sizes are correctly measured
    - Tree entry counts are accurate
    - Commit counts match repository history
    - Path depths are properly calculated
    """

    @property
    def dimension_name(self) -> str:
        return "size_accuracy"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and extract size measurements."""
        analysis = self.load_analysis()
        if "error" in analysis:
            return analysis

        repositories = analysis.get("repositories", [])

        # Extract size metrics per repo
        repo_metrics = []
        for repo in repositories:
            metrics = repo.get("metrics", {})
            repo_metrics.append({
                "repository": repo.get("repository", "unknown"),
                "health_grade": repo.get("health_grade", ""),
                "blob_count": metrics.get("blob_count", 0),
                "blob_total_size": metrics.get("blob_total_size", 0),
                "blob_total_size_mb": metrics.get("blob_total_size", 0) / (1024 * 1024),
                "max_blob_size": metrics.get("max_blob_size", 0),
                "max_blob_size_mb": metrics.get("max_blob_size", 0) / (1024 * 1024),
                "tree_count": metrics.get("tree_count", 0),
                "max_tree_entries": metrics.get("max_tree_entries", 0),
                "commit_count": metrics.get("commit_count", 0),
                "max_path_depth": metrics.get("max_path_depth", 0),
                "max_path_length": metrics.get("max_path_length", 0),
            })

        # Identify repos with expected issues
        bloated_repo = None
        deep_history_repo = None
        wide_tree_repo = None
        healthy_repo = None

        for repo in repositories:
            name = repo.get("repository", "")
            if "bloated" in name.lower():
                bloated_repo = repo
            elif "deep-history" in name.lower():
                deep_history_repo = repo
            elif "wide-tree" in name.lower():
                wide_tree_repo = repo
            elif "healthy" in name.lower():
                healthy_repo = repo

        # Expected values based on synthetic repo creation
        expected_values = {
            "bloated": {
                "max_blob_size_min_mb": 5.0,  # At least 5 MB blob
                "total_blob_size_min_mb": 15.0,  # At least 15 MB total
            },
            "deep-history": {
                "commit_count_range": (490, 510),  # Around 501 commits
            },
            "wide-tree": {
                "max_tree_entries_min": 900,  # At least 900 entries
                "max_path_depth_min": 15,  # At least 15 deep
            },
        }

        # Calculate accuracy scores
        accuracy_results = []

        if bloated_repo:
            metrics = bloated_repo.get("metrics", {})
            max_blob_mb = metrics.get("max_blob_size", 0) / (1024 * 1024)
            total_blob_mb = metrics.get("blob_total_size", 0) / (1024 * 1024)
            accuracy_results.append({
                "test": "bloated_max_blob",
                "expected": f">= {expected_values['bloated']['max_blob_size_min_mb']} MB",
                "actual": f"{max_blob_mb:.1f} MB",
                "passed": max_blob_mb >= expected_values["bloated"]["max_blob_size_min_mb"],
            })
            accuracy_results.append({
                "test": "bloated_total_blob",
                "expected": f">= {expected_values['bloated']['total_blob_size_min_mb']} MB",
                "actual": f"{total_blob_mb:.1f} MB",
                "passed": total_blob_mb >= expected_values["bloated"]["total_blob_size_min_mb"],
            })

        if deep_history_repo:
            metrics = deep_history_repo.get("metrics", {})
            commit_count = metrics.get("commit_count", 0)
            exp_range = expected_values["deep-history"]["commit_count_range"]
            accuracy_results.append({
                "test": "deep_history_commits",
                "expected": f"{exp_range[0]}-{exp_range[1]}",
                "actual": str(commit_count),
                "passed": exp_range[0] <= commit_count <= exp_range[1],
            })

        if wide_tree_repo:
            metrics = wide_tree_repo.get("metrics", {})
            max_entries = metrics.get("max_tree_entries", 0)
            max_depth = metrics.get("max_path_depth", 0)
            accuracy_results.append({
                "test": "wide_tree_entries",
                "expected": f">= {expected_values['wide-tree']['max_tree_entries_min']}",
                "actual": str(max_entries),
                "passed": max_entries >= expected_values["wide-tree"]["max_tree_entries_min"],
            })
            accuracy_results.append({
                "test": "wide_tree_depth",
                "expected": f">= {expected_values['wide-tree']['max_path_depth_min']}",
                "actual": str(max_depth),
                "passed": max_depth >= expected_values["wide-tree"]["max_path_depth_min"],
            })

        # Calculate pass rate
        passed_tests = sum(1 for r in accuracy_results if r["passed"])
        total_tests = len(accuracy_results)
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        summary = analysis.get("summary", {})

        return {
            "repo_metrics": repo_metrics,
            "accuracy_results": accuracy_results,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "pass_rate": round(pass_rate, 1),
            "expected_values": expected_values,
            "total_repositories": len(repositories),
            "total_duration_ms": summary.get("total_duration_ms", 0),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate size accuracy requirements."""
        failures = []

        analysis = self.load_analysis()
        if "error" in analysis:
            failures.append(analysis["error"])
            return False, failures

        # Check all repos have metrics
        for repo in analysis.get("repositories", []):
            if not repo.get("metrics"):
                failures.append(f"Repository {repo.get('repository')} has no metrics")

            metrics = repo.get("metrics", {})
            required_fields = ["blob_count", "commit_count", "tree_count"]
            for field in required_fields:
                if field not in metrics:
                    failures.append(
                        f"Repository {repo.get('repository')} missing {field}"
                    )

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Size Accuracy Judge

You are evaluating the **size accuracy** of git-sizer's repository health analysis.

## Evaluation Dimension
**Size Accuracy (35% weight)**: Are blob/tree/commit size measurements correct?

## Background
git-sizer analyzes Git repositories to measure:
- Blob sizes (file content sizes in Git object store)
- Tree entry counts (files per directory)
- Commit counts and history depth
- Path depths and lengths

Accurate measurements are critical for:
- Identifying LFS candidates (large blobs)
- Detecting monorepo anti-patterns (wide trees)
- Understanding repository complexity (deep history)

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | All measurements within 5% of expected values |
| 4 | Most measurements accurate, minor variations |
| 3 | Generally accurate, some significant variations |
| 2 | Several measurements significantly off |
| 1 | Measurements unreliable or missing |

## Sub-Dimensions
1. **Blob Accuracy (40%)**: Blob sizes correctly measured
2. **Tree Accuracy (30%)**: Tree entry counts correct
3. **Commit Accuracy (30%)**: Commit counts and depth correct

## Evidence to Evaluate

### Repository Metrics
```json
{{ repo_metrics }}
```

### Accuracy Test Results
```json
{{ accuracy_results }}
```

### Summary
- Tests passed: {{ passed_tests }}/{{ total_tests }}
- Pass rate: {{ pass_rate }}%

### Expected Values
```json
{{ expected_values }}
```

## Evaluation Questions
1. Are blob sizes accurately measured for both small and large files?
2. Do tree entry counts reflect actual directory contents?
3. Are commit counts accurate for both shallow and deep histories?
4. Is path depth calculation correct for nested structures?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "size_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of size accuracy assessment",
  "evidence_cited": ["specific measurements examined"],
  "recommendations": ["improvements for accuracy"],
  "sub_scores": {
    "blob_accuracy": <1-5>,
    "tree_accuracy": <1-5>,
    "commit_accuracy": <1-5>
  }
}
```
'''

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
