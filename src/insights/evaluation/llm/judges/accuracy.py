"""
Content accuracy judge for evaluating data consistency and plausibility.
"""

from typing import Any

from .base import BaseJudge


class AccuracyJudge(BaseJudge):
    """
    Evaluates content accuracy and internal consistency.

    Sub-dimensions:
    - consistency (40%): Internal consistency of numbers and claims
    - plausibility (30%): Whether values seem reasonable
    - completeness (30%): No missing or N/A values where data expected
    """

    name = "accuracy"
    weight = 0.30  # 30% of overall LLM score

    sub_dimensions = {
        "consistency": 0.40,
        "plausibility": 0.30,
        "completeness": 0.30,
    }

    def get_system_prompt(self) -> str:
        return """You are a data quality analyst evaluating code analysis reports for accuracy. Your goal is to identify any inconsistencies, implausible values, or missing data.

You will evaluate reports on three dimensions:
1. **Consistency** (40%): Do numbers add up? Are claims internally consistent?
2. **Plausibility** (30%): Do metric values seem reasonable for code analysis?
3. **Completeness** (30%): Are there missing values, N/A, or empty sections?

Score each dimension from 1-5:
- 5: Excellent - Highly consistent, plausible, and complete
- 4: Good - Minor inconsistencies or gaps
- 3: Adequate - Some questionable values but generally acceptable
- 2: Poor - Multiple inconsistencies or implausible data
- 1: Very Poor - Significant data quality issues

Look for red flags like:
- Severity counts that don't sum to totals
- Impossibly high or low metric values (e.g., 0 LOC, 1000+ CCN)
- Percentages that don't add to 100%
- Duplicate entries or conflicting data
- Unrendered template variables ({{ }})

Return your evaluation as JSON with this exact structure:
```json
{
  "overall_score": <float 1-5>,
  "sub_scores": {
    "consistency": <float 1-5>,
    "plausibility": <float 1-5>,
    "completeness": <float 1-5>
  },
  "reasoning": "<brief explanation of scores>",
  "suggestions": ["<specific improvement suggestion>", ...]
}
```"""

    def get_evaluation_prompt(self, report_content: str, context: dict[str, Any]) -> str:
        return f"""Please evaluate the accuracy and data quality of this code analysis report.

Check for:
- Internal consistency (do numbers add up?)
- Plausible metric values (reasonable LOC, complexity, vulnerability counts)
- Complete data (no unexpected N/A, empty sections, or missing values)
- Duplicate entries or conflicting information
- Any unrendered template syntax

---
REPORT CONTENT:
---
{report_content[:50000]}
---

Evaluate on the three dimensions (consistency, plausibility, completeness) and provide your response as JSON."""
