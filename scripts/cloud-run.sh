#!/usr/bin/env bash
# =============================================================================
# cloud-run.sh — One-command cloud analysis via Hetzner + Terraform
#
# Usage:
#   ./scripts/cloud-run.sh https://github.com/org/repo
#   ./scripts/cloud-run.sh https://github.com/org/repo --server cx42 --skip sonarqube --clone-depth 1
#
# Prerequisites:
#   1. terraform installed (brew install terraform)
#   2. .env configured with HCLOUD_TOKEN (see .env.example)
#      OR infra/terraform.tfvars with caldera_repo_url (secrets via .env)
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

# Load secrets from .env if present (when run outside Make)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Export Terraform variables from environment (so direct invocations work
# without the Makefile's TF_VAR_ exports, and secrets stay out of CLI args).
export TF_VAR_anthropic_api_key="${ANTHROPIC_API_KEY:-}"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

REPO_URL=""
SERVER_TYPE="cx33"
SKIP_TOOLS=""
PIPELINE_LLM=0
MAX_PARALLEL=4
CLONE_DEPTH="${CLONE_DEPTH:-}"
RESULTS_DIR="${INFRA_DIR}/results"
DESTROY_AFTER=1
MAX_DURATION=""
MAX_COST=""

usage() {
    echo "Usage: $0 <repo-url> [options]"
    echo ""
    echo "Arguments:"
    echo "  <repo-url>              Git URL of the repository to analyze (required)"
    echo ""
    echo "Options:"
    echo "  --server <type|preset>  Server type or preset name (default: medium)"
    echo "                          Presets: small (cx23), medium (cx33), large (cx43), xlarge (cx53)"
    echo "                          Or raw types: cx23=2vCPU/4GB, cx33=4/8, cx43=8/16, cx53=16/32"
    echo "  --skip <tools>          Comma-separated tools to skip"
    echo "  --llm                   Enable LLM evaluation (needs ANTHROPIC_API_KEY in tfvars)"
    echo "  --parallel <n>          Max parallel tools (default: 4)"
    echo "  --clone-depth <n>       Shallow clone depth (default: full clone)"
    echo "  --results <dir>         Local results directory (default: infra/results)"
    echo "  --keep-server           Don't destroy the server after (for debugging)"
    echo "  --max-duration <secs>   Kill analysis after this many seconds"
    echo "  --max-cost <eur>        Kill analysis when estimated cost exceeds this (EUR)"
    echo "  -h, --help              Show this help"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --server)    SERVER_TYPE="$2"; shift 2 ;;
        --skip)      SKIP_TOOLS="$2"; shift 2 ;;
        --llm)       PIPELINE_LLM=1; shift ;;
        --parallel)  MAX_PARALLEL="$2"; shift 2 ;;
        --clone-depth) CLONE_DEPTH="$2"; shift 2 ;;
        --results)   RESULTS_DIR="$2"; shift 2 ;;
        --keep-server) DESTROY_AFTER=0; shift ;;
        --max-duration) MAX_DURATION="$2"; shift 2 ;;
        --max-cost)     MAX_COST="$2"; shift 2 ;;
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
# Resolve server preset to Hetzner type
# ---------------------------------------------------------------------------

PRESETS_FILE="${INFRA_DIR}/server_presets.json"

resolve_preset() {
    local input="$1"
    if [ -f "${PRESETS_FILE}" ]; then
        # Try to resolve via Python (handles both preset names and raw types)
        local resolved
        resolved=$(python3 -c "
import json, sys
with open('${PRESETS_FILE}') as f:
    data = json.load(f)
name = sys.argv[1]
if name in data['presets']:
    print(data['presets'][name]['server_type'])
elif name in data['pricing_eur_per_hour']:
    print(name)
else:
    print(name)  # pass through unknown types
" "$input" 2>/dev/null)
        echo "${resolved:-$input}"
    else
        echo "$input"
    fi
}

SERVER_TYPE=$(resolve_preset "${SERVER_TYPE}")

# Print server specs and cost rate
if [ -f "${PRESETS_FILE}" ]; then
    python3 -c "
import json, sys
with open('${PRESETS_FILE}') as f:
    data = json.load(f)
st = sys.argv[1]
rate = data['pricing_eur_per_hour'].get(st)
if rate:
    # Find matching preset for use_case info
    info = ''
    for name, p in data['presets'].items():
        if p['server_type'] == st:
            info = f\" ({p['vcpu']} vCPU, {p['ram_gb']} GB RAM — {p['use_case']})\"
            break
    print(f'Server: {st}{info}')
    print(f'Rate:   EUR {rate:.3f}/hour')
" "${SERVER_TYPE}" 2>/dev/null || true
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

# ---------------------------------------------------------------------------
# Trap: ensure VM cleanup on interrupt (Ctrl-C, TERM, or script exit)
# ---------------------------------------------------------------------------

cleanup() {
    local exit_code=$?
    if [ "${DESTROY_AFTER}" -eq 1 ] && [ -f "${INFRA_DIR}/terraform.tfstate" ]; then
        # Skip destroy if state has no resources (already clean)
        if ! terraform -chdir="${INFRA_DIR}" state list 2>/dev/null | grep -q .; then
            exit $exit_code
        fi
        echo ""
        echo ">>> Cleaning up — destroying server..."
        if terraform destroy \
            -auto-approve \
            -var="repo_url=${REPO_URL}" \
            -var="server_type=${SERVER_TYPE}" \
            -var="skip_tools=${SKIP_TOOLS}" \
            -var="pipeline_llm=${PIPELINE_LLM}" \
            -var="max_parallel=${MAX_PARALLEL}" \
            -var="clone_depth=${CLONE_DEPTH}" \
            -var="results_dir=${RESULTS_DIR}" \
            -var="max_duration=${MAX_DURATION}" \
            -var="max_cost=${MAX_COST}"; then
            echo "    Server destroyed."
        else
            echo "    WARNING: terraform destroy failed. VM may still be running."
            echo "    Run 'make cloud-destroy' or check https://console.hetzner.cloud"
        fi
    fi
    exit $exit_code
}
trap cleanup EXIT

echo "=============================================="
echo "Caldera Cloud Run"
echo "=============================================="
echo "Target:     ${REPO_URL}"
echo "Server:     ${SERVER_TYPE}"
echo "Skip:       ${SKIP_TOOLS:-none}"
echo "LLM:        ${PIPELINE_LLM}"
echo "Parallel:   ${MAX_PARALLEL}"
echo "Results:    ${RESULTS_DIR}"
if [ -n "${MAX_DURATION}" ] || [ -n "${MAX_COST}" ]; then
    echo "Max dur:    ${MAX_DURATION:-unlimited}"
    echo "Max cost:   ${MAX_COST:-unlimited} EUR"
fi
echo "=============================================="
echo ""

# Initialize Terraform (idempotent)
echo ">>> Initializing Terraform..."
if ! terraform init -input=false -no-color; then
    echo ""
    echo "ERROR: terraform init failed."
    echo "Common causes:"
    echo "  1. Network connectivity issues"
    echo "  2. Terraform state corruption (try: rm -rf infra/.terraform && rm -f infra/.terraform.lock.hcl)"
    exit 1
fi

# Plan and apply (with retry for transient SSH/network failures)
echo ">>> Creating server and running analysis..."
echo "    (This takes 10–30 minutes depending on repo size and server type)"
echo ""

APPLY_FAILED=0
MAX_RETRIES=2
for attempt in $(seq 1 $MAX_RETRIES); do
    echo ">>> Terraform apply attempt $attempt of $MAX_RETRIES..."
    if terraform apply \
        -auto-approve \
        -var="repo_url=${REPO_URL}" \
        -var="server_type=${SERVER_TYPE}" \
        -var="skip_tools=${SKIP_TOOLS}" \
        -var="pipeline_llm=${PIPELINE_LLM}" \
        -var="max_parallel=${MAX_PARALLEL}" \
        -var="clone_depth=${CLONE_DEPTH}" \
        -var="results_dir=${RESULTS_DIR}" \
        -var="max_duration=${MAX_DURATION}" \
        -var="max_cost=${MAX_COST}"; then
        break
    fi
    if [ "$attempt" -eq "$MAX_RETRIES" ]; then
        echo "ERROR: terraform apply failed after $MAX_RETRIES attempts"
        APPLY_FAILED=1
        break
    fi
    echo "  terraform apply failed, retrying in 15s..."
    sleep 15
done

echo ""

# ---------------------------------------------------------------------------
# Keep-server message (destruction handled by EXIT trap above)
# ---------------------------------------------------------------------------

if [ "${DESTROY_AFTER}" -eq 0 ]; then
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

if [ "${APPLY_FAILED}" -eq 1 ]; then
    echo ""
    echo "ERROR: terraform apply failed — results were not downloaded."
    echo "Use --keep-server to debug on the VM."
    exit 1
fi

if [ ! -d "${RESULTS_DIR}" ] || [ -z "$(ls -A "${RESULTS_DIR}" 2>/dev/null)" ]; then
    echo ""
    echo "ERROR: Results directory is empty or missing: ${RESULTS_DIR}"
    echo "The analysis may have failed or SCP download was incomplete."
    echo "Use --keep-server to debug on the VM."
    exit 1
fi

MANIFEST=$(find "${RESULTS_DIR}" -name "manifest.json" -maxdepth 4 2>/dev/null \
    | xargs ls -t 2>/dev/null | head -1)
if [ -z "${MANIFEST}" ]; then
    echo ""
    echo "ERROR: No manifest.json found in ${RESULTS_DIR}"
    echo "Results download may be incomplete."
    exit 1
fi

# Validate manifest is valid JSON
if ! python3 -m json.tool "${MANIFEST}" >/dev/null 2>&1; then
    echo "ERROR: manifest.json is not valid JSON — download may be corrupted."
    exit 1
fi

# Warn if manifest is stale (> 4 hours old — may be from a previous run)
STALE=$(python3 -c "
import json, datetime, sys
with open('${MANIFEST}') as f:
    m = json.load(f)
ca = m.get('created_at', '')
if not ca:
    sys.exit(0)
dt = datetime.datetime.fromisoformat(ca)
age = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()
if age > 14400:
    print(f'Manifest is {age/3600:.1f}h old — may be from a previous run')
" 2>/dev/null || true)

if [ -n "${STALE}" ]; then
    echo "WARNING: ${STALE}"
fi

# Check DuckDB exists and is non-empty
DUCKDB_CHECK=$(find "${RESULTS_DIR}" -name "*.duckdb" -maxdepth 4 2>/dev/null | head -1)
if [ -z "${DUCKDB_CHECK}" ]; then
    echo "WARNING: No DuckDB database found in results."
elif [ ! -s "${DUCKDB_CHECK}" ]; then
    echo "WARNING: DuckDB database exists but is empty (0 bytes)."
fi

# Check reports directory has content
REPORTS_CHECK=$(find "${RESULTS_DIR}" -name "*.html" -maxdepth 5 2>/dev/null | head -1)
if [ -z "${REPORTS_CHECK}" ]; then
    echo "WARNING: No HTML reports found in results."
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

        # Display tool status summary
        python3 -c "
import json, sys

try:
    with open('${MANIFEST}') as f:
        m = json.load(f)
except Exception:
    sys.exit(0)

tools = m.get('tools', [])
if not tools:
    sys.exit(0)

print()
print('Tool Status Summary')
print('=' * 58)
print(f\"{'Tool':<28} {'Status':<12} {'Duration':>10}\")
print('-' * 58)

success = 0
failed = 0
for t in sorted(tools, key=lambda x: x.get('tool_name', '')):
    name = t.get('tool_name', '?')
    status = t.get('status', 'unknown')
    dur = t.get('duration_seconds')
    dur_str = f'{dur:.1f}s' if dur is not None else '—'

    if status == 'success':
        indicator = '\033[32m✓ success\033[0m'
        success += 1
    elif status == 'failed':
        indicator = '\033[31m✗ failed\033[0m'
        failed += 1
    else:
        indicator = f'  {status}'

    print(f'  {name:<26} {indicator:<21} {dur_str:>10}')

print('-' * 58)
total = len(tools)
print(f'  Total: {total}   Success: {success}   Failed: {failed}')

if failed > 0:
    fail_names = [t['tool_name'] for t in tools if t.get('status') == 'failed']
    print(f\"  \033[31mFailed tools: {', '.join(fail_names)}\033[0m\")
print('=' * 58)
" 2>/dev/null || true
    fi

    # Show cost summary from manifest
    if [ -n "${MANIFEST}" ]; then
        python3 -c "
import json, sys
try:
    with open('${MANIFEST}') as f:
        m = json.load(f)
    cloud = m.get('cloud', {})
    cost = cloud.get('estimated_cost_eur')
    if cost is not None:
        rate = cloud.get('pricing_eur_per_hour', 0)
        hours = cloud.get('billable_hours', 0)
        dur = cloud.get('duration_seconds', 0)
        st = cloud.get('server_type', '?')
        mins = dur // 60
        secs = dur % 60
        print()
        print('Cost Summary')
        print('=' * 42)
        print(f'  Server type:     {st}')
        print(f'  Duration:        {mins}m {secs}s')
        print(f'  Billable hours:  {hours}')
        print(f'  Rate:            EUR {rate:.3f}/hour')
        print(f'  Estimated cost:  EUR {cost:.4f}')
        print('=' * 42)
except Exception:
    pass
" 2>/dev/null || true
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
