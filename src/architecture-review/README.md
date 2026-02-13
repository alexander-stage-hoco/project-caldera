# Architecture Reviewer

Reviews Project Caldera tool implementations for architectural conformance. Available in two modes:

1. **Programmatic (heuristic)** — deterministic, fast, testable (`reviewer.py`)
2. **LLM-powered (sub-agent)** — deeper analysis, advisory (`agent_prompt.md`)

## What It Reviews

| Dimension | Weight | What it checks |
|-----------|--------|---------------|
| D1: Entity & Persistence | 0.20 | Frozen dataclasses, `__post_init__` validation, adapter constants, schema.sql alignment, orchestrator registration |
| D2: Output Schema & Envelope | 0.20 | JSON Schema draft version, `const` for schema_version, 8 metadata fields, path normalization in analyze.py |
| D3: Code Conventions | 0.15 | `from __future__ import annotations`, PEP 604 unions, type hints, Makefile includes |
| D4: Evaluation Infrastructure | 0.15 | BaseJudge inheritance, 4+ judges, prompt `{{ evidence }}` placeholders, observability enforcement |
| D5: Cross-Tool Consistency | 0.15 | Envelope drift, naming formula adherence, adapter structure consistency |
| D6: BLUEPRINT Alignment | 0.15 | Required sections present, no template placeholders, evaluation data populated |

## Programmatic Reviewer (CLI)

```bash
# Review a single tool
python src/architecture-review/reviewer.py --target scc

# Cross-tool consistency check
python src/architecture-review/reviewer.py --target cross-tool --review-type cross_tool

# BLUEPRINT alignment only
python src/architecture-review/reviewer.py --target lizard --review-type blueprint_alignment

# Via Make
make arch-review ARCH_REVIEW_TARGET=scc
make arch-review ARCH_REVIEW_TARGET=cross-tool ARCH_REVIEW_TYPE=cross_tool
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--target` | (required) | Tool name or `cross-tool` |
| `--review-type` | `tool_implementation` | `tool_implementation`, `cross_tool`, or `blueprint_alignment` |
| `--output-dir` | `results/` | Output directory for JSON |
| `--project-root` | auto-detect | Project root path |

### Running Tests

```bash
pytest src/architecture-review/tests/ -v
```

## LLM-Powered Reviewer (Sub-Agent)

### Review a single tool

Ask Claude Code:

> Review the architecture of the lizard tool

This runs dimensions D1, D2, D3, D4, D6 and writes results to `src/architecture-review/results/lizard-<timestamp>.json`.

### Cross-tool consistency check

> Run a cross-tool architecture consistency check

This runs dimension D5 across all registered tools and writes results to `src/architecture-review/results/cross-tool-<timestamp>.json`.

### BLUEPRINT alignment only

> Check the BLUEPRINT alignment for the scc tool

This runs dimension D6 in depth and writes results.

## Review Types

| Type | Trigger phrase | Dimensions |
|------|---------------|------------|
| `tool_implementation` | "Review the architecture of [tool]" | D1, D2, D3, D4, D6 |
| `cross_tool` | "Cross-tool consistency check" | D5 |
| `blueprint_alignment` | "Check BLUEPRINT alignment for [tool]" | D6 |

## Output Format

Results are written as JSON to `src/architecture-review/results/`. See `schemas/review_result.schema.json` for the full schema.

Example summary:

```json
{
  "summary": {
    "total_findings": 5,
    "by_severity": { "error": 1, "warning": 3, "info": 1 },
    "overall_status": "WEAK_PASS",
    "overall_score": 3.2,
    "dimensions_reviewed": 5
  }
}
```

## Scoring

### Per-Dimension (1-5)

| Score | Criteria |
|-------|----------|
| 5 | 0 findings |
| 4 | 1-3 info, 0 warnings, 0 errors |
| 3 | 4+ info OR 1-3 warnings, 0 errors |
| 2 | 4+ warnings OR 1-2 errors |
| 1 | 3+ errors |

### Overall Status (advisory)

| Status | Score threshold |
|--------|----------------|
| STRONG_PASS | >= 4.0 |
| PASS | >= 3.5 |
| WEAK_PASS | >= 3.0 |
| NEEDS_WORK | < 3.0 |

## Relationship to Other Tools

```
Compliance Scanner (rule-based, ~51 checks, fast)
  Checks: file existence, Makefile targets, schema structure

Architecture Reviewer — Programmatic (heuristic, ~30 rules, deterministic)
  Checks: code patterns, cross-tool consistency, BLUEPRINT quality
  Run: python reviewer.py --target <tool>

Architecture Reviewer — LLM (sub-agent, ~30 rules, advisory)
  Checks: deeper code analysis, nuanced pattern matching
  Run: Ask Claude Code to "review the architecture of <tool>"

LLM Judges (per-tool, evaluates output quality)
  Checks: accuracy, actionability, false positives, integration fit
```

The architecture reviewer fills the gap between structural compliance (does the file exist?) and output quality evaluation (is the tool's output good?). It answers: does the code follow the project's patterns correctly? The programmatic mode runs deterministically without LLM costs; the LLM mode provides deeper analysis.

## Files

| File | Purpose |
|------|---------|
| `reviewer.py` | CLI entry point for programmatic reviews |
| `models.py` | Frozen dataclasses (Finding, DimensionResult, ReviewResult) |
| `discovery.py` | File discovery protocol (resolves tool paths from YAML config) |
| `scoring.py` | Scoring logic (findings → score → status) |
| `checks/d1_entity_persistence.py` | D1 dimension checks |
| `checks/d2_output_schema.py` | D2 dimension checks |
| `checks/d3_code_conventions.py` | D3 dimension checks |
| `checks/d4_evaluation_infra.py` | D4 dimension checks |
| `checks/d5_cross_tool.py` | D5 dimension checks |
| `checks/d6_blueprint.py` | D6 dimension checks |
| `agent_prompt.md` | Self-contained prompt for the LLM sub-agent |
| `schemas/review_result.schema.json` | JSON Schema for review output |
| `results/` | Persisted review results |
| `tests/` | Unit and integration tests (123 tests) |
