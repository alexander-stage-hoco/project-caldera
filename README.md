# Project Caldera

Tool-first workspace for building and validating analysis tools before SoT integration.

## Repository Layout

```
docs/                 # Architecture + standards
src/tool-compliance/  # Tool compliance scanner
src/tools/            # Individual tools (scc, lizard, ...)
src/sot-engine/       # SoT engine (dbt + persistence)
```

## Tools

Current tools in scope:
- `scc`: size/LOC analysis
- `lizard`: function-level complexity analysis
- `semgrep`: code smell detection (87 DD-mapped rules) *(adapter ready, orchestrator pending)*

Each tool is self-contained under `src/tools/<tool>/` with its own Makefile, schemas, eval repos, and tests.

## Top-Level Commands

Project venv (shared tooling, Python 3.12):

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

```bash
make compliance
make tools-setup
make tools-analyze
make tools-evaluate
make tools-evaluate-llm
make tools-test
make tools-clean
```

Scope to a single tool:

```bash
make tools-test TOOL=scc VENV=/tmp/scc-venv
```

`make compliance` writes reports to `/tmp` by default. Override with
`COMPLIANCE_OUT_JSON` and `COMPLIANCE_OUT_MD`.

## Evaluation Workflow

Per tool:
1. `make setup` to install dependencies.
2. `make analyze` to generate `outputs/<run-id>/output.json`.
3. `make evaluate` for programmatic checks (writes to `evaluation/results/`).
4. `make evaluate-llm` for LLM judge results (also in `evaluation/results/`).

Evaluation outputs are overwritten on each run:
```
evaluation/results/
├── output.json
├── checks.json
├── scorecard.md
└── llm_evaluation.json
```

## Tool Compliance

Run compliance without executing tools:

```bash
python src/tool-compliance/tool_compliance.py --root .
```

Run compliance with analysis/evaluation steps:

```bash
python src/tool-compliance/tool_compliance.py --root . \
  --run-analysis --run-evaluate \
  --venv /tmp/scc-venv
```

Reports:
- `/tmp/tool_compliance_report.json`
- `/tmp/tool_compliance_report.md`

Override report locations:

```bash
make compliance COMPLIANCE_OUT_JSON=/tmp/custom.json COMPLIANCE_OUT_MD=/tmp/custom.md
```

## Standards

Tool requirements and readiness gates are defined in `docs/TOOL_REQUIREMENTS.md`.

## Orchestrator

Run layout → tool ingestion → dbt in one command:

```bash
python src/sot-engine/orchestrator.py \
  --repo-path /path/to/repo \
  --repo-id <repo-uuid> \
  --run-id <run-uuid> \
  --scc-output src/tools/scc/outputs/<run-id>/output.json \
  --lizard-output src/tools/lizard/outputs/<run-id>/output.json \
  --run-dbt
```

To execute tools inside the orchestrator:

```bash
python src/sot-engine/orchestrator.py \
  --repo-path /path/to/repo \
  --repo-id <repo-uuid> \
  --run-id <run-uuid> \
  --run-tools \
  --run-dbt
```

## Repo Identity & Paths

Tools receive `repo_id` and `repo_path` from the orchestrator. `repo_id` is emitted in the output for downstream correlation. Paths in tool outputs must be repo‑relative and use `/` separators (no absolute paths, no `..`, no leading `./`).
If no git metadata is available, tools compute a deterministic 40‑hex content hash for `metadata.commit`.

## Rollups (dbt)

Directory rollups are materialized in DuckDB by dbt, with two variants:

- `rollup_*_directory_recursive_distributions`: includes files from the full subtree of each directory.
- `rollup_*_directory_direct_distributions`: includes only files directly in the directory (no descendants).

dbt tests assert:
- distribution values are in valid ranges
- recursive rollups have `value_count >= direct` for matching directory/metric pairs
- report analyses compile and execute via unit-style DuckDB fixtures (`src/sot-engine/tests/test_report_*.py`)
