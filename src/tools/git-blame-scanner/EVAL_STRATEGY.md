# git-blame-scanner - Evaluation Strategy

> How we measure the quality and accuracy of per-file authorship metrics.

## Philosophy & Approach

"Correct" for git-blame-scanner means:

1. **Line counts match git blame exactly** - The sum of author lines equals git blame output
2. **Ownership percentages are accurate** - Mathematical correctness (lines / total * 100)
3. **Churn metrics reflect actual commits** - Matches git log --since output
4. **Knowledge silos correctly identified** - Files with unique_authors=1 and >100 LOC

We prioritize **accuracy over coverage** because incorrect authorship data can lead to wrong conclusions about knowledge distribution.

## Dimension Summary

| Dimension | Weight | Method | Target |
|-----------|--------|--------|--------|
| Accuracy | 50% | Programmatic + LLM | >99% |
| Coverage | 25% | Programmatic | >95% |
| Performance | 10% | Programmatic | <60s/1K files |
| Actionability | 15% | LLM | >80% |

**Rationale for weights:**
- Accuracy is critical - wrong authorship data is worse than missing data
- Coverage is important but binary files are expected to be skipped
- Performance is secondary since this is often a batch job
- Actionability ensures findings drive real actions

## Check Catalog

### Programmatic Checks

Located in `scripts/checks/`:

| Check Module | Dimension | Description |
|--------------|-----------|-------------|
| `accuracy.py` | Accuracy | Ownership percentages sum to 100%, line counts match |
| `coverage.py` | Coverage | All tracked files attempted, success rate tracked |
| `performance.py` | Performance | Execution time within limits |

**Specific accuracy checks:**
- `check_ownership_sums_100`: Each file's author ownership sums to 100%
- `check_unique_authors_consistency`: unique_authors matches actual author count
- `check_churn_monotonic`: churn_30d <= churn_90d (invariant)
- `check_top_author_valid`: top_author_pct >= 0 and <= 100

### LLM Judges

Located in `evaluation/llm/judges/`:

| Judge | Dimension | Evaluates |
|-------|-----------|-----------|
| `ownership_accuracy.py` | Accuracy | Do ownership percentages align with git blame? |
| `churn_validity.py` | Accuracy | Are churn metrics consistent with git history? |
| `actionability.py` | Actionability | Can findings guide knowledge transfer decisions? |
| `integration.py` | Integration | Schema compatibility with SoT layer |

## Scoring Methodology

### Aggregate Score Calculation

```
total_score = (
    accuracy_score * 0.50 +
    coverage_score * 0.25 +
    performance_score * 0.10 +
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
| Accuracy | =100% | 95-99% | <95% |
| Coverage | >=95% | 85-95% | <85% |
| Performance | <60s | 60-120s | >120s |
| Actionability | >=80% | 60-80% | <60% |

**Note:** Accuracy is strict because mathematical correctness is verifiable.

## Ground Truth Specifications

### Synthetic Repositories

Located in `eval-repos/synthetic/`:

| Repo | Purpose | Key Scenarios |
|------|---------|---------------|
| `single-author/` | All files by one author | 100% ownership, knowledge silos |
| `balanced/` | Equal contribution (3 authors) | 33% ownership each |
| `concentrated/` | 80% from one author | High concentration detection |
| `high-churn/` | Many recent commits | Churn metric validation |

### Ground Truth Format

See `evaluation/ground-truth/synthetic.json`.

```json
{
  "repo_name": "single-author",
  "files": {
    "src/main.py": {
      "unique_authors": 1,
      "top_author_pct": 100.0,
      "is_knowledge_silo": true
    }
  },
  "summary": {
    "single_author_pct": 100.0,
    "knowledge_silo_count": 3
  }
}
```

**Tip:** After running analysis, use `make seed-ground-truth` to auto-populate expected values from actual output.

---

## Rollup Validation

Rollups:
- `rollup_git_blame_directory_ownership_direct.sql`
- `rollup_git_blame_directory_ownership_recursive.sql`

**Invariants:**
- recursive_count >= direct_count
- avg_unique_authors (recursive) >= avg_unique_authors (direct)
- Files with unique_authors=1 contribute to single_author_files

Tests:
- src/sot-engine/dbt/tests/test_rollup_git_blame_invariants.sql
- src/tools/git-blame-scanner/tests/unit/test_analyze.py

## Invariants

| Invariant | Description | Check |
|-----------|-------------|-------|
| Ownership sum | Each file's author %'s sum to 100 | `check_ownership_sums_100` |
| Churn monotonic | churn_30d <= churn_90d | `check_churn_monotonic` |
| Top author valid | top_author_pct in [0, 100] | Schema validation |
| Unique authors | unique_authors >= 1 | Schema validation |
| Exclusive files | exclusive_files <= total_files | `check_exclusive_invariant` |
