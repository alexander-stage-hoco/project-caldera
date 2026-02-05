# SoT Integration Evaluation

You are evaluating the integration quality of dotCover output with the Caldera SoT engine.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

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
