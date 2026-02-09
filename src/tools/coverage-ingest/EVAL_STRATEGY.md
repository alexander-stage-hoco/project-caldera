# coverage-ingest Evaluation Strategy

## Overview

Coverage data is purely numeric and deterministic. Unlike tools that produce findings requiring subjective assessment, coverage metrics can be verified exactly against expected values. Programmatic checks provide 100% coverage of quality dimensions.

## Evaluation Dimensions (5 Total)

| Dimension | Weight | Target | Method |
|-----------|--------|--------|--------|
| Parser Accuracy | 35% | >= 99% metric match | Programmatic |
| Normalization Correctness | 25% | 100% invariant compliance | Programmatic |
| Format Coverage | 20% | 100% format support | Programmatic |
| Edge Case Handling | 10% | >= 95% graceful handling | Programmatic |
| Performance | 10% | < 5s for 10K files | Programmatic |

## Check Catalog (34 Checks)

### Parser Accuracy (PA-1 to PA-12)
- PA-1: LCOV line counts match expected
- PA-2: LCOV branch counts match expected
- PA-3: LCOV coverage percentages accurate (±0.01%)
- PA-4: Cobertura line rates match expected
- PA-5: Cobertura branch rates match expected
- PA-6: Cobertura coverage percentages accurate
- PA-7: JaCoCo instruction counts match expected
- PA-8: JaCoCo branch counts match expected
- PA-9: JaCoCo coverage percentages accurate
- PA-10: Istanbul statement counts match expected
- PA-11: Istanbul branch counts match expected
- PA-12: Istanbul coverage percentages accurate

### Normalization Correctness (NC-1 to NC-8)
- NC-1: covered_lines <= total_lines invariant
- NC-2: branches_covered <= branches_total invariant
- NC-3: 0 <= coverage_pct <= 100 invariant
- NC-4: coverage_pct matches (covered/total)*100
- NC-5: All paths are repo-relative
- NC-6: No absolute paths in output
- NC-7: POSIX separators only
- NC-8: Cross-format equivalence (same source = same output)

### Format Coverage (FC-1 to FC-6)
- FC-1: LCOV format detected correctly
- FC-2: Cobertura format detected correctly
- FC-3: JaCoCo format detected correctly
- FC-4: Istanbul format detected correctly
- FC-5: Format override works correctly
- FC-6: Invalid format rejected gracefully

### Edge Cases (EC-1 to EC-8)
- EC-1: Empty coverage file handled
- EC-2: Zero coverage file handled
- EC-3: 100% coverage file handled
- EC-4: Unicode paths handled
- EC-5: Deep nested paths handled
- EC-6: Special characters in paths handled
- EC-7: Malformed XML/JSON rejected gracefully
- EC-8: Missing required fields handled

### Performance (PF-1 to PF-4)
- PF-1: Small file (<100 entries) < 100ms
- PF-2: Medium file (1K entries) < 500ms
- PF-3: Large file (10K entries) < 5s
- PF-4: Memory usage < 500MB for large files

## Ground Truth Structure

```
evaluation/
├── ground-truth/
│   ├── lcov/
│   │   ├── simple.json          # Basic single-file coverage
│   │   ├── multi-file.json      # Multiple files
│   │   ├── branches.json        # Branch coverage data
│   │   └── edge-cases.json      # Edge case scenarios
│   ├── cobertura/
│   │   ├── simple.json
│   │   ├── multi-package.json
│   │   ├── branches.json
│   │   └── edge-cases.json
│   ├── jacoco/
│   │   ├── simple.json
│   │   ├── multi-module.json
│   │   ├── counters.json
│   │   └── edge-cases.json
│   ├── istanbul/
│   │   ├── simple.json
│   │   ├── multi-file.json
│   │   ├── branches.json
│   │   └── edge-cases.json
│   └── cross-format/
│       └── equivalence.json     # Same source, different formats
└── synthetic/
    ├── lcov/                    # Test .info/.lcov files
    ├── cobertura/               # Test .xml files
    ├── jacoco/                  # Test .xml files
    └── istanbul/                # Test .json files
```

## Decision Thresholds

| Decision | Score | Interpretation |
|----------|-------|----------------|
| STRONG_PASS | >= 95 | Production-ready |
| PASS | >= 85 | Ready with minor issues |
| WEAK_PASS | >= 75 | Usable with limitations |
| FAIL | < 75 | Accuracy or normalization issues |
