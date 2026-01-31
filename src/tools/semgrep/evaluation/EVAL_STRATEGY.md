# Semgrep Evaluation Strategy

This document defines the evaluation methodology for the Semgrep code smell analysis tool.

## Overview

The Semgrep PoC detects code smells and security issues using Semgrep's rule-based static analysis. Evaluation focuses on:
1. Detection accuracy for known smells
2. Language and category coverage
3. False positive rate
4. Actionability of findings

## Decision Thresholds

| Decision | Score Threshold |
|----------|-----------------|
| STRONG_PASS | ≥ 4.0 |
| PASS | ≥ 3.5 |
| WEAK_PASS | ≥ 3.0 |
| FAIL | < 3.0 |

---

## Programmatic Checks

### Accuracy Checks (AC-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| AC-1 | Total smell count matches expected | 1.0 |
| AC-2 | Smell severity distribution correct | 1.0 |
| AC-3 | Smell category distribution correct | 1.0 |
| AC-4 | Line numbers present and valid | 1.0 |
| AC-5 | File paths normalized | 1.0 |
| AC-6 | Rule IDs present | 1.0 |
| AC-7 | Message quality (non-empty, descriptive) | 1.0 |
| AC-8 | Severity levels valid | 1.0 |

### Coverage Checks (CV-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| CV-1 | Python coverage | 1.0 |
| CV-2 | JavaScript coverage | 1.0 |
| CV-3 | TypeScript coverage | 1.0 |
| CV-4 | C# coverage | 1.0 |
| CV-5 | Java coverage | 1.0 |
| CV-6 | Go coverage | 1.0 |
| CV-7 | Rust coverage | 1.0 |
| CV-8 | DD category coverage | 1.0 |

### Edge Case Checks (EC-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| EC-1 | Empty files handled | 1.0 |
| EC-2 | Binary files skipped | 1.0 |
| EC-3 | Large files handled | 1.0 |
| EC-4 | Unicode files handled | 1.0 |
| EC-5 | Nested directories handled | 1.0 |
| EC-6 | Symlinks handled correctly | 1.0 |
| EC-7 | Git-ignored files skipped | 1.0 |
| EC-8 | No analysis crashes | 1.0 |

### Performance Checks (PF-*)

| Check ID | Description | Weight |
|----------|-------------|--------|
| PF-1 | Small repo analysis time | 1.0 |
| PF-2 | Medium repo analysis time | 1.0 |
| PF-3 | Large repo analysis time | 1.0 |
| PF-4 | Output size reasonable | 1.0 |

---

## LLM Judges

### Smell Accuracy Judge

| Property | Value |
|----------|-------|
| Dimension | smell_accuracy |
| Weight | 35% |
| Prompt File | prompts/smell_accuracy.md |

**Evaluation Criteria:**
- Correct smell type identification
- Accurate severity assignment
- Appropriate rule matching
- False negative rate

### Rule Coverage Judge

| Property | Value |
|----------|-------|
| Dimension | rule_coverage |
| Weight | 25% |
| Prompt File | prompts/rule_coverage.md |

**Evaluation Criteria:**
- Breadth of rules exercised
- Language support completeness
- Category diversity
- Missing detection gaps

### False Positive Rate Judge

| Property | Value |
|----------|-------|
| Dimension | false_positive_rate |
| Weight | 20% |
| Prompt File | prompts/false_positive_rate.md |

**Evaluation Criteria:**
- True positive ratio
- Pattern-specific accuracy
- Context-aware detection
- Noise reduction

### Actionability Judge

| Property | Value |
|----------|-------|
| Dimension | actionability |
| Weight | 20% |
| Prompt File | prompts/actionability.md |

**Evaluation Criteria:**
- Message clarity
- Fix suggestion quality
- Priority guidance
- Integration suitability

---

## Dimension Weights Summary

| Dimension | Weight | Source |
|-----------|--------|--------|
| Smell Accuracy | 35% | LLM |
| Rule Coverage | 25% | LLM |
| False Positive Rate | 20% | LLM |
| Actionability | 20% | LLM |

## Combined Scoring

The final score combines programmatic and LLM evaluations:

```
combined_score = (programmatic_score * 0.60) + (llm_score * 0.40)
```

---

## Test Scenarios

### Synthetic Repositories

| Scenario | Purpose | Languages |
|----------|---------|-----------|
| csharp-smells | C# code smell detection | C# |
| go-smells | Go code smell detection | Go |
| java-smells | Java code smell detection | Java |
| javascript-smells | JavaScript smell detection | JavaScript |
| python-smells | Python smell detection | Python |
| rust-smells | Rust smell detection | Rust |
| typescript-smells | TypeScript smell detection | TypeScript |

### Ground Truth Files

Located in `evaluation/ground-truth/`:
- `csharp-smells.json`
- `go-smells.json`
- `java-smells.json`
- `javascript-smells.json`
- `python-smells.json`
- `rust-smells.json`
- `typescript-smells.json`

---

## Running Evaluation

```bash
# Programmatic evaluation
make evaluate

# LLM evaluation
make evaluate-llm

# Combined evaluation
make evaluate-combined

# Quick evaluation (subset of checks)
make evaluate-quick
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial version |
