# Language Detection Evaluation

You are evaluating the Layout Scanner's programming language detection accuracy.

## Evaluation Dimension: Language Detection (Weight: 20%)

This dimension assesses how accurately the scanner identifies programming languages for files.

### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Extension Detection | 40% | Are common extensions correctly mapped? |
| Special Files | 25% | Are Makefile, Dockerfile, etc. detected? |
| Edge Cases | 20% | Are files without extensions handled? |
| Distribution Accuracy | 15% | Are language counts consistent? |

---

## What to Evaluate

### 1. Extension-Based Detection (40%)

**Expected Mappings:**
| Extension | Language |
|-----------|----------|
| `.py` | python |
| `.js` | javascript |
| `.ts` | typescript |
| `.tsx` | typescript |
| `.jsx` | javascript |
| `.java` | java |
| `.cs` | csharp |
| `.go` | go |
| `.rs` | rust |
| `.rb` | ruby |
| `.php` | php |
| `.swift` | swift |
| `.kt` | kotlin |
| `.md` | markdown |
| `.json` | json |
| `.yaml`, `.yml` | yaml |
| `.html` | html |
| `.css` | css |
| `.scss` | scss |
| `.sql` | sql |

**Normalization:**
- Languages should be lowercase
- No trailing/leading whitespace
- Consistent naming (e.g., "javascript" not "JavaScript" or "JS")

### 2. Special File Detection (25%)

**Expected Detections:**
| Filename | Language |
|----------|----------|
| `Makefile` | makefile |
| `Dockerfile` | dockerfile |
| `Jenkinsfile` | groovy |
| `.gitignore` | gitignore |
| `.editorconfig` | editorconfig |
| `package.json` | json |

**Shebang Detection:**
- `#!/usr/bin/env python` -> python
- `#!/bin/bash` -> shell
- `#!/usr/bin/env node` -> javascript

### 3. Edge Cases (20%)

**Files Without Extensions:**
- Should attempt detection via shebang or filename
- May be "unknown" if no signals

**Binary Files:**
- Should NOT have language assigned (or "binary")
- Images, executables, archives

**Vendor Files:**
- Should still have languages detected
- node_modules/*.js should be "javascript"

### 4. Language Distribution (15%)

**Consistency Checks:**
- `language_distribution` in directories should match file counts
- Total language counts should sum correctly
- No duplicate counting

---

## Evidence

{{ evidence }}

### File Language Samples
{{ language_samples }}

### Language Statistics
{{ language_statistics }}

### Ground Truth
{{ ground_truth }}

---

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All common extensions correct (>98%), special files detected, edge cases handled gracefully |
| 4 | 95%+ correct, minor issues with ambiguous extensions (.h) |
| 3 | 90%+ correct, some special files missed, basic edge case handling |
| 2 | 80-90% correct, significant detection gaps |
| 1 | <80% correct, language detection unreliable |

---

## Required Output

Analyze the evidence and return a JSON object with this exact structure:

```json
{
    "dimension": "language_detection",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of your assessment>",
    "sub_scores": {
        "extension_detection": <1-5>,
        "special_files": <1-5>,
        "edge_cases": <1-5>,
        "distribution_accuracy": <1-5>
    },
    "evidence_cited": [
        "<quote specific language detections>",
        "<note any misdetections>"
    ],
    "recommendations": [
        "<specific improvements if score < 5>"
    ]
}
```

**Important:**
- Verify common extensions map correctly
- Check special files (Makefile, Dockerfile) are detected
- Note any files with "unknown" language that should be known
- Verify language names are normalized (lowercase, consistent)
