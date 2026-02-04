"""Detection Accuracy Judge for DevSkim security linting evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class DetectionAccuracyJudge(BaseJudge):
    """Evaluates the accuracy of DevSkim's security issue detection.

    Assesses whether DevSkim correctly identifies security vulnerabilities,
    comparing against ground truth expectations.
    """

    @property
    def dimension_name(self) -> str:
        return "detection_accuracy"

    @property
    def weight(self) -> float:
        return 0.40  # Primary dimension for security tools

    def collect_evidence(self) -> dict[str, Any]:
        """Collect detection accuracy evidence."""
        all_results = self.load_all_analysis_results()

        # Load ground truth
        gt_path = self.working_dir / "evaluation" / "ground-truth" / "csharp.json"
        ground_truth = {}
        if gt_path.exists():
            ground_truth = json.loads(gt_path.read_text())

        # Security-focused categories
        security_categories = {
            "sql_injection": 0,
            "xss": 0,
            "path_traversal": 0,
            "secrets": 0,
            "crypto": 0,
            "deserialization": 0,
            "other": 0,
        }

        total_files = 0
        total_findings = 0
        findings_by_severity = {"critical": 0, "important": 0, "moderate": 0, "low": 0}
        sample_findings = []

        for repo_name, data in all_results.items():
            files = data.get("files", data.get("results", []))
            total_files += len(files)

            for file_info in files:
                findings = file_info.get("issues", file_info.get("findings", []))
                total_findings += len(findings)

                for finding in findings:
                    # Categorize by security type
                    rule_id = finding.get("rule_id", finding.get("ruleId", "")).lower()
                    category = finding.get("category", "").lower()

                    if "sql" in rule_id or "sql" in category:
                        security_categories["sql_injection"] += 1
                    elif "xss" in rule_id or "cross-site" in category:
                        security_categories["xss"] += 1
                    elif "path" in rule_id or "traversal" in category:
                        security_categories["path_traversal"] += 1
                    elif "secret" in rule_id or "credential" in category or "password" in rule_id:
                        security_categories["secrets"] += 1
                    elif "crypto" in rule_id or "encrypt" in category:
                        security_categories["crypto"] += 1
                    elif "serial" in rule_id or "deserial" in category:
                        security_categories["deserialization"] += 1
                    else:
                        security_categories["other"] += 1

                    # Track severity
                    severity = finding.get("severity", "moderate").lower()
                    if severity in findings_by_severity:
                        findings_by_severity[severity] += 1

                    # Collect samples
                    if len(sample_findings) < 10:
                        sample_findings.append({
                            "rule": finding.get("rule_id", finding.get("ruleId", "")),
                            "severity": severity,
                            "message": finding.get("message", "")[:100],
                            "file": str(file_info.get("path", file_info.get("filename", "")))[-50:],
                        })

        # Ground truth expectations
        gt_files = ground_truth.get("files", {})
        expected_categories = ground_truth.get("aggregate_expectations", {}).get("required_categories", [])

        return {
            "total_files_analyzed": total_files,
            "total_findings": total_findings,
            "security_categories": security_categories,
            "findings_by_severity": findings_by_severity,
            "sample_findings": sample_findings,
            "ground_truth": {
                "files_with_expectations": list(gt_files.keys()),
                "required_categories": expected_categories,
                "min_total_issues": ground_truth.get("aggregate_expectations", {}).get("min_total_issues", 0),
            },
            "repos_analyzed": list(all_results.keys()),
            # Synthetic context for LLM evaluation
            "evaluation_mode": self.evaluation_mode or "synthetic",
            "synthetic_baseline": "Ground truth files define expected security findings for synthetic test repositories",
            "interpretation_guidance": "This evaluation uses synthetic repos with known vulnerabilities. Detection rates should be evaluated against ground truth expectations.",
        }

    def get_default_prompt(self) -> str:
        return """# DevSkim Detection Accuracy Evaluation

You are an expert security evaluator assessing the detection accuracy of the DevSkim security linter.

## Evidence
{{ evidence }}

## Evaluation Criteria

Evaluate the following aspects:

1. **True Positive Rate** (weight: 40%)
   - Are known security vulnerabilities being detected?
   - Do findings match expected security categories?

2. **False Positive Rate** (weight: 30%)
   - Are there spurious security findings?
   - Is the noise level acceptable for security scanning?

3. **Vulnerability Classification** (weight: 30%)
   - Are security categories correctly identified (SQL injection, XSS, etc.)?
   - Are severity levels appropriate for the vulnerability type?

## Security Categories to Verify
- SQL Injection
- Cross-Site Scripting (XSS)
- Path Traversal
- Hardcoded Secrets/Credentials
- Weak Cryptography
- Insecure Deserialization

## Scoring Rubric

- **5 (Excellent)**: >95% detection rate, minimal false positives, accurate classification
- **4 (Good)**: 85-95% detection rate, low false positives, mostly accurate
- **3 (Acceptable)**: 70-85% detection rate, moderate false positives
- **2 (Poor)**: 50-70% detection rate, high false positives
- **1 (Failing)**: <50% detection rate, unreliable for security assessment

## Required Output

Provide your evaluation as a JSON object:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "true_positive_rate": <1-5>,
    "false_positive_rate": <1-5>,
    "vulnerability_classification": <1-5>
  }
}
```
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify basic security detection requirements."""
        failures = []
        all_results = self.load_all_analysis_results()

        # Load ground truth
        gt_path = self.working_dir / "evaluation" / "ground-truth" / "csharp.json"
        if gt_path.exists():
            gt = json.loads(gt_path.read_text())
            min_issues = gt.get("aggregate_expectations", {}).get("min_total_issues", 0)

            total_findings = 0
            for data in all_results.values():
                for file_info in data.get("files", data.get("results", [])):
                    total_findings += len(file_info.get("issues", file_info.get("findings", [])))

            if total_findings < min_issues:
                failures.append(f"Total findings {total_findings} < expected minimum {min_issues}")

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
