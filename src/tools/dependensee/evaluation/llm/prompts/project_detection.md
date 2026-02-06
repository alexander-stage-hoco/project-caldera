# Project Detection Evaluation

## Task

Evaluate DependenSee's ability to detect and analyze .NET projects.

## Evidence

- Total projects detected: {total_projects}
- Projects with target framework: {projects_with_framework}
- Path quality metrics: {path_quality}

Sample projects:
{sample_projects}

## Evaluation Criteria

Rate on a scale of 0.0-1.0:

1. **Completeness** (40%): Are all .NET project files detected?
   - 1.0: All .csproj, .fsproj, .vbproj files found
   - 0.5: Most projects found
   - 0.0: Many projects missing

2. **Path Quality** (30%): Are paths correctly normalized?
   - 1.0: All paths are repo-relative, no ".." or absolute paths
   - 0.5: Some path issues
   - 0.0: Paths are absolute or contain ".."

3. **Framework Detection** (30%): Are target frameworks identified?
   - 1.0: All projects have target framework
   - 0.5: Most have framework
   - 0.0: Framework missing from most

## Output Format

Respond with:
```json
{
  "score": <0.0-1.0>,
  "verdict": "PASS" | "FAIL",
  "reasoning": "<explanation>"
}
```
