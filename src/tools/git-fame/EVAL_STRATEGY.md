# git-fame Evaluation Strategy

This document describes the evaluation framework for git-fame authorship analysis.

## Philosophy & Approach

The evaluation framework assesses git-fame's fitness for DD Platform integration across 6 dimensions.

### Key Principles

1. **Ground truth anchored**: All evaluations reference synthetic test repositories with known ownership patterns
2. **Multi-dimensional**: Accuracy, coverage, and reliability all matter
3. **Transparent scoring**: Every score has traceable evidence

---

## Dimension Summary

| Dimension | Code | Checks | Weight | Description |
|-----------|------|--------|--------|-------------|
| Authorship Accuracy | AA | 8 | 35% | Core ownership attribution |
| Output Quality | OQ | 6 | 15% | Schema and structure compliance |
| Reliability | RL | 4 | 15% | Determinism and edge cases |
| Performance | PF | 4 | 10% | Execution speed |
| Integration Fit | IF | 4 | 15% | DD Platform compatibility |
| Installation | IN | 2 | 10% | Setup and dependencies |
| **Total** | | **28** | **100%** | |

---

## Complete Check Catalog

### 1. Authorship Accuracy (AA) - 35% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| AA-1 | Total LOC | `total_loc == expected.total_loc` |
| AA-2 | Author Count | `author_count == expected.author_count` |
| AA-3 | Top Author LOC | `top_author_loc >= expected.top_author_loc * 0.9` |
| AA-4 | Ownership Percentages | Within 5% of expected per author |
| AA-5 | Bus Factor | `bus_factor == expected.bus_factor` |
| AA-6 | HHI Index | Within 0.1 of expected |
| AA-7 | Top Two Percentage | Within 5% of expected |
| AA-8 | File Attribution | All files have author attribution |

### 2. Output Quality (OQ) - 15% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| OQ-1 | Schema Version | `schema_version` present |
| OQ-2 | Timestamp | Valid ISO8601 timestamp |
| OQ-3 | Summary Fields | All required summary fields present |
| OQ-4 | Author Fields | All author records have required fields |
| OQ-5 | File Fields | All file records have required fields |
| OQ-6 | JSON Validity | Output parses as valid JSON |

### 3. Reliability (RL) - 15% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| RL-1 | Determinism | Two runs produce identical results |
| RL-2 | Empty Repo | Handles empty repository gracefully |
| RL-3 | Single Author | Handles single-author repo correctly |
| RL-4 | Rename Handling | Tracks authorship through file renames |

### 4. Performance (PF) - 10% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| PF-1 | Small Repo Speed | < 5 seconds for <100 files |
| PF-2 | Medium Repo Speed | < 30 seconds for 100-500 files |
| PF-3 | Memory Usage | < 500MB for standard repos |
| PF-4 | Incremental | Faster on subsequent runs |

### 5. Integration Fit (IF) - 15% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| IF-1 | Path Normalization | Paths match DD schema format |
| IF-2 | Metric Compatibility | Metrics map to L5/L8/L9 lenses |
| IF-3 | Directory Rollups | Aggregation by directory works |
| IF-4 | Collector Integration | Output matches collector schema |

### 6. Installation (IN) - 10% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| IN-1 | pip Install | `pip install git-fame` succeeds |
| IN-2 | CLI Help | `git-fame --help` returns 0 |

---

## Scoring Methodology

### Per-Dimension Scoring

| Checks Passed | Score |
|---------------|-------|
| 100% | 5 |
| 80-99% | 4 |
| 60-79% | 3 |
| 40-59% | 2 |
| <40% | 1 |

### Decision Thresholds

| Decision | Weighted Score |
|----------|----------------|
| STRONG_PASS | >= 4.0 |
| PASS | >= 3.5 |
| WEAK_PASS | >= 3.0 |
| FAIL | < 3.0 |

---

## Ground Truth Specifications

### Synthetic Test Repositories

| Repository | Authors | Expected Bus Factor | Expected HHI |
|------------|---------|---------------------|--------------|
| single-author | 1 | 1 | 1.0 |
| multi-author | 3 | 2 | 0.38 |
| bus-factor-1 | 3 | 1 | 0.82 |
| balanced | 4 | 3 | 0.25 |

---

## Running Evaluation

```bash
# Setup and run analysis
make setup
make build-repos
make analyze

# Run programmatic evaluation
make evaluate

# Run LLM evaluation
make evaluate-llm
```

---

## Rollup Validation

Rollups:
<!-- Author-level tool with no directory aggregations -->

Tests:
- src/tools/git-fame/tests/scripts/test_analyze.py
- src/tools/git-fame/tests/scripts/test_authorship_accuracy_checks.py
- src/tools/git-fame/tests/scripts/test_output_quality_checks.py
- src/tools/git-fame/tests/scripts/test_reliability_checks.py
