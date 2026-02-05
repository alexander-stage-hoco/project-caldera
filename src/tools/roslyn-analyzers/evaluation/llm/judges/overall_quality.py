"""Overall Quality Judge for Roslyn Analyzers evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class OverallQualityJudge(BaseJudge):
    """Evaluates overall analysis quality and reliability.

    Assesses:
    - False positive control (clean file analysis)
    - Detection precision (accuracy vs ground truth)
    - Coverage completeness (categories covered)
    - Actionability of messages (fix suggestions)

    Sub-scores:
    - false_positive_control (25%)
    - detection_precision (25%)
    - coverage_completeness (25%)
    - actionability (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "overall_quality"

    @property
    def weight(self) -> float:
        return 0.20

    def get_default_prompt(self) -> str:
        return """# Overall Quality Evaluation

You are evaluating the overall analysis quality and reliability of Roslyn Analyzers.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low violation counts are NOT automatically failures
- Judge output quality: schema compliance, category coverage, message clarity
- Consider: A tool that finds 0 issues in a high-quality codebase with proper output format deserves a high score

## Evidence to Review

### Overall Summary
{{ overall_summary }}

### Category Coverage
{{ category_coverage }}

### False Positive Analysis
{{ false_positive_analysis }}

### Message Quality Samples
{{ message_quality }}

## Evaluation Criteria

### Score 5 (Excellent)
- Very low false positive rate (<5%)
- High detection precision across all categories
- Complete coverage of expected categories
- Clear, actionable violation messages with fix suggestions
- Consistent severity classification

### Score 4 (Good)
- Low false positive rate (5-10%)
- Good detection precision
- Most categories covered
- Generally clear messages
- Good severity classification

### Score 3 (Acceptable)
- Moderate false positive rate (10-15%)
- Acceptable precision
- Core categories covered
- Messages understandable
- Basic severity classification

### Score 2 (Poor)
- High false positive rate (15-25%)
- Poor precision
- Missing categories
- Confusing messages
- Inconsistent severity

### Score 1 (Unacceptable)
- Very high false positive rate (>25%)
- Unreliable detection
- Major gaps in coverage
- Unclear messages
- No useful severity info

## Response Format

Respond with JSON:
```json
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific findings>"],
    "recommendations": ["<improvements>"],
    "sub_scores": {
        "false_positive_control": <1-5>,
        "detection_precision": <1-5>,
        "coverage_completeness": <1-5>,
        "actionability": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect overall quality evidence from all analysis outputs.

        For real-world evaluation mode, also injects synthetic evaluation
        context to help the LLM understand tool baseline capability.
        """
        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "overall_summary": {
                "total_files_analyzed": 0,
                "total_violations": 0,
                "total_repos": 0,
                "violations_by_severity": {},
                "violations_by_category": {},
            },
            "category_coverage": {
                "expected_categories": ["security", "design", "resource", "dead_code", "performance"],
                "detected_categories": [],
                "missing_categories": [],
            },
            "false_positive_analysis": {
                "clean_files_with_violations": 0,
                "total_clean_files": 0,
                "false_positive_rate": 0.0,
                "fp_examples": [],
            },
            "message_quality": [],
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()
        evidence["overall_summary"]["total_repos"] = len(all_results)

        all_categories = set()
        severity_totals = {}
        category_totals = {}
        message_samples = []

        for repo_name, output in all_results.items():
            results = self.unwrap_output(output)
            summary = results.get("summary", {})

            # Accumulate totals
            evidence["overall_summary"]["total_files_analyzed"] += summary.get("total_files_analyzed", 0)
            evidence["overall_summary"]["total_violations"] += summary.get("total_violations", 0)

            # Accumulate severity breakdown
            for severity, count in summary.get("violations_by_severity", {}).items():
                severity_totals[severity] = severity_totals.get(severity, 0) + count

            # Accumulate category breakdown
            for category, count in summary.get("violations_by_category", {}).items():
                category_totals[category] = category_totals.get(category, 0) + count
                all_categories.add(category)

            # Collect message samples
            files = results.get("files", [])
            for file_data in files[:3]:  # First 3 files per repo
                for violation in file_data.get("violations", [])[:2]:
                    message_samples.append({
                        "repo": repo_name,
                        "rule_id": violation.get("rule_id", ""),
                        "message": violation.get("message", "")[:300],
                        "severity": violation.get("severity", ""),
                        "has_documentation": bool(violation.get("documentation_url")),
                    })

        evidence["overall_summary"]["violations_by_severity"] = severity_totals
        evidence["overall_summary"]["violations_by_category"] = category_totals

        # Determine category coverage
        evidence["category_coverage"]["detected_categories"] = list(all_categories)
        evidence["category_coverage"]["missing_categories"] = [
            c for c in evidence["category_coverage"]["expected_categories"]
            if c not in all_categories
        ]

        # Analyze false positives using clean-code ground truth
        clean_gt = self.load_ground_truth_by_name("clean-code")
        if clean_gt:
            expected_clean = clean_gt.get("expected_clean_files", [])
            evidence["false_positive_analysis"]["total_clean_files"] = len(expected_clean)

            for repo_name, output in all_results.items():
                results = self.unwrap_output(output)
                files = results.get("files", [])
                for file_data in files:
                    file_path = file_data.get("path", "")
                    if any(clean_file in file_path for clean_file in expected_clean):
                        violation_count = file_data.get("violation_count", 0)
                        if violation_count > 0:
                            evidence["false_positive_analysis"]["clean_files_with_violations"] += 1
                            evidence["false_positive_analysis"]["fp_examples"].append({
                                "file": file_path,
                                "violations": violation_count,
                                "sample_rules": [v.get("rule_id") for v in file_data.get("violations", [])[:3]],
                            })

            # Calculate FP rate
            total_clean = evidence["false_positive_analysis"]["total_clean_files"]
            if total_clean > 0:
                fp_rate = evidence["false_positive_analysis"]["clean_files_with_violations"] / total_clean
                evidence["false_positive_analysis"]["false_positive_rate"] = round(fp_rate, 4)

        # Limit examples
        evidence["false_positive_analysis"]["fp_examples"] = evidence["false_positive_analysis"]["fp_examples"][:5]
        evidence["message_quality"] = message_samples[:10]

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
        """Check overall quality ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()
        evaluation = self.load_evaluation()

        # If we have neither analysis results nor evaluation summary, fail fast.
        if not all_results and not evaluation:
            failures.append("No analysis results or evaluation summary found")
            return False, failures

        if all_results:
            # Check that core categories are present
            all_categories = set()
            for output in all_results.values():
                results = self.unwrap_output(output)
                summary = results.get("summary", {})
                all_categories.update(summary.get("violations_by_category", {}).keys())

            # Security, design, and resource should be present
            required_categories = ["security", "design"]
            missing = [c for c in required_categories if c not in all_categories]
            if missing:
                failures.append(f"Missing required categories: {missing}")

            # Check false positive rate on clean files
            clean_gt = self.load_ground_truth_by_name("clean-code")
            if clean_gt:
                expected_clean = clean_gt.get("expected_clean_files", [])
                max_fp_rate = clean_gt.get("max_false_positive_rate", 0.1)

                clean_files_with_violations = 0
                total_clean_files = len(expected_clean)

                for output in all_results.values():
                    results = self.unwrap_output(output)
                    files = results.get("files", [])
                    for file_data in files:
                        file_path = file_data.get("path", "")
                        if any(clean_file in file_path for clean_file in expected_clean):
                            if file_data.get("violation_count", 0) > 0:
                                clean_files_with_violations += 1

                if total_clean_files > 0:
                    fp_rate = clean_files_with_violations / total_clean_files
                    if fp_rate > max_fp_rate:
                        failures.append(
                            f"False positive rate {fp_rate:.1%} exceeds maximum {max_fp_rate:.1%}"
                        )

        # Check overall pass rate from evaluation report
        if evaluation:
            summary = evaluation.get("summary", {})
            pass_rate = summary.get("pass_rate_pct", 0)
            if pass_rate < 80:
                failures.append(f"Pass rate too low: {pass_rate}% (minimum 80%)")

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
