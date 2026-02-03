"""Integration quality LLM judge for symbol-scanner evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationJudge(BaseJudge):
    """Judge for evaluating overall integration quality.

    Evaluates cross-file consistency, metadata validity, and overall
    coherence of the symbol-scanner output.
    """

    @property
    def dimension_name(self) -> str:
        """Name of the evaluation dimension."""
        return "integration"

    @property
    def weight(self) -> float:
        """Weight of this dimension in overall score (20%)."""
        return 0.20

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for integration quality evaluation.

        Returns:
            Dictionary containing full output analysis.
        """
        output_dir = self._resolve_output_dir()
        full_output: dict[str, Any] = {}

        # Find the output file
        output_file = output_dir / "output.json"
        if not output_file.exists():
            json_files = list(output_dir.glob("*.json"))
            if json_files:
                output_file = json_files[0]

        if output_file.exists():
            try:
                full_output = json.loads(output_file.read_text())
            except json.JSONDecodeError:
                pass

        # Extract components
        metadata = full_output.get("metadata", {})
        data = full_output.get("data", {})
        summary = data.get("summary", {})
        symbols = data.get("symbols", [])
        calls = data.get("calls", [])
        imports = data.get("imports", [])

        # Validate summary counts match actual data
        summary_validation = {
            "symbols_match": summary.get("total_symbols", 0) == len(symbols),
            "calls_match": summary.get("total_calls", 0) == len(calls),
            "imports_match": summary.get("total_imports", 0) == len(imports),
        }

        # Check metadata completeness
        required_metadata = [
            "tool_name", "tool_version", "run_id", "repo_id",
            "branch", "commit", "timestamp", "schema_version"
        ]
        metadata_completeness = {
            field: field in metadata
            for field in required_metadata
        }

        # Check path consistency (all paths repo-relative)
        path_issues = []
        for sym in symbols[:20]:  # Sample
            path = sym.get("path", "")
            if path.startswith("/") or path.startswith("./") or "\\" in path:
                path_issues.append(f"Symbol path not repo-relative: {path}")

        for call in calls[:20]:
            caller_file = call.get("caller_file", "")
            if caller_file.startswith("/") or caller_file.startswith("./"):
                path_issues.append(f"Call path not repo-relative: {caller_file}")

        evidence = {
            "metadata": metadata,
            "summary": summary,
            "summary_validation": summary_validation,
            "metadata_completeness": metadata_completeness,
            "path_issues": path_issues[:10],  # Limit
            "symbols_count": len(symbols),
            "calls_count": len(calls),
            "imports_count": len(imports),
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
        return """# Integration Quality Judge

## Task
Evaluate the overall integration quality and coherence of the symbol-scanner output.

## Evidence
{{ evidence }}

## Evaluation Criteria

### Data Consistency (40%)
- Summary counts match actual data
- Cross-file references valid
- No orphaned entries

### Metadata Quality (30%)
- All required fields present
- Values properly formatted
- Schema version correct

### Path Normalization (30%)
- All paths repo-relative
- Consistent separator usage
- No absolute paths

## Response Format
Respond with ONLY a JSON object with a BINARY PASS/FAIL decision:

{
  "dimension": "integration",
  "decision": "PASS" or "FAIL",
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "issues": [
    {"severity": "HIGH" or "MEDIUM" or "LOW", "type": "<issue_type>", "field": "<field_name>", "description": "<what's wrong>"}
  ],
  "recommendations": ["<improvement suggestions>"]
}

Decision rules:
- PASS: Data is consistent, metadata complete, paths normalized correctly
- FAIL: Summary/data mismatches, missing metadata, or path issues
"""


# Legacy function interface for backwards compatibility
JUDGE_NAME = "integration"
JUDGE_DESCRIPTION = "Evaluates overall integration quality"


def get_prompt(output: dict) -> str:
    """Generate the evaluation prompt for the LLM (legacy interface)."""
    summary = output.get("data", {}).get("summary", {})
    symbols_count = len(output.get("data", {}).get("symbols", []))
    calls_count = len(output.get("data", {}).get("calls", []))
    imports_count = len(output.get("data", {}).get("imports", []))

    return f"""Evaluate the integration quality of the symbol-scanner output.

## Summary Statistics
- Total symbols: {summary.get('total_symbols')} (actual: {symbols_count})
- Total calls: {summary.get('total_calls')} (actual: {calls_count})
- Total imports: {summary.get('total_imports')} (actual: {imports_count})

## Metadata
- Tool: {output.get('metadata', {}).get('tool_name')}
- Version: {output.get('metadata', {}).get('tool_version')}
- Schema: {output.get('metadata', {}).get('schema_version')}

## Task
1. Are summary statistics accurate?
2. Is the metadata complete?
3. Is the output structure correct?
4. Any data coherence issues?

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
