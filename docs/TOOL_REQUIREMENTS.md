# Tool Requirements & Readiness Gates (Caldera)

This document defines the requirements and readiness gates for tools in Project Caldera. Every tool in `src/tools/` MUST comply with these specifications.

---

## Requirement Tiers

Caldera tools target **Production tier** by default.

| Requirement | Production |
|-------------|:----------:|
| Makefile (6 targets) | Required |
| README.md | Required |
| BLUEPRINT.md | Required |
| EVAL_STRATEGY.md | Required |
| Unit + Integration tests | Required |
| Output schema validation | Required |
| LLM evaluation assets | Required |
| SoT adapter | Required |
| dbt models | Required |

---

## Production Gates

Each gate must have evidence (file path or test) and is enforced for production readiness.

### Gate A: Structure and Orchestration

Evidence:
- `src/tools/<tool>/Makefile`
- `src/tools/<tool>/README.md`
- `src/tools/<tool>/BLUEPRINT.md`
- `src/tools/<tool>/EVAL_STRATEGY.md`
- `src/tools/<tool>/requirements.txt`
- `src/tools/<tool>/scripts/analyze.py`
- `src/tools/<tool>/scripts/evaluate.py`
- `src/tools/<tool>/scripts/checks/`
- `src/tools/<tool>/schemas/output.schema.json`
- `src/tools/<tool>/eval-repos/synthetic/`
- `src/tools/<tool>/eval-repos/real/`
- `src/tools/<tool>/evaluation/ground-truth/`
- `src/tools/<tool>/evaluation/llm/orchestrator.py`
- `src/tools/<tool>/evaluation/llm/judges/`
- `src/tools/<tool>/evaluation/llm/prompts/`
- `src/tools/<tool>/evaluation/scorecard.md`
- `src/tools/<tool>/tests/unit/`
- `src/tools/<tool>/tests/integration/`

Notes:
- Standard Make targets are required; see [Makefile Requirements](#makefile-requirements).
- Output contract is `outputs/<run-id>/output.json` for analysis runs.
- Evaluation outputs are written to `evaluation/results/` and overwrite the previous run.

### Gate B: Output Schema and Validation

Evidence:
- `src/tools/<tool>/schemas/output.schema.json`
- Schema validation tests in tool test suites.

Rules:
- Paths are repo-relative with `/` separators.
- No absolute paths, no `..` segments, no leading `./`.
- Tools MUST NOT emit layout file IDs; the SoT engine resolves file IDs during persistence.
- Schema draft is `https://json-schema.org/draft/2020-12/schema`.
- `metadata.commit` MUST be a 40-hex SHA; when no git metadata is available, tools compute a deterministic content hash for the repo.
- `metadata.schema_version` MUST use `const` (not pattern) in the schema for version alignment validation.

### Gate C: Evaluation Coverage

Evidence:
- `src/tools/<tool>/evaluation/ground-truth/*.json`
- `src/tools/<tool>/evaluation/llm/prompts/*.md`
- `src/tools/<tool>/evaluation/scorecard.md`

Rules:
- Evaluation dimensions match the tool's EVAL_STRATEGY.
- Programmatic checks include precision/recall where feasible (synthetic repos).
- LLM judges are supplemental on real repos and MUST propose concrete improvements on synthetic repos.
- If rollups are declared, EVAL_STRATEGY.md MUST include a `Rollup Validation` section with `Rollups:` and `Tests:` lists.

### Gate D: Testing

Evidence:
- `src/tools/<tool>/tests/unit/`
- `src/tools/<tool>/tests/integration/`
- Tool `make test` succeeds.

Rules:
- Unit tests validate schema adherence and core parsing.
- Integration tests validate end-to-end output generation.
- Test files follow `test_*.py` naming convention.

### Gate E: Rollup Correctness (dbt)

Evidence:
- `src/sot-engine/dbt/models/staging/stg_<tool>_*.sql`
- `src/sot-engine/dbt/models/marts/rollup_<tool>_directory_*.sql`
- `src/sot-engine/dbt/tests/test_rollup_<tool>_*.sql`

Rules:
- Direct rollups include only files directly in a directory.
- Recursive rollups include all descendant files.
- dbt tests assert:
  - distribution values are in valid ranges
  - distribution metrics include counts, quantiles, shape, and concentration metrics
  - recursive `value_count >= direct` for identical run/directory/metric
  - recursive `min_value <= direct min_value` and `max_value >= direct max_value`
- If `Rollup Validation` is absent in EVAL_STRATEGY.md, rollups are treated as not declared.

### Gate F: SoT Adapter

Evidence:
- `src/sot-engine/persistence/adapters/<tool>_adapter.py`
- `src/sot-engine/persistence/entities.py` (tool entities)
- `src/sot-engine/persistence/repositories.py` (tool repository)

Rules:
- Adapter exposes: `SCHEMA_PATH`, `LZ_TABLES`, `QUALITY_RULES`, `TABLE_DDL`
- Adapter class has: `validate_schema`, `validate_lz_schema`, `validate_quality`, `ensure_lz_tables`
- `TABLE_DDL` column definitions match canonical `schema.sql`
- Entity dataclasses are frozen (`@dataclass(frozen=True)`)
- Repository classes have insert methods

---

## Required Paths (18)

The compliance scanner checks for these paths:

```
Makefile
README.md
BLUEPRINT.md
EVAL_STRATEGY.md
requirements.txt
scripts/analyze.py
scripts/evaluate.py
scripts/checks/
schemas/output.schema.json
eval-repos/synthetic/
eval-repos/real/
evaluation/ground-truth/
evaluation/llm/orchestrator.py
evaluation/llm/judges/
evaluation/llm/prompts/
evaluation/scorecard.md
tests/unit/
tests/integration/
```

---

## Makefile Requirements

Required targets (6):

| Target | Description |
|--------|-------------|
| `setup` | Install tool binary and Python dependencies |
| `analyze` | Run analysis, output to `outputs/<run-id>/output.json` |
| `evaluate` | Run programmatic evaluation |
| `evaluate-llm` | Run LLM judges |
| `test` | Run unit + integration tests |
| `clean` | Remove generated files |

Required variables:

| Variable | Description |
|----------|-------------|
| `REPO_PATH` | Path to repository being analyzed |
| `REPO_NAME` | Repository name for output naming |
| `OUTPUT_DIR` | Directory for analysis outputs |
| `RUN_ID` | UUID for this collection run |
| `REPO_ID` | UUID for the repository |
| `BRANCH` | Git branch being analyzed |
| `COMMIT` | 40-character commit SHA |
| `EVAL_OUTPUT_DIR` | Directory for evaluation outputs |

---

## Required Metadata Fields (8)

All tool outputs use the envelope format with these required metadata fields:

```json
{
  "metadata": {
    "tool_name": "string",
    "tool_version": "semver",
    "run_id": "uuid",
    "repo_id": "uuid",
    "branch": "string",
    "commit": "40-hex-sha",
    "timestamp": "ISO8601",
    "schema_version": "semver"
  },
  "data": { ... }
}
```

---

## Compliance Scanner

Caldera uses a top-level compliance scanner to validate tool readiness across `src/tools/`.

### Location

`src/tool-compliance/tool_compliance.py`

### Usage

```bash
# Basic scan (structure and schema checks only)
python src/tool-compliance/tool_compliance.py --root /path/to/project

# Full scan with execution
python src/tool-compliance/tool_compliance.py \
  --root /path/to/project \
  --run-analysis --run-evaluate --run-llm

# Output to specific files
python src/tool-compliance/tool_compliance.py \
  --root /path/to/project \
  --out-json /tmp/tool_compliance_report.json \
  --out-md /tmp/tool_compliance_report.md

# Tool-specific venv mapping
python src/tool-compliance/tool_compliance.py \
  --root /path/to/project \
  --venv-map "scc=/tmp/scc-venv,lizard=/tmp/lizard-venv"
```

### Outputs

- `/tmp/tool_compliance_report.json` (machine-readable)
- `/tmp/tool_compliance_report.md` (human-readable)

---

## Complete Check Reference (36 Checks)

### Structure Checks

| Check ID | Severity | Description |
|----------|----------|-------------|
| `structure.paths` | high | All 18 required paths exist |
| `make.targets` | high | Makefile includes all 6 required targets |

### Schema Checks

| Check ID | Severity | Description |
|----------|----------|-------------|
| `schema.valid_json` | medium | Schema file parses as valid JSON |
| `schema.draft` | medium | Schema uses JSON Schema draft 2020-12 |
| `schema.contract` | high | Schema requires `metadata` + `data` with 8 metadata fields |
| `schema.version_alignment` | high | Output `schema_version` matches schema `const`/`enum` constraint |

### Output Checks

| Check ID | Severity | Description |
|----------|----------|-------------|
| `output.load` | high | Output JSON is available and parses |
| `output.paths` | high | All path values are repo-relative (no `/`, `./`, `\`, `..`) |
| `output.required_fields` | high | All 8 metadata fields present and non-empty |
| `output.schema_version` | medium | `schema_version` is valid semver |
| `output.tool_name_match` | low | `metadata.tool_name` matches `data.tool` |
| `output.schema_validate` | critical | Output validates against schema (requires `jsonschema`) |
| `output.metadata_consistency` | medium | Commit is 40-hex SHA, timestamp is ISO8601 |

### Evaluation Checks

| Check ID | Severity | Description |
|----------|----------|-------------|
| `evaluation.check_modules` | medium | Tool-specific check modules present per TOOL_RULES |
| `evaluation.llm_prompts` | medium | Tool-specific LLM prompts present per TOOL_RULES |
| `evaluation.ground_truth` | high | Ground truth files present for synthetic repos |
| `evaluation.scorecard` | low | Scorecard exists and is non-empty |
| `evaluation.rollup_validation` | high | EVAL_STRATEGY.md has `## Rollup Validation` with `Rollups:` and `Tests:` |

### Run Checks (optional, via flags)

| Check ID | Severity | Flag | Description |
|----------|----------|------|-------------|
| `run.analyze` | critical | `--run-analysis` | `make analyze` succeeds |
| `run.evaluate` | high | `--run-evaluate` | `make evaluate` succeeds |
| `run.evaluate_llm` | medium | `--run-llm` | `make evaluate-llm` succeeds |
| `evaluation.results` | high | `--run-evaluate` | Evaluation outputs created |
| `evaluation.llm_results` | medium | `--run-llm` | LLM evaluation outputs created |

### Adapter Checks

| Check ID | Severity | Description |
|----------|----------|-------------|
| `adapter.compliance` | high | Adapter exposes `SCHEMA_PATH`, `LZ_TABLES`, `QUALITY_RULES`, `TABLE_DDL`; class has `validate_schema`, `validate_lz_schema`, `validate_quality`, `ensure_lz_tables` |
| `adapter.schema_alignment` | high | `TABLE_DDL` column definitions match canonical `schema.sql` |
| `adapter.integration` | high | Adapter can persist fixture data to in-memory database |
| `adapter.quality_rules_coverage` | medium | `QUALITY_RULES` have implementations in `validate_quality()` |

### dbt/Entity Checks

| Check ID | Severity | Description |
|----------|----------|-------------|
| `dbt.model_coverage` | high | Staging models exist; if rollups declared, rollup models exist |
| `entity.repository_alignment` | high | Entity dataclasses have frozen=True; repositories have insert methods |

### Test Structure Checks

| Check ID | Severity | Description |
|----------|----------|-------------|
| `test.structure_naming` | medium | `tests/unit/` and `tests/integration/` exist; test files follow `test_*.py` |

---

## Tool-Specific Rules (TOOL_RULES)

The compliance scanner uses `TOOL_RULES` dict to enforce tool-specific requirements:

```python
TOOL_RULES = {
    "scc": {
        "required_check_modules": ["cocomo.py", "coverage.py", ...],
        "required_prompts": ["api_design.md", "code_quality.md", ...],
        "ground_truth_mode": "synthetic_json",
        "evaluation_outputs": ["scorecard.md", "checks.json"],
        "adapter": ("persistence.adapters.scc_adapter", "SccAdapter"),
    },
    # ... other tools
}
```

### Adding Tool-Specific Rules

To add custom requirements for a new tool:

1. Add entry to `TOOL_RULES` in `src/tool-compliance/tool_compliance.py`
2. Define `required_check_modules` (list of check module filenames)
3. Define `required_prompts` (list of LLM prompt filenames)
4. Optionally set `ground_truth_mode`: `synthetic_json`, `per_language`, or `any`
5. Define `adapter` tuple: `(module_path, class_name)`

---

## Top-Level Makefile

Caldera provides a top-level Makefile to run tool targets and compliance scans.

Targets:
- `make compliance`
- `make tools-setup`
- `make tools-analyze`
- `make tools-evaluate`
- `make tools-evaluate-llm`
- `make tools-test`
- `make tools-clean`

Variables:
- `TOOL=<name>` limit to a single tool
- `VENV=<path>` pass through to tool Makefiles
- `COMPLIANCE_FLAGS="--run-analysis --run-evaluate --run-llm"`
- `COMPLIANCE_OUT_JSON=/tmp/tool_compliance_report.json`
- `COMPLIANCE_OUT_MD=/tmp/tool_compliance_report.md`

---

## Directory Structure

Every tool MUST follow this standard layout:

```
src/tools/<tool-name>/
├── Makefile
├── README.md
├── BLUEPRINT.md
├── EVAL_STRATEGY.md
├── requirements.txt
│
├── scripts/
│   ├── analyze.py
│   ├── evaluate.py
│   └── checks/
│       ├── __init__.py
│       └── *.py
│
├── schemas/
│   └── output.schema.json
│
├── tests/
│   ├── unit/
│   │   └── test_*.py
│   └── integration/
│       └── test_*.py
│
├── eval-repos/
│   ├── synthetic/
│   └── real/
│
├── evaluation/
│   ├── ground-truth/
│   │   └── *.json
│   ├── results/
│   ├── scorecard.md
│   └── llm/
│       ├── orchestrator.py
│       ├── judges/
│       └── prompts/
│
└── outputs/
    └── <run-id>/
        └── output.json
```

---

## Quick Reference

### Envelope Format

```json
{
  "metadata": {
    "tool_name": "<tool>",
    "tool_version": "<semver>",
    "run_id": "<uuid>",
    "repo_id": "<uuid>",
    "branch": "<branch>",
    "commit": "<40-hex-sha>",
    "timestamp": "<ISO8601>",
    "schema_version": "<semver>"
  },
  "data": {
    "tool": "<tool>",
    "tool_version": "<semver>",
    "files": [ ... ]
  }
}
```

### Path Rules

| Valid | Invalid |
|-------|---------|
| `src/main.py` | `/src/main.py` (absolute) |
| `lib/utils.ts` | `./lib/utils.ts` (leading `./`) |
| `tests/test_foo.py` | `C:\tests\test_foo.py` (Windows absolute) |
| `.` (root dir) | `../outside/file.py` (`..` segment) |

### Schema Version Constraint

Use `const` in your schema (not pattern):

```json
{
  "properties": {
    "metadata": {
      "properties": {
        "schema_version": { "const": "1.0.0" }
      }
    }
  }
}
```

---

## References

- [DEVELOPMENT.md](./DEVELOPMENT.md) - Tutorial for adding new tools
- [TOOL_MIGRATION_CHECKLIST.md](./TOOL_MIGRATION_CHECKLIST.md) - Vulcan to Caldera migration guide
- [templates/BLUEPRINT.md.template](./templates/BLUEPRINT.md.template) - Architecture document template
- [templates/EVAL_STRATEGY.md.template](./templates/EVAL_STRATEGY.md.template) - Evaluation strategy template
