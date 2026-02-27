# Cloud Analysis Guide for Large Repos

Run the full Caldera analysis pipeline on an ephemeral Hetzner Cloud VM. This guide covers the complete workflow — from first-time setup through server sizing, execution, monitoring, and cost management — with a focus on large real-world repositories.

## When to Use Cloud vs Local

| Scenario | Recommended mode |
|----------|-----------------|
| Quick analysis of a small repo on your machine | Local (`make analyze`) |
| Repo requires tools you don't have installed locally | Cloud |
| Large repo that would take 30+ minutes locally | Cloud |
| CI/CD integration or automated analysis | Cloud |
| Debugging tool issues interactively | Local |

Cloud analysis is especially useful when the target repo is already hosted remotely — the VM clones directly from GitHub/GitLab, avoiding a local clone + upload step.

## Prerequisites

Before your first cloud run, ensure you have:

- [ ] **Terraform >= 1.5** — `brew install terraform` (verify: `terraform --version`)
- [ ] **SSH key pair** — `ls ~/.ssh/id_ed25519` (generate: `ssh-keygen -t ed25519`)
- [ ] **Hetzner Cloud account** — [console.hetzner.cloud](https://console.hetzner.cloud)
- [ ] **Hetzner API token** (read/write) — Console → Project → Security → API Tokens
- [ ] **`.env` file** configured with `HCLOUD_TOKEN` (see `.env.example`)

## One-Time Setup

```bash
# 1. Create terraform.tfvars from the example
cp infra/terraform.tfvars.example infra/terraform.tfvars

# 2. Edit infra/terraform.tfvars — fill in:
#    hcloud_token     = "your-hetzner-api-token"
#    caldera_repo_url = "https://github.com/yourorg/caldera.git"

# 3. Initialize Terraform
make cloud-setup
```

That's it. The `terraform.tfvars` file is gitignored and persists across runs.

## Server Sizing

Choose a server preset based on your repository's characteristics. The defaults work well for most repos; upsize when you have many files or deep git history.

| Repo profile | Example | Preset | Type | vCPU | RAM | Rate |
|---|---|---|---|---|---|---|
| Small (<50 files, <1k commits) | utility library | `small` | cx23 | 2 | 4 GB | EUR 0.007/hr |
| Medium (<500 files, <10k commits) | typical web app | `medium` | cx33 | 4 | 8 GB | EUR 0.013/hr |
| Large (<5k files, <50k commits) | major framework | `large` | cx43 | 8 | 16 GB | EUR 0.025/hr |
| Very large (5k+ files, 100k+ commits) | monorepo | `xlarge` | cx53 | 16 | 32 GB | EUR 0.050/hr |

**Key factors that increase resource needs:**

- **File count** — more files means more per-file analysis across all tools
- **Git history depth** — git-fame, git-blame-scanner, and gitleaks scan the full commit log
- **Language diversity** — each language activates additional analysis rules in tools like semgrep, lizard, and scc

Use preset names directly with `CLOUD_SERVER`:

```bash
make cloud-run REPO=https://github.com/org/repo CLOUD_SERVER=large
```

All types use shared vCPU (Intel). Pricing is per-hour with a 1-hour minimum billing increment, so a typical run costs between EUR 0.007 and EUR 0.050 regardless of actual duration.

## Clone Depth Strategy

By default, the cloud VM performs a full `git clone`. For large repos with deep history, a shallow clone can significantly reduce clone time and disk usage.

**When to use `CLONE_DEPTH`:**

| Tool | Needs full history? | Impact of shallow clone |
|------|---|---|
| git-fame | Yes — scans all commits for contributor stats | Incomplete/inaccurate results |
| git-blame-scanner | Yes — needs full blame history | May attribute all lines to latest commit |
| gitleaks | Yes — scans commit diffs for secrets | Misses secrets in older commits |
| git-sizer | Yes — measures repo history size | Underreports repository size |
| All other tools | No — analyze working tree only | No impact |

**Recommendation:**

- For security audits or contributor analysis: use full clone (default)
- For code quality only (complexity, duplication, coverage): use `CLONE_DEPTH=1` and skip history tools

```bash
# Shallow clone + skip history-dependent tools
make cloud-run \
    REPO=https://github.com/org/large-monorepo \
    CLONE_DEPTH=1 \
    SKIP_TOOLS=git-fame,git-blame-scanner,gitleaks,git-sizer
```

> **Note:** `CLONE_DEPTH` is passed to `git clone --depth` on the VM. The target repo must be accessible from the VM (public URL or SSH with deployed keys).

## Running the Analysis

**Basic run:**

```bash
make cloud-run REPO=https://github.com/pallets/flask
```

**Full options:**

```bash
make cloud-run \
    REPO=https://github.com/org/large-repo \
    CLOUD_SERVER=large \
    SKIP_TOOLS=sonarqube,trivy \
    MAX_PARALLEL=8 \
    PIPELINE_LLM=0 \
    KEEP_SERVER=1
```

**Option reference:**

| Option | Default | Purpose |
|--------|---------|---------|
| `REPO` | (required) | Git URL of the target repository |
| `CLOUD_SERVER` | `medium` (cx33) | Server preset or raw Hetzner type |
| `SKIP_TOOLS` | (none) | Comma-separated tools to skip |
| `MAX_PARALLEL` | `4` | Max parallel tool execution |
| `PIPELINE_LLM` | `0` | Set to `1` to enable LLM evaluation (needs `ANTHROPIC_API_KEY`) |
| `KEEP_SERVER` | (unset) | Set to `1` to keep VM alive after run |
| `CLONE_DEPTH` | (full) | Shallow clone depth |
| `CLOUD_RESULTS` | `infra/results` | Local directory for downloaded results |

You can also invoke the script directly for more control:

```bash
./scripts/cloud-run.sh https://github.com/org/repo \
    --server large \
    --skip sonarqube,trivy \
    --parallel 8 \
    --keep-server
```

## What Happens During the Run

A typical cloud run proceeds through these phases:

```
Phase                        Approximate duration
─────────────────────────────────────────────────
1. Terraform apply           ~30s
   Creates Hetzner VM

2. Cloud-init bootstrap      ~1-2 min
   Installs git, python3, pip, venv, make, curl, jq
   Clones Caldera project to /opt/caldera/project

3. SSH connection             ~30s (up to 5 min timeout)
   Terraform connects and uploads run-analysis.sh

4. Caldera setup              ~1-2 min
   Creates Python venv, installs requirements.txt

5. Target repo clone          Varies (seconds to minutes)
   git clone to /tmp/target-repo

6. Tool setup                 ~2-3 min
   Per-tool `make setup` (best-effort, failures non-fatal)
   .NET tools auto-skipped (dotnet not on VM)
   SonarQube auto-skipped if Docker Compose unavailable

7. Tool execution             Varies (5-30+ min)
   `make analyze` with CONTINUE_ON_TOOL_FAILURE=1
   Runs up to MAX_PARALLEL tools concurrently

8. dbt + report generation    ~1-2 min
   Staging → marts → HTML report

9. Results export             ~30s
   Packages DuckDB, reports, manifest, run log

10. SCP download              ~30s-2 min
    Downloads results to local machine

11. Terraform destroy         ~30s
    Removes VM (unless KEEP_SERVER=1)
```

**Total wall time:** 10-40 minutes depending on repo size, server type, and tool count.

The Terraform execution has a **60-minute timeout** — if the analysis exceeds this, the provisioner fails and results are not downloaded. For very large repos, consider skipping expensive tools or using a larger server.

## Monitoring and Debugging

### Keeping the server alive

Use `KEEP_SERVER=1` to prevent automatic destruction:

```bash
make cloud-run REPO=https://github.com/org/repo KEEP_SERVER=1
```

The script prints the server IP when done. SSH in to inspect:

```bash
ssh root@<server-ip>
```

### Log locations on the VM

| Location | Content |
|----------|---------|
| `/tmp/caldera-run.log` | Full pipeline output (tool execution, adapter ingestion, dbt) |
| `journalctl -u cloud-init` | VM bootstrap log (package install, Caldera clone) |
| `/opt/caldera/project/src/tools/*/outputs/` | Per-tool raw outputs |
| `/opt/caldera/results/` | Exported results (DuckDB, reports, manifest) |

### Checking tool status on the VM

```bash
cd /opt/caldera/project

# List tool outputs
ls -la src/tools/*/outputs/

# Check the database
.venv/bin/python -c "
import duckdb
conn = duckdb.connect('~/.caldera/caldera_sot.duckdb', read_only=True)
print(conn.execute('SELECT * FROM lz_collection_runs').fetchdf())
conn.close()
"
```

### Destroying the server when done

```bash
make cloud-destroy
```

## Inspecting Results

Results are downloaded to `infra/results/<repo-id>/<run-id>/`:

```
manifest.json                    # Run metadata, timestamps, tool status, cost
run.log                          # Full pipeline output
database/
  caldera_sot.duckdb             # Complete DuckDB database
reports/
  report.html                    # HTML insights report
  evaluation.json                # LLM evaluation (if PIPELINE_LLM=1)
  top3_insights.json             # Top 3 insights (if PIPELINE_LLM=1)
```

### Open the HTML report

```bash
open infra/results/<repo-id>/<run-id>/reports/report.html
```

### Query the downloaded database

```bash
# Interactive DuckDB shell
duckdb infra/results/<repo-id>/<run-id>/database/caldera_sot.duckdb

# Example queries
SELECT * FROM lz_collection_runs;
SELECT tool_name, status, duration_seconds FROM lz_tool_runs ORDER BY duration_seconds DESC;
SELECT file_path, complexity FROM mart_lizard_file_metrics WHERE complexity > 20 ORDER BY complexity DESC;
```

### Read the manifest

The `manifest.json` includes run metadata and cost data:

```json
{
  "schema_version": 1,
  "repo": { "repo_id": "flask-a1b2c3d4e5", "commit": "..." },
  "cloud": {
    "server_type": "cx33",
    "duration_seconds": 842,
    "estimated_cost_eur": 0.013,
    "billable_hours": 1
  },
  "tools": [
    { "tool_name": "scc", "status": "success", "duration_seconds": 12.3 },
    { "tool_name": "lizard", "status": "success", "duration_seconds": 45.7 }
  ]
}
```

## Cost Management

### Pricing

All server types use shared vCPU with **1-hour minimum billing** (Hetzner bills per-hour, not per-second):

| Preset | Type | EUR/hour | Typical run cost |
|--------|------|----------|-----------------|
| `small` | cx23 | 0.007 | EUR 0.007 |
| `medium` | cx33 | 0.013 | EUR 0.013 |
| `large` | cx43 | 0.025 | EUR 0.025 |
| `xlarge` | cx53 | 0.050 | EUR 0.050 |

Since most runs complete in under an hour, the cost equals the hourly rate. The cost summary is printed at the end of every run and recorded in `manifest.json`.

### Cleaning up orphaned VMs

If a run is interrupted (network failure, Ctrl-C, etc.), the VM may still be running. Use the cleanup command to find and destroy orphans:

```bash
# Preview orphaned VMs (dry run)
make cloud-cleanup DRY_RUN=1

# Destroy orphaned VMs older than TTL (default: 4 hours)
make cloud-cleanup

# Custom TTL
make cloud-cleanup TTL_HOURS=2
```

This requires the `hcloud` CLI (`brew install hcloud`). It finds servers with the `project=caldera` label and destroys any older than the TTL.

### Monitoring spending

Check your Hetzner billing at [console.hetzner.cloud](https://console.hetzner.cloud) → Billing. Each Caldera VM is labeled `project=caldera` for easy identification.

## Performance Tuning

### Scaling parallelism with server size

The `MAX_PARALLEL` setting controls how many tools run concurrently. Match it to your server's vCPU count:

| Preset | vCPU | Recommended MAX_PARALLEL |
|--------|------|-------------------------|
| `small` | 2 | 2 |
| `medium` | 4 | 4 (default) |
| `large` | 8 | 6-8 |
| `xlarge` | 16 | 8-12 |

```bash
make cloud-run REPO=https://github.com/org/repo CLOUD_SERVER=large MAX_PARALLEL=8
```

### Skipping expensive tools

Some tools are significantly slower on large repos. Skip them if their output isn't needed:

| Tool | Why it's slow on large repos | Skip if you don't need |
|------|------------------------------|----------------------|
| git-fame | Scans every commit for contributor stats | Contributor analysis |
| git-blame-scanner | Runs `git blame` on every file | Per-file authorship |
| gitleaks | Scans full commit history for secrets | Secret detection |
| semgrep | Applies hundreds of rules across all files | Code smell detection |
| pmd-cpd | Pairwise file comparison for copy-paste | Duplication analysis |

```bash
make cloud-run \
    REPO=https://github.com/org/large-repo \
    SKIP_TOOLS=git-fame,git-blame-scanner,gitleaks \
    CLOUD_SERVER=large
```

### Using shallow clones for speed

For code-quality-only analysis, a shallow clone with `CLONE_DEPTH=1` can save minutes on repos with deep history. See [Clone Depth Strategy](#clone-depth-strategy) above.

## Troubleshooting

### Large-repo-specific issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Clone takes very long or times out | Large repo with deep history | Use `CLONE_DEPTH=100` or `CLONE_DEPTH=1`; ensure the repo is on a fast host |
| Disk space exhaustion | Large repo + many tool outputs + DuckDB | Use `large` or `xlarge` preset (more disk); skip tools you don't need |
| Out of memory (OOM) | Tool processing very large files | Use a larger server preset; add the offending tool to `SKIP_TOOLS` |
| Analysis exceeds 60-minute timeout | Too many tools on a very large repo | Skip slow tools, use a larger server, or use `CLONE_DEPTH` |
| SCP download fails | Large DuckDB file or network interruption | Use `KEEP_SERVER=1`, then `scp root@<ip>:/opt/caldera/results/ ./results/` manually |
| .NET tools skipped | Expected — dotnet is not installed on the VM | No action needed; devskim, dotcover, roslyn-analyzers auto-skip |
| SonarQube skipped | Docker Compose not available | Expected if the VM image doesn't include `docker compose` |

### General issues

| Problem | Solution |
|---------|----------|
| `terraform.tfvars not found` | `cp infra/terraform.tfvars.example infra/terraform.tfvars` and fill in values |
| SSH key not found | Set `ssh_private_key_path` in `terraform.tfvars` to match your key (check `ls ~/.ssh/id_*`) |
| SSH connection timeout | Verify SSH key path; check that Hetzner API token is valid |
| Cloud-init error | Caldera clone failed — check `caldera_repo_url` is accessible. Use `KEEP_SERVER=1` + `journalctl -u cloud-init` |
| Hetzner auth error | Regenerate API token at console.hetzner.cloud |
| Results directory empty | Use `KEEP_SERVER=1` to debug; check `/opt/caldera/results/` on the VM |
| `cloud-destroy` fails | Delete manually: `hcloud server list && hcloud server delete <id>` |
| Terraform retry message | Transient SSH/network failure — the script retries up to 2 times automatically |

## Further Reading

- [infra/README.md](../infra/README.md) — Full infrastructure reference (variables, datacenter locations, manifest schema)
- [docs/USER_GUIDE.md](USER_GUIDE.md) — Getting started guide (local + cloud quick-start)
- [docs/CLOUD_HOSTING_COMPARISON.md](CLOUD_HOSTING_COMPARISON.md) — Cloud provider comparison
- [docs/PRODUCTION_MODES.md](PRODUCTION_MODES.md) — All three production modes (local, bundle, Docker)
