"""False Positive Rate Judge - Evaluates precision of smell detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class FalsePositiveRateJudge(BaseJudge):
    """Evaluates false positive rate in smell detection.

    Validates that:
    - Clean files have minimal/zero smells detected
    - Detected smells are contextually appropriate
    - No trivial code flagged as problematic
    - Severity levels match actual severity
    """

    @property
    def dimension_name(self) -> str:
        return "false_positive_rate"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and identify potential false positives."""
        # Load from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate files from all repos
        all_files = []
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                file_info["_repo"] = repo_name
                all_files.append(file_info)
        analysis = {"files": all_files}

        # Identify files that should be clean (no_smell in name)
        clean_file_results = []
        for file_info in analysis.get("files", []):
            path = file_info.get("path", "").lower()
            file_name = Path(path).name
            if "no_smell" in path or "clean" in path or "no_smells" in path:
                clean_file_results.append({
                    "file": file_name,
                    "smell_count": file_info.get("smell_count", 0),
                    "smells": [
                        {
                            "rule": s.get("rule_id", "")[:50],
                            "line": s.get("line_start", 0),
                            "message": s.get("message", "")[:100],
                        }
                        for s in file_info.get("smells", [])
                    ],
                })

        # Analyze severity distribution
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "WARNING": 0, "INFO": 0}
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                sev = smell.get("severity", "UNKNOWN").upper()
                if sev in severity_counts:
                    severity_counts[sev] += 1

        # Sample potential false positives (low-confidence detections)
        potential_fps = []
        for file_info in analysis.get("files", []):
            file_name = Path(file_info.get("path", "")).name
            for smell in file_info.get("smells", []):
                # Look for potentially trivial detections
                msg = smell.get("message", "").lower()
                rule = smell.get("rule_id", "").lower()

                # Heuristics for potential FPs
                is_trivial = any([
                    "consider" in msg,
                    "may be" in msg,
                    "might" in msg,
                    "info" in smell.get("severity", "").lower(),
                ])

                if is_trivial and len(potential_fps) < 10:
                    potential_fps.append({
                        "file": file_name,
                        "rule": smell.get("rule_id", "")[:50],
                        "severity": smell.get("severity", ""),
                        "line": smell.get("line_start", 0),
                        "message": smell.get("message", "")[:150],
                        "reason": "Low confidence language in message",
                    })

        # Calculate precision metrics
        total_smells = sum(f.get("smell_count", 0) for f in analysis.get("files", []))
        fp_in_clean_files = sum(f["smell_count"] for f in clean_file_results)

        summary = analysis.get("summary", {})

        return {
            "clean_file_results": clean_file_results,
            "potential_false_positives": potential_fps,
            "severity_distribution": severity_counts,
            "total_smells": total_smells,
            "fp_in_clean_files": fp_in_clean_files,
            "clean_files_tested": len(clean_file_results),
            "precision_estimate": (total_smells - fp_in_clean_files) / max(total_smells, 1) * 100,
            "total_files": summary.get("total_files", 0),
            "files_with_smells": summary.get("files_with_smells", 0),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate false positive rate is acceptable."""
        failures = []

        # Load from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            failures.append(f"No analysis files found in {self.output_dir}")
            return False, failures

        # Aggregate files from all repos
        all_files = []
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                all_files.append(file_info)
        analysis = {"files": all_files}

        # Check clean files have no smells
        for file_info in analysis.get("files", []):
            path = file_info.get("path", "").lower()
            smell_count = file_info.get("smell_count", 0)

            if ("no_smell" in path or "no_smells" in path) and smell_count > 0:
                failures.append(
                    f"Clean file {Path(path).name} has {smell_count} smells (expected 0)"
                )

        # Check severity reasonableness (not all HIGH)
        high_count = 0
        total_count = 0
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                total_count += 1
                if smell.get("severity", "").upper() == "HIGH":
                    high_count += 1

        if total_count > 0 and high_count / total_count > 0.8:
            failures.append(
                f"Severity inflation: {high_count}/{total_count} ({high_count/total_count:.0%}) marked HIGH"
            )

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# False Positive Rate Judge

You are evaluating the **precision (false positive rate)** of Semgrep's code smell detection.

## Evaluation Dimension
**False Positive Rate (20% weight)**: Are detected smells genuine issues, or are there false alarms?

## Background
False positives in code analysis are problematic because:
- They waste developer time investigating non-issues
- They erode trust in the tool
- They create noise that hides real problems

A good analyzer should:
- NOT flag clean, well-written code
- NOT flag trivial patterns as severe
- NOT inflate severity levels
- Be contextually aware

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | <5% false positive rate, clean files have 0 smells |
| 4 | 5-10% FP rate, rare false alarms |
| 3 | 10-20% FP rate, occasional false alarms |
| 2 | 20-40% FP rate, significant noise |
| 1 | >40% FP rate, many false alarms |

## Sub-Dimensions
1. **Clean File Precision (40%)**: Files marked clean have no smells
2. **Contextual Appropriateness (35%)**: Detections are contextually valid
3. **Severity Calibration (25%)**: Severity levels are not inflated

## Evidence to Evaluate

### Clean File Results (Expected 0 Smells)
```json
{{ clean_file_results }}
```

### Potential False Positives
```json
{{ potential_false_positives }}
```

### Severity Distribution
```json
{{ severity_distribution }}
```

### Metrics
- Total smells detected: {{ total_smells }}
- False positives in clean files: {{ fp_in_clean_files }}
- Clean files tested: {{ clean_files_tested }}
- Precision estimate: {{ precision_estimate }}%
- Total files analyzed: {{ total_files }}
- Files with smells: {{ files_with_smells }}

## Evaluation Questions
1. Do clean files (no_smell in name) correctly have 0 smells?
2. Are the potential false positives actually non-issues?
3. Is severity distribution reasonable (not all HIGH)?
4. Are trivial patterns incorrectly flagged as problems?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "false_positive_rate",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of precision assessment",
  "evidence_cited": ["specific files and false positives examined"],
  "recommendations": ["improvements to reduce false positives"],
  "sub_scores": {
    "clean_file_precision": <1-5>,
    "contextual_appropriateness": <1-5>,
    "severity_calibration": <1-5>
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
