# Cloud Infrastructure — Hetzner

Run the full Caldera analysis pipeline on an ephemeral Hetzner Cloud VM. The server is created via Terraform, executes the pipeline, downloads results locally, and is destroyed automatically.

## Prerequisites

| Requirement | Check | Install |
|-------------|-------|---------|
| Terraform >= 1.5 | `terraform --version` | `brew install terraform` |
| SSH key pair | `ls ~/.ssh/id_ed25519` | `ssh-keygen -t ed25519` |
| Hetzner API token | — | [console.hetzner.cloud](https://console.hetzner.cloud) → Project → Security → API Tokens |

## One-Time Setup

```bash
# 1. Create terraform.tfvars from the example
cp infra/terraform.tfvars.example infra/terraform.tfvars

# 2. Edit terraform.tfvars — fill in these required values:
#    hcloud_token     = "your-hetzner-api-token"
#    caldera_repo_url = "https://github.com/yourorg/caldera.git"

# 3. Initialize Terraform
make cloud-setup
```

## Usage

```bash
# Analyze a GitHub repository
make cloud-run REPO=https://github.com/pallets/flask

# With options
make cloud-run REPO=https://github.com/org/repo CLOUD_SERVER=cx43 SKIP_TOOLS=sonarqube,trivy
make cloud-run REPO=https://github.com/org/repo PIPELINE_LLM=1    # Enable LLM evaluation
make cloud-run REPO=https://github.com/org/repo KEEP_SERVER=1      # Keep VM for debugging
```

Results are downloaded to `infra/results/<repo-id>/<run-id>/`.

## Terraform Variables

Configured in `infra/terraform.tfvars`. See `terraform.tfvars.example` for the template.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `hcloud_token` | Yes | — | Hetzner Cloud API token (read/write) |
| `caldera_repo_url` | Yes | — | Git URL of your Caldera fork (cloned onto the VM) |
| `repo_url` | — | Set by script | Target repo to analyze (passed by `cloud-run.sh`) |
| `server_type` | No | `cx33` | VM size (see Server Presets below) |
| `location` | No | `nbg1` | Datacenter location |
| `ssh_public_key_path` | No | `~/.ssh/id_ed25519.pub` | SSH public key for server access |
| `ssh_private_key_path` | No | `~/.ssh/id_ed25519` | SSH private key for provisioner connections |
| `caldera_branch` | No | `main` | Caldera branch to checkout on the VM |
| `skip_tools` | No | `""` | Comma-separated tools to skip |
| `pipeline_llm` | No | `0` | Set to `1` to enable LLM evaluation |
| `max_parallel` | No | `4` | Max parallel tool execution |
| `results_dir` | No | `./results` | Local directory for downloaded results |

## Server Presets

Instead of remembering raw Hetzner type codes, use preset names:

| Preset | Type | vCPU | RAM | Use case |
|--------|------|------|-----|----------|
| `small` | `cx23` | 2 | 4 GB | Small repos, CI |
| `medium` | `cx33` | 4 | 8 GB | Medium repos — **default** |
| `large` | `cx43` | 8 | 16 GB | Large repos, parallel-heavy |
| `xlarge` | `cx53` | 16 | 32 GB | Very large monorepos |

```bash
# Use a preset name
make cloud-run REPO=https://github.com/org/repo CLOUD_SERVER=large

# Or a raw Hetzner type (still works)
make cloud-run REPO=https://github.com/org/repo CLOUD_SERVER=cx43
```

Presets and pricing are defined in `infra/server_presets.json` (single source of truth).

All types use shared vCPU (Intel). Pricing is per-hour; a typical run costs a few cents.

## Cost Tracking

Cloud run manifests automatically include cost estimates:

```json
{
  "cloud": {
    "server_type": "cx33",
    "duration_seconds": 842,
    "estimated_cost_eur": 0.013,
    "pricing_eur_per_hour": 0.013,
    "billable_hours": 1
  }
}
```

Pricing data is inlined in `run-analysis.sh` (mirroring `server_presets.json`) since the remote VM doesn't have the presets file. The cost summary is also printed at the end of `cloud-run.sh`.

## VM Cleanup

Orphaned VMs (e.g. from interrupted runs) can be destroyed automatically:

```bash
# List orphaned VMs (default TTL: 4 hours)
make cloud-cleanup DRY_RUN=1

# Destroy orphaned VMs
make cloud-cleanup

# Custom TTL
make cloud-cleanup TTL_HOURS=2
```

Requires the `hcloud` CLI (`brew install hcloud`) with a configured context. The cleanup script finds servers with the `project=caldera` label and destroys any older than the TTL based on the Hetzner API `created` timestamp.

Server labels include `created_at` for traceability (set by Terraform).

## Datacenter Locations

| Code | Location |
|------|----------|
| `nbg1` | Nuremberg, Germany (default) |
| `fsn1` | Falkenstein, Germany |
| `hel1` | Helsinki, Finland |
| `ash` | Ashburn, Virginia, USA |

## What Gets Installed (cloud-init)

The VM uses the Hetzner `docker-ce` image (Ubuntu + Docker pre-installed). Cloud-init adds:

- `git`, `python3`, `python3-pip`, `python3-venv`, `make`, `curl`, `jq`
- Clones the Caldera project to `/opt/caldera/project`

The `run-analysis.sh` script then:
1. Creates a Python venv and installs Caldera dependencies
2. Clones the target repo to `/tmp/target-repo`
3. Auto-skips .NET tools (devskim, dotcover, roslyn-analyzers) since dotnet is not installed
4. Sets up each tool's environment (best-effort, failures are non-fatal)
5. Runs `make analyze` with `CONTINUE_ON_TOOL_FAILURE=1`
6. Exports DuckDB, reports, and manifest to `/opt/caldera/results/`

## Results Structure

After a successful run, `infra/results/<repo-id>/<run-id>/` contains:

```
manifest.json                    # Run metadata (timestamps, config, export paths)
run.log                          # Full pipeline output log
database/
  caldera_sot.duckdb             # Complete DuckDB database
reports/
  report.html                    # HTML insights report
  evaluation.json                # LLM evaluation (if PIPELINE_LLM=1)
  top3_insights.json             # Top 3 insights (if PIPELINE_LLM=1)
```

### Manifest Schema

The `manifest.json` follows the canonical bundle schema with a `cloud` extension:

```json
{
  "schema_version": 1,
  "created_at": "2026-02-19T...",
  "repo": { "repo_id": "flask-a1b2c3d4e5", "commit": "..." },
  "run_id": "...",
  "cloud": {
    "mode": "cloud-hetzner",
    "server_type": "cx33",
    "duration_seconds": 842,
    "estimated_cost_eur": 0.013,
    "pricing_eur_per_hour": 0.013,
    "billable_hours": 1,
    "skip_tools": [],
    "pipeline_llm": false
  },
  "exports": {
    "database": "database/caldera_sot.duckdb",
    "reports": "reports/",
    "run_log": "run.log"
  }
}
```

## Debugging

### Keep the server alive

```bash
make cloud-run REPO=https://github.com/org/repo KEEP_SERVER=1
```

The script prints the server IP. SSH in to inspect:

```bash
ssh root@<server-ip>

# Logs
cat /tmp/caldera-run.log
journalctl -u cloud-init        # cloud-init logs

# Caldera project
cd /opt/caldera/project
ls -la src/tools/*/outputs/

# Target repo
ls /tmp/target-repo/

# Database
.venv/bin/python -c "import duckdb; print(duckdb.connect('~/.caldera/caldera_sot.duckdb').execute('SELECT * FROM lz_collection_runs').fetchdf())"
```

### Destroy the server when done

```bash
make cloud-destroy
# or
cd infra && terraform destroy -auto-approve -var="repo_url=placeholder"
```

### Common issues

| Problem | Solution |
|---------|----------|
| `terraform.tfvars not found` | `cp infra/terraform.tfvars.example infra/terraform.tfvars` and fill in values |
| SSH key not found | The pre-flight check shows your available keys. Set `ssh_private_key_path` / `ssh_public_key_path` in `terraform.tfvars` to match your key (e.g. `~/.ssh/id_rsa` for RSA) |
| SSH connection timeout | Verify SSH key path in tfvars matches your actual key (`ls ~/.ssh/id_*`) |
| Cloud-init error | Caldera clone failed — check that `caldera_repo_url` is a public URL or the VM has access. Use `KEEP_SERVER=1` and `journalctl -u cloud-init` to debug |
| `Caldera project missing Makefile` | Wrong repo was cloned — check `caldera_repo_url` in tfvars points to your Caldera fork |
| Hetzner auth error | Regenerate API token at console.hetzner.cloud |
| .NET tools skipped | Expected — dotnet is not on the VM. These auto-skip gracefully |
| Analysis takes too long | Use a larger `CLOUD_SERVER` type or add slow tools to `SKIP_TOOLS` |
| Results directory empty | Check `terraform apply` output for errors; use `KEEP_SERVER=1` to debug on the VM |
| No manifest.json after download | SCP may have failed — check network connectivity. Use `KEEP_SERVER=1` and verify results exist on the VM at `/opt/caldera/results/` |
| `cloud-destroy` fails (no tfvars) | Delete the server manually via [Hetzner console](https://console.hetzner.cloud) or `hcloud server list && hcloud server delete <id>` |

## File Reference

| File | Purpose |
|------|---------|
| `infra/main.tf` | Terraform config (server, provisioners, outputs) |
| `infra/cloud-init.yml` | Cloud-init template (packages, Caldera clone) |
| `infra/run-analysis.sh` | Remote analysis script (uploaded to VM via Terraform) |
| `infra/server_presets.json` | Server presets and pricing (single source of truth) |
| `infra/cloud_pricing.py` | Python pricing utilities (cost estimation, preset resolution) |
| `infra/terraform.tfvars.example` | Template for required variables |
| `scripts/cloud-run.sh` | Local orchestrator (parses args, runs terraform apply/destroy) |
| `scripts/cloud_cleanup.py` | Orphan VM cleanup (TTL-based destruction via hcloud CLI) |
