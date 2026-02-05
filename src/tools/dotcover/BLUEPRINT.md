# dotcover - Architecture Blueprint

> JetBrains dotCover provides .NET code coverage at statement level across assembly/type/method hierarchy.

## Executive Summary

**dotCover** (JetBrains dotCover Command-Line Tools) provides code coverage analysis for .NET applications, reporting statement-level coverage metrics across the assembly→namespace→type→method hierarchy.

| Aspect | Status |
|--------|--------|
| **Purpose** | Code coverage analysis with statement-level granularity |
| **Evaluation Score** | Pending |
| **Recommendation** | ADOPT for .NET code coverage layer |
| **Languages Supported** | C#, F#, VB.NET (all .NET languages) |
| **Programmatic Checks** | Pending |

**Key Strengths:**
- Statement-level coverage granularity
- Integration with dotnet test workflow
- Assembly/Type/Method hierarchy reporting
- JSON and XML output formats

**Known Limitations:**
- Requires tests to run (coverage collected during test execution)
- macOS ARM64 report generation bug (timeout workaround in place)
- No branch coverage (statement coverage only)
- No line-level coverage detail

---

## Gap Analysis

### Current State

| Aspect | Status |
|--------|--------|
| Tool maturity | Stable |
| Output format | JSON |
| Language support | .NET (C#, F#, VB.NET) |
| Performance | Moderate (30s-2min depending on test suite) |

### Integration Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| Requires dotnet test to run first | Medium | Build step dependency in Makefile |
| macOS ARM64 report generation bug | Medium | Timeout with snapshot fallback |
| No line-level coverage | Low | Accept statement-level granularity |
| No branch coverage | Low | Statement coverage sufficient for MVP |

### Integration Strategy
1. Use dotCover for all .NET code coverage metrics (authoritative source)
2. Integrate with dotnet test workflow for coverage collection
3. Map assembly/type/method hierarchy to SoT entities
4. Accept macOS ARM64 limitations with snapshot fallback

---

## Architecture

### Data Flow

```
Repository
    |
    v
+------------------+
| dotnet test      |  Build and run tests
+------------------+
    |
    v
+------------------+
| dotCover cover   |  Collect coverage during test run
+------------------+
    |
    v
+------------------+
| dotCover report  |  Generate JSON/XML reports
+------------------+
    |
    v
+------------------+
| analyze.py       |  Parse, normalize, wrap in envelope
+------------------+
    |
    v
+------------------+
| output.json      |  Caldera envelope format
+------------------+
    |
    v
+------------------+
| SoT Adapter      |  Persist to landing zone
+------------------+
```

### Output Schema

See `schemas/output.schema.json` for complete schema.

Key data structures:
- `assemblies[]`: Assembly-level coverage (name, covered/total statements, percentage)
- `types[]`: Type (class) level coverage with optional source file mapping
- `methods[]`: Method-level coverage detail
- `summary`: Aggregate coverage statistics

---

## Implementation Plan

### Phase 1: Standalone Tool

- [x] Create directory structure (done by create-tool.py)
- [x] Implement analyze.py with envelope output
- [x] Customize output.schema.json for tool metrics
- [x] Add test files to eval-repos/synthetic/
- [ ] Implement programmatic checks in scripts/checks/
- [ ] Pass compliance scanner: `make compliance`

### Phase 2: SoT Integration

- [x] Create entity dataclass in persistence/entities.py
- [x] Create repository class in persistence/repositories.py
- [x] Create adapter in persistence/adapters/
- [x] Add dbt staging models

### Phase 3: Evaluation

- [ ] Create ground truth in evaluation/ground-truth/
- [ ] Implement LLM judges in evaluation/llm/judges/
- [ ] Generate and review scorecard

---

## Configuration Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| REPO_PATH | `eval-repos/synthetic` | Repository to analyze |
| OUTPUT_DIR | `outputs/$(RUN_ID)` | Output directory |
| TEST_PROJECT | (auto-detected) | Path to test project (.csproj) |

### CLI Options (analyze.py)

| Option | Description |
|--------|-------------|
| `--repo-path` | Path to repository to analyze |
| `--output-dir` | Directory for output files |
| `--test-project` | Specific test project to run (.csproj) |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `REPO_PATH` | Repository path (alternative to CLI arg) |
| `OUTPUT_DIR` | Output directory (alternative to CLI arg) |

---

## Performance Characteristics

### Benchmarks

| Repository Size | Test Count | Execution Time | Notes |
|-----------------|------------|----------------|-------|
| Small (synthetic) | ~10 | 30-60s | Includes build + test |
| Medium (100 tests) | ~100 | 1-2 min | Dominated by test execution |
| Large (1000+ tests) | 1000+ | 5-10 min | Test suite dependent |

### Key Performance Metrics

- **Primary bottleneck**: Test execution time (not coverage collection)
- **Report generation**: ~10-30s for JSON/XML output
- **Memory usage**: Depends on solution size
- **macOS ARM64 bug**: Report generation may hang, 2-minute timeout applied

### Optimization Notes

1. **Use `--no-build`** when tests are already built (saves rebuild time)
2. **Target specific test project** to reduce scope
3. **Snapshot-only mode** on macOS ARM64 (generate reports on supported platform)

---

## Evaluation Results

See [evaluation/scorecard.md](./evaluation/scorecard.md) for results.

---

## Risk Assessment

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Requires tests to run | High | Document build prerequisites |
| macOS ARM64 report timeout | Medium | 2-min timeout, snapshot fallback |
| No branch coverage | Low | Statement coverage sufficient |
| No line-level detail | Low | Method-level granularity acceptable |

### Dependency Risks

| Dependency | Version | Risk | Mitigation |
|------------|---------|------|------------|
| dotCover CLI | 2025.3+ | Tool updates may change output | Pin version in CI |
| dotnet SDK | 6.0+ | Version compatibility | Specify in requirements |
| Test framework | xUnit/NUnit/MSTest | Must be testable project | Document requirements |

### Integration Risks

| Risk | Description | Mitigation |
|------|-------------|------------|
| Build failures | Tests must compile and pass | Pre-check build status |
| No test project | Repository may lack tests | Graceful degradation with empty coverage |
| Platform issues | macOS ARM64 known issues | Snapshot fallback mechanism |
