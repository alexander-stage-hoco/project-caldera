#!/usr/bin/env bash
# =============================================================================
# run-analysis.sh — Runs a Caldera analysis on the remote VM
#
# Expected environment variables:
#   REPO_URL        — Target repository to analyze (required)
#   SKIP_TOOLS      — Comma-separated tools to skip (optional)
#   PIPELINE_LLM    — 0 or 1 (default: 0)
#   MAX_PARALLEL    — Max parallel tools (default: 4)
#   SERVER_TYPE     — Hetzner server type (for manifest metadata)
#   ANTHROPIC_API_KEY — Required if PIPELINE_LLM=1
#
# This script is uploaded to the VM by Terraform and executed via SSH.
# =============================================================================
set -euo pipefail

REPO_URL="${REPO_URL:?REPO_URL is required}"
SKIP_TOOLS="${SKIP_TOOLS:-}"
PIPELINE_LLM="${PIPELINE_LLM:-0}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"
SERVER_TYPE="${SERVER_TYPE:-unknown}"
CLONE_DEPTH="${CLONE_DEPTH:-}"
MAX_DURATION="${MAX_DURATION:-}"
MAX_COST="${MAX_COST:-}"

# When LLM evaluation is enabled, configure the Anthropic SDK provider
# (Claude Code CLI is not available on the VM)
if [ "${PIPELINE_LLM}" = "1" ] && [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    export ANTHROPIC_API_KEY
    export USE_ANTHROPIC_SDK=1
    export PIPELINE_PROVIDER=anthropic
elif [ "${PIPELINE_LLM}" = "1" ]; then
    echo "WARNING: PIPELINE_LLM=1 but ANTHROPIC_API_KEY is not set."
    echo "LLM evaluation will fail. Pass anthropic_api_key in terraform.tfvars."
fi

WORK_DIR="/opt/caldera"
RESULTS_DIR="${WORK_DIR}/results"
CALDERA_DIR="${WORK_DIR}/project"
CLONE_DIR="/tmp/target-repo"

# Scrub secrets file as early as possible (env vars already in memory from caller)
rm -f "${WORK_DIR}/.env.secrets"

echo "=============================================="
echo "Caldera Cloud Runner"
echo "=============================================="
echo "Target repo:    ${REPO_URL}"
echo "Server type:    ${SERVER_TYPE}"
echo "Skip tools:     ${SKIP_TOOLS:-none}"
echo "LLM eval:       ${PIPELINE_LLM}"
echo "Max parallel:   ${MAX_PARALLEL}"
if [ -n "${MAX_DURATION}" ] || [ -n "${MAX_COST}" ]; then
    echo "Max duration:   ${MAX_DURATION:-unlimited}"
    echo "Max cost:       ${MAX_COST:-unlimited} EUR"
fi
echo "=============================================="

# ---------------------------------------------------------------------------
# 1. Ensure Caldera project is available
# ---------------------------------------------------------------------------

if [ ! -d "${CALDERA_DIR}" ]; then
    echo "ERROR: Caldera project not found at ${CALDERA_DIR}"
    echo "Cloud-init may have failed to clone the repo."
    echo "Set caldera_repo_url in Terraform variables to a valid, accessible Git URL."
    exit 1
fi

if [ ! -f "${CALDERA_DIR}/Makefile" ]; then
    echo "ERROR: Caldera project at ${CALDERA_DIR} is missing Makefile."
    echo "The clone may be incomplete or the wrong repository was specified."
    echo "Check caldera_repo_url in terraform.tfvars."
    exit 1
fi

cd "${CALDERA_DIR}"

# Disk space pre-flight check
AVAIL_GB=$(df --output=avail / | tail -1 | awk '{print int($1/1048576)}')
if [ "${AVAIL_GB}" -lt 10 ]; then
    echo "WARNING: Only ${AVAIL_GB} GB disk space available. Large repos may exhaust disk."
fi

# ---------------------------------------------------------------------------
# 2. Set up Caldera project environment
# ---------------------------------------------------------------------------

echo ""
echo ">>> Setting up Caldera project..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

# ---------------------------------------------------------------------------
# 3. Clone the target repository
# ---------------------------------------------------------------------------

echo ""
echo ">>> Cloning target repository..."
rm -rf "${CLONE_DIR}"

if ! echo "${REPO_URL}" | grep -qE '^(https?://|git@)'; then
    echo "ERROR: REPO_URL must be a git URL (https:// or git@)"
    echo "Local paths are not supported in cloud mode."
    exit 1
fi

CLONE_OK=0
CLONE_DEPTH_ARGS=""
if [ -n "${CLONE_DEPTH}" ]; then
    CLONE_DEPTH_ARGS="--depth=${CLONE_DEPTH}"
    echo "  Using shallow clone (depth=${CLONE_DEPTH})"

    HISTORY_TOOLS="git-fame git-blame-scanner gitleaks"
    HISTORY_WARN=""
    for ht in ${HISTORY_TOOLS}; do
        if ! echo ",${SKIP_TOOLS}," | grep -q ",${ht},"; then
            HISTORY_WARN="${HISTORY_WARN} ${ht}"
        fi
    done
    if [ -n "${HISTORY_WARN}" ]; then
        echo "  WARNING: Shallow clone may produce incomplete results for:${HISTORY_WARN}"
        echo "  Consider --skip or full clone for accurate history analysis."
    fi
fi
for clone_attempt in 1 2 3; do
    echo "  Clone attempt ${clone_attempt} of 3..."
    if git clone ${CLONE_DEPTH_ARGS} "${REPO_URL}" "${CLONE_DIR}"; then
        CLONE_OK=1
        break
    fi
    if [ "${clone_attempt}" -lt 3 ]; then
        echo "  Clone failed, retrying in 10s..."
        rm -rf "${CLONE_DIR}"
        sleep 10
    fi
done

if [ "${CLONE_OK}" -eq 0 ]; then
    echo "ERROR: git clone failed after 3 attempts."
    exit 1
fi

# Compute repo ID from URL
REPO_ID=$(python3 -c "
import sys, hashlib, urllib.parse
u = sys.argv[1]
p = urllib.parse.urlparse(u)
name = p.path.rstrip('/').split('/')[-1]
name = name[:-4] if name.endswith('.git') else name
h = hashlib.sha1(u.encode()).hexdigest()[:10]
print(f'{name}-{h}')
" "${REPO_URL}" 2>/dev/null || echo "remote-repo")

echo "Repo ID: ${REPO_ID}"

# ---------------------------------------------------------------------------
# 4. Set up tools
# ---------------------------------------------------------------------------

# Tools requiring .NET SDK won't work on this VM unless dotnet is installed.
# Auto-skip them if dotnet is unavailable.
DOTNET_SKIP=""
if ! command -v dotnet &>/dev/null; then
    echo ">>> dotnet not found — auto-skipping devskim, dotcover, roslyn-analyzers"
    DOTNET_SKIP="devskim,dotcover,roslyn-analyzers"
    if [ -n "${SKIP_TOOLS}" ]; then
        SKIP_TOOLS="${SKIP_TOOLS},${DOTNET_SKIP}"
    else
        SKIP_TOOLS="${DOTNET_SKIP}"
    fi
fi

# SonarQube requires Docker Compose to run its containers.
# Auto-skip if neither 'docker compose' nor 'docker-compose' is available.
if ! docker compose version &>/dev/null && ! command -v docker-compose &>/dev/null; then
    echo ">>> Docker Compose not found — auto-skipping sonarqube"
    if [ -n "${SKIP_TOOLS}" ]; then
        SKIP_TOOLS="${SKIP_TOOLS},sonarqube"
    else
        SKIP_TOOLS="sonarqube"
    fi
fi

echo ""
echo ">>> Setting up tools (best-effort, failures are non-fatal)..."
# Run setup for each tool individually so one failure doesn't block others.
# Tools that fail setup will also fail during analyze and be reported there.
SETUP_OK=0
SETUP_FAIL=0
SETUP_SKIP=0
SETUP_FAILED_NAMES=""
for tool_dir in src/tools/*/; do
    tool_name=$(basename "$tool_dir")
    # Skip tools that are in SKIP_TOOLS
    if echo ",${SKIP_TOOLS}," | grep -q ",${tool_name},"; then
        echo "  Skipping setup for ${tool_name} (in SKIP_TOOLS)"
        SETUP_SKIP=$((SETUP_SKIP + 1))
        continue
    fi
    echo "  Setting up ${tool_name}..."
    if make -C "$tool_dir" setup 2>&1 | tail -3; then
        SETUP_OK=$((SETUP_OK + 1))
    else
        echo "  WARNING: ${tool_name} setup failed (will be skipped during analyze)"
        SETUP_FAIL=$((SETUP_FAIL + 1))
        SETUP_FAILED_NAMES="${SETUP_FAILED_NAMES} ${tool_name}"
    fi
done

echo ""
echo "  Tool setup summary: ${SETUP_OK} succeeded, ${SETUP_FAIL} failed, ${SETUP_SKIP} skipped"
if [ "${SETUP_FAIL}" -gt 0 ]; then
    echo "  Failed:${SETUP_FAILED_NAMES}"
fi

# ---------------------------------------------------------------------------
# 5. Run the analysis pipeline
# ---------------------------------------------------------------------------

echo ""
echo ">>> Running analysis pipeline..."
START_TIME=$(date +%s)

# Budget guard: compute effective timeout for make analyze
ANALYSIS_TIMEOUT=""
BUDGET_GUARD_TRIGGERED=false

if [ -n "${MAX_COST}" ] && [ -n "${SERVER_TYPE}" ]; then
    COST_DURATION=$(python3 -c "
import json, math, sys
with open('/opt/caldera/project/infra/server_presets.json') as f:
    data = json.load(f)
rate = data['pricing_eur_per_hour'].get('${SERVER_TYPE}', 0)
if rate <= 0:
    print('')
    sys.exit(0)
max_hours = math.floor(float('${MAX_COST}') / rate)
if max_hours < 1:
    print(f'ERROR: MAX_COST ${MAX_COST} EUR < 1 billable hour (EUR {rate:.3f}/hr for ${SERVER_TYPE}). '
          f'Set MAX_COST >= {rate:.3f} or remove it.', file=sys.stderr)
    sys.exit(1)
print(str(max_hours * 3600))
" 2>&1)
    COST_EXIT=$?
    if [ $COST_EXIT -ne 0 ]; then
        echo "${COST_DURATION}"
        exit 1
    fi
    if [ -n "${COST_DURATION}" ]; then
        echo "  Budget guard: --max-cost ${MAX_COST} EUR -> ${COST_DURATION}s for ${SERVER_TYPE}"
        ANALYSIS_TIMEOUT="${COST_DURATION}"
    fi
fi

if [ -n "${MAX_DURATION}" ]; then
    echo "  Budget guard: --max-duration ${MAX_DURATION}s"
    if [ -z "${ANALYSIS_TIMEOUT}" ]; then
        ANALYSIS_TIMEOUT="${MAX_DURATION}"
    elif [ "${MAX_DURATION}" -lt "${ANALYSIS_TIMEOUT}" ]; then
        ANALYSIS_TIMEOUT="${MAX_DURATION}"
    fi
fi

if [ -n "${ANALYSIS_TIMEOUT}" ]; then
    echo "  Effective analysis timeout: ${ANALYSIS_TIMEOUT}s ($(( ANALYSIS_TIMEOUT / 60 ))m)"
fi

set +e
if [ -n "${ANALYSIS_TIMEOUT}" ]; then
    timeout --signal=TERM --kill-after=30 "${ANALYSIS_TIMEOUT}" \
        make analyze \
            REPO="${CLONE_DIR}" \
            SKIP_TOOLS="${SKIP_TOOLS}" \
            PIPELINE_LLM="${PIPELINE_LLM}" \
            ${PIPELINE_PROVIDER:+PIPELINE_PROVIDER=${PIPELINE_PROVIDER}} \
            CONTINUE_ON_TOOL_FAILURE=1 \
            REPLACE=1 \
            2>&1 | tee /tmp/caldera-run.log
    ANALYSIS_EXIT=${PIPESTATUS[0]}
else
    make analyze \
        REPO="${CLONE_DIR}" \
        SKIP_TOOLS="${SKIP_TOOLS}" \
        PIPELINE_LLM="${PIPELINE_LLM}" \
        ${PIPELINE_PROVIDER:+PIPELINE_PROVIDER=${PIPELINE_PROVIDER}} \
        CONTINUE_ON_TOOL_FAILURE=1 \
        REPLACE=1 \
        2>&1 | tee /tmp/caldera-run.log
    ANALYSIS_EXIT=${PIPESTATUS[0]}
fi
set -e

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "${ANALYSIS_EXIT}" -eq 124 ]; then
    BUDGET_GUARD_TRIGGERED=true
    echo ""
    echo ">>> BUDGET GUARD: Analysis terminated after ${DURATION}s (limit: ${ANALYSIS_TIMEOUT}s)"
    echo ">>> Exporting partial results..."
elif [ "${ANALYSIS_EXIT}" -ne 0 ]; then
    echo ""
    echo ">>> Pipeline exited with code ${ANALYSIS_EXIT}. Exporting whatever results exist..."
else
    echo ""
    echo ">>> Pipeline completed in ${DURATION} seconds."
fi

# ---------------------------------------------------------------------------
# 6. Export results
# ---------------------------------------------------------------------------

echo ""
echo ">>> Exporting results..."

# Find the latest run identifiers
DB_PATH="${HOME}/.caldera/caldera_sot.duckdb"
RUN_ID=$(
  .venv/bin/python -c "import duckdb; import pathlib; p=pathlib.Path('${DB_PATH}'); \
conn=duckdb.connect(str(p), read_only=True); \
row=conn.execute(\"SELECT collection_run_id FROM lz_collection_runs ORDER BY started_at DESC LIMIT 1\").fetchone(); \
print(row[0] if row else ''); conn.close()" 2>/dev/null || echo ""
)
RUN_PK=$(.venv/bin/python scripts/get_latest_run_pk.py --db "${DB_PATH}" 2>/dev/null || echo "")

if [ -z "${RUN_ID}" ]; then
    RUN_ID="unknown-run"
    echo "WARNING: Could not determine latest run ID. Exporting under ${RUN_ID}."
fi

EXPORT_DIR="${RESULTS_DIR}/${REPO_ID}/${RUN_ID}"
mkdir -p "${EXPORT_DIR}"

# Copy DuckDB database
if [ -f "${DB_PATH}" ]; then
    mkdir -p "${EXPORT_DIR}/database"
    cp "${DB_PATH}" "${EXPORT_DIR}/database/caldera_sot.duckdb"
    echo "  Copied DuckDB ($(du -h "${DB_PATH}" | cut -f1))"
fi

# Copy reports
REPORT_DIR="src/insights/output/pipeline"
if [ -d "${REPORT_DIR}" ]; then
    mkdir -p "${EXPORT_DIR}/reports"
    cp -r "${REPORT_DIR}"/* "${EXPORT_DIR}/reports/" 2>/dev/null || true
    echo "  Copied reports"
fi

# Copy run log
cp /tmp/caldera-run.log "${EXPORT_DIR}/run.log"

# Resolve commit from cloned repo
TARGET_COMMIT=$(cd "${CLONE_DIR}" 2>/dev/null && git rev-parse HEAD 2>/dev/null || printf '%0.s0' {1..40})

# Write manifest (aligned with canonical bundle schema from collect_artifacts.py)
# Note: the cloud runner uses `make analyze` (LOCAL mode on the VM), so the export
# contains DuckDB + reports, not raw tool bundles.  The top-level keys match the
# canonical schema; cloud-specific metadata lives under the `cloud` extension key.
python3 -c "
import json, datetime, os, math

# Read per-tool status from orchestrator summary (if available)
import glob as _glob
tools_list = []
try:
    _candidates = _glob.glob('${CALDERA_DIR}/${REPORT_DIR}/runs/*/*/tool_run_summary.json')
    _candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    with open(_candidates[0]) as f:
        summary = json.load(f)
    raw_tools = summary.get('steps', {}).get('tools', {}).get('tools', [])
    for t in raw_tools:
        tools_list.append({
            'tool_name': t.get('tool_name', ''),
            'status': t.get('status', 'unknown'),
            'duration_seconds': t.get('duration_seconds'),
            'error': t.get('error'),
        })
except (FileNotFoundError, json.JSONDecodeError, KeyError, IndexError):
    pass  # Fall back to empty list

# Read dbt summary (if available)
dbt_info = None
try:
    _candidates = _glob.glob('${CALDERA_DIR}/${REPORT_DIR}/runs/*/*/dbt_summary.json')
    _candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    with open(_candidates[0]) as f:
        dbt_info = json.load(f)
except (FileNotFoundError, json.JSONDecodeError, IndexError):
    pass

# Pricing lookup — inline dict mirrors infra/server_presets.json
_pricing = {'cx23': 0.007, 'cx33': 0.013, 'cx43': 0.025, 'cx53': 0.050}
_hourly_rate = _pricing.get('${SERVER_TYPE}', 0.0)
_billable_hours = math.ceil(${DURATION} / 3600) if ${DURATION} > 0 else 0
_estimated_cost = round(_billable_hours * _hourly_rate, 4)

cloud_section = {
    'mode': 'cloud-hetzner',
    'server_type': '${SERVER_TYPE}',
    'started_at': datetime.datetime.fromtimestamp(${START_TIME}, tz=datetime.timezone.utc).isoformat(),
    'completed_at': datetime.datetime.fromtimestamp(${END_TIME}, tz=datetime.timezone.utc).isoformat(),
    'duration_seconds': ${DURATION},
    'estimated_cost_eur': _estimated_cost,
    'pricing_eur_per_hour': _hourly_rate,
    'billable_hours': _billable_hours,
    'skip_tools': '${SKIP_TOOLS}'.split(',') if '${SKIP_TOOLS}' else [],
    'pipeline_llm': bool(int('${PIPELINE_LLM}')),
    'run_pk': int('${RUN_PK}') if '${RUN_PK}' else None,
}
budget_guard = {
    'max_duration': int('${MAX_DURATION}') if '${MAX_DURATION}' else None,
    'max_cost': float('${MAX_COST}') if '${MAX_COST}' else None,
    'effective_timeout': int('${ANALYSIS_TIMEOUT}') if '${ANALYSIS_TIMEOUT}' else None,
    'triggered': True if '${BUDGET_GUARD_TRIGGERED}' == 'true' else False,
    'analysis_exit_code': ${ANALYSIS_EXIT},
}
cloud_section['budget_guard'] = budget_guard

if dbt_info is not None:
    cloud_section['dbt'] = dbt_info

manifest = {
    'schema_version': 1,
    'created_at': datetime.datetime.fromtimestamp(${END_TIME}, tz=datetime.timezone.utc).isoformat(),
    'bundle_root': '${EXPORT_DIR}',
    'repo': {
        'repo_id': '${REPO_ID}',
        'repo_path': '${CLONE_DIR}',
        'is_git': True,
        'branch': 'HEAD',
        'commit': '${TARGET_COMMIT}',
    },
    'run_id': '${RUN_ID}' if '${RUN_ID}' else None,
    'tools': tools_list,
    'cloud': cloud_section,
    'exports': {
        'database': 'database/caldera_sot.duckdb' if os.path.isdir('${EXPORT_DIR}/database') else None,
        'reports': 'reports/' if os.path.isdir('${EXPORT_DIR}/reports') else None,
        'run_log': 'run.log',
    },
}
with open('${EXPORT_DIR}/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
print('  Wrote manifest.json')
"

# ---------------------------------------------------------------------------
# 7. Validate results
# ---------------------------------------------------------------------------

echo ""
echo ">>> Validating results..."

VALIDATION_ERRORS=0

if [ ! -f "${EXPORT_DIR}/manifest.json" ]; then
    echo "ERROR: manifest.json not found in ${EXPORT_DIR}"
    VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ ! -f "${EXPORT_DIR}/database/caldera_sot.duckdb" ]; then
    echo "WARNING: DuckDB database not found in results"
fi

if [ ! -d "${EXPORT_DIR}/reports" ] || [ -z "$(ls -A "${EXPORT_DIR}/reports" 2>/dev/null)" ]; then
    echo "WARNING: No reports found in results"
fi

if [ "${VALIDATION_ERRORS}" -gt 0 ]; then
    echo "ERROR: Results validation failed with ${VALIDATION_ERRORS} error(s)."
    exit 1
fi

echo "  Results validation passed."

echo ""
echo "=============================================="
echo "Results exported to: ${EXPORT_DIR}"
echo "Contents:"
du -sh "${EXPORT_DIR}"/*
echo "=============================================="
