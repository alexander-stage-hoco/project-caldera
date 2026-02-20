#!/usr/bin/env bash
# =============================================================================
# cloud-run.sh — One-command cloud analysis via Hetzner + Terraform
#
# Usage:
#   ./scripts/cloud-run.sh https://github.com/org/repo
#   ./scripts/cloud-run.sh https://github.com/org/repo --server cx42 --skip sonarqube
#
# Prerequisites:
#   1. terraform installed (brew install terraform)
#   2. infra/terraform.tfvars configured with hcloud_token + caldera_repo_url
#   3. SSH key at ~/.ssh/id_ed25519 (or override via tfvars)
#
# This script:
#   1. terraform apply  — creates VM + runs analysis + downloads results
#   2. terraform destroy — tears down the VM
#   3. Prints results location
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INFRA_DIR="${PROJECT_ROOT}/infra"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

REPO_URL=""
SERVER_TYPE="cx33"
SKIP_TOOLS=""
PIPELINE_LLM=0
MAX_PARALLEL=4
RESULTS_DIR="${INFRA_DIR}/results"
DESTROY_AFTER=1

usage() {
    echo "Usage: $0 <repo-url> [options]"
    echo ""
    echo "Arguments:"
    echo "  <repo-url>              Git URL of the repository to analyze (required)"
    echo ""
    echo "Options:"
    echo "  --server <type>         Hetzner server type (default: cx33)"
    echo "                          cx23=2vCPU/4GB, cx33=4/8, cx43=8/16, cx53=16/32"
    echo "  --skip <tools>          Comma-separated tools to skip"
    echo "  --llm                   Enable LLM evaluation (needs ANTHROPIC_API_KEY in tfvars)"
    echo "  --parallel <n>          Max parallel tools (default: 4)"
    echo "  --results <dir>         Local results directory (default: infra/results)"
    echo "  --keep-server           Don't destroy the server after (for debugging)"
    echo "  -h, --help              Show this help"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --server)    SERVER_TYPE="$2"; shift 2 ;;
        --skip)      SKIP_TOOLS="$2"; shift 2 ;;
        --llm)       PIPELINE_LLM=1; shift ;;
        --parallel)  MAX_PARALLEL="$2"; shift 2 ;;
        --results)   RESULTS_DIR="$2"; shift 2 ;;
        --keep-server) DESTROY_AFTER=0; shift ;;
        -h|--help)   usage ;;
        -*)          echo "Unknown option: $1"; usage ;;
        *)           REPO_URL="$1"; shift ;;
    esac
done

if [ -z "${REPO_URL}" ]; then
    echo "ERROR: Repository URL is required."
    echo ""
    usage
fi

# ---------------------------------------------------------------------------
# Validate prerequisites
# ---------------------------------------------------------------------------

if ! command -v terraform &>/dev/null; then
    echo "ERROR: terraform is not installed."
    echo "Install with: brew install terraform"
    exit 1
fi

if [ ! -f "${INFRA_DIR}/terraform.tfvars" ]; then
    echo "ERROR: infra/terraform.tfvars not found."
    echo ""
    echo "Copy the example and fill in your values:"
    echo "  cp infra/terraform.tfvars.example infra/terraform.tfvars"
    echo "  # Edit infra/terraform.tfvars with your Hetzner API token"
    exit 1
fi

# Check SSH key exists (read path from tfvars or use default)
SSH_KEY_PATH=$(grep -E '^\s*ssh_private_key_path\s*=' "${INFRA_DIR}/terraform.tfvars" 2>/dev/null \
    | sed 's/.*=\s*"\(.*\)"/\1/' | sed "s|~|${HOME}|" || true)
SSH_KEY_PATH="${SSH_KEY_PATH:-${HOME}/.ssh/id_ed25519}"

if [ ! -f "${SSH_KEY_PATH}" ]; then
    echo "ERROR: SSH private key not found at: ${SSH_KEY_PATH}"
    echo ""
    echo "Either:"
    echo "  1. Generate a key:  ssh-keygen -t ed25519"
    echo "  2. Or set ssh_private_key_path in infra/terraform.tfvars to your existing key"
    echo ""
    echo "Common key locations:"
    ls -1 "${HOME}/.ssh/id_"* 2>/dev/null | sed 's/^/    /' || echo "    (no keys found in ~/.ssh/)"
    exit 1
fi

# ---------------------------------------------------------------------------
# Run Terraform
# ---------------------------------------------------------------------------

cd "${INFRA_DIR}"

echo "=============================================="
echo "Caldera Cloud Run"
echo "=============================================="
echo "Target:     ${REPO_URL}"
echo "Server:     ${SERVER_TYPE}"
echo "Skip:       ${SKIP_TOOLS:-none}"
echo "LLM:        ${PIPELINE_LLM}"
echo "Parallel:   ${MAX_PARALLEL}"
echo "Results:    ${RESULTS_DIR}"
echo "=============================================="
echo ""

# Initialize Terraform (idempotent)
terraform init -input=false -no-color 2>&1 | grep -E "^(Initializing|Terraform has been)" || true

# Plan and apply
echo ">>> Creating server and running analysis..."
echo "    (This takes 10–30 minutes depending on repo size and server type)"
echo ""

terraform apply \
    -auto-approve \
    -var="repo_url=${REPO_URL}" \
    -var="server_type=${SERVER_TYPE}" \
    -var="skip_tools=${SKIP_TOOLS}" \
    -var="pipeline_llm=${PIPELINE_LLM}" \
    -var="max_parallel=${MAX_PARALLEL}" \
    -var="results_dir=${RESULTS_DIR}"

echo ""

# ---------------------------------------------------------------------------
# Tear down (unless --keep-server)
# ---------------------------------------------------------------------------

if [ "${DESTROY_AFTER}" -eq 1 ]; then
    echo ">>> Destroying server..."
    terraform destroy \
        -auto-approve \
        -var="repo_url=${REPO_URL}" \
        -var="server_type=${SERVER_TYPE}" \
        -var="skip_tools=${SKIP_TOOLS}" \
        -var="pipeline_llm=${PIPELINE_LLM}" \
        -var="max_parallel=${MAX_PARALLEL}" \
        -var="results_dir=${RESULTS_DIR}" \
        2>&1 | grep -E "^(Destroy|hcloud_)" || true
    echo "    Server destroyed."
else
    SERVER_IP=$(terraform output -raw server_ip 2>/dev/null || echo "unknown")
    echo ">>> Server kept alive at: ${SERVER_IP}"
    echo "    SSH: ssh root@${SERVER_IP}"
    echo "    Destroy later: cd infra && terraform destroy"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Verify results were downloaded
# ---------------------------------------------------------------------------

if [ ! -d "${RESULTS_DIR}" ] || [ -z "$(ls -A "${RESULTS_DIR}" 2>/dev/null)" ]; then
    echo ""
    echo "ERROR: Results directory is empty or missing: ${RESULTS_DIR}"
    echo "The analysis may have failed or SCP download was incomplete."
    echo "Use KEEP_SERVER=1 to debug on the VM."
    exit 1
fi

MANIFEST=$(find "${RESULTS_DIR}" -name "manifest.json" -maxdepth 4 2>/dev/null | head -1)
if [ -z "${MANIFEST}" ]; then
    echo ""
    echo "ERROR: No manifest.json found in ${RESULTS_DIR}"
    echo "Results download may be incomplete."
    exit 1
fi

echo ""
echo "=============================================="
echo "Done!"
echo "=============================================="
echo ""
echo "Results: ${RESULTS_DIR}/"

if [ -d "${RESULTS_DIR}" ]; then
    echo ""
    ls -la "${RESULTS_DIR}/"

    # Find and show manifest
    MANIFEST=$(find "${RESULTS_DIR}" -name "manifest.json" -maxdepth 3 2>/dev/null | head -1)
    if [ -n "${MANIFEST}" ]; then
        echo ""
        echo "Manifest:"
        python3 -m json.tool "${MANIFEST}" 2>/dev/null || cat "${MANIFEST}"
    fi

    # Find DuckDB
    DUCKDB=$(find "${RESULTS_DIR}" -name "*.duckdb" -maxdepth 4 2>/dev/null | head -1)
    if [ -n "${DUCKDB}" ]; then
        echo ""
        echo "Query the database:"
        echo "  duckdb ${DUCKDB}"
    fi

    # Find report
    REPORT=$(find "${RESULTS_DIR}" -name "*.html" -maxdepth 4 2>/dev/null | head -1)
    if [ -n "${REPORT}" ]; then
        echo ""
        echo "Open the report:"
        echo "  open ${REPORT}"
    fi
fi
