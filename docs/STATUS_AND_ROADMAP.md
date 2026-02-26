# Project Caldera — Status & Forward Roadmap

## Current State: v0.12.0-dev (2026-02-26)

Core platform is production-ready. All 18 tools pass compliance, all 3 production modes work (LOCAL, BUNDLE, DOCKERIZED), CI/CD has 5 gates, cloud runs on Hetzner, and the dbt warehouse has 168 models + 2 snapshots + 25 analyses.

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
- 168 dbt models (51 staging + 117 marts) + 2 snapshots + 25 analyses
- `unified_directory_metrics` mart for cross-tool directory analysis
- dbt snapshots for trend analysis (unified_run_summary, unified_repo_metrics)
- Run-over-run comparison and file-level regression detection analyses

### Gap Analysis

All 6 product spec deliverables now have implementations. Remaining gaps are platform-level:

| Gap | Status | Notes |
|-----|--------|-------|
| PDF report generation | Not started | Formal deliverable format for stakeholders |
| Stakeholder report variants | Not started | CTO/Investor/CEO tailored section selections per product spec Appendix A |
| Unified CLI | Not started | 20+ scripts with no single entry point |
| Execution abstraction | Deferred | Only LocalBackend; DOCKER/VM handled externally |
| Multi-platform Docker | Not started | amd64 only, no arm64 |
| Incremental pipeline | Not started | No skip-unchanged-tools capability |

---

## Forward Roadmap

### Near-term: v0.13 — Stakeholder Reports

**Goal:** Deliver tailored reports for different audiences.

- Stakeholder report variants (CTO, Investor, CEO per product spec Appendix A)
- PDF generation for formal deliverables
- Update product spec gap analysis table to reflect 100% coverage

### Mid-term: v0.14–v1.0 — Platform Polish

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
