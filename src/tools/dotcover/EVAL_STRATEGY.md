# dotcover - Evaluation Strategy

> How we measure the quality and accuracy of this tool's output.

<!--
Template instructions (delete this section when done):
- Review docs/templates/EVAL_STRATEGY.md.template for full guidance
- See src/tools/scc/EVAL_STRATEGY.md for a complete example
- The Rollup Validation section is REQUIRED for compliance
-->

## Philosophy & Approach

[TODO: Describe what "correct" means for this tool]

**Example approaches:**
- **Metric accuracy**: Comparing detected metrics against manually verified values
- **Detection coverage**: Ensuring all relevant files/functions are analyzed
- **Precision/Recall**: For tools that detect issues (smells, vulnerabilities)

## Dimension Summary

| Dimension | Weight | Method | Target |
|-----------|--------|--------|--------|
| Accuracy | 40% | Programmatic + LLM | >95% |
| Coverage | 30% | Programmatic | >90% |
| Performance | 15% | Programmatic | <60s/10K files |
| Actionability | 15% | LLM | >80% |

[TODO: Adjust weights and targets based on your tool's priorities]

## Check Catalog

### Programmatic Checks

Located in `scripts/checks/`:

| Check Module | Dimension | Description |
|--------------|-----------|-------------|
| `accuracy.py` | Accuracy | Compare output against ground truth |
| `coverage.py` | Coverage | Verify all files are analyzed |
| `performance.py` | Performance | Measure execution time |

[TODO: Add your tool-specific checks]

### LLM Judges

Located in `evaluation/llm/judges/`:

| Judge | Dimension | Evaluates |
|-------|-----------|-----------|
| `accuracy.py` | Accuracy | Do findings match expected results? |
| `actionability.py` | Actionability | Are findings useful for developers? |
| `false_positive_rate.py` | Precision | Are findings actual issues? |
| `integration_fit.py` | Integration | Does output fit SoT schema? |

[TODO: Implement 4 standard judges - see docs/TOOL_REQUIREMENTS.md]

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
| Coverage | >=90% | 80-90% | <80% |
| Performance | <60s | 60-120s | >120s |
| Actionability | >=80% | 60-80% | <60% |

## Ground Truth Specifications

### Synthetic Repositories

Located in `eval-repos/synthetic/`:

| Repo | Purpose | Key Scenarios |
|------|---------|---------------|
| [TODO] | Basic functionality | Happy path, simple inputs |
| [TODO] | Edge cases | Empty files, large files, special chars |
| [TODO] | Language coverage | One file per supported language |

### Ground Truth Format

See `evaluation/ground-truth/synthetic.json`.

**Tip:** After running analysis, use `make seed-ground-truth` to auto-populate
expected values from actual output.

---

## Rollup Validation

Rollups:

<!-- dotcover reports coverage at assembly/type/method levels, not traditional file/directory hierarchies -->

Tests:
- src/tools/dotcover/tests/unit/test_analyze.py

<!--
NOTE: If your tool produces directory-level rollups, update this section:

Rollups:
- directory_direct_distributions
- directory_recursive_distributions

Tests:
- src/sot-engine/dbt/tests/test_rollup_dotcover_invariants.sql
-->
