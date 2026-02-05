# dotcover - Architecture Blueprint

> Brief description of what this tool analyzes.

<!--
Template instructions (delete this section when done):
- Review docs/templates/BLUEPRINT.md.template for full guidance
- See src/tools/scc/BLUEPRINT.md for a complete example
- Run `make compliance` to verify all required sections are present
-->

## Executive Summary

[TODO: Describe what the tool analyzes, key metrics, and why it was selected for Caldera]

**Example** (from scc):
> scc provides fast, accurate source code counting with per-file metrics including
> lines of code, comments, blanks, and cyclomatic complexity estimates.

## Gap Analysis

### Current State

| Aspect | Status |
|--------|--------|
| Tool maturity | [alpha/beta/stable] |
| Output format | JSON |
| Language support | [All/Specific languages] |
| Performance | [Fast/Moderate/Slow] |

### Integration Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| [TODO: Identify gaps] | [Impact level] | [Resolution plan] |

## Architecture

### Data Flow

```
Repository
    |
    v
+-------------+
| analyze.py  |  Parse, normalize, wrap in envelope
+-------------+
    |
    v
+-------------+
| output.json |  Caldera envelope format
+-------------+
    |
    v
+-------------+
| SoT Adapter |  Persist to landing zone
+-------------+
```

### Output Schema

See `schemas/output.schema.json` for complete schema.

Key data structures:
- `files[]`: Per-file metrics (path, [TODO: your metrics])
- `summary`: Aggregate statistics

## Implementation Plan

### Phase 1: Standalone Tool

- [x] Create directory structure (done by create-tool.py)
- [ ] Implement analyze.py with envelope output
- [ ] Customize output.schema.json for tool metrics
- [ ] Add test files to eval-repos/synthetic/
- [ ] Implement programmatic checks in scripts/checks/
- [ ] Pass compliance scanner: `make compliance`

### Phase 2: SoT Integration

- [ ] Create entity dataclass in persistence/entities.py
- [ ] Create repository class in persistence/repositories.py
- [ ] Create adapter in persistence/adapters/
- [ ] Add dbt staging models

### Phase 3: Evaluation

- [ ] Create ground truth in evaluation/ground-truth/
- [ ] Implement LLM judges in evaluation/llm/judges/
- [ ] Generate and review scorecard

## Configuration Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| REPO_PATH | `eval-repos/synthetic` | Repository to analyze |
| OUTPUT_DIR | `outputs/$(RUN_ID)` | Output directory |
| [TODO: Add tool-specific variables] | | |

## Performance Characteristics

[TODO: Add benchmarks after implementation]

Target performance:
- 10K files: < 60 seconds
- 100K files: < 10 minutes

## Evaluation Results

See [evaluation/scorecard.md](./evaluation/scorecard.md) for results.

## Risk Assessment

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| [TODO: Document limitations] | [Impact] | [Mitigation] |
