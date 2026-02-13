# Evaluation Strategy: dotCover Code Coverage

This document describes the evaluation methodology for the dotCover code coverage analysis tool. It covers the hybrid evaluation pipeline combining programmatic checks with LLM-as-a-Judge assessment, the ground truth approach, scoring formulas, and operational guidance.

---

## Evaluation Philosophy

The dotCover evaluation answers a single question: **does the tool produce accurate, actionable, and integration-ready code coverage data?**

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- validates data invariants, coverage accuracy, schema compliance, and performance |
| LLM Judges | 40% | Semantic understanding -- assesses coverage actionability, false positive detection, and SoT integration readiness |

This hybrid approach provides both mathematical precision (are the numbers correct?) and qualitative depth (can a developer act on this output?).

### Design Principles

1. **Invariants over heuristics.** Coverage data has strict mathematical properties (covered <= total, 0 <= pct <= 100). These are tested first and gate everything else.
2. **Hierarchy validation.** dotCover produces a three-level hierarchy (assembly > type > method). Each level is validated independently and cross-referenced for consistency.
3. **Ground truth anchoring.** LLM judges are calibrated against a synthetic .NET project with known coverage characteristics. If ground truth assertions fail, LLM scores are capped at 2/5.
4. **Dual evaluation modes.** The system supports `synthetic` mode (strict ground truth comparison) and `real_world` mode (structural integrity and schema compliance focus). Mode is auto-detected from output directory naming patterns.
5. **Evidence transparency.** Every check and every judge collects and reports the specific evidence that drove its result, enabling reproducible debugging.

---

## Dimension Summary

### Programmatic Dimensions

Programmatic checks are organized into four modules. Within the programmatic component, all categories are weighted equally (each category receives `1/N` weight where N is the number of active categories).

| Dimension | Module | Focus | Check Count |
|-----------|--------|-------|-------------|
| Accuracy | `scripts/checks/accuracy.py` | Coverage percentage correctness, assembly detection | 2 |
| Coverage | `scripts/checks/coverage.py` | Completeness of type analysis | 1 |
| Invariants | `scripts/checks/invariants.py` | Mathematical constraints at all hierarchy levels | 14 |
| Performance | `scripts/checks/performance.py` | Execution time thresholds | 1 |

### LLM Judge Dimensions

| Judge | Weight | Focus | Sub-Dimensions |
|-------|--------|-------|----------------|
| Accuracy | 35% | Coverage measurement correctness | statement_counts, percentage_accuracy, hierarchy_consistency, ground_truth_match |
| Actionability | 25% | Test improvement guidance quality | low_coverage_identification, uncovered_detection, priority_ranking, improvement_guidance |
| False Positive | 20% | Uncovered code detection reliability | uncovered_line_accuracy, coverage_attribution, edge_case_handling, instrumentation_reliability |
| Integration | 20% | SoT schema and pipeline readiness | envelope_compliance, entity_alignment, dbt_compatibility, join_readiness |

### Combined Weight Breakdown

```
Overall = 0.60 * programmatic_normalized + 0.40 * llm_weighted_score

Where:
  programmatic_normalized = 1 + (programmatic_raw * 4)   # maps 0-1 to 1-5
  llm_weighted_score = sum(judge_score * judge_weight)    # already on 1-5 scale
```

---

## Check Catalog

### Accuracy Checks (accuracy.py)

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| `accuracy.overall_coverage` | Overall coverage within expected range | High | `overall_min <= actual_pct <= overall_max` from ground truth `expected_coverage` | Actual percentage, expected min/max range |
| `accuracy.assembly_detected` | Expected assemblies present | High | All assemblies listed in `ground_truth.expected_assemblies` appear in output `data.assemblies` | Set of expected vs. actual assembly names, missing assemblies |

**Behavior without ground truth:** Both checks return `status: pass` with message "No ground truth (skipped)" when `ground_truth` is `None`. This allows the checks to run in real-world mode without false failures.

#### accuracy.overall_coverage

Extracts `data.summary.statement_coverage_pct` from tool output and compares against the `expected_coverage.overall_min` and `expected_coverage.overall_max` values in ground truth. For the synthetic project, the valid range is 50.0% to 75.0%.

```python
# Pass condition:
min_pct <= actual_pct <= max_pct
```

#### accuracy.assembly_detected

Builds a set of actual assembly names from `data.assemblies[*].name` and verifies it is a superset of the expected assembly names from ground truth. Uses Python set subset check (`expected <= assemblies`).

---

### Coverage Checks (coverage.py)

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| `coverage.files_analyzed` | Types analyzed | Medium | `data.types` array is non-empty | Count of types analyzed |

**Note:** dotCover (via Coverlet backend) reports coverage by type rather than by file. This check validates that at least one type was successfully analyzed. An empty `types` array triggers a `warn` status rather than `fail`, since the analysis may have succeeded but found no instrumentable types.

---

### Invariant Checks (invariants.py)

Invariant checks enforce mathematical constraints that must hold at every level of the coverage hierarchy. A single violation at any level causes a `fail` for that specific sub-check.

#### Covered <= Total (check_covered_lte_total)

Validates that `covered_statements <= total_statements` at four levels.

| Check ID | Level | Pass Criteria | Evidence Collected |
|----------|-------|---------------|--------------------|
| `invariants.covered_lte_total.summary` | Summary | `covered_statements <= total_statements` | Covered count, total count |
| `invariants.covered_lte_total.assemblies` | Assemblies | All assemblies satisfy invariant | Count of assemblies checked, violation list (capped at 5) |
| `invariants.covered_lte_total.types` | Types | All types satisfy invariant | Count of types checked, violation list (capped at 5) |
| `invariants.covered_lte_total.methods` | Methods | All methods satisfy invariant | Count of methods checked, violation list (capped at 5) |

#### Percentage Bounds (check_percentage_bounds)

Validates that `0 <= statement_coverage_pct <= 100` at four levels.

| Check ID | Level | Pass Criteria | Evidence Collected |
|----------|-------|---------------|--------------------|
| `invariants.percentage_bounds.summary` | Summary | `0 <= pct <= 100` | Actual percentage value |
| `invariants.percentage_bounds.assemblies` | Assemblies | All assemblies satisfy bounds | Count checked, out-of-bounds violations (capped at 5) |
| `invariants.percentage_bounds.types` | Types | All types satisfy bounds | Count checked, out-of-bounds violations (capped at 5) |
| `invariants.percentage_bounds.methods` | Methods | All methods satisfy bounds | Count checked, out-of-bounds violations (capped at 5) |

#### Non-Negative Counts (check_non_negative_counts)

Validates that `covered_statements >= 0` and `total_statements >= 0` at four levels.

| Check ID | Level | Pass Criteria | Evidence Collected |
|----------|-------|---------------|--------------------|
| `invariants.non_negative_counts.summary` | Summary | Both counts >= 0 | Covered and total values |
| `invariants.non_negative_counts.assemblies` | Assemblies | All assemblies satisfy constraint | Count checked, negative violations (capped at 5) |
| `invariants.non_negative_counts.types` | Types | All types satisfy constraint | Count checked, negative violations (capped at 5) |
| `invariants.non_negative_counts.methods` | Methods | All methods satisfy constraint | Count checked, negative violations (capped at 5) |

#### Hierarchy Consistency (check_hierarchy_consistency)

Validates referential integrity across the assembly > type > method hierarchy.

| Check ID | Relationship | Pass Criteria | Evidence Collected |
|----------|-------------|---------------|--------------------|
| `invariants.hierarchy_consistency.types_to_assemblies` | Type -> Assembly | Every type's `assembly` field references a valid assembly name | Type count, invalid references (capped at 5) |
| `invariants.hierarchy_consistency.methods_to_types` | Method -> Type | Every method's `type_name` field references a valid type name (plain or namespace-qualified) | Method count, invalid references (capped at 5) |
| `invariants.hierarchy_consistency.methods_to_assemblies` | Method -> Assembly | Every method's `assembly` field references a valid assembly name | Method count, invalid references (capped at 5) |

**Type name resolution:** The hierarchy check builds a valid type set that includes both plain names (e.g., `Calculator`) and namespace-qualified names (e.g., `CoverageDemo.Calculator`). Method references are checked against both forms.

---

### Performance Checks (performance.py)

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| `performance.execution_time` | Execution time | High | < 120 seconds (pass), < 300 seconds (warn), >= 300 seconds (fail) | `metadata.timing.total_seconds` from envelope |

**Thresholds:**

| Status | Time Range | Interpretation |
|--------|-----------|----------------|
| Pass | < 2 minutes (120s) | Acceptable for CI/CD integration |
| Warn | 2-5 minutes (120s-300s) | Tolerable but should be optimized |
| Fail | > 5 minutes (300s) | Too slow for standard pipeline execution |

**Missing timing data:** If `metadata.timing.total_seconds` is absent from the output envelope, the check returns `pass` with a note that timing was not recorded. This allows evaluation to proceed when timing instrumentation is not yet integrated.

---

## Scoring Methodology

### Programmatic Score Calculation

The programmatic evaluator computes a raw score from check results:

```python
score = passed / total  # Range: 0.0 to 1.0
```

Where:
- `passed` = count of checks with `status == "pass"`
- `total` = total number of checks executed

The `decision` field at the summary level uses a simple binary rule:

```python
decision = "PASS" if (failed == 0 and errored == 0) else "FAIL"
```

This means any single failure or error causes the entire programmatic evaluation to fail, regardless of the raw score.

### Normalized Score for Decision Thresholds

The raw 0-1 score is normalized to a 1-5 scale for decision thresholds:

```python
normalized = score * 5.0
```

The `determine_decision()` function maps this normalized score to a decision label:

```python
def determine_decision(score: float) -> str:
    normalized = score * 5.0
    if normalized >= 4.0:
        return "STRONG_PASS"
    elif normalized >= 3.5:
        return "PASS"
    elif normalized >= 3.0:
        return "WEAK_PASS"
    return "FAIL"
```

### Scorecard Dimension Scoring

When generating the scorecard, each category receives an equal weight (`1/N` where N = number of categories). Within each category, the dimension score is computed as:

```python
dimension_score = (passed / total) * 5.0  # Range: 0.0 to 5.0
weighted_score = dimension_score / num_categories
```

### LLM Judge Scoring

Each LLM judge produces a `JudgeResult` with:
- `score`: Integer 1-5
- `confidence`: Float 0.0-1.0
- `sub_scores`: Dictionary of sub-dimension scores (each 1-5)

The combined LLM score is the weighted sum:

```python
llm_weighted_score = (
    accuracy_score    * 0.35 +
    actionability_score * 0.25 +
    false_positive_score * 0.20 +
    integration_score  * 0.20
)
```

### Ground Truth Score Capping

Each LLM judge runs ground truth assertions before scoring. If assertions fail, the LLM score is capped:

```python
if not gt_passed:
    score = min(llm_score, 2)  # Maximum score of 2 if ground truth fails
```

This ensures that even a favorable qualitative assessment cannot override concrete data correctness failures.

---

## Decision Thresholds

### Overall Decision Table

| Decision | Normalized Score | Raw Score Equivalent | Interpretation |
|----------|-----------------|---------------------|----------------|
| STRONG_PASS | >= 4.0 | >= 80% checks passing | Excellent, production-ready coverage data |
| PASS | >= 3.5 | >= 70% checks passing | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 | >= 60% checks passing | Acceptable with caveats, review recommended |
| FAIL | < 3.0 | < 60% checks passing | Significant issues, requires remediation |

### Programmatic Pass/Fail Rule

The programmatic evaluator uses a strict rule: **any single failed or errored check causes FAIL**. The normalized score-based decision (`STRONG_PASS`, `PASS`, `WEAK_PASS`, `FAIL`) is used for the scorecard report and for informational purposes.

### LLM Judge Confidence Thresholds

Each judge reports a confidence level:

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review needed |

---

## LLM Judge Details

### Accuracy Judge (35% weight)

**File:** `evaluation/llm/judges/accuracy.py`
**Prompt:** `evaluation/llm/prompts/accuracy.md`

Evaluates the correctness of coverage percentage calculations and statement counts across the full assembly > type > method hierarchy.

#### Sub-Dimensions (equal weight: 25% each)

| Sub-Dimension | What It Measures |
|---------------|-----------------|
| `statement_counts` | Are covered_statements and total_statements counts accurate? |
| `percentage_accuracy` | Is statement_coverage_pct correctly calculated as (covered/total)*100? |
| `hierarchy_consistency` | Do assembly totals equal the sum of their type totals? Do type totals equal the sum of their method totals? |
| `ground_truth_match` | How closely does the output match known expected values from the synthetic project? |

#### Scoring Rubric -- Synthetic Mode

| Score | Criteria |
|-------|----------|
| 5 | All coverage percentages match ground truth within 1%. Statement counts exact. No invariant violations. Hierarchy sums correct. |
| 4 | Percentages within 5% of ground truth. Minor count discrepancies. No invariant violations. |
| 3 | Percentages within 10%. Some count discrepancies. No critical invariant violations. |
| 2 | Large deviations (>10%). Multiple count discrepancies. Some invariant violations. |
| 1 | Completely incorrect data. Major invariant violations. Corrupted or unusable output. |

#### Scoring Rubric -- Real-World Mode

| Score | Criteria |
|-------|----------|
| 5 | All invariants hold (covered <= total, 0 <= pct <= 100). Percentages correctly calculated. Complete schema compliance. |
| 4 | Minor calculation rounding issues. All data structurally correct. |
| 3 | Some schema issues but data usable. |
| 2 | Multiple schema or calculation issues. |
| 1 | Broken output, invalid data. |

#### Evidence Collected

- `coverage_summary`: Per-run summary with covered/total/pct values
- `assembly_coverage`: Up to 5 assemblies per run with name, covered, total, pct
- `type_coverage_sample`: Up to 10 types per run with assembly, name, covered, total, pct
- `method_coverage_sample`: Up to 15 methods per run with type, name, covered, total, pct
- `ground_truth_comparison`: Expected coverage ranges and assembly definitions
- `synthetic_baseline`: Prior synthetic evaluation results (real-world mode only)
- `interpretation_guidance`: Context-appropriate instructions for the LLM judge

#### Ground Truth Assertions

1. **Invariant check:** `covered_statements <= total_statements` at summary level
2. **Bounds check:** `0 <= statement_coverage_pct <= 100` at summary level
3. **Percentage calculation:** `abs(pct - (covered/total)*100) <= 0.1` when total > 0
4. **Expected coverage match:** Actual coverage within 5% of ground truth expected values

---

### Actionability Judge (25% weight)

**File:** `evaluation/llm/judges/actionability.py`
**Prompt:** `evaluation/llm/prompts/actionability.md`

Evaluates whether the coverage output provides sufficient detail for developers to identify where to add tests and prioritize testing efforts.

#### Sub-Dimensions (equal weight: 25% each)

| Sub-Dimension | What It Measures |
|---------------|-----------------|
| `low_coverage_identification` | Are methods with < 50% coverage clearly surfaced with type and method names? |
| `uncovered_detection` | Are completely uncovered types (0% coverage) identified with statement counts? |
| `priority_ranking` | Can developers prioritize by impact (e.g., uncovered statement count)? |
| `improvement_guidance` | Does the data enable targeted test writing (specific namespaces, types, methods)? |

#### Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Clearly identifies all methods with < 50% coverage. Provides specific type/method names. Enables prioritization by impact. Easy to find "quick wins." |
| 4 | Identifies most low-coverage areas. Type/method granularity allows targeted testing. Coverage percentages enable comparison. |
| 3 | Basic identification of uncovered areas. Some granularity for test targeting. Percentages present but limited context. |
| 2 | Limited identification of problem areas. Too coarse-grained for actionable testing. Missing key coverage gaps. |
| 1 | No useful information for test improvement. Cannot identify where tests are needed. Data too aggregated or missing. |

#### Evidence Collected

- `coverage_summary`: Per-run summary metrics
- `low_coverage_methods`: Methods with < 50% coverage, sorted by uncovered statement count (top 20). Each entry includes: run_id, type, method name, coverage_pct, total_statements, uncovered_statements
- `uncovered_types`: Types with 0% coverage and total_statements > 0, sorted by total statements (top 10). Each entry includes: run_id, assembly, namespace, type name, total_statements
- `coverage_distribution`: Histogram of methods across four buckets: 0-25%, 25-50%, 50-75%, 75-100%
- `ground_truth_findings`: Expected low-coverage methods and uncovered types from ground truth

#### Ground Truth Assertions

1. **Low-coverage method detection:** Each method in `ground_truth.expected_low_coverage_methods` must appear in output with `statement_coverage_pct < 50`
2. **Uncovered type detection:** Each type in `ground_truth.expected_uncovered_types` must appear in output with `statement_coverage_pct == 0`

---

### False Positive Judge (20% weight)

**File:** `evaluation/llm/judges/false_positive.py`
**Prompt:** `evaluation/llm/prompts/false_positive.md`

Evaluates the reliability of coverage detection, focusing on whether "uncovered" lines are truly uncovered and "covered" lines are truly covered.

#### Sub-Dimensions (equal weight: 25% each)

| Sub-Dimension | What It Measures |
|---------------|-----------------|
| `uncovered_line_accuracy` | Are lines reported as uncovered truly not exercised by tests? |
| `coverage_attribution` | Are coverage counts correctly attributed to the right methods/types? |
| `edge_case_handling` | Are generics, async methods, lambdas, and nested classes handled correctly? |
| `instrumentation_reliability` | Does the instrumentation produce consistent results across runs? |

#### Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | No false positives on verified covered code. Accurate attribution for all scenarios. Edge cases correct (generics, async, lambdas). Consistent instrumentation. |
| 4 | Rare false positives (< 2% error rate). Minor edge case issues. Overall reliable. |
| 3 | Some false positives (2-5% error rate). Known edge case limitations. Usable but requires verification. |
| 2 | Significant false positives (5-10% error rate). Multiple edge case failures. Manual verification required. |
| 1 | Unreliable detection (> 10% error rate). Systematic false positives. Data cannot be trusted. |

#### Evidence Collected

- `coverage_summary`: Per-run summary
- `known_covered_code`: Methods from `ground_truth.known_covered_methods` expected to be covered
- `reported_coverage`: Sample of up to 10 methods per run with covered/total counts
- `edge_cases`: Types with generic markers (`<`, backtick) or nested class markers (`+`, `/`), each with coverage_pct (capped at 15)
- `anomalies`: Detected data anomalies (capped at 10):
  - `percentage_mismatch`: pct == 100 but covered != total
  - `zero_pct_with_coverage`: pct == 0 but covered > 0

#### Ground Truth Assertions

1. **Covered > total violation:** `covered_statements > total_statements` at method level is always a false positive failure
2. **Percentage calculation mismatch:** `abs(pct - (covered/total)*100) > 1` at method level
3. **Known covered code verification:** Methods listed in `ground_truth.known_covered_methods` must have `covered_statements > 0`

---

### Integration Judge (20% weight)

**File:** `evaluation/llm/judges/integration.py`
**Prompt:** `evaluation/llm/prompts/integration.md`

Evaluates SoT schema compatibility and readiness for persistence into the Caldera data pipeline.

#### Sub-Dimensions (equal weight: 25% each)

| Sub-Dimension | What It Measures |
|---------------|-----------------|
| `envelope_compliance` | Does the output follow the Caldera envelope format (metadata + data sections)? |
| `entity_alignment` | Do assemblies, types, and methods contain all required entity fields? |
| `dbt_compatibility` | Is the data structure compatible with dbt staging and mart models? |
| `join_readiness` | Can the output be joined with other tool outputs (e.g., via file paths, assembly names)? |

#### Required Metadata Fields

The integration judge validates the presence of 8 required metadata fields:

```
tool_name, tool_version, run_id, repo_id, branch, commit, timestamp, schema_version
```

#### Expected Data Fields

```
tool, tool_version, summary, assemblies, types, methods
```

#### Entity Field Requirements

| Entity Level | Required Fields |
|-------------|----------------|
| Assembly | `name`, `covered_statements`, `total_statements`, `statement_coverage_pct` |
| Type | `assembly`, `name`, `covered_statements`, `total_statements`, `statement_coverage_pct` |
| Method | `assembly`, `type_name`, `name`, `covered_statements`, `total_statements`, `statement_coverage_pct` |

#### Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Full Caldera envelope. All 8 metadata fields present and valid. Schema matches entity definitions exactly. All paths repo-relative. Ready for immediate persistence. |
| 4 | Envelope correct. Minor metadata issues (optional fields missing). Schema mostly aligned. Paths generally correct. |
| 3 | Basic envelope present. Some metadata gaps. Schema requires minor transformation. Some path normalization needed. |
| 2 | Incomplete envelope. Missing required metadata. Major schema misalignment. Path format issues. |
| 1 | No envelope. Critical metadata missing. Incompatible schema. Absolute or malformed paths. |

#### Evidence Collected

- `envelope_structure`: Per-run envelope validation (has_metadata, has_data, is_valid_envelope, top_level_keys)
- `metadata_completeness`: Per-run metadata field presence (fields_present, fields_missing, completeness_pct)
- `data_schema_sample`: Per-run data field presence and entity counts (assembly_count, type_count, method_count)
- `entity_field_coverage`: Per-run entity field validation issues (sampled from first 3 entities per level)
- `path_normalization`: Per-run path format issues (absolute paths, relative dot paths, Windows separators)

#### Ground Truth Assertions

1. **Envelope structure:** `metadata` and `data` sections must be present
2. **Required metadata:** All 8 fields must be present and non-null
3. **Data structure:** `assemblies`, `types`, and `methods` arrays must be present in data
4. **Path normalization:** No absolute paths (starting with `/`) in type file_path fields

---

## Ground Truth Methodology

### Synthetic Project

**File:** `evaluation/ground-truth/synthetic.json`

The ground truth is built from a synthetic .NET 10 project named "CoverageDemo" designed to exercise specific coverage scenarios.

#### Project Structure

| Component | Purpose | Expected Coverage |
|-----------|---------|-------------------|
| `CoverageDemo` assembly | Main library | 50-75% overall |
| `Calculator` type | Fully tested class (Add, Subtract, Multiply, Divide) | ~100% |
| `StringUtils` type | Partially tested class (Reverse tested, Truncate untested, IsValidEmail partial) | Partial |
| `UntestedClass` type | No tests exist | 0% |

#### Expected Values

```json
{
  "expected_coverage": {
    "overall_min": 50.0,
    "overall_max": 75.0
  },
  "expected_assemblies": [
    {
      "name": "CoverageDemo",
      "min_coverage": 50,
      "max_coverage": 75
    }
  ],
  "expected_full_coverage_types": [
    { "name": "Calculator" }
  ],
  "expected_partial_coverage_types": [
    { "name": "StringUtils" }
  ],
  "expected_uncovered_types": [
    { "name": "UntestedClass" }
  ],
  "expected_low_coverage_methods": [
    {
      "type": "StringUtils",
      "name": "Truncate",
      "expected_coverage": 0
    }
  ]
}
```

### Generation Process

1. **Build synthetic project.** Create a .NET project with known code paths: fully tested, partially tested, and untested classes.
2. **Run Coverlet/dotCover.** Execute the coverage tool against the test suite.
3. **Manual verification.** Inspect coverage reports to confirm Calculator has 100% coverage, StringUtils.Truncate has 0%, and UntestedClass has 0%.
4. **Document expected ranges.** Record overall coverage range (50-75%) accounting for dotCover version variations.
5. **Persist as ground truth.** Save verified expectations to `evaluation/ground-truth/synthetic.json`.

### Known Caveats

- Coverage percentages may vary slightly across dotCover/Coverlet versions
- The 50-75% overall range accounts for this version variance
- `UntestedClass` must always report 0% coverage since no tests target it
- `Calculator` should always report ~100% with all branches covered

### Evaluation Modes

| Mode | Trigger | Ground Truth Usage |
|------|---------|-------------------|
| `synthetic` | Output directory matches synthetic repo patterns | Strict comparison against expected values |
| `real_world` | Default / non-synthetic directory patterns | Structural integrity focus; synthetic baseline used as calibration context |
| Auto-detect | `evaluation_mode=None` | Directory naming patterns determine mode |

In `real_world` mode, the LLM judges receive a `synthetic_baseline` evidence field containing prior synthetic evaluation results. This provides calibration context: "we know the tool works correctly on synthetic data; now evaluate whether this real-world output has structural integrity."

---

## Evidence Collection

### Programmatic Evidence

Each programmatic check returns a result dictionary:

```json
{
  "check_id": "invariants.covered_lte_total.types",
  "status": "pass",
  "message": "All 5 types have covered <= total"
}
```

Status values: `pass`, `fail`, `warn`, `error`.

When a check fails, the message includes specific violation details (entity names, values) capped at 5 items with a `"..."` suffix if more exist.

### LLM Evidence

Each LLM judge collects structured evidence via `collect_evidence()`. Evidence is injected into the prompt template using `{{ placeholder }}` syntax. The evidence includes:

| Placeholder | Description |
|-------------|-------------|
| `{{ evaluation_mode }}` | "synthetic" or "real_world" |
| `{{ interpretation_guidance }}` | Mode-appropriate instructions for the judge |
| `{{ synthetic_baseline }}` | Prior synthetic results (real-world mode) or "N/A" (synthetic mode) |
| `{{ coverage_summary }}` | Per-run coverage summary data |
| Judge-specific placeholders | See individual judge sections above |

### LLM Response Format

All judges expect a structured JSON response:

```json
{
  "score": 4,
  "confidence": 0.9,
  "reasoning": "Detailed explanation of the score",
  "evidence_cited": ["Specific finding 1", "Specific finding 2"],
  "recommendations": ["Improvement suggestion 1"],
  "sub_scores": {
    "sub_dimension_1": 4,
    "sub_dimension_2": 5
  }
}
```

---

## Running Evaluation

### Prerequisites

```bash
# Set up virtual environment
cd src/tools/dotcover
make setup
```

### Programmatic Evaluation

```bash
# Full evaluation (runs synthetic analysis if needed, then checks)
make evaluate

# Manually run evaluation against existing output
.venv/bin/python -m scripts.evaluate \
    --results-dir outputs/dotcover-test-run \
    --ground-truth-dir evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json
```

The `make evaluate` target will:
1. Check for synthetic output at `outputs/dotcover-test-run/output.json`
2. If missing, run `make analyze REPO_PATH=eval-repos/synthetic RUN_ID=dotcover-test-run`
3. Execute all programmatic checks
4. Save `evaluation_report.json` and generate `scorecard.json` + `scorecard.md`

### LLM Evaluation

```bash
# Run LLM evaluation (4 judges)
make evaluate-llm

# With specific model
make evaluate-llm LLM_MODEL=opus-4.5

# Manually run LLM evaluation
.venv/bin/python -m evaluation.llm.orchestrator \
    outputs/ \
    --output evaluation/results/llm_evaluation.json \
    --model sonnet \
    --programmatic-results evaluation/results/evaluation_report.json
```

The LLM orchestrator accepts the programmatic evaluation results as input, enabling it to include programmatic pass/fail context in its assessment.

### Full Pipeline

```bash
# 1. Analyze synthetic repo
make analyze REPO_PATH=eval-repos/synthetic

# 2. Run programmatic evaluation
make evaluate

# 3. Run LLM evaluation
make evaluate-llm

# 4. Review results
cat evaluation/scorecard.md
cat evaluation/results/evaluation_report.json
cat evaluation/results/llm_evaluation.json
```

### Evaluation Outputs

All evaluation artifacts are written to a fixed location and overwrite the previous run:

```
evaluation/
├── EVAL_STRATEGY.md             # This document
├── ground-truth/
│   └── synthetic.json           # Ground truth definitions
├── results/
│   ├── evaluation_report.json   # Programmatic check results
│   ├── scorecard.json           # Structured scorecard
│   ├── scorecard.md             # Human-readable scorecard
│   └── llm_evaluation.json      # LLM judge results
└── llm/
    ├── judges/                  # Judge implementations
    │   ├── __init__.py
    │   ├── base.py              # dotCover BaseJudge (extends shared)
    │   ├── accuracy.py          # AccuracyJudge
    │   ├── actionability.py     # ActionabilityJudge
    │   ├── false_positive.py    # FalsePositiveJudge
    │   └── integration.py       # IntegrationJudge
    ├── prompts/                 # Prompt templates
    │   ├── accuracy.md
    │   ├── actionability.md
    │   ├── false_positive.md
    │   └── integration.md
    └── orchestrator.py          # LLM evaluation entry point
```

---

## Extending Evaluation

### Adding a Programmatic Check

1. Create or edit a file in `scripts/checks/` (e.g., `scripts/checks/schema.py`)
2. Implement one or more `check_*` functions with the signature:

```python
def check_example(output: dict, ground_truth: dict | None) -> dict | list[dict]:
    """Each function receives the tool output and ground truth.

    Returns a single dict or list of dicts with:
    - check_id: str (format: "module.check_name" or "module.check_name.sublevel")
    - status: str ("pass", "fail", "warn", "error")
    - message: str (human-readable explanation)
    """
```

3. The evaluator auto-discovers all `check_*` functions from all non-underscore `.py` files in `scripts/checks/`
4. Run `make evaluate` to verify
5. Update this document with the new check

### Adding an LLM Judge

1. Create `evaluation/llm/judges/<dimension>.py` inheriting from `BaseJudge`
2. Implement required properties and methods:
   - `dimension_name` property returning the dimension string
   - `weight` property returning float 0.0-1.0 (ensure all weights sum to 1.0)
   - `collect_evidence()` returning evidence dict
   - `get_default_prompt()` returning the prompt template string
   - `run_ground_truth_assertions()` returning `(passed: bool, failures: list[str])`
3. Create `evaluation/llm/prompts/<dimension>.md` with the prompt template
4. Register in `evaluation/llm/judges/__init__.py`
5. Update the orchestrator to include the new judge
6. Update this document

### Updating Ground Truth

1. Modify the synthetic .NET project if needed (`eval-repos/synthetic/`)
2. Run the analysis: `make analyze REPO_PATH=eval-repos/synthetic`
3. Manually verify the output matches expectations
4. Update `evaluation/ground-truth/synthetic.json` with new expected values
5. Run `make evaluate` to confirm all checks pass

### Updating Thresholds

Performance thresholds are defined as module-level constants:

```python
# In scripts/checks/performance.py
THRESHOLD_PASS_SECONDS = 120   # < 2 minutes = pass
THRESHOLD_WARN_SECONDS = 300   # 2-5 minutes = warn, > 5 minutes = fail
```

Coverage range thresholds are defined in ground truth:

```json
{
  "expected_coverage": {
    "overall_min": 50.0,
    "overall_max": 75.0
  }
}
```

---

## References

- [dotCover Documentation](https://www.jetbrains.com/help/dotcover/)
- [Coverlet Documentation](https://github.com/coverlet-coverage/coverlet)
- [Caldera Envelope Specification](../../../docs/REFERENCE.md)
- [Caldera Persistence Patterns](../../../docs/PERSISTENCE.md)
- [Shared BaseJudge](../../../shared/evaluation/base_judge.py)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
