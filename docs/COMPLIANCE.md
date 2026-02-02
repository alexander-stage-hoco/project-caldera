# Compliance Requirements & Checks

This document defines the requirements and readiness gates for tools in Project Caldera. Every tool in `src/tools/` MUST comply with these specifications to pass compliance scanning.

---

## Quick Start

```bash
# Full scan on all tools
make compliance

# Single tool scan (faster)
python src/tool-compliance/tool_compliance.py src/tools/<tool-name>

# Preflight mode (~100ms, structure checks only)
python src/tool-compliance/tool_compliance.py src/tools/<tool-name> --preflight

# Full scan with execution
python src/tool-compliance/tool_compliance.py --root . \
  --run-analysis --run-evaluate --run-llm

# Output reports
python src/tool-compliance/tool_compliance.py --root . \
  --out-json /tmp/report.json \
  --out-md /tmp/report.md
```

---

## Compliance Gates Overview

Caldera tools target **Production tier** by default. Each gate must have evidence (file path or test) and is enforced for production readiness.

| Gate | Focus | Key Evidence |
|------|-------|--------------|
| **A: Structure** | Directory layout, files | 18 required paths, Makefile |
| **B: Schema** | Output validation | output.schema.json, envelope format |
| **C: Evaluation** | Quality assessment | LLM judges, ground truth, scorecard |
| **D: Testing** | Test coverage | Unit tests, integration tests |
| **E: dbt/Rollups** | Data transformation | Staging models, rollup models |
| **F: SoT Adapter** | Persistence layer | Adapter class, entities, repository |

---

## Gate A: Structure and Orchestration

### Requirements

| Requirement | Status |
|-------------|:------:|
| Makefile (6 targets) | Required |
| README.md | Required |
| BLUEPRINT.md | Required |
| EVAL_STRATEGY.md | Required |
| requirements.txt | Required |
| 18 required paths | Required |

### Required Paths (18)

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

### Checks & Fix Actions

#### structure.paths (high)

**Validates:** All 18 required paths exist in the tool directory.

**Common failures:**
- Missing `tests/integration/` directory
- Missing `evaluation/scorecard.md`
- Missing `eval-repos/real/` directory

**Fix action:**
```bash
# Create missing directories
mkdir -p tests/integration tests/unit
mkdir -p eval-repos/synthetic eval-repos/real
mkdir -p evaluation/ground-truth evaluation/llm/judges evaluation/llm/prompts
mkdir -p scripts/checks

# Create placeholder files
touch tests/integration/__init__.py
touch tests/unit/__init__.py
touch evaluation/scorecard.md
touch scripts/checks/__init__.py
```

#### make.targets (high)

**Validates:** Makefile includes all 6 required targets.

**Required targets:** `setup`, `analyze`, `evaluate`, `evaluate-llm`, `test`, `clean`

**Common failures:**
- Target named `llm-evaluate` instead of `evaluate-llm`
- Missing `evaluate-llm` target entirely

**Fix action:**
```makefile
evaluate-llm: $(VENV_READY)
	@echo "Running LLM evaluation..."
	@$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		$(OUTPUT_DIR) \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json
```

#### make.uses_common (medium)

**Validates:** Makefile includes `../Makefile.common`.

**Fix action:**
```makefile
# Add at top of Makefile (after SHELL if present)
include ../Makefile.common
```

#### make.output_dir_convention (low)

**Validates:** OUTPUT_DIR uses `outputs/$(RUN_ID)` pattern.

**Common failures:**
- Using `output/` (singular) instead of `outputs/` (plural)
- Hardcoding subdirectory instead of using `$(RUN_ID)`

**Fix action:**
```makefile
# Option 1: Remove local definition (inherit from Makefile.common)
# Delete the OUTPUT_DIR line entirely

# Option 2: Define correctly if you need a custom default
OUTPUT_DIR ?= outputs/$(RUN_ID)
```

#### make.output_filename (medium)

**Validates:** analyze target produces `output.json` (not custom names).

**Fix action:** Update `scripts/analyze.py`:
```python
output_path = Path(args.output_dir) / "output.json"
```

#### make.permissions (low)

**Validates:** Makefile has correct file permissions (readable).

**Fix action:**
```bash
chmod 644 src/tools/<tool>/Makefile
```

---

## Gate B: Output Schema and Validation

### Requirements

- Paths are repo-relative with `/` separators
- No absolute paths, no `..` segments, no leading `./`
- Schema draft is `https://json-schema.org/draft/2020-12/schema`
- `metadata.commit` MUST be a 40-hex SHA
- `metadata.schema_version` MUST use `const` (not pattern)
- All 8 metadata fields required

See [REFERENCE.md](./REFERENCE.md) for envelope format and path rules.

### Checks & Fix Actions

#### schema.valid_json (medium)

**Validates:** `schemas/output.schema.json` is valid JSON.

**Fix action:**
```bash
python -c "import json; json.load(open('schemas/output.schema.json'))"
```

#### schema.draft (medium)

**Validates:** Schema uses JSON Schema draft 2020-12.

**Fix action:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "<Tool Name> Output",
  "type": "object",
  ...
}
```

#### schema.contract (high)

**Validates:** Schema requires `metadata` + `data` with all 8 metadata fields.

**Fix action:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["metadata", "data"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": [
        "tool_name", "tool_version", "run_id", "repo_id",
        "branch", "commit", "timestamp", "schema_version"
      ],
      "properties": {
        "tool_name": { "type": "string" },
        "tool_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
        "run_id": { "type": "string", "format": "uuid" },
        "repo_id": { "type": "string", "format": "uuid" },
        "branch": { "type": "string" },
        "commit": { "type": "string", "pattern": "^[0-9a-fA-F]{40}$" },
        "timestamp": { "type": "string", "format": "date-time" },
        "schema_version": { "const": "1.0.0" }
      }
    },
    "data": { "type": "object" }
  }
}
```

#### schema.version_alignment (high)

**Validates:** Output `schema_version` matches schema's `const`/`enum` constraint.

**Common failures:**
- Schema uses pattern for schema_version instead of const
- Output schema_version doesn't match schema const

**Fix action:** Use `const` in schema:
```json
"schema_version": { "const": "1.0.0" }
```

#### output.load (high)

**Validates:** Output JSON is available and parses.

**Fix action:**
```bash
make analyze REPO_PATH=eval-repos/synthetic
```

#### output.paths (high)

**Validates:** All path values are repo-relative.

**Fix action:** Use shared path normalization:
```python
from common.path_normalization import normalize_file_path

for file_entry in files:
    file_entry["path"] = normalize_file_path(raw_path, repo_root)
```

#### output.required_fields (high)

**Validates:** All 8 metadata fields present and non-empty.

**Fix action:** Ensure analyze.py creates complete envelope (see [REFERENCE.md](./REFERENCE.md)).

#### output.schema_version (medium)

**Validates:** `schema_version` is valid semver (X.Y.Z).

#### output.tool_name_match (low)

**Validates:** `metadata.tool_name` matches `data.tool`.

#### output.schema_validate (critical)

**Validates:** Output validates against schema.

**Fix action:**
```bash
pip install jsonschema
python -c "import json, jsonschema; \
  data = json.load(open('outputs/<run-id>/output.json')); \
  schema = json.load(open('schemas/output.schema.json')); \
  jsonschema.validate(data, schema)"
```

#### output.metadata_consistency (medium)

**Validates:** Commit is 40-hex SHA, timestamp is ISO8601.

**Fix action:**
```python
commit = subprocess.check_output(
    ["git", "-C", repo_path, "rev-parse", "HEAD"],
    text=True
).strip()

from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat()
```

---

## Gate C: Evaluation Coverage

### Requirements

- Minimum 4 LLM judges
- Ground truth files for synthetic repos
- EVAL_STRATEGY.md with required sections
- If rollups declared, EVAL_STRATEGY.md MUST include `Rollup Validation` section

### Required LLM Judges (4 minimum)

| Judge | Purpose |
|-------|---------|
| `accuracy.py` or equivalent | Validates findings match expected |
| `actionability.py` | Assesses if findings are useful |
| `false_positive_rate.py` or equivalent | Evaluates false positive assessment |
| `integration_fit.py` | Validates SoT schema compatibility |

### Checks & Fix Actions

#### evaluation.check_modules (medium)

**Validates:** Tool-specific check modules present in `scripts/checks/`.

**Fix action:**
```bash
touch scripts/checks/__init__.py
touch scripts/checks/accuracy.py
touch scripts/checks/coverage.py
```

#### evaluation.llm_prompts (medium)

**Validates:** LLM prompts present in `evaluation/llm/prompts/`.

**Fix action:**
```bash
touch evaluation/llm/prompts/actionability.md
touch evaluation/llm/prompts/accuracy.md
```

#### evaluation.llm_judge_count (medium)

**Validates:** Minimum 4 LLM judges present.

#### evaluation.synthetic_context (high)

**Validates:** Tool implements the synthetic evaluation context pattern.

The synthetic evaluation context pattern ensures LLM judges don't penalize low finding counts on clean real-world repos by providing context about tool validation on synthetic repos.

**Requirements:**
1. `evaluation/llm/judges/base.py` must accept `evaluation_mode: str | None = None` parameter in `__init__`
2. Primary judge's `collect_evidence()` must set these evidence keys:
   - `evaluation_mode` - set from `self.evaluation_mode`
   - `synthetic_baseline` - from `load_synthetic_evaluation_context()` or fallback
   - `interpretation_guidance` - from `get_interpretation_guidance()` or fallback
3. Primary prompt must have placeholders:
   - `{{ evaluation_mode }}`
   - `{{ synthetic_baseline }}`
   - `{{ interpretation_guidance }}`

**Common failures:**
- base.py missing `evaluation_mode` parameter
- Primary judge only sets synthetic context in real_world mode (should always set with fallback values)
- Prompt missing required placeholders

**Fix action for base.py:**
```python
def __init__(
    self,
    model: str = "opus-4.5",
    timeout: int = 120,
    # ... other params
    evaluation_mode: str | None = None,  # Add this parameter
):
    super().__init__(
        # ... other params
        evaluation_mode=evaluation_mode,  # Pass to parent
    )
```

**Fix action for primary judge collect_evidence():**
```python
def collect_evidence(self) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "evaluation_mode": self.evaluation_mode,
        # ... other evidence
    }

    # Always set these keys (not just for real_world mode)
    if self.evaluation_mode == "real_world":
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "No synthetic baseline available"
            evidence["interpretation_guidance"] = "Evaluate based on ground truth comparison only"
    else:
        # Synthetic mode fallbacks
        evidence["synthetic_baseline"] = "N/A - synthetic mode uses direct ground truth comparison"
        evidence["interpretation_guidance"] = "Strict ground truth evaluation"

    return evidence
```

**Fix action for prompt:**
```markdown
# Evaluation

## Context

{{ interpretation_guidance }}

### Synthetic Baseline
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evidence

{{ evidence }}
```

#### evaluation.ground_truth (high)

**Validates:** Ground truth files present for synthetic repos.

**Ground truth modes:**
- `synthetic_json`: Requires `evaluation/ground-truth/synthetic.json`
- `per_language`: Requires `evaluation/ground-truth/<repo-name>.json` per repo
- `any`: At least one `.json` file

**Fix action:**
```json
// evaluation/ground-truth/synthetic.json
{
  "repo_name": "synthetic",
  "expected_file_count": 10,
  "files": {
    "src/main.py": { "metric_a": 42 }
  }
}
```

#### evaluation.scorecard (low)

**Validates:** Scorecard exists and is non-empty.

**Fix action:**
```bash
make evaluate
# Or create placeholder:
echo "# Scorecard\n\n*Run \`make evaluate\` to generate.*" > evaluation/scorecard.md
```

#### evaluation.rollup_validation (high)

**Validates:** EVAL_STRATEGY.md has `## Rollup Validation` with `Rollups:` and `Tests:`.

**Fix action:** Add to EVAL_STRATEGY.md:
```markdown
---

## Rollup Validation

Rollups:
- directory_direct_counts (metrics for files directly in directory)
- directory_recursive_counts (metrics for all files in subtree)

Tests:
- src/sot-engine/dbt/tests/test_rollup_<tool>_direct_vs_recursive.sql

### Invariants Tested

| Invariant | Description |
|-----------|-------------|
| recursive >= direct | Recursive counts include all descendants |
```

#### docs.blueprint_structure (medium)

**Validates:** BLUEPRINT.md has required sections.

**Required sections:** Executive Summary, Architecture, Implementation Plan, Configuration, Performance, Evaluation, Risk

**Fix action:**
```bash
cp docs/templates/BLUEPRINT.md.template src/tools/<tool>/BLUEPRINT.md
```

#### docs.eval_strategy_structure (high)

**Validates:** EVAL_STRATEGY.md has required sections.

**Required sections:** Philosophy, Dimension Summary, Check Catalog, Scoring, Decision Thresholds, Ground Truth

**Fix action:**
```bash
cp docs/templates/EVAL_STRATEGY.md.template src/tools/<tool>/EVAL_STRATEGY.md
```

---

## Gate D: Testing

### Requirements

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Test files follow `test_*.py` naming
- `make test` succeeds

### Checks & Fix Actions

#### test.structure_naming (medium)

**Validates:** Test directories exist and files follow `test_*.py` naming.

**Valid:** `test_accuracy.py`, `test_coverage.py`, `conftest.py`, `__init__.py`
**Invalid:** `accuracy_test.py` (suffix instead of prefix)

**Fix action:**
```bash
mkdir -p tests/unit tests/integration
mv tests/unit/accuracy_test.py tests/unit/test_accuracy.py
```

#### run.analyze (critical)

**Validates:** `make analyze` succeeds (only with `--run-analysis`).

#### run.evaluate (high)

**Validates:** `make evaluate` succeeds (only with `--run-evaluate`).

#### run.evaluate_llm (medium)

**Validates:** `make evaluate-llm` succeeds (only with `--run-llm`).

---

## Gate E: Rollup Correctness (dbt)

### Requirements

- Staging models: `src/sot-engine/dbt/models/staging/stg_<tool>_*.sql`
- Rollup models (if declared): `src/sot-engine/dbt/models/marts/rollup_<tool>_directory_*.sql`
- dbt tests: `src/sot-engine/dbt/tests/test_rollup_<tool>_*.sql`

### Rollup Invariants

- Direct rollups include only files directly in a directory
- Recursive rollups include all descendant files
- `recursive_count >= direct_count` for identical run/directory/metric
- `recursive_min_value <= direct_min_value`
- `recursive_max_value >= direct_max_value`

See [REFERENCE.md](./REFERENCE.md) for dbt patterns.

### Checks & Fix Actions

#### dbt.model_coverage (high)

**Validates:** Tools with adapters have corresponding dbt models.

**Expected models:**
- `src/sot-engine/dbt/models/staging/stg_<tool>_*.sql`
- `src/sot-engine/dbt/models/marts/rollup_<tool>_*.sql` (if rollups declared)

**Fix action:** Use automation:
```bash
python scripts/generate_dbt_models.py <tool> --table lz_<tool>_metrics --metrics col1,col2
```

---

## Gate F: SoT Adapter

### Requirements

- Adapter file: `src/sot-engine/persistence/adapters/<tool>_adapter.py`
- Entity dataclasses in `entities.py` (frozen)
- Repository class in `repositories.py`
- Tables in `schema.sql`
- Registered in orchestrator

### Adapter Contract

Must expose: `SCHEMA_PATH`, `LZ_TABLES`, `QUALITY_RULES`, `TABLE_DDL`
Must implement: `validate_schema`, `validate_lz_schema`, `validate_quality`, `ensure_lz_tables`

See [REFERENCE.md](./REFERENCE.md) for adapter patterns.

### Checks & Fix Actions

#### adapter.compliance (high)

**Validates:** Adapter exposes required contract elements.

**Fix action:** See `src/sot-engine/persistence/adapters/scc_adapter.py` for reference.

#### adapter.schema_alignment (high)

**Validates:** TABLE_DDL column definitions match canonical `schema.sql`.

#### adapter.integration (high)

**Validates:** Adapter can persist fixture data to in-memory database.

**Fix action:** Create fixture at `src/sot-engine/persistence/fixtures/<tool>_output.json`

#### adapter.quality_rules_coverage (medium)

**Validates:** QUALITY_RULES have implementations in validate_quality().

#### sot.adapter_registered (medium)

**Validates:** Adapter exported in `adapters/__init__.py`.

**Fix action:**
```python
# In src/sot-engine/persistence/adapters/__init__.py
from .my_tool_adapter import MyToolAdapter

__all__ = [
    # ... existing exports
    "MyToolAdapter",
]
```

#### sot.schema_table (high)

**Validates:** Landing zone tables exist in `schema.sql`.

**Fix action:**
```sql
CREATE TABLE IF NOT EXISTS lz_my_tool_metrics (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    -- ... columns
    PRIMARY KEY (run_pk, file_id)
);
```

Or use automation: `python scripts/create-tool.py <tool> --sot-only`

#### sot.orchestrator_wired (high)

**Validates:** Tool is in `TOOL_INGESTION_CONFIGS` in orchestrator.py.

**Note:** layout-scanner is handled specially and always passes.

**Fix action:**
```python
TOOL_INGESTION_CONFIGS = [
    # ... existing configs
    ToolIngestionConfig(
        tool_name="my-tool",
        makefile_dir="src/tools/my-tool",
        adapter_class=MyToolAdapter,
    ),
]
```

#### sot.dbt_staging_model (high)

**Validates:** dbt staging model exists (`stg_*<tool>*.sql`).

#### entity.repository_alignment (high)

**Validates:** Entity dataclasses have frozen=True; repositories have insert methods.

---

## Complete Check Reference (42 Checks)

### Quick Reference by Severity

| Severity | Checks |
|----------|--------|
| **critical** | output.schema_validate, run.analyze |
| **high** | structure.paths, make.targets, schema.contract, schema.version_alignment, output.load, output.paths, output.required_fields, evaluation.ground_truth, evaluation.rollup_validation, evaluation.synthetic_context, docs.eval_strategy_structure, adapter.compliance, adapter.schema_alignment, adapter.integration, sot.schema_table, sot.orchestrator_wired, sot.dbt_staging_model, dbt.model_coverage, entity.repository_alignment, run.evaluate |
| **medium** | schema.valid_json, schema.draft, output.schema_version, output.metadata_consistency, make.uses_common, make.output_filename, docs.blueprint_structure, evaluation.check_modules, evaluation.llm_prompts, evaluation.llm_judge_count, adapter.quality_rules_coverage, sot.adapter_registered, test.structure_naming, run.evaluate_llm |
| **low** | make.output_dir_convention, make.permissions, output.tool_name_match, evaluation.scorecard |

### All Checks by Category

| Check ID | Severity | Description |
|----------|----------|-------------|
| **Structure** | | |
| structure.paths | high | All 18 required paths exist |
| make.targets | high | Makefile includes all 6 required targets |
| make.uses_common | medium | Makefile includes Makefile.common |
| make.output_dir_convention | low | OUTPUT_DIR uses outputs/$(RUN_ID) |
| make.output_filename | medium | analyze produces output.json |
| make.permissions | low | Makefile is readable |
| **Schema** | | |
| schema.valid_json | medium | Schema parses as valid JSON |
| schema.draft | medium | Schema uses draft 2020-12 |
| schema.contract | high | Schema requires metadata + data |
| schema.version_alignment | high | Output version matches schema const |
| **Output** | | |
| output.load | high | Output JSON parses |
| output.paths | high | All paths repo-relative |
| output.required_fields | high | All 8 metadata fields present |
| output.schema_version | medium | schema_version is valid semver |
| output.tool_name_match | low | metadata.tool_name matches data.tool |
| output.schema_validate | critical | Output validates against schema |
| output.metadata_consistency | medium | Commit 40-hex, timestamp ISO8601 |
| **Documents** | | |
| docs.blueprint_structure | medium | BLUEPRINT.md has required sections |
| docs.eval_strategy_structure | high | EVAL_STRATEGY.md has required sections |
| **Evaluation** | | |
| evaluation.check_modules | medium | Check modules present |
| evaluation.llm_prompts | medium | LLM prompts present |
| evaluation.llm_judge_count | medium | Minimum 4 LLM judges |
| evaluation.synthetic_context | high | Synthetic evaluation context pattern implemented |
| evaluation.ground_truth | high | Ground truth files present |
| evaluation.scorecard | low | Scorecard exists |
| evaluation.rollup_validation | high | EVAL_STRATEGY has Rollup Validation |
| **Adapter** | | |
| adapter.compliance | high | Adapter has required contract |
| adapter.schema_alignment | high | TABLE_DDL matches schema.sql |
| adapter.integration | high | Adapter persists fixture data |
| adapter.quality_rules_coverage | medium | QUALITY_RULES implemented |
| **SoT Integration** | | |
| sot.adapter_registered | medium | Adapter in __init__.py |
| sot.schema_table | high | Tables in schema.sql |
| sot.orchestrator_wired | high | Tool in TOOL_INGESTION_CONFIGS |
| sot.dbt_staging_model | high | Staging model exists |
| **dbt/Entity** | | |
| dbt.model_coverage | high | Models exist for adapter tools |
| entity.repository_alignment | high | Frozen entities, insert methods |
| **Testing** | | |
| test.structure_naming | medium | test_*.py naming convention |
| **Run Checks** | | |
| run.analyze | critical | make analyze succeeds |
| run.evaluate | high | make evaluate succeeds |
| run.evaluate_llm | medium | make evaluate-llm succeeds |
| evaluation.results | high | Evaluation outputs created |
| evaluation.llm_results | medium | LLM outputs created |

---

## Preflight Mode

For rapid iteration during development, use preflight mode (~100ms):

```bash
python src/tool-compliance/tool_compliance.py src/tools/<tool> --preflight
```

**Preflight checks only:**
- structure.paths
- make.targets
- make.uses_common
- make.output_dir_convention
- make.output_filename
- schema.valid_json (draft check)
- schema.contract
- docs.blueprint_structure
- docs.eval_strategy_structure
- test.structure_naming

**Skipped in preflight:**
- All adapter checks
- All output validation
- All execution checks
- dbt model checks
- Entity alignment checks

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

To add custom requirements, edit `src/tool-compliance/tool_compliance.py`.

---

## Fixing Multiple Failures

When you have many failures, fix in this order:
1. **Structure checks** - Create directories/files
2. **Makefile checks** - Add include, fix targets
3. **Schema checks** - Fix output.schema.json
4. **Document checks** - Copy from templates
5. **Evaluation checks** - Create check modules, prompts
6. **Adapter checks** - Implement SoT integration
7. **Output checks** - Fix analyze.py

---

## References

- [REFERENCE.md](./REFERENCE.md) - Technical specifications (envelope, paths, patterns)
- [TOOL_GUIDE.md](./TOOL_GUIDE.md) - Creating and migrating tools
- [EVALUATION.md](./EVALUATION.md) - LLM judge infrastructure
- [templates/BLUEPRINT.md.template](./templates/BLUEPRINT.md.template) - Architecture template
- [templates/EVAL_STRATEGY.md.template](./templates/EVAL_STRATEGY.md.template) - Evaluation template
