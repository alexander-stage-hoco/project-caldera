# Evaluation Strategy: git-blame-scanner

This document describes the evaluation methodology for the git-blame-scanner tool, which analyzes git blame data to compute per-file authorship, ownership concentration, knowledge silo detection, and churn metrics.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation to cover both objective data integrity and subjective quality dimensions:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 17 checks | Objective, reproducible, fast: validates invariants, bounds, schema compliance |
| LLM Judges | 4 judges | Semantic understanding: ownership accuracy, churn validity, actionability, integration |

**Why a hybrid approach?**

git-blame-scanner produces structured authorship and churn data where many correctness properties are verifiable through deterministic checks (e.g., ownership percentages must be 0-100%, churn_30d must not exceed churn_90d). However, higher-order quality dimensions -- such as whether findings are actionable for engineering managers or whether ownership calculations faithfully reflect git history -- require the nuanced judgment that LLM evaluation provides.

The programmatic layer acts as a fast, reliable gate: if any check fails, the overall programmatic decision is FAIL regardless of LLM scores. The LLM layer adds depth by evaluating evidence bundles that include file samples, repo summaries, ground truth comparisons, and validation results.

**Key design decisions:**

- Programmatic checks use binary pass/fail/warn status, not 1-5 scales, to avoid ambiguity
- LLM judges use 1-5 scoring with explicit sub-dimension rubrics and confidence levels
- Ground truth assertions in each LLM judge run before the LLM call; if assertions fail, the LLM score is constrained
- Each judge collects its own evidence bundle, providing transparency into what the LLM evaluated
- Synthetic evaluation repos with known ownership patterns serve as controlled ground truth

---

## Dimension Summary

### Programmatic Dimensions

Programmatic checks are grouped into three modules. Each check returns a status of `pass`, `fail`, `warn`, or `error`. The overall programmatic score is the ratio of passed checks to total checks.

| Module | Check Count | Focus Area |
|--------|-------------|------------|
| Accuracy | 6 | Ownership bounds, author counts, churn invariants, cross-field consistency |
| Coverage | 6 | Output completeness: files present, authors present, summary fields, knowledge silos |
| Performance | 5 | Metadata integrity, path normalization, file/author count reasonableness |
| **Total** | **17** | |

### LLM Judge Dimensions

| Judge | Weight | Focus Area |
|-------|--------|------------|
| Ownership Accuracy | 30% | Ownership percentage correctness, author counts, concentration detection |
| Churn Validity | 25% | Churn metric consistency, value validity, temporal coherence |
| Actionability | 25% | Knowledge silo identification, risk prioritization, action enablement |
| Integration | 20% | Schema compliance, field completeness, data quality for SoT pipeline |
| **Total** | **100%** | |

### Combined Weight Table

| Dimension | Programmatic Checks | LLM Judge Weight | Combined Purpose |
|-----------|---------------------|------------------|------------------|
| Accuracy / Ownership | 6 checks (accuracy module) | 30% (Ownership Accuracy) | Data correctness |
| Churn Validity | 1 check (churn_monotonicity) | 25% (Churn Validity) | Temporal metric integrity |
| Coverage / Completeness | 6 checks (coverage module) | -- | Output completeness |
| Actionability | -- | 25% (Actionability) | Usefulness of findings |
| Integration / Schema | 5 checks (performance module) | 20% (Integration) | SoT pipeline readiness |

---

## Check Catalog

### Accuracy Checks (6 checks)

Located in `scripts/checks/accuracy.py`. These checks validate the mathematical correctness and internal consistency of ownership and authorship data.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| `accuracy.ownership_bounds` | Ownership percentage bounds | Critical | All files have `top_author_pct` in range [0, 100] | Count of files checked; list of violating file paths and percentages |
| `accuracy.unique_authors_positive` | Unique authors positive | Critical | All files have `unique_authors >= 1` | Count of files checked; list of violating file paths and counts |
| `accuracy.churn_monotonicity` | Churn window monotonicity | Critical | All files satisfy `churn_30d <= churn_90d` | Count of files checked; list of violating file paths with 30d/90d values |
| `accuracy.exclusive_files_bound` | Exclusive files bound | High | All authors satisfy `exclusive_files <= total_files` | Count of authors checked; list of violating author emails with exclusive/total counts |
| `accuracy.single_author_consistency` | Single-author count consistency | High | Count of files with `unique_authors == 1` matches `summary.single_author_files` | Actual counted value vs. reported summary value |
| `accuracy.high_concentration_consistency` | High-concentration count consistency | High | Count of files with `top_author_pct >= 80` matches `summary.high_concentration_files` | Actual counted value vs. reported summary value |

#### Accuracy Check Detail

**ownership_bounds**: Iterates all files in `data.files`, verifying each `top_author_pct` is between 0 and 100 inclusive. Any value outside this range indicates a calculation error in the blame analysis. Reports up to 5 violating paths on failure.

**unique_authors_positive**: Every file in a git repository must have at least one author. A value of 0 indicates the blame analysis failed to attribute any lines, which would break downstream knowledge risk calculations.

**churn_monotonicity**: The 30-day churn window is a strict subset of the 90-day window. Therefore `churn_30d > churn_90d` is a logical impossibility that indicates a bug in the churn calculation. Reports violating paths with both values.

**exclusive_files_bound**: An author's exclusive files (files where they are the sole contributor) cannot exceed their total file count. This cross-validates the author-level aggregation logic.

**single_author_consistency**: Cross-validates the summary-level `single_author_files` count against the actual count derived from file-level `unique_authors` data. Detects aggregation bugs.

**high_concentration_consistency**: Cross-validates the summary-level `high_concentration_files` count (files with >= 80% ownership by a single author) against the count derived from file-level data. Detects threshold or aggregation bugs.

---

### Coverage Checks (6 checks)

Located in `scripts/checks/coverage.py`. These checks validate that the output contains all expected structural components with required fields.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| `coverage.has_files` | Files array present | Critical | `data.files` contains at least one file | Count of files found |
| `coverage.has_authors` | Authors array present | Critical | `data.authors` contains at least one author | Count of authors found |
| `coverage.has_summary` | Summary fields complete | Critical | Summary contains all 6 required fields: `total_files_analyzed`, `total_authors`, `single_author_files`, `single_author_pct`, `high_concentration_files`, `high_concentration_pct` | List of missing field names |
| `coverage.file_fields_complete` | File record completeness | High | All files contain required fields: `path`, `total_lines`, `unique_authors`, `top_author`, `top_author_pct`, `last_modified`, `churn_30d`, `churn_90d` | Count of incomplete files; first 3 violations with missing field names |
| `coverage.author_fields_complete` | Author record completeness | High | All authors contain required fields: `author_email`, `total_files`, `total_lines`, `exclusive_files`, `avg_ownership_pct` | Count of incomplete authors; first 3 violations with missing field names |
| `coverage.knowledge_silos_identified` | Knowledge silo detection | Medium | Knowledge silo count in summary matches count of files where `unique_authors == 1` AND `total_lines > 100` | Expected count vs. reported count; status is `warn` (not `fail`) on mismatch |

#### Coverage Check Detail

**has_files / has_authors**: These are fundamental structural checks. An output with no files or no authors indicates a complete analysis failure, not a partial result.

**has_summary**: The summary section is consumed by downstream reports and the SoT pipeline. The 6 required fields represent the minimum viable summary for knowledge risk reporting.

**file_fields_complete / author_fields_complete**: These checks validate record-level completeness. The required fields represent the contract between git-blame-scanner and the SoT adapter. Missing fields would cause adapter ingestion failures.

**knowledge_silos_identified**: Knowledge silos are defined as single-author files with more than 100 lines of code. This threshold distinguishes trivially small files (config, init) from substantive code that represents real knowledge risk. This check uses `warn` status rather than `fail` because the silo definition may evolve.

---

### Performance Checks (5 checks)

Located in `scripts/checks/performance.py`. These checks validate metadata integrity, output sanity, and path normalization rather than runtime performance.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| `performance.reasonable_file_count` | File count sanity | High | `total_files_analyzed > 0` and `<= 100,000` | Actual file count; status is `warn` if count exceeds 100,000 |
| `performance.author_count_reasonable` | Author-to-file ratio | Medium | At least 1 author found; ratio of authors to files is computed | Author-to-file ratio value |
| `performance.metadata_complete` | Metadata fields complete | Critical | Metadata contains all 8 required fields: `tool_name`, `tool_version`, `run_id`, `repo_id`, `branch`, `commit`, `timestamp`, `schema_version` | List of missing field names |
| `performance.commit_sha_valid` | Commit SHA format | Low | Commit string is exactly 40 hex characters | Truncated SHA value; status is `warn` (not `fail`) on invalid format |
| `performance.paths_normalized` | Path normalization | Critical | All file paths are repo-relative: no leading `/`, no `./` prefix, no `..` segments, no backslashes | Count of files checked; first 3 violations with path and issue type |

#### Performance Check Detail

**reasonable_file_count**: A zero file count means analysis produced nothing. An extremely large count (>100K) may indicate the tool is scanning non-source files or failing to apply exclusion filters. The warn threshold at 100K is deliberately generous.

**author_count_reasonable**: The ratio of authors to files provides a sanity check. Zero authors is always a failure. A ratio > 1 (more authors than files) is possible in collaborative repositories and passes with a note.

**metadata_complete**: The 8 metadata fields match the Caldera envelope specification. Missing metadata fields prevent the SoT pipeline from creating valid collection and tool run records.

**commit_sha_valid**: Validates the 40-character lowercase hex format of git commit SHAs. Uses `warn` rather than `fail` because the all-zeros fallback SHA (`0000...`) is valid for non-git contexts.

**paths_normalized**: Enforces the Caldera path normalization contract: all file paths must be repo-relative with POSIX separators. This is critical because absolute paths, `./` prefixes, `..` segments, or Windows backslashes would break path matching in the SoT data warehouse.

---

## Scoring Methodology

### Programmatic Score Calculation

The programmatic evaluator computes a simple ratio-based score:

```python
def compute_summary(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") == "fail")
    warned = sum(1 for r in results if r.get("status") == "warn")
    errored = sum(1 for r in results if r.get("status") == "error")

    score = passed / total if total > 0 else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "errored": errored,
        "score": round(score, 4),
        "decision": "PASS" if failed == 0 and errored == 0 else "FAIL",
    }
```

Key properties of this scoring:

- **Score range**: 0.0 to 1.0 (ratio of passed checks to total)
- **Decision logic**: Binary PASS/FAIL. The decision is PASS only when there are zero failed checks AND zero errored checks. Warned checks do not trigger a FAIL.
- **No severity weighting**: All checks contribute equally to the score. Critical, high, medium, and low severities are informational (for prioritizing fixes), not weighted.

### LLM Judge Score Calculation

Each LLM judge produces a score on a 1-5 scale. The orchestrator computes a weighted average:

```python
# From evaluation/llm/orchestrator.py
JUDGES = {
    "ownership_accuracy": (OwnershipAccuracyJudge, 0.30),
    "churn_validity":     (ChurnValidityJudge,     0.25),
    "actionability":      (ActionabilityJudge,      0.25),
    "integration":        (IntegrationJudge,        0.20),
}

# Weighted average calculation
total_weighted_score = 0.0
total_weight = 0.0

for name, (judge_class, weight) in judge_classes.items():
    result = judge.evaluate()
    total_weighted_score += result.score * weight
    total_weight += weight

final_score = total_weighted_score / total_weight  # 1-5 scale
```

The final LLM score remains on a 1-5 scale. A normalized 0-1 score is also computed as `final_score / 5.0`.

### Letter Grade Mapping

The orchestrator maps the weighted LLM score to a letter grade:

| Score Range | Grade |
|-------------|-------|
| >= 4.5 | A |
| >= 4.0 | A- |
| >= 3.5 | B+ |
| >= 3.0 | B |
| >= 2.5 | B- |
| >= 2.0 | C |
| >= 1.5 | D |
| < 1.5 | F |

---

## Decision Thresholds

### LLM Verdict Thresholds

The LLM orchestrator assigns a verdict based on the weighted score (1-5 scale):

| Verdict | Weighted Score | Interpretation |
|---------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent, production-ready output |
| PASS | >= 3.5 | Good, minor improvements possible |
| WEAK_PASS | >= 3.0 | Acceptable with caveats noted |
| FAIL | < 3.0 | Significant issues requiring attention |

### Programmatic Decision

The programmatic evaluator uses a strict binary decision:

| Decision | Condition | Interpretation |
|----------|-----------|----------------|
| PASS | 0 failed checks AND 0 errored checks | All invariants and requirements satisfied |
| FAIL | Any failed or errored check | At least one requirement violated |

Warned checks do not affect the decision. They indicate conditions that are unusual but not definitively wrong (e.g., an all-zeros commit SHA, a very large file count, or a knowledge silo count mismatch).

### Ground Truth Assertion Gating

Each LLM judge runs ground truth assertions before invoking the LLM. If assertions fail:

- The assertion failures are recorded in the judge result
- The LLM evaluation still runs, but the result is annotated with `assertions_passed: false`
- Downstream consumers can use assertion status to cap or discount the LLM score

```python
# From orchestrator.py - assertion flow
assertions_passed, failures = judge.run_ground_truth_assertions()
result = judge.evaluate()

results["judges"][name] = {
    "score": result.score,
    "assertions_passed": assertions_passed,
    "assertion_failures": failures if not assertions_passed else [],
    ...
}
```

---

## LLM Judge Details

### Ownership Accuracy Judge (30% weight)

**Module**: `evaluation/llm/judges/ownership_accuracy.py`
**Prompt template**: `evaluation/llm/prompts/ownership_accuracy.md`

Evaluates the correctness of per-file ownership percentage calculations. This is the highest-weighted judge because ownership data drives downstream knowledge risk analysis, bus factor calculations, and resource allocation recommendations.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Ownership Bounds | 40% | Are percentages within 0-100% and summing correctly? |
| Author Count Accuracy | 35% | Do `unique_authors` counts match actual contributor counts? |
| Concentration Detection | 25% | Are high-concentration files (>= 80%) correctly identified? |

**Scoring Rubric - Ownership Bounds (40%)**:

| Score | Criteria |
|-------|----------|
| 5 | All percentages between 0-100% |
| 4 | Minor edge case issues (<1% of files) |
| 3 | Some boundary violations (1-5% of files) |
| 2 | Multiple violations (5-15% of files) |
| 1 | Major data integrity issues (>15% of files) |

**Scoring Rubric - Author Count Accuracy (35%)**:

| Score | Criteria |
|-------|----------|
| 5 | All counts match expected values |
| 4 | Minor discrepancies (<5% of files) |
| 3 | Some issues (5-15% of files) |
| 2 | Significant issues (15-30% of files) |
| 1 | Major inaccuracies (>30% of files) |

**Scoring Rubric - Concentration Detection (25%)**:

| Score | Criteria |
|-------|----------|
| 5 | All high-concentration files correctly identified |
| 4 | Most identified (>95%) |
| 3 | Majority identified (85-95%) |
| 2 | Some missed (70-85%) |
| 1 | Many missed (<70%) |

**Evidence collected**: Sample of up to 20 files sorted by top_author_pct (descending), per-repo summaries with file counts and single-author counts, ownership validation results, ground truth comparisons when available, synthetic baseline context.

**Ground truth assertions**: Validates ownership percentages are in bounds for all repos; checks expected file counts match actual counts.

---

### Churn Validity Judge (25% weight)

**Module**: `evaluation/llm/judges/churn_validity.py`
**Prompt template**: Inline in judge class `get_default_prompt()`

Evaluates the validity and consistency of churn metrics (churn_30d, churn_90d). Churn metrics indicate how actively a file is being modified, which is essential for identifying stale code and active hotspots.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Metric Consistency | 40% | Is `churn_30d <= churn_90d` for all files? |
| Value Validity | 30% | Are churn values non-negative and reasonable? |
| Temporal Coherence | 30% | Does churn correlate with `last_modified` dates? |

**Scoring Rubric - Metric Consistency (40%)**:

| Score | Criteria |
|-------|----------|
| 5 | All files satisfy the `churn_30d <= churn_90d` invariant |
| 4 | Minor violations (<1% of files) |
| 3 | Some violations (1-5% of files) |
| 2 | Significant violations (5-15% of files) |
| 1 | Major data integrity issues (>15% of files) |

**Scoring Rubric - Value Validity (30%)**:

| Score | Criteria |
|-------|----------|
| 5 | All values valid and reasonable |
| 4 | Minor edge cases (<1%) |
| 3 | Some issues (1-5%) |
| 2 | Multiple issues (5-15%) |
| 1 | Major validity issues (>15%) |

**Scoring Rubric - Temporal Coherence (30%)**:

| Score | Criteria |
|-------|----------|
| 5 | Perfect correlation (stale files have 0 churn, active files have > 0) |
| 4 | High correlation (>95%) |
| 3 | Moderate correlation (85-95%) |
| 2 | Low correlation (70-85%) |
| 1 | Poor correlation (<70%) |

**Evidence collected**: Total file counts, active file counts at 30d/90d windows, stale file count, sample of up to 15 high-churn files, per-repo summaries with churn totals, validation issues, ground truth comparisons when available.

**Ground truth assertions**: Validates churn metric consistency (`churn_30d <= churn_90d`, non-negative values) for all repos using the `validate_churn_metrics()` utility.

---

### Actionability Judge (25% weight)

**Module**: `evaluation/llm/judges/actionability.py`
**Prompt template**: `evaluation/llm/prompts/actionability.md`

Evaluates whether the git-blame-scanner output provides actionable insights for reducing knowledge risk and improving team collaboration. This judge assesses the practical utility of findings for engineering managers and team leads.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Knowledge Silo Identification | 35% | Are knowledge silos clearly identified with file paths, authors, and line counts? |
| Risk Prioritization | 35% | Are high-risk files surfaced with appropriate priority ordering? |
| Action Enablement | 30% | Can findings drive concrete actions (pairing, reviews, documentation)? |

**Scoring Rubric - Knowledge Silo Identification (35%)**:

| Score | Criteria |
|-------|----------|
| 5 | All silos identified with file paths, authors, and line counts |
| 4 | Most silos identified with key details |
| 3 | Silos identified but missing some context |
| 2 | Partial identification, missing key details |
| 1 | Silos not effectively identified |

**Scoring Rubric - Risk Prioritization (35%)**:

| Score | Criteria |
|-------|----------|
| 5 | Clear prioritization by risk (size, concentration, staleness) |
| 4 | Good prioritization with minor gaps |
| 3 | Moderate prioritization |
| 2 | Weak prioritization |
| 1 | No effective prioritization |

**Scoring Rubric - Action Enablement (30%)**:

| Score | Criteria |
|-------|----------|
| 5 | Findings directly enable actions (pairing, reviews, documentation) |
| 4 | Most findings are actionable |
| 3 | Some actionable findings |
| 2 | Limited actionability |
| 1 | Findings not actionable |

**Evidence collected**: Knowledge silo samples (up to 15, sorted by total_lines descending), high-concentration file samples (up to 15, sorted by top_author_pct descending), stale file samples (up to 10), per-repo risk metric summaries, total counts for each risk category.

**Heuristic fallback**: When running without an LLM (`use_llm=False`), a heuristic evaluator scores based on: whether knowledge silos have required detail fields (+1), whether high concentration files are identified (+0.5), and whether repo summaries contain risk metrics (+0.5). Base score is 3, maximum is 5. Confidence is 0.7 for heuristic evaluations.

---

### Integration Judge (20% weight)

**Module**: `evaluation/llm/judges/integration.py`
**Prompt template**: Inline in judge class `get_default_prompt()`

Evaluates schema compliance and readiness for ingestion by the Source-of-Truth (SoT) pipeline. This judge validates that the output can be consumed by the persistence adapter without errors.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Schema Compliance | 40% | Does output match the expected schema with correct types? |
| Field Completeness | 30% | Are all required fields present in all records? |
| Data Quality | 30% | Are values well-formed and consistent? |

**Scoring Rubric - Schema Compliance (40%)**:

| Score | Criteria |
|-------|----------|
| 5 | All records conform to schema with correct types |
| 4 | Minor issues (<5% of records) |
| 3 | Some issues (5-15% of records) |
| 2 | Significant issues (15-30% of records) |
| 1 | Major schema violations (>30% of records) |

**Scoring Rubric - Field Completeness (30%)**:

| Score | Criteria |
|-------|----------|
| 5 | All required fields present in all records |
| 4 | Minor missing fields (<5%) |
| 3 | Some missing fields (5-15%) |
| 2 | Many missing fields (15-30%) |
| 1 | Critical fields missing (>30%) |

**Scoring Rubric - Data Quality (30%)**:

| Score | Criteria |
|-------|----------|
| 5 | All values properly typed and consistent |
| 4 | Minor type/consistency issues |
| 3 | Some issues |
| 2 | Significant issues |
| 1 | Major data quality problems |

**Validation logic**: The Integration Judge performs structural validation of individual records:

- **File records** must contain: `path`, `total_lines`, `unique_authors`, `top_author`, `top_author_pct`, `last_modified`, `churn_30d`, `churn_90d`
- **Author records** must contain: `author_email`, `total_files`, `total_lines`, `exclusive_files`, `avg_ownership_pct`
- **Type checks**: `total_lines`, `unique_authors`, `churn_30d`, `churn_90d`, `total_files`, `exclusive_files` must be integers; `top_author_pct`, `avg_ownership_pct` must be numeric

**Evidence collected**: File validation rate, author validation rate, sampled file issues (up to 10), sampled author issues (up to 10), envelope issues, schema availability status.

**Heuristic fallback**: Computes average of file and author validation rates, penalizes 10% per envelope issue. Maps to 1-5 scale: >= 95% = 5, >= 85% = 4, >= 70% = 3, >= 50% = 2, < 50% = 1.

**Ground truth assertions**: Validates that each repo contains files or authors, then spot-checks the first 5 file and author records for required fields and correct types.

---

## Evidence Collection

Every evaluation check and LLM judge collects structured evidence for transparency and reproducibility.

### Programmatic Check Evidence

Each programmatic check returns a result dictionary:

```json
{
  "check_id": "accuracy.churn_monotonicity",
  "status": "pass",
  "message": "All 4 files satisfy churn_30d <= churn_90d"
}
```

Status values: `pass`, `fail`, `warn`, `error`. The `message` field provides human-readable context including counts and sample violations.

### LLM Judge Evidence

Each LLM judge returns a `JudgeResult` with structured evidence:

```json
{
  "dimension": "ownership_accuracy",
  "score": 4,
  "confidence": 0.88,
  "reasoning": "Detailed explanation of assessment...",
  "evidence_cited": [
    "All 18 file-level ownership percentages are within valid 0-100% bounds",
    "Percentage calculations are mathematically correct: e.g., src/api.py: 40/120 = 33.33%"
  ],
  "recommendations": [
    "Fix avg_top_author_pct calculation in repo_summaries"
  ],
  "sub_scores": {
    "ownership_bounds": 5,
    "author_count_accuracy": 4,
    "concentration_detection": 5
  }
}
```

### Evidence by Judge

| Judge | Evidence Includes |
|-------|-------------------|
| Ownership Accuracy | Sample files (up to 20), repo summaries, ownership validation results, ground truth comparisons |
| Churn Validity | File activity counts (30d/90d/stale), high-churn file samples, repo churn totals, validation issues |
| Actionability | Knowledge silo samples, high-concentration file samples, stale file samples, per-repo risk metrics |
| Integration | File/author validation rates, record-level issues, envelope structure issues, schema availability |

### Synthetic Baseline Context

All judges load a synthetic evaluation context when available. This context includes the programmatic evaluation results (score, decision, checks passed/failed) and provides interpretation guidance to the LLM. For synthetic evaluation mode, the LLM applies stricter rubrics (ground truth comparison). For real-world mode, the LLM evaluates against internal consistency and domain expectations.

---

## Ground Truth Methodology

### Synthetic Repository Design

Ground truth is defined in `evaluation/ground-truth/synthetic.json`. The file contains 4 synthetic repositories, each designed to test specific ownership patterns:

| Repo Name | Purpose | Files | Authors | Key Pattern |
|-----------|---------|-------|---------|-------------|
| `single-author` | Knowledge silo detection | 4 | 1 | All files by alice@example.com; 100% ownership; 3 knowledge silos (files > 100 lines) |
| `balanced` | Equal contribution | 3 | 3 | 3 authors contributing equally; `top_author_pct` expected in 30-40% range; no silos |
| `concentrated` | Dominant author | 4 | 3 | alice@example.com dominates at 80-95%; 3 high-concentration files; 1 knowledge silo |
| `high-churn` | Churn metric validation | 3 | 3 | Active file with 4-6 commits in 30d; stale file with 0 churn; moderate file in between |

### Expected Value Formats

The ground truth uses two formats for expected values:

**Exact values** -- used when the expected value is deterministic:
```json
{
  "unique_authors": 1,
  "top_author": "alice@example.com",
  "top_author_pct": 100.0,
  "churn_30d": 0,
  "churn_90d": 0
}
```

**Range values** -- used when the expected value depends on timing or git history detail:
```json
{
  "top_author_pct_range": [30, 40],
  "churn_30d_range": [4, 6],
  "churn_90d_range": [7, 9]
}
```

Range values use a `_range` suffix with a `[min, max]` array. The tolerance for percentage comparisons is 5.0 percentage points (defined in `tolerance.percentage`).

### Invariants

The ground truth file defines 4 invariants that must hold for ALL repos:

| Invariant | Description |
|-----------|-------------|
| `ownership_sums_100` | Sum of author ownership percentages equals 100 for each file |
| `churn_monotonic` | `churn_30d <= churn_90d` for all files |
| `unique_authors_positive` | `unique_authors >= 1` for all files |
| `top_author_bounded` | `0 <= top_author_pct <= 100` |

### Knowledge Silo Definition

A file is classified as a knowledge silo when:
- `unique_authors == 1` (single contributor)
- `total_lines > 100` (substantive code, not trivially small)

The `is_knowledge_silo` boolean in the ground truth explicitly marks expected silo status per file. For example, in the `single-author` repo:
- `src/main.py` and `src/utils.py`: `is_knowledge_silo: true` (single author, > 100 lines)
- `src/config.py` and `tests/test_main.py`: `is_knowledge_silo: false` (single author, but <= 100 lines)

### Ground Truth Comparison Utility

The `evaluation/llm/judges/utils.py` module provides a `compare_files()` function for ground truth validation:

```python
def compare_files(actual, expected, tolerance=0.05):
    """Compare actual file metrics against expected ground truth.

    Compares:
    - unique_authors: exact match
    - top_author_pct: within tolerance (default 5%)

    Returns:
    - matches: files where all metrics match
    - mismatches: files with specific metric deviations
    - missing: expected files not found in actual output
    - extra: actual files not in expected set
    - accuracy: match count / expected count
    """
```

---

## Running Evaluation

### Prerequisites

```bash
# Ensure virtual environment is set up
cd src/tools/git-blame-scanner
make setup
```

### Programmatic Evaluation

```bash
# Run all 17 programmatic checks
make evaluate

# Equivalent manual invocation
.venv/bin/python -m scripts.evaluate \
    --results-dir outputs/<run-id> \
    --ground-truth-dir evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json
```

Output is written to `evaluation/results/evaluation_report.json`.

### LLM Evaluation

```bash
# Run all 4 LLM judges (default model: opus-4.5)
make evaluate-llm

# Run with specific model
make evaluate-llm LLM_MODEL=sonnet

# Run a single judge
.venv/bin/python -m evaluation.llm.orchestrator \
    outputs/<run-id> \
    --judge ownership_accuracy \
    --output evaluation/results/llm_evaluation.json

# JSON-only output (no console report)
.venv/bin/python -m evaluation.llm.orchestrator \
    outputs/<run-id> \
    --json \
    --output evaluation/results/llm_evaluation.json

# With custom timeout
.venv/bin/python -m evaluation.llm.orchestrator \
    outputs/<run-id> \
    --timeout 180

# With explicit programmatic results input
.venv/bin/python -m evaluation.llm.orchestrator \
    outputs/<run-id> \
    --programmatic-results evaluation/results/evaluation_report.json
```

Output is written to `evaluation/results/llm_evaluation.json`.

### Full Pipeline

```bash
# 1. Analyze synthetic repos
make analyze REPO_PATH=eval-repos/synthetic

# 2. Run programmatic evaluation
make evaluate

# 3. Run LLM evaluation (uses programmatic results as context)
make evaluate-llm

# 4. View results
cat evaluation/results/evaluation_report.json
cat evaluation/results/llm_evaluation.json
```

### Evaluation Outputs

```
evaluation/results/
  evaluation_report.json    # Programmatic evaluation (17 checks)
  llm_evaluation.json       # LLM judge results (4 judges)
```

---

## Extending Evaluation

### Adding a Programmatic Check

1. Add a `check_<name>` function to the appropriate module in `scripts/checks/`:
   - `accuracy.py` for data correctness invariants
   - `coverage.py` for output completeness checks
   - `performance.py` for metadata and structural checks

2. The function signature must be:
   ```python
   def check_<name>(output: dict, ground_truth: dict | None) -> list[dict]:
   ```

3. Return a list of result dictionaries with `check_id`, `status`, and `message`:
   ```python
   return [{
       "check_id": "accuracy.new_check",
       "status": "pass",  # or "fail", "warn"
       "message": "Description of result",
   }]
   ```

4. The check is automatically discovered by `evaluate.py` (no registration needed). All `check_*` functions in `scripts/checks/*.py` modules are loaded dynamically.

5. Update this document with the new check details.

### Adding an LLM Judge

1. Create `evaluation/llm/judges/<dimension>.py` extending `BaseJudge`
2. Implement required methods:
   - `dimension_name` (property): unique identifier string
   - `weight` (property): float between 0 and 1
   - `collect_evidence()`: returns evidence dictionary
   - `get_default_prompt()`: returns prompt template string with `{{ evidence }}` placeholder
   - `run_ground_truth_assertions()`: returns `(bool, list[str])`
3. Optionally implement `run_heuristic_evaluation()` for LLM-free fallback
4. Create prompt template in `evaluation/llm/prompts/<dimension>.md` (optional, can use inline prompt)
5. Register in `evaluation/llm/orchestrator.py`:
   ```python
   JUDGES = {
       ...
       "new_dimension": (NewDimensionJudge, 0.XX),
   }
   ```
6. Register in `evaluation/llm/judges/__init__.py`
7. Adjust existing weights so total equals 1.0
8. Update this document

### Adding Ground Truth

1. Add a new repo entry to `evaluation/ground-truth/synthetic.json`:
   ```json
   "new-scenario": {
     "description": "Purpose of this test scenario",
     "expected_summary": { ... },
     "files": {
       "path/to/file.py": {
         "unique_authors": 2,
         "top_author_pct_range": [60, 70]
       }
     }
   }
   ```

2. Create the corresponding synthetic repository in `eval-repos/synthetic/`
3. Run the tool against it and verify output matches expectations
4. Add the repo name to the `SYNTHETIC_PATTERNS` set in `evaluation/llm/judges/base.py`:
   ```python
   SYNTHETIC_PATTERNS = SharedBaseJudge.SYNTHETIC_PATTERNS | {
       "single-author", "balanced", "concentrated", "high-churn",
       "new-scenario",
   }
   ```

---

## Confidence Requirements

### LLM Judge Confidence

Each judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review needed |

### Heuristic vs. LLM Confidence

When running in heuristic mode (no LLM), judges report lower confidence (typically 0.7-0.8) because the heuristic logic is simpler than LLM reasoning. This signals to downstream consumers that the scores should be interpreted with more caution.

### Most Recent Evaluation Results

The most recent evaluation run (2026-02-09) produced:

| Component | Result |
|-----------|--------|
| Programmatic | PASS (17/17, score: 1.0) |
| LLM Overall | STRONG_PASS (4.45/5.0, Grade: A-) |
| Avg Confidence | 0.875 |

| LLM Judge | Score | Confidence | Sub-scores |
|-----------|-------|------------|------------|
| Ownership Accuracy | 4/5 | 0.88 | bounds: 5, author_count: 4, concentration: 5 |
| Churn Validity | 5/5 | 0.95 | consistency: 5, validity: 5, coherence: 4 |
| Actionability | 4/5 | 0.85 | silo_id: 5, risk_prioritization: 4, action_enablement: 4 |
| Integration | 5/5 | 0.82 | schema: 5, completeness: 5, quality: 5 |

---

## Utility Functions

### Shared Validation Utilities

Located in `evaluation/llm/judges/utils.py`:

| Function | Purpose |
|----------|---------|
| `load_analysis_bundle(output_dir)` | Load all analysis JSON files from output directory into a structured bundle |
| `validate_ownership_percentages(files)` | Check all `top_author_pct` values are in [0, 100] |
| `validate_churn_metrics(files)` | Check `churn_30d <= churn_90d` and non-negative values |
| `compare_files(actual, expected, tolerance)` | Compare actual vs expected file metrics with tolerance |
| `calculate_knowledge_risk_metrics(files)` | Compute risk summary: single-author count, high-concentration count, silo count, stale count, averages |

### Base Judge Helpers

Located in `evaluation/llm/judges/base.py`:

| Method | Purpose |
|--------|---------|
| `extract_files(analysis)` | Extract files list from analysis data, handling envelope unwrapping |
| `extract_authors(analysis)` | Extract authors list from analysis data |
| `extract_summary(analysis)` | Extract summary dict from analysis data |
| `load_all_analysis_results()` | Load all analysis results from output directory |
| `load_ground_truth()` | Load ground truth from ground truth directory |
| `load_synthetic_evaluation_context()` | Load synthetic baseline for LLM context |

---

## References

- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
- [Project Caldera Evaluation Docs](../../../docs/EVALUATION.md)
- [Shared BaseJudge](../../../shared/evaluation/base_judge.py)
- [Tool Compliance Scanner](../../../tool-compliance/tool_compliance.py)
