# Blueprint: git-sizer Integration

## Executive Summary

**Tool**: git-sizer (GitHub-maintained)
**Purpose**: Repository health and size analysis
**Verdict**: RECOMMENDED for Caldera Platform integration

### Key Findings

| Dimension | Score | Notes |
|-----------|-------|-------|
| Size Accuracy | 5/5 | Precise blob/tree/commit measurements |
| Threshold Quality | 5/5 | Appropriate violation detection |
| Actionability | 5/5 | Clear LFS recommendations, useful grades |
| Integration Fit | 5/5 | Fills clear gap, fast performance |

## Gap Analysis

### What Caldera Has

| Tool | Level | Metrics |
|------|-------|---------|
| scc | File | LOC, language, blank/comment lines |
| lizard | Function | CCN, NLOC, token count |
| semgrep | File | Code smell detection |
| trivy | Package | Vulnerability detection |
| sonarqube | File | Quality issues, coverage |

### What git-sizer Adds

| Metric | Caldera Gap Filled |
|--------|-------------------|
| `health_grade` | Repository-level health scoring |
| `blob_total_size` | Total object store size |
| `max_blob_size` | Largest file (LFS candidates) |
| `max_tree_entries` | Directory width issues |
| `max_path_depth` | Path depth anti-patterns |
| `lfs_candidates[]` | Files to migrate to LFS |
| `violations[]` | Automatic issue detection |

### Overlap Assessment

| Metric | Overlap | Resolution |
|--------|---------|------------|
| commit_count | Partial | git-sizer provides additional depth metrics |
| blob sizes | No | Unique to git-sizer |
| tree metrics | No | Unique to git-sizer |
| LFS detection | No | Unique to git-sizer |

**Conclusion**: Minimal overlap. git-sizer provides unique repository-level health insights not available from existing tools.

## Integration Architecture

### Caldera SoT Engine Schema

```sql
-- Landing zone tables for git-sizer

CREATE TABLE lz_git_sizer_metrics (
    run_pk BIGINT NOT NULL PRIMARY KEY,
    repo_id VARCHAR NOT NULL,
    health_grade VARCHAR NOT NULL,
    duration_ms INTEGER,
    commit_count INTEGER,
    commit_total_size BIGINT,
    max_commit_size BIGINT,
    max_history_depth INTEGER,
    max_parent_count INTEGER,
    tree_count INTEGER,
    tree_total_size BIGINT,
    tree_total_entries INTEGER,
    max_tree_entries INTEGER,
    blob_count INTEGER,
    blob_total_size BIGINT,
    max_blob_size BIGINT,
    tag_count INTEGER,
    max_tag_depth INTEGER,
    reference_count INTEGER,
    branch_count INTEGER,
    max_path_depth INTEGER,
    max_path_length INTEGER,
    expanded_tree_count INTEGER,
    expanded_blob_count INTEGER,
    expanded_blob_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lz_git_sizer_violations (
    run_pk BIGINT NOT NULL,
    metric VARCHAR NOT NULL,
    value_display VARCHAR,
    raw_value BIGINT,
    level INTEGER NOT NULL,
    object_ref VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, metric)
);

CREATE TABLE lz_git_sizer_lfs_candidates (
    run_pk BIGINT NOT NULL,
    file_path VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_path)
);
```

### Adapter Implementation

The `GitSizerAdapter` class in `src/sot-engine/persistence/adapters/git_sizer_adapter.py`:

- Validates output against `schemas/output.schema.json`
- Persists to landing zone tables via `GitSizerRepository`
- Applies data quality rules (health grade valid, metrics non-negative, etc.)

### Entity Classes

```python
@dataclass(frozen=True)
class GitSizerMetric:
    """Repository-level metrics from git-sizer."""
    run_pk: int
    repo_id: str
    health_grade: str
    duration_ms: int
    commit_count: int
    # ... 20+ metric fields

@dataclass(frozen=True)
class GitSizerViolation:
    """Threshold violation from git-sizer."""
    run_pk: int
    metric: str
    value_display: str
    raw_value: int
    level: int  # 1-4
    object_ref: str | None

@dataclass(frozen=True)
class GitSizerLfsCandidate:
    """LFS migration candidate from git-sizer."""
    run_pk: int
    file_path: str
```

## Configuration

### Makefile Variables

```makefile
REPO_PATH ?= eval-repos/synthetic/healthy-repo
REPO_NAME ?= healthy-repo
OUTPUT_DIR ?= output/$(RUN_ID)
RUN_ID ?= $(shell uuidgen | tr '[:upper:]' '[:lower:]')
REPO_ID ?= $(shell uuidgen | tr '[:upper:]' '[:lower:]')
BRANCH ?= main
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD)
```

### Threshold Configuration

```python
# Threshold levels for violation detection
THRESHOLDS = {
    "max_blob_size": [
        (1 * 1024 * 1024, 1),    # 1 MiB = Level 1
        (10 * 1024 * 1024, 2),   # 10 MiB = Level 2
        (50 * 1024 * 1024, 3),   # 50 MiB = Level 3
        (100 * 1024 * 1024, 4),  # 100 MiB = Level 4
    ],
    "max_tree_entries": [
        (1000, 1),
        (5000, 2),
        (10000, 3),
        (50000, 4),
    ],
    # ... more thresholds
}
```

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Synthetic repos (5) | ~600ms | < 1s total |
| Per-repo average | ~120ms | Well under 2s threshold |
| Memory usage | Low | Single-pass analysis |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Binary dependency | Low | Medium | Auto-download, version pin |
| Large repo timeout | Medium | Low | Configurable timeout (300s default) |
| Threshold calibration | Medium | Low | Customizable thresholds |
| Schema migration | Low | Medium | Versioned schema |

## Lessons Learned

### What Worked Well

1. **Synthetic repos with specific characteristics** - Enabled precise accuracy testing
2. **Health grade system** - Provides actionable summary at repository level
3. **LFS candidate detection** - Immediately actionable recommendation
4. **Fast performance** - No pipeline impact concerns

### What Could Be Improved

1. **Threshold customization** - Current thresholds may need tuning per project type
2. **Path-based filtering** - Some false positives in LFS detection
3. **Shallow clone support** - Not tested with partial clones

### Recommendations

1. **Start with synthetic repos** - Allows controlled testing of edge cases
2. **Test on real repos early** - Validates real-world applicability
3. **Keep raw output** - Enables future metric extraction without re-running
4. **Make thresholds configurable** - Different projects have different norms

## Appendix: Test Results

### Synthetic Repository Results

| Repository | Grade | Violations | Blob Size | Duration |
|------------|-------|------------|-----------|----------|
| healthy | A | 0 | ~250 B | ~90ms |
| bloated | C+ | 1 | ~22 MiB | ~95ms |
| deep-history | A | 0 | ~14 KiB | ~280ms |
| wide-tree | D+ | 2 | ~300 KiB | ~145ms |

### Programmatic Evaluation

| Category | Passed | Total | Score |
|----------|--------|-------|-------|
| Accuracy | 8 | 8 | 100% |
| Coverage | 8 | 8 | 100% |
| Edge Cases | 8 | 8 | 100% |
| Performance | 4 | 4 | 100% |
| **Total** | **28** | **28** | **100%** |
