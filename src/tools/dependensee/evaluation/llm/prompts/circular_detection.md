# Circular Dependency Detection Evaluation

You are an expert .NET architect evaluating DependenSee's ability to detect circular dependencies.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Zero cycles found is a VALID result for clean codebases
- Judge output quality: Is the detection consistent and well-formed?
- Focus on accuracy of what IS detected

## Task

Evaluate the accuracy and completeness of circular dependency detection.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Detection Accuracy (40%)
Are circular dependencies correctly identified?
- **5**: All cycles detected with no false positives
- **4**: Most cycles detected (>90%), minimal false positives
- **3**: Majority detected (70-90%), some false positives
- **2**: Some cycles missed (50-70%) or many false positives
- **1**: Many cycles missed (<50%) or unreliable results

### 2. Path Completeness (30%)
Are full cycle paths reported?
- **5**: All cycles include complete path (A -> B -> C -> A)
- **4**: Most paths complete (>90%)
- **3**: Majority complete (70-90%)
- **2**: Some paths incomplete (50-70%)
- **1**: Paths are missing or incomplete (<50%)

### 3. Internal Consistency (30%)
Is the data internally consistent?
- **5**: Summary counts match actual cycle counts exactly
- **4**: Minor discrepancies (<5%)
- **3**: Some discrepancies (5-15%)
- **2**: Significant discrepancies (15-30%)
- **1**: Major inconsistencies (>30%)

## Special Case: No Cycles

If no circular dependencies are found AND ground truth confirms zero cycles expected:
- Score 5 if output is well-formed and consistent
- This is a valid and correct result

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of your evaluation>",
  "evidence_cited": [
    "<specific evidence about cycle detection>",
    "<consistency between summary and actual counts>"
  ],
  "recommendations": [
    "<suggestions for improving cycle detection>",
    "<path reporting improvements>"
  ],
  "sub_scores": {
    "detection_accuracy": <1-5>,
    "path_completeness": <1-5>,
    "internal_consistency": <1-5>
  }
}
