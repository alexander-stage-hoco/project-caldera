"""
Insight Quality judge for evaluating top insights extraction from analysis reports.

This judge evaluates how well the report identifies and prioritizes the most
critical insights from code analysis, and produces recommendations for improvement.
"""

from dataclasses import dataclass, field
from typing import Any

from .base import BaseJudge, JudgeResult


@dataclass
class InsightQualityResult(JudgeResult):
    """Extended result with top 3 insights and improvement proposals."""

    recommended_top_3: list[dict[str, Any]] = field(default_factory=list)
    improvement_proposals: list[dict[str, Any]] = field(default_factory=list)
    missed_critical_issues: list[str] = field(default_factory=list)


class InsightQualityJudge(BaseJudge):
    """
    Evaluates the quality of insights in analysis reports.

    This judge focuses on:
    1. Whether insights are grounded in evidence from the analysis data
    2. Whether the most critical issues are properly prioritized
    3. Whether insights are actionable
    4. Whether any critical issues were missed

    Sub-dimensions:
    - evidence_grounding (30%): Are insights backed by analysis data?
    - prioritization_quality (25%): Are top issues truly most important?
    - actionability (25%): Can developers act on these insights?
    - completeness (20%): Were critical issues missed?
    """

    name = "insight_quality"
    weight = 0.50  # Higher weight for insight extraction focus

    sub_dimensions = {
        "evidence_grounding": 0.30,
        "prioritization_quality": 0.25,
        "actionability": 0.25,
        "completeness": 0.20,
    }

    def get_system_prompt(self) -> str:
        return """You are a senior software architect evaluating code analysis reports for insight quality. Your goal is to assess whether the report correctly identifies and prioritizes the most critical findings.

## Priority Hierarchy (use this for evaluating prioritization)
When evaluating whether insights are properly prioritized, apply this severity ordering:
1. **Security issues** (CRITICAL/HIGH CVEs, exposed secrets, injection vulnerabilities)
2. **Stability risks** (high cyclomatic complexity in critical paths, untested code)
3. **Maintainability issues** (code duplication, tight coupling, knowledge silos)
4. **Code quality** (linting issues, style violations, minor smells)

## Evaluation Dimensions

### 1. Evidence Grounding (30%)
Are the stated insights backed by specific data from the analysis?
- 5: Every insight cites specific metrics, files, or findings
- 4: Most insights have clear evidence with minor gaps
- 3: Some insights lack supporting data
- 2: Many claims without supporting evidence
- 1: Insights appear disconnected from analysis data

### 2. Prioritization Quality (25%)
Are the highlighted issues truly the most critical?
- 5: Top issues perfectly align with severity hierarchy
- 4: Mostly correct with minor ordering issues
- 3: Some important issues buried, less critical ones highlighted
- 2: Significant prioritization problems
- 1: Critical issues ignored, trivial issues emphasized

### 3. Actionability (25%)
Can a developer take action based on these insights?
- 5: Clear next steps with specific file/function locations
- 4: Good guidance with minor gaps in specificity
- 3: General direction but requires investigation
- 2: Vague recommendations without clear targets
- 1: No actionable guidance

### 4. Completeness (20%)
Were critical issues properly surfaced?
- 5: All critical issues identified and explained
- 4: Most issues covered, minor omissions
- 3: Some notable gaps in coverage
- 2: Important issues missed
- 1: Major blind spots in the analysis

## Response Format

Return your evaluation as JSON with this exact structure:
```json
{
  "overall_score": <float 1-5>,
  "sub_scores": {
    "evidence_grounding": <float 1-5>,
    "prioritization_quality": <float 1-5>,
    "actionability": <float 1-5>,
    "completeness": <float 1-5>
  },
  "reasoning": "<explanation of scores>",
  "suggestions": ["<improvement suggestion>", ...],
  "recommended_top_3": [
    {
      "rank": 1,
      "insight": "<what the top insight should be>",
      "evidence": "<supporting data from the report>",
      "rationale": "<why this is the most critical>"
    },
    {
      "rank": 2,
      "insight": "<second most critical insight>",
      "evidence": "<supporting data>",
      "rationale": "<why this ranks second>"
    },
    {
      "rank": 3,
      "insight": "<third most critical insight>",
      "evidence": "<supporting data>",
      "rationale": "<why this ranks third>"
    }
  ],
  "improvement_proposals": [
    {
      "current_insight": "<insight as stated in report>",
      "issue": "<what's wrong with it>",
      "proposed_improvement": "<how to improve it>"
    }
  ],
  "missed_critical_issues": ["<issue that should have been highlighted>", ...]
}
```

Important:
- Base recommended_top_3 on the ACTUAL DATA in the report, not hypotheticals
- Each insight should reference specific findings (CVE IDs, file paths, metric values)
- Apply the priority hierarchy strictly when determining rankings
- Be constructive in improvement_proposals - help make insights better"""

    def get_evaluation_prompt(self, report_content: str, context: dict[str, Any]) -> str:
        format_type = context.get("format", "html")

        return f"""Please evaluate the insight quality of this code analysis report.

## Your Task
1. Identify what the report presents as its key findings/insights
2. Evaluate whether these insights are well-grounded in the analysis data
3. Assess if the most critical issues are properly prioritized
4. Determine what the TRUE top 3 insights should be based on the data
5. Suggest improvements for weak insights

## Report Format
This is a {format_type.upper()} report from a multi-tool code analysis pipeline.

---
REPORT CONTENT:
---
{report_content[:50000]}
---

Evaluate on all four dimensions (evidence_grounding, prioritization_quality, actionability, completeness) and provide your response as JSON with recommended_top_3 and improvement_proposals."""

    def _parse_response(self, response: str) -> InsightQualityResult:
        """
        Parse the LLM response into an InsightQualityResult.

        Extends base parsing to extract top 3 insights and improvement proposals.
        """
        try:
            # Try to extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            import json
            data = json.loads(json_str.strip())

            return InsightQualityResult(
                judge_name=self.name,
                overall_score=float(data.get("overall_score", 3.0)),
                sub_scores={k: float(v) for k, v in data.get("sub_scores", {}).items()},
                reasoning=data.get("reasoning", ""),
                suggestions=data.get("suggestions", []),
                raw_response=response,
                recommended_top_3=data.get("recommended_top_3", []),
                improvement_proposals=data.get("improvement_proposals", []),
                missed_critical_issues=data.get("missed_critical_issues", []),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Return a default result on parse failure
            return InsightQualityResult(
                judge_name=self.name,
                overall_score=3.0,
                sub_scores={},
                reasoning=f"Failed to parse response: {e}",
                suggestions=[],
                raw_response=response,
                metadata={"parse_error": str(e)},
                recommended_top_3=[],
                improvement_proposals=[],
                missed_critical_issues=[],
            )
