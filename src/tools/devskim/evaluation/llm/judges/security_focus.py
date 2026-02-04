"""Security Focus Judge for DevSkim security linting evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class SecurityFocusJudge(BaseJudge):
    """Evaluates DevSkim's focus on security-relevant findings.

    Assesses whether DevSkim maintains appropriate security focus
    versus general code quality issues.
    """

    @property
    def dimension_name(self) -> str:
        return "security_focus"

    @property
    def weight(self) -> float:
        return 0.15  # Ensures tool stays focused on security

    def collect_evidence(self) -> dict[str, Any]:
        """Collect security focus evidence."""
        all_results = self.load_all_analysis_results()

        # Categorize findings
        security_findings = 0
        quality_findings = 0
        unknown_findings = 0

        security_keywords = {
            "inject", "sql", "xss", "script", "secret", "password", "credential",
            "crypto", "encrypt", "hash", "auth", "session", "token", "csrf",
            "deserial", "traversal", "path", "redirect", "ssrf", "xxe", "ldap"
        }

        security_samples = []
        quality_samples = []

        for repo_name, data in all_results.items():
            for file_info in data.get("files", data.get("results", [])):
                for finding in file_info.get("issues", file_info.get("findings", [])):
                    rule = finding.get("rule_id", finding.get("ruleId", "")).lower()
                    message = finding.get("message", "").lower()
                    category = finding.get("category", "").lower()

                    combined_text = f"{rule} {message} {category}"

                    is_security = any(kw in combined_text for kw in security_keywords)

                    if is_security:
                        security_findings += 1
                        if len(security_samples) < 8:
                            security_samples.append({
                                "rule": finding.get("rule_id", finding.get("ruleId", "")),
                                "message": finding.get("message", "")[:80],
                            })
                    else:
                        quality_findings += 1
                        if len(quality_samples) < 5:
                            quality_samples.append({
                                "rule": finding.get("rule_id", finding.get("ruleId", "")),
                                "message": finding.get("message", "")[:80],
                            })

        total = security_findings + quality_findings
        security_ratio = security_findings / total if total > 0 else 0

        return {
            "security_findings": security_findings,
            "quality_findings": quality_findings,
            "security_ratio": f"{security_ratio:.1%}",
            "security_samples": security_samples,
            "quality_samples": quality_samples,
            "focus_assessment": {
                "expected": "DevSkim should primarily report security issues",
                "threshold": "Security findings should be >80% of total",
                "keywords_checked": list(security_keywords)[:10],
            },
            "repos_analyzed": list(all_results.keys()),
        }

    def get_default_prompt(self) -> str:
        return """# DevSkim Security Focus Evaluation

You are an expert security evaluator assessing whether DevSkim maintains appropriate security focus.

## Evidence
{{ evidence }}

## Evaluation Criteria

Evaluate the following aspects:

1. **Security Relevance** (weight: 50%)
   - Are findings primarily security-related?
   - Is the tool focused on vulnerabilities vs. style issues?

2. **Signal Quality** (weight: 30%)
   - Are security findings actionable?
   - Is there excessive noise from non-security issues?

3. **Appropriate Scope** (weight: 20%)
   - Is DevSkim staying in its lane (security)?
   - Are general code quality issues appropriately minimal?

## Expected Focus
DevSkim is a security linter and should primarily report:
- Injection vulnerabilities
- Authentication/Authorization issues
- Cryptographic weaknesses
- Sensitive data exposure
- Security misconfigurations

NOT primarily:
- Code style issues
- Performance problems
- General best practices (unless security-related)

## Scoring Rubric

- **5 (Excellent)**: >90% security focus, all findings actionable
- **4 (Good)**: 80-90% security focus, minimal noise
- **3 (Acceptable)**: 60-80% security focus, some irrelevant findings
- **2 (Poor)**: 40-60% security focus, significant noise
- **1 (Failing)**: <40% security focus, tool is not security-focused

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
    "security_relevance": <1-5>,
    "signal_quality": <1-5>,
    "appropriate_scope": <1-5>
  }
}
```
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify DevSkim maintains security focus."""
        failures = []
        all_results = self.load_all_analysis_results()

        security_keywords = {"inject", "sql", "xss", "secret", "password", "crypto", "auth", "csrf"}

        security_count = 0
        total_count = 0

        for data in all_results.values():
            for file_info in data.get("files", data.get("results", [])):
                for finding in file_info.get("issues", file_info.get("findings", [])):
                    total_count += 1
                    combined = f"{finding.get('rule_id', '')} {finding.get('message', '')}".lower()
                    if any(kw in combined for kw in security_keywords):
                        security_count += 1

        if total_count > 10:  # Only check if sufficient findings
            security_ratio = security_count / total_count
            if security_ratio < 0.5:
                failures.append(f"Security focus ratio {security_ratio:.0%} is below 50% threshold")

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
