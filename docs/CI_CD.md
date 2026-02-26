# CI/CD Pipeline

Project Caldera uses GitHub Actions with a branch promotion model: `develop → release → main`.

## Branching Strategy

```
feature/*  ──PR──►  develop  ──PR──►  release  ──PR──►  main  ──tag──►  vX.Y.Z
fix/*      ──PR──►  develop
tool/*/**  ──PR──►  develop
infra/*    ──PR──►  develop
```

| Branch | Purpose | Required Gates |
|--------|---------|----------------|
| `feature/*`, `fix/*`, `tool/*/**`, `infra/*` | Development | Gate 0 (preflight on push) |
| `develop` | Integration | Gate A |
| `release` | Pre-production staging | Gates A, B, C, D |
| `main` | Production-ready | Gates A, B (C, D already passed) |
| Tags `vX.Y.Z` | Releases cut from `main` | Gate E on `vX.0.0` only |

## Pipeline Gates

### Gate 0 — Preflight (feature branch push)

**File:** `.github/workflows/preflight.yml`
**Trigger:** Push to `feature/*`, `fix/*`, `tool/*/**`, `infra/*`
**Duration:** ~30s | **Cost:** Free

Runs `make compliance-preflight` for immediate structural feedback.

### Gate A — Fast Quality

**File:** `.github/workflows/ci.yml` → `quality` job
**Trigger:** Every PR to `develop`, `release`, or `main`
**Duration:** ~2 min | **Cost:** Free

| Check | Command |
|-------|---------|
| Compliance preflight | `make compliance-preflight` |
| Core unit tests | `pytest -m "not slow and not integration"` |
| Observability compliance | `python scripts/check_observability_compliance.py` |

### Gate B — Compliance Report

**File:** `.github/workflows/ci.yml` → `compliance-report` job
**Trigger:** PRs to `release` or `main`
**Duration:** ~10s | **Cost:** Free

Runs `make compliance-preflight` as a hard gate (must pass), then runs `make compliance` with `continue-on-error` to generate a full compliance report. Uploads JSON + MD reports as artifacts for release readiness assessment.

### Gate C — LOCAL Smoke Test

**File:** `.github/workflows/ci.yml` → `prod-smoke-local` job
**Trigger:** PRs to `release`
**Duration:** ~5-10 min | **Cost:** Free

Proves LOCAL production mode works: runs `make pipeline-eval` against `tests/fixtures/ci-repo/` with only `scc` and `layout-scanner` enabled and LLM off. Verifies `report.html` is generated.

### Gate D — BUNDLE Smoke Test

**File:** `.github/workflows/ci.yml` → `prod-smoke-bundle` job
**Trigger:** PRs to `release`
**Duration:** ~5-10 min | **Cost:** Free

Proves BUNDLE mode works: collects artifacts, ingests bundle, generates report. Same fixture repo and tool allowlist as Gate C.

### Gate E — Deep Tool Evaluation (LLM)

**File:** `.github/workflows/tool-evaluation-major.yml`
**Trigger:** Tag matching `vX.0.0` on `main`
**Duration:** ~30-45 min | **Cost:** ~$5-15 (LLM API)

Runs `make compliance-full` (analysis + programmatic eval + LLM eval + coverage). Protected by GitHub Environment `llm-eval` requiring manual approval.

### Release Workflow

**File:** `.github/workflows/release.yml`
**Trigger:** Tag push matching `v*`
**Duration:** ~30s | **Cost:** Free

Automatically creates a GitHub Release with a changelog when any version tag is pushed. Changelog groups commits by prefix (`Add`, `Fix`, `Update`, other). Gate E runs after the release is created and attaches evaluation artifacts to it.

Use `make release` to create and push tags locally:

```bash
make release                     # Next minor version (default)
make release RELEASE_TYPE=major  # Next major version
make release RELEASE_TYPE=patch  # Next patch version
```

The `make release` target enforces that you are on the `main` branch, computes the next version from the latest tag, and pushes an annotated tag to origin.

### Docker Images

**File:** `.github/workflows/docker-images.yml`
**Trigger:** Push to `main`, tag push `v*`, `workflow_dispatch`
**Duration:** ~10-20 min | **Cost:** Free

Builds and pushes all Docker images to GHCR (`ghcr.io/<owner>/caldera-*`). Uses a phased job chain:

1. **detect-changes** — On `main` pushes, diffs changed paths to determine which images need rebuilding. Tags and manual dispatch rebuild everything.
2. **build-bases** — Builds `caldera-python-base`, `caldera-java-base`, `caldera-dotnet-base` (skips unchanged).
3. **build-tools** — Matrix of 17 tool images, `max-parallel: 10`. Each receives `--build-arg BASE_IMAGE=ghcr.io/.../caldera-<base>-base:<tag>`.
4. **build-infra** — Builds `caldera-runner` and `caldera-orchestrator` (parallel with tools, no base dependency).

**Tagging:** `latest` on `main`, `sha-<short>` always, `1.2.3` / `1.2` / `1` on version tags.

**Pulling pre-built images:**

```bash
make docker-pull-all                    # Pull all from GHCR, tag locally
GHCR_REGISTRY=ghcr.io/my-org make docker-pull-all  # Custom registry
```

### Cloud Smoke Test

**File:** `.github/workflows/cloud-smoke.yml`
**Trigger:** `workflow_dispatch` or tag `vX.0.0`
**Duration:** ~30-45 min | **Cost:** ~$0.10 (Hetzner VM)

Spins up a Hetzner VM, runs full pipeline, downloads results, destroys VM. Protected by GitHub Environment `cloud`.

## GitHub Environments

| Environment | Secrets | Protection |
|-------------|---------|-----------|
| `llm-eval` | `ANTHROPIC_API_KEY` | Required reviewers (manual approval) |
| `cloud` | `HCLOUD_TOKEN`, `SSH_PRIVATE_KEY` | Required reviewers (manual approval) |

## Caching

| What | Key | Used by |
|------|-----|---------|
| Project `.venv/` | `core-venv-{os}-{hash(requirements.txt)}` | All jobs |
| pip cache | `pip-{os}-{hash(requirements.txt)}` | All jobs |
| Tool venvs | `tool-venvs-{os}-{hash(tool requirements)}` | Gates C, D, E |
| Tool binaries (scc, git-sizer, gitleaks, trivy) | `tool-bins-{os}-{hash(tool Makefiles)}` | Gates C, D, E |

## Branch Protection Rules

**`develop`:** Require PR, status check `"Gate A — Quality"`, no force push.

**`release`:** Require PR (from `develop`), status checks: `"Gate A — Quality"`, `"Gate B — Compliance Report"`, `"Gate C — LOCAL Smoke"`, `"Gate D — BUNDLE Smoke"`. No force push.

**`main`:** Require PR (from `release`), status checks: `"Gate A — Quality"`, `"Gate B — Compliance Report"`, `"Promotion Policy"`. No force push, no deletion. The `"Promotion Policy"` check enforces that PRs to `main` originate from the `release` branch.

## CI Fixture Repo

`tests/fixtures/ci-repo/` is a minimal repository committed in-tree for offline, deterministic CI smoke tests. It contains just enough files for `layout-scanner` to analyze.

## Infrastructure as Code

GitHub repository settings (branches, branch protection, environments) are managed via Terraform in `infra/github/`. This keeps settings versioned and reproducible.

```bash
make github-setup    # One-time: terraform init
make github-plan     # Preview changes
make github-apply    # Apply changes (requires GITHUB_TOKEN)
```

**What's managed:** `develop` and `release` branch creation, branch protection rules for all three long-lived branches, and `llm-eval` / `cloud` environments with optional reviewer gates.

**What's NOT managed:** Environment secrets (`ANTHROPIC_API_KEY`, `HCLOUD_TOKEN`, `SSH_PRIVATE_KEY`) — add these manually in GitHub UI.

See [infra/github/README.md](../infra/github/README.md) for full details.

## Adding a New Gate

1. Add a new job to `.github/workflows/ci.yml` (or create a separate workflow)
2. Use the `caldera-setup` composite action for consistent environment setup
3. Add `setup-tools: "true"` if the gate needs tool binaries
4. Update branch protection rules to require the new check name
5. Update this document
