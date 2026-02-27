# =============================================================================
# Project Caldera — Hetzner Cloud Infrastructure
#
# Creates an ephemeral VM, runs a Caldera analysis, exports results, destroys.
#
# Usage:
#   terraform init
#   terraform apply -var="repo_url=https://github.com/org/target"
#   terraform destroy
#
# Or via the Makefile wrapper:
#   make cloud-run REPO=https://github.com/org/target
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.49"
    }
  }
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "hcloud_token" {
  description = "Hetzner Cloud API token (read/write)"
  type        = string
  sensitive   = true
}

variable "repo_url" {
  description = "Target repository URL or path to analyze"
  type        = string
}

variable "server_type" {
  description = "Hetzner server type (cx23=2vCPU/4GB, cx33=4/8, cx43=8/16, cx53=16/32)"
  type        = string
  default     = "cx33"
}

variable "location" {
  description = "Hetzner datacenter (fsn1=Falkenstein, nbg1=Nuremberg, hel1=Helsinki, ash=Ashburn)"
  type        = string
  default     = "nbg1"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for server access"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key for provisioner connections"
  type        = string
  default     = "~/.ssh/id_ed25519"
}

variable "caldera_repo_url" {
  description = "Git URL for the Caldera project itself"
  type        = string
  default     = ""
}

variable "caldera_branch" {
  description = "Caldera branch to checkout on the runner"
  type        = string
  default     = "main"
}

variable "skip_tools" {
  description = "Comma-separated tool names to skip"
  type        = string
  default     = ""
}

variable "pipeline_llm" {
  description = "Enable LLM evaluation (requires ANTHROPIC_API_KEY on server)"
  type        = number
  default     = 0
}

variable "anthropic_api_key" {
  description = "Anthropic API key for LLM evaluation (optional, only needed if pipeline_llm=1)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "max_parallel" {
  description = "Max parallel tool execution"
  type        = number
  default     = 4
}

variable "clone_depth" {
  description = "Shallow clone depth for the target repository (empty = full clone)"
  type        = string
  default     = ""
}

variable "results_dir" {
  description = "Local directory to download results into"
  type        = string
  default     = "./results"
}

# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

provider "hcloud" {
  token = var.hcloud_token
}

# ---------------------------------------------------------------------------
# SSH Key
# ---------------------------------------------------------------------------

resource "hcloud_ssh_key" "caldera" {
  name       = "caldera-deploy"
  public_key = file(pathexpand(var.ssh_public_key_path))

  lifecycle {
    # Don't fail if key already exists with same name
    ignore_changes = [public_key]
  }
}

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

resource "hcloud_server" "runner" {
  name        = "caldera-run-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  server_type = var.server_type
  image       = "docker-ce"
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.caldera.id]

  labels = {
    project    = "caldera"
    purpose    = "analysis-run"
    created_at = formatdate("YYYY-MM-DD-hh-mm-ss", timestamp())
  }

  # Cloud-init installs prerequisites and clones Caldera
  user_data = templatefile("${path.module}/cloud-init.yml", {
    caldera_repo_url = var.caldera_repo_url
    caldera_branch   = var.caldera_branch
  })

  # Wait for cloud-init to finish before running provisioners
  connection {
    type        = "ssh"
    user        = "root"
    private_key = file(pathexpand(var.ssh_private_key_path))
    host        = self.ipv4_address
    timeout     = "5m"
  }

  # Wait for cloud-init to complete and verify success
  provisioner "remote-exec" {
    inline = [
      "echo 'Waiting for cloud-init to finish...'",
      "cloud-init status --wait",
      "if cloud-init status | grep -q 'error'; then echo 'ERROR: cloud-init finished with errors:'; cat /var/log/cloud-init-output.log | tail -30; exit 1; fi",
      "echo 'Verifying Caldera project was cloned...'",
      "test -d /opt/caldera/project && test -f /opt/caldera/project/Makefile || (echo 'ERROR: /opt/caldera/project not found or missing Makefile. Check caldera_repo_url in terraform.tfvars.'; exit 1)",
      "echo 'Cloud-init done. Docker version:'",
      "docker --version",
      "echo 'Python version:'",
      "python3 --version",
    ]
  }
}

# ---------------------------------------------------------------------------
# Run the analysis
# ---------------------------------------------------------------------------

resource "null_resource" "run_analysis" {
  depends_on = [hcloud_server.runner]

  triggers = {
    # Re-run if any input changes
    repo_url   = var.repo_url
    server_id  = hcloud_server.runner.id
    skip_tools = var.skip_tools
  }

  connection {
    type        = "ssh"
    user        = "root"
    private_key = file(pathexpand(var.ssh_private_key_path))
    host        = hcloud_server.runner.ipv4_address
    timeout     = "60m"
  }

  # Upload the run script
  provisioner "file" {
    source      = "${path.module}/run-analysis.sh"
    destination = "/opt/caldera/run-analysis.sh"
  }

  # Upload API key as a secrets file (avoids exposing in ps/command-line)
  provisioner "file" {
    content     = "ANTHROPIC_API_KEY='${var.anthropic_api_key}'"
    destination = "/opt/caldera/.env.secrets"
  }

  # Execute the analysis
  provisioner "remote-exec" {
    inline = [
      "chmod +x /opt/caldera/run-analysis.sh",
      "chmod 600 /opt/caldera/.env.secrets",
      "trap 'rm -f /opt/caldera/.env.secrets' EXIT && set -a && . /opt/caldera/.env.secrets && set +a && REPO_URL='${var.repo_url}' SKIP_TOOLS='${var.skip_tools}' PIPELINE_LLM='${var.pipeline_llm}' MAX_PARALLEL='${var.max_parallel}' SERVER_TYPE='${var.server_type}' CLONE_DEPTH='${var.clone_depth}' /opt/caldera/run-analysis.sh",
    ]
  }

  # Download results to local machine (with retry for transient network failures)
  provisioner "local-exec" {
    command = <<-EOT
      set -e
      mkdir -p "${var.results_dir}"
      MAX_RETRIES=3
      RETRY_DELAY=10
      attempt=1
      while [ "$attempt" -le "$MAX_RETRIES" ]; do
        echo ">>> SCP download attempt $attempt of $MAX_RETRIES..."
        if scp -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30 \
            -i ${pathexpand(var.ssh_private_key_path)} \
            -r root@${hcloud_server.runner.ipv4_address}:/opt/caldera/results/* \
            "${var.results_dir}/"; then
          break
        fi
        if [ "$attempt" -eq "$MAX_RETRIES" ]; then
          echo "ERROR: SCP failed after $MAX_RETRIES attempts"
          exit 1
        fi
        echo "  SCP failed, retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
        RETRY_DELAY=$((RETRY_DELAY * 2))
        attempt=$((attempt + 1))
      done
      # Verify manifest.json was downloaded and is non-empty
      MANIFEST=$(find "${var.results_dir}" -name "manifest.json" -maxdepth 4 | head -1)
      if [ -z "$MANIFEST" ]; then
        echo "ERROR: No manifest.json found in downloaded results. SCP may have failed silently."
        exit 1
      fi
      # Verify DuckDB was downloaded and is non-empty
      DUCKDB=$(find "${var.results_dir}" -name "*.duckdb" -maxdepth 4 | head -1)
      if [ -z "$DUCKDB" ]; then
        echo "WARNING: No DuckDB database found in downloaded results."
      elif [ ! -s "$DUCKDB" ]; then
        echo "ERROR: DuckDB file downloaded but is empty (0 bytes). Download may be corrupted."
        exit 1
      fi
      echo ""
      echo "========================================"
      echo "Results downloaded to: ${var.results_dir}"
      echo "========================================"
    EOT
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "server_ip" {
  description = "Server IP address (for manual SSH if needed)"
  value       = hcloud_server.runner.ipv4_address
}

output "server_name" {
  description = "Server name"
  value       = hcloud_server.runner.name
}

output "results_dir" {
  description = "Local directory where results were downloaded"
  value       = var.results_dir
}
