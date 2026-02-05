"""Integration Fit Judge - evaluates DD Platform integration compatibility (15% weight)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationFitJudge(BaseJudge):
    """Evaluates DD Platform integration compatibility of Roslyn Analyzers output.

    Assesses:
    - Schema compliance (output.schema.json)
    - DD Platform field mapping (L1/L6 lenses)
    - Aggregator compatibility (rollups and summaries)
    - Collector integration readiness

    Sub-scores:
    - schema_compliance (40%)
    - dd_platform_mapping (35%)
    - aggregator_compatibility (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "integration_fit"

    @property
    def weight(self) -> float:
        return 0.15  # 15%

    def get_default_prompt(self) -> str:
        return """# Integration Fit Evaluation

You are evaluating the DD Platform integration compatibility of Roslyn Analyzers static analysis output.

## Evidence to Review

### Metadata
{{ metadata }}

### Schema Version
{{ schema_version }}

### Output Structure
{{ output_structure }}

### Sample Violations
{{ violations_sample }}

### Summary Structure
{{ summary }}

### Rollup Completeness
{{ rollup_completeness }}

## DD Platform Requirements

1. **Schema Compatibility** - Output matches DD Platform expected schema
2. **Lens Mapping** - Data maps to L1 (Structural) and L6 (Quality) lenses
3. **Path Format** - File paths follow DD Platform conventions
4. **Violation Format** - Violations include file, line, rule_id, message, severity
5. **Collector Integration** - Output can be ingested by collector
6. **Rollup Data** - by_severity, by_category, by_rule rollups present

## Evaluation Criteria

### Score 5 (Excellent)
- Schema fully compatible with DD Platform
- Clear mapping to L1/L6 lenses
- Paths normalized to DD conventions
- Complete violation context (file, line, rule_id, message, severity, category)
- Ready for direct collector integration
- All rollup data complete (by_severity, by_category, by_rule)

### Score 4 (Good)
- Schema mostly compatible
- Mappable to DD lenses with minor transforms
- Paths in correct format
- Violations have required fields
- Minor schema adjustments needed
- Most rollups present

### Score 3 (Acceptable)
- Core schema compatible
- Some lens mapping required
- Most paths correct
- Basic violation data present
- Moderate integration work needed
- Basic rollups present

### Score 2 (Poor)
- Schema partially compatible
- Significant lens mapping work
- Inconsistent path formats
- Missing violation context
- Substantial integration effort
- Missing rollups

### Score 1 (Unacceptable)
- Schema incompatible
- Cannot map to DD lenses
- Incorrect path formats
- Incomplete violation data
- Major rework required
- No rollup data

## Response Format

Respond with JSON:
```json
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific findings>"],
    "recommendations": ["<improvements>"],
    "sub_scores": {
        "schema_compliance": <1-5>,
        "dd_platform_mapping": <1-5>,
        "aggregator_compatibility": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect integration fit data for evaluation."""
        evidence: dict[str, Any] = {
            "metadata": {},
            "schema_version": "",
            "output_structure": {},
            "violations_sample": [],
            "summary": {},
            "rollup_completeness": {
                "by_severity": False,
                "by_category": False,
                "by_rule": False,
                "by_file": False,
            },
        }

        # Load schema if available
        schema_path = self.working_dir / "schemas" / "output.schema.json"
        if schema_path.exists():
            try:
                schema = json.loads(schema_path.read_text())
                evidence["schema_version"] = schema.get("$id", schema.get("version", "unknown"))
            except json.JSONDecodeError:
                evidence["schema_version"] = "parse_error"

        # Load all analysis outputs
        all_results = self.load_all_analysis_results()

        combined_violations = []
        for repo_name, output in all_results.items():
            # Handle both flat and nested (results.X) structures
            results = self.unwrap_output(output)

            # Extract metadata
            metadata = {
                "schema_version": output.get("schema_version", ""),
                "generated_at": output.get("generated_at", ""),
                "repo_name": output.get("repo_name", ""),
            }
            if metadata.get("schema_version") or metadata.get("generated_at"):
                evidence["metadata"][repo_name] = metadata

            # Track output structure
            evidence["output_structure"][repo_name] = {
                key: type(value).__name__
                for key, value in output.items()
            }

            # Collect violations sample
            files = results.get("files", [])
            for file_data in files[:5]:
                for violation in file_data.get("violations", [])[:3]:
                    combined_violations.append({
                        "repo": repo_name,
                        "file": file_data.get("path", ""),
                        "line": violation.get("line_start", violation.get("line", 0)),
                        "rule_id": violation.get("rule_id", ""),
                        "message": violation.get("message", "")[:150],
                        "severity": violation.get("severity", ""),
                        "category": violation.get("category", ""),
                    })

            # Extract summary
            summary = results.get("summary", output.get("summary", {}))
            if summary:
                evidence["summary"][repo_name] = {
                    "total_files_analyzed": summary.get("total_files_analyzed", 0),
                    "total_violations": summary.get("total_violations", 0),
                    "files_with_violations": summary.get("files_with_violations", 0),
                    "has_severity_breakdown": "violations_by_severity" in summary,
                    "has_category_breakdown": "violations_by_category" in summary,
                    "has_rule_breakdown": "violations_by_rule" in summary,
                }

            # Check rollup completeness
            if "violations_by_severity" in summary:
                evidence["rollup_completeness"]["by_severity"] = True
            if "violations_by_category" in summary:
                evidence["rollup_completeness"]["by_category"] = True
            if "violations_by_rule" in summary:
                evidence["rollup_completeness"]["by_rule"] = True
            if files:
                evidence["rollup_completeness"]["by_file"] = True

        evidence["violations_sample"] = combined_violations[:15]

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify basic integration requirements."""
        failures = []

        all_results = self.load_all_analysis_results()

        if not all_results:
            failures.append("No analysis results found for integration validation")
            return False, failures

        for repo_name, output in all_results.items():
            # Handle both flat and nested (results.X) structures
            results = self.unwrap_output(output)

            # Check required top-level fields
            if "schema_version" not in output:
                failures.append(f"{repo_name}: Missing schema_version field")

            # Check required results fields
            required_fields = ["summary"]
            missing_fields = [
                f for f in required_fields
                if f not in output and f not in results
            ]

            if missing_fields:
                failures.append(
                    f"{repo_name}: Missing required fields: {missing_fields}"
                )

            # Check summary structure
            summary = results.get("summary", output.get("summary", {}))
            required_summary_fields = ["total_violations", "violations_by_severity", "violations_by_category"]
            missing_summary = [f for f in required_summary_fields if f not in summary]
            if missing_summary:
                failures.append(
                    f"{repo_name}: Summary missing fields: {missing_summary}"
                )

            # Check violation structure
            files = results.get("files", [])
            if files:
                for file_data in files[:3]:  # Check first 3 files
                    violations = file_data.get("violations", [])
                    if violations:
                        v = violations[0]
                        # Check for severity field (can be 'severity' or 'dd_severity')
                        has_severity = "severity" in v or "dd_severity" in v
                        required_violation_fields = ["rule_id", "message"]
                        missing_v_fields = [f for f in required_violation_fields if f not in v]

                        if not has_severity:
                            missing_v_fields.append("severity/dd_severity")

                        if missing_v_fields:
                            failures.append(
                                f"{repo_name}: Violations missing fields: {missing_v_fields}"
                            )
                            break

            # Check path format (should be relative or absolute)
            if files:
                file_path = files[0].get("path", "")
                if not file_path:
                    failures.append(f"{repo_name}: File entries missing path field")

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
