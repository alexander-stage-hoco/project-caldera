# Symbol Scanner Evaluation Strategy

## Philosophy

Symbol Scanner evaluation prioritizes **extraction completeness** over false-positive avoidance. The tool should capture all visible symbols, calls, and imports in Python and C# source code, accepting some noise from dynamic patterns rather than missing legitimate code elements.

**Guiding Principles:**
1. **Completeness first**: Better to extract extra symbols than miss real ones
2. **Accuracy matters**: Line numbers, types, and names must be precise
3. **Ground truth anchors**: Programmatic checks against known-good outputs
4. **LLM validation**: Human-like review for edge cases and coherence

## Dimension Summary

| Dimension | Weight | Pass Threshold | Description |
|-----------|--------|----------------|-------------|
| Symbol Extraction | 30% | 90% | Functions, classes, methods captured correctly |
| Call Relationships | 30% | 85% | Caller/callee pairs with accurate line numbers |
| Import Completeness | 20% | 90% | All import statements with correct paths |
| Integration Quality | 20% | 85% | Cross-file consistency, envelope validity |

## Evaluation Dimensions

### 1. Symbol Extraction Accuracy

**Metrics:**
- Symbol count match (precision/recall)
- Symbol type accuracy
- Line number accuracy (±0 tolerance)
- Export detection accuracy

**Ground Truth:**
- Manual annotation of test repos
- Verified against IDE symbol listings

### 2. Call Relationship Accuracy

**Metrics:**
- Call count match
- Caller/callee symbol accuracy
- Call type classification
- Line number accuracy

**Ground Truth:**
- Manual trace through source code
- Cross-reference with static analysis tools

### 3. Import Extraction Accuracy

**Metrics:**
- Import count match
- Import path accuracy
- Symbol list accuracy
- Import type classification

**Ground Truth:**
- Direct comparison with source imports
- Verified import semantics

### 4. Integration Quality

**Metrics:**
- Cross-file consistency
- Path normalization correctness
- Envelope metadata validity
- Schema compliance

## Programmatic Evaluation

### Check Catalog

| Check ID | Category | Description | Severity |
|----------|----------|-------------|----------|
| `SYM001` | Schema | Valid JSON Schema 2020-12 | Critical |
| `SYM002` | Schema | Required metadata fields present | Critical |
| `SYM003` | Symbols | Symbol count matches expected | High |
| `SYM004` | Symbols | Symbol types correct (function/class/method) | High |
| `SYM005` | Symbols | Line numbers within file bounds | Medium |
| `SYM006` | Calls | Call count matches expected | High |
| `SYM007` | Calls | Caller/callee pairs exist in symbol list | High |
| `SYM008` | Calls | Call type classification correct | Medium |
| `SYM009` | Imports | Import count matches expected | High |
| `SYM010` | Imports | Import paths are valid module references | Medium |
| `SYM011` | Integration | All paths repo-relative | Critical |
| `SYM012` | Integration | Summary counts match actual data | High |

### Check Categories

| Category | Checks | Weight |
|----------|--------|--------|
| Schema | JSON schema validation | 10% |
| Symbols | Count, types, locations | 30% |
| Calls | Count, accuracy, types | 30% |
| Imports | Count, paths, symbols | 20% |
| Integration | Paths, metadata | 10% |

### Scoring

```
score = weighted_sum(category_scores)
grade = A (>=90%) | B (>=80%) | C (>=70%) | D (>=60%) | F (<60%)
```

## Decision Thresholds

| Decision | Threshold | Action |
|----------|-----------|--------|
| Pass | Score ≥ 85% | Tool output accepted |
| Warn | 70% ≤ Score < 85% | Review required, output usable |
| Fail | Score < 70% | Output rejected, investigation needed |

**Critical Check Failures:**
- Any Critical severity check failure → automatic Fail
- 3+ High severity failures → automatic Fail

**Regression Detection:**
- Score drops >5% from baseline → flag for review
- New check failures → block merge until resolved

## LLM Judges

### Judge 1: Symbol Accuracy Judge

**Prompt Focus:**
- Are all visible symbols extracted?
- Are symbol types correct?
- Are line numbers accurate?

**Input:**
- Source code
- Extracted symbols

**Output:**
- Accuracy score (0-100)
- Missing symbols list
- Incorrect classifications

### Judge 2: Call Relationship Judge

**Prompt Focus:**
- Are all calls captured?
- Are caller/callee pairs correct?
- Are call types appropriate?

**Input:**
- Source code
- Extracted calls

**Output:**
- Completeness score
- False positive rate
- Edge case handling

### Judge 3: Import Completeness Judge

**Prompt Focus:**
- Are all imports captured?
- Are import paths correct?
- Are imported symbols listed?

**Input:**
- Source code
- Extracted imports

**Output:**
- Import coverage
- Path accuracy
- Symbol accuracy

### Judge 4: Integration Judge

**Prompt Focus:**
- Cross-file consistency
- Overall coherence
- Edge case handling

**Input:**
- Full analysis output
- Multiple source files

**Output:**
- Consistency score
- Integration issues
- Recommendations

## Ground Truth

Ground truth files define expected outputs for synthetic test repositories.

### Structure

```json
{
  "metadata": {
    "repo": "simple-functions",
    "created": "2026-02-03",
    "version": "1.0"
  },
  "expected": {
    "symbols": [...],
    "calls": [...],
    "imports": [...],
    "summary": {...}
  }
}
```

### Management

- **Creation**: Manual annotation verified against IDE symbol listings
- **Updates**: Require peer review when test repos change
- **Location**: `evaluation/ground-truth/*.json`

### Test Repos

#### Python Test Repos

| Repo | Purpose | Focus |
|------|---------|-------|
| simple-functions | Basic extraction | Function defs, simple calls |
| class-hierarchy | OOP patterns | Classes, methods, inheritance |
| import-patterns | Import variations | Static, relative, star imports |
| cross-module-calls | Multi-file | Cross-file function calls |
| unresolved-externals | External deps | Stdlib, third-party calls |

#### C# Test Repos

| Repo | Purpose | Focus |
|------|---------|-------|
| csharp-tshock | Real-world validation | TShock server mod (107 files, 2,815 symbols) |

C# evaluation validates all 3 extractors (tree-sitter, roslyn, hybrid) produce consistent results.

## Evaluation Pipeline

```bash
# 1. Run analysis
make analyze REPO_PATH=eval-repos/synthetic/simple-functions

# 2. Run programmatic evaluation
make evaluate

# 3. Run LLM evaluation
make evaluate-llm

# 4. Generate combined scorecard
make evaluate-combined
```

## Scorecard Format

```markdown
# Symbol Scanner Evaluation Scorecard

## Summary
- Overall Grade: A (92%)
- Symbols: 95%
- Calls: 88%
- Imports: 94%
- Integration: 91%

## Details
[Per-category breakdown]

## Issues Found
[List of failures with context]

## Recommendations
[Improvement suggestions]
```

## Continuous Evaluation

### On Code Changes
1. Run programmatic evaluation
2. Compare against baseline
3. Flag regressions

### Periodic Full Evaluation
1. Run all test repos
2. Run LLM judges
3. Update baseline if justified

## Rollup Validation

Directory-level aggregations for symbol-scanner data are validated through dbt staging models.

Tests:
- src/sot-engine/dbt/models/staging/stg_lz_code_symbols.sql

### Rollup Details

Symbol-scanner data feeds into cross-tool coupling rollups:

| Rollup | Description |
|--------|-------------|
| `rollup_coupling_directory_metrics_direct` | Import/call coupling metrics per directory |

The symbol-scanner staging models provide data used in:
- `stg_lz_code_symbols` - Symbol extraction staging
- `stg_lz_symbol_calls` - Call relationship staging
- `stg_lz_file_imports` - Import statement staging

### Invariants

1. **Non-negative counts**: All symbol/call/import counts must be >= 0
2. **Valid symbol types**: Symbol types must be one of: function, class, method, variable, property, field, event
3. **Valid call types**: Call types must be one of: direct, dynamic, async, delegate, event
4. **Valid import types**: Import types must be one of: static, dynamic, type_checking, side_effect, global, extern
