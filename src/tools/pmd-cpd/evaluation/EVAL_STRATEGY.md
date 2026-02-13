# Evaluation Strategy: PMD CPD (Copy/Paste Detector)

This document describes the evaluation methodology for the PMD CPD tool, which performs
token-based code duplication detection with optional semantic comparison across 7 languages.

---

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation in a
hybrid approach that balances objectivity with semantic depth:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- validates clone counts, coverage, edge cases, performance |
| LLM Judges | 40% | Semantic understanding -- evaluates whether detected clones are genuine, cross-file linking is clear, reports are actionable |

**Why hybrid?** Programmatic checks excel at verifiable numerical assertions (clone count
within expected range, file coverage across languages, execution time thresholds) but
cannot assess whether a detected clone represents meaningful duplication or whether a
report gives a developer enough context to act. LLM judges fill that gap by evaluating
output quality, report usefulness, and semantic correctness that resist simple heuristics.

**Design principles:**

1. **Ground truth first** -- Every programmatic check compares tool output against
   hand-verified ground truth files, one per supported language.
2. **Binary pass/fail with graduated scores** -- Each check has a clear pass/fail
   threshold, but also produces a continuous 0.0-1.0 score for finer-grained tracking.
3. **Evidence transparency** -- Every check and judge collects structured evidence so
   failures can be diagnosed without re-running the evaluation.
4. **Mode awareness** -- The evaluation distinguishes standard token matching from
   semantic mode (`--ignore-identifiers`, `--ignore-literals`) and adjusts expectations
   accordingly. Checks AC-6 and AC-7 award a neutral 0.5 score when semantic mode is
   not enabled rather than penalizing the tool.

---

## Dimension Summary

### Programmatic Dimensions (60% of combined score)

Programmatic evaluation runs 28 checks across 4 equally-weighted categories. Each
category's weight is `1 / number_of_categories` (25% each within the programmatic
component).

| Dimension | ID Range | Check Count | Internal Weight | Effective Weight (of total) |
|-----------|----------|-------------|-----------------|----------------------------|
| Accuracy | AC-1 to AC-8 | 8 | 25.0% | 15.0% |
| Coverage | CV-1 to CV-8 | 8 | 25.0% | 15.0% |
| Edge Cases | EC-1 to EC-8 | 8 | 25.0% | 15.0% |
| Performance | PF-1 to PF-4 | 4 | 25.0% | 15.0% |
| **Total** | | **28** | **100%** | **60%** |

### LLM Judge Dimensions (40% of combined score)

| Judge | Weight (within LLM) | Effective Weight (of total) | Sub-Dimensions |
|-------|---------------------|----------------------------|----------------|
| Duplication Accuracy | 35% | 14.0% | genuine_clones, false_positive_rate, location_accuracy |
| Semantic Detection | 25% | 10.0% | identifier_detection, literal_detection, type2_clone_detection |
| Cross-File Detection | 20% | 8.0% | detection_rate, file_linking, reporting_clarity |
| Actionability | 20% | 8.0% | location_clarity, context_provided, prioritization_support |
| **Total** | **100%** | **40%** | |

---

## Programmatic Check Catalog

### Accuracy Checks (AC-1 to AC-8)

These checks validate the correctness of clone detection against ground truth expectations.

| Check ID | Name | Pass Threshold | Pass Criteria | Evidence Collected |
|----------|------|----------------|---------------|-------------------|
| AC-1 | Heavy duplication detection | >= 80% | Files named `*heavy*` in ground truth must have at least 1 clone detected, or meet the `expected_clone_range` minimum | Per-file: filename, detected clone count, status (detected/missed) |
| AC-2 | Clone count accuracy | >= 70% | Actual `duplicate_blocks` count falls within the `expected_clone_range` [min, max] specified in ground truth | Per-file: filename, actual count, expected range, status (in_range/out_of_range) |
| AC-3 | Duplication percentage accuracy | >= 60% | Actual `duplication_percentage` falls within `duplication_percentage_range` [min, max]; skips light_duplication, semantic, and cross_file files | Per-file: filename, actual percentage, expected range, status |
| AC-4 | No false positives in clean files | >= 90% | Files named `*no_dup*` must have 0 or at most 1 `duplicate_blocks` (tolerance of 1) | Per-file: filename, detected clone count, status (correct/false_positive) |
| AC-5 | Cross-file clone detection | >= 70% | For each `cross_file_expectations` pair, the number of cross-file clones involving both listed files meets the `expected_cross_file_clone_range` minimum | Per-pair: pair name, files, detected clones, expected range, status |
| AC-6 | Semantic identifier detection | >= 70% | When `--ignore-identifiers` is active, files with `expected_clones_semantic.requires_ignore_identifiers` have clone counts within the specified `count_range`. Returns neutral 0.5 score if semantic mode is off. | Per-file: filename, detected clones, expected range, mode status |
| AC-7 | Semantic literal detection | >= 70% | When `--ignore-literals` is active, files with `expected_clones_semantic.requires_ignore_literals` have clone counts within the specified `count_range`. Returns neutral 0.5 score if semantic mode is off. | Per-file: filename, detected clones, expected range, mode status |
| AC-8 | Clone line accuracy | >= 80% | Each detected duplication must have `lines >= 3` and `occurrences >= 2` to be considered a valid clone entry | Per-clone (first 10): clone_id, lines, tokens, occurrences, validity flag |

### Coverage Checks (CV-1 to CV-8)

These checks validate that the tool analyzes files from all supported languages.

| Check ID | Name | Pass Threshold | Pass Criteria | Evidence Collected |
|----------|------|----------------|---------------|-------------------|
| CV-1 | Python file coverage | >= 80% | All Python files listed in `python.json` ground truth appear in analysis `files` array | Per-file: filename, status (found/not_found) |
| CV-2 | JavaScript file coverage | >= 80% | All JavaScript files listed in `javascript.json` ground truth appear in analysis `files` array | Per-file: filename, status (found/not_found) |
| CV-3 | TypeScript file coverage | >= 80% | All TypeScript files listed in `typescript.json` ground truth appear in analysis `files` array | Per-file: filename, status (found/not_found) |
| CV-4 | C# file coverage | >= 80% | All C# files listed in `csharp.json` ground truth appear in analysis `files` array | Per-file: filename, status (found/not_found) |
| CV-5 | Java file coverage | >= 80% | All Java files listed in `java.json` ground truth appear in analysis `files` array | Per-file: filename, status (found/not_found) |
| CV-6 | Go file coverage | >= 80% | All Go files listed in `go.json` ground truth appear in analysis `files` array | Per-file: filename, status (found/not_found) |
| CV-7 | Rust file coverage | >= 80% | All Rust files listed in `rust.json` ground truth appear in analysis `files` array | Per-file: filename, status (found/not_found) |
| CV-8 | Multi-language detection | >= 70% | The set of languages detected in analysis (after normalizing `ecmascript` to `javascript` and `cs` to `csharp`) covers at least 70% of languages present in ground truth files | detected vs. expected language lists, covered set, missing set |

### Edge Case Checks (EC-1 to EC-8)

These checks validate graceful handling of unusual inputs and boundary conditions.

| Check ID | Name | Pass Threshold | Pass Criteria | Evidence Collected |
|----------|------|----------------|---------------|-------------------|
| EC-1 | Empty file handling | All pass | No errors in `analysis.errors` mention "empty" | List of empty-file-related errors |
| EC-2 | Single-line file handling | All pass | No files with `total_lines <= 1` report `duplicate_lines > 0` | Per-file: filename, total_lines, duplicate_lines (for violations only) |
| EC-3 | Large file handling | Elapsed < 600s | Analysis completes within 10-minute timeout; reports count of files with `total_lines > 1000` | elapsed_seconds, large_file_count, timeout_threshold |
| EC-4 | Unicode content handling | All pass | No errors containing encoding-related terms (`encoding`, `unicode`, `utf`, `decode`, `codec`) | List of encoding-related errors |
| EC-5 | Mixed line endings handling | All pass | No errors containing line-ending-related terms (`line ending`, `crlf`, `newline`) | List of line-ending-related errors |
| EC-6 | Deeply nested code handling | Always passes | If the evaluation reaches this point, analysis did not crash on nested structures | total clone count from duplications |
| EC-7 | Special character paths handling | All pass | No errors containing path-related terms (`path`, `filename`, `directory`) | List of path-related errors |
| EC-8 | Zero duplication handling | dup_pct <= 50% | Overall duplication percentage does not exceed 50% when ground truth contains files with `expected_clone_count == 0` | total_clones, duplication_percentage, clean_files_in_gt |

### Performance Checks (PF-1 to PF-4)

These checks validate execution speed and resource efficiency. Skipped in `--quick` mode.

| Check ID | Name | Pass Threshold | Scoring Tiers | Evidence Collected |
|----------|------|----------------|---------------|-------------------|
| PF-1 | Execution time | <= 300s | Excellent (<=30s, score 1.0), Good (<=120s, score 0.8), Acceptable (<=300s, score 0.6), Slow (>300s, score 0.3) | elapsed_seconds, tier thresholds |
| PF-2 | File throughput | >= 1 file/sec | Excellent (>=10 f/s, score 1.0), Good (>=5 f/s, score 0.8), Acceptable (>=1 f/s, score 0.6), Slow (<1 f/s, score 0.3) | total_files, elapsed_seconds, files_per_second |
| PF-3 | Memory efficiency | score >= 0.6 | Efficient (avg_occ <=3, score 1.0), Reasonable (avg_occ <=5, score 0.8), High (avg_occ >5, score 0.6) based on average occurrences per clone as a proxy for data structure efficiency | total_clones, total_occurrences, avg_occurrences_per_clone |
| PF-4 | Incremental analysis support | >= 2/3 fields | Checks for `repo_path`, `analyzed_at`, and `version` in metadata; score = present_fields / 3 | has_repo_path, has_timestamp, has_version booleans |

---

## Scoring

### Per-Check Scoring

Every check produces a `CheckResult` with a continuous `score` between 0.0 and 1.0:

```python
@dataclass
class CheckResult:
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "Heavy duplication detection"
    category: CheckCategory # ACCURACY | COVERAGE | EDGE_CASES | PERFORMANCE
    passed: bool            # Binary pass/fail against threshold
    score: float            # 0.0 to 1.0 continuous score
    message: str            # Human-readable result description
    evidence: dict          # Supporting data for diagnosis
```

Most checks compute score as a simple ratio:

```python
score = correct_items / total_items
```

Performance checks use tiered scoring (1.0 / 0.8 / 0.6 / 0.3) based on threshold bands.

### Category Scoring

Each category score is the **mean of its check scores**:

```python
# From EvaluationReport.score_by_category
category_score = sum(check.score for check in category_checks) / len(category_checks)
```

### Overall Programmatic Score

The overall score is the **unweighted mean of all check scores** across all categories:

```python
# From EvaluationReport.score
overall_score = sum(check.score for check in all_checks) / len(all_checks)
```

Because categories have different check counts (Accuracy: 8, Coverage: 8, Edge Cases: 8,
Performance: 4), this means individual checks in smaller categories carry slightly more
weight. With 28 total checks, each check contributes 1/28 = ~3.57% of the overall score.

### Normalization to 0-5 Scale

The raw 0.0-1.0 score is normalized to a 0.0-5.0 scale for the scorecard:

```python
normalized_score = raw_score * 5.0
```

### Combined Score (Programmatic + LLM)

When running combined evaluation:

```python
# Normalize programmatic score to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)  # 0.0-1.0 maps to 1.0-5.0

# LLM score is already on 1-5 scale (weighted average of judge scores)
llm_score = sum(judge.score * judge.weight for judge in judges)

# Weighted combination
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

---

## Decision Thresholds

Decisions are computed from the normalized score (0-5 scale):

| Decision | Normalized Score | Raw Score (0-1) | Interpretation |
|----------|------------------|-----------------|----------------|
| STRONG_PASS | >= 4.0 | >= 80% | Excellent -- production-ready duplication detection |
| PASS | >= 3.5 | >= 70% | Good -- minor improvements possible |
| WEAK_PASS | >= 3.0 | >= 60% | Acceptable -- known limitations documented |
| FAIL | < 3.0 | < 60% | Significant issues -- requires investigation |

Implementation in `evaluate.py`:

```python
def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on score (0-1)."""
    normalized = score * 5.0
    if normalized >= 4.0:
        return "STRONG_PASS"
    elif normalized >= 3.5:
        return "PASS"
    elif normalized >= 3.0:
        return "WEAK_PASS"
    return "FAIL"
```

The evaluation script exits with code 1 if the raw score falls below 0.7 (normalized 3.5),
which corresponds to the PASS threshold. This enforces a CI gate at the PASS level.

---

## Ground Truth

### Methodology

Ground truth files are hand-crafted JSON documents stored in `evaluation/ground-truth/`,
one per supported language. They define expected duplication characteristics for synthetic
test repositories that contain controlled duplication patterns.

### Synthetic Repository Structure

Each language's test corpus contains 7 files with deterministic duplication patterns:

| File Pattern | Purpose | Expected Clones |
|-------------|---------|-----------------|
| `no_duplication.*` / `NoDuplication.*` | Clean code with zero duplicates | 0 clones, 0-5% duplication |
| `light_duplication.*` / `LightDuplication.*` | Borderline duplication near threshold | 0-2 clones, 5-25% duplication |
| `heavy_duplication.*` / `HeavyDuplication.*` | Obvious multi-block duplication | 2-5 clones, 30-60% duplication |
| `cross_file_a.*` / `CrossFileA.*` | Source side of cross-file duplication pair | 0-2 clones, 0-50% duplication |
| `cross_file_b.*` / `CrossFileB.*` | Target side of cross-file duplication pair | 0-2 clones, 0-50% duplication |
| `semantic_dup_identifiers.*` | Same logic, renamed variables | 0-1 standard / 1-4 semantic |
| `semantic_dup_literals.*` | Same logic, different constants | 0-1 standard / 1-4 semantic |

### Ground Truth Files

Seven language-specific ground truth files, all following the same schema:

| File | Language | File Count |
|------|----------|-----------|
| `evaluation/ground-truth/python.json` | Python | 7 files |
| `evaluation/ground-truth/javascript.json` | JavaScript | 7 files |
| `evaluation/ground-truth/typescript.json` | TypeScript | 7 files |
| `evaluation/ground-truth/csharp.json` | C# | 7 files |
| `evaluation/ground-truth/java.json` | Java | 7 files |
| `evaluation/ground-truth/go.json` | Go | 7 files |
| `evaluation/ground-truth/rust.json` | Rust | 7 files |

**Total:** 49 files across 7 languages, each with defined expectations.

### Ground Truth Schema

Each file follows this structure:

```json
{
  "language": "python",
  "version": "1.0",
  "description": "Ground truth for Python synthetic duplication test files (PMD CPD)",
  "files": {
    "heavy_duplication.py": {
      "expected_clone_count": 2,
      "expected_clone_range": [2, 5],
      "duplication_percentage_range": [30, 60],
      "description": "Heavy duplication with multiple duplicated blocks"
    },
    "semantic_dup_identifiers.py": {
      "expected_clones_standard": {
        "count": 0,
        "count_range": [0, 1]
      },
      "expected_clones_semantic": {
        "count": 2,
        "count_range": [1, 4],
        "requires_ignore_identifiers": true
      },
      "description": "Same logic with different variable names - requires semantic mode"
    }
  },
  "cross_file_expectations": {
    "cross_file_a_b": {
      "expected_cross_file_clones": 4,
      "expected_cross_file_clone_range": [2, 6],
      "files": ["cross_file_a.py", "cross_file_b.py"],
      "description": "Duplicated order/invoice calculation functions"
    }
  }
}
```

### Expected Value Formats

| Field | Type | Example | Used By |
|-------|------|---------|---------|
| `expected_clone_count` | integer | `2` | Reference value, not directly checked |
| `expected_clone_range` | [min, max] | `[2, 5]` | AC-1 (heavy detection), AC-2 (range check) |
| `duplication_percentage_range` | [min, max] | `[30, 60]` | AC-3 (percentage accuracy) |
| `expected_clones_standard.count_range` | [min, max] | `[0, 1]` | Baseline for non-semantic mode |
| `expected_clones_semantic.count_range` | [min, max] | `[1, 4]` | AC-6, AC-7 (semantic detection) |
| `expected_clones_semantic.requires_ignore_identifiers` | boolean | `true` | AC-6 gate condition |
| `expected_clones_semantic.requires_ignore_literals` | boolean | `true` | AC-7 gate condition |
| `expected_cross_file_clone_range` | [min, max] | `[2, 6]` | AC-5 (cross-file detection) |
| `is_cross_file_source` | boolean | `true` | Documentation/linking |
| `cross_file_partner` | string | `"cross_file_b.py"` | Documentation/linking |

### Cross-File Expectations

Each language defines one cross-file duplication pair (`cross_file_a_b`) with:
- 2-6 expected cross-file clones across the pair
- Both files listed for bidirectional matching
- Description of the duplicated logic (order/invoice calculation functions)

---

## LLM Judge Details

### Architecture

All judges extend the PMD CPD `BaseJudge` (in `evaluation/llm/judges/base.py`), which
itself extends the shared `SharedBaseJudge` from `src/shared/evaluation/`. The base class
provides:

- Automatic output directory resolution (checks `evaluation/results/`, then most recent
  `outputs/*/output.json`)
- Envelope unwrapping via `shared.output_management.unwrap_envelope`
- Test mode support (`PMD_CPD_TEST_MODE` environment variable returns mock responses)
- Prompt template loading from `evaluation/llm/prompts/{dimension_name}.md`
- Observability logging via the shared tracing infrastructure

### Judge Pipeline

Each judge follows the same execution pipeline:

1. **Evidence collection** -- `collect_evidence()` loads tool output and extracts
   dimension-specific data points
2. **Prompt construction** -- The `{{ evidence }}` placeholder in the prompt template is
   replaced with the collected evidence (JSON-formatted)
3. **LLM invocation** -- Claude evaluates the evidence against the rubric
4. **Response parsing** -- The JSON response is parsed into a `JudgeResult` with score,
   confidence, reasoning, evidence_cited, recommendations, and sub_scores

### Duplication Accuracy Judge (35%)

**Dimension name:** `duplication_accuracy`

**Purpose:** Evaluates whether detected clones are genuine duplicates, whether important
duplicates are missed, and whether line counts and locations are accurate.

**Sub-dimensions:**

| Sub-Dimension | Internal Weight | Evaluation Focus |
|---------------|-----------------|------------------|
| genuine_clones | 40% | Do detected code fragments represent actual duplicated logic? Are clones meaningful (not trivial patterns like imports)? |
| false_positive_rate | 30% | Are there clones detected that should not be? Are clean `no_duplication` files showing unexpected clones? |
| location_accuracy | 30% | Do line numbers and file paths look correct? Are token counts proportional to line counts? |

**Scoring rubric (1-5):**

| Score | Criteria |
|-------|----------|
| 5 | All detected clones are genuine, no false positives, accurate line counts |
| 4 | Most clones are genuine with minor inaccuracies |
| 3 | Some false positives or missed duplicates |
| 2 | Significant accuracy issues |
| 1 | Mostly incorrect results |

**Evidence collected:**
- `analysis_summary`: total_files, total_clones, duplication_percentage
- `sample_duplications` (up to 5): clone_id, lines, tokens, occurrence count, first 200
  chars of code_fragment
- `file_metrics` (up to 10): path, total_lines, duplicate_lines, duplication_percentage
- `evaluation_mode`: synthetic or real_world
- `synthetic_baseline` / `interpretation_guidance`: Context for real-world evaluations

**Prompt template:** `evaluation/llm/prompts/duplication_accuracy.md`

### Semantic Detection Judge (25%)

**Dimension name:** `semantic_detection`

**Purpose:** Evaluates CPD's ability to detect Type 2 clones -- code with identical logic
but different variable names or literal values. This is CPD's unique strength over
string-based duplication tools.

**Sub-dimensions:**

| Sub-Dimension | Internal Weight | Evaluation Focus |
|---------------|-----------------|------------------|
| identifier_detection | 35% | Does `--ignore-identifiers` mode detect clones with renamed variables? Are `semantic_dup_identifiers` files showing expected clone counts? |
| literal_detection | 35% | Does `--ignore-literals` mode detect clones with different constants? Are `semantic_dup_literals` files showing expected clone counts? |
| type2_clone_detection | 30% | Overall assessment of near-duplicate detection. Comparison with what a string-based tool would find. |

**Scoring rubric (1-5):**

| Score | Criteria |
|-------|----------|
| 5 | Accurately detects Type 2 clones with renamed variables and different literals |
| 4 | Detects most semantic duplicates with few misses |
| 3 | Some semantic detection capability |
| 2 | Limited semantic detection |
| 1 | Only detects exact matches |

**Evidence collected:**
- `semantic_mode_enabled`: boolean
- `ignore_identifiers`: boolean (from analysis metadata)
- `ignore_literals`: boolean (from analysis metadata)
- `semantic_files_detected`: list of files with "semantic" in path, including
  duplicate_blocks and duplication_percentage
- `standard_vs_semantic`: comparison data when available

**Prompt template:** `evaluation/llm/prompts/semantic_detection.md`

### Cross-File Detection Judge (20%)

**Dimension name:** `cross_file_detection`

**Purpose:** Evaluates how well CPD detects and reports duplicates that span multiple
files, and whether the file relationships are properly linked and reported.

**Sub-dimensions:**

| Sub-Dimension | Internal Weight | Evaluation Focus |
|---------------|-----------------|------------------|
| detection_rate | 40% | Are `cross_file_a`/`cross_file_b` test files showing expected clones? Is the cross_file_clone_count reasonable? |
| file_linking | 30% | Are `files_involved` lists accurate? Do occurrences properly identify both source files? |
| reporting_clarity | 30% | Is it clear which parts of each file are duplicated? Would a developer know what to refactor? |

**Scoring rubric (1-5):**

| Score | Criteria |
|-------|----------|
| 5 | All cross-file clones detected with clear file relationships |
| 4 | Most cross-file clones detected with useful linking |
| 3 | Basic cross-file detection works |
| 2 | Misses many cross-file duplicates |
| 1 | Fails to detect cross-file clones |

**Evidence collected:**
- `cross_file_clone_count`: total number of clones spanning multiple files
- `total_clone_count`: total number of all clones
- `cross_file_clones` (up to 5): clone_id, lines, files_involved list, occurrence_count
- `cross_file_test_files`: files with "cross_file" in path, including duplicate_blocks
  and duplication_percentage

**Prompt template:** `evaluation/llm/prompts/cross_file_detection.md`

### Actionability Judge (20%)

**Dimension name:** `actionability`

**Purpose:** Evaluates whether the duplication reports are useful for developers to take
action -- do they provide enough context to understand and prioritize refactoring?

**Sub-dimensions:**

| Sub-Dimension | Internal Weight | Evaluation Focus |
|---------------|-----------------|------------------|
| location_clarity | 35% | Are file paths and line numbers clearly provided? Can a developer jump directly to the duplicated code? |
| context_provided | 35% | Is there a code fragment showing the duplication? Is there enough context to understand it? |
| prioritization_support | 30% | Do summaries help identify the most important duplicates? Are statistics useful for understanding overall code quality? |

**Scoring rubric (1-5):**

| Score | Criteria |
|-------|----------|
| 5 | Reports clearly guide refactoring with specific locations and context |
| 4 | Reports are useful with good location info and context |
| 3 | Basic actionable information provided |
| 2 | Hard to act on the reports |
| 1 | Reports are not actionable |

**Evidence collected:**
- `report_structure`: booleans for has_metadata, has_summary, has_files, has_duplications,
  has_statistics
- `metadata_available`: booleans for version, cpd_version, min_tokens, analyzed_at,
  elapsed_seconds
- `summary_quality`: booleans for has_total_files, has_total_clones,
  has_duplication_percentage, has_cross_file_clones
- `sample_clone_details` (up to 3): has_clone_id, has_lines, has_tokens,
  has_code_fragment, occurrence_fields list

**Prompt template:** `evaluation/llm/prompts/actionability.md`

---

## Evidence Collection

### Programmatic Evidence

Every `CheckResult` includes a structured `evidence` dictionary. Evidence varies by check
type but generally follows these patterns:

| Check Category | Evidence Pattern |
|----------------|-----------------|
| Accuracy | `{"files": [{"file": "...", "actual": N, "expected_range": [lo, hi], "status": "..."}]}` |
| Coverage | `{"files": [{"file": "...", "status": "found|not_found"}]}` |
| Edge Cases | `{"errors": [...]}` or `{"issues": [...]}` with failure details |
| Performance | `{"elapsed_seconds": N, "thresholds": {...}}` or `{"files_per_second": N}` |

### LLM Judge Evidence

Each judge's `collect_evidence()` method produces a dictionary that is serialized to JSON
and injected into the prompt template via the `{{ evidence }}` placeholder. The evidence
is also stored in the evaluation output for auditability.

---

## Running Evaluations

### Programmatic Evaluation

```bash
# From src/tools/pmd-cpd/

# Full evaluation with verbose output (28 checks)
make evaluate

# Quick evaluation (24 checks, skips PF-1 to PF-4)
make evaluate-quick

# JSON-only output (no human-readable report)
make evaluate-json

# Direct script invocation
.venv/bin/python scripts/evaluate.py \
    --analysis outputs/cpd-test-run/output.json \
    --ground-truth evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json
```

### LLM Evaluation

```bash
# Run all 4 LLM judges
make evaluate-llm

# Combined programmatic + LLM evaluation
make evaluate-combined
```

The default LLM model is `opus-4.5`, configurable via `LLM_MODEL`:

```bash
make evaluate-llm LLM_MODEL=sonnet
```

### Analysis Modes

Standard and semantic analysis produce different outputs, affecting checks AC-6 and AC-7:

```bash
# Standard token-based detection
make analyze

# Semantic mode (enables identifier and literal ignoring)
make analyze-semantic
```

### Evaluation Output Artifacts

All outputs are written to `evaluation/results/` (overwriting previous runs):

| File | Contents |
|------|----------|
| `evaluation/results/evaluation_report.json` | Full programmatic evaluation report with all 28 checks |
| `evaluation/scorecard.json` | Structured scorecard with dimensions, scores, and thresholds |
| `evaluation/scorecard.md` | Human-readable markdown scorecard |
| `evaluation/results/llm_evaluation.json` | LLM judge results (when `evaluate-llm` is run) |
| `evaluation/results/combined_evaluation.json` | Combined results (when `evaluate-combined` is run) |

### CI Exit Code

The evaluation script exits with code 1 if `report.score < 0.7`, enforcing a minimum
70% pass rate (PASS threshold) in CI pipelines.

---

## Extending the Evaluation

### Adding a New Programmatic Check

1. Identify the appropriate category module in `scripts/checks/`:
   - `accuracy.py` for clone detection correctness
   - `coverage.py` for language/file coverage
   - `edge_cases.py` for boundary conditions
   - `performance.py` for speed/resource checks
2. Implement the check function following the pattern:
   ```python
   def _xx_N_check_name(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
       """XX-N: Description of what this check validates."""
       # ... validation logic ...
       return CheckResult(
           check_id="XX-N",
           name="Check name",
           category=CheckCategory.CATEGORY,
           passed=score >= threshold,
           score=score,
           message=f"Result summary",
           evidence={...}
       )
   ```
3. Add the function call to the corresponding `run_*_checks()` function.
4. Update ground truth files if new expected values are needed.
5. Run `make evaluate` to verify the new check.

### Adding a New LLM Judge

1. Create a new judge class in `evaluation/llm/judges/` extending `BaseJudge`.
2. Implement `dimension_name`, `weight`, `collect_evidence()`, and optionally
   `get_default_prompt()`.
3. Create a prompt template in `evaluation/llm/prompts/{dimension_name}.md` with the
   `{{ evidence }}` placeholder.
4. Register the judge in `evaluation/llm/judges/__init__.py`.
5. Update the LLM evaluation script to include the new judge.

### Updating Ground Truth

Ground truth files should be updated when:
- New synthetic test files are added to `eval-repos/synthetic/`
- Expected ranges need adjustment based on PMD version changes
- New languages are added to the supported set

Each ground truth file is versioned (`"version": "1.0"`) and should be incremented
when expectations change.

---

## Confidence Requirements

### LLM Judge Confidence

Each judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence -- reliable score |
| 0.7-0.9 | Moderate confidence -- some uncertainty |
| < 0.7 | Low confidence -- manual review needed |

### Programmatic Check Robustness

Programmatic checks degrade gracefully when ground truth data is absent:

- If no ground truth files exist for a category, checks return `passed=True` with
  `score=1.0` and a message indicating no expectations were available.
- If no files match a naming pattern (e.g., no `*heavy*` files), the check passes with
  a neutral score rather than failing.
- Semantic checks (AC-6, AC-7) return `score=0.5` when the corresponding mode flag is
  not active, avoiding penalization for standard-mode runs.

---

## References

- [PMD CPD Documentation](https://pmd.github.io/latest/pmd_userdocs_cpd.html)
- [Clone Detection Taxonomy (Roy & Cordy, 2007)](https://research.cs.queensu.ca/TechReports/Reports/2007-541.pdf) -- Type 1/2/3 clone classification
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
- Project Caldera shared evaluation infrastructure: `src/shared/evaluation/base_judge.py`
