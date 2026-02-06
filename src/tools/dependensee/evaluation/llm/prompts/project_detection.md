# Project Detection Evaluation

You are an expert .NET architect evaluating DependenSee's ability to detect and analyze .NET projects.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Judge output quality: Are paths normalized? Are frameworks detected?
- Low project counts may be valid for small repositories
- Focus on accuracy of what IS detected, not raw counts

## Task

Evaluate the completeness and accuracy of project detection in the analysis output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Completeness (40%)
Are all .NET project files detected?
- **5**: All .csproj, .fsproj, .vbproj files found
- **4**: Most projects found (>90%)
- **3**: Majority found (70-90%)
- **2**: Some projects missing (50-70%)
- **1**: Many projects missing (<50%)

### 2. Path Quality (30%)
Are paths correctly normalized?
- **5**: All paths are repo-relative, no ".." or absolute paths
- **4**: Minor path issues (<5%)
- **3**: Some path issues (5-15%)
- **2**: Significant path issues (15-30%)
- **1**: Paths are mostly absolute or contain ".."

### 3. Framework Detection (30%)
Are target frameworks identified?
- **5**: All projects have target framework
- **4**: Most have framework (>90%)
- **3**: Majority have framework (70-90%)
- **2**: Some missing (50-70%)
- **1**: Framework missing from most (<50%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of your evaluation>",
  "evidence_cited": [
    "<specific evidence from the analysis output>",
    "<comparison with expected counts if ground truth available>"
  ],
  "recommendations": [
    "<suggestions for improving detection accuracy>",
    "<missing project types to consider>"
  ],
  "sub_scores": {
    "completeness": <1-5>,
    "path_quality": <1-5>,
    "framework_detection": <1-5>
  }
}
