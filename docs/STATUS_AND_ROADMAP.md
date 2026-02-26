# Project Caldera — Status & Forward Roadmap

## Current State: v0.12.0-dev (2026-02-26)

Core platform is production-ready. All 18 tools pass compliance, all 3 production modes work (LOCAL, BUNDLE, DOCKERIZED), CI/CD has 5 gates, cloud runs on Hetzner, and the dbt warehouse has 170+ models.

### What's Complete

- 18/18 tools with adapters, schemas, judges, tests, and Docker images
- Full E2E pipeline: tools → adapters → DuckDB → dbt → reports
- 3 production modes (LOCAL, BUNDLE, DOCKERIZED)
- CI/CD gates (0, A, B, C, E) with branch promotion (develop → release → main)
- Cloud infrastructure (Hetzner Terraform)
- Insights component with 20+ report sections
- Artifact bundle workflow + results export
- LLM evaluation infrastructure (BaseJudge, observability)
- GitHub IaC for branch protection and environments
- All 18 tools have full dbt staging → mart → rollup models
- `unified_directory_metrics` mart for cross-tool directory analysis
- dbt snapshots for trend analysis (unified_run_summary, unified_repo_metrics)
- Run-over-run comparison and file-level regression detection analyses

### Gap Analysis

#### 1. Insights Deliverable Coverage (biggest gap)

Per `docs/INSIGHTS_PRODUCT_SPEC.md`, deliverable coverage is partial:

| Deliverable | Coverage | Missing |
|-------------|----------|---------|
| Code Quality Report | ~60% | Sampling rationale, pattern narrative |
| Technical Evidence Pack | ~40% | Evidence IDs, location references |
| Risk Register | ~40% | "Triggered by" reasoning |
| Component Inventory | ~30% | Responsibilities, interactions |
| Rewrite Risk Memo | ~20% | Structural vs addressable assessment |
| Claim Register | 0% | Entire capability |

Missing capabilities: evidence-claim linking, component boundary detection, sampling rationale, code ownership integration.

#### 2. Execution Abstraction Incomplete

- Only `LocalBackend` implemented in `src/sot-engine/execution.py`
- DOCKER/VM deferred by design (bundle-first architecture handles it externally via `docker_runner.py` and `cloud-run.sh`)

#### 3. No Unified CLI

- 20+ scripts scattered across `scripts/` with no single entry point
- Inconsistent error handling and logging across scripts

#### 4. Docker Gaps

- No multi-platform builds (amd64 only, no arm64 for M-series Macs)
- No HEALTHCHECK directives in tool Dockerfiles
- No image size tracking or optimization targets

---

## Forward Roadmap

### Mid-term: v0.13 – v1.0 — Insights Maturity

**Goal:** Close the deliverable gaps in the insights product spec.

- Evidence-claim linking:
  - Structured claim register with traceable evidence IDs
  - Each insight maps to specific tool findings with file:line references
- Component boundary detection:
  - Leverage symbol-scanner call graphs for coupling/cohesion analysis
  - Identify logical components beyond directory structure
- Code ownership integration:
  - Wire git-blame-scanner data into risk scoring
  - Bus factor per component, knowledge silo detection
  - New report sections: authorship concentration, knowledge risk heatmap
- Sampling rationale:
  - Risk-driven analysis focus instead of equal treatment of all files
  - Prioritize files with high complexity + low coverage + recent churn
- Report format expansion:
  - Markdown output for CI integration
  - PDF generation for formal deliverables

### Longer-term: v1.x — Platform Polish

**Goal:** Improve developer experience and operational maturity.

- Unified `caldera` CLI:
  - Single entry point with subcommands (analyze, report, collect, export, cloud, compliance)
  - Replace 20+ standalone scripts
  - Consistent error handling, logging, and progress feedback
- Multi-platform Docker:
  - arm64 support for M-series Macs
  - `platforms: [linux/amd64, linux/arm64]` in docker-images.yml
- Incremental pipeline:
  - Skip unchanged tools on re-analysis of same repo
  - Content-hash-based cache invalidation
- Cloud operational improvements:
  - Embed Hetzner API cost per run in manifests
  - Scheduled job to destroy orphaned VMs (TTL labels)
  - Expose server type presets (cx22 for CI, cx42 for heavy workloads)
- Execution abstraction completion:
  - Evaluate whether DOCKER/VM backends in execution.py add value vs current external scripts
  - If so, implement; if not, document the decision and remove placeholders

---

## Tool Maturity Matrix

All 18 tools are fully mature with compliance, adapters, dbt models, and Docker images.

| Tool | Compliance | Adapter | dbt (staging/rollups) | Docker | Status |
|------|:---:|:---:|:---:|:---:|---|
| coverage-ingest | ✓ | ✓ | ✓ | ✓ | Mature |
| dependensee | ✓ | ✓ | ✓ | ✓ | Mature |
| devskim | ✓ | ✓ | ✓ | ✓ | Mature |
| dotcover | ✓ | ✓ | ✓ | ✓ | Mature |
| git-blame-scanner | ✓ | ✓ | ✓ | ✓ | Mature |
| git-fame | ✓ | ✓ | ✓ | ✓ | Mature |
| git-sizer | ✓ | ✓ | ✓ | ✓ | Mature |
| gitleaks | ✓ | ✓ | ✓ | ✓ | Mature |
| layout-scanner | ✓ | ✓ | ✓ | ✓ | Mature |
| lizard | ✓ | ✓ | ✓ | ✓ | Mature |
| pmd-cpd | ✓ | ✓ | ✓ | ✓ | Mature |
| roslyn-analyzers | ✓ | ✓ | ✓ | ✓ | Mature |
| scancode | ✓ | ✓ | ✓ | ✓ | Mature |
| scc | ✓ | ✓ | ✓ | ✓ | Mature |
| semgrep | ✓ | ✓ | ✓ | ✓ | Mature |
| sonarqube | ✓ | ✓ | ✓ | ✓ | Mature |
| symbol-scanner | ✓ | ✓ | ✓ | ✓ | Mature |
| trivy | ✓ | ✓ | ✓ | ✓ | Mature |
