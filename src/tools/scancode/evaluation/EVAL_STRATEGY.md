# Evaluation Strategy: ScanCode License Analysis

This document describes the evaluation methodology for the ScanCode license detection and compliance risk assessment tool.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation to measure both objective correctness and subjective quality of license analysis outputs.

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- verifies detection counts, field presence, classification correctness, and performance bounds |
| LLM Judges | 40% | Semantic understanding, nuance -- assesses whether outputs are accurate in context, cover all license scenarios, classify risk appropriately, and provide actionable guidance |

This hybrid approach is motivated by the nature of license analysis:

1. **Deterministic facts** (license counts, SPDX IDs, field presence) are best validated by programmatic checks that produce binary pass/fail verdicts with zero ambiguity.
2. **Contextual judgment** (whether risk classification is reasonable, whether findings are actionable for compliance teams) requires an LLM judge that can reason about legal nuance and output quality.
3. **Ground truth diversity** matters: the evaluation runs against 8 synthetic repositories that span the full spectrum of license scenarios, from simple single-license repos to complex multi-license and edge-case configurations.

"Correct" for ScanCode means: every license present in a repository is detected with the right SPDX identifier, classified into the right category (permissive, copyleft, weak-copyleft, unknown), assigned the right risk level, and reported with sufficient detail for a compliance team to act without further investigation.

---

## Dimension Summary

### Programmatic Dimensions

Programmatic checks are organized into four categories. Each category receives equal weight (25%) within the programmatic component, and the programmatic component as a whole contributes 60% of the combined score.

| Dimension | Category | Checks | Weight (of Programmatic) | Purpose |
|-----------|----------|--------|--------------------------|---------|
| D1 | Accuracy | LA-1 to LA-14 | 25% | License detection correctness against ground truth |
| D2 | Coverage | LC-1 to LC-8 | 25% | Output completeness and field presence |
| D3 | Detection | LD-1 to LD-6 | 25% | Detection method quality (SPDX, file, header) |
| D4 | Performance | LP-1 to LP-4 | 25% | Scan speed and completion |

### LLM Judge Dimensions

| Judge | Weight (of LLM) | Focus |
|-------|------------------|-------|
| License Accuracy | 30% | SPDX ID correctness, false positive/negative rate |
| License Coverage | 25% | Category and file coverage across test repos |
| Risk Classification | 25% | Risk level accuracy, category flag correctness, reason quality |
| Actionability | 20% | Clarity, specificity, and compliance-readiness of outputs |

### Combined Score Calculation

```python
# Programmatic score: proportion of checks passed (0.0 to 1.0)
programmatic_raw = passed_checks / total_checks

# Normalize programmatic score to 1-5 scale
programmatic_normalized = programmatic_raw * 5.0

# LLM score: weighted average of judge scores (already 1-5)
llm_score = (
    accuracy_judge.score * 0.30 +
    coverage_judge.score * 0.25 +
    risk_classification_judge.score * 0.25 +
    actionability_judge.score * 0.20
)

# Combined score
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

---

## Check Catalog

### Accuracy Checks (LA-1 to LA-14)

These checks compare analysis output against ground truth for each synthetic repository. Checks LA-13 and LA-14 are conditional -- they only run when the ground truth defines `expected_findings`.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| LA-1 | Total licenses found | High | `len(licenses_found)` equals `expected.total_licenses` within `count_tolerance` | Expected count, actual count |
| LA-2 | Expected licenses detected | Critical | All licenses in `expected.licenses` appear in `analysis.licenses_found` | Missing license IDs |
| LA-3 | License file count | High | `analysis.license_files_found` equals `expected.license_files_found` within `count_tolerance` | Expected count, actual count |
| LA-4 | Files with licenses | High | `analysis.files_with_licenses` equals `expected.files_with_licenses` within `count_tolerance` | Expected count, actual count |
| LA-5 | Overall risk level | Critical | `analysis.overall_risk` exactly matches `expected.overall_risk` | Expected risk, actual risk |
| LA-6 | Has permissive flag | Medium | `analysis.has_permissive` matches `expected.has_permissive` | Boolean comparison |
| LA-7 | Has copyleft flag | Critical | `analysis.has_copyleft` matches `expected.has_copyleft` | Boolean comparison |
| LA-8 | Has weak-copyleft flag | Medium | `analysis.has_weak_copyleft` matches `expected.has_weak_copyleft` | Boolean comparison |
| LA-9 | Has unknown flag | Medium | `analysis.has_unknown` matches `expected.has_unknown` | Boolean comparison |
| LA-10 | License counts match | High | Per-license counts in `analysis.license_counts` match `expected.license_counts` within `count_tolerance` | Expected counts dict, actual counts dict |
| LA-11 | No unexpected licenses | High | No licenses in `analysis.licenses_found` that are absent from `expected.licenses` (false positive check) | Unexpected license IDs |
| LA-12 | Finding paths present | Medium | All entries in `analysis.findings` have a non-empty `file_path` | Count of invalid findings |
| LA-13 | Expected paths detected | High | All paths in `expected.expected_findings` appear in `analysis.findings` (conditional) | Missing file paths |
| LA-14 | No unexpected paths | Medium | No paths in `analysis.findings` that are absent from `expected.expected_findings` (conditional) | Extra file paths |

#### Accuracy Scoring

```python
def check_equal(check_id, category, name, expected, actual, tolerance=0):
    """Compare expected vs actual with optional numeric tolerance."""
    if tolerance > 0 and isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        passed = abs(expected - actual) <= tolerance
    else:
        passed = expected == actual
    return CheckResult(check_id=check_id, category=category, passed=passed, ...)
```

LA-2 uses a set containment check (`expected <= actual`), while LA-11 uses the inverse (`actual <= expected`). Together they verify exact-match license detection with no false positives and no false negatives.

### Coverage Checks (LC-1 to LC-8)

These checks verify that the analysis output contains all required fields and data structures, regardless of their specific values.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| LC-1 | Summary metrics present | High | Fields `total_files_scanned`, `files_with_licenses`, `license_files_found` all exist in output | List of missing fields |
| LC-2 | License inventory present | High | Both `licenses_found` and `license_counts` fields exist in output | Presence booleans |
| LC-3 | Category flags present | High | Fields `has_permissive`, `has_weak_copyleft`, `has_copyleft`, `has_unknown` all exist | List of missing fields |
| LC-4 | Risk assessment present | High | Both `overall_risk` and `risk_reasons` fields exist in output | Presence booleans |
| LC-5 | Findings array complete | Critical | `findings` array exists; every finding contains `file_path`, `spdx_id`, `category`, `confidence`, `match_type` | Presence and completeness booleans |
| LC-6 | File summaries complete | Medium | `files` dict exists; every file entry contains `file_path`, `licenses`, `category`, `has_spdx_header` | Presence and completeness booleans |
| LC-7 | Metadata present | Medium | Fields `schema_version`, `repository`, `timestamp`, `tool`, `tool_version` all exist | List of missing fields |
| LC-8 | Timing present | Low | `scan_time_ms` field exists in output | Presence boolean |

### Detection Checks (LD-1 to LD-6)

These checks validate the quality and correctness of individual license detections (findings), focusing on detection method classification, confidence scores, and category labels.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| LD-1 | SPDX header detection | High | Count of findings with `match_type == "spdx"` equals `expected.spdx_headers_found` | Expected count, actual count |
| LD-2 | License file detection | High | Count of findings with `match_type == "file"` equals `expected.license_file_detections` | Expected count, actual count |
| LD-3 | Confidence scores valid | Critical | All `confidence` values in findings are in range [0, 1] | Min and max confidence values |
| LD-4 | Category classification correct | Critical | All `category` values in findings are one of: `permissive`, `weak-copyleft`, `copyleft`, `unknown` | List of actual categories |
| LD-5 | Match type classification correct | High | All `match_type` values in findings are one of: `file`, `header`, `spdx` | List of actual match types |
| LD-6 | Finding count matches | High | Total number of findings equals `expected.total_findings` | Expected count, actual count |

#### Valid Enum Values

| Field | Valid Values |
|-------|-------------|
| `category` | `permissive`, `weak-copyleft`, `copyleft`, `unknown` |
| `match_type` | `file`, `header`, `spdx` |
| `confidence` | Any float in [0.0, 1.0] |

### Performance Checks (LP-1 to LP-4)

These checks validate that analysis completes within acceptable time bounds and that the scan actually executed.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| LP-1 | Scan time within limit | High | `scan_time_ms` in range [0, `max_scan_time_ms`] (default: 5000ms) | Scan time, threshold |
| LP-2 | Scan time positive | Medium | `scan_time_ms > 0` (scan actually ran) | Scan time value |
| LP-3 | Processing rate reasonable | Medium | `total_files_scanned / (scan_time_ms / 1000) >= min_files_per_second` (default: 1 file/sec); auto-passes if no files or zero time | Files per second rate |
| LP-4 | Analysis completed | Low | `scan_time_ms > 0` (validates scan finished successfully) | Scan time value |

#### Threshold Defaults

Thresholds are defined per ground truth file in the `thresholds` object:

| Threshold | Default | Purpose |
|-----------|---------|---------|
| `max_scan_time_ms` | 5000 | Maximum acceptable scan time in milliseconds |
| `min_files_per_second` | 1 | Minimum acceptable processing throughput |
| `count_tolerance` | 0 | Numeric tolerance for license count comparisons |

---

## Scoring Methodology

### Programmatic Score

The programmatic evaluator computes a raw pass rate across all checks for all evaluated repositories:

```python
overall_score = total_passed / total_checks   # 0.0 to 1.0
```

This raw score is then normalized to a 1-5 scale for the scorecard:

```python
normalized_score = overall_score * 5.0        # 0.0 to 5.0
```

### Per-Dimension Scores

Within the scorecard, each dimension (Accuracy, Coverage, Detection, Performance) receives its own score:

```python
dimension_score = (dimension_passed / dimension_total) * 5.0
```

Dimensions are weighted equally (each gets `1 / num_categories` weight). This is computed dynamically:

```python
num_categories = len(category_data)
for category, data in sorted(category_data.items()):
    total = data["passed"] + data["failed"]
    score = (data["passed"] / total * 5.0) if total > 0 else 0
    weighted_score = score / num_categories
```

### Per-Repository Evaluation

The evaluator runs all checks independently per repository. Each `(analysis_file, ground_truth_file)` pair produces an `EvaluationReport` with its own pass rate. The final score aggregates across all repositories.

### LLM Judge Scoring

Each LLM judge returns a score on a 1-5 scale with sub-scores for its specific sub-dimensions. The weighted LLM score is:

```python
llm_score = (
    accuracy_judge.score  * 0.30 +   # 30% weight
    coverage_judge.score  * 0.25 +   # 25% weight
    risk_judge.score      * 0.25 +   # 25% weight
    actionability_judge.score * 0.20  # 20% weight
)
```

---

## Decision Thresholds

The overall decision is derived from the normalized score (0-5 scale):

| Decision | Normalized Score | Raw Pass Rate | Interpretation |
|----------|------------------|---------------|----------------|
| STRONG_PASS | >= 4.0 | >= 80% | Excellent, production-ready |
| PASS | >= 3.5 | >= 70% | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 | >= 60% | Acceptable with caveats |
| FAIL | < 3.0 | < 60% | Significant issues |

The decision function from `evaluate.py`:

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

Note that the input `score` is the raw 0-1 pass rate, which is multiplied by 5.0 internally to map onto the decision thresholds.

---

## LLM Judge Details

### Judge Architecture

All judges inherit from a scancode-specific `BaseJudge` class (in `evaluation/llm/judges/base.py`) which itself extends the shared `BaseJudge` from `src/shared/evaluation/base_judge.py`. The inheritance chain provides:

- **Shared BaseJudge**: LLM client management, observability/tracing, prompt loading, response parsing
- **Scancode BaseJudge**: Analysis result loading from output directories, ground truth fixture loading, template-based prompt building with `{{ placeholder }}` substitution

Each judge implements four methods:
1. `dimension_name` (property) -- identifies the judge for prompt template lookup
2. `weight` (property) -- the judge's contribution to the combined LLM score
3. `collect_evidence()` -- gathers analysis results and ground truth into an evidence dictionary
4. `run_ground_truth_assertions()` -- pre-flight checks that fail-fast if required data is missing

The prompt template is automatically resolved from the `dimension_name`:

```python
@property
def prompt_file(self) -> Path:
    return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"
```

### License Accuracy Judge (30%)

**Class**: `LicenseAccuracyJudge`
**Prompt template**: `evaluation/llm/prompts/accuracy.md`
**Weight**: 0.30

**Sub-dimensions**:

| Sub-score | Focus |
|-----------|-------|
| `detection` (1-5) | Correctness of detected SPDX IDs compared to ground truth |
| `risk` (1-5) | Correctness of overall risk classification |

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Perfect match: all SPDX IDs correct, zero false positives/negatives |
| 4 | >90% accuracy, minor deviations in edge cases |
| 3 | >80% accuracy, some false positives or missed licenses |
| 2 | >70% accuracy, significant detection gaps |
| 1 | <70% accuracy, systematic detection failures |

**Evidence collected**:
- `analysis_results`: All analysis JSON files from the output directory
- `ground_truth`: All ground truth fixtures from `evaluation/ground-truth/`
- `evaluation_mode`: `"synthetic"` (default) or `"real_world"`
- `synthetic_baseline`: Expected licenses (`MIT`, `Apache-2.0`, `GPL-3.0`, `BSD-3-Clause`), minimum accuracy (0.80), tolerance (0.05)
- `interpretation_guidance`: Scoring guidance mapping accuracy percentages to 1-5 scores

**Ground truth assertions**:
- Analysis results must exist in output directory
- Ground truth fixtures must exist in `evaluation/ground-truth/`

### License Coverage Judge (25%)

**Class**: `LicenseCoverageJudge`
**Prompt template**: `evaluation/llm/prompts/coverage.md`
**Weight**: 0.25

**Sub-dimensions**:

| Sub-score | Focus |
|-----------|-------|
| `categories` (1-5) | Coverage of license categories (permissive, weak-copyleft, copyleft, none) |
| `files` (1-5) | Coverage of license files and SPDX headers across test repositories |

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All license categories represented, all file types detected across all repos |
| 4 | Most categories covered, minor gaps in file detection |
| 3 | Core categories covered, some missing edge cases |
| 2 | Significant category or file coverage gaps |
| 1 | Major coverage failures |

**Evidence collected**:
- `analysis_results`: All analysis JSON files
- `ground_truth`: All ground truth fixtures

**Ground truth assertions**:
- Analysis results must exist
- Ground truth fixtures must exist

### Risk Classification Judge (25%)

**Class**: `RiskClassificationJudge`
**Prompt template**: `evaluation/llm/prompts/risk_classification.md`
**Weight**: 0.25

**Sub-dimensions**:

| Sub-score | Focus |
|-----------|-------|
| `overall_risk` (1-5) | Correctness of the `overall_risk` level (low, medium, high, critical) |
| `category_flags` (1-5) | Accuracy of boolean flags (`has_permissive`, `has_copyleft`, `has_weak_copyleft`, `has_unknown`) |
| `risk_reasons` (1-5) | Appropriateness and clarity of `risk_reasons` explanations |

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | All risk levels correct, all category flags accurate, reasons are clear and complete |
| 4 | Risk levels mostly correct, minor flag issues, reasons adequate |
| 3 | Some risk misclassification, flags partially correct, reasons present but vague |
| 2 | Significant risk misclassification, multiple incorrect flags |
| 1 | Risk classification unreliable, flags systematically wrong |

**Risk Classification Rules** (embedded in prompt):

| Risk Level | Trigger Condition | Examples |
|------------|-------------------|----------|
| Low | Only permissive licenses | MIT, BSD, Apache-2.0 |
| Medium | Contains weak-copyleft licenses | LGPL, MPL |
| High | Contains unknown licenses or licenses requiring special handling | No license detected |
| Critical | Contains copyleft licenses with commercial risk | GPL, AGPL |

**Evidence collected**:
- `analysis_results`: All analysis JSON files
- `ground_truth`: All ground truth fixtures

**Ground truth assertions**:
- Analysis results must exist
- Ground truth fixtures must exist
- Each analysis result must contain an `overall_risk` field (checked within `data` or at top level)

### Actionability Judge (20%)

**Class**: `ActionabilityJudge`
**Prompt template**: `evaluation/llm/prompts/actionability.md`
**Weight**: 0.20

**Sub-dimensions**:

| Sub-score | Focus |
|-----------|-------|
| `clarity` (1-5) | Clarity of risk level and rationale |
| `guidance` (1-5) | Specificity of license findings and file locations; usability for remediation |

**Scoring Rubric**:

| Score | Criteria |
|-------|----------|
| 5 | Immediately actionable: clear risk level, specific file locations, concrete guidance for compliance teams |
| 4 | Actionable with minor clarification: risk and findings clear, some guidance could be more specific |
| 3 | Requires investigation: risk present but rationale unclear, file locations incomplete |
| 2 | Vague: risk level present but findings lack specificity, no remediation path |
| 1 | Not actionable: insufficient information for any compliance decision |

**Evidence collected**:
- `analysis_results`: All analysis JSON files (no ground truth needed -- this judge evaluates output quality independently)

**Ground truth assertions**:
- Analysis results must exist

---

## LLM Judge Confidence

Each judge reports a confidence level (0.0 to 1.0) alongside its score:

| Confidence | Interpretation | Action |
|------------|----------------|--------|
| >= 0.9 | High confidence, reliable score | Use directly |
| 0.7 - 0.9 | Moderate confidence, some uncertainty | Use with awareness of margin |
| < 0.7 | Low confidence, judge struggled to assess | Flag for manual review |

Ground truth assertions run before LLM invocation. If assertions fail, the judge can cap its score to prevent inflated results when fundamental data is missing.

---

## Evidence Collection

### Prompt Template Mechanism

Each judge has a corresponding Markdown prompt template in `evaluation/llm/prompts/`. The base judge loads the template and substitutes `{{ placeholder }}` tokens with serialized evidence:

```python
def build_prompt(self, evidence: dict[str, Any]) -> str:
    template = self.load_prompt_template()
    prompt = template
    for key, value in evidence.items():
        placeholder = f"{{{{ {key} }}}}"
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, indent=2)
        else:
            value_str = str(value)
        prompt = prompt.replace(placeholder, value_str)
    return prompt
```

### Evidence by Judge

| Judge | Evidence Keys | Data Source |
|-------|---------------|-------------|
| LicenseAccuracyJudge | `analysis_results`, `ground_truth`, `evaluation_mode`, `synthetic_baseline`, `interpretation_guidance` | Output dir + ground truth dir |
| LicenseCoverageJudge | `analysis_results`, `ground_truth` | Output dir + ground truth dir |
| RiskClassificationJudge | `analysis_results`, `ground_truth` | Output dir + ground truth dir |
| ActionabilityJudge | `analysis_results` | Output dir only |

### Analysis Result Loading

The base judge loads analysis results from two locations:
1. **Run subdirectories**: `outputs/<run-id>/output.json` -- keyed by run ID
2. **Direct JSON files**: `outputs/*.json` -- keyed by filename stem

It also supports the Caldera envelope format (`{"metadata": {...}, "data": {...}}`) and the legacy Vulcan format (`{"results": {...}}`), normalizing both into a flat structure via `normalize_analysis()` in `evaluate.py`.

---

## Ground Truth

### Methodology

Ground truth files define the expected analysis output for synthetic test repositories. Each file represents a controlled scenario with known licenses, risk levels, and detection patterns.

**Generation process**:
1. **Define scenario**: Choose a license configuration that tests a specific capability (single license, multi-license, copyleft risk, etc.)
2. **Create synthetic repository**: Build a minimal repository with the defined licenses (LICENSE files, SPDX headers in source files)
3. **Run ScanCode**: Analyze the synthetic repository to get baseline output
4. **Manual verification**: Confirm detected licenses, risk levels, and category flags against the known repository contents
5. **Document expected values**: Record verified values in the ground truth JSON file

### Synthetic Repositories (8 Total)

| Ground Truth File | Scenario | Licenses | Expected Risk | Key Test Focus |
|-------------------|----------|----------|---------------|----------------|
| `mit-only.json` | Single permissive license | MIT | low | Baseline detection, single license file + SPDX header |
| `apache-bsd.json` | Two permissive licenses | Apache-2.0, BSD-3-Clause | low | Multi-license permissive detection |
| `gpl-mixed.json` | Copyleft license | GPL-3.0-only | critical | Copyleft detection, commercial risk flagging |
| `multi-license.json` | Mixed license types | MIT, Apache-2.0, LGPL-2.1-only | medium | Multi-category detection (permissive + weak-copyleft) |
| `public-domain.json` | Public domain dedication | Unlicense | low | Unlicense/public domain detection |
| `no-license.json` | No license present | (none) | high | Missing license detection, unknown flag |
| `spdx-expression.json` | SPDX WITH expression | GPL-2.0-only WITH Classpath-exception-2.0 | medium | Complex SPDX expression parsing |
| `dual-licensed.json` | Dual licensing choice | MIT, Apache-2.0 | low | Dual-license OR choice detection |

### Ground Truth Schema

Every ground truth file follows this structure:

```json
{
  "repository": "<repo-name>",
  "description": "<human-readable description of the scenario>",
  "expected": {
    "total_licenses": <int>,
    "licenses": ["<SPDX-ID>", ...],
    "license_files_found": <int>,
    "files_with_licenses": <int>,
    "overall_risk": "<low|medium|high|critical>",
    "has_permissive": <bool>,
    "has_copyleft": <bool>,
    "has_weak_copyleft": <bool>,
    "has_unknown": <bool>,
    "license_counts": {"<SPDX-ID>": <int>, ...},
    "total_findings": <int>,
    "spdx_headers_found": <int>,
    "license_file_detections": <int>,
    "expected_findings": [
      {"file_path": "<path>", "spdx_id": "<SPDX-ID>", "match_type": "<file|header|spdx>"},
      ...
    ]
  },
  "thresholds": {
    "count_tolerance": <int>,
    "max_scan_time_ms": <int>,
    "min_files_per_second": <int>
  }
}
```

### Expected Value Formats

| Field | Type | Semantics |
|-------|------|-----------|
| `total_licenses` | int | Count of distinct SPDX license identifiers in the repository |
| `licenses` | list[str] | Sorted list of unique SPDX license identifiers |
| `license_files_found` | int | Count of dedicated license files (LICENSE, COPYING, etc.) |
| `files_with_licenses` | int | Count of files containing any license reference |
| `overall_risk` | str | One of: `low`, `medium`, `high`, `critical` |
| `has_permissive` | bool | True if any permissive license detected |
| `has_copyleft` | bool | True if any copyleft license detected |
| `has_weak_copyleft` | bool | True if any weak-copyleft license detected |
| `has_unknown` | bool | True if license status is unknown or missing |
| `license_counts` | dict[str, int] | Per-SPDX-ID count of detections |
| `total_findings` | int | Total number of individual findings |
| `spdx_headers_found` | int | Count of findings detected via SPDX header |
| `license_file_detections` | int | Count of findings detected via license file |
| `expected_findings` | list[dict] | Per-finding expected path, SPDX ID, and match type |

### Scenario Design Rationale

The 8 synthetic repositories are designed to cover the license detection matrix:

| Axis | Values Covered | Repos |
|------|----------------|-------|
| License category | permissive, copyleft, weak-copyleft, unknown, none | mit-only, gpl-mixed, multi-license, no-license, spdx-expression |
| License count | 0, 1, 2, 3 | no-license, mit-only, dual-licensed, multi-license |
| Detection method | file, spdx, header | All repos use file + spdx combinations |
| Risk level | low, medium, high, critical | mit-only (low), multi-license (medium), no-license (high), gpl-mixed (critical) |
| Edge cases | SPDX WITH expressions, public domain, dual-licensing | spdx-expression, public-domain, dual-licensed |

---

## Core Data Types

### CheckResult

Every programmatic check produces a `CheckResult` instance:

```python
@dataclass
class CheckResult:
    check_id: str      # e.g., "LA-1", "LC-3", "LD-5", "LP-2"
    category: str      # e.g., "Accuracy", "Coverage", "Detection", "Performance"
    passed: bool       # Binary pass/fail
    message: str       # Human-readable description of result
    expected: Any      # Expected value (for debugging)
    actual: Any        # Actual value (for debugging)
```

### EvaluationReport

Per-repository aggregation of check results:

```python
@dataclass
class EvaluationReport:
    repository: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    pass_rate: float          # passed_checks / total_checks
    results: list[CheckResult]
```

### Helper Functions

The check module provides reusable comparison helpers:

| Function | Purpose | Used By |
|----------|---------|---------|
| `check_equal()` | Compare expected vs actual with optional numeric tolerance | LA-1, LA-3, LA-4, LA-5 |
| `check_contains()` | Verify expected items are subset of actual items | LA-2 |
| `check_boolean()` | Compare boolean flags | LA-6, LA-7, LA-8, LA-9, LC-8 |
| `check_in_range()` | Verify value falls within [min, max] range | LP-1 |

---

## Evaluation Outputs

### Output Directory Structure

```
evaluation/
├── ground-truth/                          # Ground truth fixtures (8 JSON files)
│   ├── mit-only.json
│   ├── apache-bsd.json
│   ├── gpl-mixed.json
│   ├── multi-license.json
│   ├── public-domain.json
│   ├── no-license.json
│   ├── spdx-expression.json
│   └── dual-licensed.json
├── results/                               # Programmatic evaluation output
│   └── evaluation_report.json             # Full evaluation report
├── scorecard.json                         # Structured scorecard (JSON)
├── scorecard.md                           # Human-readable scorecard (Markdown)
└── llm/
    ├── judges/                            # Judge implementations
    ├── prompts/                           # Prompt templates
    └── results/                           # LLM evaluation results
        └── llm_evaluation.json            # Latest LLM evaluation
```

### Evaluation Report Format

```json
{
  "timestamp": "2026-02-13T10:00:00+00:00",
  "tool": "scancode",
  "version": "1.0.0",
  "decision": "STRONG_PASS",
  "score": 4.85,
  "summary": {
    "passed": 97,
    "failed": 3,
    "total": 100,
    "pass_rate": 0.97
  },
  "checks": [
    {
      "check_id": "LA-1",
      "name": "Total licenses found",
      "passed": true,
      "message": "Total licenses found: expected=1, actual=1",
      "repository": "mit-only",
      "category": "Accuracy"
    }
  ],
  "total_repositories": 8,
  "reports": [...]
}
```

### Scorecard Format

The scorecard JSON includes per-dimension breakdowns:

```json
{
  "tool": "scancode",
  "version": "1.0.0",
  "summary": {
    "total_checks": 100,
    "passed": 97,
    "failed": 3,
    "score": 0.97,
    "score_percent": 97.0,
    "normalized_score": 4.85,
    "decision": "STRONG_PASS"
  },
  "dimensions": [
    {
      "id": "D1",
      "name": "Accuracy",
      "weight": 0.25,
      "total_checks": 40,
      "passed": 39,
      "score": 4.88,
      "weighted_score": 1.22,
      "checks": [...]
    }
  ],
  "thresholds": {
    "STRONG_PASS": ">= 4.0 (80%+)",
    "PASS": ">= 3.5 (70%+)",
    "WEAK_PASS": ">= 3.0 (60%+)",
    "FAIL": "< 3.0 (below 60%)"
  }
}
```

---

## Running Evaluations

### Programmatic Evaluation

```bash
# Full evaluation (all repos, all checks)
make evaluate

# Direct invocation with custom paths
.venv/bin/python scripts/evaluate.py \
    --analysis-dir outputs \
    --ground-truth-dir evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json
```

The evaluator discovers analysis files by matching filenames against ground truth:
- Pattern 1: Direct JSON files in `outputs/` (e.g., `outputs/mit-only.json` matches `evaluation/ground-truth/mit-only.json`)
- Pattern 2: Subdirectories with `output.json` (e.g., `outputs/<run-id>/output.json` where the output's `repo_path` metadata matches a ground truth fixture)

### LLM Evaluation

```bash
# Full LLM evaluation (all 4 judges)
make evaluate-llm

# With custom model
make evaluate-llm LLM_MODEL=sonnet

# With custom timeout
make evaluate-llm LLM_TIMEOUT=300
```

The LLM evaluator invokes all four judges, each of which:
1. Runs ground truth assertions (fail-fast on missing data)
2. Collects evidence from analysis results and ground truth
3. Builds a prompt from the template with evidence substitution
4. Invokes the LLM (default model: `opus-4.5`)
5. Parses the JSON response into a `JudgeResult`

### Full Pipeline

```bash
# Build synthetic repos, analyze, and evaluate
make build-repos
make analyze REPO_PATH=eval-repos/synthetic
make evaluate
make evaluate-llm

# Or use the all-in-one target
make all
```

### Viewing Results

```bash
# View programmatic scorecard
cat evaluation/scorecard.md

# View structured results
cat evaluation/scorecard.json | python -m json.tool

# View LLM evaluation
cat evaluation/results/llm_evaluation.json | python -m json.tool
```

---

## Extending the Evaluation

### Adding a New Programmatic Check

1. Choose the appropriate check module in `scripts/checks/`:
   - `accuracy.py` for license detection correctness
   - `coverage.py` for output completeness
   - `detection.py` for detection method quality
   - `performance.py` for timing and throughput

2. Add the check function, returning a `CheckResult`:
   ```python
   results.append(
       CheckResult(
           check_id="LA-15",
           category="Accuracy",
           passed=condition,
           message=f"Description: expected={expected}, actual={actual}",
           expected=expected,
           actual=actual,
       )
   )
   ```

3. The check is automatically picked up by `evaluate.py` since it calls `run_*_checks()` which returns all results from the module.

4. Update ground truth files if the new check requires additional expected values.

5. Update this document with the new check ID, name, severity, and pass criteria.

### Adding a New LLM Judge

1. Create a new judge class in `evaluation/llm/judges/<dimension>.py`:
   ```python
   class NewDimensionJudge(BaseJudge):
       @property
       def dimension_name(self) -> str:
           return "new_dimension"

       @property
       def weight(self) -> float:
           return 0.XX  # Adjust weights to sum to 1.0

       def collect_evidence(self) -> dict[str, Any]:
           return {"analysis_results": self.load_all_analysis_results()}

       def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
           ...
   ```

2. Create a prompt template at `evaluation/llm/prompts/new_dimension.md` with `{{ placeholder }}` tokens matching the evidence keys.

3. Register the judge in `evaluation/llm/judges/__init__.py`.

4. Register in the LLM evaluation orchestrator (`scripts/llm_evaluate.py`).

5. Adjust existing judge weights so all weights sum to 1.0.

6. Update this document.

### Adding a New Ground Truth Scenario

1. Define the scenario: choose licenses, risk level, and detection patterns.

2. Create a synthetic repository in `eval-repos/synthetic/<repo-name>/` with appropriate license files and SPDX headers.

3. Run analysis: `make analyze REPO_PATH=eval-repos/synthetic/<repo-name>`

4. Manually verify the output against expected values.

5. Create `evaluation/ground-truth/<repo-name>.json` following the ground truth schema above.

6. Re-run evaluation to verify the new scenario passes: `make evaluate`

---

## Input Normalization

The evaluator handles multiple output formats via `normalize_analysis()`:

| Format | Detection | Normalization |
|--------|-----------|---------------|
| Caldera envelope | `"data"` and `"metadata"` keys present | Merges `data` as top-level; copies `schema_version`, `repo_name`, `repo_path`, `timestamp`, `tool_name`, `tool_version` from metadata |
| Legacy Vulcan | `"results"` key present | Unwraps `results` as top-level; copies `schema_version`, `repo_name`, `repo_path`, `generated_at` from outer object |
| Already normalized | Neither pattern matches | Returns as-is |

This ensures the evaluation checks work consistently regardless of the output format produced by the analysis script.

---

## References

- [ScanCode Toolkit](https://github.com/nexB/scancode-toolkit)
- [SPDX License List](https://spdx.org/licenses/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
- [Project Caldera EVAL_STRATEGY template](../../docs/templates/EVAL_STRATEGY.md.template)
