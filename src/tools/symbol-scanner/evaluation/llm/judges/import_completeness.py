"""Import completeness LLM judge for symbol-scanner evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ImportCompletenessJudge(BaseJudge):
    """Judge for evaluating import extraction accuracy.

    Evaluates whether the symbol-scanner correctly extracts all import
    statements with accurate paths and symbols.
    """

    @property
    def dimension_name(self) -> str:
        """Name of the evaluation dimension."""
        return "import_completeness"

    @property
    def weight(self) -> float:
        """Weight of this dimension in overall score (20%)."""
        return 0.20

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for import completeness evaluation.

        Returns:
            Dictionary containing extracted imports and source context.
        """
        output_dir = self._resolve_output_dir()
        imports: list[dict[str, Any]] = []
        source_samples: list[dict[str, Any]] = []

        # Find the output file
        output_file = output_dir / "output.json"
        if not output_file.exists():
            json_files = list(output_dir.glob("*.json"))
            if json_files:
                output_file = json_files[0]

        if output_file.exists():
            data = self._load_tool_output(output_file)
            imports = data.get("imports", [])

            # Sample source files for context
            unique_paths = list({i.get("file") for i in imports if i.get("file")})[:3]
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
        imports_by_type = {}
        for imp in imports:
            imp_type = imp.get("import_type", "unknown")
            imports_by_type[imp_type] = imports_by_type.get(imp_type, 0) + 1

        evidence = {
            "imports": imports[:50],  # Sample for context
            "imports_count": len(imports),
            "imports_by_type": imports_by_type,
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
        return """# Import Completeness Judge

## Task
Evaluate whether the symbol-scanner correctly extracts all import statements.

## Evidence
{{ evidence }}

## Evaluation Criteria

### Completeness (40%)
- All import statements captured
- Module imports included
- From imports included

### Accuracy (40%)
- Import paths correct
- Imported symbols listed
- Line numbers accurate

### Edge Cases (20%)
- Relative imports handled
- Star imports captured
- Dynamic imports detected

## Response Format
Respond with ONLY a JSON object with a BINARY PASS/FAIL decision:

{
  "dimension": "import_completeness",
  "decision": "PASS" or "FAIL",
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "issues": [
    {"severity": "HIGH" or "MEDIUM" or "LOW", "type": "<issue_type>", "import": "<import_path>", "description": "<what's wrong>"}
  ],
  "recommendations": ["<improvement suggestions>"]
}

Decision rules:
- PASS: All import statements captured with correct paths and symbols
- FAIL: Missing imports, incorrect paths, or systematic errors
"""


# Legacy function interface for backwards compatibility
JUDGE_NAME = "import_completeness"
JUDGE_DESCRIPTION = "Evaluates import extraction accuracy"


def get_prompt(source_code: str, extracted_imports: list) -> str:
    """Generate the evaluation prompt for the LLM (legacy interface)."""
    imports_text = "\n".join(
        f"- {i.get('imported_path')} ({i.get('imported_symbols') or 'module'}) at line {i.get('line_number')}"
        for i in extracted_imports
    )

    return f"""Evaluate the import extraction accuracy.

## Source Code
```python
{source_code}
```

## Extracted Imports
{imports_text}

## Task
1. Are all import statements captured?
2. Are import paths correct?
3. Are imported symbols listed correctly?
4. Are any imports missing?

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
