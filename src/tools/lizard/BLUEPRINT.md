# BLUEPRINT: Lizard PoC Lessons Learned

**PoC #2: Function-Level Complexity Analysis**

This document captures lessons learned from evaluating [Lizard](https://github.com/terryyin/lizard) as a function-level complexity analyzer for the DD Platform.

## Final Results

| Metric | Value |
|--------|-------|
| Programmatic Checks | 76/76 (100%) |
| Programmatic Score | 98.8% |
| LLM Score | 5.00/5.0 |
| Combined Score | 4.84/5.0 |
| Decision | **STRONG_PASS** |

---

## What Worked

### 1. Function-Level Granularity
Lizard fills the critical gap left by scc (PoC #1). Where scc provides file-level LOC metrics, Lizard provides:
- Per-function cyclomatic complexity (CCN)
- Per-function NLOC, parameter count, token count
- Function location (start_line, end_line)
- Nested function detection with qualified names

This enables identification of **complexity hotspots** at the function level, which is essential for prioritizing refactoring.

### 2. 22-Metric Distribution Statistics
Following the pattern from PoC #1, we compute comprehensive distribution statistics:
- Basic: count, min, max, mean, median, stddev
- Percentiles: p25, p50, p75, p90, p95, p99
- Shape: skewness, kurtosis, cv, iqr
- Inequality: gini, theil, hoover, palma, top_10/20_pct_share, bottom_50_pct_share

These distributions enable statistical outlier detection and cross-project benchmarking.

### 3. Directory Rollup (Recursive vs Direct)
The directory rollup feature from PoC #1 proved valuable here too:
- **Direct stats**: Metrics from files directly in a directory
- **Recursive stats**: Metrics including all subdirectories

This helps identify which directories contain complexity vs. where it accumulates.

### 4. LLM-as-a-Judge Evaluation
Four specialized judges provide nuanced evaluation:
- **CCN Accuracy (35%)**: Validates CCN against ground truth
- **Function Detection (25%)**: Checks nested functions, lambdas, methods
- **Statistics (20%)**: Validates distribution monotonicity and validity
- **Hotspot Ranking (20%)**: Confirms high-CCN functions are flagged

The combined programmatic + LLM evaluation (60/40 weighting) provides both precision and semantic understanding.

### 5. Comprehensive Language Support
Lizard correctly analyzed all 7 target languages:

| Language | Files | Functions | CCN |
|----------|-------|-----------|-----|
| Java | 9 | 115 | 237 |
| JavaScript | 9 | 89 | 232 |
| Python | 9 | 60 | 227 |
| Go | 9 | 66 | 192 |
| Rust | 9 | 88 | 169 |
| TypeScript | 9 | 62 | 155 |
| C# | 9 | 44 | 139 |
| **Total** | **63** | **524** | **1,351** |

---

## What Didn't Work

### 1. Fan-In/Fan-Out Returns 0
Lizard's `fan_in` and `fan_out` fields always return 0. These would require additional static analysis:
- Fan-in: How many functions call this function
- Fan-out: How many functions this function calls

**Workaround**: Combine with dedicated dependency analysis tools.

### 2. Duplicate Function Names
Some files have multiple functions with the same short name (e.g., two functions named `>` in massive.ts with CCN=1 and CCN=26). This required special handling in ground truth matching:

```python
def _find_function_in_analysis(analysis, filename, func_name, expected_ccn=None):
    """If expected_ccn provided and multiple matches, return closest match."""
    if len(candidates) > 1 and expected_ccn:
        return min(candidates, key=lambda f: abs(f.get("ccn", 0) - expected_ccn))
```

### 3. Anonymous Function Naming
Anonymous functions are reported as `(anonymous)` without unique identifiers:
- TypeScript arrow functions: `(anonymous)` at line N
- JavaScript callbacks: `(anonymous)` at line M

This makes it hard to track specific anonymous functions across analyses.

### 4. Line Range Accuracy for Some Constructs
Some language constructs have inaccurate line ranges:
- Rust `impl` blocks: Some methods report wrong start/end
- JavaScript generators: Iterator methods may have off-by-one
- TypeScript arrow functions: Often report single-line ranges

Overall accuracy: 85-99% depending on language.

### 5. NLOC Definition Varies
Lizard's NLOC (non-commenting lines of code) definition differs slightly from expectations:
- Sometimes includes blank lines within function body
- Sometimes excludes closing braces
- Accuracy within 10% for 90%+ of functions

---

## Design Decisions

### 1. Standalone eval-repos (No Symlinks)
**Decision**: Copy synthetic repos, add real repos as git submodules.

**Rationale**: Self-contained PoC that can run independently. Enables different test configurations per PoC.

**Implementation**:
```bash
# Synthetic repos copied from poc-scc
cp -r ../poc-scc/eval-repos/synthetic ./eval-repos/

# Real repos as submodules
git submodule add https://github.com/pallets/click eval-repos/real/click
```

### 2. Single Output Envelope
**Decision**: Emit a single envelope output at `outputs/<run-id>/output.json`.

**Rationale**: One stable path simplifies ingestion and validation.

**Structure**:
```
outputs/<run-id>/
├── output.json            # Envelope output
└── metadata.json          # Run parameters, versions
```

```
evaluation/results/
├── output.json            # Envelope output for evaluation runs
├── evaluation_report.json # Programmatic evaluation report
├── scorecard.md           # Programmatic scorecard
└── llm_evaluation.json    # LLM judge results (if run)
```

### 3. Schema-First Design
**Decision**: Define envelope schema v1.0.0 before implementation.

**Key Schema Elements**:
```json
{
  "metadata": {
    "tool_name": "lizard",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "660e8400-e29b-41d4-a716-446655440001",
    "schema_version": "1.0.0"
  },
  "data": {
    "directories": [...],   // Rollup stats
    "files": [...],         // Per-file functions
    "summary": {...}        // Aggregate stats
  }
}
```

### 4. 16-Section Dashboard
**Decision**: Rich terminal dashboard with 16 sections.

**Sections**:
1. Header (repo, timestamp, version)
2. Quick Stats (files, functions, CCN)
3. CCN Distribution (histogram + percentiles)
4. Hotspot Functions (top 10 by CCN)
5. Large Functions (top 10 by NLOC)
6. Parameter-Heavy (5+ parameters)
7. Per-Language Summary
8. File Summary
9. Threshold Violations (CCN > 10)
10. Complexity Density (CCN/NLOC ratio)
11. Function Size Distribution
12. Analysis Summary
13. Directory Structure
14. Top Directories by CCN
15. Top Directories by Functions
16. Complete Directory Tree

---

## Language-Specific Quirks

### Python
- **Decorators**: `@property`, `@staticmethod` don't affect CCN
- **List comprehensions**: Each `if` adds +1 to CCN
- **Nested functions**: Detected with qualified names like `outer._inner`
- **Type hints**: Don't affect CCN calculation

### C#
- **Properties**: Getters/setters detected as separate functions
- **LINQ expressions**: Lambdas detected as anonymous functions
- **Expression-bodied members**: Correctly parsed
- **Local functions**: Detected with qualified names

### JavaScript
- **Arrow functions**: Detected as `(anonymous)` or with assigned name
- **Callbacks**: Detected but hard to identify by context
- **Generators**: `function*` correctly parsed
- **Class methods**: Qualified with class name

### TypeScript
- **Type annotations**: Don't affect CCN
- **Generics**: Correctly handled
- **Interface methods**: Not detected (no implementation)
- **Overloads**: Each overload is a separate function

### Go
- **Methods with receivers**: `(r *Repo) Find(id int)` format
- **defer/panic/recover**: Don't add to CCN
- **Goroutines**: `go func()` detected as anonymous
- **Multiple return values**: Don't affect CCN

### Rust
- **impl blocks**: Methods detected with qualified names
- **Closures**: Detected as anonymous
- **Pattern matching**: Each arm adds to CCN
- **Lifetime annotations**: Don't affect parsing

### Java
- **Constructors**: Detected as `ClassName::ClassName`
- **Anonymous classes**: Inner methods detected
- **Streams**: Lambda expressions detected
- **Switch expressions**: Each case adds to CCN

---

## Integration Recommendations

### 1. Combine with scc
Use both tools for comprehensive coverage:
- **scc**: File-level LOC, language detection, directory structure
- **Lizard**: Function-level CCN, hotspots, refactoring targets

```python
def analyze_codebase(path):
    scc_results = run_scc(path)      # File-level metrics
    lizard_results = run_lizard(path)  # Function-level metrics

    return merge_results(scc_results, lizard_results)
```

### 2. CCN Thresholds
Recommended thresholds for DD Platform:

| Level | CCN | Action |
|-------|-----|--------|
| Low | 1-5 | Normal complexity |
| Medium | 6-10 | Monitor, consider refactoring |
| High | 11-20 | Should refactor |
| Critical | 21+ | Must refactor or document |

### 3. Hotspot Prioritization
Combine CCN with churn data for prioritization:
```
Hotspot Score = CCN × Churn Factor
```
Files with high CCN AND high churn are the highest priority.

### 4. Distribution-Based Benchmarking
Use P90/P95 percentiles for benchmarking:
- P90 CCN < 6: Healthy codebase
- P90 CCN 6-10: Moderate complexity
- P90 CCN > 10: Needs attention

---

## Key Metrics Summary

| Check Category | Passed | Total | Score |
|----------------|--------|-------|-------|
| Accuracy | 56 | 56 | 98.9% |
| Coverage | 8 | 8 | 100% |
| Edge Cases | 8 | 8 | 100% |
| Performance | 4 | 4 | 100% |
| **Total** | **76** | **76** | **98.8%** |

**Performance Highlights**:
- Synthetic repos: 0.29s (threshold: 2s)
- Real repo (click): 0.35s (threshold: 5s)
- Real repo (picocli/src): 1.63s (threshold: 30s)
- Memory usage: 45.1MB (threshold: 500MB)

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/function_analyzer.py` | Main analysis script (16-section dashboard) |
| `scripts/evaluate.py` | Programmatic evaluation runner |
| `scripts/checks/*.py` | 76 evaluation checks |
| `evaluation/ground-truth/*.json` | Expected CCN for 524 functions |
| `evaluation/llm/judges/*.py` | 4 LLM judge implementations |
| `evaluation/llm/prompts/*.md` | Judge prompt templates |
| `schemas/output.schema.json` | Envelope JSON Schema v1.0.0 |
| `tests/` | Test suite |

---

## Next Steps

1. **Integration**: Merge Lizard results into DD Platform analytics layer
2. **Trend Analysis**: Track CCN changes over time via git history
3. **Dependency Analysis**: Add fan-in/fan-out via AST tools
4. **IDE Integration**: VSCode extension showing hotspots inline

---

## References

- [Lizard GitHub](https://github.com/terryyin/lizard)
- [Cyclomatic Complexity (Wikipedia)](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [McCabe (1976) - Original Paper](https://doi.org/10.1109/TSE.1976.233837)
- [PoC #1 BLUEPRINT](../poc-scc/BLUEPRINT.md)
