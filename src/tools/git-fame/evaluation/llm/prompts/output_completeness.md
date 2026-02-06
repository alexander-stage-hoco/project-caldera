# Output Completeness Evaluation

You are evaluating the overall completeness of git-fame analysis output.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Complete output enables full analysis capabilities
- Missing sections limit actionable insights
- Error-free execution indicates tool reliability

## Background

Complete git-fame output should include:

### Required Sections
- **Summary Section**: Aggregate metrics (author_count, total_loc, hhi_index, bus_factor, top_author_pct)
- **Authors Section**: Complete list of authors with individual metrics
- **Provenance Section**: Tool information and command used

### Author Data Quality
Each author record should have:
- `name`: Author identifier (required)
- `surviving_loc`: Lines of code attributed (required)
- `commit_count`: Number of commits (required)
- `ownership_pct`: Ownership percentage (required)
- `insertions_total`: Total insertions (optional)
- `deletions_total`: Total deletions (optional)
- `files_touched`: Files modified count (optional)

### Error Conditions
- No `error` field should be present in successful runs
- If errors occur, they should be clearly documented

## Task

Evaluate the completeness of git-fame output across all analyzed repositories.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Section Presence (25%)
Are all required sections present?
- **5**: All sections (summary, authors, provenance) present in all repos
- **4**: Minor sections missing in <5% of repos
- **3**: Some sections missing (5-15% of repos)
- **2**: Many sections missing (15-30% of repos)
- **1**: Critical sections missing (>30%)

### 2. Author Data Quality (40%)
Is author data complete and valid?
- **5**: All authors have all required fields, data is valid
- **4**: >95% of authors have complete, valid data
- **3**: 85-95% of authors have complete data
- **2**: 70-85% of authors have complete data
- **1**: <70% of authors have complete data

### 3. Summary Data Quality (25%)
Are summary metrics present and valid?
- **5**: All summary metrics present and valid in all repos
- **4**: >95% of summary metrics present
- **3**: 85-95% of summary metrics present
- **2**: 70-85% of summary metrics present
- **1**: <70% of summary metrics present

### 4. Error Rate (10%)
Are there analysis errors in the output?
- **5**: No errors in any repo
- **4**: Errors in <5% of repos (edge cases)
- **3**: Errors in 5-15% of repos
- **2**: Errors in 15-30% of repos
- **1**: Errors in >30% of repos - tool is unreliable

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of completeness assessment>",
  "evidence_cited": [
    "<section presence statistics>",
    "<author data completeness rates>"
  ],
  "recommendations": [
    "<suggestions for improving output completeness>",
    "<error handling improvements>"
  ],
  "sub_scores": {
    "section_presence": <1-5>,
    "author_data_quality": <1-5>,
    "summary_data_quality": <1-5>,
    "error_rate": <1-5>
  }
}
