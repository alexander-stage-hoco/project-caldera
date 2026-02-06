# dependensee - Evaluation Strategy

> How we measure the quality and accuracy of .NET dependency analysis.

## Philosophy & Approach

DependenSee analyzes .NET solutions to extract project dependencies, NuGet package references, and detect circular dependencies. "Correct" output means:

1. **Complete Discovery**: All .csproj, .fsproj, and .vbproj files in the repository are found
2. **Accurate References**: Project-to-project references and NuGet packages are correctly identified with versions
3. **Valid Graph**: The dependency graph accurately represents the relationship between all projects and packages
4. **Cycle Detection**: Circular dependencies are correctly identified with full path information

### Evaluation Modes

| Mode | Description | Ground Truth |
|------|-------------|--------------|
| `synthetic` | Controlled repos with known structure | Full validation against expected values |
| `real_world` | Production repositories | Quality-focused (schema, consistency) |

For real-world repos, we validate output quality rather than counts, since we don't have ground truth for expected dependencies.

## Dimension Summary

| Dimension | Weight | Method | Target | Description |
|-----------|--------|--------|--------|-------------|
| Project Detection | 30% | Programmatic + LLM | 100% | All .NET projects discovered |
| Dependency Accuracy | 30% | Programmatic + LLM | 100% | References correctly captured |
| Graph Quality | 20% | Programmatic + LLM | No dangling refs | Graph structure is consistent |
| Circular Detection | 20% | Programmatic + LLM | Matches ground truth | Cycles correctly identified |

## Check Catalog

### Programmatic Checks

Located in `scripts/checks/`:

| Check Module | Dimension | Check Name | Description |
|--------------|-----------|------------|-------------|
| `accuracy.py` | Accuracy | `check_project_count_matches` | Project count matches ground truth |
| `accuracy.py` | Accuracy | `check_reference_count_matches` | Reference count matches ground truth |
| `accuracy.py` | Accuracy | `check_package_count_matches` | Package count matches ground truth |
| `accuracy.py` | Accuracy | `check_graph_node_count` | Graph nodes match expected |
| `accuracy.py` | Accuracy | `check_graph_edge_count` | Graph edges match expected |
| `coverage.py` | Coverage | `check_all_csproj_found` | All .csproj files detected |
| `coverage.py` | Coverage | `check_frameworks_detected` | Target frameworks identified |
| `output_quality.py` | Output | `check_schema_compliance` | Output matches JSON schema |
| `output_quality.py` | Output | `check_envelope_structure` | Standard envelope format |
| `output_quality.py` | Output | `check_paths_normalized` | No absolute paths or ".." |
| `performance.py` | Performance | `check_execution_time` | Under 30s threshold |
| `performance.py` | Performance | `check_memory_usage` | Under 512MB threshold |

### LLM Judges

Located in `evaluation/llm/judges/`:

| Judge | Dimension | Weight | Evaluates |
|-------|-----------|--------|-----------|
| `project_detection.py` | Project Detection | 30% | Completeness, path quality, framework detection |
| `dependency_accuracy.py` | Dependency Accuracy | 30% | Project refs, package refs, internal consistency |
| `graph_quality.py` | Graph Quality | 20% | Structural completeness, consistency, connectivity |
| `circular_detection.py` | Circular Detection | 20% | Detection accuracy, path completeness, consistency |

## Scoring Methodology

### LLM Judge Scoring (1-5 Scale)

Each judge evaluates sub-dimensions and produces an overall score:

| Score | Meaning | Typical Threshold |
|-------|---------|-------------------|
| 5 | Excellent | 100% correct, no issues |
| 4 | Good | >90% correct, minor issues |
| 3 | Acceptable | 70-90% correct, some issues |
| 2 | Poor | 50-70% correct, significant issues |
| 1 | Failing | <50% correct, major problems |

### Aggregate Score Calculation

```
llm_score = (
    project_detection_score * 0.30 +
    dependency_accuracy_score * 0.30 +
    graph_quality_score * 0.20 +
    circular_detection_score * 0.20
)

combined_score = (
    programmatic_score * 0.60 +
    llm_score * 0.40
)
```

### Per-Check Scoring (Programmatic)

| Status | Points | Description |
|--------|--------|-------------|
| PASS | 1.0 | Check passed completely |
| WARN | 0.5 | Partial success or minor issue |
| FAIL | 0.0 | Check failed |

## Decision Thresholds

### LLM Evaluation Decisions

| Decision | Score Range | Meaning |
|----------|-------------|---------|
| STRONG_PASS | >= 4.0 | Excellent quality, production ready |
| PASS | 3.5 - 3.99 | Good quality, acceptable for use |
| WEAK_PASS | 3.0 - 3.49 | Acceptable but needs improvement |
| FAIL | < 3.0 | Unacceptable quality |

### Ground Truth Assertion Penalty

If ground truth assertions fail:
- LLM score is capped at 2 (Poor) maximum
- This ensures hard failures override subjective LLM evaluation

## Ground Truth Specifications

### Synthetic Repositories

Located in `eval-repos/`:

| Scenario | Purpose | Projects | Cycles | Key Validations |
|----------|---------|----------|--------|-----------------|
| `synthetic` | Happy path | 4 | 0 | Basic detection, no cycles |
| `circular` | Cycle detection | 3 | 1 | A -> B -> C -> A cycle |
| `empty` | Edge case | 0 | 0 | Handle empty repos gracefully |
| `multi-framework` | Framework variety | 3 | 0 | net6.0, net7.0, net8.0 |
| `transitive` | Dependency chains | 4 | 0 | A -> B -> C -> D chains |

### Ground Truth Format

Each scenario has a corresponding `evaluation/ground-truth/<scenario>.json`:

```json
{
  "id": "synthetic",
  "description": "Ground truth for synthetic .NET solution test case",
  "repo_path": "eval-repos/synthetic",
  "expected": {
    "project_count": 4,
    "projects": [
      {
        "name": "MyApp",
        "path": "src/MyApp/MyApp.csproj",
        "target_framework": "net8.0",
        "project_references": ["src/MyApp.Core/MyApp.Core.csproj"],
        "package_references": [
          {"name": "Serilog", "version": "3.1.1"}
        ]
      }
    ],
    "package_count": 9,
    "reference_count": 6,
    "circular_dependency_count": 0,
    "graph_node_count": 13,
    "graph_edge_count": 15
  }
}
```

### Running Evaluations

```bash
# Run programmatic evaluation
cd src/tools/dependensee && make evaluate

# Run LLM evaluation
.venv/bin/python -m evaluation.llm.orchestrator --model sonnet

# Run focused LLM evaluation (2 judges)
.venv/bin/python -m evaluation.llm.orchestrator --model haiku --focused

# Check compliance
python src/tool-compliance/tool_compliance.py src/tools/dependensee
```

---

## Rollup Validation

Rollups:
- None (project-level tool)

Tests:
- src/tools/dependensee/tests/unit/test_analyze.py

Note: This is a project-level tool (not file-level) with no directory aggregations. It analyzes .NET solutions at the project level, producing project metadata and inter-project dependency graphs rather than file-by-file metrics.
