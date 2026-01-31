"""Actionability Judge - Evaluates clarity and usefulness of smell reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ActionabilityJudge(BaseJudge):
    """Evaluates actionability of smell detection reports.

    Validates that:
    - Messages are clear and understandable
    - Fix suggestions are provided where appropriate
    - Severity helps prioritization
    - Location information is precise
    """

    @property
    def dimension_name(self) -> str:
        return "actionability"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess message quality."""
        # Load from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate files from all repos
        all_files = []
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                file_info["_repo"] = repo_name
                all_files.append(file_info)
        analysis = {"files": all_files}

        # Sample messages for quality assessment
        sample_messages = []
        for file_info in analysis.get("files", []):
            file_name = Path(file_info.get("path", "")).name
            for smell in file_info.get("smells", [])[:3]:  # Max 3 per file
                msg = smell.get("message", "")
                sample_messages.append({
                    "file": file_name,
                    "rule_id": smell.get("rule_id", ""),
                    "dd_category": smell.get("dd_category", ""),
                    "severity": smell.get("severity", ""),
                    "line_start": smell.get("line_start", 0),
                    "line_end": smell.get("line_end", 0),
                    "message": msg[:300],
                    "has_fix_suggestion": any([
                        "use " in msg.lower(),
                        "instead" in msg.lower(),
                        "should" in msg.lower(),
                        "consider" in msg.lower(),
                        "replace" in msg.lower(),
                    ]),
                    "message_length": len(msg),
                })

        # Analyze message quality metrics
        total_messages = len(sample_messages)
        with_fix_suggestion = sum(1 for m in sample_messages if m["has_fix_suggestion"])
        avg_message_length = sum(m["message_length"] for m in sample_messages) / max(total_messages, 1)

        # Severity usage
        severity_usage = {}
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                sev = smell.get("severity", "UNKNOWN")
                severity_usage[sev] = severity_usage.get(sev, 0) + 1

        # Location precision assessment
        location_quality = []
        for msg in sample_messages[:15]:
            has_line = msg["line_start"] > 0
            has_range = msg["line_end"] > msg["line_start"]
            location_quality.append({
                "file": msg["file"],
                "has_line": has_line,
                "has_range": has_range,
                "range_size": msg["line_end"] - msg["line_start"] if has_range else 0,
            })

        # Calculate scores
        fix_suggestion_rate = with_fix_suggestion / max(total_messages, 1) * 100
        has_line_rate = sum(1 for l in location_quality if l["has_line"]) / max(len(location_quality), 1) * 100

        summary = analysis.get("summary", {})

        return {
            "sample_messages": sample_messages[:20],
            "total_messages_sampled": total_messages,
            "with_fix_suggestion": with_fix_suggestion,
            "fix_suggestion_rate": fix_suggestion_rate,
            "avg_message_length": round(avg_message_length, 0),
            "severity_usage": severity_usage,
            "location_quality": location_quality,
            "has_line_rate": has_line_rate,
            "total_smells": summary.get("total_smells", 0),
            "total_files": summary.get("total_files", 0),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate actionability requirements."""
        failures = []

        # Load from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            failures.append(f"No analysis files found in {self.output_dir}")
            return False, failures

        # Aggregate files from all repos
        all_files = []
        for repo_name, repo_analysis in all_results.items():
            for file_info in self.extract_files(repo_analysis):
                all_files.append(file_info)
        analysis = {"files": all_files}

        # Check all smells have messages
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                if not smell.get("message"):
                    failures.append(
                        f"Smell {smell.get('rule_id')} in {file_info.get('path')} has no message"
                    )

        # Check all smells have severity
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                if not smell.get("severity"):
                    failures.append(
                        f"Smell {smell.get('rule_id')} in {file_info.get('path')} has no severity"
                    )

        # Check all smells have line numbers
        for file_info in analysis.get("files", []):
            for smell in file_info.get("smells", []):
                if not smell.get("line_start"):
                    failures.append(
                        f"Smell {smell.get('rule_id')} in {file_info.get('path')} has no line number"
                    )

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Actionability Judge

You are evaluating the **actionability** of Semgrep's code smell detection reports.

## Evaluation Dimension
**Actionability (20% weight)**: Can developers easily understand and fix the detected issues?

## Background
Actionable smell detection should:
- Provide clear, understandable messages
- Include fix suggestions where possible
- Use severity to help prioritization
- Give precise locations (file, line, range)

Good messages:
- "Use 'using' statement for IDisposable resources to ensure proper cleanup"
- "Empty catch block swallows exception - add logging or specific handling"

Bad messages:
- "Issue detected"
- "Problem at line 42"

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Clear messages, fix suggestions, precise locations, useful severity |
| 4 | Good messages, some fix suggestions, accurate locations |
| 3 | Adequate messages, few fix suggestions |
| 2 | Vague messages, no fix suggestions, imprecise locations |
| 1 | Unclear/unhelpful messages, missing critical info |

## Sub-Dimensions
1. **Message Clarity (40%)**: Messages explain the issue clearly
2. **Fix Suggestions (30%)**: Actionable remediation advice provided
3. **Location Precision (30%)**: Exact file, line, and range specified

## Evidence to Evaluate

### Sample Messages
```json
{{ sample_messages }}
```

### Message Quality Metrics
- Total messages sampled: {{ total_messages_sampled }}
- With fix suggestion: {{ with_fix_suggestion }}
- Fix suggestion rate: {{ fix_suggestion_rate }}%
- Average message length: {{ avg_message_length }} chars

### Severity Usage
```json
{{ severity_usage }}
```

### Location Quality
```json
{{ location_quality }}
```
- Has line number rate: {{ has_line_rate }}%

### Overall Statistics
- Total smells: {{ total_smells }}
- Total files: {{ total_files }}

## Evaluation Questions
1. Are messages clear and explain WHY something is a problem?
2. Do messages include actionable fix suggestions?
3. Is severity used effectively for prioritization?
4. Are locations precise (line numbers, ranges)?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "actionability",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of actionability assessment",
  "evidence_cited": ["specific messages and patterns examined"],
  "recommendations": ["improvements for actionability"],
  "sub_scores": {
    "message_clarity": <1-5>,
    "fix_suggestions": <1-5>,
    "location_precision": <1-5>
  }
}
```
'''
    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
