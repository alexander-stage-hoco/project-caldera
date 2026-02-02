# Size Accuracy Judge

You are evaluating the **size accuracy** of git-sizer's repository health analysis.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension
**Size Accuracy (35% weight)**: Are blob/tree/commit size measurements correct?

## Background
git-sizer analyzes Git repositories to measure:
- Blob sizes (file content sizes in Git object store)
- Tree entry counts (files per directory)
- Commit counts and history depth
- Path depths and lengths

Accurate measurements are critical for:
- Identifying LFS candidates (large blobs)
- Detecting monorepo anti-patterns (wide trees)
- Understanding repository complexity (deep history)

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):
| Score | Criteria |
|-------|----------|
| 5 | All measurements within 5% of expected values |
| 4 | Most measurements accurate, minor variations |
| 3 | Generally accurate, some significant variations |
| 2 | Several measurements significantly off |
| 1 | Measurements unreliable or missing |

### For Real-World Repos (when synthetic_baseline shows validated tool):
| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, measurements present and consistent |
| 4 | Minor schema issues but measurements are internally consistent |
| 3 | Schema issues OR questionable measurement consistency |
| 2 | Multiple schema issues AND inconsistent measurements |
| 1 | Broken output, missing required fields |

## Sub-Dimensions
1. **Blob Accuracy (40%)**: Blob sizes correctly measured
2. **Tree Accuracy (30%)**: Tree entry counts correct
3. **Commit Accuracy (30%)**: Commit counts and depth correct

## Evidence to Evaluate

### Repository Metrics
```json
{{ repo_metrics }}
```

### Accuracy Test Results
```json
{{ accuracy_results }}
```

### Summary
- Tests passed: {{ passed_tests }}/{{ total_tests }}
- Pass rate: {{ pass_rate }}%

### Expected Values
```json
{{ expected_values }}
```

## Evaluation Questions
1. Are blob sizes accurately measured for both small and large files?
2. Do tree entry counts reflect actual directory contents?
3. Are commit counts accurate for both shallow and deep histories?
4. Is path depth calculation correct for nested structures?

## Required Output Format
Respond with ONLY a JSON object (no markdown code fences, no explanation):
```json
{
  "dimension": "size_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of size accuracy assessment",
  "evidence_cited": ["specific measurements examined"],
  "recommendations": ["improvements for accuracy"],
  "sub_scores": {
    "blob_accuracy": <1-5>,
    "tree_accuracy": <1-5>,
    "commit_accuracy": <1-5>
  }
}
```
