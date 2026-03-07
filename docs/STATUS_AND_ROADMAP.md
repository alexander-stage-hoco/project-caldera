# Project Caldera — Status & Forward Roadmap

## Current State: v0.14.0-dev (2026-03-06)

Core platform is production-ready. All 18 tools pass compliance, all 3 production modes work (LOCAL, BUNDLE, DOCKERIZED), CI/CD has 5 gates with trust score enforcement, cloud runs on Hetzner, and the dbt warehouse has 168 models + 2 snapshots + 23 analyses.

### What's Complete

- 18/18 tools with adapters, schemas, judges, tests, and Docker images
- Full E2E pipeline: tools → adapters → DuckDB → dbt → reports
- 3 production modes (LOCAL, BUNDLE, DOCKERIZED)
- CI/CD gates (0, A, B, C, E) with branch promotion (develop → release → main)
- Cloud infrastructure (Hetzner Terraform)
- Insights component with 43 report sections covering all 6 product spec deliverables
- 95 SQL insight queries with 84 Jinja2 templates (HTML + Markdown)
- Evidence & Claim framework — full end-to-end chain:
  - EvidenceCollector (6 categories: complexity, security, coupling, coverage, ownership, quality)
  - ClaimGenerator (7 rules + LLM synthesis)
  - RiskAggregator (5 patterns with severity escalation)
  - Persistence (lz_evidence, lz_claims, lz_risks, lz_warnings)
  - Report sections: EvidencePack, ClaimRegister, RiskRegister
- Symbol-scanner integration: BlastRadius, CouplingAnalysis, CouplingDebt, ComponentInventory, ImportDependencies, CircularDependencies sections
- Cross-tool compound queries: composite risk scoring, coverage gap analysis, complex+smelly, complex+vulnerable
- Sampling rationale with composite risk scoring
- Rewrite risk assessment (structural vs addressable constraint detection)
- Artifact bundle workflow + results export
- LLM evaluation infrastructure (BaseJudge, observability)
- GitHub IaC for branch protection and environments
- All 18 tools have full dbt staging → mart → rollup models
- 168 dbt models (51 staging + 117 marts) + 2 snapshots + 23 analyses
- `unified_directory_metrics` mart for cross-tool directory analysis
- dbt snapshots for trend analysis (unified_run_summary, unified_repo_metrics)
- Run-over-run comparison and file-level regression detection analyses
- Stakeholder report profiles (CTO, Investor, CEO) with tailored section selections
- Unified `caldera` CLI with 10 subcommand groups
- Cloud operational improvements: cost tracking, orphan VM cleanup, server presets

### Recently Completed (v0.13 → v0.14)

| Feature | Description |
|---------|-------------|
| Trust score in reports | Trust score displayed in executive summary with trend indicator |
| Warning count wired | Actual warning count from insights pipeline persisted (was hardcoded 0) |
| CI trust gate | Gate C validates trust score >= 50 after pipeline runs |
| Delta lead section | Delta summary promoted to priority 1 (lead actionable section) |
| Trust score trend | Executive summary shows trust score trajectory across runs |
| Adapter boundary tests | Schema-valid-but-entity-fails gap covered by integration tests |
| Product spec reconciled | INSIGHTS_PRODUCT_SPEC.md updated: 9→18 tools, 12→43 sections, gap analysis refreshed |

---

## Forward Roadmap

### Phase 1: Deliverables & Polish (v0.14.x — near-term)

**Goal:** Produce stakeholder-ready outputs and improve operational maturity.

| Item | Description | Priority |
|------|-------------|----------|
| PDF report generation | WeasyPrint integration for formal deliverables (CTO detailed, Investor summary, CEO one-pager) | P1 |
| Incremental pipeline | Content-hash cache per tool (hash repo state + tool config → skip if unchanged), `--force` override | P2 |
| Orchestrator refactor | Split 1,454-line orchestrator.py into phase modules (tool_execution, ingestion, dbt_phase, reporting) | P2 |
| Multi-platform Docker | arm64 builds for M-series Macs, multi-arch manifests on GHCR | P3 |

### Phase 2: Close the Loop (v0.15 — mid-term)

**Goal:** Go from "analysis" to "action."

| Item | Description | Priority |
|------|-------------|----------|
| Policy Layer v1 | Configurable quality gates per repo (trust score thresholds, zero-critical-vuln policies), policy waivers with expiry, drift detection | P2 |

### Phase 3: Scale (v1.0 — longer-term)

**Goal:** Multi-repo and enterprise readiness.

| Item | Description | Priority |
|------|-------------|----------|
| Portfolio Layer | Multi-repo aggregation (per-repo DBs + portfolio aggregation layer), cross-repo comparison dashboards, comparative health scoring | P1 |
| LLM provider abstraction | Support Claude, GPT-4, local models for judge evaluations via provider-agnostic interface | P2 |
| Results retention | TTL-based cleanup with configurable keep-last-N | P3 |

### Open Design Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| PDF engine | WeasyPrint vs wkhtmltopdf vs Playwright | WeasyPrint (pure Python, good CSS support) |
| Multi-repo storage | Single DuckDB vs per-repo DBs with federation | Per-repo DBs + portfolio aggregation layer |
| Results export format | Git LFS for DuckDB vs Parquet export | Parquet export (portable, no LFS dependency) |

---

## Gap Analysis

All 6 product spec deliverables have implementations. Remaining gaps:

| Gap | Status | Notes |
|-----|--------|-------|
| PDF report generation | Not started | Formal deliverable format for stakeholders |
| Multi-platform Docker | Not started | amd64 only, no arm64 |
| Incremental pipeline | Not started | No skip-unchanged-tools capability |
| Policy Layer | Not started | Configurable quality gates, waivers, drift tracking |
| Portfolio Layer | Not started | Multi-repo dashboards, cross-repo aggregation |

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
