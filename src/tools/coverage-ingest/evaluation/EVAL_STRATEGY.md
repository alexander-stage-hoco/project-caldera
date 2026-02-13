# Evaluation Strategy: coverage-ingest

This document describes the evaluation methodology for the coverage-ingest tool, which parses multi-format test coverage data (LCOV, Cobertura, JaCoCo, Istanbul) into a normalized representation suitable for persistence, aggregation, and risk analysis.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation to achieve both precision and nuance across the tool's core responsibilities: parsing accuracy, normalization correctness, format coverage, edge case handling, and performance.

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- validates invariants, parser correctness, and performance |
| LLM Judges | 40% | Semantic understanding of cross-format consistency, risk tier quality, gap actionability |

**Why a hybrid approach?** Programmatic checks catch deterministic failures (wrong line counts, broken invariants, invalid paths) with zero ambiguity. LLM judges evaluate higher-order qualities that resist mechanical specification: whether risk tiers are reasonable given a codebase profile, whether gap analysis output is actionable enough for a developer to know where to add tests, and whether parsers produce genuinely equivalent output across formats for the same underlying coverage data.

The evaluation supports two modes:

- **Synthetic mode** (default): Runs against hand-crafted ground truth scenarios with known expected values. Applies strict pass/fail criteria.
- **Real-world mode**: Runs against actual repository coverage data. LLM judges use a relaxed rubric focused on reasonableness and consistency rather than exact value matching. When a synthetic baseline exists from a prior run, judges use it as calibration context.

---

## Dimension Summary

### Programmatic Dimensions (60% of combined score)

| Category | Weight | Checks | Purpose |
|----------|--------|--------|---------|
| Parser Accuracy | 35% | PA-1 to PA-12 | Validate that parsed coverage metrics match ground truth |
| Normalization Correctness | 25% | NC-1 to NC-8 | Validate data invariants, path normalization, percentage consistency |
| Format Coverage | 20% | FC-1 to FC-6 | Validate format detection and parsing for all 4 formats |
| Edge Case Handling | 10% | EC-1 to EC-8 | Validate behavior on boundary inputs (empty, zero, 100%, unicode, malformed) |
| Performance | 10% | PF-1 to PF-4 | Validate parsing speed and memory usage |

### LLM Judge Dimensions (40% of combined score)

| Judge | Weight | Focus |
|-------|--------|-------|
| Parser Accuracy | 25% | Semantic accuracy of metric extraction across formats |
| Cross-Format Consistency | 25% | Equivalent data across formats produces identical output |
| Gap Actionability | 25% | Coverage gaps are specific enough for immediate developer action |
| Risk Tier Quality | 25% | Coverage percentages are correctly classified into CRITICAL/HIGH/MEDIUM/LOW tiers |

---

## Check Catalog

### Parser Accuracy Checks (PA-1 to PA-12)

These checks validate that each of the 4 format parsers correctly extracts line counts, branch counts, and coverage percentages. Each check instantiates its parser, feeds it known input, and compares against ground truth values.

| ID | Name | Category | Severity | Pass Criteria | Evidence Collected |
|----|------|----------|----------|---------------|-------------------|
| PA-1 | LCOV line counts | accuracy | critical | `lines_total == 10`, `lines_covered == 7` from basic LCOV input | Parsed file count, lines_total, lines_covered |
| PA-2 | LCOV branch counts | accuracy | critical | `branches_total == 4`, `branches_covered == 2` from BRF/BRH records | branches_total, branches_covered |
| PA-3 | LCOV coverage percentage | accuracy | high | `line_coverage_pct == 70.0` (7/10 * 100) | Expected vs actual percentage, tolerance < 0.01% |
| PA-4 | Cobertura line rates | accuracy | critical | `lines_total == 5`, `lines_covered == 4` from XML with hit counts | Parsed line data from `<line>` elements |
| PA-5 | Cobertura branch rates | accuracy | high | `branch_coverage_pct is None` when only `branch-rate` attribute exists without condition-coverage | Null check on branch_coverage_pct |
| PA-6 | Cobertura coverage pct | accuracy | high | `line_coverage_pct == 80.0` from `line-rate="0.8"` | Coverage percentage from rate attribute |
| PA-7 | JaCoCo instruction counts | accuracy | critical | `lines_total == 10`, `lines_covered == 7` from LINE counter (missed=3, covered=7) | Parsed counter data |
| PA-8 | JaCoCo branch counts | accuracy | critical | `branches_total == 8`, `branches_covered == 6` from BRANCH counter | Parsed branch counter data |
| PA-9 | JaCoCo coverage pct | accuracy | high | `line_coverage_pct == 70.0` from counter values | Calculated percentage |
| PA-10 | Istanbul statement counts | accuracy | critical | `lines_total == 3`, `lines_covered == 2` from statement map `{"0": 1, "1": 1, "2": 0}` | Statement map parsing |
| PA-11 | Istanbul branch counts | accuracy | critical | `branches_total == 2`, `branches_covered == 1` from branch map `{"0": [1, 0]}` | Branch array parsing |
| PA-12 | Istanbul coverage pct | accuracy | high | `line_coverage_pct == round((2/3)*100, 2)` = 66.67% | Calculated percentage from statement counts |

The `checks/accuracy.py` module also provides ground-truth-based variants of these checks (functions `check_pa1_lcov_line_counts()` through `check_pa12_istanbul_coverage_pct()`) that load expected values from format-specific JSON files under `evaluation/ground-truth/<format>/<scenario>.json`. These produce `CheckResult` objects with `expected` and `actual` fields for detailed comparison.

### Normalization Correctness Checks (NC-1 to NC-8)

These checks validate structural invariants and path normalization rules that must hold across all formats and scenarios. The `checks/output_quality.py` module loads all ground truth files and verifies each one.

| ID | Name | Category | Severity | Pass Criteria | Evidence Collected |
|----|------|----------|----------|---------------|-------------------|
| NC-1 | covered <= total invariant | normalization | critical | `lines_covered <= lines_total` for every file across all ground truth | Count of violations, file paths of violators |
| NC-2 | branches covered <= total | normalization | critical | `branches_covered <= branches_total` for every file where branch data is present | Count of violations, file paths |
| NC-3 | coverage pct 0-100 | normalization | high | `0 <= line_coverage_pct <= 100` and `0 <= branch_coverage_pct <= 100` for all files | Out-of-range values found |
| NC-4 | pct matches calculation | normalization | high | `abs(line_coverage_pct - (lines_covered/lines_total)*100) < 0.01` for all files with `lines_total > 0` | Mismatched calculations |
| NC-5 | paths repo-relative | normalization | high | No `relative_path` starts with `/` | Absolute paths found |
| NC-6 | no absolute paths | normalization | high | No paths start with `/` or contain Windows drive letters (`C:`) | Drive letter or absolute path violations |
| NC-7 | POSIX separators | normalization | medium | No `relative_path` contains backslash (`\`) | Backslash paths found |
| NC-8 | cross-format equivalence | normalization | medium | Cross-format ground truth file exists at `evaluation/ground-truth/cross-format/equivalence.json` and has valid structure (`formats`, `equivalences`, or `test_cases` key present) | Structure validation result |

### Format Coverage Checks (FC-1 to FC-6)

These checks validate that all 4 format parsers can detect and parse their respective formats. Each check instantiates the parser and calls its `detect()` or `parse()` method against format-specific content.

| ID | Name | Category | Severity | Pass Criteria | Evidence Collected |
|----|------|----------|----------|---------------|-------------------|
| FC-1 | LCOV detection | format_coverage | critical | `LcovParser().detect(lcov_content)` returns `True` | Detection boolean |
| FC-2 | Cobertura detection | format_coverage | critical | `CoberturaParser().detect(cobertura_content)` returns `True` | Detection boolean |
| FC-3 | JaCoCo detection | format_coverage | critical | `JacocoParser().detect(jacoco_content)` returns `True` | Detection boolean |
| FC-4 | Istanbul detection | format_coverage | critical | `IstanbulParser().detect(istanbul_content)` returns `True` | Detection boolean |
| FC-5 | format override | format_coverage | high | All 4 parsers return non-empty result lists when parsing their own format content | Per-parser result count |
| FC-6 | invalid format rejected | format_coverage | medium | `LcovParser().parse('<invalid xml>')` either returns a list (graceful handling) or raises `ValueError` (explicit rejection); no unexpected exceptions | Exception type or return type |

### Edge Case Checks (EC-1 to EC-8)

These checks validate behavior on boundary and unusual inputs that parsers must handle gracefully.

| ID | Name | Category | Severity | Pass Criteria | Evidence Collected |
|----|------|----------|----------|---------------|-------------------|
| EC-1 | empty file handled | edge_case | medium | `LcovParser().parse("")` returns `[]` (empty list) | Return value type and length |
| EC-2 | zero coverage handled | edge_case | high | `lines_covered == 0` and `line_coverage_pct == 0.0` for `LH:0` input | Parsed coverage values |
| EC-3 | 100% coverage handled | edge_case | high | `line_coverage_pct == 100.0` for `LH:10` / `LF:10` input | Parsed coverage percentage |
| EC-4 | unicode paths handled | edge_case | medium | Cyrillic characters preserved in `relative_path` (e.g., `"тест"` substring check) | Parsed path string |
| EC-5 | deep paths handled | edge_case | low | 20-level deep path (`a/a/.../test.py`) parses to exactly 1 result | Result count |
| EC-6 | special chars handled | edge_case | low | Path with spaces and parentheses (`test file (1).py`) parses to exactly 1 result | Result count |
| EC-7 | malformed XML rejected | edge_case | high | `CoberturaParser().parse("<unclosed>")` raises `ValueError` | Exception type |
| EC-8 | required fields validated | edge_case | medium | `FileCoverage` dataclass accepts all required fields without error | Construction success |

### Performance Checks (PF-1 to PF-4)

These checks validate parsing speed for different input sizes.

| ID | Name | Category | Severity | Threshold | Evidence Collected |
|----|------|----------|----------|-----------|-------------------|
| PF-1 | small file < 100ms | performance | high | Parse 100 LCOV records in < 100ms | Elapsed time in milliseconds |
| PF-2 | medium file < 500ms | performance | medium | Parse 1,000 LCOV records in < 500ms | Elapsed time in milliseconds |
| PF-3 | large file < 5s | performance | medium | Parse 10,000+ records in < 5s (skipped in quick mode) | Elapsed time or "Skipped" |
| PF-4 | memory < 500MB | performance | low | Peak memory usage below 500MB (skipped in quick mode) | Memory usage or "Skipped" |

---

## Scoring

### Programmatic Score Calculation

The programmatic evaluator in `scripts/evaluate.py` calculates scores as follows:

```python
# Count passing checks
passed = sum(1 for r in all_results if r.passed)
total = len(all_results)

# Score is a simple percentage
score = (passed / total) * 100  # 0-100 scale
```

The evaluator runs checks grouped by 5 weighted categories:

```python
categories = [
    ("Parser Accuracy (35%)",          run_parser_accuracy_checks),
    ("Normalization Correctness (25%)", run_normalization_checks),
    ("Format Coverage (20%)",          run_format_coverage_checks),
    ("Edge Case Handling (10%)",       run_edge_case_checks),
    ("Performance (10%)",              run_performance_checks),
]
```

The category weights (35%, 25%, 20%, 10%, 10%) indicate relative importance but the current scoring implementation uses a flat pass rate across all 38 checks (12 PA + 8 NC + 6 FC + 8 EC + 4 PF).

### LLM Score Calculation

Each LLM judge produces a score on a 1-5 scale. The judge registry in `evaluation/llm/judges/__init__.py` defines equal weights:

```python
JUDGES = {
    "risk_tier_quality":         (RiskTierQualityJudge,         0.25),
    "gap_actionability":         (GapActionabilityJudge,        0.25),
    "cross_format_consistency":  (CrossFormatConsistencyJudge,  0.25),
    "parser_accuracy":           (ParserAccuracyJudge,          0.25),
}
```

The weighted LLM score is:

```python
llm_score = sum(judge_score * judge_weight for judge_score, judge_weight in judge_results)
# = 0.25 * parser_accuracy + 0.25 * cross_format + 0.25 * gap_actionability + 0.25 * risk_tier
```

### Combined Score Calculation

The combined score normalizes the programmatic percentage to the 1-5 scale and blends with the LLM score:

```python
# Normalize programmatic score (0-100%) to 1-5 scale
programmatic_normalized = 1 + (programmatic_score / 100) * 4  # 0% -> 1.0, 100% -> 5.0

# Weighted combination
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

### Ground Truth Assertion Cap

Each LLM judge runs `run_ground_truth_assertions()` before scoring. If assertions fail, the LLM score is capped:

```python
gt_passed, gt_failures = self.run_ground_truth_assertions()

# Cap score if assertions failed
if not gt_passed:
    score = min(llm_score, 2)  # Max score of 2 if GT fails
```

This prevents high LLM scores when fundamental data integrity checks fail.

---

## Decision Thresholds

### Programmatic Decision (percentage-based)

| Decision | Score | Interpretation |
|----------|-------|----------------|
| STRONG_PASS | >= 95% | Excellent, production-ready parsing |
| PASS | >= 85% | Good, minor improvements needed |
| WEAK_PASS | >= 75% | Acceptable with caveats |
| FAIL | < 75% | Significant parsing or normalization issues |

These thresholds are implemented directly in `scripts/evaluate.py`:

```python
if score >= 95:
    decision = "STRONG_PASS"
elif score >= 85:
    decision = "PASS"
elif score >= 75:
    decision = "WEAK_PASS"
else:
    decision = "FAIL"
```

### Combined Decision (1-5 scale)

When both programmatic and LLM evaluations are combined, the decision uses the normalized scale:

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent, production-ready |
| PASS | >= 3.5 | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 | Acceptable with caveats |
| FAIL | < 3.0 | Significant issues |

---

## Ground Truth

### Methodology

Ground truth files are hand-crafted JSON scenarios stored in `evaluation/ground-truth/`, organized by format and scenario. Each scenario defines exact expected values for a known coverage input.

### Generation Process

1. **Define scenario**: Choose a format (LCOV, Cobertura, JaCoCo, Istanbul) and a specific coverage situation (simple, multi-file, branches, edge-cases, high-gaps).
2. **Compute expected values**: Manually calculate the expected `lines_total`, `lines_covered`, `lines_missed`, `line_coverage_pct`, `branches_total`, `branches_covered`, and `branch_coverage_pct` for each file in the scenario.
3. **Cross-validate**: For cross-format equivalence tests, ensure the same logical coverage data produces identical expected values regardless of source format.
4. **Record invariants**: Document which data integrity invariants must hold (covered <= total, percentage in 0-100, etc.).

### Ground Truth File Structure

Each format-specific ground truth file follows this schema:

```json
{
  "metadata": {
    "format": "lcov|cobertura|jacoco|istanbul",
    "scenario": "simple|multi-file|branches|edge-cases|high-gaps|counters",
    "description": "Human-readable description of this scenario",
    "created": "2026-02-09"
  },
  "expected": {
    "file_count": 1,
    "files": [
      {
        "relative_path": "src/main.py",
        "lines_total": 10,
        "lines_covered": 8,
        "lines_missed": 2,
        "line_coverage_pct": 80.0,
        "branches_total": null,
        "branches_covered": null,
        "branch_coverage_pct": null
      }
    ]
  }
}
```

### Ground Truth File Inventory

The ground truth corpus contains 20 files across 5 directories:

| Directory | Files | Scenarios |
|-----------|-------|-----------|
| `ground-truth/lcov/` | 5 | `simple`, `multi-file`, `branches`, `edge-cases`, `high-gaps` |
| `ground-truth/cobertura/` | 4 | `simple`, `multi-package`, `branches`, `edge-cases`, `high-gaps` |
| `ground-truth/jacoco/` | 4 | `simple`, `multi-module`, `counters`, `edge-cases` |
| `ground-truth/istanbul/` | 4 | `simple`, `multi-file`, `branches`, `edge-cases` |
| `ground-truth/cross-format/` | 1 | `equivalence` (5 test cases comparing outputs across all 4 formats) |
| `ground-truth/` | 1 | `synthetic.json` (consolidated index of all scenarios with invariants and thresholds) |

### Synthetic Consolidated Index

The top-level `synthetic.json` provides a manifest of all format test cases, along with global invariants and evaluation thresholds:

```json
{
  "invariants": [
    "lines_covered <= lines_total",
    "branches_covered <= branches_total (when present)",
    "0 <= line_coverage_pct <= 100",
    "0 <= branch_coverage_pct <= 100 (when present)",
    "All paths are repo-relative POSIX format"
  ],
  "evaluation_thresholds": {
    "STRONG_PASS": 95,
    "PASS": 85,
    "WEAK_PASS": 75,
    "FAIL": 0
  }
}
```

### Cross-Format Equivalence Tests

The `cross-format/equivalence.json` file defines 5 test cases that verify consistent output across formats:

| Test Case | Description | Expected Common Values |
|-----------|-------------|----------------------|
| `simple_file_equivalence` | Same file should have identical coverage stats | `lines_total: 10`, `lines_covered: 8`, `line_coverage_pct: 80.0` |
| `multi_file_equivalence` | Multi-file scenarios should produce same file counts | `file_count: 3` |
| `branch_coverage_equivalence` | Branch coverage should be consistent | `branches_total: 8`, `branches_covered: 6`, `branch_coverage_pct: 75.0` |
| `zero_coverage_equivalence` | 0% coverage handled consistently | `lines_covered: 0`, `line_coverage_pct: 0.0` |
| `full_coverage_equivalence` | 100% coverage handled consistently | `line_coverage_pct: 100.0` |

Each test also defines 5 validation rules: path normalization, POSIX separators, covered-le-total invariant, missed-equals-diff invariant, and percentage range.

### Edge Case Coverage

The edge-case ground truth scenarios (present for all 4 formats) test these situations:

| Edge Case | Expected Behavior |
|-----------|-------------------|
| Empty file (0 lines) | `lines_total: 0`, `line_coverage_pct: null` |
| 0% coverage | `lines_covered: 0`, `line_coverage_pct: 0.0` |
| 100% coverage | `lines_covered == lines_total`, `line_coverage_pct: 100.0` |
| Unicode paths | Cyrillic characters preserved in `relative_path` |
| Spaces and special characters | Spaces and parentheses in paths handled |
| Deep nesting | 10+ level directory nesting (e.g., `a/b/c/d/e/f/g/h/i/j/deep_nested.py`) |

### High-Gap Scenarios

High-gap ground truth files (`high-gaps.json`) provide files in the 25-50% coverage range to validate HIGH-risk tier classification:

- `src/service_a.py`: 25.0% coverage (HIGH/CRITICAL boundary)
- `src/service_b.py`: 35.0% coverage (mid-HIGH range)
- `src/service_c.py`: 45.0% coverage (HIGH/MEDIUM boundary)

---

## LLM Judge Details

### Parser Accuracy Judge (25%)

**File:** `evaluation/llm/judges/parser_accuracy.py`
**Prompt:** `evaluation/llm/prompts/parser_accuracy.md`

Evaluates whether coverage metrics are parsed correctly from each of the 4 formats. Collects per-format accuracy statistics and sample file data as evidence.

**Sub-Dimensions:**

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Line Metric Accuracy | 40% | Are `lines_total` and `lines_covered` extracted correctly? |
| Branch Metric Accuracy | 30% | Are `branches_total` and `branches_covered` extracted correctly? |
| Percentage Calculation | 30% | Is `line_coverage_pct` computed accurately (within 0.01%)? |

**Scoring Rubric (Synthetic Mode):**

| Score | Criteria |
|-------|----------|
| 5 | >= 99% accuracy across all 4 formats, all metrics correct |
| 4 | >= 95% accuracy, minor discrepancies in edge cases |
| 3 | >= 85% accuracy, some systematic errors in one format |
| 2 | >= 70% accuracy, significant parsing issues |
| 1 | < 70% accuracy, fundamental parsing problems |

**Scoring Rubric (Real-World Mode):**

| Score | Criteria |
|-------|----------|
| 5 | Metrics consistent and reasonable, all formats parse without error |
| 4 | Minor inconsistencies, but overall reasonable values |
| 3 | Some questionable values but formats parse correctly |
| 2 | Multiple parsing issues or inconsistent metrics |
| 1 | Parsing appears broken or produces invalid data |

**Heuristic Fallback:** When `use_llm=False`, the judge scores based on `overall_accuracy` percentage and `formats_covered` count:
- Score 5: >= 99% accuracy, 4 formats covered
- Score 4: >= 95% accuracy, >= 3 formats
- Score 3: >= 85% accuracy, >= 2 formats
- Score 2: >= 70% accuracy
- Score 1: < 70% accuracy

**Ground Truth Assertions:** Requires ground truth data for all 4 formats. Validates no negative values for `lines_total`, `lines_covered`, `branches_total`, `branches_covered`.

**Evidence Collected:**
- `format_accuracy`: Per-format check counts, pass counts, and accuracy percentages
- `sample_files`: Up to 10 sample file records with format and scenario metadata
- `total_checks` / `passed_checks` / `overall_accuracy`
- `programmatic_results`: Summary string from programmatic evaluation
- `synthetic_baseline` / `interpretation_guidance`: Context for real-world evaluation

### Cross-Format Consistency Judge (25%)

**File:** `evaluation/llm/judges/cross_format_consistency.py`
**Prompt:** `evaluation/llm/prompts/cross_format_consistency.md`

Evaluates whether all 4 format parsers produce consistent output for equivalent coverage data.

**Sub-Dimensions:**

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Metric Consistency | 40% | Same coverage data produces same metrics across formats |
| Path Normalization | 30% | Paths normalized consistently (no leading `/`, POSIX only) |
| Branch Handling | 30% | Branch coverage treated uniformly across formats |

**Scoring Rubric (Synthetic Mode):**

| Score | Criteria |
|-------|----------|
| 5 | Perfect consistency across all formats and test cases |
| 4 | Minor format-specific variations that do not affect usability |
| 3 | Mostly consistent with some explainable differences |
| 2 | Significant inconsistencies that affect data reliability |
| 1 | Inconsistent output that cannot be trusted across formats |

**Scoring Rubric (Real-World Mode):**

| Score | Criteria |
|-------|----------|
| 5 | Output format is consistent, paths normalized correctly |
| 4 | Minor format artifacts but core metrics are consistent |
| 3 | Some format-specific quirks but generally usable |
| 2 | Noticeable format-specific differences in output |
| 1 | Format-specific output that breaks downstream consumers |

**Heuristic Fallback:** Scores based on `consistency_rate` percentage and path normalization issues. Score deducted by 1 for any path normalization issues. Returns score 1 with 0.7 confidence if no cross-format tests exist.

**Ground Truth Assertions:** Requires cross-format ground truth data (`cross-format/equivalence.json`) with test cases and validation rules. Requires ground truth data for all 4 formats.

**Evidence Collected:**
- `consistency_results`: Per-test-case consistency analysis with inconsistencies
- `validation_rules`: Normalization rules from cross-format ground truth
- `consistency_rate`: Percentage of consistent tests
- `path_normalization_issues`: List of path violations (leading `/`, backslashes)
- `formats_evaluated`: List of formats checked (`["lcov", "cobertura", "jacoco", "istanbul"]`)

### Gap Actionability Judge (25%)

**File:** `evaluation/llm/judges/gap_actionability.py`
**Prompt:** `evaluation/llm/prompts/gap_actionability.md`

Evaluates whether coverage gap findings are specific enough for developers to take immediate action (locate files, understand scope of missing coverage, prioritize work).

**Sub-Dimensions:**

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Gap Clarity | 40% | Are coverage gaps clearly identified and ranked? |
| Path Specificity | 30% | Are file paths specific enough to locate? |
| Metric Precision | 30% | Are line/branch counts precise and accurate? |

**Scoring Rubric (Synthetic Mode):**

| Score | Criteria |
|-------|----------|
| 5 | Highly actionable with clear priorities, specific paths, precise metrics |
| 4 | Actionable with minor gaps in detail or prioritization |
| 3 | Somewhat actionable but requires additional investigation |
| 2 | Limited actionability due to vague paths or missing metrics |
| 1 | Not actionable -- cannot determine where to add tests |

**Scoring Rubric (Real-World Mode):**

| Score | Criteria |
|-------|----------|
| 5 | Output clearly shows what files need tests, with precise metrics |
| 4 | Most files have actionable data, minor gaps in some areas |
| 3 | Generally actionable but some files lack detail |
| 2 | Significant gaps in actionability for many files |
| 1 | Cannot determine action items from output |

**Heuristic Fallback:** Scores based on `actionability_score` percentage (derived from 5 boolean actionability metrics: has_file_paths, has_line_counts, has_coverage_pct, paths_are_specific, files_prioritized). Returns score 1 with 0.7 confidence if no files found.

**Ground Truth Assertions:** Validates that all files have non-empty paths, no files with zero total lines but non-null coverage percentage, and coverage percentage consistency within 1% of calculated value.

**Risk Tier Classification for Gaps:**

| Tier | Coverage Range | Priority |
|------|---------------|----------|
| CRITICAL | 0-25% | Immediate attention |
| HIGH | 25-50% | Significant risk |
| MEDIUM | 50-75% | Moderate risk |
| LOW | 75-100% | Acceptable |

**Evidence Collected:**
- `top_coverage_gaps`: Top 10 files sorted by lowest coverage (ascending)
- `actionability_metrics`: 5 boolean checks (file paths present, line counts valid, coverage pct present, paths specific, files prioritized)
- `actionability_score`: Percentage of actionability metrics passing
- `gap_distribution`: Count of files in each risk tier
- `branch_gap_analysis`: Files with branch coverage data and top 5 branch gaps (< 75%)
- `total_files_analyzed`: Count of files with coverage data

### Risk Tier Quality Judge (25%)

**File:** `evaluation/llm/judges/risk_tier_quality.py`
**Prompt:** `evaluation/llm/prompts/risk_tier_quality.md`

Evaluates whether coverage percentages are correctly classified into risk tiers using the defined thresholds.

**Sub-Dimensions:**

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Tier Accuracy | 50% | Are files assigned to the correct tier? |
| Boundary Handling | 30% | Are edge cases at tier boundaries handled correctly (e.g., exactly 25%, exactly 50%)? |
| Distribution Reasonableness | 20% | Is the tier distribution realistic for a codebase? |

**Tier Definitions:**

| Tier | Coverage Range | Boundary Behavior |
|------|---------------|-------------------|
| CRITICAL | `0 <= pct < 25` | Lower bound inclusive, upper bound exclusive |
| HIGH | `25 <= pct < 50` | Lower bound inclusive, upper bound exclusive |
| MEDIUM | `50 <= pct < 75` | Lower bound inclusive, upper bound exclusive |
| LOW | `75 <= pct <= 100` | Both bounds inclusive (100% is LOW) |

**Scoring Rubric (Synthetic Mode):**

| Score | Criteria |
|-------|----------|
| 5 | Perfect match to severity thresholds, all tiers correctly assigned |
| 4 | Minor discrepancies at tier boundaries (within 1% of threshold) |
| 3 | Generally appropriate classifications, few edge case errors |
| 2 | Significant misclassifications affecting prioritization |
| 1 | No correlation between coverage and tier assignment |

**Scoring Rubric (Real-World Mode):**

| Score | Criteria |
|-------|----------|
| 5 | Tier assignments consistent with coverage values, reasonable distribution |
| 4 | Minor edge cases, but overall reasonable tier assignments |
| 3 | Some questionable assignments but generally follows thresholds |
| 2 | Multiple tier assignments that do not match coverage values |
| 1 | Tier assignments appear random or broken |

**Heuristic Fallback:** Calculates `accuracy = (total_files - misclassification_count) / total_files * 100` and maps to score:
- Score 5: >= 95% accuracy
- Score 4: >= 85% accuracy
- Score 3: >= 70% accuracy
- Score 2: >= 50% accuracy
- Score 1: < 50% accuracy

**Ground Truth Assertions:** Requires at least one format with ground truth data. Validates all coverage percentages are in the 0-100 range.

**Evidence Collected:**
- `file_classifications`: Up to 20 file classification records with format, scenario, file path, coverage_pct, and assigned_tier
- `tier_distribution`: Per-tier statistics (count, percentage, coverage range)
- `tier_definitions`: Tier threshold definitions
- `misclassifications`: Files where assigned tier differs from expected tier
- `misclassification_count`: Total count of misclassifications

---

## LLM Judge Infrastructure

### Base Judge Architecture

All 4 judges inherit from `evaluation/llm/judges/base.py:BaseJudge`, which extends `shared.evaluation.BaseJudge` (the shared project-wide judge base class). The coverage-ingest `BaseJudge` adds:

- **Multi-format data loading**: `load_coverage_results()` scans output directories for JSON files organized by `source_format`.
- **Ground truth by format**: `load_ground_truth_by_format()` loads all ground truth files organized as `format -> scenario -> data`.
- **Programmatic summary injection**: `_build_programmatic_summary()` creates a text summary of programmatic check results for inclusion in LLM prompts.
- **Prompt building**: `build_prompt()` replaces `{{ placeholder }}` tokens with JSON-serialized evidence values. Raises `ValueError` if unresolved placeholders remain.
- **Error handling**: Graceful handling of empty responses, error responses from Claude, and unresolved prompt placeholders.
- **Synthetic pattern detection**: Extended `SYNTHETIC_PATTERNS` set including coverage-specific patterns (`simple`, `multi-file`, `branches`, `edge-cases`, `counters`, `equivalence`).

### Prompt Template Structure

Each judge has a Markdown prompt template at `evaluation/llm/prompts/<dimension_name>.md`. All templates share a common structure:

1. **Evaluation Context**: Interpretation guidance and synthetic baseline
2. **Evaluation Dimension**: Dimension name, weight, and description
3. **Background**: Domain-specific context about coverage formats and use cases
4. **Scoring Rubric**: Separate rubrics for synthetic mode (strict ground truth) and real-world mode (reasonableness)
5. **Sub-Dimensions**: Weighted sub-criteria with descriptions
6. **Evidence to Evaluate**: Placeholder-driven sections filled with collected evidence
7. **Evaluation Questions**: Specific questions the judge must answer
8. **Required Output Format**: JSON schema for structured response

Prompts use `{{ key }}` placeholders that are resolved by `build_prompt()` at evaluation time. Required placeholders vary by judge:

| Judge | Required Placeholders |
|-------|-----------------------|
| Parser Accuracy | `format_accuracy`, `sample_files`, `total_checks`, `passed_checks`, `overall_accuracy`, `programmatic_results`, `interpretation_guidance`, `synthetic_baseline`, `evaluation_mode` |
| Cross-Format Consistency | `consistency_results`, `validation_rules`, `path_normalization_issues`, `formats_evaluated`, `total_tests`, `consistent_tests`, `consistency_rate`, `programmatic_results`, `interpretation_guidance`, `synthetic_baseline`, `evaluation_mode` |
| Gap Actionability | `top_coverage_gaps`, `actionability_metrics`, `gap_distribution`, `branch_gap_analysis`, `total_files_analyzed`, `actionability_score`, `programmatic_results`, `interpretation_guidance`, `synthetic_baseline`, `evaluation_mode` |
| Risk Tier Quality | `tier_definitions`, `file_classifications`, `tier_distribution`, `misclassifications`, `total_files_analyzed`, `misclassification_count`, `programmatic_results`, `interpretation_guidance`, `synthetic_baseline`, `evaluation_mode` |

### Judge Response Format

All judges expect a JSON response with this structure:

```json
{
  "dimension": "<dimension_name>",
  "score": 1-5,
  "confidence": 0.0-1.0,
  "reasoning": "detailed explanation",
  "evidence_cited": ["specific evidence items"],
  "recommendations": ["improvement suggestions"],
  "sub_scores": {
    "<sub_dimension_1>": 1-5,
    "<sub_dimension_2>": 1-5,
    "<sub_dimension_3>": 1-5
  }
}
```

### Confidence Levels

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review needed |

Heuristic evaluations use fixed confidence levels (0.7-0.85 depending on judge and data availability).

---

## Evidence Collection

### Programmatic Evidence

Each `CheckResult` captures:

```python
@dataclass
class CheckResult:
    check_id: str     # e.g., "PA-1"
    name: str         # Human-readable name
    passed: bool      # Pass/fail
    message: str      # Explanation or error message
    expected: Any     # Expected value (accuracy checks only)
    actual: Any       # Actual value (accuracy checks only)
```

### LLM Evidence

Each judge's `collect_evidence()` method returns a dictionary that is serialized into the prompt. Evidence always includes:

- Format-specific ground truth data (loaded from JSON files)
- Programmatic evaluation results summary (if available)
- Evaluation mode indicator (`synthetic` or `real_world`)
- Synthetic baseline context (for real-world mode calibration)
- Interpretation guidance (strict for synthetic, relaxed for real-world)

---

## Running Evaluations

### Programmatic Evaluation

```bash
# From the coverage-ingest tool directory
cd src/tools/coverage-ingest

# Run programmatic evaluation
make evaluate

# Equivalent manual command
EVAL_OUTPUT_DIR=evaluation/results .venv/bin/python scripts/evaluate.py
```

### LLM Evaluation

```bash
# Run LLM evaluation with default model (opus-4.5)
make evaluate-llm

# Run with a different model
make evaluate-llm LLM_MODEL=sonnet

# Equivalent manual command
.venv/bin/python -m evaluation.llm.orchestrator \
    outputs/<run-id> \
    --output evaluation/results/llm_evaluation.json \
    --model opus-4.5
```

### Full Pipeline

```bash
# Setup, analyze, and evaluate
make all

# Or run everything individually:
make setup
make analyze COVERAGE_FILE=/path/to/coverage.xml
make evaluate
make evaluate-llm
```

### Evaluation Outputs

All evaluation artifacts are written to `evaluation/results/`:

```
evaluation/results/
  scorecard.md                # Human-readable programmatic scorecard
  evaluation_results.json     # Programmatic results (JSON)
  evaluation_report.json      # Programmatic results (JSON, alternate name)
  llm_evaluation.json         # LLM judge results (when run)
```

The JSON output format:

```json
{
  "timestamp": "2026-02-09T10:00:00+00:00",
  "score": 97.4,
  "decision": "STRONG_PASS",
  "summary": "37/38 checks passed (97.4%)",
  "passed": 37,
  "total": 38,
  "checks": [
    {
      "id": "PA-1",
      "name": "LCOV line counts",
      "passed": true,
      "message": "Basic LCOV parsing"
    }
  ]
}
```

---

## Extending the Evaluation

### Adding New Programmatic Checks

1. Add the check function to the appropriate module in `scripts/checks/`:
   - `accuracy.py` for parser accuracy checks (PA-series)
   - `coverage.py` for format coverage checks (FC-series)
   - `output_quality.py` for normalization checks (NC-series)
   - Or add a new module for a new check category.

2. Add the check to the module's `run_all_*_checks()` function.

3. If the check requires new ground truth data, add a JSON file under `evaluation/ground-truth/<format>/`.

4. Add a corresponding entry in `scripts/evaluate.py` if it belongs to a new category.

5. Run `make evaluate` to verify the check passes or fails as expected.

### Adding New LLM Judges

1. Create a new judge class in `evaluation/llm/judges/` extending `BaseJudge`.
2. Implement `dimension_name`, `weight`, `collect_evidence()`, `run_ground_truth_assertions()`, `run_heuristic_evaluation()`, and `get_default_prompt()`.
3. Create a prompt template in `evaluation/llm/prompts/<dimension_name>.md`.
4. Register the judge in `evaluation/llm/judges/__init__.py` by adding it to the `JUDGES` dictionary with its weight.
5. Ensure all weights in the `JUDGES` dictionary sum to 1.0.

### Adding New Ground Truth Scenarios

1. Create a new JSON file under `evaluation/ground-truth/<format>/<scenario>.json`.
2. Follow the established schema with `metadata` and `expected` sections.
3. Ensure all paths are repo-relative (no leading `/`, POSIX separators only).
4. Ensure all invariants hold: `lines_covered <= lines_total`, `0 <= line_coverage_pct <= 100`, etc.
5. If adding a cross-format scenario, update `cross-format/equivalence.json` with a new test case.
6. Update the `synthetic.json` manifest if adding a new format or modifying the test case index.

---

## References

- [LCOV Format Specification](https://ltp.sourceforge.net/coverage/lcov/geninfo.1.php)
- [Cobertura XML Schema](https://cobertura.github.io/cobertura/)
- [JaCoCo Report Format](https://www.jacoco.org/jacoco/trunk/doc/counters.html)
- [Istanbul Coverage JSON Format](https://istanbul.js.org/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
