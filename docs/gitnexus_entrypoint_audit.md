# GitNexus Entrypoint Detection Audit

**Date:** 2026-03-02
**Repository:** Project Caldera
**Branch:** `promote/20260302-101714`
**Method:** Cross-referenced GitNexus knowledge graph (step=1 in STEP_IN_PROCESS) against exhaustive codebase search (`if __name__`, pyproject.toml console_scripts, shell shebangs, Dockerfile ENTRYPOINT/CMD).

---

## Summary

| Category | Actual | Found | Missed | Hit Rate |
|----------|--------|-------|--------|----------|
| Tool analyzers (`scripts/analyze.py`) | 18 | 13 | 5 | 72% |
| Tool evaluators (`scripts/evaluate.py`) | 8 | 6 | 2 | 75% |
| Tool LLM orchestrators | 5 | 5 | 0 | 100% |
| Tool dashboards/analyzers (secondary) | 5 | 5 | 0 | 100% |
| Programmatic checks | 14 | 14 | 0 | 100% |
| Core scripts (`scripts/*.py`) | 21 | 3 | 18 | 14% |
| Core source modules | 7 | 2 | 5 | 29% |
| Console script entrypoints (pyproject.toml) | 3 | 0 | 3 | 0% |
| Shell script entrypoints | 5 | 0 | 5 | 0% |
| Docker ENTRYPOINT directives | 19 | 0 | 19 | 0% |
| Insight section `fetch_data` | 3 | 3 | 0 | 100% |
| SonarQube API client roots | 11 | 11 | 0 | 100% |
| **Total** | **119** | **62** | **57** | **52%** |

---

## What GitNexus Found (62 entrypoints)

### Tool Analyzers (13 of 18)

| Symbol | File |
|--------|------|
| `main` | `src/tools/coverage-ingest/scripts/analyze.py` |
| `main` | `src/tools/dependensee/scripts/analyze.py` |
| `main` | `src/tools/devskim/scripts/analyze.py` |
| `main` | `src/tools/dotcover/scripts/analyze.py` |
| `main` | `src/tools/gitleaks/scripts/analyze.py` |
| `main` | `src/tools/layout-scanner/scripts/analyze.py` |
| `main` | `src/tools/lizard/scripts/analyze.py` |
| `main` | `src/tools/scancode/scripts/analyze.py` |
| `main` | `src/tools/scc/scripts/analyze.py` |
| `main` | `src/tools/semgrep/scripts/analyze.py` |
| `main` | `src/tools/symbol-scanner/scripts/analyze.py` |
| `analyze_repository` | `src/tools/git-sizer/scripts/analyze.py` |
| `run_analysis` | `src/tools/sonarqube/scripts/analyze.py` |

### Tool Evaluators & Dashboards (11)

| Symbol | File |
|--------|------|
| `main` | `src/tools/git-sizer/scripts/evaluate.py` |
| `main` | `src/tools/scancode/scripts/evaluate.py` |
| `main` | `src/tools/scc/scripts/evaluate.py` |
| `main` | `src/tools/semgrep/scripts/evaluate.py` |
| `main` | `src/tools/sonarqube/scripts/evaluate.py` |
| `main` | `src/tools/symbol-scanner/scripts/evaluate.py` |
| `main` | `src/tools/symbol-scanner/scripts/benchmark.py` |
| `main` | `src/tools/semgrep/scripts/llm_evaluate.py` |
| `main` | `src/tools/devskim/scripts/security_analyzer.py` |
| `main` | `src/tools/semgrep/scripts/smell_analyzer.py` |
| `main` | `src/tools/lizard/scripts/function_analyzer.py` |
| `main` | `src/tools/trivy/scripts/vulnerability_analyzer.py` |
| `display_dashboard` | `src/tools/devskim/scripts/security_analyzer.py` |
| `run_analysis_dashboard` | `src/tools/scc/scripts/directory_analyzer.py` |

### Tool LLM Orchestrators (5)

| Symbol | File |
|--------|------|
| `main` | `src/tools/devskim/evaluation/llm/orchestrator.py` |
| `main` | `src/tools/lizard/evaluation/llm/orchestrator.py` |
| `main` | `src/tools/roslyn-analyzers/evaluation/llm/orchestrator.py` |
| `main` | `src/tools/scancode/evaluation/llm/orchestrator.py` |
| `main` | `src/tools/sonarqube/evaluation/llm/orchestrator.py` |

### Programmatic Check Harnesses (14)

| Symbol | File |
|--------|------|
| `run_all_accuracy_checks` | `src/tools/coverage-ingest/scripts/checks/accuracy.py` |
| `run_accuracy_checks` | `src/tools/devskim/scripts/checks/accuracy.py` |
| `run_accuracy_checks` | `src/tools/lizard/scripts/checks/accuracy.py` |
| `run_all_accuracy_checks` | `src/tools/roslyn-analyzers/scripts/checks/accuracy.py` |
| `run_accuracy_checks` | `src/tools/sonarqube/scripts/checks/accuracy.py` |
| `run_coverage_checks` | `src/tools/lizard/scripts/checks/coverage.py` |
| `run_coverage_checks` | `src/tools/pmd-cpd/scripts/checks/coverage.py` |
| `run_coverage_checks` | `src/tools/scc/scripts/checks/coverage.py` |
| `run_edge_case_checks` | `src/tools/lizard/scripts/checks/edge_cases.py` |
| `run_performance_checks` | `src/tools/lizard/scripts/checks/performance.py` |
| `run_classification_checks` | `src/tools/layout-scanner/scripts/checks/classification.py` |
| `run_output_quality_checks` | `src/tools/layout-scanner/scripts/checks/output_quality.py` |
| `run_all` | `src/tools/git-fame/scripts/checks/output_quality.py` |
| `run_directory_analysis_checks` | `src/tools/scc/scripts/checks/directory_analysis.py` |

### Core Pipeline (2)

| Symbol | File |
|--------|------|
| `main` | `src/sot-engine/orchestrator.py` |
| `scan_tool` | `src/tool-compliance/tool_compliance.py` |

### Utility Scripts (3)

| Symbol | File |
|--------|------|
| `main` | `scripts/docker_runner.py` |
| `main` | `scripts/export_results.py` |
| `create_tool` | `scripts/create-tool.py` |

### Insight Section Data Fetchers (3)

| Symbol | File |
|--------|------|
| `fetch_data` | `src/insights/sections/executive_summary.py` |
| `fetch_data` | `src/insights/sections/file_hotspots.py` |
| `fetch_data` | `src/insights/sections/technical_debt_summary.py` |

### SonarQube API Client Roots (11)

| Symbol | File | Topic |
|--------|------|-------|
| `wait_for_analysis_complete` | `src/tools/sonarqube/scripts/api/module_a_task.py` | Task polling |
| `get_component_tree` | `src/tools/sonarqube/scripts/api/module_b_components.py` | Component tree |
| `get_directory_components` | `src/tools/sonarqube/scripts/api/module_b_components.py` | Directory listing |
| `extract_measures_chunked` | `src/tools/sonarqube/scripts/api/module_d_measures.py` | Metrics extraction |
| `stream_issues_to_jsonl` | `src/tools/sonarqube/scripts/api/module_e_issues.py` | Issue streaming |
| `get_security_rules` | `src/tools/sonarqube/scripts/api/module_f_rules.py` | Security rules |
| `get_rules_for_issues` | `src/tools/sonarqube/scripts/api/module_f_rules.py` | Issue rules |
| `get_file_duplications` | `src/tools/sonarqube/scripts/api/module_g_duplications.py` | Duplications |
| `extract_duplications` | `src/tools/sonarqube/scripts/api/module_g_duplications.py` | Duplications |
| `get_quality_gate_status` | `src/tools/sonarqube/scripts/api/module_h_quality_gate.py` | Quality gate |
| `get_analysis_history` | `src/tools/sonarqube/scripts/api/module_i_history.py` | History |

### Caldera CLI Sub-command (1)

| Symbol | File |
|--------|------|
| `tool_readiness` | `src/caldera_cli/commands/report.py` |

### Misc (1)

| Symbol | File |
|--------|------|
| `main` | `src/tools/git-fame/scripts/build_repos.py` |

---

## What GitNexus Missed (57 entrypoints)

### Missed Tool Analyzers (5)

| Tool | File | Likely Cause |
|------|------|--------------|
| git-fame | `src/tools/git-fame/scripts/analyze.py` | Only `build_repos.py` detected |
| git-blame-scanner | `src/tools/git-blame-scanner/scripts/analyze.py` | Completely absent from graph |
| pmd-cpd | `src/tools/pmd-cpd/scripts/analyze.py` | Only `checks/coverage.py` detected |
| roslyn-analyzers | `src/tools/roslyn-analyzers/scripts/analyze.py` | Only `roslyn_analyzer.py` detected |
| trivy | `src/tools/trivy/scripts/analyze.py` | Only `vulnerability_analyzer.py` detected |

### Missed Core Scripts (18)

| Script | Purpose | Invoked By |
|--------|---------|------------|
| `scripts/analyze_bundle.py` | Bundle ingest + report generation | Makefile (`analyze-bundle`), CI Gate C |
| `scripts/archive_tool_eval.py` | Archive tool evaluation outputs | Manual |
| `scripts/build_results_index.py` | Build results `index.json` catalog | Manual / export pipeline |
| `scripts/check_observability_compliance.py` | LLM observability compliance | CI Gate A |
| `scripts/check_run_quality.py` | Trust score / warning budget checks | CI Gate C |
| `scripts/cloud_cleanup.py` | Destroy orphaned Hetzner VMs | Makefile (`cloud-cleanup`) |
| `scripts/collect_artifacts.py` | Collect tool outputs into bundles | Makefile (`collect`), CI Gate C |
| `scripts/compare_tool_outputs.py` | Docker vs native output comparison | Makefile (`docker-test-tool`) |
| `scripts/count_collection_runs.py` | Count collection runs | Makefile (`status`) |
| `scripts/create_risk_issues.py` | Create GitHub issues from risk register | Manual |
| `scripts/docker_orchestrator_entrypoint.py` | Docker orchestrator container entrypoint | Dockerfile ENTRYPOINT |
| `scripts/generate_dbt_models.py` | dbt model generator | Manual |
| `scripts/get_latest_collection_run_id.py` | Query latest collection run ID | Makefile |
| `scripts/get_latest_run_pk.py` | Query latest tool run PK | Makefile |
| `scripts/get_run_pk.py` | Query specific run PK | Makefile |
| `scripts/list_runs.py` | List all collection runs | Makefile (`list-runs`) |
| `scripts/seed_ground_truth.py` | Seed ground truth for evaluation | Manual |
| `scripts/write_run_manifest.py` | Write post-ingest manifest | Pipeline / export |

### Missed Core Source Modules (5)

| Module | Purpose | Invoked By |
|--------|---------|------------|
| `src/caldera_cli/app.py` | Caldera CLI main app (Typer) | `caldera` console script |
| `src/architecture-review/reviewer.py` | Architecture conformance reviewer | Makefile (`arch-review`) |
| `src/insights/cli.py` | Insights CLI (Typer) | `insights` console script |
| `src/insights/scripts/evaluate.py` | Insights evaluation | `insights-evaluate` console script |
| `src/insights/scripts/extract_top_insights.py` | Top insights extraction | Pipeline |

### Missed Module Entrypoints (1)

| Module | Purpose | Invoked By |
|--------|---------|------------|
| `src/insights/__main__.py` | `python -m insights` module entry | `python -m insights` |

### Missed Console Script Entrypoints (3)

From `pyproject.toml` `[project.scripts]` — installed as CLI commands:

| Command | Entrypoint | Source File |
|---------|-----------|-------------|
| `caldera` | `caldera_cli.app:main` | Root `pyproject.toml` |
| `insights` | `insights.cli:main` | `src/insights/pyproject.toml` |
| `insights-evaluate` | `insights.scripts.evaluate:main` | `src/insights/pyproject.toml` |

### Missed Shell Script Entrypoints (5)

| Script | Purpose |
|--------|---------|
| `scripts/caldera-run` | Top-level dockerized pipeline wrapper (Mode 3) |
| `scripts/cloud-run.sh` | Cloud analysis via Terraform |
| `scripts/docker_test_all.sh` | Batch Docker parity testing |
| `scripts/hooks/check-tool-compliance.sh` | Pre-commit hook |
| `infra/run-analysis.sh` | Remote VM analysis runner |

### Missed Docker ENTRYPOINT Directives (19)

**17 tool Dockerfiles** — each with `ENTRYPOINT ["make", "analyze", ...]`:

| Tool | Dockerfile |
|------|-----------|
| coverage-ingest | `src/tools/coverage-ingest/Dockerfile` |
| dependensee | `src/tools/dependensee/Dockerfile` |
| devskim | `src/tools/devskim/Dockerfile` |
| dotcover | `src/tools/dotcover/Dockerfile` |
| git-blame-scanner | `src/tools/git-blame-scanner/Dockerfile` |
| git-fame | `src/tools/git-fame/Dockerfile` |
| git-sizer | `src/tools/git-sizer/Dockerfile` |
| gitleaks | `src/tools/gitleaks/Dockerfile` |
| layout-scanner | `src/tools/layout-scanner/Dockerfile` |
| lizard | `src/tools/lizard/Dockerfile` |
| pmd-cpd | `src/tools/pmd-cpd/Dockerfile` |
| roslyn-analyzers | `src/tools/roslyn-analyzers/Dockerfile` |
| scancode | `src/tools/scancode/Dockerfile` |
| scc | `src/tools/scc/Dockerfile` |
| semgrep | `src/tools/semgrep/Dockerfile` |
| sonarqube | `src/tools/sonarqube/Dockerfile` |
| symbol-scanner | `src/tools/symbol-scanner/Dockerfile` |

**2 infrastructure Dockerfiles:**

| Image | Dockerfile | ENTRYPOINT |
|-------|-----------|------------|
| caldera-runner | `docker/caldera-runner/Dockerfile` | `python scripts/docker_runner.py` |
| caldera-orchestrator | `docker/caldera-orchestrator/Dockerfile` | `python scripts/docker_orchestrator_entrypoint.py` |

### Missed Tool Evaluators (2)

| Tool | File |
|------|------|
| lizard | `src/tools/lizard/scripts/evaluate.py` |
| devskim | `src/tools/devskim/scripts/evaluate.py` |

---

## Root Cause Analysis

| Gap Category | Root Cause | Severity |
|--------------|-----------|----------|
| 18 standalone scripts | No inbound CALLS edges from indexed Python code. Invoked by Makefiles, shell scripts, or CI YAML — not by Python imports. Call-graph tracing cannot reach them. | **High** |
| 5 tool analyzers | Likely incomplete indexing or parsing issues. These tools have complex subprocess patterns (Java for pmd-cpd, .NET for roslyn, shell for trivy/git-blame-scanner). | **High** |
| Caldera CLI + Insights CLI | Typer `@app.command()` decorator pattern not recognized as call-chain root. Framework magic hides the entrypoint relationship. | **Medium** |
| Console scripts (pyproject.toml) | Package manager config, not code. Outside the knowledge graph's scope. | **Low** |
| Shell scripts | GitNexus indexes Python/JS/Java etc., not Bash. Expected blind spot. | **Expected** |
| Dockerfiles | `CMD`/`ENTRYPOINT` directives are infrastructure config. Outside the knowledge graph's scope. | **Expected** |
| `fetch_data` found but not parent `insights/cli.py` | `fetch_data` functions are called from Python code. `cli.py` is only reachable via Typer framework registration, which the graph doesn't trace. | **Medium** |

---

## Recommendations

1. **Script-level entrypoint heuristic:** Any Python file with `if __name__ == "__main__"` that is not imported by another indexed file should be flagged as a standalone CLI entrypoint.
2. **Framework-aware detection:** Recognize Typer/Click `@app.command()` and `@app.callback()` as entrypoint markers.
3. **pyproject.toml parsing:** Extract `[project.scripts]` and `[project.gui-scripts]` as declared entrypoints.
4. **Makefile/CI cross-referencing:** Parse `Makefile` and `.github/workflows/*.yml` for `python` invocations to discover externally-invoked scripts.
5. **Dockerfile parsing:** Extract `CMD` and `ENTRYPOINT` directives as infrastructure-level entrypoints.

---

## Methodology

1. Queried GitNexus knowledge graph: `MATCH (s)-[r:CodeRelation {type: 'STEP_IN_PROCESS'}]->(p:Process) WHERE r.step = 1` to find all process entry symbols.
2. Filtered out `eval-repos/` (test fixture repositories bundled inside tools).
3. Searched codebase exhaustively for:
   - `if __name__ == "__main__"` blocks (excluding `.venv/`, `eval-repos/`, `node_modules/`)
   - `[project.scripts]` in `pyproject.toml` files
   - `#!/` shebangs in `scripts/`, `infra/`, `docker/` directories
   - `ENTRYPOINT` and `CMD` in all Dockerfiles
   - `@app.command()` and `@click.command` decorators
   - `argparse.ArgumentParser` usage
   - `add_common_args` from common CLI parser
4. Compared the two sets and categorized gaps by root cause.

---
---

# GitNexus Flow Detection Audit

**Date:** 2026-03-02
**Question:** Does GitNexus detect logical flows? Do they resemble real business flows?

---

## Real Business Flows in Project Caldera

These are the 5 actual end-to-end flows that define the system, traced from source code:

### F1: Full Pipeline (Orchestrator)

```
orchestrator.main()
├─ _get_or_create_collection_run()
├─ _run_tools()                          # Phase 1
│  └─ run_tool_make() → subprocess.run(["make", "analyze"])  ← subprocess boundary
├─ ingest_outputs()                      # Phase 2
│  └─ [for each tool]:
│     ├─ load_payload() → validate_payload()
│     └─ adapter.persist()               ← dynamic dispatch via adapter_registry
│        ├─ validate_schema()
│        ├─ ensure_lz_tables()
│        └─ _do_persist() → entities → repo.insert()
├─ compute_run_quality()
├─ run_dbt()                             # Phase 3
│  └─ subprocess.run(["dbt", "run/test"])  ← subprocess boundary
└─ collection_repo.mark_status()
```

**Files:** orchestrator.py, 18 adapters, repositories.py, entities.py, execution.py (~25 files)

### F2: Tool Analysis

```
main()
├─ add_common_args() + validate_common_args()   # src/common/cli_parser.py
├─ run_<tool>() → subprocess.run([tool_binary])  # tool-specific execution
├─ normalize paths                                # src/common/path_normalization.py
├─ create_envelope()                              # src/common/envelope_formatter.py
└─ output_path.write_text(json.dumps(...))
```

**Files:** ~5 per tool (analyze.py, cli_parser.py, envelope_formatter.py, path_utils.py, tool helpers)

### F3: Adapter Persistence (Template Method)

```
BaseAdapter.persist(payload)
├─ validate_schema()          # JSON Schema Draft 2020-12
├─ ensure_lz_tables()         # CREATE TABLE IF NOT EXISTS
├─ validate_lz_schema()       # column verification
├─ _do_persist()              # abstract → concrete adapter
│  ├─ _create_tool_run()      # ToolRun entity → lz_tool_runs
│  ├─ validate_quality()      # tool-specific quality rules
│  ├─ _map_entities()         # data → frozen dataclass entities
│  └─ repo.insert_*()         # batch INSERT into landing zone
└─ _run_post_persist_quality() # FK integrity, uniqueness (advisory)
```

**Files:** base_adapter.py, 18 concrete adapters, entities.py, repositories.py, validation.py, quality.py

### F4: Insights Report Generation

```
cli.generate()                  # Typer @app.command()
├─ load_profile()               # stakeholder profile
├─ [for each section]:
│  ├─ fetch_data()              # query DuckDB marts
│  └─ render_section()          # Markdown output
└─ assemble_report()
```

**Files:** cli.py, sections/*.py, DuckDB mart tables (~10 files)

### F5: Compliance Scan

```
scan_tool(tool_root)
├─ structural_checks()          # paths, Makefile targets, BLUEPRINT
├─ _run_make("analyze")         # subprocess.run(["make", "analyze"])  ← boundary
├─ _run_make("evaluate")        # subprocess.run(["make", "evaluate"]) ← boundary
├─ _check_evaluation_quality()  # parse decision/score from eval JSON
├─ data_validation_checks()     # path consistency, rollup invariants
└─ aggregate → ToolResult       # pass/fail with CheckResult list
```

**Files:** tool_compliance.py, config.py, rules/*.yaml (~4 files)

---

## What GitNexus Detected vs. Real Flows

### Top GitNexus Processes (project code, excluding eval-repos)

| Rank | GitNexus Process | Symbols | Files | Maps To |
|------|-----------------|---------|-------|---------|
| 1 | `Main → _resolve_arg` | 14 | 12 | **Partial F2** — arg parsing only |
| 2 | `Main → ValidationError` | 14 | 12 | **Partial F2** — same flow, different leaf |
| 3 | `Main → Lenient` | 14 | 12 | **Partial F2** — same flow, different leaf |
| 4 | `Main → ConfigError` | 13 | 11 | **Partial F2** — same flow, different leaf |
| 5 | `Main → ToolConfig` | 13 | 11 | **Partial F2** — same flow, different leaf |
| 6 | `Main → C` | 12 | 4 | **Artifact** — "things that print to Rich Console" |
| 7 | `Main → Distribution_to_dict` | 10 | 2 | **Partial F2 variant** — output serialization only |
| 8 | `Main → AnalysisResult` | 10 | 5 | **Partial F2 variant** — tool execution step only |
| 9 | `Main → Determine_decision` | 9 | 3 | **Real sub-flow** — evaluation pass/fail gate |
| 10 | `Main → _to_posix` | 9 | 3 | **Partial F2** — path normalization only |

### Detailed Process Step Traces

**Process: `Main → _resolve_arg` (the "largest" flow)**

| Step | Symbol | File |
|------|--------|------|
| 1 | `main` | 11 tool `analyze.py` files |
| 2 | `validate_common_args` | `src/common/cli_parser.py` |
| 3 | `validate_common_args_raising` | `src/common/cli_parser.py` |
| 4 | `_resolve_arg` | `src/common/cli_parser.py` |

This captures only the first 4 function calls of F2 (Tool Analysis). The remaining steps — tool execution, path normalization, envelope creation, output writing — are absent.

**Process: `Main → Determine_decision` (closest to a real flow)**

| Step | Symbol | File |
|------|--------|------|
| 1 | `main` | sonarqube/evaluate.py, semgrep/evaluate.py, git-sizer/evaluate.py |
| 2 | `print_report` / `generate_scorecard_json` | Same files |
| 3 | `determine_decision` | Same files |

This is a real sub-flow (evaluation gate), but only 3 steps of a larger evaluation pipeline.

**Process: `Main → Distribution_to_dict` (serialization chain)**

| Step | Symbol | File |
|------|--------|------|
| 1 | `main` | semgrep/smell_analyzer.py, devskim/security_analyzer.py |
| 2 | `save_output` | Same files |
| 3 | `result_to_dict` | Same files |
| 4 | `directory_stats_to_dict` | Same files |
| 5 | `distribution_to_dict` | Same files |

5-step chain within 2 files — the deepest intra-file trace detected. Real but narrow.

**Orchestrator processes (F1)**

| Process | Steps | Coverage |
|---------|-------|----------|
| `Main → Fetchone` | main → ensure_schema → fetchone | 3 steps of a 10+ step flow |
| `Main → _apply_migrations` | main → ensure_schema → _apply_migrations | 3 steps of a 10+ step flow |

The entire core pipeline (tools → ingest → adapters → dbt → quality) is invisible.

---

## Coverage Matrix: Real Flows vs. GitNexus Detection

| Real Flow | Steps in Flow | Steps Detected | Coverage | Best GitNexus Process |
|-----------|--------------|---------------|----------|----------------------|
| **F1: Full Pipeline** | ~15 (orchestrate → tools → ingest → dbt) | 3 | **20%** | `Main → Fetchone` (schema init only) |
| **F2: Tool Analysis** | ~8 (args → execute → normalize → envelope → write) | 4 | **50%** | `Main → _resolve_arg` (args only) |
| **F3: Adapter Persistence** | ~8 (validate → tables → entities → insert) | 0 | **0%** | None detected |
| **F4: Insights Report** | ~6 (load → fetch → render → assemble) | 0 | **0%** | None detected |
| **F5: Compliance Scan** | ~8 (structure → run → evaluate → aggregate) | 2 | **25%** | `Scan_tool → _attach_duration` |

---

## Structural Problems with Detected Processes

### Problem 1: Leaf-Oriented Fragmentation

GitNexus names processes by their terminal symbol (`Main → X`), not by business intent. This means **one real flow is split into N processes** — one for each leaf node the entrypoint can reach.

**Example:** The Tool Analysis flow (F2) is fragmented into at least 10 separate processes:

- `Main → _resolve_arg` (arg resolution path)
- `Main → ValidationError` (validation error path)
- `Main → Lenient` (lenient mode path)
- `Main → ConfigError` (config error path)
- `Main → ToolConfig` (config loading path)
- `Main → AnalysisResult` (execution path)
- `Main → Distribution_to_dict` (serialization path)
- `Main → _to_posix` (path normalization path)
- `Main → _strip_repo_prefix` (path stripping path)
- `Main → Add_pattern` (pattern addition path)

A developer would describe this as **one flow** ("tool analysis"), not ten.

### Problem 2: Cross-Boundary Blindness

The graph cannot trace across:
- `subprocess.run()` calls (orchestrator → tools, orchestrator → dbt, compliance → make)
- Dynamic dispatch (adapter registry, Typer decorators, dynamic imports)
- SQL queries (DuckDB operations are opaque strings)
- dbt model references (Jinja SQL, not Python)

These boundaries sever exactly the connections that define the real business flows.

### Problem 3: Artifacts Ranked as Top Flows

`Main → C` (Rich Console) ranks #6 by symbol count. This is not a flow — it's "functions that eventually call `console.print()`". Similarly, `Main → ValidationError` is "functions that can raise a validation error", not a business operation.

---

## Verdict

| Question | Answer | Grade |
|----------|--------|-------|
| **Does GitNexus detect logical flows?** | It detects **call-chain fragments** — paths from entrypoints to leaf symbols. These are syntactically valid traces but semantically incomplete. The deepest real-code trace is 5 steps (`Main → Distribution_to_dict`). Most are 3-4 steps. | **C-** |
| **Do they resemble real business flows?** | **No.** The top processes are mechanical artifacts (arg parsing, error paths, console printing), not recognizable business operations. The 5 real flows (pipeline, analysis, persistence, insights, compliance) are either absent (F3, F4), fragmented into stubs (F1, F5), or split into leaf-oriented slices (F2). A developer reviewing these processes would not recognize their system's architecture. | **D** |

---

## Root Causes

| Cause | Impact | Severity |
|-------|--------|----------|
| **Subprocess boundaries** sever call graph | Orchestrator → tools, orchestrator → dbt, compliance → make targets all invisible | **Critical** |
| **Dynamic dispatch** not resolved | Adapter registry, Typer decorators, dynamic section imports | **High** |
| **Leaf-oriented naming** fragments flows | One real flow → N processes, losing holistic view | **High** |
| **Large file depth limits** | orchestrator.py (1100+ lines), tool_compliance.py (5000+ lines) may not be fully traced | **Medium** |
| **SQL/config opacity** | DuckDB queries, dbt models, YAML rules are dead ends | **Medium** |

---

## Recommendations for Flow Detection Improvement

1. **Subprocess tracing heuristic:** When `subprocess.run(["make", "analyze"])` is detected in tool directory context, link to that tool's `analyze.py:main()` as a virtual CALLS edge.
2. **Template method resolution:** Recognize `BaseAdapter.persist()` → `_do_persist()` as dispatching to all concrete adapters via inheritance.
3. **Business flow aggregation:** Merge leaf-oriented processes that share the same entrypoint into a single composite flow, named by the entrypoint rather than the leaf.
4. **Framework-aware tracing:** Resolve Typer `@app.command()` registrations to their handler functions.
5. **Adapter registry resolution:** Trace `adapter_registry[tool_name]` to concrete adapter classes.

---

## Methodology

1. Identified the 5 real business flows by reading source code of orchestrator.py, scc/analyze.py, scc_adapter.py, insights/cli.py, and tool_compliance.py.
2. Queried GitNexus for all processes involving project code (excluding eval-repos) via Cypher: `MATCH (s)-[r:CodeRelation {type: 'STEP_IN_PROCESS'}]->(p:Process)`.
3. Retrieved full step traces for the top 5 processes by symbol count.
4. Mapped each GitNexus process to real flows and assessed coverage.
5. Identified structural problems (fragmentation, boundary blindness, artifact ranking) from the mapping.

---
---

# GitNexus Impact Analysis Audit: `BaseAdapter.persist`

**Date:** 2026-03-02
**Target:** `BaseAdapter.persist` at `src/sot-engine/persistence/adapters/base_adapter.py:265`
**Direction:** Upstream (what depends on this)
**Depth:** 2
**Validating:** Structural fan-in accuracy, whether impact feels realistic

---

## What GitNexus Found

### `impact()` Tool Result

The `impact()` tool **resolved to the wrong symbol**: `src/insights/evidence/builder.py:persist` instead of `src/sot-engine/persistence/adapters/base_adapter.py:persist`. It returned:

```
target:    insights/evidence/builder.py:persist  ← WRONG
impacted:  0
risk:      LOW
```

This is a **disambiguation failure** — `persist` is a common function name and `impact()` does not accept a `file_path` parameter to narrow the match.

### `context()` Tool Result (Corrected)

Using `context(name="persist", file_path="src/sot-engine/persistence/adapters/base_adapter.py")` correctly resolved the symbol and returned:

**Incoming CALLS (d=1):**

| Caller | File |
|--------|------|
| `ingest_outputs` | `src/sot-engine/orchestrator.py` |

**Outgoing CALLS (what `persist` calls):**

| Callee | File |
|--------|------|
| `check_metadata` | `src/sot-engine/persistence/quality.py` |
| `_log` | `src/sot-engine/persistence/adapters/base_adapter.py` |
| `validate_schema` | `src/sot-engine/persistence/adapters/base_adapter.py` |
| `ensure_lz_tables` | `src/sot-engine/persistence/adapters/base_adapter.py` |
| `validate_lz_schema` | `src/sot-engine/persistence/adapters/base_adapter.py` |
| `_do_persist` | `src/sot-engine/persistence/adapters/base_adapter.py` |
| `_run_post_persist_quality` | `src/sot-engine/persistence/adapters/base_adapter.py` |

### `context()` for `ingest_outputs` (d=2)

**Incoming CALLS:**

| Caller | File | Type |
|--------|------|------|
| `main` | `src/sot-engine/orchestrator.py` | Production |
| `test_orchestrator_end_to_end` | `src/sot-engine/tests/test_orchestrator_e2e.py` | Test |
| `test_ingest_outputs_validates_run_id` | `src/sot-engine/tests/test_orchestrator.py` | Test |
| `test_ingest_outputs_writes_expected_rows` | `src/sot-engine/tests/test_orchestrator.py` | Test |
| `ingested_db` (fixture) | `src/sot-engine/tests/test_multi_tool_integration.py` | Test |
| `subset_db` (fixture) | `src/sot-engine/tests/test_multi_tool_integration.py` | Test |
| `test_replace_mode` | `src/sot-engine/tests/test_multi_tool_integration.py` | Test |
| `test_e2e_live_tools` | `src/sot-engine/tests/test_e2e_live_tools.py` | Test |
| `pipeline_db` (fixture) | `src/sot-engine/tests/test_dbt_pipeline_e2e.py` | Test |

---

## Ground Truth (Actual Codebase)

### Production Callers of `.persist()` — 2 call sites, 1 file

| Call Site | File | Line | Context |
|-----------|------|------|---------|
| `LayoutScannerAdapter(...).persist(payload)` | `orchestrator.py` | 857 | Layout-first mandatory ingest |
| `adapter.persist(payload)` | `orchestrator.py` | 921 | Loop over remaining tool adapters |

Both are inside `ingest_outputs()`. No other production code calls `persist()` directly.

### Production Callers of `ingest_outputs()` — 1 call site

| Call Site | File | Line |
|-----------|------|------|
| `ingest_outputs(...)` | `orchestrator.py` | 1314 |

Inside `main()`. No scripts call `ingest_outputs()` — `scripts/analyze_bundle.py` invokes the orchestrator via subprocess, not Python import.

### Test Callers of `ingest_outputs()` — 8 call sites, 4 files

| Caller | File |
|--------|------|
| `test_orchestrator_end_to_end` | `tests/test_orchestrator_e2e.py` |
| `test_ingest_outputs_validates_run_id` | `tests/test_orchestrator.py` |
| `test_ingest_outputs_writes_expected_rows` | `tests/test_orchestrator.py` |
| `ingested_db` (fixture) | `tests/test_multi_tool_integration.py` |
| `subset_db` (fixture) | `tests/test_multi_tool_integration.py` |
| `test_replace_mode` | `tests/test_multi_tool_integration.py` |
| `test_e2e_live_tools` | `tests/test_e2e_live_tools.py` |
| `pipeline_db` (fixture) | `tests/test_dbt_pipeline_e2e.py` |

### Test Callers of `.persist()` Directly — 292 call sites, 36 test files

These adapter unit tests call `adapter.persist()` directly, bypassing `ingest_outputs()`. Examples: `test_scc_adapter.py`, `test_lizard_adapter.py`, `test_gitleaks_adapter_comprehensive.py`, etc.

---

## Comparison: GitNexus vs. Ground Truth

### Fan-In Accuracy

| Metric | GitNexus (`context`) | Actual | Match? |
|--------|---------------------|--------|--------|
| d=1 production callers of `persist()` | 1 (`ingest_outputs`) | 1 function, 2 call sites | **Correct** |
| d=2 production callers of `ingest_outputs()` | 1 (`main`) | 1 (`main`) | **Correct** |
| d=2 test callers of `ingest_outputs()` | 8 across 4 files | 8 across 4 files | **Correct** |
| d=1 test callers of `persist()` directly | **Not reported** | 292 calls across 36 files | **Missed** |

### Full Upstream Call Tree (Ground Truth)

```
main()                                          # orchestrator.py:1016  [d=2]
└─ ingest_outputs()                             # orchestrator.py:812   [d=1]
   ├─ LayoutScannerAdapter.persist(payload)     # orchestrator.py:857   [d=0] TARGET
   └─ adapter.persist(payload)                  # orchestrator.py:921   [d=0] TARGET
      └─ [18 concrete _do_persist() overrides]  # ← not traced (dynamic dispatch)

# Test paths bypassing ingest_outputs (d=1 direct):
36 test files → adapter.persist()               # ← missed by context/impact
```

### What GitNexus Got Right

1. **Production call chain is perfect:** `main → ingest_outputs → persist` — both edges correct, no false positives.
2. **Test callers of `ingest_outputs` are complete:** All 8 callers across 4 files found, including fixtures.
3. **Outgoing calls from `persist()` are accurate:** All 7 callees (check_metadata, validate_schema, ensure_lz_tables, validate_lz_schema, _do_persist, _run_post_persist_quality, _log) correctly identified.

### What GitNexus Got Wrong

1. **`impact()` disambiguation failure:** Resolved to `insights/evidence/builder.py:persist` instead of `base_adapter.py:persist`. The `impact()` tool lacks a `file_path` parameter, unlike `context()` which disambiguated correctly. This is the most important analysis tool returning completely wrong results for common symbol names.

2. **36 direct test callers missed:** Adapter unit tests call `.persist()` directly (not through `ingest_outputs`). These don't appear in the `context()` output for `persist`. This is likely because the graph edges are stored against concrete adapter classes (e.g., `SccAdapter.persist`), not the base class method — a polymorphism resolution gap.

3. **Dynamic dispatch not resolved:** `persist()` calls `_do_persist()` which is abstract. The 18 concrete overrides (one per tool adapter) are not linked. A change to `persist()`'s contract would break all 18, but the graph shows only the abstract method.

---

## Is the Impact Realistic?

| Aspect | Assessment |
|--------|-----------|
| **Production fan-in shape** | **Realistic.** The narrow funnel (`main → ingest_outputs → persist`) is correct. This is a template method pattern with a single orchestration entry point — changing `persist()` truly does affect all data ingestion through one bottleneck. |
| **Risk level** | **Unrealistic (tool failure).** `impact()` reported LOW/0. Real risk is **CRITICAL**: `persist()` is the single gateway for all 18 tools' data entering DuckDB. Any signature change, validation change, or error handling change here breaks the entire pipeline. |
| **Test coverage signal** | **Partially realistic.** The 8 integration test callers via `ingest_outputs` are found and give a useful signal for what e2e tests to run. But the 36 adapter unit tests (the primary regression safety net) are invisible. |
| **Blast radius for refactoring** | **Underestimated.** The true downstream fan-out is: `persist → _do_persist → 18 concrete adapters`, plus `persist → validate_schema/ensure_lz_tables/etc → 6 shared utilities`. GitNexus shows 7 outgoing calls from `persist` (correct for base_adapter.py), but doesn't trace through to the 18 concrete implementations. |

---

## Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| **Fan-in accuracy (production)** | **A** | `main → ingest_outputs → persist` — both edges correct, no false positives |
| **Fan-in accuracy (tests)** | **B-** | 8/8 `ingest_outputs` test callers found; 36 direct `persist()` test callers missed |
| **Risk realism** | **F** | Wrong symbol → reported 0 impact on the most critical function in the persistence layer |
| **Disambiguation** | **D** | `impact()` lacks `file_path` parameter; `context()` handles it correctly — tooling inconsistency |
| **Dynamic dispatch resolution** | **D** | `_do_persist()` abstract method found but 18 concrete overrides not linked |
| **Overall** | **C** | Graph edges are correct when the right symbol is targeted; tool UX and polymorphism gaps undermine practical utility |

---

## Recommendations

1. **Add `file_path` parameter to `impact()`** to match `context()`'s disambiguation capability.
2. **Resolve inheritance dispatch:** When an abstract method (`_do_persist`) is called, link to all concrete overrides in subclasses as virtual CALLS edges.
3. **Aggregate polymorphic call sites:** Test files calling `SccAdapter.persist()` should be linked to `BaseAdapter.persist` via EXTENDS/IMPLEMENTS edges.
4. **Risk heuristic for template methods:** A method that is abstract + called from a high-fan-in function should auto-escalate risk based on the number of concrete implementations.

---

## Methodology

1. Ran `impact(target="persist", direction="upstream", maxDepth=2)` — observed disambiguation failure.
2. Ran `context(name="persist", file_path="src/sot-engine/persistence/adapters/base_adapter.py")` — got correct d=1 edges.
3. Ran `context(name="ingest_outputs", file_path="src/sot-engine/orchestrator.py")` — got correct d=2 edges.
4. Ran Cypher query for direct CALLS to `persist` in `base_adapter.py` — confirmed 1 production caller.
5. Grep'd codebase for `.persist(` in `src/sot-engine/` — found 294 total call sites (2 production, 292 test).
6. Grep'd for `ingest_outputs(` in `src/sot-engine/` and `scripts/` — found 1 production + 8 test callers, 0 in scripts.
7. Compared GitNexus results against ground truth across all dimensions.

---
---

# GitNexus Call Chain Audit: Entrypoints to `orchestrator.py`

**Date:** 2026-03-02
**Target:** `src/sot-engine/orchestrator.py` — the main pipeline entry point
**Question:** Can GitNexus show call chains from entrypoints into the orchestrator? Are the edges in the graph even if processes aren't surfaced?

---

## What GitNexus Detected as Processes

Only **2 processes** touch the orchestrator, both shallow stubs:

| Process | Steps | Trace |
|---------|-------|-------|
| `Main → Fetchone` | 3 | main → ensure_schema → fetchone |
| `Main → _apply_migrations` | 3 | main → ensure_schema → _apply_migrations |

Both cover schema initialization — a minor startup step. The 3 core pipeline phases are absent from the process catalog.

---

## What the Graph Actually Contains (via manual `context()` chaining)

By querying `context()` for each symbol in sequence, the full call tree can be reconstructed. The graph **has the edges** — the process detector just doesn't assemble them.

### Path 1: Tool Execution Phase

```
main()                                           # orchestrator.py:1015
└─ _run_tools()                                  # orchestrator.py:564
   ├─ execute_batch()                            # execution.py
   │  └─ ToolTask, ExecutionConfig, LocalBackend # execution.py (classes)
   ├─ log_pipe()                                 # orchestrator.py
   └─ _default_output_path()                     # orchestrator.py
      ← DEAD END: subprocess.run(["make","analyze"]) not traced →
```

| Metric | Value |
|--------|-------|
| Files | `orchestrator.py` → `execution.py` |
| Depth reached | 3 (main → _run_tools → execute_batch) |
| Real depth | 5+ (→ subprocess → tool/analyze.py → cli_parser → envelope) |
| Boundary | `subprocess.run` severs chain to 18 tool analyzers |

### Path 2: Data Ingestion Phase

```
main()                                           # orchestrator.py:1015
└─ ingest_outputs()                              # orchestrator.py:812
   ├─ ensure_schema()                            # orchestrator.py:88
   ├─ load_payload()                             # orchestrator.py:185
   ├─ validate_payload()                         # orchestrator.py
   ├─ LayoutScannerAdapter (class)               # adapters/layout_adapter.py
   ├─ persist()                                  # adapters/base_adapter.py:265
   │  ├─ check_metadata()                        # persistence/quality.py
   │  ├─ validate_schema()                       # base_adapter.py
   │  ├─ ensure_lz_tables()                      # base_adapter.py
   │  ├─ validate_lz_schema()                    # base_adapter.py
   │  ├─ _do_persist()                           # base_adapter.py (abstract)
   │  │  ← DEAD END: 18 concrete overrides not linked →
   │  └─ _run_post_persist_quality()             # base_adapter.py
   ├─ ToolRunRepository (class)                  # repositories.py
   ├─ LayoutRepository (class)                   # repositories.py
   └─ DataQualityChecker (class)                 # quality.py
```

| Metric | Value |
|--------|-------|
| Files | `orchestrator.py` → `base_adapter.py` → `quality.py`, `repositories.py`, `layout_adapter.py` |
| Depth reached | 4 (main → ingest_outputs → persist → validate_schema/etc) |
| Real depth | 6+ (→ _do_persist → concrete adapter → entity creation → repo.insert → DuckDB) |
| Boundary | Abstract `_do_persist()` not resolved to 18 concrete adapters |

### Path 3: dbt Transformation Phase

```
main()                                           # orchestrator.py:1015
└─ run_dbt()                                     # orchestrator.py:942
   ├─ _resolve_dbt_cmd()                         # orchestrator.py
   ├─ _subprocess_run_with_retry()               # orchestrator.py
   │  ← DEAD END: subprocess.run(["dbt","run"]) not traced →
   └─ log_pipe()                                 # orchestrator.py
```

| Metric | Value |
|--------|-------|
| Files | `orchestrator.py` only (self-contained) |
| Depth reached | 3 (main → run_dbt → _subprocess_run_with_retry) |
| Real depth | 3+ (→ dbt run → 168 SQL models, Jinja/SQL not Python) |
| Boundary | `subprocess.run` severs chain to dbt models |

---

## Full `main()` Fan-Out (from `context()`)

GitNexus found **14 function calls + 10 class references** as outgoing edges from `main()`:

**Correct edges (production calls):**

| Callee | File | Role in Pipeline |
|--------|------|-----------------|
| `ensure_schema` | orchestrator.py | Schema initialization |
| `_get_or_create_collection_run` | orchestrator.py | Collection run setup |
| `_run_tools` | orchestrator.py | Phase 1: Tool execution |
| `_discover_outputs` | orchestrator.py | Output discovery |
| `ingest_outputs` | orchestrator.py | Phase 2: Data ingestion |
| `compute_run_quality` | orchestrator.py | Quality scoring |
| `run_dbt` | orchestrator.py | Phase 3: dbt transformation |
| `_safe_write_json` | orchestrator.py | Summary output |
| `_format_duration` | orchestrator.py | Utility |
| `_is_fallback_commit` | orchestrator.py | Commit validation |
| `_compute_content_hash` | orchestrator.py | Content hashing |
| `_default_output_path` | orchestrator.py | Path resolution |
| `get_backend` | execution.py | Execution backend factory |
| `mark_status` | repositories.py | Collection run finalization |

**False positive edges (name collisions with eval-repos):**

| Callee | Resolved To | Should Be |
|--------|-------------|-----------|
| `Path` | `src/tools/scc/eval-repos/real/click/src/click/types.py` | `pathlib.Path` (stdlib) |
| `connect` | `src/tools/symbol-scanner/eval-repos/synthetic/metaprogramming/meta.py` | `duckdb.connect` |
| `parse_args` | `src/tools/scc/eval-repos/real/click/tests/test_commands.py` | `argparse.parse_args` |
| `add_argument` | `src/tools/scc/eval-repos/real/click/src/click/parser.py` | `argparse.add_argument` |

**Class references (correct):**

| Class | File |
|-------|------|
| `ToolConfig` | orchestrator.py |
| `OrchestratorLogger` | orchestrator.py |
| `ToolPhaseError` | orchestrator.py |
| `ExecutionMode` | execution.py |
| `DockerConfig` | execution.py |
| `CollectionRunRepository` | repositories.py |

---

## Processes Detected vs. Graph Edges Available

| Pipeline Phase | Edges in Graph? | Process Detected? | Gap |
|---------------|-----------------|-------------------|-----|
| Schema init | Yes (main → ensure_schema → fetchone/_apply_migrations) | **Yes** (2 processes) | None |
| Collection run setup | Yes (main → _get_or_create_collection_run) | No | Process detection missed it |
| Tool execution | Yes (main → _run_tools → execute_batch) | No | Process detection missed it |
| Output discovery | Yes (main → _discover_outputs) | No | Process detection missed it |
| Data ingestion | Yes (main → ingest_outputs → persist → 7 callees) | No | Process detection missed it |
| Quality scoring | Yes (main → compute_run_quality) | No | Process detection missed it |
| dbt transformation | Yes (main → run_dbt → _subprocess_run_with_retry) | No | Process detection missed it |
| Status finalization | Yes (main → mark_status) | No | Process detection missed it |

**Score: 2 of 8 phases surfaced as processes (25%).** The graph contains edges for all 8 phases.

---

## Why the Process Detector Misses These

The 2 detected processes both follow a pattern: `main → ensure_schema → leaf_function`. The process detector appears to require a **cross-file terminal symbol** to form a process. For the orchestrator:

- `ensure_schema → fetchone` crosses into test code (fetchone is in `test_orchestrator.py`) — detected
- `ensure_schema → _apply_migrations` stays in orchestrator.py but _apply_migrations has no further calls — detected
- `main → _run_tools → execute_batch` crosses into `execution.py` but `execute_batch` has further calls — **not detected** (possibly filtered as non-terminal)
- `main → ingest_outputs → persist` crosses into `base_adapter.py` and has 7 outgoing calls — **not detected** (not a leaf)

**Hypothesis:** The process detection algorithm traces to **leaf nodes only** (symbols with no outgoing calls). Functions like `ingest_outputs`, `_run_tools`, and `run_dbt` that have rich fan-out are never terminals, so no process ends at them — and the paths through them to deeper leaves may exceed a depth limit.

---

## False Positive Analysis

6 outgoing edges from `main()` and `_run_tools()` resolve to eval-repos files:

| False Edge | Root Cause |
|-----------|------------|
| `Path` → click/types.py | Name collision: `pathlib.Path` vs Click's `Path` type |
| `connect` → meta.py | Name collision: `duckdb.connect` vs synthetic test fixture |
| `parse_args` → test_commands.py | Name collision: `argparse.parse_args` vs Click test |
| `add_argument` → click/parser.py | Name collision: `argparse.add_argument` vs Click parser |
| `isatty` → _winconsole.py | Name collision: stdlib `isatty` vs Click wrapper |
| `exists` → Complex.java | Name collision: `Path.exists()` vs Java method |

**Rate:** 6 false positives out of 24 total outgoing edges = **25% false positive rate** on `main()`. All caused by eval-repos containing common symbol names that shadow stdlib/third-party imports.

---

## Grades

| Dimension | Grade | Notes |
|-----------|-------|-------|
| **Graph edge accuracy** | **B+** | 18/24 outgoing edges from `main()` are correct; 6 are eval-repos false positives |
| **Call chain depth** | **B** | 3-4 hops traced correctly before hitting subprocess/abstract boundaries |
| **Process detection** | **F** | 2/8 pipeline phases surfaced; the 3 core phases (tools, ingest, dbt) all missed |
| **Graph-vs-process gap** | **Critical** | The graph has the data; the process layer fails to expose it |
| **False positive rate** | **D+** | 25% of outgoing edges are name collisions with eval-repos |

---

## Recommendations

1. **Exclude eval-repos from indexing** (or deprioritize). These directories contain third-party code (Click, picocli, joda-money) that creates massive false-positive pollution for common names like `Path`, `connect`, `parse_args`.
2. **Import-aware resolution:** When `from pathlib import Path` is in scope, don't resolve `Path` to `click/types.py:Path`. Use import context to disambiguate.
3. **Non-leaf process detection:** Extend process detection beyond leaf-terminal paths. High-fan-out orchestration functions like `main()` should generate processes for each major branch, not just paths that reach a leaf with zero outgoing calls.
4. **Depth limit increase:** If a depth limit is truncating traces before they reach the ingestion/persistence layer, increase it for high-fan-out entrypoints.

---

## Methodology

1. Ran `context(name="main", file_path="src/sot-engine/orchestrator.py")` — got 14 function calls + 10 class references.
2. Ran `context()` for each of the 3 major callees: `_run_tools`, `ingest_outputs`, `run_dbt` — got their outgoing calls.
3. Queried `query(query="orchestrator main pipeline ingest dbt")` — got 3 processes, only 2 touching orchestrator.
4. Ran Cypher for all STEP_IN_PROCESS edges where `filePath = orchestrator.py` — confirmed only 2 processes.
5. Compared graph edges (from context) against process catalog (from query/Cypher) to identify the detection gap.
6. Classified false positives by tracing eval-repos name collisions.
