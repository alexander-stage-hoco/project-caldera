# Integration Readiness Evaluation

You are evaluating git-fame output readiness for integration with the Caldera SoT Engine.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Schema compliance is critical for data pipeline reliability
- Type correctness prevents runtime errors in DuckDB persistence
- Consistent format enables automated processing at scale

## Background

The Caldera SoT Engine requires:

### Caldera Envelope Format
Standard wrapper with metadata fields:
- `schema_version`: Semver format (e.g., "1.0.0")
- `generated_at`: ISO 8601 timestamp
- `repo_name`: Repository name string
- `repo_path`: Absolute path to repository
- `results`: Tool-specific analysis data

### Results Structure
Tool-specific data with required fields:
- `tool`: Tool identifier ("git-fame")
- `tool_version`: Tool version string
- `run_id`: Unique run identifier
- `summary`: Aggregate metrics object
- `authors`: Array of author objects

### Summary Metrics (for persistence)
Required aggregate metrics:
- `author_count`: Integer count of authors
- `total_loc`: Integer total lines of code
- `hhi_index`: Float concentration index (0-1)
- `bus_factor`: Integer bus factor value
- `top_author_pct`: Float top author percentage

## Task

Evaluate how well git-fame output conforms to SoT Engine integration requirements.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Schema Completeness (40%)
Are all required fields present?
- **5**: 100% of required fields present in all repos
- **4**: >95% field coverage across all repos
- **3**: 85-95% coverage with minor gaps
- **2**: 70-85% coverage with notable gaps
- **1**: <70% coverage - not ready for integration

### 2. Type Correctness (30%)
Are data types correct for DuckDB persistence?
- **5**: No type issues in any repo
- **4**: Minor type issues in <5% of repos
- **3**: Type issues in 5-15% of repos
- **2**: Type issues in 15-30% of repos
- **1**: Widespread type issues (>30%) - pipeline will fail

### 3. Format Consistency (30%)
Is output format consistent across all repos?
- **5**: All repos follow identical structure
- **4**: Minor structural variations (same data, different order)
- **3**: Some structural inconsistencies
- **2**: Significant inconsistencies requiring normalization
- **1**: Highly inconsistent - requires major preprocessing

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of integration readiness assessment>",
  "evidence_cited": [
    "<specific schema compliance findings>",
    "<type correctness observations>"
  ],
  "recommendations": [
    "<suggestions for improving schema compliance>",
    "<type handling improvements>"
  ],
  "sub_scores": {
    "schema_completeness": <1-5>,
    "type_correctness": <1-5>,
    "format_consistency": <1-5>
  }
}
