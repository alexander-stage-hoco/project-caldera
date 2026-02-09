# coverage-ingest Blueprint

## Executive Summary

coverage-ingest is a multi-format test coverage ingestion tool that normalizes coverage reports from LCOV, Cobertura, JaCoCo, and Istanbul formats into Caldera's unified landing zone. It enables cross-tool gap analysis by providing consistent file-level coverage metrics regardless of the original coverage tool or format.

## Purpose

Ingest test coverage reports from multiple formats (LCOV, Cobertura, JaCoCo, Istanbul) and normalize them into Caldera's landing zone for cross-tool gap analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Coverage Reports                           │
│  LCOV (.info)  │  Cobertura (.xml)  │  JaCoCo (.xml)  │        │
│                │                     │                 │ Istanbul│
└────────┬───────┴──────────┬─────────┴────────┬────────┴────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌────────────────────────────────────────────────────────────────┐
│                    Format Parsers                              │
│  LcovParser  │  CoberturaParser  │  JacocoParser  │ Istanbul  │
│              │                    │                │ Parser    │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    FileCoverage                                │
│  relative_path, line_coverage_pct, branch_coverage_pct,       │
│  lines_total, lines_covered, lines_missed,                    │
│  branches_total, branches_covered                             │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│               Envelope Output (output.json)                    │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    CoverageAdapter                             │
│  Validates paths, links to layout, persists to landing zone   │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│              lz_coverage_summary (DuckDB)                      │
└────────────────────────────────────────────────────────────────┘
```

## Implementation Plan

- [x] Phase 1: Core parser infrastructure
  - [x] Base parser interface
  - [x] LCOV parser implementation
  - [x] Cobertura parser implementation
  - [x] JaCoCo parser implementation
  - [x] Istanbul parser implementation
- [x] Phase 2: Output normalization
  - [x] FileCoverage dataclass
  - [x] Path normalization integration
  - [x] Envelope output generation
- [x] Phase 3: SoT Integration
  - [x] CoverageAdapter implementation
  - [x] CoverageSummary entity
  - [x] CoverageRepository
  - [x] dbt staging model
- [x] Phase 4: Evaluation infrastructure
  - [x] Ground truth files (all formats)
  - [x] Programmatic checks
  - [x] LLM judges

## Configuration

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Path to coverage report file | Required |
| `--format` | Override format detection | Auto-detect |
| `--output` | Output JSON path | `outputs/<run-id>/output.json` |
| `--repo-path` | Repository root for path normalization | Current directory |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COVERAGE_OUTPUT_DIR` | Default output directory | `outputs/` |
| `COVERAGE_STRICT_PATHS` | Fail on non-repo-relative paths | `false` |

## Format Details

### LCOV
- Line-oriented text format
- Records: `SF:` (source file), `LH:`/`LF:` (lines hit/found), `BRH:`/`BRF:` (branches)
- Ends with `end_of_record`

### Cobertura
- XML format from Java/Python tools
- Hierarchy: `coverage` → `packages` → `classes` → `lines`
- Attributes: `line-rate`, `branch-rate`

### JaCoCo
- XML format from Java coverage tools
- Uses instruction counters: `ci`/`mi` (covered/missed instructions)
- Branch counters: `cb`/`mb` (covered/missed branches)

### Istanbul
- JSON format from JavaScript/TypeScript tools
- Keys: `s` (statements), `b` (branches), `l` (lines)
- Maps line numbers to hit counts

## Key Design Decisions

1. **Unified Output Schema**: All formats produce the same `FileCoverage` structure
2. **Path Normalization**: Paths are normalized to repo-relative POSIX format
3. **Graceful Degradation**: Missing branch data is marked as `null`, not 0
4. **Format Detection**: Auto-detection based on file content signatures
5. **Safe XML Parsing**: Uses `defusedxml` to prevent XML attacks

## Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Small file (<100 entries) | < 100ms | ~20ms |
| Medium file (1K entries) | < 500ms | ~100ms |
| Large file (10K entries) | < 5s | ~800ms |
| Memory (10K files) | < 500MB | ~150MB |

## Evaluation

| Dimension | Weight | Method | Target |
|-----------|--------|--------|--------|
| Parser Accuracy | 35% | Programmatic | >= 99% |
| Normalization Correctness | 25% | Programmatic | 100% |
| Format Coverage | 20% | Programmatic | 100% |
| Edge Case Handling | 10% | Programmatic | >= 95% |
| Performance | 10% | Programmatic | < 5s for 10K |

## Risk

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Format version incompatibility | Medium | Medium | Version detection, graceful degradation |
| Path normalization edge cases | Low | High | Comprehensive test suite, common module |
| XML parsing vulnerabilities | Low | High | Use defusedxml exclusively |
| Memory exhaustion on large files | Low | Medium | Streaming parser consideration |

## Invariants

- `lines_covered <= lines_total`
- `branches_covered <= branches_total` (when present)
- `0 <= coverage_pct <= 100`
- `coverage_pct ≈ (covered / total) * 100` (within 0.01%)
- All paths are repo-relative POSIX format

## Dependencies

- `defusedxml`: Safe XML parsing
- `jsonschema`: Output validation
- `common.path_normalization`: Path utilities
