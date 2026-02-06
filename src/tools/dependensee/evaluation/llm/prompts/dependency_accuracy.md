# Dependency Accuracy Evaluation

## Task

Evaluate DependenSee's accuracy in detecting project and package dependencies.

## Context

**Evaluation Mode:** {{ evaluation_mode }}

{% if synthetic_baseline %}
**Synthetic Baseline Results:**
{{ synthetic_baseline }}

**Interpretation Guidance:**
{{ interpretation_guidance }}
{% endif %}

## Evidence

- Total projects: {total_projects}
- Project references found: {total_project_refs}
- Package references found: {total_package_refs}
- Packages with version info: {packages_with_version}

Sample packages:
{sample_packages}

## Evaluation Criteria

Rate on a scale of 0.0-1.0:

1. **Project References** (40%): Are project-to-project dependencies correct?
   - 1.0: All <ProjectReference> elements captured correctly
   - 0.5: Most references found
   - 0.0: Many references missing

2. **Package References** (40%): Are NuGet dependencies captured?
   - 1.0: All <PackageReference> elements with name and version
   - 0.5: Names found but versions missing
   - 0.0: Packages not detected

3. **Path Resolution** (20%): Are relative paths resolved correctly?
   - 1.0: All "../" paths resolved to absolute repo-relative paths
   - 0.5: Some resolution issues
   - 0.0: Paths left unresolved

## Output Format

Respond with:
```json
{
  "score": <0.0-1.0>,
  "verdict": "PASS" | "FAIL",
  "reasoning": "<explanation>"
}
```
