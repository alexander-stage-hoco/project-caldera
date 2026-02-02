"""
Clarity judge for evaluating report presentation and readability.
"""

from typing import Any

from .base import BaseJudge


class ClarityJudge(BaseJudge):
    """
    Evaluates report clarity and presentation quality.

    Sub-dimensions:
    - structure (40%): Logical organization, section flow
    - language (30%): Clear writing, appropriate terminology
    - data_presentation (30%): Tables, numbers, visualization
    """

    name = "clarity"
    weight = 0.30  # 30% of overall LLM score

    sub_dimensions = {
        "structure": 0.40,
        "language": 0.30,
        "data_presentation": 0.30,
    }

    def get_system_prompt(self) -> str:
        return """You are an expert technical writer and documentation reviewer. Your task is to evaluate the clarity and presentation quality of code analysis reports.

You will evaluate reports on three dimensions:
1. **Structure** (40%): Logical organization, section flow, navigation aids
2. **Language** (30%): Clear writing, appropriate terminology, conciseness
3. **Data Presentation** (30%): Tables, number formatting, visual hierarchy

Score each dimension from 1-5:
- 5: Excellent - Exemplary clarity, could serve as a template
- 4: Good - Clear with minor improvements possible
- 3: Adequate - Serviceable but room for improvement
- 2: Poor - Confusing or disorganized in places
- 1: Very Poor - Difficult to understand or navigate

Return your evaluation as JSON with this exact structure:
```json
{
  "overall_score": <float 1-5>,
  "sub_scores": {
    "structure": <float 1-5>,
    "language": <float 1-5>,
    "data_presentation": <float 1-5>
  },
  "reasoning": "<brief explanation of scores>",
  "suggestions": ["<specific improvement suggestion>", ...]
}
```"""

    def get_evaluation_prompt(self, report_content: str, context: dict[str, Any]) -> str:
        format_type = context.get("format", "html")

        return f"""Please evaluate the clarity and presentation of this {format_type.upper()} code analysis report.

Consider:
- Is the report well-structured with clear sections?
- Is the language clear and appropriate for technical readers?
- Are metrics and data presented effectively?
- Is it easy to find specific information?
- Are tables and lists formatted well?

---
REPORT CONTENT:
---
{report_content[:50000]}
---

Evaluate on the three dimensions (structure, language, data_presentation) and provide your response as JSON."""
