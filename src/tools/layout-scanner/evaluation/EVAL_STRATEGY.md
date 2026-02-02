# Evaluation Strategy: Layout Scanner

This document describes the evaluation methodology for the Layout Scanner (Tool 0).

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast |
| LLM Judges | 40% | Semantic understanding, reasoning quality |

This hybrid approach provides both precision and nuance.

---

## Scoring System

### Combined Score Calculation

```python
# Normalize programmatic score to 1-5 scale
programmatic_normalized = 1 + (programmatic_score * 4)  # 0-1 -> 1-5

# Weighted combination
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

### Decision Thresholds

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent, production-ready |
| PASS | >= 3.5 | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 | Acceptable with caveats |
| FAIL | < 3.0 | Significant issues |

---

## Dimension Summary

### Programmatic Dimensions (51 Checks)

| Dimension | Checks | Weight | Focus |
|-----------|--------|--------|-------|
| Output Quality | 8 | 25% | JSON validity, schema compliance |
| Accuracy | 8 | 25% | Counts, paths, sizes |
| Classification | 6 | 20% | Category assignments |
| Performance | 4 | 15% | Speed benchmarks |
| Edge Cases | 6 | 15% | Unicode, symlinks, nesting |
| Git Metadata | 6 | 0%* | Commit dates, authors |
| Content Metadata | 6 | 0%* | Line counts, hashes |
| SCC Comparison | 7 | 0%* | Cross-validation |

*Optional dimensions weighted separately when their passes are enabled.

### LLM Dimensions (4 Judges)

| Judge | Weight | Focus |
|-------|--------|-------|
| Classification Reasoning | 30% | Quality of classification explanations |
| Directory Taxonomy | 25% | Directory classifications match content |
| Hierarchy Consistency | 25% | Parent-child relationships coherent |
| Language Detection | 20% | Language identification accuracy |

---

## Programmatic Checks Catalog

### Output Quality Checks (OQ-1 to OQ-8)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| OQ-1 | JSON Valid | Critical | All required keys present |
| OQ-2 | Schema Compliant | Critical | Passes JSON schema validation |
| OQ-3 | Files Present | Critical | files object is non-empty dict |
| OQ-4 | Directories Present | Critical | directories object is non-empty dict |
| OQ-5 | Hierarchy Valid | High | hierarchy contains root_id, max_depth |
| OQ-6 | IDs Unique | Critical | No duplicate IDs across files/dirs |
| OQ-7 | IDs Format | High | IDs match expected format (f-*, d-*) |
| OQ-8 | Statistics Accurate | High | stats match computed values |

### Accuracy Checks (AC-1 to AC-8)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| AC-1 | File Count | Critical | Total files matches ground truth |
| AC-2 | Directory Count | Critical | Total directories matches ground truth |
| AC-3 | Path Normalization | High | Paths use forward slashes, no trailing |
| AC-4 | Size Accuracy | Medium | File sizes match filesystem |
| AC-5 | Depth Calculation | High | depth = path.count("/") |
| AC-6 | Parent Links | Critical | All parent_directory_id values valid |
| AC-7 | Child Lists | High | Children correctly associated with parents |
| AC-8 | Recursive Counts | High | recursive_file_count >= direct_file_count |

### Classification Checks (CL-1 to CL-6)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| CL-1 | Source Detection | High | src/ files classified as "source" |
| CL-2 | Test Detection | High | tests/ files classified as "test" |
| CL-3 | Vendor Detection | High | node_modules/ classified as "vendor" |
| CL-4 | Config Detection | Medium | .json, .yaml files classified as "config" |
| CL-5 | Docs Detection | Medium | docs/, README.md classified as "docs" |
| CL-6 | Confidence Scores | Medium | Confidence in valid range [0, 1] |

### Performance Checks (PF-1 to PF-4)

| ID | Name | Severity | Threshold |
|----|------|----------|-----------|
| PF-1 | Small Repo | High | < 1s for < 100 files |
| PF-2 | Medium Repo | Medium | < 5s for < 10K files |
| PF-3 | Large Repo | Medium | < 30s for < 100K files |
| PF-4 | Memory Usage | Low | < 500MB peak |

### Edge Case Checks (EC-1 to EC-6)

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| EC-1 | Unicode Paths | High | Unicode filenames handled correctly |
| EC-2 | Symlinks | Medium | Symlinks detected, not followed |
| EC-3 | Deep Nesting | High | 10+ levels of nesting handled |
| EC-4 | Empty Files | Low | 0-byte files included with size=0 |
| EC-5 | Hidden Files | Medium | .dotfiles included in output |
| EC-6 | Special Characters | Medium | Spaces, special chars in paths |

### Git Metadata Checks (GM-1 to GM-6) - Optional

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| GM-1 | Commit Dates | High | last_modified_commit present |
| GM-2 | Author Info | High | last_author present |
| GM-3 | Commit Count | Medium | commit_count > 0 |
| GM-4 | First Commit | Low | first_commit_date present |
| GM-5 | Age Calculation | Medium | age_days calculated correctly |
| GM-6 | Git Status | Low | is_tracked boolean present |

### Content Metadata Checks (CM-1 to CM-6) - Optional

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| CM-1 | Line Count | High | line_count present for text files |
| CM-2 | Content Hash | High | content_hash is valid SHA-256 |
| CM-3 | Encoding Detection | Medium | encoding field present |
| CM-4 | Binary Detection | High | is_binary correctly identified |
| CM-5 | Empty File Handling | Low | Empty files have line_count=0 |
| CM-6 | Large File Handling | Medium | Large files handled gracefully |

### SCC Comparison Checks (SC-1 to SC-7) - Cross-Validation

| ID | Name | Severity | Pass Criteria |
|----|------|----------|---------------|
| SC-1 | File Count Match | High | File count within 5% of scc |
| SC-2 | Language Coverage | High | All scc languages detected |
| SC-3 | Directory Match | Medium | Top directories match |
| SC-4 | Size Consistency | Medium | Total size within 10% |
| SC-5 | Classification Alignment | Medium | Source files align with scc |
| SC-6 | Path Consistency | Low | Paths normalize identically |
| SC-7 | Vendor Alignment | High | Vendor detection matches scc |

---

## LLM Judge Details

### Classification Reasoning Judge (30%)

**Sub-dimensions:**
- Classification Accuracy (40%): Files correctly categorized
- Reasoning Quality (30%): Explanations cite specific signals
- Confidence Calibration (30%): Scores match certainty

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | All classifications correct, reasons specific, confidence calibrated |
| 4 | 95%+ correct, reasons mostly specific, minor calibration issues |
| 3 | 85%+ correct, some generic reasons |
| 2 | 70%+ correct, many generic reasons |
| 1 | <70% correct, reasons missing |

### Directory Taxonomy Judge (25%)

**Sub-dimensions:**
- Classification Accuracy (40%): Directories match content
- Distribution Rollups (30%): Counts sum correctly
- Language Distribution (30%): Languages accurate

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | All directories correct, distributions accurate |
| 4 | 95%+ correct, minor distribution issues |
| 3 | 85%+ correct, some rollup problems |
| 2 | 70%+ correct, significant errors |
| 1 | <70% correct, distributions unreliable |

### Hierarchy Consistency Judge (25%)

**Sub-dimensions:**
- Parent-Child Relationships (35%): IDs valid
- Depth Calculations (25%): Depths correct
- Count Consistency (25%): Recursive >= direct
- Path Coherence (15%): Paths match hierarchy

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | All relationships valid, depths correct, counts consistent |
| 4 | 99%+ valid, minor discrepancies |
| 3 | 95%+ valid, some count issues |
| 2 | 90%+ valid, multiple problems |
| 1 | <90% valid, hierarchy broken |

### Language Detection Judge (20%)

**Sub-dimensions:**
- Extension Detection (40%): Common extensions correct
- Special Files (25%): Makefile, Dockerfile detected
- Edge Cases (20%): No-extension files handled
- Distribution Accuracy (15%): Counts consistent

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | All extensions correct, special files detected |
| 4 | 95%+ correct, minor ambiguity issues |
| 3 | 90%+ correct, some special files missed |
| 2 | 80%+ correct, significant gaps |
| 1 | <80% correct, detection unreliable |

---

## Ground Truth Methodology

### Source Data

Ground truth files in `evaluation/ground-truth/` define expected values for synthetic repositories:

| Repository | Purpose |
|------------|---------|
| small-clean | Basic source-only repo |
| mixed-types | Multiple classifications |
| deep-nesting | 10+ levels of nesting |
| vendor-heavy | node_modules, vendor |
| generated-code | .min.js, compiled files |
| edge-cases | Unicode, symlinks |
| mixed-language | Multiple programming languages |
| config-heavy | Configuration files |

### Ground Truth Format

```json
{
  "repository": "small-clean",
  "description": "Small clean repository with only source files",
  "expected": {
    "total_files": 6,
    "total_directories": 4,
    "max_depth": 3,
    "classifications": {
      "source": 5,
      "docs": 1
    },
    "specific_files": {
      "src/main.py": {
        "classification": "source",
        "language": "python"
      }
    }
  },
  "thresholds": {
    "classification_accuracy": 0.95,
    "count_tolerance": 0,
    "max_scan_time_seconds": 1.0
  }
}
```

---

## Evaluation Workflow

### Running Programmatic Evaluation

```bash
# Full evaluation
make evaluate

# Evaluate single output file
python -m scripts.evaluate --single output/runs/repo.json

# Filter by category
python -m scripts.evaluate --category classification

# JSON output
python -m scripts.evaluate --format json
```

### Running LLM Evaluation

```bash
# Full LLM evaluation (4 judges)
make llm-evaluate

# Focused evaluation (2 judges, faster)
python -m evaluation.llm.orchestrator --focused

# With specific model
python -m evaluation.llm.orchestrator --model opus-4.5

# Skip ground truth assertions
python -m evaluation.llm.orchestrator --no-assertions
```

### Running Combined Evaluation

```bash
# Run both programmatic and LLM evaluation
make evaluate-full
```

---

## Evaluation Output

### Programmatic Output

```json
{
  "repository": "small-clean",
  "timestamp": "2026-01-10T14:30:00Z",
  "overall_score": 4.80,
  "decision": "STRONG_PASS",
  "summary": {
    "total_checks": 51,
    "passed_checks": 49,
    "pass_rate": 96.1
  },
  "dimensions": [
    {
      "category": "output_quality",
      "passed_count": 8,
      "total_count": 8,
      "score": 5.0,
      "checks": [...]
    }
  ]
}
```

### LLM Output

```json
{
  "run_id": "llm-eval-20260110-143052",
  "timestamp": "2026-01-10T14:30:52Z",
  "model": "sonnet",
  "total_score": 4.20,
  "average_confidence": 0.85,
  "decision": "STRONG_PASS",
  "dimensions": [
    {
      "name": "classification_reasoning",
      "score": 4,
      "weight": 0.30,
      "weighted_score": 1.20,
      "confidence": 0.90,
      "reasoning": "...",
      "sub_scores": {
        "accuracy": 5,
        "reasoning_quality": 4,
        "confidence_calibration": 4
      }
    }
  ]
}
```

---

## Confidence Requirements

### LLM Judge Confidence

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review needed |

### Ground Truth Assertions

LLM judges run ground truth assertions before evaluation. If assertions fail, the judge score is capped at 2:

```python
if not gt_passed:
    result.score = min(result.score, 2)
```

---

## Evidence Collection

Each check collects evidence for transparency:

```python
evidence = {
    "expected": 6,
    "actual": 6,
    "paths_checked": ["src/main.py", "README.md"],
    "misclassified": []
}
```

### Evidence Types by Dimension

| Dimension | Evidence Collected |
|-----------|-------------------|
| Output Quality | Missing keys, schema errors |
| Accuracy | Expected vs actual counts |
| Classification | Misclassified files, confidence scores |
| Performance | Elapsed time, file count, memory |
| Edge Cases | Problem files, handling results |
| LLM Judges | Sampled files, distributions |

---

## Extending Evaluation

### Adding New Programmatic Checks

1. Add check function in appropriate `checks/` module
2. Register with `@register_check("XX-N")` decorator
3. Add to `run_*_checks()` function
4. Update ground truth if needed
5. Run `make evaluate` to verify

```python
@register_check("CL-7")
def check_new_classification(output: Dict, ground_truth: Dict) -> CheckResult:
    """CL-7: Check new classification logic."""
    # Implementation
    return CheckResult(
        check_id="CL-7",
        name="New Classification",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message="Check passed",
    )
```

### Adding New LLM Judges

1. Create judge class in `evaluation/llm/judges/`
2. Implement `dimension_name`, `weight`, `collect_evidence()`
3. Create prompt template in `evaluation/llm/prompts/`
4. Register in `orchestrator.py`
5. Run `make llm-evaluate` to verify

### Updating Thresholds

Thresholds are defined in:
- Check functions (performance thresholds)
- `checks/__init__.py` (scoring tables, decision thresholds)
- `orchestrator.py` (LLM decision thresholds)

---

## Appendix: Data Structures

### CheckResult

```python
@dataclass
class CheckResult:
    check_id: str         # e.g., "OQ-1"
    name: str             # Human-readable name
    category: CheckCategory
    passed: bool
    score: float          # 0.0 to 1.0
    message: str          # Result description
    evidence: Dict        # Supporting data
```

### JudgeResult

```python
@dataclass
class JudgeResult:
    dimension: str        # e.g., "classification_reasoning"
    score: int            # 1-5
    confidence: float     # 0.0-1.0
    reasoning: str        # Explanation
    sub_scores: Dict[str, int]
    evidence_cited: List[str]
    recommendations: List[str]
```

### DimensionResult

```python
@dataclass
class DimensionResult:
    category: CheckCategory
    checks: List[CheckResult]
    passed_count: int
    total_count: int
    score: float          # 1.0 to 5.0
```

---

## References

- [BLUEPRINT.md](../BLUEPRINT.md) - Architecture and decisions
- [README.md](../../README.md) - Quick start and usage
- [JSON Schema](../../schemas/layout.json) - Output schema
- [Ground Truth](../ground-truth/) - Expected values
