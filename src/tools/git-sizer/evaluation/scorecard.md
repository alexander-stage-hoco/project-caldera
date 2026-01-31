# git-sizer Evaluation Scorecard

## Summary

| Metric | Value |
|--------|-------|
| **Overall Score** | Pending evaluation |
| **Programmatic Checks** | 28 total |
| **LLM Judges** | 4 total |
| **Decision** | Pending |

## Programmatic Evaluation Results

### Size Accuracy Checks (AC-1 to AC-8)

| Check | Status | Notes |
|-------|--------|-------|
| AC-1 | - | Large blob detection |
| AC-2 | - | Total blob size accuracy |
| AC-3 | - | Commit count accuracy |
| AC-4 | - | Tree entries detection |
| AC-5 | - | Path depth detection |
| AC-6 | - | Health grade accuracy |
| AC-7 | - | LFS candidate identification |
| AC-8 | - | Threshold violation detection |

### Coverage Checks (CV-1 to CV-8)

| Check | Status | Notes |
|-------|--------|-------|
| CV-1 | - | Blob metrics coverage |
| CV-2 | - | Tree metrics coverage |
| CV-3 | - | Commit metrics coverage |
| CV-4 | - | Reference metrics coverage |
| CV-5 | - | Path metrics coverage |
| CV-6 | - | Expanded checkout metrics |
| CV-7 | - | Health grade coverage |
| CV-8 | - | Violation detail coverage |

### Edge Case Checks (EC-1 to EC-8)

| Check | Status | Notes |
|-------|--------|-------|
| EC-1 | - | Minimal repo handling |
| EC-2 | - | Large history handling |
| EC-3 | - | Wide tree handling |
| EC-4 | - | Deep path handling |
| EC-5 | - | No violations case |
| EC-6 | - | Multiple violations case |
| EC-7 | - | JSON output validity |
| EC-8 | - | Raw output preservation |

### Performance Checks (PF-1 to PF-4)

| Check | Status | Notes |
|-------|--------|-------|
| PF-1 | - | Total analysis speed |
| PF-2 | - | Per-repo analysis speed |
| PF-3 | - | Large repo handling |
| PF-4 | - | Output size efficiency |

## LLM Evaluation Results

| Judge | Weight | Score | Notes |
|-------|--------|-------|-------|
| Size Accuracy | 35% | - | Blob/tree/commit sizing |
| Threshold Quality | 25% | - | Violation detection |
| Actionability | 20% | - | Report usefulness |
| Integration Fit | 20% | - | Caldera compatibility |

## Decision Thresholds

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Production-ready |
| PASS | >= 3.5 | Good quality |
| WEAK_PASS | >= 3.0 | Acceptable |
| FAIL | < 3.0 | Significant issues |

---

*Run `make evaluate` and `make evaluate-llm` to populate this scorecard.*
