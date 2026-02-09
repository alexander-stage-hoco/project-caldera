# git-blame-scanner - Architecture Blueprint

> Per-file authorship metrics for knowledge concentration and bus factor analysis at the file level.

## Executive Summary

git-blame-scanner complements git-fame by providing **per-file authorship metrics** rather than per-author aggregates. This enables identification of:

- **Knowledge silos**: Files owned by a single contributor
- **Ownership concentration**: Files where one author owns >80% of lines
- **Staleness indicators**: Files with no recent commits
- **Churn metrics**: Recent activity patterns at the file level

**Key use cases:**
- Bus factor analysis at file granularity
- Identifying knowledge transfer needs before team changes
- Finding stale, unmaintained code
- Measuring code review coverage gaps

## Gap Analysis

### Current State

| Aspect | Status |
|--------|--------|
| Tool maturity | Beta (new implementation) |
| Output format | JSON (Caldera envelope) |
| Language support | All (git blame is language-agnostic) |
| Performance | Moderate (O(n) git blame calls per file) |

### Integration Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| No author deduplication | Medium | Use email normalization or mailmap |
| Binary files not handled | Low | Excluded via git blame behavior |
| Large repos slow | Medium | Parallel blame execution in v2 |

## Architecture

### Data Flow

```
Repository (.git)
    |
    v
+-------------------+
| git ls-files      |  Get tracked files
+-------------------+
    |
    v
+-------------------+
| git blame         |  Per-file: author lines
+-------------------+
    |
    v
+-------------------+
| git log           |  Churn: commits per period
+-------------------+
    |
    v
+-------------------+
| analyze.py        |  Aggregate, normalize, envelope
+-------------------+
    |
    v
+-------------------+
| output.json       |  Caldera envelope format
+-------------------+
    |
    v
+-------------------+
| SoT Adapter       |  Persist to landing zone
+-------------------+
```

### Output Schema

See `schemas/output.schema.json` for complete schema.

Key data structures:
- `files[]`: Per-file metrics
  - `path`: Repo-relative file path
  - `unique_authors`: Count of distinct contributors
  - `top_author`, `top_author_pct`: Ownership concentration
  - `churn_30d`, `churn_90d`: Recent activity
  - `last_modified`: Date of most recent change
- `authors[]`: Per-author aggregates
  - `exclusive_files`: Files where author is sole contributor
  - `avg_ownership_pct`: Average ownership across files
- `summary`: Repository-level statistics
  - `single_author_pct`: Knowledge silo indicator
  - `high_concentration_pct`: Concentration risk
  - `knowledge_silo_count`: Critical single-author files

## Implementation Plan

### Phase 1: Standalone Tool

- [x] Create directory structure
- [x] Implement analyze.py with envelope output
- [x] Customize output.schema.json for tool metrics
- [ ] Add test files to eval-repos/synthetic/
- [ ] Implement programmatic checks in scripts/checks/
- [ ] Pass compliance scanner: `make compliance`

### Phase 2: SoT Integration

- [ ] Create entity dataclass in persistence/entities.py
- [ ] Create repository class in persistence/repositories.py
- [ ] Create adapter in persistence/adapters/
- [ ] Add dbt staging models
- [ ] Add rollup models for directory aggregations

### Phase 3: Evaluation

- [ ] Create ground truth in evaluation/ground-truth/
- [ ] Implement LLM judges in evaluation/llm/judges/
- [ ] Generate and review scorecard

## Configuration Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| REPO_PATH | `eval-repos/synthetic` | Repository to analyze |
| OUTPUT_DIR | `outputs/$(RUN_ID)` | Output directory |
| BRANCH | `main` | Branch to analyze |

### Analysis Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Churn periods | 30d, 90d | Short-term activity vs quarterly trends |
| Knowledge silo threshold | >100 LOC | Significant files only |
| High concentration | >=80% | Industry standard for code ownership |

## Performance Characteristics

**Bottleneck:** git blame calls (one per file)

| Repo Size | Estimated Time | Notes |
|-----------|---------------|-------|
| 100 files | ~5 seconds | Single blame ~50ms |
| 1K files | ~1 minute | Linear scaling |
| 10K files | ~10 minutes | Consider parallelization |

**Optimization opportunities:**
1. Parallel git blame execution
2. Caching blame results between runs
3. Incremental analysis (only changed files)

## Evaluation Results

See [evaluation/scorecard.md](./evaluation/scorecard.md) for results.

## Risk Assessment

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Author email variations | Names may not merge | Use git mailmap |
| Renamed files lose history | Missing blame data | `git log --follow` (future) |
| Binary files skipped | Incomplete coverage | Expected behavior |
| Large file blame slow | Performance | Progress indicator |
| Uncommitted changes ignored | Current state only | Document limitation |

### Security Considerations

- No secrets exposure (only author emails, line counts)
- All data from git history (already committed)
- Output should be treated as internal metrics
