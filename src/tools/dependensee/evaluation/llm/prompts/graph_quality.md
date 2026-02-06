# Graph Quality Evaluation

## Task

Evaluate the quality and consistency of DependenSee's dependency graph output.

## Evidence

- Total nodes: {total_nodes}
- Total edges: {total_edges}
- Dangling references: {dangling_refs}

## Evaluation Criteria

Rate on a scale of 0.0-1.0:

1. **Completeness** (40%): Does the graph include all projects and packages?
   - 1.0: All projects as nodes, all packages as nodes
   - 0.5: Projects present but some packages missing
   - 0.0: Graph is incomplete

2. **Consistency** (40%): Are all edges valid?
   - 1.0: All edge sources and targets exist as nodes
   - 0.5: Some dangling references
   - 0.0: Many inconsistencies

3. **Structure** (20%): Is the graph properly typed?
   - 1.0: Node types (project/package) and edge types (project_reference/package_reference) correct
   - 0.5: Some type issues
   - 0.0: Types missing or wrong

## Output Format

Respond with:
```json
{
  "score": <0.0-1.0>,
  "verdict": "PASS" | "FAIL",
  "reasoning": "<explanation>"
}
```
