# Evidence Quality Evaluation

You are evaluating the quality and completeness of evidence in git-fame output.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Evidence quality matters for actionable insights
- Complete data enables better decision-making
- Provenance enables reproducibility and auditing

## Background

Good evidence quality in authorship analysis means:
- **Required Metrics**: name, surviving_loc, commit_count, ownership_pct
- **Optional Metrics**: insertions_total, deletions_total, files_touched
- **Provenance**: Tool name, version, and command used
- **Consistency**: Data is non-contradictory and validates correctly

## Task

Evaluate the completeness and quality of evidence in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Required Field Coverage (40%)
Are required fields present for all authors?
- **5**: 100% of authors have all required fields (name, loc, commits, ownership)
- **4**: >95% of authors have all required fields
- **3**: 85-95% coverage of required fields
- **2**: 70-85% coverage
- **1**: <70% coverage - critical data missing

### 2. Optional Field Coverage (30%)
Are optional metrics available for deeper analysis?
- **5**: >90% of authors have all optional fields (insertions, deletions, files)
- **4**: 70-90% coverage of optional fields
- **3**: 50-70% coverage
- **2**: 30-50% coverage
- **1**: <30% coverage - limited actionable detail

### 3. Provenance Quality (30%)
Is provenance properly tracked for reproducibility?
- **5**: All repos have complete provenance (tool, command, version)
- **4**: Most repos have provenance (>90%)
- **3**: Some repos have provenance (70-90%)
- **2**: Few repos have provenance (50-70%)
- **1**: Provenance rarely present (<50%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of evidence quality assessment>",
  "evidence_cited": [
    "<specific field coverage statistics>",
    "<provenance presence data>"
  ],
  "recommendations": [
    "<suggestions for improving data completeness>",
    "<provenance tracking improvements>"
  ],
  "sub_scores": {
    "required_field_coverage": <1-5>,
    "optional_field_coverage": <1-5>,
    "provenance_quality": <1-5>
  }
}
