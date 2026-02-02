"""
Actionability judge for evaluating how useful the report is for taking action.
"""

from typing import Any

from .base import BaseJudge


class ActionabilityJudge(BaseJudge):
    """
    Evaluates how actionable the report findings are.

    Sub-dimensions:
    - prioritization (35%): Clear ranking of issues by importance
    - locations (35%): Specific file/line locations provided
    - remediation (30%): Guidance on fixing issues
    """

    name = "actionability"
    weight = 0.40  # 40% of overall LLM score

    sub_dimensions = {
        "prioritization": 0.35,
        "locations": 0.35,
        "remediation": 0.30,
    }

    def get_system_prompt(self) -> str:
        return """You are a senior software engineer evaluating code analysis reports for actionability. Your goal is to assess whether a developer could use this report to effectively improve their codebase.

You will evaluate reports on three dimensions:
1. **Prioritization** (35%): Are issues clearly ranked by severity/importance?
2. **Locations** (35%): Are specific files, directories, or code locations identified?
3. **Remediation** (30%): Is there guidance on what to fix and how?

Score each dimension from 1-5:
- 5: Excellent - Immediately actionable, clear next steps
- 4: Good - Mostly actionable with minor gaps
- 3: Adequate - Provides direction but requires additional investigation
- 2: Poor - Vague or missing key details needed for action
- 1: Very Poor - No clear path to improvement

Return your evaluation as JSON with this exact structure:
```json
{
  "overall_score": <float 1-5>,
  "sub_scores": {
    "prioritization": <float 1-5>,
    "locations": <float 1-5>,
    "remediation": <float 1-5>
  },
  "reasoning": "<brief explanation of scores>",
  "suggestions": ["<specific improvement suggestion>", ...]
}
```"""

    def get_evaluation_prompt(self, report_content: str, context: dict[str, Any]) -> str:
        return f"""Please evaluate the actionability of this code analysis report.

Consider:
- Are the most critical issues clearly highlighted?
- Can a developer easily find where problems are located?
- Does the report help prioritize what to fix first?
- Is there enough context to understand each issue?
- Are there any recommendations or next steps?

---
REPORT CONTENT:
---
{report_content[:50000]}
---

Evaluate on the three dimensions (prioritization, locations, remediation) and provide your response as JSON."""
