"""Classification Reasoning Judge for Layout Scanner evaluation.

Evaluates the quality and accuracy of file classification reasoning,
including confidence scores and classification explanations.
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge


class ClassificationReasoningJudge(BaseJudge):
    """Judge that evaluates the quality of classification reasoning.

    Focuses on:
    - Accuracy of classification assignments
    - Quality of classification_reason explanations
    - Appropriateness of confidence scores
    - Consistency across similar files
    """

    @property
    def dimension_name(self) -> str:
        return "classification_reasoning"

    @property
    def weight(self) -> float:
        return 0.30  # 30% of total LLM score

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Classification Reasoning Evaluation

You are evaluating the Layout Scanner's file classification reasoning quality.

## Evaluation Dimension: Classification Reasoning (Weight: 30%)

### What to Evaluate

1. **Classification Accuracy** (40%)
   - Are files correctly classified into categories (source, test, config, docs, vendor, etc.)?
   - Do edge cases (files that could belong to multiple categories) have appropriate classifications?

2. **Reasoning Quality** (30%)
   - Does the `classification_reason` field explain WHY the classification was made?
   - Are reasons specific (e.g., "path:tests/" vs generic "pattern match")?
   - Do reasons cite the actual signals used (path, filename, extension)?

3. **Confidence Calibration** (30%)
   - Are confidence scores appropriately calibrated?
   - High confidence (>0.9) for unambiguous files?
   - Lower confidence for edge cases?

## Evidence

### Scanner Output Sample
{{ sample_files }}

### Ground Truth
{{ ground_truth }}

### Classification Distribution
{{ classification_distribution }}

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All classifications correct, reasons are specific and cite signals, confidence well-calibrated |
| 4 | 95%+ correct, reasons mostly specific, minor confidence issues |
| 3 | 85%+ correct, some generic reasons, confidence mostly appropriate |
| 2 | 70%+ correct, many generic reasons, confidence poorly calibrated |
| 1 | <70% correct, reasons missing or meaningless, confidence unreliable |

## Required Output

Return a JSON object with this structure:
```json
{
    "dimension": "classification_reasoning",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "sub_scores": {
        "accuracy": <1-5>,
        "reasoning_quality": <1-5>,
        "confidence_calibration": <1-5>
    },
    "evidence_cited": ["<specific examples from the output>"],
    "recommendations": ["<improvements if score < 5>"]
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for classification reasoning evaluation."""
        outputs = self._load_output_files()
        ground_truths = self._load_ground_truth_files()

        # Aggregate sample files and distributions
        sample_files = []
        classification_distribution: dict[str, int] = {}

        for output in outputs:
            files = output.get("files", {})
            sampled = self._sample_files(files, sample_size=10)
            sample_files.extend(sampled)

            # Build distribution
            for f in files.values():
                cls = f.get("classification", "other")
                classification_distribution[cls] = (
                    classification_distribution.get(cls, 0) + 1
                )

        # Collect ground truth expectations
        gt_expectations = []
        for gt in ground_truths:
            expected = gt.get("expected", {})
            if "classifications" in expected:
                gt_expectations.append(
                    {
                        "repository": gt.get("repository"),
                        "expected_classifications": expected["classifications"],
                        "specific_files": expected.get("specific_files", {}),
                    }
                )

        evidence = {
            "sample_files": sample_files[:30],  # Limit for prompt size
            "ground_truth": gt_expectations,
            "classification_distribution": classification_distribution,
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
                    "Evaluate based on ground truth comparison only"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions for classification accuracy."""
        outputs = self._load_output_files()
        ground_truths = self._load_ground_truth_files()
        failures = []

        # Build lookup from repository name to ground truth
        gt_by_repo = {gt.get("repository"): gt for gt in ground_truths}

        for output in outputs:
            repo = output.get("repository")
            gt = gt_by_repo.get(repo)

            if not gt:
                continue

            expected = gt.get("expected", {})
            specific_files = expected.get("specific_files", {})

            files = output.get("files", {})

            # Check specific file classifications
            for path, expected_info in specific_files.items():
                expected_cls = expected_info.get("classification")
                if not expected_cls:
                    continue

                # Find file by path
                actual_file = None
                for f in files.values():
                    if f.get("path") == path:
                        actual_file = f
                        break

                if actual_file is None:
                    failures.append(f"{repo}: File {path} not found in output")
                elif actual_file.get("classification") != expected_cls:
                    failures.append(
                        f"{repo}: {path} classified as "
                        f"'{actual_file.get('classification')}' "
                        f"but expected '{expected_cls}'"
                    )

        return len(failures) == 0, failures
