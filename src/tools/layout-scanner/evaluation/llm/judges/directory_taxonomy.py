"""Directory Taxonomy Judge for Layout Scanner evaluation.

Evaluates whether directory classifications accurately reflect
the content and purpose of directories.
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge


class DirectoryTaxonomyJudge(BaseJudge):
    """Judge that evaluates directory taxonomy accuracy.

    Focuses on:
    - Directory classification accuracy based on content
    - Classification distribution rollups
    - Language distribution accuracy
    - Direct vs recursive metric correctness
    """

    @property
    def dimension_name(self) -> str:
        return "directory_taxonomy"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total LLM score

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Directory Taxonomy Evaluation

You are evaluating the Layout Scanner's directory classification accuracy.

## Evaluation Dimension: Directory Taxonomy (Weight: 25%)

### What to Evaluate

1. **Directory Classification Accuracy** (40%)
   - Do directory classifications match their actual content?
   - Is `src/` classified as "source"?
   - Is `tests/` classified as "test"?
   - Is `docs/` classified as "docs"?
   - Is `node_modules/` or `vendor/` classified as "vendor"?

2. **Classification Distribution Rollups** (30%)
   - Does `classification_distribution` accurately count files by category?
   - Are nested directories correctly aggregated?
   - Do recursive counts include all subdirectories?

3. **Language Distribution** (30%)
   - Does `language_distribution` accurately reflect file languages?
   - Are language counts consistent with file extensions?
   - Are multi-language directories correctly represented?

## Evidence

### Directory Sample
{{ sample_directories }}

### Repository Structure Overview
{{ structure_overview }}

### Ground Truth
{{ ground_truth }}

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All directories correctly classified, distributions accurate, rollups consistent |
| 4 | 95%+ directories correct, minor distribution discrepancies |
| 3 | 85%+ directories correct, some rollup issues |
| 2 | 70%+ directories correct, significant distribution errors |
| 1 | <70% correct, distributions unreliable |

## Required Output

Return a JSON object with this structure:
```json
{
    "dimension": "directory_taxonomy",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "sub_scores": {
        "classification_accuracy": <1-5>,
        "distribution_rollups": <1-5>,
        "language_distribution": <1-5>
    },
    "evidence_cited": ["<specific examples from the output>"],
    "recommendations": ["<improvements if score < 5>"]
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for directory taxonomy evaluation."""
        outputs = self._load_output_files()
        ground_truths = self._load_ground_truth_files()

        # Collect directory samples
        sample_directories = []
        structure_overview = []

        for output in outputs:
            repo = output.get("repository", "unknown")
            directories = output.get("directories", {})

            # Sample directories
            dir_list = list(directories.values())
            sampled = dir_list[:15]  # Top directories

            for d in sampled:
                sample_directories.append(
                    {
                        "repository": repo,
                        "path": d.get("path"),
                        "classification": d.get("classification"),
                        "classification_reason": d.get("classification_reason"),
                        "direct_file_count": d.get("direct_file_count"),
                        "recursive_file_count": d.get("recursive_file_count"),
                        "classification_distribution": d.get(
                            "classification_distribution", {}
                        ),
                        "language_distribution": d.get("language_distribution", {}),
                    }
                )

            # Build structure overview
            root_dirs = [d for d in dir_list if d.get("path", "").count("/") == 0]
            structure_overview.append(
                {
                    "repository": repo,
                    "total_directories": len(directories),
                    "root_directories": [
                        {"path": d.get("path"), "classification": d.get("classification")}
                        for d in root_dirs
                    ],
                }
            )

        # Collect ground truth
        gt_expectations = []
        for gt in ground_truths:
            expected = gt.get("expected", {})
            gt_expectations.append(
                {
                    "repository": gt.get("repository"),
                    "total_directories": expected.get("total_directories"),
                    "classifications": expected.get("classifications", {}),
                }
            )

        return {
            "sample_directories": sample_directories[:30],
            "structure_overview": structure_overview,
            "ground_truth": gt_expectations,
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions for directory taxonomy."""
        outputs = self._load_output_files()
        ground_truths = self._load_ground_truth_files()
        failures = []

        gt_by_repo = {gt.get("repository"): gt for gt in ground_truths}

        for output in outputs:
            repo = output.get("repository")
            gt = gt_by_repo.get(repo)

            if not gt:
                continue

            expected = gt.get("expected", {})
            expected_dirs = expected.get("total_directories")

            if expected_dirs is not None:
                actual_dirs = len(output.get("directories", {}))
                if actual_dirs != expected_dirs:
                    failures.append(
                        f"{repo}: Expected {expected_dirs} directories, "
                        f"got {actual_dirs}"
                    )

            # Verify classification distribution totals
            directories = output.get("directories", {})
            for d in directories.values():
                cls_dist = d.get("classification_distribution", {})
                recursive_count = d.get("recursive_file_count", 0)
                dist_total = sum(cls_dist.values())

                if dist_total != recursive_count and recursive_count > 0:
                    path = d.get("path", "unknown")
                    failures.append(
                        f"{repo}: Directory {path} classification_distribution "
                        f"sum ({dist_total}) != recursive_file_count ({recursive_count})"
                    )

        return len(failures) == 0, failures
