"""CCN Accuracy Judge - Evaluates cyclomatic complexity accuracy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class CCNAccuracyJudge(BaseJudge):
    """Evaluates accuracy of CCN (cyclomatic complexity) values.

    Compares reported CCN values against ground truth to assess whether
    Lizard correctly calculates complexity for different function types.
    """

    @property
    def dimension_name(self) -> str:
        return "ccn_accuracy"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis output and ground truth for comparison."""
        gt_dir = self.working_dir / "evaluation" / "ground-truth"

        # Load analysis
        if not self.analysis_path.exists():
            return {"error": f"Analysis file not found: {self.analysis_path}"}

        analysis = self._load_analysis()

        # Sample functions for LLM review (diverse selection)
        samples = []
        simple_funcs = []
        complex_funcs = []
        edge_case_funcs = []

        for file_info in analysis.get("files", []):
            for func in file_info.get("functions", []):
                func_data = {
                    "file": file_info["path"],
                    "function": func["name"],
                    "reported_ccn": func["ccn"],
                    "nloc": func["nloc"],
                    "params": func.get("parameter_count", 0),
                }

                # Categorize by CCN
                if func["ccn"] == 1:
                    simple_funcs.append(func_data)
                elif func["ccn"] >= 10:
                    complex_funcs.append(func_data)
                elif "edge_case" in file_info["path"].lower():
                    edge_case_funcs.append(func_data)

        # Build balanced sample
        samples.extend(simple_funcs[:5])
        samples.extend(complex_funcs[:5])
        samples.extend(edge_case_funcs[:5])

        # Load ground truth for comparison
        gt_comparison = []
        for lang_file in gt_dir.glob("*.json"):
            try:
                gt = json.loads(lang_file.read_text())
                for file_name, file_data in gt.get("files", {}).items():
                    for func_name, func_data in file_data.get("functions", {}).items():
                        gt_comparison.append({
                            "file": file_name,
                            "function": func_name,
                            "expected_ccn": func_data.get("ccn"),
                            "expected_nloc": func_data.get("nloc"),
                        })
            except (json.JSONDecodeError, KeyError):
                continue

        # Compute by_language from files
        by_language = {}
        for file_info in analysis.get("files", []):
            lang = file_info.get("language", "unknown")
            func_count = file_info.get("function_count", 0)
            by_language[lang] = by_language.get(lang, 0) + func_count

        evidence = {
            "sample_functions": samples[:20],
            "ground_truth_sample": gt_comparison[:25],
            "total_functions": analysis.get("summary", {}).get("total_functions", 0),
            "ccn_distribution": analysis.get("summary", {}).get("ccn_distribution", {}),
            "by_language": by_language,
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
        """Validate CCN values are within expected ranges."""
        failures = []

        if not self.analysis_path.exists():
            failures.append(f"Analysis file not found: {self.analysis_path}")
            return False, failures

        try:
            analysis = self._load_analysis()
        except json.JSONDecodeError as e:
            failures.append(f"Invalid JSON in analysis file: {e}")
            return False, failures

        # Check CCN values are valid (>= 1)
        for file_info in analysis.get("files", []):
            for func in file_info.get("functions", []):
                if func.get("ccn", 0) < 1:
                    failures.append(
                        f"Invalid CCN {func.get('ccn')} for {func.get('name')} "
                        f"in {file_info.get('path')}"
                    )

        # Check distribution validity
        dist = analysis.get("summary", {}).get("ccn_distribution", {})
        if dist:
            min_val = dist.get("min", 0)
            median = dist.get("median", 0)
            max_val = dist.get("max", 0)

            if min_val > median or median > max_val:
                failures.append(
                    f"Invalid CCN distribution: min({min_val}) > median({median}) "
                    f"or median > max({max_val})"
                )

            # Check percentiles are monotonic
            percentiles = ["p25", "p50", "p75", "p90", "p95", "p99"]
            prev_val = 0
            for p in percentiles:
                val = dist.get(p, 0)
                if val < prev_val:
                    failures.append(f"Non-monotonic percentiles: {p}={val} < previous")
                prev_val = val

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# CCN Accuracy Judge

You are evaluating the **accuracy of cyclomatic complexity (CCN)** values reported by Lizard, a static analysis tool.

## Evaluation Dimension
**CCN Accuracy (35% weight)**: Does the reported CCN correctly reflect the branching structure of each function?

## Background
Cyclomatic complexity (CCN) measures the number of linearly independent paths through code:
- CCN = 1 + number of decision points (if, elif, else, for, while, case, catch, &&, ||, ?)
- CCN=1 means straight-line code with no branches
- CCN=2-5 indicates simple conditional logic
- CCN=10-20 indicates complex business logic
- CCN>20 indicates functions that should be refactored

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | All sampled CCN values match ground truth exactly |
| 4 | 90%+ exact matches, minor deviations (±1) for rest |
| 3 | 70%+ within ±1 of expected, some outliers |
| 2 | Significant errors (>30% off by ±2 or more) |
| 1 | CCN values are systematically wrong or unreliable |

## Sub-Dimensions
1. **Simple Functions (33%)**: CCN=1 functions correctly identified
2. **Complex Functions (33%)**: CCN 10-20 range accuracy
3. **Edge Cases (34%)**: Lambdas, nested functions, class methods

## Evidence to Evaluate

### Sample Functions from Analysis
```json
{{ sample_functions }}
```

### Ground Truth Comparison
```json
{{ ground_truth_sample }}
```

### Overall Statistics
- Total functions: {{ total_functions }}
- CCN distribution: {{ ccn_distribution }}
- By language: {{ by_language }}

## Evaluation Questions
1. Do simple functions (straight-line code) correctly report CCN=1?
2. Do complex functions with multiple branches report CCN proportional to branch count?
3. Are edge cases (lambdas, nested, methods) handled consistently?
4. Are there any systematic over/under-counting patterns?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "ccn_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of accuracy assessment",
  "evidence_cited": ["specific functions examined"],
  "recommendations": ["improvements for accuracy"],
  "sub_scores": {
    "simple_functions": <1-5>,
    "complex_functions": <1-5>,
    "edge_cases": <1-5>
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
