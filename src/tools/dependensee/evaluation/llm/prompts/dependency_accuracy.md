# Dependency Accuracy Evaluation

You are an expert .NET architect evaluating DependenSee's accuracy in detecting project and package dependencies.

## Evaluation Context

{{ interpretation_guidance }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Judge output quality: Are references captured with correct paths and versions?
- Low dependency counts may be valid for simple projects
- Focus on accuracy of what IS detected, not raw counts

## Task

Evaluate the accuracy and completeness of dependency detection in the analysis output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Project Reference Accuracy (40%)
Are project references correctly identified?
- **5**: All project references captured with correct paths
- **4**: Most references correct (>90%)
- **3**: Majority correct (70-90%)
- **2**: Some issues (50-70%)
- **1**: Many references missing or incorrect (<50%)

### 2. Package Reference Accuracy (35%)
Are NuGet packages correctly identified?
- **5**: All packages with correct names and versions
- **4**: Most packages correct (>90%)
- **3**: Majority correct (70-90%)
- **2**: Some packages missing versions (50-70%)
- **1**: Many packages missing or incorrect (<50%)

### 3. Internal Consistency (25%)
Is the dependency data internally consistent?
- **5**: No orphan references, all targets exist
- **4**: Minor inconsistencies (<5%)
- **3**: Some inconsistencies (5-15%)
- **2**: Significant inconsistencies (15-30%)
- **1**: Major data integrity issues (>30%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of your evaluation>",
  "evidence_cited": [
    "<specific evidence from package/project references>",
    "<comparison with expected counts if ground truth available>"
  ],
  "recommendations": [
    "<suggestions for improving dependency detection>",
    "<version handling improvements>"
  ],
  "sub_scores": {
    "project_ref_accuracy": <1-5>,
    "package_ref_accuracy": <1-5>,
    "internal_consistency": <1-5>
  }
}
