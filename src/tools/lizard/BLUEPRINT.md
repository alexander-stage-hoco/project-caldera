# BLUEPRINT: Lizard PoC Lessons Learned

**PoC #2: Function-Level Complexity Analysis**

This document captures lessons learned from evaluating [Lizard](https://github.com/terryyin/lizard) as a function-level complexity analyzer for the DD Platform.

## Executive Summary

**Tool:** Lizard v1.17.10+
**Purpose:** Function-level cyclomatic complexity (CCN) and metrics analysis
**Recommendation:** ADOPT for complexity hotspot detection

| Metric | Result |
|--------|--------|
| Programmatic Score | 98.8% (76/76 checks) |
| LLM Score | 5.00/5.0 |
| Combined Score | 4.84/5.0 |
| Languages Supported | 7 (Python, C#, Java, JavaScript, TypeScript, Go, Rust) |
| Decision | **STRONG_PASS** |

**Key Strengths:**
- Per-function CCN, NLOC, parameter count, token count
- 22-metric distribution statistics
- Directory rollup (recursive vs direct)
- Multi-language support with unified output

**Key Limitations:**
- Fan-in/fan-out always returns 0
- Duplicate function names require CCN-based disambiguation
- Anonymous function naming not unique

---

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

## Recent Changes

### Performance Optimizations

#### O(n) Directory Aggregation

Directory rollup was refactored from recursive traversal to bottom-up memoized aggregation:

```python
# Process directories bottom-up (leaves first)
sorted_dirs = sorted(all_dirs, key=lambda d: d.count('/'), reverse=True)

# Cache for recursive data: {dir_path: (files, functions)}
recursive_cache: Dict[str, tuple[List[FileInfo], List[FunctionInfo]]] = {}

for dir_path in sorted_dirs:
    # Start with direct data
    recursive_files = list(direct_files)
    recursive_functions = list(direct_functions)

    # Aggregate from already-computed children (O(1) lookup)
    for child in dir_children.get(dir_path, []):
        child_files, child_funcs = recursive_cache[child]
        recursive_files.extend(child_files)
        recursive_functions.extend(child_funcs)

    recursive_cache[dir_path] = (recursive_files, recursive_functions)
```

This reduces complexity from O(n × depth) to O(n), dramatically improving performance for deeply nested directories.

#### Thread Limiting

Default thread count reduced from `cpu_count()` to `min(cpu_count() // 2, 4)` to avoid thrashing on hyperthreaded CPUs. Configurable via `LIZARD_THREADS` Makefile variable.

### File Exclusion System

#### Pattern-Based Exclusions

Files matching these patterns are excluded from analysis:

```python
EXCLUDE_PATTERNS = [
    # Minified files
    '*.min.js', '*.min.css', '*.min.ts',
    # Bundled/compiled output
    '*.bundle.js', '*.chunk.js', '*.umd.js',
    # Common vendor libraries
    'jquery*.js', 'react*.js', 'vue*.js', 'angular*.js',
    'lodash*.js', 'moment*.js', 'd3*.js',
    # Generated code
    '*.designer.cs', '*.g.cs', '*.generated.*',
    '*_pb2.py', '*.pb.go', '*_pb2_grpc.py', '*.d.ts',
    # Source maps
    '*.map',
]
```

#### Content-Based Minification Detection

For JavaScript/TypeScript files, content heuristics detect minified code:

```python
def is_likely_minified(filepath: Path, sample_size: int = 8192) -> bool:
    # Heuristic 1: Average line length > 500 chars
    avg_line_length = len(content) / len(lines)
    if avg_line_length > 500:
        return True

    # Heuristic 2: Single line > 1000 chars in first 10 lines
    for line in lines[:10]:
        if len(line) > 1000:
            return True

    # Heuristic 3: Very few newlines (< 1 per 500 chars)
    newline_ratio = len(lines) / len(content) if content else 0
    if newline_ratio < 0.002:
        return True

    return False
```

#### Excluded Files Tracking

Excluded files are tracked via the `ExcludedFile` dataclass:

```python
@dataclass
class ExcludedFile:
    path: str       # Repo-relative path
    reason: str     # 'pattern', 'minified', 'large', 'language'
    language: str   # Detected language (if applicable)
    details: str    # Additional info (matched pattern, file size)
```

### DuckDB Adapter Integration

#### LizardExcludedFile Entity

New frozen dataclass for excluded file records:

```python
@dataclass(frozen=True)
class LizardExcludedFile:
    run_pk: int
    file_path: str        # Repo-relative path
    reason: str           # 'pattern', 'minified', 'large', 'language'
    language: str | None
    details: str | None

    def __post_init__(self) -> None:
        _validate_positive_pk(self.run_pk)
        _validate_relative_path(self.file_path, "file_path")
        _validate_required_string(self.reason, "reason")
```

#### Landing Zone Table

```sql
CREATE TABLE lz_lizard_excluded_files (
    run_pk BIGINT NOT NULL,
    file_path VARCHAR NOT NULL,
    reason VARCHAR NOT NULL,
    language VARCHAR,
    details VARCHAR,
    PRIMARY KEY (run_pk, file_path)
);
```

#### Adapter Enhancements

**Pseudo-Function Filtering**: Skips lizard artifacts like `*global*` with invalid line numbers:

```python
# Skip pseudo-functions like *global* with line_start < 1
if line_start is not None and line_start < 1:
    self._log(f"WARN: skipping pseudo-function {func.get('name')}")
    continue
```

**Flexible Field Mapping**: Handles field name variations for backward compatibility:

```python
# Handle both naming conventions
line_start = func.get("line_start") or func.get("start_line")
line_end = func.get("line_end") or func.get("end_line")
params = func.get("params") or func.get("parameter_count")
```

### Schema Changes

The output schema (`schemas/output.schema.json`) now includes:

1. **`excluded_files` array**: Top-level array tracking all excluded files
2. **Summary exclusion counts**: `excluded_count`, `excluded_by_pattern`, `excluded_by_minified`, `excluded_by_size`, `excluded_by_language`
3. **22-metric distributions**: count, min, max, mean, median, stddev, percentiles (p25-p99), skewness, kurtosis, cv, iqr, gini, theil, hoover, palma, share metrics

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Lizard Analysis                                 │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  function_      │───▶│  Lizard CLI     │───▶│  JSON Output    │        │
│  │  analyzer.py    │    │  (per-language) │    │  (envelope)     │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                     │                       │                  │
│           ▼                     ▼                       ▼                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  Dashboard      │    │  Statistics     │    │  Directory      │        │
│  │  (16 sections)  │    │  (22 metrics)   │    │  Rollups        │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Evaluation Framework                               │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  evaluate.py    │───▶│  76 checks      │───▶│  Scorecard      │        │
│  │                 │    │  (4 categories) │    │  (JSON/MD)      │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                               │
│  │  LLM Judges     │───▶│  orchestrator   │                               │
│  │  (4 judges)     │    │                 │                               │
│  └─────────────────┘    └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Repository path passed to `function_analyzer.py`
2. **File Discovery**: Walk directory tree, apply exclusion patterns
3. **Minification Detection**: Content-based heuristics for JS/TS files
4. **Exclusion Tracking**: Excluded files logged with reason/details
5. **Analysis**: Lizard CLI extracts per-function metrics
6. **Statistics**: 22-metric distributions computed per file/directory
7. **Rollups**: Bottom-up O(n) directory aggregation with memoization
8. **Output**: Caldera envelope JSON with files, functions, and excluded_files
9. **Persistence**: Adapter maps to entities, inserts into DuckDB landing zone

---

## Implementation Plan

### Completed Phases

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1: Core Analysis** | Complete | function_analyzer.py with Lizard integration |
| **Phase 2: Statistics** | Complete | 22-metric distributions |
| **Phase 3: Rollups** | Complete | Directory recursive/direct aggregations |
| **Phase 4: Dashboard** | Complete | 16-section terminal output |
| **Phase 5: Evaluation** | Complete | 76 programmatic checks, 4 LLM judges |
| **Phase 6: Documentation** | Complete | BLUEPRINT, EVAL_STRATEGY, README |

---

## Configuration

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | `eval-repos/synthetic` | Repository to analyze |
| `REPO_NAME` | `synthetic` | Output file naming |
| `OUTPUT_DIR` | `outputs/$(RUN_ID)` | Output directory |
| `LLM_MODEL` | `opus-4.5` | Model for LLM evaluation |
| `LIZARD_THREADS` | `4` | Number of analysis threads |
| `QUIET` | unset | Set to `1` to suppress progress output |

### CLI Options

| Option | Description |
|--------|-------------|
| `--repo-path` | Path to repository to analyze |
| `--output` | Output JSON file path |
| `--threshold` | CCN threshold for violations (default: 10) |
| `--verbose` | Enable verbose output |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `RUN_ID` | UUID for the analysis run |
| `REPO_ID` | UUID identifying the repository |
| `PYTHONPATH` | Must include src/ for shared imports |

---

## Performance

### Optimizations

| Optimization | Description |
|--------------|-------------|
| O(n) Directory Aggregation | Bottom-up memoized aggregation instead of O(n × depth) recursive traversal |
| Thread Limiting | Default `min(cpu_count // 2, 4)` to avoid thrashing on hyperthreaded CPUs |
| File Exclusions | Skip minified/bundled/generated files before parsing |

### Benchmarks

| Repository Size | Files | Functions | Time | Memory |
|-----------------|-------|-----------|------|--------|
| Synthetic | 63 | 524 | 0.29s | ~45MB |
| click | 62 | ~800 | 0.35s | ~50MB |
| picocli/src | ~200 | ~2000 | 1.63s | ~80MB |

### Performance Thresholds

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Synthetic repos | < 2s | Quick feedback loop |
| Real repo (small) | < 5s | Acceptable CI time |
| Real repo (large) | < 30s | Maximum acceptable |
| Memory usage | < 500MB | Reasonable footprint |

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CCN miscounting | Low | Medium | Ground truth validation for 524 functions |
| Language parser bugs | Low | Low | Lizard is well-maintained |
| Memory on large repos | Low | Medium | Streaming output if needed |
| Anonymous function tracking | Medium | Low | Document limitation |
| Line range inaccuracy | Medium | Low | Tolerance in accuracy checks |

### Security Considerations

1. **No Code Execution**: Lizard parses AST, doesn't execute code
2. **Path Safety**: All paths normalized to repo-relative
3. **Output Safety**: No sensitive data in output

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
| `scripts/analyze.py` | CLI wrapper with shared argument parsing |
| `scripts/evaluate.py` | Programmatic evaluation runner |
| `scripts/checks/*.py` | 76 evaluation checks |
| `scripts/checks/exclusion.py` | Exclusion pattern validation checks |
| `evaluation/ground-truth/*.json` | Expected CCN for 524 functions |
| `evaluation/llm/judges/*.py` | 4 LLM judge implementations |
| `evaluation/llm/prompts/*.md` | Judge prompt templates |
| `schemas/output.schema.json` | Envelope JSON Schema v1.0.0 |
| `tests/` | Test suite |

### SoT Engine Integration Files

| File | Purpose |
|------|---------|
| `src/sot-engine/persistence/entities.py` | `LizardExcludedFile` entity |
| `src/sot-engine/persistence/schema.sql` | `lz_lizard_excluded_files` table DDL |
| `src/sot-engine/persistence/adapters/lizard_adapter.py` | JSON → entity mapping |

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
