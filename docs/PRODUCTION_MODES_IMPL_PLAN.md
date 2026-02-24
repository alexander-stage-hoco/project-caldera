# Production Modes — Implementation Plan

**Date:** 2026-02-19 (revised)
**Depends on:** [PRODUCTION_MODES.md](PRODUCTION_MODES.md)

---

## Current State

### What's done

| Item | Status | Files |
|------|--------|-------|
| LOCAL mode (Mode 1) | **Working** | `orchestrator.py`, `Makefile` (`make analyze`) |
| BUNDLE mode (Mode 2) | **Working** | `scripts/collect_artifacts.py`, `scripts/analyze_bundle.py`, `Makefile` (`make collect`, `make analyze-bundle`) |
| Hetzner Terraform infra | **Built + hardened** | `infra/main.tf`, `infra/cloud-init.yml`, `infra/run-analysis.sh` |
| Cloud wrapper script | **Built + hardened** | `scripts/cloud-run.sh` |
| Makefile cloud targets | **Built + hardened** | `Makefile` (`cloud-setup`, `cloud-run`, `cloud-destroy`) |
| Terraform config template | **Done** | `infra/terraform.tfvars.example`, `infra/.gitignore` |
| DOCKERIZED mode (Mode 3) | **Wave 2 done** | `docs/PRODUCTION_MODES.md` (bundle-first architecture) |
| Tool Dockerfiles (18) | **Done (17 of 18)** | `docker/caldera-{python,java,dotnet}-base/`, `src/tools/*/Dockerfile` (sonarqube deferred to Phase 4) |
| `ExecutionBackend` refactor | **Deprioritized** | Not needed for bundle-first approach |

### Key decisions made

1. **Bundle-first**: DOCKERIZED mode reuses the bundle layout — runner writes bundle, orchestrator ingests in BUNDLE mode. No `ExecutionBackend` refactor needed.
2. **Hetzner + Terraform**: Chosen over 15 alternatives. ~$0.004/run on CX32.
3. **Cloud runner uses LOCAL mode on VM**: `infra/run-analysis.sh` runs `make analyze` (not Docker) on the Hetzner VM. This is the v1 cloud path.
4. **coverage-ingest skipped by default** in `make collect` (requires explicit `--coverage-file`).
5. **Canonical manifest**: `collect_artifacts.py` defines the schema; cloud runner aligns with it.

---

## What remains — ordered by priority

### Phase 1: Validate Hetzner cloud path (next)

The infra is built but untested. This phase proves the end-to-end cloud workflow.

| # | Task | Effort | How to test |
|---|------|--------|-------------|
| 1.1 | Fill in `infra/terraform.tfvars` (token + caldera repo URL) | 5 min | — |
| 1.2 | `make cloud-setup` (terraform init) | 1 min | Exits 0 |
| 1.3 | `make cloud-run REPO=https://github.com/kelseyhightower/nocode` | 15 min | Results appear in `infra/results/` |
| 1.4 | Verify results: DuckDB queryable, manifest.json valid, report HTML opens | 5 min | `duckdb infra/results/*/database/caldera_sot.duckdb "SELECT count(*) FROM lz_tool_runs"` |
| 1.5 | `make cloud-run REPO=<medium-repo> CLOUD_SERVER=cx42` | 20 min | Full pipeline completes |
| 1.6 | Fix any issues found during 1.3–1.5 | Variable | — |

**Acceptance:** A single `make cloud-run REPO=<url>` creates a Hetzner VM, runs the full pipeline, downloads results, destroys the VM, and you can query the DuckDB + open the report locally.

#### Known risks to watch for

- **SSH key**: Terraform expects `~/.ssh/id_ed25519`. If your key is different, update `terraform.tfvars`.
- **cloud-init timing**: The VM may not have finished package installation when `run-analysis.sh` executes. The Terraform `null_resource` has a `time_sleep` dependency, but timing may need tuning.
- **Tool failures on fresh VM**: Some tools may need system packages not in `cloud-init.yml` (e.g., `clang` for lizard on certain repos). The `CONTINUE_ON_TOOL_FAILURE=1` flag handles graceful degradation.
- **get_latest_run_pk.py**: The cloud runner calls this script to find the run PK after `make analyze`. Verify this script exists and works.

---

### Phase 2: Harden cloud path

After the basic flow works, improve reliability and UX.

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 2.1 | ~~Add `--skip` passthrough for `SKIP_TOOLS` in cloud-run.sh~~ | ~~Medium~~ | **Done** |
| 2.2 | ~~Add `ANTHROPIC_API_KEY` passthrough for LLM eval on VM~~ | ~~Medium~~ | **Done** |
| 2.3 | ~~Better error reporting: capture tool-level failures in manifest~~ | ~~Medium~~ | **Done** |
| 2.4 | ~~Retry logic for transient cloud-init/SSH failures~~ | ~~Low~~ | **Done** |
| 2.5 | ~~Add `make cloud-status` to check running servers~~ | ~~Low~~ | **Done** |
| 2.6 | ~~Add timing breakdown to manifest (per-tool durations from DuckDB)~~ | ~~Low~~ | **Done** |

---

### Phase 3: Tool Dockerfiles (future — enables Mode 3)

This phase is only needed if you want the fully DOCKERIZED mode (Mode 3). The cloud path (Phase 1–2) already works without it by running tools natively on the VM.

| # | Task | Effort |
|---|------|--------|
| 3.1 | ~~Base Python image (`docker/caldera-python-base/Dockerfile`)~~ | **Done** |
| 3.2 | ~~layout-scanner + scc Dockerfiles + native-vs-Docker output comparison~~ | **Done** |
| 3.3 | ~~Remaining 17 tool Dockerfiles~~ | **Done** |
| 3.4 | ~~`make docker-build-tools` target~~ | **Done** |
| 3.5 | ~~`make docker-test-tool TOOL=<name> REPO=<path>` target~~ | **Done** |
| 3.6 | ~~`scripts/compare_tool_outputs.py` (ignore timestamps)~~ | **Done** |

**Acceptance:** All 18 tools produce matching output in Docker vs native.

---

### Phase 4: Dockerized runner + compose stack (future — Mode 3)

Only after Phase 3. Uses bundle-first architecture from PRODUCTION_MODES.md.

| # | Task | Effort |
|---|------|--------|
| 4.1 | Runner Dockerfile (dispatches tool containers, writes bundle) | 4 hrs |
| 4.2 | Orchestrator Dockerfile (BUNDLE-mode ingestion only, no docker.sock) | 2 hrs |
| 4.3 | `docker-compose.yml` (runner → orchestrator, shared volumes) | 2 hrs |
| 4.4 | `caldera-run` wrapper script | 2 hrs |
| 4.5 | Results repository export (`ResultsExporter` + git push) | 4 hrs |

**Acceptance:** `caldera-run --repo <url>` runs the full pipeline in containers and produces a queryable results directory.

---

### Phase 5: Results repository

| # | Task | Effort |
|---|------|--------|
| 5.1 | ~~Git results repo export (commit + push after run)~~ | **Done** |
| 5.2 | ~~`index.json` catalog of all runs~~ | **Done** |
| 5.3 | ~~DuckDB handling: Git LFS~~ | **Done** (Git LFS tracking for `*.duckdb`) |

---

## Local Testing Strategy

### Test the cloud path on your laptop (Phase 1)

```bash
# 1. Prerequisites
brew install terraform
cp infra/terraform.tfvars.example infra/terraform.tfvars
# Edit terraform.tfvars: hcloud_token, caldera_repo_url

# 2. Initialize
make cloud-setup

# 3. Smoke test (tiny repo, fast)
make cloud-run REPO=https://github.com/kelseyhightower/nocode

# 4. Check results
ls infra/results/
duckdb infra/results/*/database/caldera_sot.duckdb "SELECT tool_name, count(*) FROM lz_tool_runs GROUP BY 1"

# 5. Real test (medium repo, bigger server)
make cloud-run REPO=https://github.com/pallets/flask CLOUD_SERVER=cx42

# 6. Debug mode (keep server alive)
make cloud-run REPO=https://github.com/pallets/flask KEEP_SERVER=1
# SSH in: ssh root@<ip>
# When done: make cloud-destroy
```

### Test the local path (already working)

```bash
# Basic local run
make analyze REPO=/path/to/repo

# Bundle workflow
make collect REPO=/path/to/repo
make analyze-bundle REPO=/path/to/repo BUNDLE=artifacts/<repo-id>/<run-id>
```

### Test future Docker mode (Phase 3+)

```bash
# Single tool
make docker-build-tool TOOL=scc
make docker-test-tool TOOL=scc REPO=/path/to/repo

# Full compose stack
./caldera-run --repo https://github.com/org/target --results-dir /tmp/results
```

---

## Cost Reference

| Scenario | Server | Time | Cost |
|----------|--------|------|------|
| Tiny repo (nocode) | CX32 | ~5 min | ~$0.001 |
| Small Python project (~500 files) | CX32 | ~10 min | ~$0.002 |
| Medium project (~5k files) | CX32 | ~15 min | ~$0.004 |
| Large project (~20k files) | CX42 | ~25 min | ~$0.010 |
| Very large project + SonarQube | CX52 | ~45 min | ~$0.037 |

All costs are Hetzner CX-series (shared vCPU). Billing is per-hour, minimum 1 hour.

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| SSH key mismatch | Terraform can't connect to VM | Override in `terraform.tfvars` |
| cloud-init race condition | Tools fail because packages not yet installed | `time_sleep` dependency in Terraform; can increase delay |
| Tool failures on VM (missing deps) | Partial results | `CONTINUE_ON_TOOL_FAILURE=1` already set; review logs |
| DuckDB too large for results download | Slow SCP transfer | Skip tools for small runs; use `SKIP_TOOLS` |
| Hetzner API rate limits | Terraform apply fails | Unlikely at our scale; retry manually |
| VM left running (forgot to destroy) | Ongoing charges | Default is auto-destroy; `KEEP_SERVER=1` requires explicit `make cloud-destroy` |

---

## Summary

| Phase | What | Status | Effort |
|-------|------|--------|--------|
| **1** | Validate Hetzner cloud path | **Tested (Flask, Feb 19)** | 1 hr (mostly waiting) |
| **2** | Harden cloud path | **Hardened (8 fixes)** | 1 day |
| **3** | Tool Dockerfiles | **Done** (3 bases + 17 tools) | 2 days |
| **4** | Dockerized compose stack | Future | 2 days |
| **5** | Results repository | **Done** | 0.5 day |

**We are on track.** Phase 1 (cloud via Hetzner) is fully built and ready for your first test run. Phases 3–5 (full DOCKERIZED mode) are design-only and deferred — they're not needed for production use of LOCAL + BUNDLE + cloud.
