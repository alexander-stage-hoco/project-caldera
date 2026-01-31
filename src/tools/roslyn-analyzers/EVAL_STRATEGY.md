# Roslyn Analyzers PoC Evaluation Strategy

This document describes the evaluation framework for the Roslyn Analyzers (.NET code quality analysis) tool PoC, including the complete check catalog, scoring methodology, weight allocation, and decision thresholds.

## Philosophy & Approach

The evaluation framework assesses Roslyn Analyzers' fitness for integration into the DD Platform across 4 dimensions with 34 individual checks.

### Version History

| Version | Dimensions | Checks | Description |
|---------|------------|--------|-------------|
| v1.0 (Original) | 4 | 30 | Initial evaluation framework with P0 analyzer packages |
| v1.1 (Current) | 4 | 34 | Added EC-9 to EC-12 for NuGet, severity, TFM, and multi-targeting |

### Evaluation Principles

1. **Category-based detection**: Validates detection across 5 DD categories (security, design, resource, performance, dead code)
2. **Recall-focused**: Prioritizes finding all known issues (>=80% recall)
3. **Low false positives**: Clean files should not be flagged
4. **Built-in integration**: Leverages .NET SDK built-in analyzers plus curated P0 packages

---

## Dimension Summary

| Dimension | Code | Checks | Weight | Description |
|-----------|------|--------|--------|-------------|
| Accuracy | AC | 10 | 35% | Detection accuracy per category |
| Coverage | CV | 8 | 25% | Rule and category coverage |
| Edge Cases | EC | 12 | 25% | Edge case handling |
| Performance | PF | 4 | 15% | Speed and efficiency |
| **Total** | | **34** | **100%** | |

---

## Complete Check Catalog

### 1. Accuracy (AC) - 35% Weight

Validates detection accuracy per violation category.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| AC-1 | SQL Injection Detection | CA3001/CA2100 detection | >= 80% recall on sql_injection.cs |
| AC-2 | XSS Detection | CA3002/SCS0029 detection | >= 80% recall OR analyzer_limitation |
| AC-3 | Hardcoded Secrets Detection | CA5390/SCS0015 detection | >= 80% recall OR analyzer_limitation |
| AC-4 | Weak Crypto Detection | CA5350/CA5351 detection | >= 80% recall on weak_crypto.cs |
| AC-5 | Insecure Deserialization | CA2300-CA2315 detection | >= 80% recall |
| AC-6 | Resource Disposal Detection | CA2000/CA1001 detection | >= 80% recall across resource files |
| AC-7 | Dead Code Detection | IDE0005/IDE0060 detection | >= 80% recall (excluding analyzer_limitation files) |
| AC-8 | Design Violation Detection | CA1051/CA1040 detection | >= 80% recall |
| AC-9 | Overall Precision | False positive rate on clean files | >= 85% precision |
| AC-10 | Overall Recall | Total detection rate | >= 80% recall |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 10 | 5 |
| 8-9 | 4 |
| 6-7 | 3 |
| 4-5 | 2 |
| 0-3 | 1 |

**Analyzer Limitation Handling:**

Some checks accept `analyzer_limitation: true` in ground truth when built-in analyzers have known gaps:
- **XSS (AC-2)**: CA3002 requires sophisticated data flow analysis
- **Hardcoded Secrets (AC-3)**: CA5390 is deprecated by Microsoft
- **Dead Code (AC-7)**: IDE0005 requires IDE analysis, not reliable in MSBuild

When `analyzer_limitation: true` and `expected_count == 0`, the check passes automatically.

---

### 2. Coverage (CV) - 25% Weight

Validates rule coverage across categories.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| CV-1 | Security Rule Coverage | Security rules triggered | >= 8/15 security rules |
| CV-2 | Design Rule Coverage | Design rules triggered | >= 8/16 design rules (includes RCS) |
| CV-3 | Resource Rule Coverage | Resource rules triggered | >= 6/10 resource rules |
| CV-4 | Performance Rule Coverage | Performance rules triggered | >= 3/5 performance rules |
| CV-5 | Dead Code Rule Coverage | Dead code rules triggered | >= 4/5 IDE rules |
| CV-6 | DD Category Coverage | All 5 DD categories covered | 5/5 categories have violations |
| CV-7 | File Coverage | All expected files analyzed | 100% file coverage |
| CV-8 | Line-Level Precision | Violations have line numbers | >= 70% have line_start > 0 |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 8 | 5 |
| 7 | 4 |
| 5-6 | 3 |
| 3-4 | 2 |
| 0-2 | 1 |

---

### 3. Edge Cases (EC) - 25% Weight

Validates handling of edge cases and real-world .NET project scenarios.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| EC-1 | Empty Files | No crashes on empty .cs files | Analysis completes |
| EC-2 | Unicode Content | Handles unicode identifiers | files_analyzed > 0 |
| EC-3 | Large Files | Analyzes files > 2000 LOC | Large files processed or none exist |
| EC-4 | Deeply Nested Code | Handles 10+ nesting levels | Analysis completes |
| EC-5 | Partial Classes | Handles partial class definitions | Analysis completes |
| EC-6 | False Positives | Low FP rate on clean files | <= 1 violation per clean file average |
| EC-7 | Syntax Errors | Graceful handling of invalid C# | duration_ms > 0 |
| EC-8 | Multi-Project Solutions | Handles .sln with multiple .csproj | Analysis completes |
| EC-9 | NuGet Analyzers | Validates diagnostics from NuGet packages | CA rules detected or NuGet metadata present |
| EC-10 | Severity Mapping | Validates diagnostic severities match expectations | >= 80% severity accuracy |
| EC-11 | Framework-Specific Rules | Validates TFM-specific diagnostics | TFM info captured or framework-specific diags detected |
| EC-12 | Multi-Targeting Evaluation | Validates handling of net48;net6.0 style projects | Multi-target support validated |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 12 | 5 |
| 10-11 | 4 |
| 7-9 | 3 |
| 4-6 | 2 |
| 0-3 | 1 |

---

#### EC-9: NuGet-Delivered Analyzers

**Description:**
Validates that diagnostics from NuGet-delivered analyzer packages are correctly captured and attributed. Many enterprise .NET projects use third-party analyzers delivered via NuGet (e.g., StyleCop.Analyzers, Roslynator, IDisposableAnalyzers).

**Acceptance Criteria:**
- NuGet analyzer package metadata is captured when available
- CA-prefixed diagnostics (from Microsoft.CodeAnalysis.NetAnalyzers) are detected
- Diagnostics from third-party analyzers are properly attributed

**Scoring Methodology:**
| Condition | Score |
|-----------|-------|
| NuGet analyzer info captured in metadata | 1.0 |
| CA diagnostics detected (implicit NuGet presence) | 0.8 |
| No NuGet metadata but analysis completes | 0.5 |

**Real-World Scenarios:**
- Enterprise codebases with custom analyzer packages enforcing coding standards
- Projects using IDisposableAnalyzers for resource leak detection
- SecurityCodeScan for OWASP vulnerability detection
- Roslynator for extended code quality rules

---

#### EC-10: Severity Mapping

**Description:**
Validates that diagnostic severities (Error, Warning, Info, Hidden) match expected values from ground truth. Severity accuracy is critical for prioritization in DD reports.

**Acceptance Criteria:**
- Diagnostic severities match ground truth expectations >= 80% of the time
- Severity mismatches are tracked and reported
- Supports all Roslyn severity levels (Error, Warning, Info, Hidden)

**Scoring Methodology:**
| Accuracy | Score |
|----------|-------|
| >= 80% | Pass (accuracy value as score) |
| < 80% | Fail |
| No expectations in GT | Skip (1.0) |

**Real-World Scenarios:**
- CI/CD pipelines that fail builds on Error-level diagnostics
- Security scanning where CA3001 (SQL injection) must be Error severity
- Projects with custom .editorconfig severity overrides
- Compliance requirements mandating specific severity for certain rules

---

#### EC-11: Framework-Specific Rules

**Description:**
Validates handling of Target Framework Moniker (TFM) specific diagnostics. Some Roslyn rules only apply to specific frameworks (e.g., .NET Framework vs .NET Core APIs).

**Acceptance Criteria:**
- Target framework information is captured in metadata
- Framework-specific diagnostic messages are identified
- Handles projects targeting legacy (.NET Framework 4.x) and modern (.NET 6+) frameworks

**Scoring Methodology:**
| Condition | Score |
|-----------|-------|
| TFM info captured in metadata | 1.0 |
| Framework-specific diagnostics detected | 0.8 |
| No framework info (single TFM, not tested) | 0.5 |

**Real-World Scenarios:**
- Migration projects moving from .NET Framework to .NET 6+
- Platform compatibility warnings (CA1416 for Windows-only APIs)
- API availability diagnostics that differ between TFMs
- SDK-style projects with explicit TargetFramework settings

---

#### EC-12: Multi-Targeting Evaluation

**Description:**
Validates handling of multi-targeting projects that target multiple frameworks (e.g., `<TargetFrameworks>net48;net6.0</TargetFrameworks>`). This is common in libraries that must support both legacy and modern .NET.

**Acceptance Criteria:**
- Multi-target projects are detected via TargetFrameworks property
- Ideally, diagnostics are broken down per TFM
- No diagnostic loss when analyzing multi-target projects

**Scoring Methodology:**
| Condition | Score |
|-----------|-------|
| Per-TFM diagnostic breakdown available | 1.0 |
| Multi-target detected, no per-TFM breakdown | 0.7 |
| Single-target project (not tested) | 0.5 |

**Real-World Scenarios:**
- NuGet library packages supporting netstandard2.0;net6.0;net8.0
- Enterprise libraries maintaining .NET Framework compatibility
- Projects with TFM-conditional code (#if NETFRAMEWORK)
- API surface differences requiring different analysis per TFM

**Implementation Notes:**
Full multi-targeting support requires building each TFM separately, as Roslyn analyzers run during compilation and each TFM produces different IL and has different API availability.

---

### 4. Performance (PF) - 15% Weight

Validates analysis speed and efficiency.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| PF-1 | Synthetic Analysis Speed | Total analysis time | < 30 seconds |
| PF-2 | Per-File Efficiency | Average time per file | < 2000ms per file |
| PF-3 | Throughput | Lines of code per second | >= 50 LOC/second |
| PF-4 | Memory Usage | Peak memory usage | < 500MB (estimated) |

**Scoring Table:**
| Checks Passed | Score |
|---------------|-------|
| 4 | 5 |
| 3 | 4 |
| 2 | 3 |
| 1 | 2 |
| 0 | 1 |

---

## Scoring Methodology

### Per-Dimension Score Calculation

1. Run all checks for the dimension
2. Count passed checks
3. Map to 1-5 score using dimension-specific scoring table
4. Multiply by dimension weight to get weighted score

```python
dimension_score = scoring_table[passed_count]
weighted_score = dimension_score * dimension_weight
```

### Total Score Calculation

```python
total_score = sum(d.weighted_score for d in dimensions)
```

The maximum possible score is 5.0 (all dimensions score 5/5).

### Combined Scoring Formula

```python
# Programmatic component (per-dimension weighted)
prog_accuracy = accuracy_passed / 10 * 0.35
prog_coverage = coverage_passed / 8 * 0.25
prog_edge_cases = edge_cases_passed / 12 * 0.25
prog_performance = performance_passed / 4 * 0.15
programmatic_score = sum([prog_*])

# Normalize to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)

# LLM component (already 1-5 scale)
llm_score = (
    security_detection * 0.35 +
    design_analysis * 0.25 +
    resource_management * 0.20 +
    overall_quality * 0.20
)

# Combined (60/40 split)
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

---

## Decision Thresholds

| Decision | Threshold | Description |
|----------|-----------|-------------|
| **STRONG_PASS** | >= 0.80 | Excellent fit, approved for immediate use |
| **PASS** | >= 0.70 | Good fit, approved with minor reservations |
| **WEAK_PASS** | >= 0.60 | Marginal fit, review failing checks before proceeding |
| **FAIL** | < 0.60 | Does not meet requirements |

### Decision Logic

```python
if total_score >= 0.80:
    return "STRONG_PASS"
elif total_score >= 0.70:
    return "PASS"
elif total_score >= 0.60:
    return "WEAK_PASS"
else:
    return "FAIL"
```

---

## Weight Allocation Rationale

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Accuracy | 35% | Highest priority - detection accuracy is critical |
| Coverage | 25% | Comprehensive rule coverage across categories |
| Edge Cases | 25% | Robustness for real-world codebases |
| Performance | 15% | Speed is important but secondary |

---

## Ground Truth Specifications

### Synthetic Repository Structure

```
eval-repos/synthetic/csharp/
├── security/
│   ├── sql_injection.cs           # CA3001, CA2100
│   ├── xss_vulnerabilities.cs     # CA3002 (analyzer_limitation)
│   ├── hardcoded_secrets.cs       # CA5390 (analyzer_limitation)
│   ├── weak_crypto.cs             # CA5350, CA5351
│   ├── insecure_deserialization.cs # CA2300-CA2315
│   ├── deprecated_tls.cs          # CA5364, CA5397
│   ├── missing_csrf.cs            # CA3147
│   ├── aspnet_xss.cs              # CA5395
│   └── aspnet_csrf.cs             # SCS0016
├── design/
│   ├── god_class.cs               # CA1502, CA1506 (analyzer_limitation)
│   ├── visible_fields.cs          # CA1051
│   ├── empty_interfaces.cs        # CA1040
│   ├── improper_inheritance.cs    # CA1061
│   ├── static_generics.cs         # CA1000
│   └── missing_accessibility.cs   # IDE0040
├── resource/
│   ├── undisposed_objects.cs      # CA2000
│   ├── missing_idisposable.cs     # CA1001, IDISP006
│   ├── improper_dispose.cs        # CA1063
│   ├── missing_cancellation.cs    # CA2016
│   ├── async_void.cs              # ASYNC0001
│   └── disposal_patterns.cs       # IDISP014, IDISP017
├── performance/
│   ├── inefficient_linq.cs        # CA1826, CA1829
│   ├── empty_array_alloc.cs       # CA1825
│   ├── string_concat_loop.cs      # CA1834
│   └── boxing_unboxing.cs         # CA1858
├── dead_code/
│   ├── unused_imports.cs          # IDE0005 (analyzer_limitation)
│   ├── unused_parameters.cs       # IDE0060
│   ├── unused_fields.cs           # IDE0052
│   ├── unused_locals.cs           # IDE0059
│   └── uninstantiated_classes.cs  # CA1812
└── clean/                         # False positive tests
    ├── clean_service.cs
    ├── clean_repository.cs
    ├── clean_controller.cs
    └── clean_crypto.cs
```

**Total: 34 files across 5 categories + 4 clean files**

### Ground Truth Schema

```json
{
  "schema_version": "1.0",
  "scenario": "csharp",
  "expected": {
    "summary": {
      "total_files": 34,
      "total_expected_violations": 115,
      "violation_categories": {
        "security": 31,
        "design": 20,
        "resource": 34,
        "performance": 16,
        "dead_code": 16
      },
      "false_positive_test_files": 4
    },
    "thresholds": {
      "precision_min": 0.85,
      "recall_min": 0.80,
      "false_positive_rate_max": 0.10
    }
  },
  "files": {
    "security/sql_injection.cs": {
      "expected_violations": [
        {
          "rule_id": "CA3001",
          "dd_category": "security",
          "count": 3,
          "lines": [15, 28, 39]
        }
      ],
      "total_expected": 5,
      "safe_patterns": 2
    },
    "security/xss_vulnerabilities.cs": {
      "expected_violations": [],
      "total_expected": 0,
      "analyzer_limitation": true,
      "note": "CA3002 requires sophisticated data flow analysis"
    }
  }
}
```

### Tolerance Policy

| Metric | Tolerance | Rationale |
|--------|-----------|-----------|
| Recall | 80% minimum | Allow for minor detection gaps |
| Precision | 85% minimum | Low false positive rate |
| Line matching | ± 5 lines | Build artifacts may shift line numbers |
| File coverage | 100% | All expected files must be analyzed |

---

## LLM Judge Dimensions (4 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| Security Detection | 35% | OWASP vulnerabilities detection |
| Design Analysis | 25% | Design violations and best practices |
| Resource Management | 20% | IDisposable and async patterns |
| Overall Quality | 20% | Message clarity and actionability |

### Security Detection Judge (35%)

**Sub-dimensions:**
- SQL injection detection (25%): CA3001/CA2100 accuracy
- Crypto vulnerabilities (25%): CA5350/CA5351 detection
- Deserialization (25%): CA2300-CA2315 coverage
- CSRF/XSS patterns (25%): Web security rules

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | All critical security vulnerabilities detected |
| 4 | Most vulnerabilities detected, minor gaps |
| 3 | Core vulnerabilities detected |
| 2 | Significant detection gaps |
| 1 | Poor security detection |

### Design Analysis Judge (25%)

**Sub-dimensions:**
- Design violations (40%): CA1051, CA1040 detection
- Code complexity (30%): Coupling and cohesion rules
- Inheritance issues (30%): CA1061 and related

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | Comprehensive design violation detection |
| 4 | Most design issues found |
| 3 | Core design rules covered |
| 2 | Limited design coverage |
| 1 | Poor design detection |

### Resource Management Judge (20%)

**Sub-dimensions:**
- Disposal patterns (40%): CA2000, CA1001, IDISP* rules
- Async patterns (30%): CA2016, ASYNC0001
- IDisposable (30%): CA1063 proper implementation

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | All resource issues detected with clear guidance |
| 4 | Most resource issues found |
| 3 | Core disposal issues detected |
| 2 | Limited resource coverage |
| 1 | Poor resource detection |

### Overall Quality Judge (20%)

**Sub-dimensions:**
- Message clarity (40%): Violation messages are understandable
- Fix suggestions (30%): Actionable remediation guidance
- Prioritization (30%): Severity levels are appropriate

**Scoring Rubric:**
| Score | Criteria |
|-------|----------|
| 5 | All violations have clear, actionable messages |
| 4 | Most violations are actionable |
| 3 | Basic actionability |
| 2 | Limited clarity |
| 1 | Messages not actionable |

---

## Running Evaluation

### Prerequisites

1. .NET SDK 8.0 or later
2. Python 3.10+ with virtual environment
3. Synthetic test project in `eval-repos/synthetic/csharp/`
4. Ground truth file in `evaluation/ground-truth/csharp.json`
5. (Optional) Anthropic API key for LLM evaluation

### Commands

```bash
# Setup environment
make setup

# Build synthetic C# project
make build

# Run analysis with dashboard
make analyze

# Run programmatic evaluation
make evaluate

# Run LLM evaluation
make evaluate-llm

# Combined evaluation
make evaluate-combined

# Clean generated files
make clean
```

### Output Artifacts

| File | Description |
|------|-------------|
| `evaluation/scorecard.md` | Human-readable evaluation report |
| `evaluation/results/<run_id>_checks.json` | Detailed check results |
| `evaluation/llm/results/*.json` | LLM judge results |
| `output/runs/<timestamp>.json` | Raw analysis output |

---

## Roslyn Rules Covered (44 Core Rules)

### Security Rules (15)

| Rule | Description | Severity |
|------|-------------|----------|
| CA3001 | SQL Injection | CRITICAL |
| CA3002 | XSS | CRITICAL |
| CA2100 | SQL (legacy) | CRITICAL |
| CA5350 | Weak Crypto (DES, 3DES) | HIGH |
| CA5351 | Broken Crypto (MD5) | HIGH |
| CA5385 | RSA Key Size < 2048 | HIGH |
| CA5390 | Hardcoded Keys | HIGH |
| CA5364 | Deprecated TLS | HIGH |
| CA5397 | Deprecated SSL | HIGH |
| CA2300-CA2315 | Insecure Deserialization | CRITICAL |
| CA3147 | Missing CSRF | MEDIUM |
| CA5391 | Missing Antiforgery | MEDIUM |
| SCS0016 | CSRF (SecurityCodeScan) | HIGH |

### Design Rules (12)

| Rule | Description | Severity |
|------|-------------|----------|
| CA1051 | Visible Instance Fields | HIGH |
| CA1040 | Empty Interfaces | MEDIUM |
| CA1000 | Static Members on Generic Types | MEDIUM |
| CA1001 | Missing IDisposable | HIGH |
| CA1061 | Hidden Base Methods | MEDIUM |
| CA1063 | Improper IDisposable | HIGH |
| CA1502 | Excessive Complexity | HIGH |
| CA1506 | Excessive Coupling | HIGH |
| IDE0040 | Missing Accessibility Modifiers | MEDIUM |

### Resource Management Rules (6)

| Rule | Description | Severity |
|------|-------------|----------|
| CA2000 | Objects Not Disposed | HIGH |
| CA2016 | Missing CancellationToken | MEDIUM |
| CA2007 | Task Await Issues | MEDIUM |
| IDISP001-017 | IDisposableAnalyzers | MEDIUM-HIGH |
| ASYNC0001 | Async Void | HIGH |

### Dead Code Rules (6)

| Rule | Description | Severity |
|------|-------------|----------|
| IDE0005 | Unused Imports | MEDIUM |
| IDE0060 | Unused Parameters | MEDIUM |
| IDE0052 | Unused Private Members | MEDIUM |
| IDE0059 | Unused Locals | LOW |
| CA1801 | Unused Parameters | MEDIUM |
| CA1812 | Uninstantiated Classes | LOW |

### Performance Rules (5)

| Rule | Description | Severity |
|------|-------------|----------|
| CA1826 | LINQ Alternatives | LOW |
| CA1829 | Length/Count Property | LOW |
| CA1825 | Empty Array Allocation | LOW |
| CA1834 | StringBuilder in Loops | MEDIUM |
| CA1858 | StartsWith Char | LOW |

---

## Extending Evaluation

### Adding a New Check

1. Add check function to appropriate module in `scripts/checks/`
2. Register in `run_all_*_checks()` function
3. Update scoring table thresholds if needed
4. Update documentation

### Adding a New Rule

1. Add rule to `rule_to_category_map` in ground truth
2. Create test file demonstrating the violation
3. Add expected violations to ground truth
4. Run evaluation to verify

### Adding Analyzer Package

1. Add package reference to `.csproj` file
2. Update ground truth with new rules
3. Update coverage checks with expected rule counts
4. Test and verify detection

---

## Appendix: Data Structures

### CheckResult

```python
@dataclass
class CheckResult:
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "SQL Injection Detection"
    category: str           # accuracy, coverage, edge_cases, performance
    passed: bool
    score: float            # 0.0 to 1.0
    threshold: float
    actual_value: float
    message: str
    evidence: dict = field(default_factory=dict)
```

### EvaluationReport

```python
@dataclass
class EvaluationReport:
    evaluation_id: str
    timestamp: str
    analysis_file: str
    summary: dict
    category_scores: dict
    checks: list[CheckResult]
    decision: str
    decision_reason: str
```

### Analysis Output Schema

```json
{
  "metadata": {
    "tool": "roslyn-analyzers",
    "tool_version": ".NET 8.0",
    "timestamp": "2026-01-06T10:30:00Z",
    "analysis_duration_ms": 5000,
    "target_path": "/path/to/project"
  },
  "summary": {
    "total_files_analyzed": 34,
    "total_violations": 113,
    "violations_by_category": {
      "security": 31,
      "design": 22,
      "resource": 22,
      "performance": 16,
      "dead_code": 22
    },
    "violations_by_rule": {
      "CA3001": 3,
      "CA5350": 2
    }
  },
  "files": [
    {
      "path": "security/sql_injection.cs",
      "relative_path": "security/sql_injection.cs",
      "lines_of_code": 80,
      "violations": [
        {
          "rule_id": "CA3001",
          "message": "Possible SQL injection vulnerability",
          "line_start": 15,
          "line_end": 15,
          "severity": "warning"
        }
      ]
    }
  ]
}
```

---

## Current Evaluation Results

### Summary (as of PoC completion)

| Metric | Value |
|--------|-------|
| Total Checks | 34 |
| Pass Rate | TBD (pending re-evaluation with EC-9 to EC-12) |
| Decision | STRONG_PASS |
| Recommendation | ADOPT for DD Platform integration |

### Per-Category Results

| Category | Checks | Pass Rate |
|----------|--------|-----------|
| Accuracy | 10 | 100% |
| Coverage | 8 | 100% |
| Edge Cases | 12 | TBD (8/8 original + 4 new) |
| Performance | 4 | 100% |

### LLM Evaluation Results

| Judge | Weight | Score | Confidence |
|-------|--------|-------|------------|
| Security Detection | 35% | 4/5 | 90% |
| Design Analysis | 25% | 4/5 | 85% |
| Resource Management | 20% | 5/5 | 95% |
| Overall Quality | 20% | 5/5 | 92% |
| **Combined** | | **4.45/5.0** | |

### Key Findings

1. **Strengths:**
   - Excellent resource management detection (CA2000, CA1001)
   - Strong security detection (SQL injection, weak crypto, deserialization)
   - Comprehensive design violation coverage
   - Built into .NET SDK, no external tools needed

2. **Limitations:**
   - XSS detection requires specialized data flow analysis (CA3002)
   - Hardcoded secrets detection limited (CA5390 deprecated)
   - IDE-only rules (IDE0005) don't work in MSBuild SARIF output
   - Code metrics rules (CA1502, CA1506) require separate NuGet package

3. **Recommendation:** STRONG_PASS - Approved for DD Platform integration

---

## DD Analyzer Lens Coverage

| Lens | Coverage | Roslyn Rules |
|------|----------|--------------|
| L1 (Structural) | Design violations | CA1051, CA1040, CA1502, CA1506 |
| L2 (Tech Debt) | Dead code + resources | IDE0005, IDE0060, CA2000, CA1001 |
| L6 (Quality) | Comprehensive rules | 44 rules across 5 categories |
| L7 (Security) | OWASP Top 10 | CA3001, CA3002, CA5350, CA2300-2315 |

---

## References

- [Roslyn Analyzers](https://docs.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview)
- [Microsoft.CodeAnalysis.NetAnalyzers](https://github.com/dotnet/roslyn-analyzers)
- [IDisposableAnalyzers](https://github.com/DotNetAnalyzers/IDisposableAnalyzers)
- [SecurityCodeScan](https://security-code-scan.github.io/)
- [Roslynator](https://github.com/JosefPihrt/Roslynator)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)

---

## Rollup Validation

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_roslyn_direct_vs_recursive.sql
