# Classification Reasoning Evaluation

You are evaluating the Layout Scanner's file classification reasoning quality.

## Evaluation Dimension: Classification Reasoning (Weight: 30%)

This dimension assesses how well the layout scanner classifies files and explains its reasoning.

### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Classification Accuracy | 40% | Are files correctly assigned to categories? |
| Reasoning Quality | 30% | Does classification_reason explain the "why"? |
| Confidence Calibration | 30% | Are confidence scores appropriately calibrated? |

---

## What to Evaluate

### 1. Classification Accuracy (40%)

**Expected Classifications:**
- `source`: Production code files (.py, .js, .ts, .cs, .java, .go, .rs)
- `test`: Test files (test_*.py, *.spec.ts, tests/, __tests__/)
- `config`: Configuration (.json, .yaml, .toml, pyproject.toml, Makefile)
- `docs`: Documentation (.md, docs/, README)
- `vendor`: Third-party (node_modules/, vendor/, third_party/)
- `generated`: Auto-generated (*.min.js, *.g.cs, dist/, build/)
- `ci`: CI/CD (.github/, .gitlab-ci.yml, Jenkinsfile)
- `other`: Unclassified

**Questions to Ask:**
- Are all test files in tests/ classified as "test"?
- Are README.md files classified as "docs"?
- Are node_modules/* files classified as "vendor"?
- Are edge case files (could be multiple categories) reasonably classified?

### 2. Reasoning Quality (30%)

**Good Reasons (specific, cite signals):**
- `"path:tests/"` - cites path signal
- `"filename:test_*.py"` - cites filename pattern
- `"extension:.md"` - cites extension
- `"majority source (85%)"` - for directories, explains aggregation

**Poor Reasons (generic, uninformative):**
- `"pattern match"` - too vague
- `"default"` - doesn't explain
- `"unknown"` - fallback without explanation

### 3. Confidence Calibration (30%)

**Expected Confidence Levels:**
- High (0.9-1.0): Unambiguous files (.py in src/, .md in docs/)
- Medium (0.6-0.8): Moderate certainty (config files in root)
- Low (0.3-0.5): Ambiguous files (could belong to multiple categories)

---

## Evidence

### Scanner Output Sample
{{ sample_files }}

### Ground Truth
{{ ground_truth }}

### Classification Distribution
{{ classification_distribution }}

---

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All classifications correct (>98%), reasons are specific and cite signals, confidence well-calibrated |
| 4 | 95%+ classifications correct, reasons mostly specific, minor confidence miscalibration |
| 3 | 85%+ classifications correct, some generic reasons, confidence mostly appropriate |
| 2 | 70-85% classifications correct, many generic reasons, confidence poorly calibrated |
| 1 | <70% correct, reasons missing or meaningless, confidence unreliable |

---

## Required Output

Analyze the evidence and return a JSON object with this exact structure:

```json
{
    "dimension": "classification_reasoning",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of your assessment>",
    "sub_scores": {
        "accuracy": <1-5>,
        "reasoning_quality": <1-5>,
        "confidence_calibration": <1-5>
    },
    "evidence_cited": [
        "<quote specific file classifications that support your score>",
        "<note any misclassifications found>"
    ],
    "recommendations": [
        "<specific improvements if score < 5>"
    ]
}
```

**Important:**
- Be specific in your reasoning - cite actual file paths and classifications
- If you find misclassifications, list them explicitly
- Consider edge cases (files that could reasonably be multiple categories)
- Evaluate confidence scores relative to classification certainty
