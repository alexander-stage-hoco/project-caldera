# git-fame Blueprint

## Executive Summary

git-fame provides line-level authorship attribution using git blame to identify code ownership and calculate knowledge concentration metrics. It is essential for L5 (Bus Factor), L8 (Authorship Distribution), and L9 (Knowledge Risk) lenses in the Due Diligence framework.

| Attribute | Value |
|-----------|-------|
| Tool | git-fame |
| Version | 3.1.1 |
| License | MPL-2.0 |
| Install | `pip install git-fame` |
| Primary Use | Line-level authorship attribution |
| DD Lenses | L5, L8, L9 |

## Architecture

### Data Flow

```
Repository → git-fame → Raw JSON → analyze.py → Caldera Envelope → Adapter → DuckDB
```

### Components

1. **Analysis Script** (`scripts/analyze.py`)
   - Runs git-fame on target repository
   - Transforms raw output to Caldera envelope format
   - Computes derived metrics (HHI, bus factor)

2. **Entities** (`sot-engine/persistence/entities.py`)
   - `GitFameAuthor`: Per-author metrics
   - `GitFameSummary`: Repository-level summary

3. **Adapter** (`sot-engine/persistence/adapters/git_fame_adapter.py`)
   - Validates output against schema
   - Creates entities from JSON
   - Persists to DuckDB landing zone

### Key Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| `surviving_loc` | Lines currently attributed to author | 0+ |
| `ownership_pct` | Percentage of total LOC | 0-100 |
| `hhi_index` | Ownership concentration | 0-1 (0=equal, 1=monopoly) |
| `bus_factor` | Authors needed for 50% coverage | 1+ |

## Implementation Plan

### Phase 1: Core Analysis
- [x] Run git-fame on repository
- [x] Parse JSON output
- [x] Compute HHI index
- [x] Compute bus factor

### Phase 2: Caldera Integration
- [x] Implement Caldera envelope format
- [x] Create entity definitions
- [x] Create persistence adapter
- [x] Add dbt staging models

### Phase 3: Evaluation
- [x] Build synthetic test repos
- [x] Create ground truth
- [x] Implement programmatic checks
- [x] Implement LLM judges

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RUN_ID` | Collection run UUID | Auto-generated |
| `REPO_ID` | Repository UUID | Auto-generated |
| `REPO_PATH` | Path to repository | Required |
| `OUTPUT_DIR` | Output directory | `outputs/$(RUN_ID)` |

### Command Line Options

```bash
python scripts/analyze.py <repo_path> [OPTIONS]

Options:
  -o, --output PATH       Output file or directory
  --by-extension         Show stats per file extension
  --since DATE           Date from which to check
  --until DATE           Date up to which to check
```

## Performance

### Benchmarks

| Repository Size | Time | Memory |
|----------------|------|--------|
| Small (<1k files) | <5s | <100MB |
| Medium (1-10k files) | 10-30s | 100-500MB |
| Large (10k+ files) | 1-5min | 500MB-1GB |

### Performance Characteristics

- **Linear Complexity**: O(files × commits) for git blame
- **Memory Bound**: Loads entire blame output per file
- **I/O Bound**: Git operations are primary bottleneck

### Optimization Strategies

1. Use `--since` flag for recent commits only
2. Run on shallow clones for quick estimates
3. Consider parallel execution on large repos

## Evaluation

### Evaluation Scores

| Evaluation Type | Score | Classification |
|-----------------|-------|----------------|
| Programmatic | 5.0/5.0 | STRONG_PASS |
| LLM-as-Judge | Requires API key | - |

### Programmatic Checks (28 total)

| Dimension | Checks | Weight |
|-----------|--------|--------|
| Output Quality | 6 | 20% |
| Authorship Accuracy | 8 | 20% |
| Reliability | 5 | 15% |
| Performance | 4 | 15% |
| Integration Fit | 3 | 15% |
| Installation | 2 | 15% |

### LLM Judges (6 total)

1. Authorship Quality
2. Bus Factor Accuracy
3. Concentration Metrics
4. Evidence Quality
5. Integration Readiness
6. Output Completeness

### Synthetic Test Repositories

| Repo | Authors | Distribution | Expected HHI | Expected Bus Factor |
|------|---------|--------------|--------------|---------------------|
| single-author | 1 | 100% | 1.0 | 1 |
| multi-author | 3 | 50/30/20 | ~0.38 | 1 |
| bus-factor-1 | 3 | 90/5/5 | ~0.82 | 1 |
| balanced | 4 | 25/25/25/25 | 0.25 | 2 |

### Scores

| Metric | Score | Detail |
|--------|-------|--------|
| Programmatic | 5.0/5.0 | 28/28 checks passed |
| LLM | 4.30/5.0 | 2 judges |
| **Combined** | **4.72/5.0** | **STRONG_PASS** |

## Risk

### Technical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Large repo timeout | Medium | Use `--since` flag, set timeout |
| Shallow clone data | High | Require full clone for analysis |
| Author identity fragmentation | Medium | Use `.mailmap` for normalization |

### Data Quality Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Binary file exclusion | Low | Expected behavior, document |
| Commit history manipulation | Medium | Cross-reference with commit analysis |
| Empty repository | Low | Validate file count > 0 |

### Operational Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| git-fame version mismatch | Low | Pin version in requirements |
| Python version incompatibility | Low | Use Python 3.12+ |
| Disk space for large repos | Medium | Monitor available space |

## Implementation Notes

### HHI Calculation

```python
def compute_hhi(ownership_pcts: List[float]) -> float:
    """HHI = sum of squared ownership percentages (as decimals)."""
    decimals = [p / 100.0 for p in ownership_pcts]
    return sum(d * d for d in decimals)
```

### Bus Factor Calculation

```python
def compute_bus_factor(ownership_pcts: List[float], threshold: float = 50.0) -> int:
    """Minimum authors for threshold% coverage."""
    sorted_pcts = sorted(ownership_pcts, reverse=True)
    cumulative = 0.0
    for i, pct in enumerate(sorted_pcts, 1):
        cumulative += pct
        if cumulative >= threshold:
            return i
    return len(sorted_pcts)
```

## Evidence Quality Assessment

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Completeness | High | All expected fields present |
| Accuracy | High | Matches ground truth |
| Provenance | High | Tool and command captured |
| Schema | High | Versioned, consistent |
| Transformability | High | Direct mapping to DD schema |

## Recommendations

1. **Use for Knowledge Risk Assessment**
   - Bus factor is highly reliable
   - HHI provides nuanced concentration view

2. **Combine with Commit Analysis**
   - git-fame shows surviving code
   - Commit analysis shows activity patterns
   - Together they provide full picture

3. **Consider Author Normalization**
   - Use `.mailmap` before analysis
   - Or post-process to merge identities

4. **Set Realistic Performance Expectations**
   - Small repos: < 5 seconds
   - Medium repos: 10-30 seconds
   - Large repos: minutes
