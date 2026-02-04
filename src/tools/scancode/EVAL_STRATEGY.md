# scancode Evaluation Strategy

This document describes the evaluation framework for ScanCode license and copyright detection.

## Philosophy & Approach

The evaluation framework assesses ScanCode's fitness for DD Platform integration across 6 dimensions.

### Key Principles

1. **License accuracy**: Correct SPDX identification
2. **Copyright detection**: Author and holder extraction
3. **Compliance focus**: Copyleft and risk detection
4. **Legal clarity**: Clear license expression output

---

## Dimension Summary

| Dimension | Code | Checks | Weight | Description |
|-----------|------|--------|--------|-------------|
| License Accuracy | LA | 8 | 35% | SPDX detection accuracy |
| Copyright Detection | CD | 6 | 20% | Copyright holder extraction |
| Compliance Analysis | CA | 4 | 15% | Copyleft/risk detection |
| Performance | PF | 4 | 10% | Execution speed |
| Integration Fit | IF | 4 | 15% | DD Platform compatibility |
| Output Quality | OQ | 2 | 5% | Schema compliance |
| **Total** | | **28** | **100%** | |

---

## Complete Check Catalog

### 1. License Accuracy (LA) - 35% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| LA-1 | MIT Detection | Correctly identifies MIT |
| LA-2 | Apache Detection | Correctly identifies Apache-2.0 |
| LA-3 | GPL Detection | Correctly identifies GPL variants |
| LA-4 | BSD Detection | Correctly identifies BSD variants |
| LA-5 | LGPL Detection | Correctly identifies LGPL |
| LA-6 | Proprietary Detection | Flags proprietary/unknown |
| LA-7 | SPDX Expression | Valid SPDX expression output |
| LA-8 | Confidence Score | Reports detection confidence |

### 2. Copyright Detection (CD) - 20% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| CD-1 | Author Extraction | Extracts copyright authors |
| CD-2 | Year Extraction | Extracts copyright years |
| CD-3 | Holder Extraction | Extracts copyright holders |
| CD-4 | Multiple Copyrights | Handles multiple per file |
| CD-5 | Company Names | Extracts company names |
| CD-6 | Email Detection | Extracts contact emails |

### 3. Compliance Analysis (CA) - 15% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| CA-1 | Copyleft Detection | Flags GPL/LGPL/AGPL |
| CA-2 | Commercial Risk | Flags proprietary deps |
| CA-3 | Attribution Required | Identifies attribution needs |
| CA-4 | License Compatibility | Reports compatibility issues |

### 4. Performance (PF) - 10% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| PF-1 | Small Repo | < 30 seconds for <100 files |
| PF-2 | Medium Repo | < 2 minutes for 100-500 files |
| PF-3 | Large Repo | < 10 minutes for 500+ files |
| PF-4 | Memory | < 2GB for standard repos |

### 5. Integration Fit (IF) - 15% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| IF-1 | Path Normalization | Paths match DD schema |
| IF-2 | Lens Mapping | Maps to L1/L6 lenses |
| IF-3 | SPDX Format | Standard SPDX output |
| IF-4 | Collector Schema | Output matches collector |

### 6. Output Quality (OQ) - 5% Weight

| Check ID | Name | Pass Criteria |
|----------|------|---------------|
| OQ-1 | JSON Validity | Valid JSON output |
| OQ-2 | Schema Version | Version present |

---

## Scoring Methodology

### Decision Thresholds

| Decision | Weighted Score |
|----------|----------------|
| STRONG_PASS | >= 4.0 |
| PASS | >= 3.5 |
| WEAK_PASS | >= 3.0 |
| FAIL | < 3.0 |

---

## Ground Truth Specifications

### Synthetic Test Repositories

| Repository | Licenses | Expected Detection |
|------------|----------|-------------------|
| mit-only | MIT | MIT (SPDX: MIT) |
| apache-2 | Apache-2.0 | Apache-2.0 |
| gpl-3 | GPL-3.0 | GPL-3.0 (copyleft) |
| mixed-licenses | MIT, Apache, GPL | All detected |
| proprietary | None | Unknown/Proprietary |

---

## Running Evaluation

```bash
# Setup
make setup

# Run analysis
make analyze REPO_PATH=/path/to/repo

# Run evaluation
make evaluate
```
