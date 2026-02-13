# Evaluation Strategy: Roslyn Analyzers PoC

This document describes the evaluation methodology for the Roslyn Analyzers tool, which performs .NET static analysis detecting security vulnerabilities, design violations, resource management issues, dead code, and performance anti-patterns across C# codebases.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation in a hybrid approach:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- verifies detection accuracy, rule coverage, edge case handling, and performance |
| LLM Judges | 40% | Semantic understanding -- evaluates security depth, design reasoning, resource management nuance, overall quality, and integration fit |

This hybrid approach provides both **precision** (programmatic checks produce deterministic, auditable results against ground truth) and **nuance** (LLM judges assess whether violation messages are actionable, whether coverage gaps matter for due diligence, and whether output integrates cleanly with downstream systems).

### Design Rationale

Roslyn Analyzers present unique evaluation challenges compared to simpler metric tools:

1. **Multi-category detection** -- The tool spans five violation categories (security, design, resource, performance, dead_code), each requiring domain-specific ground truth.
2. **Analyzer limitations** -- Some Roslyn rules (CA3002 for XSS, CA5390 for secrets, IDE0005 for unused imports) have known gaps. The evaluation must distinguish "tool failed to detect" from "analyzer cannot detect this pattern" to avoid penalizing known limitations.
3. **False positive sensitivity** -- For due diligence reporting, false positives on clean code are more damaging than missed detections. The evaluation weighs precision heavily (AC-9 threshold at 85%).
4. **Real-world vs. synthetic modes** -- LLM judges operate in two modes: strict ground-truth evaluation for synthetic repos, and output-quality evaluation for real-world repos where low finding counts on secure codebases should not penalize the tool.

---

## Dimension Summary

### Programmatic Dimensions

| ID | Dimension | Weight | Checks | Purpose |
|----|-----------|--------|--------|---------|
| D1 | Accuracy | 40% | AC-1 to AC-10 | Detection recall and precision per violation category |
| D2 | Coverage | 25% | CV-1 to CV-8 | Rule triggering breadth and file coverage |
| D3 | Edge Cases | 20% | EC-1 to EC-12 | Robustness against unusual inputs and .NET-specific patterns |
| D4 | Performance | 15% | PF-1 to PF-4 | Analysis speed, throughput, and resource usage |

### LLM Judge Dimensions

| Judge | Weight | Sub-Dimensions |
|-------|--------|----------------|
| Security Detection | 30% | sql_injection (25%), cryptography (25%), deserialization (25%), overall_coverage (25%) |
| Design Analysis | 25% | encapsulation (25%), interface_design (25%), inheritance (25%), complexity (25%) |
| Resource Management | 25% | idisposable_impl (25%), undisposed_detection (25%), async_patterns (25%), leak_prevention (25%) |
| Overall Quality | 20% | false_positive_control (25%), detection_precision (25%), coverage_completeness (25%), actionability (25%) |

**Note:** A fifth judge, **Integration Fit** (15% weight), is available but runs as a supplementary assessment. It evaluates schema compliance, DD Platform mapping, and aggregator compatibility with sub-dimensions: schema_compliance (40%), dd_platform_mapping (35%), aggregator_compatibility (25%).

---

## Check Catalog

### Accuracy Checks (AC-1 to AC-10)

All accuracy checks use a recall threshold of >= 80% unless otherwise noted. Each check targets specific Roslyn analyzer rules against known-vulnerable synthetic files.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| AC-1 | SQL Injection Detection | Critical | >= 80% recall on CA3001/CA2100 rules against `security/sql_injection.cs` | expected count, detected count, missed count, rules checked, file path |
| AC-2 | XSS Detection | High | >= 80% recall on CA3002/SCS0029/SCS0002 OR pass if `analyzer_limitation` flag set (known gap) | expected count, detected count, analyzer limitation flag, rules checked |
| AC-3 | Hardcoded Secrets Detection | High | >= 80% recall on CA5390/SCS0015 OR pass if `analyzer_limitation` flag set (CA5390 deprecated) | expected count, detected count, analyzer limitation flag, rules checked |
| AC-4 | Weak Crypto Detection | Critical | >= 80% recall on CA5350/CA5351 rules against `security/weak_crypto.cs` | expected count, detected count, missed count, rules checked |
| AC-5 | Insecure Deserialization Detection | Critical | >= 80% recall on CA2300/CA2301/CA2305/CA2311/CA2315 rules | expected count, detected count, missed count, rules checked |
| AC-6 | Resource Disposal Detection | High | >= 80% recall on CA2000/CA1001 across `resource/undisposed_objects.cs` and `resource/missing_idisposable.cs` | expected count, detected count per file, rules checked, files list |
| AC-7 | Dead Code Detection | High | >= 80% recall on IDE0005/IDE0060, skipping files with `analyzer_limitation` flag | expected count, detected count, skipped files, active files |
| AC-8 | Design Violation Detection | High | >= 80% recall on CA1051/CA1040 across `design/visible_fields.cs` and `design/empty_interfaces.cs` | expected count, detected count, rules checked, files list |
| AC-9 | Overall Precision | Critical | >= 85% precision. Measures false positive rate on clean files (files with `is_false_positive_test: true`). Precision = (total_reported - FP_on_clean) / total_reported | true positives, false positives, total reported, clean files tested, FP file details |
| AC-10 | Overall Recall | Critical | >= 80% overall recall (detected / total_expected from ground truth summary) | detected count, expected count, missed count, recall ratio |

**Analyzer Limitation Handling:** Checks AC-2, AC-3, and AC-7 implement graceful degradation. When a ground truth file is marked with `analyzer_limitation: true` and `total_expected: 0`, the check passes automatically with score 1.0, documenting the known gap rather than producing a misleading failure.

### Coverage Checks (CV-1 to CV-8)

Coverage checks verify that the analysis triggers a sufficient breadth of analyzer rules and covers all expected files.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| CV-1 | Security Rule Coverage | Critical | >= 8 of 15 security rules triggered (CA2100, CA5350, CA5351, CA5364, CA5386, CA2300, CA2301, CA2326, CA2327, SCS0006, SCS0010, SCS0013, SCS0028, CA3001, CA3147) | triggered rules, missing rules, total count |
| CV-2 | Design Rule Coverage | High | >= 8 of 12 design rules triggered (CA1051, CA1040, CA1000, CA1061, CA1502, CA1506, IDE0040, CA1001, VSTHRD100, VSTHRD110, VSTHRD111, VSTHRD200) plus up to 4 Roslynator (RCS) rules | triggered rules, missing rules, RCS rules found |
| CV-3 | Resource Rule Coverage | High | >= 6 of 10 resource rules triggered (CA2000, CA1001, CA1063, CA2016, CA2007, CA1821, IDISP001, IDISP006, IDISP014, IDISP017) | triggered rules, missing rules, total count |
| CV-4 | Performance Rule Coverage | Medium | >= 3 of 5 performance rules triggered (CA1826, CA1829, CA1825, CA1805, CA1834) | triggered rules, missing rules, total count |
| CV-5 | Dead Code Rule Coverage | High | >= 4 of 5 dead code rules triggered (IDE0005, IDE0060, IDE0052, IDE0059, CA1812) | triggered rules, missing rules, total count |
| CV-6 | DD Category Coverage | Critical | All 5 categories covered: security, design, resource, performance, dead_code | covered categories, missing categories, category counts |
| CV-7 | File Coverage | Critical | 100% of synthetic ground truth files analyzed | expected file count, covered count, covered files (first 10), missing files |
| CV-8 | Line-Level Precision | High | >= 70% of violations have non-zero `line_start` values | total violations, with line numbers, without line numbers |

### Edge Case Checks (EC-1 to EC-12)

Edge case checks verify robustness against unusual inputs and .NET-specific scenarios.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| EC-1 | Empty Files Handling | Medium | Analysis completes without crashes when empty .cs files exist | analysis completed flag, timestamp |
| EC-2 | Unicode Content Handling | Medium | Files with unicode identifiers analyzed successfully (files_analyzed > 0) | files analyzed count |
| EC-3 | Large Files Handling | High | Files > 2000 LOC analyzed successfully (or pass by default if none exist) | large file count, large file paths |
| EC-4 | Deeply Nested Code Handling | Medium | Analysis handles 10+ nesting levels without errors | files analyzed count |
| EC-5 | Partial Classes Handling | Medium | Partial class definitions do not cause crashes | files analyzed count |
| EC-6 | False Positive Rate | Critical | <= 1 violation per clean file on average across `is_false_positive_test` files | clean files checked, violations on clean files, per-file details |
| EC-7 | Syntax Error Handling | Low | Analysis completes gracefully even with invalid C# (duration_ms > 0) | duration in ms, completed flag |
| EC-8 | Multi-Project Solutions | Low | Single project analyzed successfully (multi-project not tested in synthetic) | files analyzed count, note |
| EC-9 | NuGet Analyzers | Medium | NuGet-delivered analyzer diagnostics present. Score 1.0 if package metadata captured, 0.8 if CA diagnostics found, 0.5 minimum pass | NuGet packages, analyzer assemblies, diagnostic prefixes |
| EC-10 | Severity Mapping | High | >= 80% of diagnostics with ground truth severity expectations match actual severity | total checked, matches, mismatches (up to 10) |
| EC-11 | Framework-Specific Rules | Medium | Framework-specific diagnostic info captured. Score 1.0 if TFM info present, 0.8 if framework-specific diagnostics found, 0.5 minimum pass | target frameworks, TFM string, framework-specific diagnostics |
| EC-12 | Multi-Targeting Evaluation | Medium | Multi-TFM handling assessed. Score 1.0 if per-TFM breakdown exists, 0.7 if multi-target detected, 0.5 for single-target (always passes) | is_multi_target flag, target frameworks, per-TFM diagnostics |

### Performance Checks (PF-1 to PF-4)

Performance checks verify that analysis completes within acceptable time and resource bounds.

| Check ID | Name | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|--------------------|
| PF-1 | Synthetic Analysis Speed | High | < 30 seconds for synthetic repo. Score = max(0, 1.0 - duration/threshold) | duration_ms, duration_seconds, threshold_seconds |
| PF-2 | Per-File Efficiency | Medium | < 2000ms average per file. Score = max(0, 1.0 - ms_per_file/threshold) | duration_ms, files_analyzed, ms_per_file, threshold_ms |
| PF-3 | Throughput | Medium | >= 50 LOC/second. Score = min(1.0, loc_per_second/threshold) | total_loc, duration_seconds, loc_per_second, threshold_loc |
| PF-4 | Memory Usage | Low | < 500MB peak (estimated from completion; actual measurement is a future enhancement) | estimated_memory_mb, threshold_mb, note |

---

## Scoring

### Category Score Calculation

Each category score is computed as the ratio of passed checks to total checks within that category:

```python
CATEGORY_WEIGHTS = {
    "accuracy": 0.40,
    "coverage": 0.25,
    "edge_cases": 0.20,
    "performance": 0.15,
}

# Per-category score
category_score = passed_checks / total_checks  # range: 0.0 to 1.0

# Weighted contribution
weighted_score = category_score * category_weight
```

### Overall Programmatic Score

The overall programmatic score is the sum of all weighted category scores:

```python
overall_score = sum(category_score * weight for category, weight in CATEGORY_WEIGHTS.items())
# Range: 0.0 to 1.0
```

### Combined Score (Programmatic + LLM)

When LLM evaluation runs alongside programmatic evaluation, the combined score is:

```python
# Normalize programmatic score to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)  # 0.0-1.0 -> 1.0-5.0

# LLM score is already on 1-5 scale
# Weighted combination
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

### Scorecard Normalization

For the scorecard output, raw category scores are normalized to a 1-5 scale:

```python
normalized_score = raw_score * 5.0  # 0.0-1.0 -> 0.0-5.0
```

### Category Minimum Enforcement

Before applying overall thresholds, all categories must meet a 70% minimum:

```python
for category, scores in category_scores.items():
    if scores["score"] < 0.70:
        decision = "FAIL"  # Regardless of overall score
```

This prevents a tool from passing overall by excelling in one area while severely underperforming in another.

---

## Decision Thresholds

### Programmatic Decision (0.0-1.0 scale)

| Decision | Score Range | Interpretation |
|----------|-------------|----------------|
| STRONG_PASS | >= 0.80 | Excellent, production-ready quality analysis |
| PASS | >= 0.70 | Good, minor improvements possible |
| WEAK_PASS | >= 0.60 | Acceptable with caveats, some gaps to address |
| FAIL | < 0.60 | Significant issues, not ready for due diligence |

### Combined Decision (1.0-5.0 scale)

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent across both programmatic and LLM dimensions |
| PASS | >= 3.5 | Good overall, minor improvements needed |
| WEAK_PASS | >= 3.0 | Acceptable with caveats |
| FAIL | < 3.0 | Significant issues requiring attention |

### Automatic FAIL Conditions

The following conditions override score-based decisions and force a FAIL:

1. **Category minimum not met** -- Any category scoring below 70% triggers automatic FAIL, regardless of the overall weighted score.
2. **LLM ground truth assertion failure** -- If `run_ground_truth_assertions()` returns failures, the LLM score is capped at 2.0 maximum, which typically drives the combined score below the PASS threshold.

---

## Ground Truth

### Methodology

Ground truth is organized across six JSON files in `evaluation/ground-truth/`, each serving a distinct purpose:

| File | Purpose | Schema |
|------|---------|--------|
| `csharp.json` | Primary ground truth with per-file violation expectations, rule-to-category mapping, and thresholds | Full V1 schema (see below) |
| `security-issues.json` | Range-based expectations for security-focused scenarios | Min/max range schema |
| `design-violations.json` | Range-based expectations for design violation scenarios | Min/max range schema |
| `resource-management.json` | Range-based expectations for resource management scenarios | Min/max range schema |
| `dead-code.json` | Range-based expectations for dead code detection scenarios | Min/max range schema |
| `clean-code.json` | Zero-violation expectations for false positive testing | Zero-assertion schema |

### Primary Ground Truth Structure (csharp.json)

The primary ground truth file contains detailed per-file expectations for 34 synthetic C# files organized into five categories:

```json
{
  "schema_version": "1.0",
  "scenario": "csharp",
  "expected": {
    "summary": {
      "total_files": 34,
      "total_expected_violations": 120,
      "violation_categories": {
        "security": 31,
        "design": 25,
        "resource": 34,
        "performance": 16,
        "dead_code": 16
      },
      "false_positive_test_files": 4,
      "safe_pattern_count": 41,
      "p0_packages": ["SecurityCodeScan.VS2019", "IDisposableAnalyzers", ...],
      "p1_packages": ["AsyncFixer", "ErrorProne.NET.CoreAnalyzers", ...],
      "p2_packages": ["StyleCop.Analyzers", "xunit.analyzers", ...]
    },
    "thresholds": {
      "precision_min": 0.85,
      "recall_min": 0.8,
      "false_positive_rate_max": 0.1
    },
    "rule_to_category_map": { "CA3001": "security", "CA1051": "design", ... }
  },
  "files": {
    "security/sql_injection.cs": {
      "expected_violations": [
        { "rule_id": "CA3001", "dd_category": "security", "count": 3, "lines": [15, 28, 39] },
        { "rule_id": "CA2100", "dd_category": "security", "count": 2, "lines": [50, 62] }
      ],
      "total_expected": 5,
      "safe_patterns": 2
    }
  }
}
```

### Per-File Expected Violation Format

Each file entry in the ground truth specifies:

| Field | Type | Description |
|-------|------|-------------|
| `expected_violations` | array | List of expected violations, each with `rule_id`, `dd_category`, `count`, and `lines` |
| `total_expected` | int | Total number of expected violations for this file |
| `safe_patterns` | int | Number of safe code patterns in the file (should NOT trigger violations) |
| `is_false_positive_test` | bool | If true, this file should produce zero violations |
| `analyzer_limitation` | bool | If true, the check passes automatically (known analyzer gap) |
| `note` | string | Documentation of known limitations or special handling |

### Range-Based Ground Truth Format

The secondary ground truth files (security-issues, design-violations, etc.) use min/max ranges:

```json
{
  "schema_version": "1.0",
  "scenario": "security-issues",
  "expected": {
    "total_files": {"min": 5, "max": 30},
    "total_violations": {"min": 10, "max": 50},
    "security_violations": {"min": 8, "max": 40},
    "key_rules_expected": {
      "CA3001": "SQL injection",
      "CA5350": "Weak cryptographic algorithm"
    }
  },
  "assertions": [
    "SQL injection vulnerabilities detected (CA3001)",
    "Weak crypto usage identified (CA5350)"
  ]
}
```

### Synthetic Repository

The primary evaluation synthetic repo is located at `eval-repos/synthetic/csharp/` and contains:

- **34 C# files** across 7 subdirectories (security/, design/, resource/, performance/, dead_code/, clean/)
- **120 expected violations** across 5 categories
- **4 false positive test files** in `clean/` (clean_service.cs, clean_controller.cs, clean_crypto.cs) with `is_false_positive_test: true`
- **41 safe patterns** embedded alongside violations to test contextual understanding
- **.editorconfig** suppression for style rules to isolate security/quality rule evaluation

### Violation Matching

The `match_violations()` function in `scripts/checks/__init__.py` matches detected violations to expected violations using:

1. **Rule ID grouping** -- Violations are grouped by `rule_id` for comparison
2. **Line tolerance** -- A detected violation matches an expected violation if any expected line is within +/- 5 lines of the detected `line_start`
3. **Greedy matching** -- Each expected and detected violation can match at most once

```python
def match_violations(detected, expected, file_key, tolerance_lines=5):
    # Returns (true_positives, false_positives, false_negatives)
```

### NuGet Analyzer Packages

The ground truth documents three tiers of NuGet analyzer packages:

| Tier | Packages | Purpose |
|------|----------|---------|
| P0 (Core) | SecurityCodeScan.VS2019, IDisposableAnalyzers, Microsoft.VisualStudio.Threading.Analyzers, Roslynator.Analyzers | Primary detection rules, always enabled |
| P1 (Extended) | AsyncFixer, ErrorProne.NET.CoreAnalyzers, Meziantou.Analyzer, SmartAnalyzers.ExceptionAnalyzer, SonarAnalyzer.CSharp | Additional detection rules, evaluated but not required |
| P2 (Style) | StyleCop.Analyzers, xunit.analyzers, Moq.Analyzers, BlowinCleanCode, DotNetProjectFile.Analyzers | Style/convention rules, suppressed via .editorconfig for due diligence evaluation |

---

## LLM Judge Details

### Judge Architecture

All LLM judges extend a Roslyn-specific `BaseJudge` class (in `evaluation/llm/judges/base.py`) which itself extends the shared `SharedBaseJudge` from `src/shared/evaluation/`. The base class provides:

- **Analysis loading** -- `load_analysis()`, `load_all_analysis_results()`, `load_ground_truth_by_name()`
- **Output unwrapping** -- `unwrap_output()` handles both old format and new envelope format
- **Prompt template loading** -- Loads from `evaluation/llm/prompts/{dimension_name}.md`
- **Evaluation pipeline** -- `evaluate()` calls `collect_evidence()` -> renders prompt -> invokes LLM -> parses response -> runs `run_ground_truth_assertions()` -> returns `JudgeResult`
- **Dual-mode evaluation** -- Supports `evaluation_mode` of "synthetic" (strict ground truth) or "real_world" (output quality focus)
- **Synthetic baseline injection** -- Real-world mode injects synthetic evaluation context so LLM judges can calibrate expectations

### SecurityDetectionJudge (30% weight)

**Purpose:** Evaluates security vulnerability detection quality across SQL injection, cryptography, deserialization, and XSS categories.

**Sub-dimensions and weights:**

| Sub-dimension | Weight | Focus Areas |
|---------------|--------|-------------|
| sql_injection | 25% | CA2100, CA3001, CA3002 detection accuracy |
| cryptography | 25% | CA5350, CA5351, CA5358-5402 coverage |
| deserialization | 25% | CA2300-CA2322 unsafe deserializer detection |
| overall_coverage | 25% | Breadth across all security categories |

**Scoring rubric (synthetic mode):**

| Score | Criteria |
|-------|----------|
| 5 | All expected SQL injection, weak crypto, and deserialization patterns detected. Zero false negatives on security-critical files. Coverage > 95% of ground truth. |
| 4 | Most SQL injection and crypto issues detected. Coverage 85-95% of ground truth. |
| 3 | Common security issues detected but some missed patterns. Coverage 70-85%. |
| 2 | Misses many security issues, incomplete pattern coverage. Coverage 50-70%. |
| 1 | Fails to detect critical vulnerabilities. Coverage < 50%. |

**Evidence collected:** Security summary by sub-category (detected counts and rules), detection breakdown by repository, sample violations (up to 15), ground truth comparison, evaluation mode context.

### DesignAnalysisJudge (25% weight)

**Purpose:** Evaluates design pattern and code quality detection including encapsulation, interface design, inheritance, and complexity.

**Sub-dimensions and weights:**

| Sub-dimension | Weight | Focus Areas |
|---------------|--------|-------------|
| encapsulation | 25% | CA1051, CA1034, SA1401 -- visible fields and accessible members |
| interface_design | 25% | CA1040, CA1033, CA1710, CA1711 -- empty and marker interfaces |
| inheritance | 25% | CA1061, CA1501, CA1052 -- deep hierarchies and improper overrides |
| complexity | 25% | CA1502, CA1505, CA1506 -- cyclomatic complexity and coupling |

**Scoring rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Detects encapsulation violations, empty interfaces, deep inheritance, accurate complexity measurement. Coverage > 95%. |
| 4 | Detects most encapsulation issues, common interface problems, most inheritance concerns. Coverage 85-95%. |
| 3 | Detects major design issues, some missed patterns. Coverage 70-85%. |
| 2 | Misses many design issues, incomplete pattern coverage. Coverage 50-70%. |
| 1 | Fails to detect basic design violations. Coverage < 50%. |

**Evidence collected:** Design summary by sub-category, detection by repository, sample violations (up to 15), ground truth comparison.

### ResourceManagementJudge (25% weight)

**Purpose:** Evaluates resource management and disposal detection including IDisposable patterns, async patterns, and leak prevention.

**Sub-dimensions and weights:**

| Sub-dimension | Weight | Focus Areas |
|---------------|--------|-------------|
| idisposable_impl | 25% | CA1063, CA1816, CA1821 -- proper IDisposable implementation |
| undisposed_detection | 25% | IDISP006, IDISP014, CA2000 -- objects not disposed before scope exit |
| async_patterns | 25% | ASYNC0001, CA2007, CA2012, VSTHRD110/111 -- async void, ConfigureAwait |
| leak_prevention | 25% | CA2213, CA2215, IDISP001, IDISP004 -- resource leak detection |

**Scoring rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Detects all IDisposable issues, undisposed objects, async pattern problems, and resource leaks. Coverage > 95%. |
| 4 | Detects most IDisposable issues and common undisposed objects. Coverage 85-95%. |
| 3 | Detects major resource issues, some missed patterns. Coverage 70-85%. |
| 2 | Misses many resource issues, incomplete pattern coverage. Coverage 50-70%. |
| 1 | Fails to detect basic resource problems. Coverage < 50%. |

**Evidence collected:** Resource summary by sub-category, detection by repository, sample violations (up to 15), ground truth comparison, IDISP rule breakdown.

### OverallQualityJudge (20% weight)

**Purpose:** Evaluates overall analysis quality, false positive control, and actionability of violation messages.

**Sub-dimensions and weights:**

| Sub-dimension | Weight | Focus Areas |
|---------------|--------|-------------|
| false_positive_control | 25% | Violations on clean files, FP rate |
| detection_precision | 25% | Accuracy vs. ground truth expectations |
| coverage_completeness | 25% | All 5 DD categories covered |
| actionability | 25% | Message clarity, fix suggestions, documentation links |

**Scoring rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Very low FP rate (< 5%), high precision across all categories, complete coverage, clear actionable messages with fix suggestions. |
| 4 | Low FP rate (5-10%), good precision, most categories covered, generally clear messages. |
| 3 | Moderate FP rate (10-15%), acceptable precision, core categories covered, understandable messages. |
| 2 | High FP rate (15-25%), poor precision, missing categories, confusing messages. |
| 1 | Very high FP rate (> 25%), unreliable detection, major coverage gaps, unclear messages. |

**Evidence collected:** Overall summary (files, violations, severity/category breakdown), category coverage analysis, false positive analysis against clean-code ground truth, message quality samples (up to 10).

### IntegrationFitJudge (15% weight -- supplementary)

**Purpose:** Evaluates DD Platform integration compatibility of the analysis output.

**Sub-dimensions and weights:**

| Sub-dimension | Weight | Focus Areas |
|---------------|--------|-------------|
| schema_compliance | 40% | Output matches DD Platform expected schema, `schema_version` present |
| dd_platform_mapping | 35% | Data maps to L1 (Structural) and L6 (Quality) lenses, path normalization |
| aggregator_compatibility | 25% | Rollup completeness (by_severity, by_category, by_rule, by_file) |

**Scoring rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Schema fully compatible, clear lens mapping, paths normalized, complete violation context, all rollups present. |
| 4 | Schema mostly compatible, minor transforms needed, most rollups present. |
| 3 | Core schema compatible, some mapping required, basic rollups present. |
| 2 | Partially compatible, significant mapping work, missing rollups. |
| 1 | Schema incompatible, cannot map to DD lenses, no rollup data. |

**Evidence collected:** Metadata by repo, schema version, output structure (field types), sample violations (up to 15), summary structure, rollup completeness flags.

### Ground Truth Assertions

Each LLM judge implements `run_ground_truth_assertions()` which performs hard checks before the LLM scores. If assertions fail, the LLM score is capped at a maximum of 2.0:

```python
def evaluate(self):
    gt_passed, gt_failures = self.run_ground_truth_assertions()
    # ... invoke LLM ...
    if not gt_passed:
        score = min(llm_score, 2)  # Cap score if GT fails
```

Assertion examples:
- **SecurityDetectionJudge:** Synthetic repo must have > 0 security findings; clean files must have 0 security false positives.
- **DesignAnalysisJudge:** Synthetic repo must have > 0 design findings; minimum encapsulation violations if expected.
- **ResourceManagementJudge:** Synthetic repo must have > 0 resource findings; minimum IDISP rule triggers if expected.
- **OverallQualityJudge:** Required categories (security, design) must be present; false positive rate must not exceed maximum; pass rate must be >= 80%.
- **IntegrationFitJudge:** Analysis results must exist; `schema_version` field required; summary must include `total_violations`, `violations_by_severity`, `violations_by_category`; violations must have `rule_id`, `message`, and `severity`/`dd_severity`.

---

## LLM Prompt Templates

Prompt templates are stored as Markdown files in `evaluation/llm/prompts/`. The following templates are available:

| Template | Used By | Key Placeholders |
|----------|---------|------------------|
| `security_detection.md` | SecurityDetectionJudge | `{{ security_summary }}`, `{{ detection_by_category }}`, `{{ violations_sample }}`, `{{ ground_truth_comparison }}`, `{{ evaluation_mode }}`, `{{ synthetic_baseline }}`, `{{ interpretation_guidance }}` |
| `security_coverage.md` | Standalone prompt | `{{ security_rules_triggered }}`, `{{ owasp_coverage_map }}`, `{{ severity_breakdown }}` |
| `detection_accuracy.md` | Standalone prompt | `{{ detection_sample }}`, `{{ ground_truth_comparison }}`, `{{ false_positives }}` |
| `false_positive_rate.md` | Standalone prompt | `{{ clean_file_violations }}`, `{{ safe_pattern_results }}`, `{{ confidence_scores }}` |
| `actionability.md` | Standalone prompt | `{{ message_samples }}`, `{{ fix_suggestions }}`, `{{ severity_priority_info }}` |

Legacy prompt templates (`.legacy.md` suffix) exist for `design_analysis`, `resource_management`, `overall_quality`, and `security_detection`. These are preserved for reference and are not used in active evaluation.

---

## Evidence Collection

Each programmatic check collects structured evidence for transparency and debugging. The evidence is stored in the `evidence` field of each `CheckResult`.

### CheckResult Schema

```python
@dataclass
class CheckResult:
    check_id: str       # e.g., "AC-1"
    name: str           # e.g., "SQL Injection Detection"
    category: str       # e.g., "accuracy"
    passed: bool        # True/False
    score: float        # 0.0 to 1.0
    threshold: float    # Pass threshold
    actual_value: float # Measured value
    message: str        # Human-readable summary
    evidence: dict      # Structured evidence (varies by check)
```

### Evidence Types by Category

| Category | Evidence Fields |
|----------|----------------|
| Accuracy | expected count, detected count, missed count, rules checked, file(s) checked, recall ratio, analyzer_limitation flag |
| Coverage | triggered rules list, missing rules list, total rule count, category counts, covered/missing files |
| Edge Cases | files analyzed count, clean files checked, violations on clean files, diagnostic prefixes, NuGet packages, target frameworks, severity match/mismatch details |
| Performance | duration_ms, duration_seconds, threshold, files_analyzed, ms_per_file, total_loc, loc_per_second, estimated_memory_mb |

---

## Confidence Requirements

### LLM Judge Confidence

Each LLM judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review recommended |

### Ground Truth Confidence

Ground truth assertions can override LLM scores. If assertions fail, the LLM score is capped at 2 (maximum), ensuring that fundamental detection failures are not masked by favorable LLM reasoning.

---

## Evaluation Workflow

### Running Programmatic Evaluation

```bash
# Full evaluation with verbose output (builds synthetic repo, runs analysis, evaluates)
make evaluate

# Quick evaluation (skip performance checks PF-1 to PF-4)
make evaluate-quick

# JSON-only output (no terminal formatting)
make evaluate-json
```

The evaluation script accepts the following arguments:

```bash
python scripts/evaluate.py \
    --analysis output/runs/roslyn_analysis.json \
    --ground-truth evaluation/ground-truth \
    --output output/runs/evaluation_report.json \
    [--json]    # JSON-only mode
    [--quick]   # Skip performance checks
```

### Running LLM Evaluation

```bash
# Full LLM evaluation (5 judges, opus-4.5 model)
make evaluate-llm

# Focused evaluation (detection accuracy only, skip other judges)
make evaluate-llm-focused

# Combined evaluation (programmatic + LLM)
make evaluate-combined
```

### Evaluation Outputs

Evaluation artifacts are written to `evaluation/results/` and overwrite previous runs:

```
evaluation/results/
    evaluation_report.json   # Programmatic evaluation report (compliance format)
    scorecard.json           # Structured scorecard data
    scorecard.md             # Human-readable scorecard
    llm_evaluation.json      # LLM judge results (if run)
```

### Sample Evaluation Output

```json
{
  "timestamp": "2026-01-21T18:48:53Z",
  "tool": "roslyn-analyzers",
  "decision": "STRONG_PASS",
  "score": 0.8571,
  "checks": [
    {
      "name": "AC-1",
      "status": "PASS",
      "message": "All SQL injection patterns detected (100.0% recall)"
    }
  ],
  "summary": {
    "total": 34,
    "passed": 30,
    "failed": 4
  }
}
```

---

## Extending the Evaluation

### Adding New Programmatic Checks

1. Create or extend a check function in the appropriate module under `scripts/checks/`:
   - `accuracy.py` for detection correctness checks
   - `coverage.py` for rule breadth checks
   - `edge_cases.py` for robustness checks
   - `performance.py` for speed/resource checks
2. The function must return a `CheckResult` with a unique `check_id` (e.g., "AC-11").
3. Add the function call to the corresponding `run_all_*_checks()` function.
4. Update ground truth in `evaluation/ground-truth/csharp.json` if needed.
5. Run `make evaluate` to verify.

### Adding New LLM Judges

1. Create a new judge class extending `BaseJudge` in `evaluation/llm/judges/`.
2. Implement `dimension_name`, `weight`, `collect_evidence()`, and `run_ground_truth_assertions()`.
3. Create a prompt template in `evaluation/llm/prompts/{dimension_name}.md`.
4. Register the judge in `evaluation/llm/judges/__init__.py`.
5. Add the judge to the LLM evaluation orchestrator.

### Updating Thresholds

Thresholds are defined inline in check functions. Key thresholds:

```python
# Accuracy checks
recall_threshold = 0.80        # AC-1 to AC-8, AC-10
precision_threshold = 0.85     # AC-9

# Coverage checks
rule_coverage_thresholds = {
    "security": 8,             # CV-1: 8/15 rules
    "design": 8,               # CV-2: 8/12 rules
    "resource": 6,             # CV-3: 6/10 rules
    "performance": 3,          # CV-4: 3/5 rules
    "dead_code": 4,            # CV-5: 4/5 rules
}
line_precision_threshold = 0.70  # CV-8

# Performance checks
analysis_speed_threshold = 30    # PF-1: seconds
per_file_threshold = 2000        # PF-2: ms
throughput_threshold = 50        # PF-3: LOC/second
memory_threshold = 500           # PF-4: MB

# Decision thresholds
category_minimum = 0.70          # All categories must meet this
```

### Refreshing Ground Truth

When updating the synthetic repository with new test files:

1. Add the C# source file to the appropriate subdirectory under `eval-repos/synthetic/csharp/`.
2. Manually verify expected violations by counting Roslyn diagnostics.
3. Add the file entry to `evaluation/ground-truth/csharp.json` with `expected_violations`, `total_expected`, and `safe_patterns`.
4. Set `is_false_positive_test: true` for clean files or `analyzer_limitation: true` for known gaps.
5. Update `summary.total_files` and `summary.total_expected_violations` counts.
6. Run `make all` to rebuild, re-analyze, and re-evaluate.

---

## References

- [Roslyn Analyzers Documentation](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview)
- [CA Rule Categories](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/categories)
- [IDisposableAnalyzers](https://github.com/DotNetAnalyzers/IDisposableAnalyzers)
- [SecurityCodeScan](https://security-code-scan.github.io/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
