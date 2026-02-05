# dotcover - Evaluation Strategy

> How we measure the quality and accuracy of this tool's output.

## Philosophy & Approach

For dotCover, "correct" means:

1. **Coverage Accuracy**: Coverage percentages match what dotCover reports at each hierarchy level
2. **Coverage Invariants**: `covered_statements ≤ total_statements` for all entities
3. **Hierarchy Consistency**: Methods belong to types, types belong to assemblies
4. **Completeness**: All assemblies, types, and methods in the solution are reported

Unlike file-based tools (scc, semgrep), dotCover operates on .NET's compiled assembly hierarchy rather than file/directory structure. Evaluation focuses on the assembly→type→method relationship and coverage metric accuracy.

## Dimension Summary

| Dimension | Weight | Method | Target |
|-----------|--------|--------|--------|
| Accuracy | 40% | Programmatic + LLM | >95% |
| Coverage Completeness | 30% | Programmatic | >90% assemblies analyzed |
| Performance | 15% | Programmatic | <2min for typical repo |
| Actionability | 15% | LLM | >80% |

## Check Catalog

### Programmatic Checks

Located in `scripts/checks/`:

| Check Module | Dimension | Description |
|--------------|-----------|-------------|
| `accuracy.py` | Accuracy | Compare assemblies/types/methods against ground truth |
| `coverage.py` | Completeness | Verify all assemblies are analyzed |
| `performance.py` | Performance | Measure execution time (<2 minutes) |
| `invariants.py` | Accuracy | Validate covered ≤ total for all entities |

### LLM Judges

Located in `evaluation/llm/judges/`:

| Judge | Dimension | Evaluates |
|-------|-----------|-----------|
| `accuracy.py` | Accuracy | Do coverage percentages match expected? |
| `actionability.py` | Actionability | Are coverage gaps useful for developers? |
| `completeness.py` | Completeness | Are all assemblies and types reported? |
| `integration_fit.py` | Integration | Does output fit SoT schema? |

## Scoring Methodology

### Aggregate Score Calculation

```
total_score = (
    accuracy_score * 0.40 +
    coverage_score * 0.30 +
    performance_score * 0.15 +
    actionability_score * 0.15
)
```

### Per-Check Scoring

- `pass`: 100 points
- `warn`: 50 points
- `fail`: 0 points

## Decision Thresholds

| Dimension | Pass | Warn | Fail |
|-----------|------|------|------|
| Accuracy | >=95% | 85-95% | <85% |
| Coverage Completeness | >=90% | 80-90% | <80% |
| Performance | <2min | 2-5min | >5min |
| Actionability | >=80% | 60-80% | <60% |

## Ground Truth Specifications

### Synthetic Repositories

Located in `eval-repos/synthetic/`:

| Repo | Purpose | Key Scenarios |
|------|---------|---------------|
| CoverageDemo | Basic functionality | Simple class with methods |
| CoverageDemo.Tests | Test project | Tests covering CoverageDemo |

The synthetic repo contains:
- A main project with known methods and coverage states
- A test project that exercises partial coverage
- Expected coverage percentages documented in ground truth

### Ground Truth Format

See `evaluation/ground-truth/synthetic.json`.

Expected structure:
```json
{
  "assemblies": [
    {
      "name": "CoverageDemo",
      "expected_coverage_range": [60, 80]
    }
  ],
  "types": [
    {
      "name": "Calculator",
      "expected_methods": ["Add", "Subtract", "Multiply", "Divide"]
    }
  ]
}
```

**Tip:** After running analysis, use `make seed-ground-truth` to auto-populate
expected values from actual output.

---

## Rollup Validation

Rollups:

<!-- dotcover reports coverage at assembly/type/method levels, not traditional file/directory hierarchies -->

Tests:
- src/tools/dotcover/tests/unit/test_analyze.py

<!--
NOTE: dotCover does not produce directory-level rollups like file-based tools.
Coverage is aggregated along the assembly→namespace→type→method hierarchy instead.
No file/directory distribution tests are applicable.
-->

## Coverage-Specific Validation

### Invariant Checks

| Invariant | Description | Validation |
|-----------|-------------|------------|
| Covered ≤ Total | Covered statements never exceed total | `covered_statements <= total_statements` |
| Percentage Bounds | Coverage percentage in valid range | `0 <= coverage_pct <= 100` |
| Hierarchy Consistency | Methods reference valid types | Type names match across levels |
| Non-negative Counts | All counts are non-negative | `statements >= 0` |

### Assembly Coverage Validation

- Each assembly should have consistent coverage across its types
- Sum of type statements should approximate assembly totals

### Type Coverage Validation

- Types with no methods should have 0 statements
- Abstract types may have 0 coverage (no executable code)

### Method Coverage Validation

- Methods with 0 total statements are likely abstract/interface
- Coverage percentage should be calculated correctly: `covered / total * 100`
