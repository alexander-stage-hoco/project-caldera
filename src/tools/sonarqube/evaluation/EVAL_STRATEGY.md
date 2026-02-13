# Evaluation Strategy: SonarQube

This document describes the evaluation methodology for the SonarQube static analysis tool integration. It covers the hybrid programmatic + LLM-as-a-Judge approach used to validate analysis output quality, data completeness, and integration fitness.

## Evaluation Philosophy

The SonarQube evaluation employs a **hybrid** approach combining deterministic programmatic checks with semantic LLM-as-a-Judge evaluation. This mirrors the dual nature of SonarQube output validation: some properties (issue counts, metric presence, structure) are objectively verifiable, while others (issue classification accuracy, remediation usefulness, integration fit) benefit from contextual judgment.

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- validates structure, counts, coverage |
| LLM Judges | 40% | Semantic understanding -- validates classification accuracy, actionability, integration |

This split reflects a deliberate bias toward deterministic checks. SonarQube output is highly structured (JSON with typed fields, severity enums, rule keys), making programmatic validation both reliable and comprehensive. The LLM judges focus on the dimensions where human-like reasoning adds value: whether bugs are genuinely bugs, whether the output is usable for remediation, and whether the data fits the downstream platform schema.

### Design Rationale

1. **Ground truth is range-based, not exact.** SonarQube issue counts vary across versions and rule profiles. Ground truth specifies `{"min": N, "max": M}` ranges rather than exact values, tolerating legitimate variance while catching regressions.

2. **Graceful degradation when ground truth is absent.** Checks that require ground truth return a neutral score of 0.5 (not 0.0 or 1.0) when no ground truth is provided, preventing penalization for missing reference data while flagging that the check was not fully evaluated.

3. **Evidence collection is first-class.** Every check produces structured evidence (expected vs. actual values, counts, percentages) enabling transparent debugging and audit trails.

4. **LLM judges use heuristic fallbacks.** Each judge implements a `evaluate()` method with keyword-based heuristics rather than always invoking the LLM API. This provides fast, deterministic scoring with the option to use the LLM prompt templates for deeper semantic evaluation.

---

## Dimension Summary

### Programmatic Dimensions

The programmatic evaluator organizes checks into five categories. Dimensions are **equally weighted** -- each category's average score contributes proportionally to the overall programmatic score.

| Dimension | ID | Checks | Weight | Purpose |
|-----------|----|--------|--------|---------|
| Accuracy | D1 | 5 (SQ-AC-1 to SQ-AC-5) | 1/5 (20%) | Issue and quality gate count correctness |
| Coverage | D2 | 4 (SQ-CV-1 to SQ-CV-4) | 1/5 (20%) | Metric, rule, file, and language coverage |
| Completeness | D3 | 6 (SQ-CM-1 to SQ-CM-6) | 1/5 (20%) | Data structure integrity and derived insights |
| Edge Cases | D4 | 4 (SQ-EC-1 to SQ-EC-4) | 1/5 (20%) | Robustness under unusual inputs |
| Performance | D5 | 4 (SQ-PF-1 to SQ-PF-4) | 1/5 (20%) | Timing, output size, memory, API efficiency |

**Total programmatic checks: 23** (19 when performance checks are skipped via `--quick`).

### LLM Judge Dimensions

Three LLM judges run during `evaluate-llm`. A fourth judge (Integration Fit) is available but not included in the standard runner.

| Judge | Dimension | Weight | Sub-dimensions |
|-------|-----------|--------|----------------|
| IssueAccuracyJudge | issue_accuracy | 35% | Bug classification (33%), Vulnerability classification (33%), Code smell classification (34%) |
| CoverageCompletenessJudge | coverage_completeness | 25% | Metric extraction (40%), Component coverage (30%), Rule hydration (30%) |
| ActionabilityJudge | actionability | 20% | Report clarity (40%), Prioritization (30%), Remediation guidance (30%) |
| IntegrationFitJudge | integration_fit | 10% | Envelope compliance (25%), Issues structure (25%), Metrics integration (25%), Cross-tool correlation (25%) |

**Note:** The `IntegrationFitJudge` is defined and importable but is not instantiated in the default `llm_evaluate.py` runner. It can be invoked independently for DD Platform integration validation. The remaining 20% of unallocated weight in the standard run is distributed proportionally across the three active judges.

---

## Check Catalog

### Accuracy Checks (SQ-AC-1 to SQ-AC-5)

These checks validate that SonarQube issue detection and quality gate results fall within ground-truth-defined ranges.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| SQ-AC-1 | Issue count accuracy | Critical | Total issue count falls within `expected_issues.min` to `expected_issues.max` from ground truth | Expected range, actual count |
| SQ-AC-2 | Bug count accuracy | Critical | Bug count (`issues.rollups.by_type.BUG`) within `expected_bugs` range | Expected range, actual count |
| SQ-AC-3 | Vulnerability count accuracy | Critical | Vulnerability count (`issues.rollups.by_type.VULNERABILITY`) within `expected_vulnerabilities` range | Expected range, actual count |
| SQ-AC-4 | Code smell count accuracy | High | Code smell count (`issues.rollups.by_type.CODE_SMELL`) within `expected_smells` range | Expected range, actual count |
| SQ-AC-5 | Quality gate match | High | Quality gate status (OK/ERROR/NONE) matches `quality_gate_expected` | Expected status, actual status |

**Scoring:** Binary pass/fail (1.0 or 0.0) for range-based checks. Returns 0.5 when ground truth is absent.

### Coverage Checks (SQ-CV-1 to SQ-CV-4)

These checks validate that the analysis captures all expected metrics, rules, files, and languages.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| SQ-CV-1 | Metric presence | Critical | All 6 required metrics present in `metric_catalog`: `ncloc`, `complexity`, `violations`, `bugs`, `vulnerabilities`, `code_smells` | Required list, available count, missing metrics |
| SQ-CV-2 | Rule coverage | High | >= 95% of triggered rules (from issues) have corresponding entries in `rules.by_key` | Triggered count, covered count, coverage %, missing rules (first 10) |
| SQ-CV-3 | File coverage | High | >= 95% of files (qualifier=FIL in components) have entries in `measures.by_component_key` | Total files, files with measures, coverage % |
| SQ-CV-4 | Language coverage | High | All `expected_languages` from ground truth are detected in component language attributes | Expected languages, detected languages, missing |

**Scoring:** Proportional (0.0-1.0). SQ-CV-1 scores as `(required - missing) / required`. SQ-CV-2, SQ-CV-3 use `min(coverage_pct / 100, 1.0)`. SQ-CV-4 scores as `(expected - missing) / expected`. Returns 0.5 when ground truth is absent (SQ-CV-4 only).

### Completeness Checks (SQ-CM-1 to SQ-CM-6)

These checks validate the structural integrity and derived data within the analysis output.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| SQ-CM-1 | Component tree complete | Critical | Component tree contains all three qualifier types: TRK (project), DIR (directory), FIL (file) | Required qualifiers, present qualifiers, missing |
| SQ-CM-2 | Issue locations | High | >= 90% of issues have `component` AND (`line` OR `text_range`) | Total issues, issues with location, coverage % |
| SQ-CM-3 | Rules hydrated | High | >= 95% of rules in `rules.by_key` have all four required fields: `key`, `name`, `type`, `severity` | Total rules, fully hydrated count, coverage % |
| SQ-CM-4 | Duplications present | Medium | When `duplicated_lines_density` > 0, per-file duplication data (`by_file_key`) must exist | Files with duplications, density % |
| SQ-CM-5 | Quality gate conditions | High | When quality gate status is present (not NONE), conditions array must be non-empty | Status, conditions count |
| SQ-CM-6 | Derived insights present | Medium | Both `derived_insights.hotspots` and `derived_insights.directory_rollups` must be non-empty | Hotspots count, directory rollups count, issues list |

**Scoring:**
- SQ-CM-1: `present / required` (3 possible)
- SQ-CM-2, SQ-CM-3: `min(coverage_pct / 100, 1.0)` with 90%/95% thresholds
- SQ-CM-4: Binary (1.0 if data present when expected, 1.0 if no duplication)
- SQ-CM-5: Binary (1.0 if conditions present, 0.5 if status=NONE, 0.0 if missing)
- SQ-CM-6: `(2 - issues) / 2` where issues count missing sections

### Edge Case Checks (SQ-EC-1 to SQ-EC-4)

These checks validate robustness when handling unusual input scenarios.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| SQ-EC-1 | Empty repository handling | Medium | When no files (qualifier=FIL) exist, output still contains `components`, `measures`, and `issues` sections | File count, structure validity, missing keys |
| SQ-EC-2 | Large file handling | Medium | All files with ncloc >= 1000 have non-zero measures (analysis did not skip them) | Large file count, analyzed count |
| SQ-EC-3 | Unicode path handling | Low | All component paths containing non-ASCII characters (ord > 127) are properly indexed in components | Unicode path count, indexed count |
| SQ-EC-4 | Missing optional data | Medium | Optional sections (`duplications`, `hotspots`, `derived_insights`) are either absent or have dict type (not malformed) | Sections checked, issues list |

**Scoring:**
- SQ-EC-1: Binary based on key presence; 1.0 if repo has files (not applicable)
- SQ-EC-2: `analyzed / large_files` ratio; 1.0 if no large files
- SQ-EC-3: `indexed / unicode_paths` ratio; 1.0 if no unicode paths
- SQ-EC-4: `(sections_checked - issues) / sections_checked`

### Performance Checks (SQ-PF-1 to SQ-PF-4)

These checks validate resource efficiency. Skipped when `--quick` flag is used.

| Check ID | Name | Severity | Default Threshold | Pass Criteria | Evidence Collected |
|----------|------|----------|-------------------|---------------|-------------------|
| SQ-PF-1 | Analysis timing | High | 300,000ms (5 min) | `duration_ms` (from metadata or computed from start/end time) <= threshold | Duration ms, limit ms |
| SQ-PF-2 | Output size | Medium | 50MB | Serialized JSON output size <= threshold | Size MB, limit MB |
| SQ-PF-3 | Memory footprint | Low | 2048MB (2GB) | `peak_memory_mb` from metadata <= threshold | Peak memory MB, limit MB |
| SQ-PF-4 | API response time | Medium | 60,000ms (60s) | Total API call time (from metadata `api_calls` or `total_api_time_ms`) <= threshold | Total API time ms, limit ms |

**Scoring:** Proportional using `min(threshold / actual, 1.0)`. Returns 0.5 when timing/memory metadata is not available.

**Threshold overrides:** Ground truth files can override default thresholds via `max_duration_ms`, `max_output_size_mb`, `max_memory_mb`, and `max_api_time_ms` fields.

---

## Scoring

### Programmatic Score Calculation

The overall programmatic score is the **unweighted mean** of all individual check scores:

```python
# From EvaluationReport.score property
score = sum(check.score for check in checks) / len(checks)
# Result: 0.0 to 1.0
```

Per-category scores are computed the same way:

```python
# Per-category average
category_score = sum(scores_in_category) / len(scores_in_category)
```

In the scorecard, dimensions are assigned equal weight: `weight = 1.0 / number_of_categories`.

### LLM Score Calculation

The weighted LLM score uses judge-defined weights:

```python
# From LLMEvaluationReport.weighted_score property
weights = {
    "issue_accuracy": 0.35,
    "coverage_completeness": 0.25,
    "actionability": 0.20,
}
total_weight = sum(weights[r.dimension] for r in results)
weighted_score = sum(r.score * weights[r.dimension] for r in results) / total_weight
# Result: 1.0 to 5.0
```

Each judge produces sub-scores that feed into its dimension score via weighted averaging:

```python
# Issue Accuracy: bug_classification * 0.33 + vulnerability_classification * 0.33 + code_smell_classification * 0.34
# Coverage Completeness: metric_extraction * 0.40 + component_coverage * 0.30 + rule_hydration * 0.30
# Actionability: report_clarity * 0.40 + prioritization * 0.30 + remediation_guidance * 0.30
```

### Combined Score Calculation

The combined score merges programmatic and LLM evaluations onto a unified 1-5 scale:

```python
# From calculate_combined_score() in llm_evaluate.py

# Step 1: Normalize programmatic score (0.0-1.0) to 1-5 scale
if programmatic_score <= 1.0:
    programmatic_normalized = programmatic_score * 4 + 1  # 0.0 -> 1.0, 1.0 -> 5.0
else:
    programmatic_normalized = programmatic_score  # Already 1-5

# Step 2: Weighted combination
combined_score = (programmatic_normalized * 0.60) + (llm_score * 0.40)
# Result: 1.0 to 5.0
```

### Dimension Weight Allocation (Full Picture)

| Component | Weight in Combined | Scale | Normalization |
|-----------|-------------------|-------|---------------|
| Programmatic (all categories) | 60% | 0.0-1.0 | Mapped to 1-5 via `score * 4 + 1` |
| LLM Issue Accuracy | 40% x 35% = 14% | 1-5 | Native |
| LLM Coverage Completeness | 40% x 25% = 10% | 1-5 | Native |
| LLM Actionability | 40% x 20% = 8% | 1-5 | Native |
| (Remaining LLM weight) | 40% x 20% = 8% | -- | Distributed proportionally across active judges |

---

## Decision Thresholds

Decisions are applied to the combined score on the 1-5 scale. The programmatic evaluator uses the same thresholds after normalizing its 0-1 score to 0-5 via `score * 5`.

| Decision | Combined Score | Programmatic Raw | Interpretation |
|----------|----------------|-----------------|----------------|
| STRONG_PASS | >= 4.0 | >= 80% | Excellent -- production-ready output |
| PASS | >= 3.5 | >= 70% | Good -- minor improvements possible |
| WEAK_PASS | >= 3.0 | >= 60% | Acceptable with caveats -- review recommended |
| FAIL | < 3.0 | < 60% | Significant issues -- requires investigation |

### Exit Codes

- Programmatic evaluator (`evaluate.py`): exits 0 if `score >= 0.6` (60%), exit 1 otherwise
- LLM evaluator (`llm_evaluate.py`): exits 0 if `weighted_score >= 3.0`, exit 1 otherwise

---

## LLM Judge Details

### Issue Accuracy Judge (35%)

**Purpose:** Validates that SonarQube correctly categorizes issues into BUG, VULNERABILITY, and CODE_SMELL types with appropriate severity levels.

**Sub-dimensions:**

| Sub-dimension | Weight | Evaluation Method |
|---------------|--------|-------------------|
| Bug classification | 33% | Keyword heuristic: checks if BUG messages contain bug-related terms (`null`, `error`, `exception`, `fail`, `crash`, `overflow`, `leak`, `undefined`) |
| Vulnerability classification | 33% | Keyword heuristic: checks if VULNERABILITY messages/rules contain security terms (`sql`, `inject`, `xss`, `csrf`, `auth`, `password`, `credential`, `secret`, `hardcoded`, `sensitive`, `exposure`, `leak`) |
| Code smell classification | 34% | Keyword heuristic: checks if CODE_SMELL messages/rules contain maintainability terms (`complexity`, `duplicate`, `unused`, `dead`, `naming`, `long`, `parameter`, `cognitive`, `method`, `class`, `refactor`) |

**Sub-score formula:** `max(1, min(5, round(1 + valid_ratio * 4)))` where `valid_ratio = matching_issues / sampled_issues`.

**Evidence collected:** Total issue count, up to 10 sampled bugs, 10 sampled vulnerabilities, 10 sampled code smells, rollup totals, evaluation mode, synthetic baseline context (in real_world mode).

**Scoring rubric (from prompt template):**

| Score | Synthetic Mode | Real-World Mode |
|-------|---------------|-----------------|
| 5 | >95% correctly typed, severity always appropriate | Output schema compliant, accurate classifications |
| 4 | 85-95% correct, severity mostly appropriate | Minor schema issues, sensible classifications |
| 3 | 70-85% correct, some severity mismatches | Schema issues OR questionable classification |
| 2 | 50-70% correct, frequent severity mismatches | Multiple schema issues AND questionable classifications |
| 1 | <50% correct OR systematic misclassification | Broken output, missing required fields |

**Default confidence:** 0.8

### Coverage Completeness Judge (25%)

**Purpose:** Validates that SonarQube data extraction captures all relevant metrics, components, and rule metadata.

**Sub-dimensions:**

| Sub-dimension | Weight | Evaluation Method |
|---------------|--------|-------------------|
| Metric extraction | 40% | Checks presence of 6 key metrics (`ncloc`, `complexity`, `cognitive_complexity`, `bugs`, `vulnerabilities`, `code_smells`) in catalog + whether measures are populated |
| Component coverage | 30% | Ratio of files (qualifier=FIL) that have entries in `measures.by_component_key` |
| Rule hydration | 30% | Ratio of triggered rules (from issues) that have entries in `rules.by_key` |

**Sub-score formula:**
- Metric extraction: `max(1, min(5, key_metrics_present + 1))` if measures populated, else `max(1, key_metrics_present)`
- Component coverage: `max(1, min(5, round(1 + files_with_measures/total_files * 4)))`
- Rule hydration: `max(1, min(5, round(1 + hydrated/triggered * 4)))`

**Evidence collected:** Metric count, first 20 metric keys, component count, measures count, rules count, issues count, first 20 triggered rule keys.

**Scoring rubric (from prompt template):**

| Score | Criteria |
|-------|----------|
| 5 | Complete metric catalog, all components have measures, 100% rule hydration |
| 4 | >80% metric coverage, most components measured, >95% rule hydration |
| 3 | 60-80% metric coverage, majority measured, >80% rule hydration |
| 2 | 40-60% metric coverage, significant gaps, <80% rule hydration |
| 1 | <40% metric coverage OR major data gaps |

**Default confidence:** 0.85

### Actionability Judge (20%)

**Purpose:** Evaluates whether the analysis output is useful for developers and due diligence teams to prioritize and fix issues.

**Sub-dimensions:**

| Sub-dimension | Weight | Evaluation Method |
|---------------|--------|-------------------|
| Report clarity | 40% | Additive scoring (+1 each): schema_version present, hotspots present, directory_rollups present, quality gate conditions present. Base score: 1 |
| Prioritization | 30% | Ratio of issues with severity field: <50% = 2, <90% = 3, <100% = 4, 100% = 5 |
| Remediation guidance | 30% | Ratio of rules with `html_desc` or `remediation_effort`: <50% = 2, <80% = 3, <95% = 4, >= 95% = 5 |

**Evidence collected:** Quality gate status, quality gate conditions count, total issues, issues with line numbers, issues with severity, rules count, rules with description, hotspots count, 5 sample issues.

**Scoring rubric (from prompt template):**

| Score | Criteria |
|-------|----------|
| 5 | Clear structure, all issues prioritized, comprehensive remediation guidance |
| 4 | Well-organized, >90% with severity, most rules documented |
| 3 | Understandable, basic prioritization, some guidance |
| 2 | Confusing output, inconsistent severity, limited guidance |
| 1 | Unusable output, no prioritization, no remediation info |

**Default confidence:** 0.75

### Integration Fit Judge (10% -- optional)

**Purpose:** Evaluates how well the output maps to the DD Platform evidence schema and Caldera envelope format.

**Ground truth assertions (run before scoring):**
1. `analysis_path` must be set and point to an existing file
2. File must be valid JSON
3. Must contain `metadata` field
4. Must contain `data` field

If assertions fail, score is capped at 1 with 0.9 confidence.

**Evaluation method:** Structural analysis (no LLM invocation required):
- Starts at score 5, decremented for each issue found
- Missing envelope format: score capped at 2
- Missing required metadata fields (`tool_name`, `run_id`, `repo_id`, `timestamp`): score capped at 4
- Missing `issues` or `items` section: score capped at 3
- Missing `rollups`: score capped at 4
- Missing `metrics.summary`: score capped at 4

**Default confidence:** 0.85 (0.9 for ground truth failures)

---

## Evidence Collection

Every check and judge produces structured evidence for transparency and debugging. Evidence is included in both the `evaluation_report.json` and `llm_evaluation.json` outputs.

### Programmatic Check Evidence

| Check Category | Evidence Fields |
|----------------|----------------|
| Accuracy (SQ-AC-*) | `expected` (min/max range), `actual` (observed value), `skipped` (bool if no ground truth) |
| Coverage (SQ-CV-*) | `required` (list), `available_count`, `missing` (list), `triggered_rules`, `coverage_pct` |
| Completeness (SQ-CM-*) | `required` (qualifiers/fields), `present`, `missing`, `coverage_pct`, `conditions_count`, `issues` |
| Edge Cases (SQ-EC-*) | `files` (count), `large_files`, `unicode_paths`, `sections_checked`, `issues` |
| Performance (SQ-PF-*) | `duration_ms`, `limit_ms`, `size_mb`, `peak_memory_mb`, `total_api_time_ms`, `skipped` |

### LLM Judge Evidence

| Judge | Evidence Fields |
|-------|----------------|
| Issue Accuracy | `total_issues`, `sampled_bugs` (up to 10), `sampled_vulnerabilities` (up to 10), `sampled_code_smells` (up to 10), `rollups`, `evaluation_mode`, `synthetic_baseline`, `interpretation_guidance` |
| Coverage Completeness | `metric_count`, `metric_keys` (first 20), `component_count`, `measures_count`, `rules_count`, `issues_count`, `triggered_rules` (first 20) |
| Actionability | `quality_gate_status`, `quality_gate_conditions`, `total_issues`, `issues_with_line`, `issues_with_severity`, `rules_count`, `rules_with_description`, `hotspots_count`, `sample_issues` (first 5) |
| Integration Fit | `tool_output`, `tool_output_summary` (condensed metadata + data summaries) |

---

## Ground Truth

### Methodology

Ground truth files define expected ranges and properties for each synthetic evaluation repository. They are used by accuracy checks (SQ-AC-*) and the language coverage check (SQ-CV-4).

### Ground Truth Schema (v1.0)

Each ground truth file follows this schema:

```json
{
  "schema_version": "1.0",
  "scenario": "<scenario-name>",
  "description": "<human-readable description>",
  "generated_at": "<ISO-8601 timestamp>",
  "repo_path": "<relative path to eval repo>",
  "id": "<scenario-id>",
  "language": "<primary language>",
  "expected_languages": ["<sonarqube language key>"],
  "expected_issues": { "min": <N>, "max": <M> },
  "expected_bugs": { "min": <N>, "max": <M> },
  "expected_vulnerabilities": { "min": <N>, "max": <M> },
  "expected_smells": { "min": <N>, "max": <M> },
  "expected_metrics": {
    "ncloc": { "min": <N>, "max": <M> },
    "complexity": { "min": <N>, "max": <M> }
  },
  "quality_gate_expected": "<OK|ERROR|NONE>",
  "notes": "<additional context>"
}
```

**Optional extensions:**
- `expected_rules`: Map of rule keys to `{ description, category, min_occurrences }` for rule-specific validation
- `expected_vulnerability_types`: List of expected vulnerability categories for security repos
- `files`: Per-file expected issue breakdowns with `expected_issues` and `issue_types`
- `max_duration_ms`, `max_output_size_mb`, `max_memory_mb`, `max_api_time_ms`: Performance threshold overrides

### Synthetic Repositories

Five ground truth files cover distinct evaluation scenarios:

| File | Scenario | Language | Key Focus | Issue Range | Quality Gate |
|------|----------|----------|-----------|-------------|-------------|
| `java-security.json` | java-security | Java | Security vulnerabilities (SQL injection, hardcoded credentials, path traversal) | 4-20 | OK |
| `python-mixed.json` | python-mixed | Python | Comprehensive mixed issues (bugs, vulns, smells) across 5 files | 15-100 | ERROR |
| `typescript-duplication.json` | typescript-duplication | TypeScript | High code duplication (20-60% density) | 6-20 | OK |
| `csharp-baseline.json` | csharp-baseline | C# | Baseline code smells (unused vars, empty methods, commented code) | 10-20 | ERROR |
| `csharp-complex.json` | csharp-complex | C# | High complexity (cognitive complexity, long methods, many smells) | 3000-3600 | ERROR |

### Scenario Design Rationale

- **java-security**: Tests vulnerability detection accuracy. Low total issue count but expects specific security vulnerability types. Quality gate passes because security-focused rules do not trip the default gate.
- **python-mixed**: Most comprehensive scenario. Includes per-file ground truth with expected issue types (`data_processor.py`, `api_handler.py`, `utils.py`, `models.py`, `clean_module.py`). Tests the full spectrum of issue types.
- **typescript-duplication**: Tests duplication detection specifically. Expects high `duplicated_lines_density` (20-60%) and validates duplication-related completeness checks.
- **csharp-baseline**: Tests detection of common code smells. Includes `expected_rules` with specific SonarQube rule keys (S1481, S3776, S1186, S125).
- **csharp-complex**: Stress test with 3000-3600 expected issues. Validates performance under high volume and tests specific complexity rules (S3776, S1541) with `min_occurrences` assertions.

### Expected Language Keys

Ground truth uses SonarQube language keys (not full names):
- Java: `java`
- Python: `py`
- TypeScript: `ts`
- C#: `cs`

### Ground Truth Loading

Ground truth is loaded by matching the analysis file name or parent directory name against ground truth file stems:

```python
# From checks/__init__.py
def load_ground_truth(ground_truth_dir: Path, name: str) -> dict | None:
    gt_path = Path(ground_truth_dir) / f"{name}.json"
    if gt_path.exists():
        with open(gt_path) as f:
            return json.load(f)
    return None
```

The evaluator also supports loading all ground truth files via `load_all_ground_truth()` for batch evaluation.

---

## Running Evaluations

### Programmatic Evaluation

```bash
# Full evaluation with verbose console output
make evaluate

# Quick evaluation (skips performance checks SQ-PF-*)
make evaluate-quick

# JSON-only output (no console formatting)
make evaluate-json

# Direct invocation with custom paths
.venv/bin/python -m scripts.evaluate \
    --analysis outputs/<run-id>/output.json \
    --ground-truth evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json
```

**CLI options:**
- `--analysis, -a` (required): Path to analysis JSON file
- `--ground-truth, -g`: Path to ground truth directory or file
- `--output, -o`: Output JSON file path
- `--json`: JSON-only output mode
- `--quick`: Skip performance checks
- `--no-color`: Disable colored terminal output

### LLM Evaluation

```bash
# Standard LLM evaluation (3 judges, default model)
make evaluate-llm

# With specific model
make evaluate-llm LLM_MODEL=opus

# Combined programmatic + LLM evaluation
make evaluate-combined

# Full evaluation (programmatic then LLM)
make evaluate-full

# Direct invocation
.venv/bin/python -m scripts.llm_evaluate \
    --analysis outputs/<run-id>/output.json \
    --output evaluation/results/llm_evaluation.json \
    --model opus-4.5 \
    --programmatic-results evaluation/results/evaluation_report.json
```

**CLI options:**
- `--analysis, -a` (required): Path to analysis JSON file
- `--output, -o`: Output JSON file path
- `--model, -m`: Claude model (`opus`, `opus-4.5`, `sonnet`, `haiku`; default: `opus-4.5`)
- `--timeout, -t`: Timeout per judge in seconds (default: 120)
- `--json`: JSON-only output mode
- `--no-color`: Disable colored output
- `--programmatic-score`: Programmatic score (0.0-1.0) for combined scoring
- `--programmatic-results`: Path to programmatic evaluation JSON for combined scoring
- `--skip-judge`: Skip specific judges (repeatable)

### Evaluation Targets for Specific Repos

```bash
# Analyze then evaluate a specific synthetic repo
make analyze-java-security
make evaluate

# Analyze all synthetic repos
make analyze-all-evals
```

### Evaluation Outputs

Evaluation artifacts are written to `evaluation/results/` (default `EVAL_OUTPUT_DIR`):

```
evaluation/results/
  evaluation_report.json     # Programmatic evaluation report
  scorecard.json             # Structured scorecard with dimensions
  scorecard.md               # Human-readable markdown scorecard
  llm_evaluation.json        # LLM judge results (if run)
  combined_evaluation.json   # Combined scoring (if run)
```

LLM judge individual results are additionally written to:

```
evaluation/llm/results/
  <dimension>_<timestamp>.json    # Per-judge results with observability data
```

---

## Extending the Evaluation

### Adding a New Programmatic Check

1. Create the check function in the appropriate module under `scripts/checks/`:

```python
def check_new_property(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-XX-N: Description of what the check validates."""
    # ... validation logic ...
    return CheckResult(
        check_id="SQ-XX-N",
        name="New check name",
        category=CheckCategory.APPROPRIATE_CATEGORY,
        passed=passed,
        score=score,
        message="Human-readable result",
        evidence={"key": "value"},
    )
```

2. Add the function to the `run_*_checks()` list in that module.

3. Update ground truth files if the check requires new expected values.

4. Run `make evaluate` to verify.

### Adding a New LLM Judge

1. Create a new judge class in `evaluation/llm/judges/`:

```python
class NewJudge(BaseJudge):
    @property
    def dimension_name(self) -> str:
        return "new_dimension"

    @property
    def weight(self) -> float:
        return 0.15  # Must be coordinated with other judge weights

    def collect_evidence(self) -> dict[str, Any]:
        # ... extract relevant data ...
        return evidence

    def evaluate(self) -> JudgeResult:
        # ... evaluation logic ...
        return self._create_result(score=score, confidence=conf, reasoning=reason)
```

2. Create a prompt template in `evaluation/llm/prompts/new_dimension.md` with `{{ evidence }}` placeholder.

3. Register the judge in `evaluation/llm/judges/__init__.py`.

4. Add to the judge instantiation list in `scripts/llm_evaluate.py`.

5. Update the weight map in `LLMEvaluationReport._get_weight()`.

### Updating Thresholds

Performance and coverage thresholds are defined in check functions:

```python
# In coverage.py
threshold = 95.0  # SQ-CV-2, SQ-CV-3 coverage threshold

# In completeness.py
threshold = 90.0  # SQ-CM-2 issue location threshold
threshold = 95.0  # SQ-CM-3 rule hydration threshold

# In performance.py
max_duration_ms = 300000   # SQ-PF-1: 5 minutes
max_size_mb = 50.0         # SQ-PF-2: 50MB
max_memory_mb = 2048       # SQ-PF-3: 2GB
max_api_time_ms = 60000    # SQ-PF-4: 60 seconds
```

Ground truth files can override performance thresholds per-scenario.

---

## Confidence and Score Capping

### LLM Judge Confidence

Each judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence -- reliable score |
| 0.7-0.9 | Moderate confidence -- some uncertainty |
| < 0.7 | Low confidence -- manual review recommended |

**Default confidence values by judge:**
- Issue Accuracy: 0.80
- Coverage Completeness: 0.85
- Actionability: 0.75
- Integration Fit: 0.85

### Ground Truth Score Capping

The Integration Fit judge demonstrates the score capping pattern: if ground truth assertions fail, the score is capped at 1 regardless of other analysis. In the LLM runner, failed ground truth assertions produce a score of 1 with 0.9 confidence.

```python
# From llm_evaluate.py
gt_passed, gt_failures = judge.run_ground_truth_assertions()
if not gt_passed:
    results.append(JudgeResult(
        dimension=judge.dimension_name,
        score=1,
        confidence=0.9,
        reasoning=f"Ground truth assertions failed: {'; '.join(gt_failures[:3])}",
    ))
```

---

## Key Implementation Files

| File | Purpose |
|------|---------|
| `scripts/evaluate.py` | Programmatic evaluation orchestrator, scorecard generation, decision logic |
| `scripts/llm_evaluate.py` | LLM judge runner, combined scoring, LLM report generation |
| `scripts/checks/__init__.py` | CheckResult/EvaluationReport classes, utility functions, data accessors |
| `scripts/checks/accuracy.py` | SQ-AC-1 to SQ-AC-5: Issue and quality gate count validation |
| `scripts/checks/coverage.py` | SQ-CV-1 to SQ-CV-4: Metric, rule, file, and language coverage |
| `scripts/checks/completeness.py` | SQ-CM-1 to SQ-CM-6: Structural integrity and derived insights |
| `scripts/checks/edge_cases.py` | SQ-EC-1 to SQ-EC-4: Robustness under unusual inputs |
| `scripts/checks/performance.py` | SQ-PF-1 to SQ-PF-4: Timing, size, memory, API efficiency |
| `evaluation/llm/judges/base.py` | SonarQube-specific BaseJudge extending shared.evaluation.BaseJudge |
| `evaluation/llm/judges/issue_accuracy.py` | IssueAccuracyJudge (35% weight) |
| `evaluation/llm/judges/coverage_completeness.py` | CoverageCompletenessJudge (25% weight) |
| `evaluation/llm/judges/actionability.py` | ActionabilityJudge (20% weight) |
| `evaluation/llm/judges/integration_fit.py` | IntegrationFitJudge (10% weight, optional) |
| `evaluation/llm/prompts/issue_accuracy.md` | Issue accuracy prompt template |
| `evaluation/llm/prompts/coverage_completeness.md` | Coverage completeness prompt template |
| `evaluation/llm/prompts/actionability.md` | Actionability prompt template |
| `evaluation/llm/prompts/integration_fit.md` | Integration fit prompt template |
| `evaluation/ground-truth/*.json` | 5 ground truth files for synthetic repos |

---

## References

- [SonarQube Documentation](https://docs.sonarsource.com/sonarqube/latest/)
- [SonarQube Web API](https://docs.sonarsource.com/sonarqube/latest/extension-guide/web-api/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
- [Project Caldera EVALUATION.md](../../../docs/EVALUATION.md)
