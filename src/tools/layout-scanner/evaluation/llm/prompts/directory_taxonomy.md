# Directory Taxonomy Evaluation

You are evaluating the Layout Scanner's directory classification and taxonomy accuracy.

## Evaluation Dimension: Directory Taxonomy (Weight: 25%)

This dimension assesses how well directories are classified based on their content and structure.

### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Classification Accuracy | 40% | Do directory classifications match content? |
| Distribution Rollups | 30% | Are classification_distribution counts accurate? |
| Language Distribution | 30% | Are language counts accurate? |

---

## What to Evaluate

### 1. Directory Classification Accuracy (40%)

**Expected Directory Classifications:**
| Directory | Expected Classification |
|-----------|------------------------|
| `src/`, `lib/` | source |
| `tests/`, `test/`, `__tests__/` | test |
| `docs/`, `documentation/` | docs |
| `node_modules/`, `vendor/` | vendor |
| `.github/`, `.gitlab/` | ci |
| `build/`, `dist/`, `out/` | generated |

**Questions to Ask:**
- Does the root `src/` directory have classification "source"?
- Does `tests/` have classification "test"?
- Are mixed directories (source + test) classified by majority?

### 2. Distribution Rollups (30%)

**Verification Points:**
- `classification_distribution` should sum to `recursive_file_count`
- Nested directory counts should roll up correctly
- Empty directories should have all zeros

**Example:**
```json
{
  "path": "src",
  "recursive_file_count": 100,
  "classification_distribution": {
    "source": 85,
    "config": 10,
    "docs": 5
  }
}
// 85 + 10 + 5 = 100 ✓
```

### 3. Language Distribution (30%)

**Verification Points:**
- Languages in `language_distribution` should match file extensions
- Counts should be consistent across directories
- Multi-language directories should show all languages

---

## Evidence

{{ evidence }}

### Directory Sample
{{ sample_directories }}

### Repository Structure Overview
{{ structure_overview }}

### Ground Truth
{{ ground_truth }}

---

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All directories correctly classified, distributions sum correctly, languages accurate |
| 4 | 95%+ directories correct, minor distribution discrepancies (<2 files off) |
| 3 | 85%+ directories correct, some rollup issues, languages mostly accurate |
| 2 | 70-85% directories correct, significant distribution errors |
| 1 | <70% correct, distributions unreliable, language detection broken |

---

## Required Output

Analyze the evidence and return a JSON object with this exact structure:

```json
{
    "dimension": "directory_taxonomy",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of your assessment>",
    "sub_scores": {
        "classification_accuracy": <1-5>,
        "distribution_rollups": <1-5>,
        "language_distribution": <1-5>
    },
    "evidence_cited": [
        "<quote specific directory classifications>",
        "<note any distribution inconsistencies>"
    ],
    "recommendations": [
        "<specific improvements if score < 5>"
    ]
}
```

**Important:**
- Verify distribution sums match recursive counts
- Check that directory classifications match their dominant content
- Note any anomalies in language detection at directory level
