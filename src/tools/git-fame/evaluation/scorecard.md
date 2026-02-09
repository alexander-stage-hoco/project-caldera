# git-fame Evaluation Scorecard

**Generated**: 2026-02-09T14:28:21.956183+00:00
**Tool**: git-fame v3.1.1

## Overall Score

**Score**: 3.69/5.0
**Classification**: MARGINAL_PASS

## Dimension Scores

| Dimension | Weight | Score | Status |
|-----------|--------|-------|--------|
| Output Quality | 20% | 5.0/5.0 | PASS |
| Authorship Accuracy | 20% | 5.0/5.0 | PASS |
| Reliability | 15% | 2.5/5.0 | FAIL |
| Performance | 15% | 3.75/5.0 | MARGINAL |
| Integration Fit | 15% | 5.0/5.0 | PASS |
| Installation | 15% | 0.0/5.0 | FAIL |

## Detailed Results

### Output Quality

| Check | Status | Message |
|-------|--------|---------|
| OQ-1 | PASS | schema_version present in all 1 analyses |
| OQ-2 | PASS | Valid ISO8601 timestamps in all 1 analyses |
| OQ-3 | PASS | All 5 required summary fields present |
| OQ-4 | PASS | All required fields present for 2 authors |
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
| AA-8 | PASS | Author-level attribution present (2 authors) |

### Reliability

| Check | Status | Message |
|-------|--------|---------|
| RL-1 | FAIL | Run 1 failed: /Users/alexander.stage/Projects/2026-01-24-Pro... |
| RL-2 | PASS | No empty repository to test (skipped) |
| RL-3 | FAIL | Single-author repo failed: /Users/alexander.stage/Projects/2... |
| RL-4 | PASS | No rename test repository available (git-fame uses git blame... |

### Performance

| Check | Status | Message |
|-------|--------|---------|
| PF-1 | PASS | Completed in 0.04s (threshold: 5.0s) |
| PF-2 | PASS | Completed in 0.03s (threshold: 30.0s) |
| PF-3 | FAIL | Execution failed: /Users/alexander.stage/Projects/2026-01-24... |
| PF-4 | PASS | Second run 17.7% faster (0.04s -> 0.03s) |

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
| IN-1 | FAIL | git-fame not properly installed: /Users/alexander.stage/Proj... |
| IN-2 | FAIL | git-fame --help failed with code 1: /Users/alexander.stage/P... |
