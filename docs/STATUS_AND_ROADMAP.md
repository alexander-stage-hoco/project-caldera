# Project Caldera — Status & Forward Roadmap

## Current State: v0.14.0-dev (2026-03-01)

Core platform is production-ready. All 18 tools pass compliance, all 3 production modes work (LOCAL, BUNDLE, DOCKERIZED), CI/CD has 5 gates with trust score enforcement, cloud runs on Hetzner, and the dbt warehouse has 168 models + 2 snapshots + 23 analyses.

### What's Complete

- 18/18 tools with adapters, schemas, judges, tests, and Docker images
- Full E2E pipeline: tools → adapters → DuckDB → dbt → reports
- 3 production modes (LOCAL, BUNDLE, DOCKERIZED)
- CI/CD gates (0, A, B, C, E) with branch promotion (develop → release → main)
- Cloud infrastructure (Hetzner Terraform)
- Insights component with 42 report sections covering all 6 product spec deliverables
- 95 SQL insight queries with 84 Jinja2 templates (HTML + Markdown)
- Evidence & Claim framework (entities, builder, collector, risk aggregator, claim generator)
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

### Gap Analysis

All 6 product spec deliverables have implementations. Remaining gaps:

| Gap | Status | Notes |
|-----|--------|-------|
| PDF report generation | Not started | Formal deliverable format for stakeholders |
| Multi-platform Docker | Not started | amd64 only, no arm64 |
| Incremental pipeline | Not started | No skip-unchanged-tools capability |
| Action Layer | Not started | Risk register → assignable actions → ticket integration |
| Policy Layer | Not started | Configurable quality gates, waivers, drift tracking |
| Portfolio Layer | Not started | Multi-repo dashboards, cross-repo aggregation |

---

## Forward Roadmap

### Near-term: v0.14 — Platform Polish

**Goal:** Improve operational maturity and developer experience.

- PDF generation for formal deliverables
- Multi-platform Docker (arm64 for M-series Macs)
- Incremental pipeline (skip unchanged tools, content-hash cache)

### Mid-term: v0.15–v1.0 — Action & Policy Layers

**Goal:** Close the loop from analysis to action.

- **Action Layer**: Assignable actions from risk register, owner/SLA tracking, ticket integration (GitHub Issues, Jira)
- **Policy Layer**: Configurable quality gates per repo/team, release/PR policy enforcement, policy waivers with expiry, policy drift tracking
- **Portfolio Layer**: Multi-repo dashboards, cross-repo aggregation, comparative health scoring

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
