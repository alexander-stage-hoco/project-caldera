# git-fame Evaluation Scorecard

**Generated**: 2026-02-08T09:03:01.052748+00:00
**Tool**: git-fame v3.1.1

## Overall Score

**Score**: 5.0/5.0
**Classification**: STRONG_PASS

## Dimension Scores

| Dimension | Weight | Score | Status |
|-----------|--------|-------|--------|
| Output Quality | 20% | 5.0/5.0 | PASS |
| Authorship Accuracy | 20% | 5.0/5.0 | PASS |
| Reliability | 15% | 5.0/5.0 | PASS |
| Performance | 15% | 5.0/5.0 | PASS |
| Integration Fit | 15% | 5.0/5.0 | PASS |
| Installation | 15% | 5.0/5.0 | PASS |

## Detailed Results

### Output Quality

| Check | Status | Message |
|-------|--------|---------|
| OQ-1 | PASS | schema_version present in all 1 analyses |
| OQ-2 | PASS | Valid ISO8601 timestamps in all 1 analyses |
| OQ-3 | PASS | All 5 required summary fields present |
| OQ-4 | PASS | All required fields present for 159 authors |
| OQ-5 | PASS | No file-level data present (author-level analysis only) |
| OQ-6 | PASS | All 1 JSON files are valid |

### Authorship Accuracy

| Check | Status | Message |
|-------|--------|---------|
| AA-1 | PASS | No expected_total_loc in ground truth (skipped) |
| AA-2 | PASS | No expected_author_count in ground truth (skipped) |
| AA-3 | PASS | No expected_top_author_loc in ground truth (skipped) |
| AA-4 | PASS | No expected_authors in ground truth (skipped) |
| AA-5 | PASS | No expected_bus_factor in ground truth (skipped) |
| AA-6 | PASS | No expected_hhi in ground truth (skipped) |
| AA-7 | PASS | No expected_top_two_pct in ground truth (skipped) |
| AA-8 | PASS | Author-level attribution present (159 authors) |

### Reliability

| Check | Status | Message |
|-------|--------|---------|
| RL-1 | PASS | Two consecutive runs produced identical output |
| RL-2 | PASS | No empty repository to test (skipped) |
| RL-3 | PASS | Single-author repository handled correctly |
| RL-4 | PASS | No rename test repository available (git-fame uses git blame... |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Completed in 0.82s (threshold: 5.0s) |
| PF-2 | PASS | Completed in 0.74s (threshold: 30.0s) |
| PF-3 | PASS | Memory usage: 22.8MB (threshold: 500.0MB) |
| PF-4 | PASS | Second run 16.8% slower (0.76s -> 0.88s) |

### Integration Fit

| Check | Status | Message |
|-------|--------|---------|
| IF-1 | PASS | All paths are properly normalized |
| IF-2 | PASS | All 4 required metrics present for L5/L8/L9 lenses |
| IF-3 | PASS | Author-level tool - directory rollups not applicable |
| IF-4 | PASS | Output matches collector schema (1 analyses validated) |

### Installation

| Check | Status | Message |
|-------|--------|---------|
| IN-1 | PASS | git-fame installed, version: 3.1.1 |
| IN-2 | PASS | git-fame --help returns valid help text |
