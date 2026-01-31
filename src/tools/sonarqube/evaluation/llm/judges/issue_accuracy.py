"""Issue Accuracy LLM Judge for SonarQube evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class IssueAccuracyJudge(BaseJudge):
    """Evaluates whether SonarQube issues are correctly categorized."""

    @property
    def dimension_name(self) -> str:
        return "issue_accuracy"

    @property
    def weight(self) -> float:
        return 0.35

    def get_default_prompt(self) -> str:
        return """You are evaluating the accuracy of SonarQube issue categorization.

Analyze the provided issues and assess:
1. Bug classification (33%): Are BUG type issues genuine bugs?
2. Vulnerability classification (33%): Are VULNERABILITY issues real security risks?
3. Code smell classification (34%): Are CODE_SMELL issues maintainability concerns?

Evidence:
{{ evidence }}

For each issue, consider:
- Does the issue type match its actual nature?
- Is the severity appropriate?
- Does the message accurately describe the problem?

Respond with JSON:
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>",
  "evidence_cited": ["<evidence item 1>", ...],
  "recommendations": ["<recommendation 1>", ...],
  "sub_scores": {
    "bug_classification": <1-5>,
    "vulnerability_classification": <1-5>,
    "code_smell_classification": <1-5>
  }
}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect issue samples for evaluation."""
        data = self.analysis_results
        issues = data.get("issues", {}).get("items", [])

        bugs = [i for i in issues if i.get("type") == "BUG"][:10]
        vulns = [i for i in issues if i.get("type") == "VULNERABILITY"][:10]
        smells = [i for i in issues if i.get("type") == "CODE_SMELL"][:10]

        return {
            "total_issues": len(issues),
            "sampled_bugs": bugs,
            "sampled_vulnerabilities": vulns,
            "sampled_code_smells": smells,
            "rollups": data.get("issues", {}).get("rollups", {}),
        }

    def evaluate(self) -> JudgeResult:
        """Evaluate issue categorization accuracy."""
        data = self.analysis_results
        issues = data.get("issues", {}).get("items", [])

        if not issues:
            return self._create_result(
                score=3,
                confidence=0.5,
                reasoning="No issues found to evaluate",
                recommendations=["Analyze a project with more issues for better evaluation"],
            )

        # Sample issues for evaluation
        bugs = [i for i in issues if i.get("type") == "BUG"][:10]
        vulns = [i for i in issues if i.get("type") == "VULNERABILITY"][:10]
        smells = [i for i in issues if i.get("type") == "CODE_SMELL"][:10]

        # Heuristic evaluation
        bug_score = self._evaluate_bugs(bugs)
        vuln_score = self._evaluate_vulns(vulns)
        smell_score = self._evaluate_smells(smells)

        # Weighted average
        total_score = round((bug_score * 0.33 + vuln_score * 0.33 + smell_score * 0.34))
        total_score = max(1, min(5, total_score))

        return self._create_result(
            score=total_score,
            confidence=0.8,
            reasoning=f"Evaluated {len(bugs)} bugs, {len(vulns)} vulnerabilities, {len(smells)} code smells",
            evidence=[
                f"Total issues: {len(issues)}",
                f"Bugs sampled: {len(bugs)}",
                f"Vulnerabilities sampled: {len(vulns)}",
                f"Code smells sampled: {len(smells)}",
            ],
            sub_scores={
                "bug_classification": bug_score,
                "vulnerability_classification": vuln_score,
                "code_smell_classification": smell_score,
            },
        )

    def _evaluate_bugs(self, bugs: list) -> int:
        """Evaluate bug classification accuracy."""
        if not bugs:
            return 3  # Neutral if no bugs
        # Check for common bug patterns in messages
        valid_count = sum(
            1 for b in bugs
            if any(kw in b.get("message", "").lower() for kw in
                   ["null", "error", "exception", "fail", "crash", "overflow", "leak", "undefined"])
        )
        ratio = valid_count / len(bugs) if bugs else 0
        return max(1, min(5, round(1 + ratio * 4)))

    def _evaluate_vulns(self, vulns: list) -> int:
        """Evaluate vulnerability classification accuracy."""
        if not vulns:
            return 3  # Neutral if no vulnerabilities
        # Check for security-related patterns
        security_keywords = ["sql", "inject", "xss", "csrf", "auth", "password", "credential",
                           "secret", "hardcoded", "sensitive", "exposure", "leak"]
        valid_count = sum(
            1 for v in vulns
            if any(kw in v.get("message", "").lower() or kw in v.get("rule", "").lower()
                   for kw in security_keywords)
        )
        ratio = valid_count / len(vulns) if vulns else 0
        return max(1, min(5, round(1 + ratio * 4)))

    def _evaluate_smells(self, smells: list) -> int:
        """Evaluate code smell classification accuracy."""
        if not smells:
            return 3  # Neutral if no smells
        # Code smells should have maintainability-related patterns
        smell_keywords = ["complexity", "duplicate", "unused", "dead", "naming", "long",
                         "parameter", "cognitive", "method", "class", "refactor"]
        valid_count = sum(
            1 for s in smells
            if any(kw in s.get("message", "").lower() or kw in s.get("rule", "").lower()
                   for kw in smell_keywords)
        )
        ratio = valid_count / len(smells) if smells else 0
        return max(1, min(5, round(1 + ratio * 4)))
