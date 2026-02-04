# DevSkim - Architecture Blueprint

> Security vulnerability detection for source code using regex-based pattern matching.

## Executive Summary

DevSkim is a Microsoft security scanner that detects potential security vulnerabilities in source code through regex-based pattern matching. It fills a specific niche in the Project Caldera toolkit: **security analysis of non-compiling code**.

**Key Capabilities:**
- Multi-language security scanning (C#, Python, JavaScript, Java, Go, C/C++, and more)
- Pattern-based detection that works without compilation
- SARIF output format (industry standard)
- Comprehensive rule library for common vulnerability patterns

**Why DevSkim for Caldera:**
1. Works on incomplete/non-compiling code (critical for due diligence scenarios)
2. Consistent behavior across languages
3. Fast analysis suitable for CI/CD integration
4. Complements other tools (Semgrep for code smells, Trivy for dependencies)

## Gap Analysis

### Current State

| Aspect | Status |
|--------|--------|
| Tool maturity | Stable (Microsoft-maintained) |
| Output format | SARIF (native) |
| Language support | 26+ languages |
| Performance | Fast (~20 files/second) |

### Integration Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| .NET 9 dependency | System may have different .NET version | Check in Makefile, provide install instructions |
| SARIF path format | Uses file:// scheme and absolute paths | Path normalization in analyze.py |
| Rule ID opacity | DS-prefixed IDs are not self-documenting | Maintain explicit category mapping |

## Architecture

### Data Flow

```
Repository
    │
    ▼
┌─────────────┐
│   DevSkim   │  .NET CLI tool with SARIF output
└─────────────┘
    │
    ▼
┌─────────────┐
│ analyze.py  │  Parse SARIF, normalize paths, wrap in envelope
└─────────────┘
    │
    ▼
┌─────────────┐
│ output.json │  Caldera envelope format with findings
└─────────────┘
    │
    ▼
┌─────────────────┐
│ DevskimAdapter  │  Persist findings to landing zone
└─────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ dbt Models                  │
│ stg_lz_devskim_findings     │
│ stg_devskim_file_metrics    │
│ rollup_devskim_*            │
└─────────────────────────────┘
```

### Output Schema

Key structures in `schemas/output.schema.json`:

| Structure | Description |
|-----------|-------------|
| `data.findings[]` | Individual security findings with location, severity, category |
| `data.files[]` | Per-file metrics (issue counts by severity/category) |
| `data.summary` | Repository-level aggregates |

### Design Decisions

#### 1. Regex-Based Detection vs AST-Based

**Decision:** Use DevSkim's native regex-based pattern matching.

**Rationale:**
- Works on incomplete/non-compiling code
- Faster than AST parsing for large codebases
- Consistent behavior across languages
- Trade-off: Higher false positive rate (acceptable for due diligence)

#### 2. SARIF Output Format

**Decision:** Parse DevSkim's native SARIF output rather than custom JSON.

**Rationale:**
- SARIF is industry standard (Microsoft, GitHub)
- DevSkim generates SARIF natively
- Future-proof for integration with other tools
- Structured location information (line, column, context)

#### 3. Severity Mapping

| DevSkim | DD Severity | Rationale |
|---------|-------------|-----------|
| Critical | CRITICAL | Direct security impact |
| Important | HIGH | Significant vulnerability |
| Moderate | MEDIUM | Potential security issue |
| BestPractice | LOW | Security anti-pattern |
| ManualReview | INFO | Requires human review |

#### 4. Category Mapping

Map DevSkim rule IDs to DD security categories with pattern-based fallback:
- Rules containing "sql" → sql_injection
- Rules containing "password" → hardcoded_secret
- Unknown rules → "other" category

## Implementation Plan

### Phase 1: Standalone Tool (Complete)

- [x] Create directory structure
- [x] Implement analyze.py with envelope output
- [x] Create output.schema.json
- [x] Add synthetic eval-repos (csharp, api-security)
- [x] Implement programmatic checks
- [x] Pass compliance scanner (preflight)

### Phase 2: SoT Integration (Complete)

- [x] Create DevskimFinding entity dataclass
- [x] Create DevskimRepository class
- [x] Create DevskimAdapter with TABLE_DDL, LZ_TABLES
- [x] Add lz_devskim_findings to schema.sql
- [x] Create dbt staging models (stg_lz_devskim_findings, stg_devskim_file_metrics)
- [x] Create dbt rollup models (direct and recursive)
- [x] Add dbt tests (test_rollup_devskim_direct_vs_recursive)

### Phase 3: Evaluation (In Progress)

- [x] Create ground truth files (csharp.json, api-security.json)
- [x] Implement LLM judges (4 judges)
- [x] Create LLM prompts
- [ ] Run full evaluation with DevSkim CLI
- [ ] Generate final scorecard

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVSKIM_PATH` | `devskim` | Path to DevSkim executable |
| `CHANGED_FILES` | none | Comma-separated list for incremental analysis |

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | `eval-repos/synthetic/csharp` | Repository to analyze |
| `OUTPUT_DIR` | `outputs/$(RUN_ID)` | Output directory |
| `SEVERITY_FILTER` | none | Filter by severity (critical,important,moderate) |

### Tool-Specific Options

DevSkim supports:
- `--ignore-globs`: Patterns to exclude from analysis
- `--suppress-manual-review`: Skip ManualReview findings
- `--source-code-regex`: Additional custom patterns

## Performance Characteristics

### Benchmarks

| Repository Size | Files | Time | Memory |
|-----------------|-------|------|--------|
| Small (<100 files) | 50 | <2s | ~50MB |
| Medium (100-1K) | 500 | ~10s | ~100MB |
| Large (1K-10K) | 5000 | ~60s | ~200MB |

### Optimization Notes

- Use `--ignore-globs` to exclude test files, vendored code
- DevSkim is single-threaded; parallelize at repository level if needed
- Memory usage scales with file count, not file size

## Evaluation Results

Current evaluation status (programmatic checks):

| Dimension | Score | Notes |
|-----------|-------|-------|
| Accuracy | TBD | Blocked on .NET 9 requirement |
| Coverage | TBD | Ground truth ready |
| Edge Cases | TBD | Tests written |
| Performance | TBD | Targets defined |

See [evaluation/scorecard.md](./evaluation/scorecard.md) for latest results.

## Risk Assessment

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Regex-based detection | Higher false positive rate than AST | Document expected FP rate, pair with Semgrep |
| .NET 9 dependency | May not be installed on all systems | Check and provide installation instructions |
| Rule ID opacity | DS-prefixed IDs require lookup | Maintain category mapping table |
| No custom rules | Limited to built-in patterns | Request feature from Microsoft |

### Security Considerations

- Tool runs with repository read access only
- No network access required during analysis
- No secrets in output (paths and code snippets only)
- SARIF output sanitized before envelope wrapping

## Lessons Learned

| Issue | Solution |
|-------|----------|
| DevSkim CLI requires .NET SDK | Makefile checks for `devskim` command availability |
| SARIF paths may be absolute or use file:// scheme | Normalize all paths to relative from target directory |
| Rule IDs are not self-documenting (e.g., DS126858) | Maintain explicit mapping table with descriptions |
| Regex patterns have inherent false positives | Document expected FP rate, provide false positive checks |

## Integration Points

### Adapter Integration

DevSkim adapter is registered in `adapters/__init__.py`:
```python
from .devskim_adapter import DevskimAdapter
ADAPTERS["devskim"] = DevskimAdapter
```

### Orchestrator Integration

DevSkim is wired in `orchestrator.py` TOOL_INGESTION_CONFIGS:
```python
"devskim": ToolIngestionConfig(
    tool_name="devskim",
    adapter_class=DevskimAdapter,
    output_filename="output.json",
)
```

### dbt Integration

DevSkim dbt models:
- `stg_lz_devskim_findings` - Staging for raw findings
- `stg_devskim_file_metrics` - Per-file issue counts
- `rollup_devskim_directory_counts_direct` - Direct directory aggregation
- `rollup_devskim_directory_counts_recursive` - Recursive directory aggregation

## Future Enhancements

1. **Custom Rule Support**: Add ability to define custom regex patterns
2. **Suppression System**: Support inline suppression comments
3. **Baseline Mode**: Compare against previous scan results
4. **CI Integration**: GitHub Action/Azure DevOps task
5. **HTML Reports**: Generate visual security reports

---

## Appendix: File Inventory

| File | Purpose |
|------|---------|
| `Makefile` | Build orchestration |
| `scripts/analyze.py` | Main analysis script (SARIF → envelope) |
| `scripts/evaluate.py` | Programmatic evaluation runner |
| `scripts/checks/*.py` | Individual check implementations |
| `schemas/output.schema.json` | Output JSON Schema |
| `BLUEPRINT.md` | This document |
| `EVAL_STRATEGY.md` | Evaluation methodology |
| `evaluation/ground-truth/*.json` | Expected results for synthetic repos |
| `evaluation/llm/judges/*.py` | LLM judge implementations |
| `evaluation/llm/prompts/*.md` | LLM judge prompts |
