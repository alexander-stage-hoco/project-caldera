# Cloud Hosting Comparison for Project Caldera

**Date:** 2026-02-19
**Context:** Evaluating all viable options to run Caldera's dockerized pipeline in the cloud at minimum cost.

---

## Caldera's Runtime Requirements

Before comparing options, here's what a Caldera run actually needs:

| Requirement | Value | Why |
|-------------|-------|-----|
| **CPU** | 2–8 vCPUs | Tools run in parallel; more cores = faster |
| **RAM** | 4–16 GB | SonarQube alone needs 2 GB; DuckDB + dbt need headroom |
| **Disk** | 5–20 GB scratch | Cloned repo + 18 tool outputs + DuckDB + dbt artifacts |
| **Runtime** | 10–45 min per repo | Small repo ~10 min, large mono-repo ~45 min |
| **Docker** | Required | 18 tool containers spawned by orchestrator |
| **Docker-in-Docker** | Ideal but not mandatory | Orchestrator spawns tool containers. Alternative: run tools natively inside a single fat container. |
| **Network** | Outbound (git clone, API keys) | Clone target repo, optionally call Anthropic API |
| **Persistent storage** | None (results pushed to git or copied out) | Ephemeral is fine — everything exportable |
| **Frequency** | On-demand, bursty | 0–10 runs/day typically, not continuous |
| **Security** | Analyzes untrusted code | Tools parse arbitrary repos; isolation matters |

### The Docker-in-Docker Question

The original design has the orchestrator spawning 18 sibling containers. This requires Docker socket access. Not all platforms support this. There are two approaches:

| Approach | Pros | Cons | Platforms |
|----------|------|------|-----------|
| **DinD (Docker-in-Docker)** | Clean isolation per tool, matches local dev | Needs privileged/socket access | VMs, GitHub Actions, some managed container services |
| **Fat container (all-in-one)** | Works everywhere, simpler | No per-tool isolation, larger image (~3–5 GB) | Cloud Run, ACI, Fargate, any container platform |

For platforms that don't support DinD, we build a single "caldera-all-in-one" image with all tool binaries installed. The orchestrator runs tools as subprocesses (local backend) inside the container. This is the pragmatic path for serverless/managed platforms.

---

## Option-by-Option Analysis

### 1. Hetzner Cloud (VMs)

**What it is:** Cheap European cloud VMs (bare metal optional). No managed container service — just Linux VMs with Docker pre-installed.

| Aspect | Detail |
|--------|--------|
| **How to run** | Spin up VM via API/CLI → SSH in → run `caldera-run` → tear down |
| **Docker support** | Full (it's a VM, install anything) |
| **DinD** | Yes (full VM, no restrictions) |
| **Pricing** | CX22 (2 vCPU/4 GB): €0.007/hr · CX32 (4/8): €0.013/hr · CX42 (8/16): €0.025/hr |
| **Cost per run (15 min)** | **€0.007–0.025 ($0.008–0.027)** (1h minimum billing) |
| **Startup time** | ~30–60s (VM boot + Docker ready) |
| **Disk** | 40–160 GB included (SSD) |
| **Regions** | EU (Nuremberg, Falkenstein, Helsinki), US East (Ashburn) |
| **API/CLI** | `hcloud` CLI, REST API, Terraform provider |
| **Setup effort** | Low (create project, add SSH key, done) |

**Pros:**
- Cheapest compute per hour in the industry
- Full VM = zero restrictions (DinD, any binary, any disk)
- Simple mental model: SSH + run script + delete
- No egress fees within Hetzner
- Terraform support for automation

**Cons:**
- No managed container service (you manage the VM lifecycle)
- EU-primary (US East available but fewer options)
- No spot/preemptible pricing (already cheap enough that it doesn't matter)
- Need to script VM create/destroy yourself
- No built-in secrets manager (pass via cloud-init or SSH)

**Verdict:** Best raw cost. Ideal if you're comfortable scripting VM lifecycle.

---

### 2. AWS EC2 (Spot Instances)

**What it is:** On-demand or spot VMs on AWS. Spot instances are excess capacity at 60–90% discount.

| Aspect | Detail |
|--------|--------|
| **How to run** | Launch spot instance → user-data script runs Caldera → terminate |
| **Docker support** | Full (Amazon Linux 2023 or Ubuntu with Docker) |
| **DinD** | Yes |
| **Pricing (spot)** | t3.medium (2/4): ~$0.01/hr · t3.xlarge (4/16): ~$0.05/hr · m6i.2xlarge (8/32): ~$0.10/hr |
| **Cost per run (15 min)** | **$0.003–0.025** (spot) |
| **Startup time** | ~60–90s |
| **Disk** | EBS gp3, 20 GB ~$0.002/hr |
| **Regions** | Global |
| **Setup effort** | Medium (IAM role, VPC/security group, key pair) |

**Pros:**
- Spot pricing makes it very cheap
- Global regions
- Mature ecosystem (CloudWatch, SSM, S3 for artifacts)
- Can store images in ECR (free tier: 500 MB)
- user-data scripts for fully automated launch-run-terminate

**Cons:**
- Spot instances can be reclaimed (rare for short runs, but possible)
- AWS billing complexity (instance + EBS + data transfer + ECR)
- IAM/VPC/SG setup overhead for first run
- Egress fees ($0.09/GB after 100 GB free/month)
- Overkill infrastructure for a simple batch job

**Verdict:** Good if already on AWS. Spot pricing is excellent. Setup overhead higher than Hetzner.

---

### 3. Google Cloud Run

**What it is:** Serverless container platform. You push a container image, Google runs it on demand. Pay only while the container is processing a request.

| Aspect | Detail |
|--------|--------|
| **How to run** | Push all-in-one image to Artifact Registry → trigger via HTTP/CLI/Pub-Sub |
| **Docker support** | Runs your container, but NO Docker inside the container |
| **DinD** | **No** — must use fat container approach |
| **Max timeout** | 60 minutes (sufficient for most repos) |
| **Max RAM** | 32 GB |
| **Max vCPUs** | 8 |
| **Pricing** | vCPU: $0.00002400/s · RAM: $0.00000250/s per GB |
| **Cost per run (15 min, 4 vCPU/8 GB)** | vCPU: $0.0864 + RAM: $0.018 = **~$0.10** |
| **Startup time** | 5–30s (cold start, depends on image size) |
| **Disk** | In-memory tmpfs only (up to RAM size). Cloud Run Jobs: 2 GB scratch. |
| **Regions** | Global |
| **Setup effort** | Low-Medium (Artifact Registry + service account) |

**Pros:**
- True pay-per-use (zero cost when idle)
- No VM management at all
- Fast cold starts for pre-cached images
- Integrated with GCP logging, monitoring
- Cloud Run **Jobs** (not Services) are perfect for batch work — no HTTP needed
- Scales to zero automatically

**Cons:**
- **No DinD** — must build a fat all-in-one container image (~3–5 GB)
- **Limited scratch disk** — Cloud Run Jobs give 2 GB ephemeral storage; may be tight for large repos
- **~10x more expensive** per run than Hetzner VMs
- Image size matters — large images have slow cold starts
- No persistent filesystem (must push results to GCS or git)
- 60-minute timeout (tight for very large repos + SonarQube)

**Cloud Run Jobs vs Cloud Run Services:**

| Feature | Cloud Run Services | Cloud Run Jobs |
|---------|-------------------|----------------|
| **Trigger** | HTTP request | CLI / scheduler / Pub-Sub |
| **Timeout** | 60 min | 24 hours |
| **Scratch disk** | tmpfs only | 2 GB ephemeral |
| **Use for Caldera** | Not ideal | **Better fit** |

**Verdict:** Works, but expensive compared to VMs and requires a fat container. Best if you're already deep in GCP and value managed infrastructure over cost.

---

### 4. Google Compute Engine (VMs)

**What it is:** GCP's VM service. Spot VMs (formerly preemptible) available at 60–91% discount.

| Aspect | Detail |
|--------|--------|
| **How to run** | Create spot VM → startup script → terminate |
| **Docker support** | Full |
| **DinD** | Yes |
| **Pricing (spot)** | e2-medium (2/4): ~$0.007/hr · e2-standard-4 (4/16): ~$0.028/hr · e2-standard-8 (8/32): ~$0.056/hr |
| **Cost per run (15 min)** | **$0.002–0.014** (spot) |
| **Startup time** | ~30–60s |
| **Disk** | 10 GB free balanced PD |
| **Setup effort** | Medium (service account, firewall rules) |

**Pros:**
- Spot VMs are very cheap
- Full VM = full flexibility
- `gcloud` CLI is clean
- Container-optimized OS available (COS, pre-installed Docker)
- Can use startup-script for fully automated runs

**Cons:**
- Spot VMs terminate after 24 hours max (fine for Caldera)
- GCP billing complexity
- Egress fees
- More setup than Hetzner

**Verdict:** Strong option if already on GCP. Spot VMs are competitive with Hetzner on price.

---

### 5. AWS Fargate (Managed Containers)

**What it is:** Serverless container execution on AWS. You define a task (container image + resources), Fargate runs it.

| Aspect | Detail |
|--------|--------|
| **How to run** | Push image to ECR → run ECS task → collect results from S3 |
| **Docker support** | Runs your container, but NO DinD |
| **DinD** | **No** — must use fat container approach |
| **Pricing** | vCPU: $0.04048/hr · RAM: $0.004445/hr per GB |
| **Cost per run (15 min, 4 vCPU/8 GB)** | vCPU: $0.041 + RAM: $0.009 = **~$0.05** |
| **Max resources** | 16 vCPU, 120 GB RAM |
| **Startup time** | 30–60s |
| **Disk** | 20 GB ephemeral (configurable up to 200 GB) |
| **Setup effort** | High (ECS cluster, task definition, IAM, VPC, ECR) |

**Pros:**
- No VM management
- Good ephemeral disk (20–200 GB)
- Integrated with AWS ecosystem (CloudWatch, S3, Secrets Manager)
- Fargate Spot: 70% discount (same caveats as EC2 Spot)

**Cons:**
- **No DinD** — fat container required
- More expensive than EC2 Spot
- Complex setup (ECS concepts: cluster, service, task definition)
- Fargate Spot tasks can be interrupted
- Cold starts can be slow for large images

**Verdict:** Over-engineered for Caldera's batch use case. Use EC2 Spot instead if on AWS.

---

### 6. Azure Container Instances (ACI)

**What it is:** Azure's simplest container service. Run a container without managing VMs.

| Aspect | Detail |
|--------|--------|
| **How to run** | `az container create` → runs container → collect results |
| **Docker support** | Runs your container, NO DinD |
| **DinD** | **No** |
| **Pricing** | vCPU: $0.0000125/s · RAM: $0.0000015/s per GB |
| **Cost per run (15 min, 4 vCPU/8 GB)** | vCPU: $0.045 + RAM: $0.011 = **~$0.06** |
| **Max resources** | 4 vCPU, 16 GB RAM per container group |
| **Startup time** | 30–120s |
| **Disk** | 50 GB ephemeral |
| **Setup effort** | Low (single CLI command) |

**Pros:**
- Simplest Azure option (one command to run a container)
- Good ephemeral disk
- No cluster management

**Cons:**
- No DinD
- 4 vCPU / 16 GB RAM max (tight for parallel tools)
- More expensive than VMs
- Slow image pull for large images
- Limited regions for spot/low-priority

**Verdict:** Simple but limited. Only consider if already on Azure and want zero VM management.

---

### 7. Azure VMs (Spot)

| Aspect | Detail |
|--------|--------|
| **Pricing (spot)** | B2s (2/4): ~$0.005/hr · D4s_v5 (4/16): ~$0.04/hr |
| **Cost per run (15 min)** | **$0.001–0.010** |
| **DinD** | Yes |
| **Setup effort** | Medium |

**Verdict:** Competitive spot pricing. Similar story to AWS/GCP VMs.

---

### 8. DigitalOcean Droplets

**What it is:** Simple cloud VMs. No spot pricing, but straightforward.

| Aspect | Detail |
|--------|--------|
| **How to run** | Create droplet → run → destroy |
| **Docker support** | Full (Docker pre-installed images available) |
| **DinD** | Yes |
| **Pricing** | s-2vcpu-4gb: $0.030/hr · s-4vcpu-8gb: $0.060/hr |
| **Cost per run (15 min)** | **$0.008–0.015** |
| **Startup time** | ~60s |
| **Setup effort** | Low (simple API, `doctl` CLI) |

**Pros:**
- Simple, developer-friendly
- Docker pre-installed images
- `doctl` CLI is clean
- Predictable pricing (no spot complexity)
- 1-click Docker Droplet marketplace image

**Cons:**
- No spot pricing (2–3x more expensive than spot VMs on other providers)
- Fewer regions than big-3
- No managed container service

**Verdict:** Good developer experience, but more expensive per run. Fine for low-volume use.

---

### 9. GitHub Actions

**What it is:** CI/CD runners triggered by workflows. Comes with Docker support.

| Aspect | Detail |
|--------|--------|
| **How to run** | `workflow_dispatch` trigger → runs in Ubuntu runner |
| **Docker support** | Yes (Docker pre-installed on runners) |
| **DinD** | Yes (Docker daemon available) |
| **Pricing** | Public repos: **free** (2,000 min/month) · Private: $0.008/min |
| **Cost per run (30 min)** | Free (public) or **$0.24** (private) |
| **Resources** | 4 vCPU, 16 GB RAM (standard runner) |
| **Max runtime** | 6 hours |
| **Disk** | 14 GB free |
| **Setup effort** | Minimal (YAML workflow file) |

**Larger runners (private repos):**

| Runner | vCPUs | RAM | $/min |
|--------|-------|-----|-------|
| 4-core | 4 | 16 GB | $0.016 |
| 8-core | 8 | 32 GB | $0.032 |
| 16-core | 16 | 64 GB | $0.064 |

**Pros:**
- **Free for public repos** (hard to beat)
- Docker pre-installed with full DinD support
- Zero infrastructure to manage
- Integrated with GitHub (secrets, artifacts, PR comments)
- `workflow_dispatch` = run on demand from GitHub UI
- Can cache Docker layers between runs (saves build time)

**Cons:**
- 14 GB disk may be tight (large repos + tool outputs + DuckDB)
- 16 GB RAM on free runners (fine for most, tight with SonarQube)
- Private repo cost adds up at scale ($0.24–0.96/run)
- 6-hour timeout (plenty for Caldera)
- Queuing delays during peak GitHub usage
- Not ideal for sensitive/proprietary target repos (runs on shared infra)

**Verdict:** Best option if Caldera is a public GitHub repo. Zero cost, zero infra. For private repos, reasonable at low volume.

---

### 10. GitLab CI/CD

**What it is:** Similar to GitHub Actions but on GitLab.

| Aspect | Detail |
|--------|--------|
| **Pricing** | 400 min/month free (all tiers) · Premium: 10,000 min/month |
| **Cost per run (30 min)** | Free (within quota) or $0.005/min on shared runners |
| **Resources** | 2 vCPU, 7.5 GB RAM (shared Linux) |
| **Docker support** | Yes (Docker executor or Kubernetes) |
| **DinD** | Yes (with `docker:dind` service) |

**Pros:**
- Generous free tier
- Good DinD support via services

**Cons:**
- Shared runners are weak (2 vCPU, 7.5 GB RAM)
- Need self-hosted runner for more power (then you're managing infra)

**Verdict:** Viable if already on GitLab. Weaker runners than GitHub Actions.

---

### 11. Fly.io

**What it is:** Container hosting platform focused on edge deployment. Supports Machines API (ephemeral containers).

| Aspect | Detail |
|--------|--------|
| **How to run** | `fly machine run` → runs container → auto-stops |
| **Docker support** | Runs your container (Firecracker micro-VMs) |
| **DinD** | **No** (Firecracker VMs don't support nested virtualization) |
| **Pricing** | shared-cpu-4x (4 vCPU/8 GB): ~$0.058/hr |
| **Cost per run (15 min)** | **~$0.015** |
| **Max resources** | 16 vCPU, 32 GB RAM |
| **Startup time** | ~3–5s (fast!) |
| **Disk** | Ephemeral or volume mounts |

**Pros:**
- Very fast startup (Firecracker)
- Machines API scales to zero (pay only when running)
- Simple CLI (`flyctl`)
- Good for bursty workloads

**Cons:**
- No DinD (Firecracker limitation) — fat container required
- Relatively expensive compared to VMs
- Less mature for batch workloads (designed for web services)
- Image size limits can be annoying

**Verdict:** Cool technology, but no DinD and pricier than VMs. Not ideal for Caldera.

---

### 12. Railway

**What it is:** PaaS for deploying containers. Simple push-to-deploy.

| Aspect | Detail |
|--------|--------|
| **Pricing** | $0.000231/min vCPU + $0.000231/min per 512 MB RAM |
| **Cost per run (15 min, 4 vCPU/8 GB)** | **~$0.07** |
| **DinD** | **No** |
| **Max resources** | 32 vCPU, 32 GB RAM |
| **Disk** | Ephemeral |

**Pros:**
- Simple developer UX
- Auto-scaling

**Cons:**
- No DinD
- Expensive for batch
- Designed for long-running services, not batch jobs

**Verdict:** Wrong tool for this job. Skip.

---

### 13. Render

**What it is:** PaaS with "cron jobs" (scheduled container runs).

| Aspect | Detail |
|--------|--------|
| **Pricing** | From $0.0021/min (512 MB) |
| **DinD** | **No** |
| **Max runtime** | Configurable |

**Verdict:** Same issues as Railway. Designed for web, not batch. Skip.

---

### 14. Coolify (Self-Hosted PaaS)

**What it is:** Open-source, self-hosted alternative to Heroku/Vercel. Deploy on your own VM.

| Aspect | Detail |
|--------|--------|
| **How to run** | Install Coolify on a Hetzner/DO VM → deploy Caldera as a "one-off task" |
| **DinD** | Yes (it's your VM) |
| **Cost** | VM cost only (Hetzner CX32: €0.013/hr) |

**Pros:**
- Full control
- Nice UI for managing deployments
- Free (open-source)

**Cons:**
- VM must be running (not truly ephemeral)
- Another thing to maintain
- Overkill for a simple batch job

**Verdict:** Interesting if you want a management UI, but a simple script on Hetzner is simpler.

---

### 15. Docker Build Cloud (Docker Inc.)

**What it is:** Docker's cloud build service. Builds Docker images in the cloud, not runs them.

| Aspect | Detail |
|--------|--------|
| **Purpose** | Fast remote Docker image builds |
| **Can it run Caldera?** | **No** — it builds images, doesn't execute arbitrary workloads |
| **Pricing** | Free tier: 50 min/month · Team: $15/user/month |

**Verdict:** Not applicable. This is a build service, not a runtime.

---

### 16. Docker Desktop / Docker Hub

**What it is:** Docker Desktop is local. Docker Hub is an image registry.

| Docker Hub | Detail |
|------------|--------|
| **Purpose** | Store and distribute container images |
| **Can it run Caldera?** | **No** — it's a registry, not compute |
| **Free tier** | 1 private repo, unlimited public |
| **Use for Caldera** | Host pre-built tool images to speed up cloud runs |

**Verdict:** Use Docker Hub (or GitHub Container Registry) to **store tool images**. Not a runtime.

---

## Summary Comparison

### Cost Per Run (15-minute analysis of a medium repo)

| Option | Cost/Run | DinD? | Setup | Best For |
|--------|----------|-------|-------|----------|
| **GitHub Actions (public)** | **$0.00** | Yes | Minimal | Public repos, zero budget |
| **Hetzner CX32 VM** | **$0.004** | Yes | Low | Cheapest option overall |
| **GCP Spot VM (e2-standard-4)** | $0.007 | Yes | Medium | GCP shops |
| **AWS Spot (t3.xlarge)** | $0.01 | Yes | Medium | AWS shops |
| **Azure Spot VM** | $0.01 | Yes | Medium | Azure shops |
| **DigitalOcean Droplet** | $0.015 | Yes | Low | Simple, no spot hassle |
| **Fly.io Machine** | $0.015 | No | Low | Fast starts, but no DinD |
| **AWS Fargate (spot)** | $0.02 | No | High | AWS + no-VM preference |
| **GitHub Actions (private)** | $0.24 | Yes | Minimal | Convenience over cost |
| **Azure Container Instances** | $0.06 | No | Low | Azure + simplicity |
| **Railway** | $0.07 | No | Low | Not recommended |
| **Google Cloud Run Job** | $0.10 | No | Low-Med | GCP + serverless preference |

### Decision Matrix

| Priority | Best Option | Runner-Up |
|----------|-------------|-----------|
| **Cheapest possible** | Hetzner CX32 ($0.004/run) | GCP Spot VM ($0.007/run) |
| **Zero cost** | GitHub Actions (public repo) | GitLab CI (400 min free) |
| **Zero infrastructure** | GitHub Actions | Google Cloud Run Jobs |
| **Already on AWS** | EC2 Spot | Fargate Spot (if no-DinD OK) |
| **Already on GCP** | GCE Spot VM | Cloud Run Jobs (if no-DinD OK) |
| **Already on Azure** | Azure Spot VM | ACI (small repos only) |
| **Maximum simplicity** | GitHub Actions | DigitalOcean |
| **Analyzing sensitive code** | Hetzner (own VM) | Self-hosted GH runner |
| **Need DinD** | Any VM option | GitHub Actions |
| **Serverless (no VMs)** | Cloud Run Jobs | Fargate |

---

## Recommended Path

### Phase 1: Start with GitHub Actions (free, zero infra)

If Caldera is on GitHub, add a `workflow_dispatch` workflow. This gives you:
- Free runs for public repos
- Docker + DinD support
- On-demand trigger from GitHub UI
- No infrastructure to manage

```yaml
# .github/workflows/caldera-analyze.yml
name: Caldera Analysis
on:
  workflow_dispatch:
    inputs:
      repo_url:
        description: 'Repository to analyze'
        required: true
```

**Limitations:** 16 GB RAM, 14 GB disk, shared infra. If these become constraints, move to Phase 2.

### Phase 2: Add Hetzner for heavy runs

When you need more resources or run sensitive analyses:
- `scripts/cloud-run.sh hetzner` spins up a CX32/CX42
- Pre-built images pulled from registry (fast)
- Results pushed to git or copied via scp
- VM destroyed after run

**Cost:** $0.004–0.007 per run. Even 100 runs/month = ~$0.50.

### Phase 3 (if needed): Managed service

If you end up running dozens of analyses daily and want zero VM management:
- Google Cloud Run Jobs (fat container) or AWS Fargate
- Higher cost per run ($0.05–0.10) but zero ops
- Only worth it at scale where VM scripting becomes a burden

### What NOT to do

- Don't use always-on VMs — Caldera is batch, pay-per-use is the right model
- Don't use serverless for v1 — the fat container requirement adds complexity; start with VMs
- Don't over-engineer — a 20-line bash script on Hetzner beats a Terraform + ECS + CodePipeline setup
- Don't use platforms without DinD unless you're committed to building the all-in-one image

---

## All-in-One Image (for platforms without DinD)

If targeting Cloud Run, Fargate, ACI, or Fly.io, you need a single container with all tools:

```dockerfile
# Dockerfile.all-in-one (~3-5 GB)
FROM python:3.12-slim

# System tools
RUN apt-get update && apt-get install -y \
    git curl default-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# Tool binaries
RUN curl -sL .../scc.tar.gz | tar xz -C /usr/local/bin/ && \
    curl -sL .../trivy.tar.gz | tar xz -C /usr/local/bin/ && \
    curl -sL .../gitleaks.tar.gz | tar xz -C /usr/local/bin/ && \
    curl -sL .../git-sizer.tar.gz | tar xz -C /usr/local/bin/ && \
    pip install semgrep

# Python tools
COPY requirements.txt .
RUN pip install -r requirements.txt

# Caldera source
COPY src/ /caldera/src/
COPY scripts/ /caldera/scripts/

ENTRYPOINT ["python", "src/sot-engine/orchestrator.py", "--mode", "local"]
```

**Trade-offs:**
- Pro: Works on any container platform
- Pro: Single image to build and push
- Con: ~3–5 GB image (slow cold starts on Cloud Run)
- Con: No per-tool isolation
- Con: Harder to update individual tools
- Con: Missing .NET tools (dotcover, roslyn) unless you add .NET SDK (+2 GB)

**Recommendation:** Build this as a secondary artifact. The DinD approach (separate tool images) remains primary for VMs and GitHub Actions.
