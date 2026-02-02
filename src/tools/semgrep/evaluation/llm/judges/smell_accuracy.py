"""Smell Accuracy Judge - Evaluates code smell detection precision/recall."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class SmellAccuracyJudge(BaseJudge):
    """Evaluates accuracy of code smell detection.

    Validates that:
    - Detected smells match expected smells from ground truth
    - DD smell categories are correctly assigned
    - Severity levels are appropriate
    - Line numbers are accurate
    """

    @property
    def dimension_name(self) -> str:
        return "smell_accuracy"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis output and ground truth for comparison.

        For real-world evaluation mode, also injects synthetic evaluation
        context to help the LLM understand tool baseline capability.
        """
        gt_dir = self.working_dir / "evaluation" / "ground-truth"

        # Load analysis from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate data from all repos
        all_files = []
        total_summary = {"total_smells": 0, "total_files": 0, "files_with_smells": 0}
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                file_info["_repo"] = repo_name  # Tag with source repo
                all_files.append(file_info)
            summary = self.extract_summary(repo_analysis)
            total_summary["total_smells"] += summary.get("total_smells", 0)
            total_summary["total_files"] += summary.get("total_files", 0)
            total_summary["files_with_smells"] += summary.get("files_with_smells", 0)

        # Create aggregated analysis dict for remaining code
        analysis = {"files": all_files, "summary": total_summary}

        # Sample smells for LLM review
        all_smells = []
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                all_smells.append({
                    "file": Path(file_info.get("path", "")).name,
                    "rule_id": smell.get("rule_id", ""),
                    "dd_smell_id": smell.get("dd_smell_id", ""),
                    "dd_category": smell.get("dd_category", ""),
                    "severity": smell.get("severity", ""),
                    "line": smell.get("line_start", 0),
                    "message": smell.get("message", "")[:150],
                })

        sample_smells = all_smells[:20]  # First 20 for review

        # Load ground truth expectations
        gt_expectations = []
        for gt_file in gt_dir.glob("*.json"):
            try:
                gt = json.loads(gt_file.read_text())
                lang = gt.get("language", gt_file.stem)
                for file_name, file_data in gt.get("files", {}).items():
                    gt_expectations.append({
                        "language": lang,
                        "file": file_name,
                        "expected_smells": file_data.get("expected_smells", []),
                        "expected_count_min": file_data.get("expected_count_min", 0),
                        "expected_count_max": file_data.get("expected_count_max", 100),
                    })
            except (json.JSONDecodeError, KeyError):
                continue

        # Compare detected vs expected
        comparison = []
        for file_info in analysis.get("files", []):
            file_path = file_info.get("path", "")
            file_name = Path(file_path).name
            detected_count = file_info.get("smell_count", 0)
            detected_types = list(set(
                s.get("dd_smell_id", s.get("rule_id", ""))
                for s in file_info.get("smells", [])
            ))

            # Find matching ground truth
            for gt in gt_expectations:
                if gt["file"] in file_path or file_name == gt["file"]:
                    comparison.append({
                        "file": file_name,
                        "detected_count": detected_count,
                        "expected_min": gt["expected_count_min"],
                        "expected_max": gt["expected_count_max"],
                        "detected_types": detected_types,
                        "expected_types": gt["expected_smells"],
                    })
                    break

        # Per-category breakdown
        by_category = {}
        for smell in all_smells:
            cat = smell.get("dd_category", "uncategorized")
            if cat not in by_category:
                by_category[cat] = {"count": 0, "sample_rules": set()}
            by_category[cat]["count"] += 1
            by_category[cat]["sample_rules"].add(smell.get("rule_id", "")[:50])

        # Convert sets to lists for JSON
        for cat in by_category:
            by_category[cat]["sample_rules"] = list(by_category[cat]["sample_rules"])[:5]

        summary = analysis.get("summary", {})

        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "sample_smells": sample_smells,
            "ground_truth_comparison": comparison,
            "by_category": by_category,
            "total_smells": summary.get("total_smells", 0),
            "total_files": summary.get("total_files", 0),
            "files_with_smells": summary.get("files_with_smells", 0),
            "categories_covered": list(by_category.keys()),
            "gt_expectations": gt_expectations[:15],
        }

        # Inject synthetic context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate smell detection against ground truth."""
        failures = []

        # Load from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            failures.append(f"No analysis files found in {self.output_dir}")
            return False, failures

        # Aggregate all files
        all_files = []
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                file_info["_repo"] = repo_name
                all_files.append(file_info)
        analysis = {"files": all_files}

        gt_dir = self.working_dir / "evaluation" / "ground-truth"

        # Load ground truth
        expectations = {}
        for gt_file in gt_dir.glob("*.json"):
            try:
                gt = json.loads(gt_file.read_text())
                for file_name, file_data in gt.get("files", {}).items():
                    expectations[file_name] = file_data
            except (json.JSONDecodeError, KeyError):
                continue

        # Check each file against ground truth
        for file_info in analysis.get("files", []):
            file_path = file_info.get("path", "")
            file_name = Path(file_path).name

            # Find matching expectation
            matched_key = None
            for key in expectations:
                if key in file_path or file_name == key:
                    matched_key = key
                    break

            if matched_key:
                expected = expectations[matched_key]
                actual_count = file_info.get("smell_count", 0)
                min_count = expected.get("expected_count_min", 0)
                max_count = expected.get("expected_count_max", 100)

                if not (min_count <= actual_count <= max_count):
                    failures.append(
                        f"{file_name}: {actual_count} smells outside expected range [{min_count}, {max_count}]"
                    )

        # Check that smells have required fields
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                if not smell.get("rule_id"):
                    failures.append(f"Smell missing rule_id in {file_info.get('path')}")
                if not smell.get("line_start"):
                    failures.append(f"Smell missing line_start in {file_info.get('path')}")

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Smell Accuracy Judge

You are evaluating the **accuracy of code smell detection** by Semgrep, a pattern-based static analysis tool.

## Evaluation Dimension
**Smell Accuracy (35% weight)**: Are detected smells genuine code quality issues? Are they correctly categorized?

## Background
Semgrep uses pattern-matching rules to detect code issues:
- Security vulnerabilities (SQL injection, XSS, etc.)
- Error handling issues (empty catch, broad exception)
- Resource management problems
- Code quality patterns

DD Smell Categories:
- error_handling: Exception handling issues
- async_concurrency: Async/threading problems
- resource_management: Resource leaks
- security: Injection, exposure issues
- size_complexity: Code complexity
- dependency: Coupling issues
- nullability: Null handling
- api_design: Interface problems
- dead_code: Unreachable code

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | All smells genuine, correct categories, accurate locations |
| 4 | 90%+ accuracy, minor category mismatches |
| 3 | 70%+ accuracy, some incorrect categorizations |
| 2 | Significant errors (>30% incorrect) |
| 1 | Many false detections or systematic failures |

## Sub-Dimensions
1. **True Positives (40%)**: Detected smells are actual issues
2. **Category Accuracy (30%)**: DD categories correctly assigned
3. **Location Accuracy (30%)**: Line numbers and file paths correct

## Evidence to Evaluate

### Sample Smells Detected
```json
{{ sample_smells }}
```

### Ground Truth Comparison
```json
{{ ground_truth_comparison }}
```

### By DD Category
```json
{{ by_category }}
```

### Overall Statistics
- Total smells: {{ total_smells }}
- Total files: {{ total_files }}
- Files with smells: {{ files_with_smells }}
- Categories covered: {{ categories_covered }}

### Ground Truth Expectations
```json
{{ gt_expectations }}
```

## Evaluation Questions
1. Do the sample smells represent genuine code quality issues?
2. Are DD categories correctly assigned (error_handling, security, etc.)?
3. Are smell counts within expected ranges for test files?
4. Are there obvious false positives (non-issues flagged)?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "smell_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of accuracy assessment",
  "evidence_cited": ["specific files and smells examined"],
  "recommendations": ["improvements for accuracy"],
  "sub_scores": {
    "true_positives": <1-5>,
    "category_accuracy": <1-5>,
    "location_accuracy": <1-5>
  }
}
```
'''
    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
