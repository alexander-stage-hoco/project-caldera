"""Function Detection Judge - Evaluates function detection quality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class FunctionDetectionJudge(BaseJudge):
    """Evaluates quality of function detection.

    Assesses whether Lizard correctly identifies all functions including:
    - Regular functions
    - Class methods
    - Nested/inner functions
    - Lambda expressions
    - Anonymous functions
    """

    @property
    def dimension_name(self) -> str:
        return "function_detection"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect function detection evidence."""
        gt_dir = self.working_dir / "evaluation" / "ground-truth"

        # Handle missing analysis file with default values for all placeholders
        if not self.analysis_path.exists():
            evidence: dict[str, Any] = {
                "error": f"Analysis file not found: {self.analysis_path}",
                "total_detected": 0,
                "by_language": {},
                "regular_functions_sample": [],
                "class_methods_sample": [],
                "nested_functions_sample": [],
                "lambda_functions_sample": [],
                "anonymous_functions_sample": [],
                "expected_counts": {},
                "actual_counts": {},
                "files_with_functions": 0,
                "files_without_functions": 0,
                "evaluation_mode": self.evaluation_mode,
            }
            # Inject synthetic context even when analysis is missing
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

        analysis = self._load_analysis()

        # Categorize detected functions
        regular_functions = []
        class_methods = []
        nested_functions = []
        lambda_functions = []
        anonymous_functions = []

        for file_info in analysis.get("files", []):
            for func in file_info.get("functions", []):
                func_data = {
                    "file": file_info["path"],
                    "name": func["name"],
                    "long_name": func.get("long_name", ""),
                    "start_line": func.get("start_line"),
                    "end_line": func.get("end_line"),
                }

                name = func["name"]
                long_name = func.get("long_name", "")

                # Categorize
                if name == "(anonymous)" or "lambda" in name.lower():
                    if "lambda" in name.lower():
                        lambda_functions.append(func_data)
                    else:
                        anonymous_functions.append(func_data)
                elif "::" in long_name or "." in name:
                    class_methods.append(func_data)
                elif "inner" in name.lower() or "_" in name:
                    nested_functions.append(func_data)
                else:
                    regular_functions.append(func_data)

        # Load expected counts from ground truth
        expected_counts = {}
        for lang_file in gt_dir.glob("*.json"):
            try:
                gt = json.loads(lang_file.read_text())
                lang = gt.get("language", lang_file.stem)
                total_expected = sum(
                    fd.get("expected_functions", 0)
                    for fd in gt.get("files", {}).values()
                )
                expected_counts[lang] = total_expected
            except (json.JSONDecodeError, KeyError):
                continue

        # Get actual counts by language (computed from files)
        actual_counts = {}
        for file_info in analysis.get("files", []):
            lang = file_info.get("language", "unknown")
            func_count = file_info.get("function_count", 0)
            actual_counts[lang] = actual_counts.get(lang, 0) + func_count

        return {
            "total_detected": analysis.get("summary", {}).get("total_functions", 0),
            "by_language": actual_counts,
            "regular_functions_sample": regular_functions[:5],
            "class_methods_sample": class_methods[:5],
            "nested_functions_sample": nested_functions[:3],
            "lambda_functions_sample": lambda_functions[:3],
            "anonymous_functions_sample": anonymous_functions[:3],
            "expected_counts": expected_counts,
            "actual_counts": actual_counts,
            "files_with_functions": len([
                f for f in analysis.get("files", [])
                if f.get("function_count", 0) > 0
            ]),
            "files_without_functions": len([
                f for f in analysis.get("files", [])
                if f.get("function_count", 0) == 0
            ]),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate function detection against ground truth."""
        failures = []
        gt_dir = self.working_dir / "evaluation" / "ground-truth"

        if not self.analysis_path.exists():
            failures.append(f"Analysis file not found: {self.analysis_path}")
            return False, failures

        try:
            analysis = self._load_analysis()
        except json.JSONDecodeError as e:
            failures.append(f"Invalid JSON: {e}")
            return False, failures

        # Check we detected functions
        total = analysis.get("summary", {}).get("total_functions", 0)
        if total == 0:
            failures.append("No functions detected")
            return False, failures

        # Compute actual counts by language from files
        actual_by_lang = {}
        for file_info in analysis.get("files", []):
            lang = file_info.get("language", "unknown")
            func_count = file_info.get("function_count", 0)
            actual_by_lang[lang] = actual_by_lang.get(lang, 0) + func_count

        # Check each language has functions (if ground truth exists)
        for lang_file in gt_dir.glob("*.json"):
            try:
                gt = json.loads(lang_file.read_text())
                lang = gt.get("language", "")

                expected_total = sum(
                    fd.get("expected_functions", 0)
                    for fd in gt.get("files", {}).values()
                )

                # Find actual count for this language (handle name variations)
                actual = 0
                lang_normalized = lang.lower().replace("#", "sharp").replace("-", "")
                for detected_lang, count in actual_by_lang.items():
                    detected_normalized = detected_lang.lower().replace("#", "sharp").replace("-", "")
                    if detected_normalized == lang_normalized:
                        actual = count
                        break

                # Allow 20% tolerance
                if actual < expected_total * 0.8:
                    failures.append(
                        f"{lang}: detected {actual} functions, expected ~{expected_total}"
                    )
            except (json.JSONDecodeError, KeyError):
                continue

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Function Detection Judge

You are evaluating the **function detection quality** of Lizard, a static analysis tool.

## Evaluation Dimension
**Function Detection (25% weight)**: Are all functions correctly identified and categorized?

## Background
Lizard should detect various function types across 7 languages:
- Regular named functions
- Class methods (with qualified names like `ClassName::method`)
- Nested/inner functions
- Lambda expressions
- Anonymous functions/callbacks

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | All function types detected correctly across all languages |
| 4 | Minor gaps (1-2 function types partially detected) |
| 3 | Major function types detected, edge cases missed |
| 2 | Significant gaps in detection (>20% missing) |
| 1 | Function detection is unreliable |

## Sub-Dimensions
1. **Regular Functions (30%)**: Standard named functions
2. **Class Methods (30%)**: Methods with qualified names
3. **Edge Cases (40%)**: Nested, lambda, anonymous functions

## Evidence to Evaluate

### Detection Summary
- Total functions detected: {{ total_detected }}
- Files with functions: {{ files_with_functions }}
- Files without functions: {{ files_without_functions }}

### By Language
```json
{{ by_language }}
```

### Expected vs Actual Counts
- Expected: {{ expected_counts }}
- Actual: {{ actual_counts }}

### Sample Regular Functions
```json
{{ regular_functions_sample }}
```

### Sample Class Methods
```json
{{ class_methods_sample }}
```

### Sample Nested Functions
```json
{{ nested_functions_sample }}
```

### Sample Lambda Functions
```json
{{ lambda_functions_sample }}
```

### Sample Anonymous Functions
```json
{{ anonymous_functions_sample }}
```

## Evaluation Questions
1. Are function counts close to expected values for each language?
2. Are class methods detected with proper qualified names?
3. Are nested/inner functions detected separately from their parents?
4. Are lambdas and anonymous functions handled appropriately?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "function_detection",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of detection quality",
  "evidence_cited": ["specific examples examined"],
  "recommendations": ["improvements"],
  "sub_scores": {
    "regular_functions": <1-5>,
    "class_methods": <1-5>,
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
