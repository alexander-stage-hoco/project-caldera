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

WORK_DIR="/opt/caldera"
RESULTS_DIR="${WORK_DIR}/results"
CALDERA_DIR="${WORK_DIR}/project"
CLONE_DIR="/tmp/target-repo"

echo "=============================================="
echo "Caldera Cloud Runner"
echo "=============================================="
echo "Target repo:    ${REPO_URL}"
echo "Server type:    ${SERVER_TYPE}"
echo "Skip tools:     ${SKIP_TOOLS:-none}"
echo "LLM eval:       ${PIPELINE_LLM}"
echo "Max parallel:   ${MAX_PARALLEL}"
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

if echo "${REPO_URL}" | grep -qE '^https?://'; then
    git clone "${REPO_URL}" "${CLONE_DIR}"
elif echo "${REPO_URL}" | grep -qE '^git@'; then
    git clone "${REPO_URL}" "${CLONE_DIR}"
else
    echo "ERROR: REPO_URL must be a git URL (https:// or git@)"
    echo "Local paths are not supported in cloud mode."
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
for tool_dir in src/tools/*/; do
    tool_name=$(basename "$tool_dir")
    # Skip tools that are in SKIP_TOOLS
    if echo ",${SKIP_TOOLS}," | grep -q ",${tool_name},"; then
        echo "  Skipping setup for ${tool_name} (in SKIP_TOOLS)"
        continue
    fi
    echo "  Setting up ${tool_name}..."
    make -C "$tool_dir" setup 2>&1 | tail -3 || echo "  WARNING: ${tool_name} setup failed (will be skipped during analyze)"
done

# ---------------------------------------------------------------------------
# 5. Run the analysis pipeline
# ---------------------------------------------------------------------------

echo ""
echo ">>> Running analysis pipeline..."
START_TIME=$(date +%s)

make analyze \
    REPO="${CLONE_DIR}" \
    SKIP_TOOLS="${SKIP_TOOLS}" \
    PIPELINE_LLM="${PIPELINE_LLM}" \
    CONTINUE_ON_TOOL_FAILURE=1 \
    REPLACE=1 \
    2>&1 | tee /tmp/caldera-run.log

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo ">>> Pipeline completed in ${DURATION} seconds."

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
import json, datetime, os

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

cloud_section = {
    'mode': 'cloud-hetzner',
    'server_type': '${SERVER_TYPE}',
    'started_at': datetime.datetime.fromtimestamp(${START_TIME}, tz=datetime.timezone.utc).isoformat(),
    'completed_at': datetime.datetime.fromtimestamp(${END_TIME}, tz=datetime.timezone.utc).isoformat(),
    'duration_seconds': ${DURATION},
    'skip_tools': '${SKIP_TOOLS}'.split(',') if '${SKIP_TOOLS}' else [],
    'pipeline_llm': bool(int('${PIPELINE_LLM}')),
    'run_pk': int('${RUN_PK}') if '${RUN_PK}' else None,
}
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
