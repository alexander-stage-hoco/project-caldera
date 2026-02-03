"""Call relationship LLM judge for symbol-scanner evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class CallRelationshipJudge(BaseJudge):
    """Judge for evaluating call extraction accuracy.

    Evaluates whether the symbol-scanner correctly extracts all function
    and method calls with accurate caller/callee relationships.
    """

    @property
    def dimension_name(self) -> str:
        """Name of the evaluation dimension."""
        return "call_relationship"

    @property
    def weight(self) -> float:
        """Weight of this dimension in overall score (30%)."""
        return 0.30

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for call relationship evaluation.

        Returns:
            Dictionary containing extracted calls and source context.
        """
        output_dir = self._resolve_output_dir()
        calls: list[dict[str, Any]] = []
        symbols: list[dict[str, Any]] = []
        source_samples: list[dict[str, Any]] = []

        # Find the output file
        output_file = output_dir / "output.json"
        if not output_file.exists():
            json_files = list(output_dir.glob("*.json"))
            if json_files:
                output_file = json_files[0]

        if output_file.exists():
            data = self._load_tool_output(output_file)
            calls = data.get("calls", [])
            symbols = data.get("symbols", [])

            # Sample source files for context
            unique_paths = list({c.get("caller_file") for c in calls if c.get("caller_file")})[:3]
            for file_path in unique_paths:
                full_path = self.working_dir / file_path
                if full_path.exists():
                    try:
                        content = full_path.read_text()[:2000]
                        source_samples.append({
                            "path": file_path,
                            "content": content,
                        })
                    except OSError:
                        pass

        # Prepare evidence summary
        calls_by_type = {}
        for call in calls:
            call_type = call.get("call_type", "unknown")
            calls_by_type[call_type] = calls_by_type.get(call_type, 0) + 1

        # Build symbol lookup for validation
        symbol_names = {s.get("symbol_name") for s in symbols if s.get("symbol_name")}

        evidence = {
            "calls": calls[:50],  # Sample for context
            "calls_count": len(calls),
            "calls_by_type": calls_by_type,
            "symbols_count": len(symbols),
            "symbol_names_sample": list(symbol_names)[:20],
            "source_samples": source_samples,
            "evaluation_mode": self.evaluation_mode,
        }

        # Add synthetic baseline context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )

        return evidence

    def get_default_prompt(self) -> str:
        """Return default prompt template if file doesn't exist."""
        return """# Call Relationship Judge

## Task
Evaluate whether the symbol-scanner correctly extracts function and method calls.

## Evidence
{{ evidence }}

## Evaluation Criteria

### Completeness (40%)
- All function calls captured
- All method calls captured
- Cross-file calls included

### Accuracy (40%)
- Caller/callee pairs correct
- Line numbers accurate
- Call types classified correctly

### Edge Cases (20%)
- Async/await calls handled
- Method chaining
- Dynamic calls

## Response Format
Respond with ONLY a JSON object with a BINARY PASS/FAIL decision:

{
  "dimension": "call_relationship",
  "decision": "PASS" or "FAIL",
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "issues": [
    {"severity": "HIGH" or "MEDIUM" or "LOW", "type": "<issue_type>", "call": "<caller->callee>", "description": "<what's wrong>"}
  ],
  "recommendations": ["<improvement suggestions>"]
}

Decision rules:
- PASS: All critical calls extracted correctly, caller/callee pairs accurate
- FAIL: Missing important calls, incorrect relationships, or systematic errors
"""


# Legacy function interface for backwards compatibility
JUDGE_NAME = "call_relationship"
JUDGE_DESCRIPTION = "Evaluates call extraction accuracy"


def get_prompt(source_code: str, extracted_calls: list) -> str:
    """Generate the evaluation prompt for the LLM (legacy interface)."""
    calls_text = "\n".join(
        f"- {c.get('caller_symbol')} -> {c.get('callee_symbol')} at line {c.get('line_number')}"
        for c in extracted_calls
    )

    return f"""Evaluate the call relationship extraction accuracy.

## Source Code
```python
{source_code}
```

## Extracted Calls
{calls_text}

## Task
1. Are all function calls captured?
2. Are caller/callee pairs correct?
3. Are line numbers accurate?
4. Are any calls missing?

Provide a score from 0-100 and explain any issues found.
"""


def parse_response(response: str) -> dict:
    """Parse the LLM response into a structured result (legacy interface)."""
    score = 85
    try:
        import re
        match = re.search(r'(\d{1,3})\s*(?:/100|%)', response)
        if match:
            score = int(match.group(1))
    except Exception:
        pass

    return {
        "judge": JUDGE_NAME,
        "score": score,
        "confidence": 0.8,
        "raw_response": response,
    }
