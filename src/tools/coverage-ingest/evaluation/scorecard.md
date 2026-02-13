# coverage-ingest Evaluation Scorecard

**Score:** 100.0%
**Decision:** STRONG_PASS
**Checks Passed:** 38/38

## Results by Category

### Parser Accuracy (35%)

| Check | Status | Notes |
|-------|--------|-------|

### Normalization Correctness (25%)

| Check | Status | Notes |
|-------|--------|-------|

### Format Coverage (20%)

| Check | Status | Notes |
|-------|--------|-------|

### Edge Case Handling (10%)

| Check | Status | Notes |
|-------|--------|-------|

### Performance (10%)

| Check | Status | Notes |
|-------|--------|-------|

## Check Details

| ID | Name | Status | Message |
|----|------|--------|--------|
| PA-1 | LCOV line counts | Pass | Basic LCOV parsing |
| PA-2 | LCOV branch counts | Pass | LCOV branch parsing |
| PA-3 | LCOV coverage percentage | Pass | Expected 70.0% |
| PA-4 | Cobertura line rates | Pass | Cobertura line parsing |
| PA-5 | Cobertura branch rates | Pass | branch_coverage_pct=None without counts |
| PA-6 | Cobertura coverage pct | Pass | Cobertura coverage |
| PA-7 | JaCoCo instruction counts | Pass | JaCoCo line counts |
| PA-8 | JaCoCo branch counts | Pass | JaCoCo branch counts |
| PA-9 | JaCoCo coverage pct | Pass | JaCoCo coverage |
| PA-10 | Istanbul statement counts | Pass | Istanbul statements |
| PA-11 | Istanbul branch counts | Pass | Istanbul branches |
| PA-12 | Istanbul coverage pct | Pass | Expected 66.67% |
| NC-1 | covered <= total invariant | Pass | Invariant check |
| NC-2 | branches covered <= total | Pass | Branch invariant |
| NC-3 | coverage pct 0-100 | Pass | Percentage range |
| NC-4 | pct matches calculation | Pass | Calculated percentage |
| NC-5 | paths repo-relative | Pass | No leading slash |
| NC-6 | no absolute paths | Pass | No drive letters |
| NC-7 | POSIX separators | Pass | Forward slashes |
| NC-8 | cross-format equivalence | Pass | Path format consistent |
| FC-1 | LCOV detection | Pass | LCOV detected |
| FC-2 | Cobertura detection | Pass | Cobertura detected |
| FC-3 | JaCoCo detection | Pass | JaCoCo detected |
| FC-4 | Istanbul detection | Pass | Istanbul detected |
| FC-5 | format override | Pass | Override works |
| FC-6 | invalid format rejected | Pass | LCOV handles non-LCOV |
| EC-1 | empty file handled | Pass | Empty returns [] |
| EC-2 | zero coverage handled | Pass | 0% coverage |
| EC-3 | 100% coverage handled | Pass | 100% coverage |
| EC-4 | unicode paths handled | Pass | Unicode in path |
| EC-5 | deep paths handled | Pass | Deep nesting |
| EC-6 | special chars handled | Pass | Spaces/parens |
| EC-7 | malformed XML rejected | Pass | ValueError raised |
| EC-8 | required fields validated | Pass | Valid FileCoverage |
| PF-1 | small file < 100ms | Pass | 0.3ms |
| PF-2 | medium file < 500ms | Pass | 2.5ms |
| PF-3 | large file < 5s | Pass | Skipped (quick mode) |
| PF-4 | memory < 500MB | Pass | Skipped (quick mode) |
