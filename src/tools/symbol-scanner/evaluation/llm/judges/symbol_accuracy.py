"""Symbol accuracy LLM judge for symbol-scanner evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class SymbolAccuracyJudge(BaseJudge):
    """Judge for evaluating symbol extraction accuracy.

    Evaluates whether the symbol-scanner correctly extracts all function,
    class, and method definitions from source code.
    """

    @property
    def dimension_name(self) -> str:
        """Name of the evaluation dimension."""
        return "symbol_accuracy"

    @property
    def weight(self) -> float:
        """Weight of this dimension in overall score (30%)."""
        return 0.30

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for symbol accuracy evaluation.

        Returns:
            Dictionary containing source code samples and extracted symbols.
        """
        output_dir = self._resolve_output_dir()
        symbols: list[dict[str, Any]] = []
        source_samples: list[dict[str, Any]] = []

        # Find the output file
        output_file = output_dir / "output.json"
        if not output_file.exists():
            # Try finding any JSON output file
            json_files = list(output_dir.glob("*.json"))
            if json_files:
                output_file = json_files[0]

        if output_file.exists():
            data = self._load_tool_output(output_file)
            symbols = data.get("symbols", [])

            # Sample source files for context (limit to avoid token overflow)
            unique_paths = list({s.get("path") for s in symbols if s.get("path")})[:3]
            for file_path in unique_paths:
                full_path = self.working_dir / file_path
                if full_path.exists():
                    try:
                        content = full_path.read_text()[:2000]  # Limit content size
                        source_samples.append({
                            "path": file_path,
                            "content": content,
                        })
                    except OSError:
                        pass

        # Prepare evidence summary
        symbols_by_type = {}
        for sym in symbols:
            sym_type = sym.get("symbol_type", "unknown")
            symbols_by_type[sym_type] = symbols_by_type.get(sym_type, 0) + 1

        evidence = {
            "symbols": symbols[:50],  # Sample for context
            "symbols_count": len(symbols),
            "symbols_by_type": symbols_by_type,
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
        return """# Symbol Accuracy Judge

## Task
Evaluate whether the symbol-scanner correctly extracts all function, class, and method definitions.

## Evidence
{{ evidence }}

## Evaluation Criteria

### Completeness (40%)
- All top-level functions extracted
- All classes extracted
- All methods within classes extracted

### Accuracy (40%)
- Symbol types correctly identified
- Line numbers accurate
- Export status correct

### Edge Cases (20%)
- Async functions handled
- Decorators don't interfere

## Response Format
Respond with ONLY a JSON object with a BINARY PASS/FAIL decision:

{
  "dimension": "symbol_accuracy",
  "decision": "PASS" or "FAIL",
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "issues": [
    {"severity": "HIGH" or "MEDIUM" or "LOW", "type": "<issue_type>", "symbol": "<symbol_name>", "description": "<what's wrong>"}
  ],
  "recommendations": ["<improvement suggestions>"]
}

Decision rules:
- PASS: All critical symbols extracted correctly, minor issues only
- FAIL: Missing important symbols, incorrect types, or systematic errors
"""


# Legacy function interface for backwards compatibility
JUDGE_NAME = "symbol_accuracy"
JUDGE_DESCRIPTION = "Evaluates symbol extraction accuracy"


def get_prompt(source_code: str, extracted_symbols: list) -> str:
    """Generate the evaluation prompt for the LLM (legacy interface)."""
    symbols_text = "\n".join(
        f"- {s.get('symbol_name')} ({s.get('symbol_type')}) at line {s.get('line_start')}"
        for s in extracted_symbols
    )

    return f"""Evaluate the symbol extraction accuracy.

## Source Code
```python
{source_code}
```

## Extracted Symbols
{symbols_text}

## Task
1. Are all functions, classes, and methods extracted?
2. Are symbol types correct?
3. Are line numbers accurate?
4. Are any symbols missing?

Provide a score from 0-100 and explain any issues found.
"""


def parse_response(response: str) -> dict:
    """Parse the LLM response into a structured result (legacy interface)."""
    score = 85  # Default score
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
