# coverage-ingest Blueprint

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
