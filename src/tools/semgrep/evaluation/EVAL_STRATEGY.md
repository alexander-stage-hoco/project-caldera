# Evaluation Strategy: Semgrep Code Smell & Security Analysis

This document describes the evaluation methodology for the Semgrep code smell and security vulnerability detection tool.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- validates detection accuracy, coverage, output quality, and performance |
| LLM Judges | 40% | Semantic understanding, contextual accuracy, actionability, and security depth assessment |

This hybrid approach provides both precision and nuance. Programmatic checks enforce hard constraints (schema validity, field presence, detection rates against ground truth), while LLM judges assess subjective qualities that resist simple codification (message clarity, contextual appropriateness of findings, severity calibration).

Semgrep occupies a unique position as both a **code smell detector** and a **security vulnerability scanner**. The evaluation reflects this dual purpose: accuracy checks validate smell detection (empty catch, catch-all, async void), while security checks (SC-1 through SC-6) and the dedicated SecurityDetectionJudge validate OWASP Top 10 coverage, CWE mapping, and injection detection rates.

The tool supports three ruleset tiers, each expanding detection scope:

| Tier | Environment Variable | Languages Added | Categories Added |
|------|---------------------|-----------------|------------------|
| Base | (always enabled) | Python, JavaScript, TypeScript, C# | 10 DD base categories |
| Multi-Lang | `SEMGREP_USE_MULTI_LANG=1` | Java, Go | correctness, best_practice, performance |
| Elttam Audit | `SEMGREP_USE_ELTTAM=1` | Rust | entrypoint_discovery, audit |

Evaluation adapts dynamically: coverage assertions and LLM judge expectations adjust based on which rulesets are enabled.

---

## Dimension Summary

### Programmatic Dimensions

Categories are equally weighted. Each category's score is the average of its check scores (0.0-1.0), then the overall programmatic score is the average across all categories.

| Dimension | Check Count | Purpose |
|-----------|-------------|---------|
| Accuracy | 9 (AC-1 to AC-9) | Smell detection precision against ground truth |
| Coverage | 8 (CV-1 to CV-8) | Language and DD category breadth |
| Edge Cases | 8 (EC-1 to EC-8) | Robustness on unusual inputs |
| Output Quality | 3 (OQ-1 to OQ-3) | Schema compliance and field completeness |
| Integration Fit | 2 (IF-1 to IF-2) | Pipeline compatibility (paths, required fields) |
| Performance | 4 (PF-1 to PF-4) | Speed, throughput, startup overhead |

**Security checks** (SC-1 to SC-6) are defined in `scripts/checks/security.py` and exported from the checks module but are not included in the main `evaluate.py` runner. They are available for standalone invocation.

### LLM Judge Dimensions

| Judge | Weight | Dimension | Sub-Dimensions |
|-------|--------|-----------|----------------|
| Smell Accuracy | 35% | `smell_accuracy` | True Positives (40%), Category Accuracy (30%), Location Accuracy (30%) |
| Rule Coverage | 25% | `rule_coverage` | Language Coverage (40%), Category Coverage (35%), Rule Variety (25%) |
| False Positive Rate | 20% | `false_positive_rate` | Clean File Precision (40%), Contextual Appropriateness (35%), Severity Calibration (25%) |
| Actionability | 20% | `actionability` | Message Clarity (40%), Fix Suggestions (30%), Location Precision (30%) |

A fifth judge, **Security Detection** (weight 40%), is available for security-focused evaluations and can be run alongside or instead of the general judges.

| Judge | Weight | Dimension | Sub-Dimensions |
|-------|--------|-----------|----------------|
| Security Detection | 40% | `security_detection` | Injection Detection (40%), OWASP Coverage (30%), CWE Mapping (30%) |

---

## Check Catalog

### Accuracy Checks (AC-1 to AC-9)

These checks validate smell detection accuracy against ground truth data.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| AC-1 | SQL injection detection | Detected count >= 50% of expected from ground truth | `detected`, `expected` counts |
| AC-2 | Empty catch detection | Detection rate >= 50% of expected D1_EMPTY_CATCH count; passes with 0.5 score if no expectations | `detected`, `expected`, `note` about custom rules |
| AC-3 | Catch-all detection | Detection rate >= 50% of expected D2_CATCH_ALL count | `detected`, `expected` counts |
| AC-4 | Async void detection | Detection rate >= 50% of expected E2_ASYNC_VOID (C# specific) | `detected`, `expected` counts |
| AC-5 | HttpClient/HTTP-related detection | Any HTTP-related issues detected (score 1.0 if found, 0.5 otherwise) | `detected` count (includes SSRF, HTTP-related keywords) |
| AC-6 | High complexity detection | Always passes (neutral score 0.5); Semgrep is not a complexity analyzer | `detected` count, `note` directing to Lizard tool |
| AC-7 | God class detection | Always passes (neutral score 0.5); structural detection not Semgrep's focus | `detected` count |
| AC-8 | Overall detection quality | Categorization rate >= 80% (properly categorized / total smells) | `total_smells`, `unknown_smells`, `categorized_smells`, `security_smells` |
| AC-9 | Line number accuracy | Line accuracy >= 70% (exact + near matches within +/-2 tolerance) | `exact_matches`, `near_matches`, `total_expected`, `per_smell_accuracy`, `worst_performers` |

#### AC-9 Scoring Detail

Line number accuracy uses a tolerance-based matching system:

```python
# For each expected line number:
if detected_line == expected_line:
    exact_match += 1
elif abs(detected_line - expected_line) <= 2:
    near_match += 1
else:
    missed += 1

line_accuracy = (exact + near) / total_expected
```

Per-smell-type statistics are tracked, and the 5 worst-performing smell types are reported for diagnostic focus.

### Coverage Checks (CV-1 to CV-8)

These checks validate language and category coverage breadth.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| CV-1 | Python coverage | Language files analyzed (files > 0) | `files_analyzed`, `smells_detected`, `categories_covered` |
| CV-2 | JavaScript coverage | Language files analyzed (files > 0) | `files_analyzed`, `smells_detected`, `categories_covered` |
| CV-3 | TypeScript coverage | Language files analyzed (files > 0) | `files_analyzed`, `smells_detected`, `categories_covered` |
| CV-4 | C# coverage | Language files analyzed (files > 0) | `files_analyzed`, `smells_detected`, `categories_covered` |
| CV-5 | Java coverage | Language files analyzed (files > 0) | `files_analyzed`, `smells_detected`, `categories_covered` |
| CV-6 | Go coverage | Language files analyzed (files > 0) | `files_analyzed`, `smells_detected`, `categories_covered` |
| CV-7 | Rust coverage | Language files analyzed (files > 0) | `files_analyzed`, `smells_detected`, `categories_covered` |
| CV-8 | DD category coverage | At least one category has detections | `total_categories`, `categories_detected`, `coverage_percentage`, `by_category` |

#### CV-1 to CV-7 Scoring Formula

Each per-language coverage check uses a composite score:

```python
score = 0.0
if files > 0:
    score += 0.4       # 40%: language files were analyzed
if smells > 0:
    score += 0.3       # 30%: at least one smell detected
if len(categories) > 0:
    score += 0.3 * min(len(categories) / 3, 1.0)  # 30%: category diversity (max at 3+)
```

#### CV-8 Scoring Formula

Category coverage uses a security-weighted scoring model:

```python
security_weight = 0.4                  # Security is 40% of score
other_weight = 0.6 / (len(SMELL_CATEGORIES) - 1)  # Remaining 60% split among other categories
bonus = 0.1 if unknown_category_has_findings else 0  # Small bonus for additional detection
category_score = min(security_component + other_components + bonus, 1.0)
```

### Edge Case Checks (EC-1 to EC-8)

These checks validate robustness on unusual inputs and boundary conditions.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| EC-1 | Empty files handling | Analysis completes without crash | `total_files_analyzed` |
| EC-2 | Unicode content handling | Unicode files processed without errors | (implicit -- passes if analysis succeeds) |
| EC-3 | Large files handling | Analysis succeeds; score 1.0 if files > 500 LOC exist, 0.5 otherwise | `large_files_count`, `largest_file` (LOC) |
| EC-4 | Deep nesting handling | Analysis completes without crash | (implicit -- passes if analysis succeeds) |
| EC-5 | Mixed language files (JS/TS) | Processes JS/TS files; score 1.0 if found, 0.5 otherwise | `mixed_language_files` count |
| EC-6 | No false positives in clean files | Zero smells detected in files containing "no_smell" in path | `clean_files_tested`, `false_positives` count, `false_positive_files` list |
| EC-7 | Syntax error tolerance | Analysis completes (Semgrep is inherently tolerant) | (implicit -- passes if analysis succeeds) |
| EC-8 | Path handling | At least one file path processed | `paths_processed` count |

#### EC-6 Scoring Formula

```python
# Files with "no_smell" in path should have 0 detected smells
false_positives = [f for f in no_smell_files if f.smell_count > 0]
passed = len(false_positives) == 0
score = 1.0 if passed else max(0, 1.0 - (len(false_positives) / len(no_smell_files)))
```

### Output Quality Checks (OQ-1 to OQ-3)

These checks validate schema compliance and structural correctness.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| OQ-1 | Required sections present | All 6 required top-level sections exist: `tool`, `tool_version`, `summary`, `directories`, `files`, `by_language` | `missing_sections` list |
| OQ-2 | File entries include required fields | All file objects contain: `path`, `language`, `lines`, `smell_count`, `smells` | `total_files`, `files_missing_fields` count |
| OQ-3 | Schema validation | Full output validates against `schemas/output.schema.json` (Draft 2020-12) | `errors` list (first 5 errors) |

### Integration Fit Checks (IF-1 to IF-2)

These checks validate compatibility with the SoT engine pipeline.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| IF-1 | Relative file paths | Zero absolute paths and zero paths embedding the root directory | `absolute_paths` count, `embedded_root` count, `root_path` |
| IF-2 | Smell entries include required fields | All smell objects contain: `dd_smell_id`, `dd_category`, `line_start`, `line_end`, `severity` | `total_smells`, `smells_missing_fields` count |

#### IF-1 Scoring Formula

```python
path_score = 1.0 if total_files == 0 else max(0.0, 1.0 - ((absolute_paths + embedded_root) / total_files))
```

### Performance Checks (PF-1 to PF-4)

These checks validate speed and efficiency. Can be skipped with `--quick` flag.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| PF-1 | Synthetic repo analysis speed | Completed in < 45s (accounts for Semgrep rule download on first run) | `duration_ms`, `duration_s`, `threshold_s` |
| PF-2 | Per-file analysis efficiency | < 1000ms per file | `total_files`, `ms_per_file`, `threshold_ms` |
| PF-3 | Analysis throughput | >= 100 LOC/s | `total_lines`, `lines_per_second`, `threshold_loc_per_s` |
| PF-4 | Startup overhead | Estimated startup < 90% of total time | `total_duration_s`, `startup_ratio`, `note` about rule caching |

#### PF-1 Scoring Formula

```python
pf1_score = min(1.0, threshold / max(duration_s, 0.1))
```

#### PF-4 Startup Estimation

```python
# Assume 100ms/file as analysis baseline; remainder attributed to startup
startup_estimate_s = max(duration_s - (total_files * 0.1), 0)
startup_ratio = startup_estimate_s / max(duration_s, 0.001)
pf4_score = 1.0 - min(startup_ratio, 1.0)
```

### Security Checks (SC-1 to SC-6) -- Available But Not In Main Runner

These checks are defined in `scripts/checks/security.py` and can be invoked standalone. They are not included in the default `evaluate.py` execution.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| SC-1 | CWE ID presence | Accuracy | >= 80% of security findings have CWE IDs | `total_security_findings`, `findings_with_cwe`, `cwe_rate`, `missing_cwe_samples` |
| SC-2 | OWASP Top 10 coverage | Coverage | >= 2 OWASP categories detected (or < 5 total security findings) | `total_security_findings`, `findings_mapped_to_owasp`, `owasp_categories_detected`, `owasp_breakdown` |
| SC-3 | SQL injection detection | Accuracy | Detection rate >= 80% of expected from ground truth | `expected`, `detected`, `detection_rate` |
| SC-4 | XSS detection | Accuracy | Detection rate >= 70% of expected from ground truth | `expected`, `detected`, `detection_rate` |
| SC-5 | Command injection detection | Accuracy | Detection rate >= 70% of expected from ground truth | `expected`, `detected`, `detection_rate` |
| SC-6 | Security severity distribution | Accuracy | >= 80% of security findings have known severity (ERROR, WARNING, INFO) | `total_security_findings`, `severity_distribution`, `severity_assignment_rate` |

SC-1 and SC-2 use OWASP Top 10 2021 mappings with keyword and CWE-based classification. The security check module maintains a mapping table (`SECURITY_SMELL_OWASP_MAP`) covering 14 security smell IDs to their OWASP categories (A01-A10).

---

## Scoring

### Programmatic Score Calculation

The overall programmatic score is the simple average of all individual check scores:

```python
@property
def score(self) -> float:
    """Overall score (0.0 to 1.0)."""
    if not self.checks:
        return 0.0
    return sum(c.score for c in self.checks) / len(self.checks)
```

Category-level scores are also simple averages of their constituent checks:

```python
@property
def score_by_category(self) -> dict[str, float]:
    categories = {}
    for check in self.checks:
        categories.setdefault(check.category.value, []).append(check.score)
    return {cat: sum(scores) / len(scores) for cat, scores in categories.items()}
```

### Scorecard Normalization

For the scorecard output, raw scores (0.0-1.0) are normalized to a 0-5 scale:

```python
normalized_score = raw_score * 5.0
```

Dimension weights in the scorecard are equal (1/N where N = number of active categories):

```python
weight = 1.0 / len(score_by_category)
weighted_score = score * 5.0 / len(score_by_category)
```

### Combined Score Calculation

When both programmatic and LLM evaluations are run:

```python
combined_score = (programmatic_score * 0.60) + (llm_score * 0.40)
```

### LLM Judge Score Aggregation

Each LLM judge produces a score on a 1-5 scale. The weighted LLM score is:

```python
llm_score = (
    smell_accuracy_score * 0.35 +
    rule_coverage_score * 0.25 +
    false_positive_rate_score * 0.20 +
    actionability_score * 0.20
)
```

When the SecurityDetectionJudge is used (security-focused evaluation):

```python
llm_score = security_detection_score * 0.40 + (other_judges_weighted * 0.60)
```

---

## Decision Thresholds

Decisions are based on the normalized score (0-5 scale):

| Decision | Score Range | Interpretation |
|----------|------------|----------------|
| STRONG_PASS | >= 4.0 (80%+) | Excellent, production-ready |
| PASS | >= 3.5 (70%+) | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 (60%+) | Acceptable with caveats |
| FAIL | < 3.0 (below 60%) | Significant issues, not ready |

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

The process exit code is 0 if score >= 0.5 (50%), otherwise 1:

```python
sys.exit(0 if report.score >= 0.5 else 1)
```

---

## Ground Truth

### Methodology

Ground truth files are stored in `evaluation/ground-truth/` as per-language JSON files. Each file follows schema version 1.1 and contains:

1. **Configuration metadata**: Which rulesets are required for specific detections
2. **File-level expectations**: Expected smell IDs, counts, and line numbers per source file
3. **Ruleset-conditional entries**: Some files require `SEMGREP_USE_MULTI_LANG=1` or `SEMGREP_USE_ELTTAM=1`

### Generation Process

1. **Analyze synthetic repos**: Run Semgrep against purpose-built code samples containing known smells
2. **Manual line verification**: Cross-reference detected line numbers with actual vulnerability/smell locations in source
3. **Reconcile counts**: Ensure `count` fields match the number of entries in `lines` arrays
4. **Document exceptions**: Add `notes` fields explaining detection limitations or line offsets

### Ground Truth Files

| File | Language | Total Expected Smells | Smell Categories Covered |
|------|----------|----------------------|--------------------------|
| `python.json` | Python | 40 | error_handling, api_design, resource_management, security, correctness, best_practice, performance, entrypoint_discovery |
| `javascript.json` | JavaScript | (varies) | error_handling, security, best_practice |
| `typescript.json` | TypeScript | (varies) | error_handling, async_concurrency, security |
| `csharp.json` | C# | (varies) | error_handling, async_concurrency, resource_management, nullability |
| `java.json` | Java | (varies) | error_handling, security, resource_management |
| `go.json` | Go | (varies) | error_handling, security, concurrency |
| `rust.json` | Rust | (varies) | security, resource_management |

### Ground Truth Entry Schema

```json
{
  "schema_version": "1.1",
  "scenario": "python",
  "description": "Ground truth for Python smell and security vulnerability detection",
  "generated_at": "2026-02-04T00:00:00Z",
  "repo_path": "eval-repos/synthetic/python",
  "configuration": {
    "base_rulesets": ["DD custom rules"],
    "multi_lang_rulesets": ["p/python"],
    "elttam_rulesets": ["elttam/rules-audit"],
    "notes": "Expected detections vary based on enabled rulesets"
  },
  "expected": {
    "language": "python",
    "summary": {
      "total_files": 12,
      "total_expected_smells": 40,
      "smell_categories_covered": ["error_handling", "security", "..."]
    }
  },
  "files": {
    "sql_injection.py": {
      "expected_smells": [
        {
          "smell_id": "SQL_INJECTION",
          "count": 5,
          "lines": [13, 22, 31, 39, 47]
        }
      ],
      "total_expected": 5,
      "notes": "Lines indicate where vulnerable query string is constructed"
    }
  }
}
```

### Expected Value Formats

Ground truth entries support two count formats:

| Field | Type | Usage |
|-------|------|-------|
| `count` | int | Exact expected count (strict comparison) |
| `min_count` | int | Minimum expected count (flexible, used for multi-lang/elttam rules) |

When both are absent, the check defaults to 0. The helper function resolves this:

```python
def _get_expected_count(smell: dict) -> int:
    return smell.get("count", smell.get("min_count", 0))
```

### Synthetic Test Repositories

Each ground truth file corresponds to a synthetic repository in `eval-repos/synthetic/<language>/`:

| Scenario | Purpose | Key Test Files |
|----------|---------|---------------|
| python | Python smell and security detection | `sql_injection.py`, `empty_catch.py`, `catch_all.py`, `no_smells.py`, `command_injection.py`, `entrypoint_patterns.py` |
| javascript | JavaScript smell detection | error handling, security patterns |
| typescript | TypeScript smell detection | async patterns, security |
| csharp | C# smell detection | async void, HttpClient, IDisposable |
| java | Java smell detection | error handling, resource management |
| go | Go smell detection | error handling, concurrency |
| rust | Rust smell detection | security, memory safety |

### DD Smell Categories

The evaluation tracks 13 DD smell categories:

| Category | Description | Example Smell IDs |
|----------|-------------|-------------------|
| size_complexity | Method/class size issues | A2_HIGH_CYCLOMATIC |
| refactoring | Code needing restructure | B6_MESSAGE_CHAINS |
| dependency | Coupling problems | C3_GOD_CLASS |
| error_handling | Exception handling issues | D1_EMPTY_CATCH, D2_CATCH_ALL |
| async_concurrency | Async/threading issues | E2_ASYNC_VOID |
| resource_management | Resource leaks | F2_MISSING_USING, F3_HTTPCLIENT_NEW |
| nullability | Null handling problems | G1_NULLABLE_DISABLED |
| api_design | Interface issues | H2_LONG_PARAM_LIST |
| dead_code | Unreachable code | I3_UNREACHABLE_CODE |
| security | Injection, exposure issues | SQL_INJECTION, XSS, COMMAND_INJECTION |
| correctness | Logic errors, boundary issues | CORRECTNESS_ISSUE |
| best_practice | Anti-patterns, deprecated APIs | UNSAFE_DESERIALIZATION |
| performance | Inefficient patterns | F4_EXCESSIVE_ALLOCATION |

---

## LLM Judge Details

### Smell Accuracy Judge (35%)

**Class**: `SmellAccuracyJudge`
**Prompt file**: `evaluation/llm/prompts/smell_accuracy.md`
**Prompt template placeholders**: `{{ sample_smells }}`, `{{ ground_truth_comparison }}`, `{{ by_category }}`, `{{ total_smells }}`, `{{ total_files }}`, `{{ files_with_smells }}`, `{{ categories_covered }}`, `{{ gt_expectations }}`, `{{ evaluation_mode }}`, `{{ interpretation_guidance }}`, `{{ synthetic_baseline }}`

**Sub-dimensions and weights**:

| Sub-Dimension | Weight | What It Measures |
|---------------|--------|-----------------|
| True Positives | 40% | Detected smells are actual code quality issues |
| Category Accuracy | 30% | DD categories correctly assigned |
| Location Accuracy | 30% | Line numbers and file paths are correct |

**Scoring Rubric (1-5)**:

| Score | Criteria |
|-------|----------|
| 5 | All smells genuine, correct categories, accurate locations |
| 4 | 90%+ accuracy, minor category mismatches |
| 3 | 70%+ accuracy, some incorrect categorizations |
| 2 | Significant errors (>30% incorrect) |
| 1 | Many false detections or systematic failures |

**Ground truth assertions**: Validates smell counts are within expected ranges per file, all smells have `rule_id` and `line_start` fields.

**Evidence collection**: Loads all analysis outputs, aggregates files across repos, samples first 20 smells for LLM review, builds ground truth comparison with expected count ranges, and computes per-category breakdown.

### Rule Coverage Judge (25%)

**Class**: `RuleCoverageJudge`
**Prompt file**: `evaluation/llm/prompts/rule_coverage.md`
**Prompt template placeholders**: `{{ language_stats }}`, `{{ category_stats }}`, `{{ languages_covered }}`, `{{ languages_missing }}`, `{{ categories_covered }}`, `{{ categories_missing }}`, `{{ language_coverage_pct }}`, `{{ category_coverage_pct }}`, `{{ total_unique_rules }}`, `{{ sample_rules }}`, `{{ total_smells }}`, `{{ total_files }}`, `{{ evaluation_mode }}`, `{{ interpretation_guidance }}`, `{{ synthetic_baseline }}`

**Sub-dimensions and weights**:

| Sub-Dimension | Weight | What It Measures |
|---------------|--------|-----------------|
| Language Coverage | 40% | All target languages detected |
| Category Coverage | 35% | All enabled DD categories addressed |
| Rule Variety | 25% | Sufficient diversity of unique rules |

**Scoring Rubric (1-5)**:

| Score | Criteria |
|-------|----------|
| 5 | 100% language + category coverage, rich rule variety |
| 4 | 85%+ coverage, minor gaps in niche categories |
| 3 | 60%+ coverage, gaps in 2-3 categories/languages |
| 2 | 40%+ coverage, significant gaps |
| 1 | <40% coverage, critical gaps |

**Ground truth assertions**: Minimum 3 languages (or 50% of targets), minimum 3 DD categories (or 30% of enabled), minimum 5 unique rules. In `real_world` mode with a validated synthetic baseline (STRONG_PASS or PASS), strict assertions are skipped -- the tool was already validated.

### False Positive Rate Judge (20%)

**Class**: `FalsePositiveRateJudge`
**Prompt file**: `evaluation/llm/prompts/false_positive_rate.md`
**Prompt template placeholders**: `{{ clean_file_results }}`, `{{ potential_false_positives }}`, `{{ severity_distribution }}`, `{{ total_smells }}`, `{{ fp_in_clean_files }}`, `{{ clean_files_tested }}`, `{{ precision_estimate }}`, `{{ total_files }}`, `{{ files_with_smells }}`

**Sub-dimensions and weights**:

| Sub-Dimension | Weight | What It Measures |
|---------------|--------|-----------------|
| Clean File Precision | 40% | Files marked clean have zero smells |
| Contextual Appropriateness | 35% | Detections are contextually valid |
| Severity Calibration | 25% | Severity levels are not inflated |

**Scoring Rubric (1-5)**:

| Score | Criteria |
|-------|----------|
| 5 | <5% FP rate, clean files have 0 smells |
| 4 | 5-10% FP rate, rare false alarms |
| 3 | 10-20% FP rate, occasional false alarms |
| 2 | 20-40% FP rate, significant noise |
| 1 | >40% FP rate, many false alarms |

**Ground truth assertions**: (1) Files with "no_smell" or "no_smells" in path must have 0 smells detected. (2) Severity inflation check: no more than 80% of findings can be marked HIGH.

**Potential FP heuristics**: Messages containing "consider", "may be", "might", or severity "INFO" are flagged as potential false positives for LLM review.

### Actionability Judge (20%)

**Class**: `ActionabilityJudge`
**Prompt file**: `evaluation/llm/prompts/actionability.md`
**Prompt template placeholders**: `{{ sample_messages }}`, `{{ total_messages_sampled }}`, `{{ with_fix_suggestion }}`, `{{ fix_suggestion_rate }}`, `{{ avg_message_length }}`, `{{ severity_usage }}`, `{{ location_quality }}`, `{{ has_line_rate }}`, `{{ total_smells }}`, `{{ total_files }}`, `{{ evaluation_mode }}`, `{{ interpretation_guidance }}`, `{{ synthetic_baseline }}`

**Sub-dimensions and weights**:

| Sub-Dimension | Weight | What It Measures |
|---------------|--------|-----------------|
| Message Clarity | 40% | Messages explain the issue clearly |
| Fix Suggestions | 30% | Actionable remediation advice provided |
| Location Precision | 30% | Exact file, line, and range specified |

**Scoring Rubric (1-5)**:

| Score | Criteria |
|-------|----------|
| 5 | Clear messages, fix suggestions, precise locations, useful severity |
| 4 | Good messages, some fix suggestions, accurate locations |
| 3 | Adequate messages, few fix suggestions |
| 2 | Vague messages, no fix suggestions, imprecise locations |
| 1 | Unclear/unhelpful messages, missing critical info |

**Ground truth assertions**: All smells must have non-empty `message`, `severity`, and `line_start` fields.

**Fix suggestion detection**: Presence of keywords "use ", "instead", "should", "consider", "replace" in message text.

### Security Detection Judge (40% -- security evaluation mode)

**Class**: `SecurityDetectionJudge`
**Prompt file**: `evaluation/llm/prompts/security_detection.md`
**Prompt template placeholders**: `{{ evidence }}`, `{{ evaluation_mode }}`, `{{ interpretation_guidance }}`, `{{ synthetic_baseline }}`

**Sub-dimensions and weights**:

| Sub-Dimension | Weight | What It Measures |
|---------------|--------|-----------------|
| Injection Detection | 40% | SQL, XSS, command, code injection accuracy |
| OWASP Coverage | 30% | Breadth of OWASP Top 10 categories detected |
| CWE Mapping | 30% | Proper CWE IDs assigned to findings |

**Scoring Rubric (1-5)**:

| Score | Criteria |
|-------|----------|
| 5 | >90% security detection, all OWASP categories covered, injection rate >95% |
| 4 | 80-90% detection, most OWASP categories, injection rate >85% |
| 3 | 70-80% detection, several OWASP categories, injection rate >70% |
| 2 | 50-70% detection, limited OWASP coverage, injection rate 50-70% |
| 1 | <50% detection, poor OWASP coverage, unreliable injection detection |

**Ground truth assertions** (score capped to max 2 on failure):
1. SQL injection detection rate >= 80%
2. At least 2 OWASP categories detected when security findings exist
3. Overall security detection rate >= 50%

**Evidence structure**: Tracks injection types (SQL, command, XSS, code), cryptographic issues (weak cipher, weak hash, hardcoded secret), authentication issues (auth bypass, hardcoded credential), OWASP category breakdown, and CWE ID extraction.

**OWASP mapping**: Uses a dual approach -- keyword matching against 10 OWASP categories, and CWE-to-OWASP lookup tables covering 200+ CWE IDs.

---

## Confidence Requirements

### LLM Judge Confidence

Each judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review recommended |

### Ground Truth Score Capping

The SecurityDetectionJudge caps LLM scores when ground truth assertions fail:

```python
def evaluate(self) -> JudgeResult:
    gt_passed, gt_failures = self.run_ground_truth_assertions()

    # ... invoke LLM and parse response ...

    # Cap score if assertions failed
    if not gt_passed:
        original_score = result.score
        result.score = min(result.score, 2)  # Max score of 2 if GT fails
```

This ensures that even a generous LLM assessment cannot override hard ground truth failures for critical security detection capabilities.

### Real-World Evaluation Mode

When `evaluation_mode == "real_world"`, judges adopt relaxed expectations:

- Low or zero smell counts are NOT automatic failures
- Output quality, schema compliance, and categorization accuracy are prioritized
- A validated synthetic baseline (STRONG_PASS or PASS) unlocks lenient coverage assertions
- Synthetic evaluation context is injected into LLM prompts for calibration

---

## Evidence Collection

### Evidence Types by Category

| Check Category | Evidence Collected |
|----------------|-------------------|
| Accuracy | Detected vs expected counts per smell type, line match statistics (exact/near/missed), per-smell-type accuracy, worst performers |
| Coverage | Per-language file/smell/category counts, DD category detection rates, security-weighted scoring |
| Edge Cases | Clean file false positives, large file counts, mixed language file counts, path processing counts |
| Output Quality | Missing sections list, files missing required fields, JSON Schema validation errors |
| Integration Fit | Absolute path counts, embedded root counts, smells missing required DD fields |
| Performance | Duration (ms/s), per-file efficiency (ms/file), throughput (LOC/s), startup ratio |
| Security | CWE IDs, OWASP category mappings, injection type breakdowns, severity distributions |

### LLM Judge Evidence

Each LLM judge collects rich evidence dictionaries that are serialized into the prompt template:

- **SmellAccuracyJudge**: 20 sample smells, ground truth comparison per file, per-category breakdown, summary statistics
- **RuleCoverageJudge**: Per-language statistics (files, smells, categories, sample rules), per-category statistics, configuration info (which rulesets enabled)
- **FalsePositiveRateJudge**: Clean file results, potential false positives (up to 10), severity distribution, precision estimate
- **ActionabilityJudge**: Sample messages (up to 20, max 3 per file), fix suggestion rate, average message length, severity usage, location quality assessment
- **SecurityDetectionJudge**: OWASP category breakdown, injection detection by type, crypto/auth detection, CWE IDs, ground truth comparison, assertion results

---

## Running Evaluation

### Programmatic Evaluation

```bash
# Full evaluation with verbose output
make evaluate

# Quick evaluation (skip performance checks)
make evaluate-quick

# JSON-only output
make evaluate-json

# Direct invocation
.venv/bin/python -m scripts.evaluate \
    --analysis outputs/<run-id>/output.json \
    --ground-truth evaluation/ground-truth \
    --output evaluation/results/eval_report.json
```

### LLM Evaluation

```bash
# Full LLM evaluation (4 judges, default model)
make evaluate-llm

# Focused evaluation (single judge)
make evaluate-llm-focused

# Combined programmatic + LLM evaluation
make evaluate-combined

# Full pipeline: programmatic + LLM
make evaluate-full

# Override model
make evaluate-llm LLM_MODEL=opus
```

### Evaluation Outputs

All evaluation artifacts are written to `evaluation/results/`:

```
evaluation/results/
  evaluation_report.json    # Programmatic evaluation report (compliance format)
  scorecard.json            # Structured scorecard with dimensions
  scorecard.md              # Human-readable markdown scorecard
  llm_evaluation.json       # LLM judge results (if run)
```

---

## Extending the Evaluation

### Adding New Programmatic Checks

1. Create or edit the check function in the appropriate module under `scripts/checks/`:
   - `accuracy.py` for detection accuracy checks
   - `coverage.py` for coverage checks
   - `edge_cases.py` for edge case handling
   - `output_quality.py` for schema and field validation
   - `integration_fit.py` for pipeline compatibility
   - `performance.py` for speed and efficiency
   - `security.py` for security-specific checks
2. Return a `CheckResult` with the correct `CheckCategory` enum value
3. Add the check to the module's `run_*_checks()` function
4. If needed, add a call to the new runner in `evaluate.py`
5. Update ground truth files if the check depends on new expectations
6. Run `make evaluate` to verify

### Updating Ground Truth

1. Modify the appropriate language JSON file in `evaluation/ground-truth/`
2. Ensure `count` matches the number of entries in `lines` array
3. Use `min_count` for checks that depend on optional rulesets
4. Add `requires_ruleset` field for ruleset-conditional entries
5. Add `notes` to document any detection limitations or line offsets
6. Run `make evaluate` to validate changes

### Adding New LLM Judges

1. Create a new judge class in `evaluation/llm/judges/` extending `BaseJudge`
2. Implement `dimension_name`, `weight`, `collect_evidence()`, `run_ground_truth_assertions()`, and `get_default_prompt()`
3. Create a prompt template in `evaluation/llm/prompts/<dimension_name>.md`
4. Register the judge in `evaluation/llm/judges/__init__.py`
5. Add invocation to the LLM evaluation runner

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial version |
| 2.0 | 2026-02-13 | Complete rewrite: added check catalog with all 34+ checks, scoring formulas, LLM judge sub-dimensions and rubrics, ground truth schema details, security check documentation, evidence collection details, confidence requirements |
