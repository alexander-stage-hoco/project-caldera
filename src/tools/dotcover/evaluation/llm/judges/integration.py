"""Integration Judge for dotCover evaluation.

Evaluates SoT schema compatibility and data pipeline integration.
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationJudge(BaseJudge):
    """Evaluates SoT schema compatibility and integration quality.

    Assesses:
    - Caldera envelope format compliance
    - Entity schema alignment
    - dbt model compatibility
    - Cross-tool join readiness

    Sub-scores:
    - envelope_compliance (25%)
    - entity_alignment (25%)
    - dbt_compatibility (25%)
    - join_readiness (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "integration"

    @property
    def weight(self) -> float:
        return 0.20

    def get_default_prompt(self) -> str:
        return """# SoT Integration Evaluation

You are evaluating the integration quality of dotCover output with the Caldera SoT engine.

## Evaluation Context

{{ interpretation_guidance }}

### Evaluation Mode
{{ evaluation_mode }}

**Focus**: Is the output ready for persistence and cross-tool analysis?

## Evidence to Review

### Envelope Structure
{{ envelope_structure }}

### Metadata Completeness
{{ metadata_completeness }}

### Data Schema Sample
{{ data_schema_sample }}

### Entity Field Coverage
{{ entity_field_coverage }}

### Path Normalization
{{ path_normalization }}

## Evaluation Criteria

### Score 5 (Excellent)
- Full Caldera envelope compliance (metadata + data sections)
- All required metadata fields present and valid
- Schema matches entity definitions exactly
- All paths are repo-relative and normalized
- Ready for immediate persistence

### Score 4 (Good)
- Envelope structure correct
- Minor metadata issues (optional fields missing)
- Schema mostly aligned
- Paths generally correct

### Score 3 (Acceptable)
- Basic envelope structure present
- Some metadata gaps
- Schema requires minor transformation
- Some path normalization needed

### Score 2 (Poor)
- Incomplete envelope structure
- Missing required metadata
- Schema misalignment requiring major transformation
- Path format issues

### Score 1 (Unacceptable)
- No envelope structure
- Critical metadata missing
- Incompatible schema
- Paths absolute or malformed

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
        "envelope_compliance": <1-5>,
        "entity_alignment": <1-5>,
        "dbt_compatibility": <1-5>,
        "join_readiness": <1-5>
    }
}
```
"""

    # Required metadata fields per Caldera spec
    REQUIRED_METADATA_FIELDS = [
        "tool_name",
        "tool_version",
        "run_id",
        "repo_id",
        "branch",
        "commit",
        "timestamp",
        "schema_version",
    ]

    # Expected data structure fields
    EXPECTED_DATA_FIELDS = [
        "tool",
        "tool_version",
        "summary",
        "assemblies",
        "types",
        "methods",
    ]

    def collect_evidence(self) -> dict[str, Any]:
        """Collect integration-related evidence from analysis outputs."""
        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "envelope_structure": {},
            "metadata_completeness": {},
            "data_schema_sample": {},
            "entity_field_coverage": {},
            "path_normalization": {},
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()

        for run_id, output in all_results.items():
            # Check envelope structure
            has_metadata = "metadata" in output
            has_data = "data" in output
            evidence["envelope_structure"][run_id] = {
                "has_metadata": has_metadata,
                "has_data": has_data,
                "is_valid_envelope": has_metadata and has_data,
                "top_level_keys": list(output.keys())[:10],
            }

            # Check metadata completeness
            metadata = output.get("metadata", {})
            missing_fields = []
            for field in self.REQUIRED_METADATA_FIELDS:
                if field not in metadata or metadata[field] is None:
                    missing_fields.append(field)

            evidence["metadata_completeness"][run_id] = {
                "fields_present": [f for f in self.REQUIRED_METADATA_FIELDS if f in metadata],
                "fields_missing": missing_fields,
                "completeness_pct": ((len(self.REQUIRED_METADATA_FIELDS) - len(missing_fields)) /
                                    len(self.REQUIRED_METADATA_FIELDS)) * 100,
            }

            # Check data schema
            data = output.get("data", output)
            missing_data_fields = []
            for field in self.EXPECTED_DATA_FIELDS:
                if field not in data:
                    missing_data_fields.append(field)

            evidence["data_schema_sample"][run_id] = {
                "fields_present": [f for f in self.EXPECTED_DATA_FIELDS if f in data],
                "fields_missing": missing_data_fields,
                "assembly_count": len(data.get("assemblies", [])),
                "type_count": len(data.get("types", [])),
                "method_count": len(data.get("methods", [])),
            }

            # Check entity field coverage
            entity_issues = []

            # Assembly coverage entity check
            for asm in data.get("assemblies", [])[:3]:
                required = ["name", "covered_statements", "total_statements", "statement_coverage_pct"]
                missing = [f for f in required if f not in asm]
                if missing:
                    entity_issues.append(f"Assembly missing: {missing}")

            # Type coverage entity check
            for t in data.get("types", [])[:3]:
                required = ["assembly", "name", "covered_statements", "total_statements", "statement_coverage_pct"]
                missing = [f for f in required if f not in t]
                if missing:
                    entity_issues.append(f"Type missing: {missing}")

            # Method coverage entity check
            for m in data.get("methods", [])[:3]:
                required = ["assembly", "type_name", "name", "covered_statements", "total_statements", "statement_coverage_pct"]
                missing = [f for f in required if f not in m]
                if missing:
                    entity_issues.append(f"Method missing: {missing}")

            evidence["entity_field_coverage"][run_id] = {
                "issues": entity_issues[:10],
                "has_issues": len(entity_issues) > 0,
            }

            # Check path normalization
            path_issues = []
            for t in data.get("types", []):
                file_path = t.get("file_path")
                if file_path:
                    if file_path.startswith("/"):
                        path_issues.append(f"Absolute path: {file_path[:50]}")
                    if file_path.startswith("./"):
                        path_issues.append(f"Relative dot path: {file_path[:50]}")
                    if "\\" in file_path:
                        path_issues.append(f"Windows separator: {file_path[:50]}")

            evidence["path_normalization"][run_id] = {
                "issues": path_issues[:10],
                "has_issues": len(path_issues) > 0,
            }

        # Add interpretation guidance
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["interpretation_guidance"] = "Evaluate based on schema compliance"
        else:
            evidence["interpretation_guidance"] = "Strict schema validation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Check integration-related ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()

        for run_id, output in all_results.items():
            # Check envelope structure
            if "metadata" not in output:
                failures.append(f"{run_id}: Missing 'metadata' section in envelope")
            if "data" not in output:
                failures.append(f"{run_id}: Missing 'data' section in envelope")

            # Check required metadata
            metadata = output.get("metadata", {})
            for field in self.REQUIRED_METADATA_FIELDS:
                if field not in metadata or metadata[field] is None:
                    failures.append(f"{run_id}: Missing required metadata field: {field}")

            # Check data structure
            data = output.get("data", output)

            # Verify coverage data lists exist
            if "assemblies" not in data:
                failures.append(f"{run_id}: Missing 'assemblies' in data")
            if "types" not in data:
                failures.append(f"{run_id}: Missing 'types' in data")
            if "methods" not in data:
                failures.append(f"{run_id}: Missing 'methods' in data")

            # Check path normalization
            for t in data.get("types", []):
                file_path = t.get("file_path")
                if file_path and file_path.startswith("/"):
                    failures.append(f"{run_id}: Absolute path found: {file_path[:50]}")
                    break  # One failure is enough

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
