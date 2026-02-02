#!/usr/bin/env bash
# Tool compliance preflight check for pre-commit hook
#
# This script detects modified tool directories and runs preflight compliance
# checks to catch issues before they reach CI.
#
# Exit codes:
#   0 - All checks passed (or no tools modified)
#   1 - One or more compliance checks failed

set -euo pipefail

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS_DIR="${REPO_ROOT}/src/tools"
COMPLIANCE_SCRIPT="${REPO_ROOT}/src/tool-compliance/tool_compliance.py"

# Colors for output (disabled if not a terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
}

# Check if compliance script exists
if [[ ! -f "${COMPLIANCE_SCRIPT}" ]]; then
    log_error "Compliance script not found: ${COMPLIANCE_SCRIPT}"
    exit 1
fi

# Find Python interpreter
PYTHON="${PYTHON:-python3}"
if ! command -v "${PYTHON}" &> /dev/null; then
    log_error "Python interpreter not found: ${PYTHON}"
    exit 1
fi

# Get list of changed files in staged changes
get_staged_tool_dirs() {
    local tool_dirs=()

    # Get staged files that are in src/tools/
    while IFS= read -r file; do
        if [[ "${file}" =~ ^src/tools/([^/]+)/ ]]; then
            local tool_name="${BASH_REMATCH[1]}"
            local tool_dir="${TOOLS_DIR}/${tool_name}"

            # Only add if directory exists and not already in list
            if [[ -d "${tool_dir}" ]] && [[ ! " ${tool_dirs[*]:-} " =~ " ${tool_dir} " ]]; then
                tool_dirs+=("${tool_dir}")
            fi
        fi
    done < <(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)

    # If no staged changes found, try working tree changes (for manual runs)
    if [[ ${#tool_dirs[@]} -eq 0 ]]; then
        while IFS= read -r file; do
            if [[ "${file}" =~ ^src/tools/([^/]+)/ ]]; then
                local tool_name="${BASH_REMATCH[1]}"
                local tool_dir="${TOOLS_DIR}/${tool_name}"

                if [[ -d "${tool_dir}" ]] && [[ ! " ${tool_dirs[*]:-} " =~ " ${tool_dir} " ]]; then
                    tool_dirs+=("${tool_dir}")
                fi
            fi
        done < <(git diff --name-only --diff-filter=ACMR 2>/dev/null || true)
    fi

    printf '%s\n' "${tool_dirs[@]:-}"
}

# Run preflight check on a single tool
run_preflight() {
    local tool_dir="$1"
    local tool_name
    tool_name="$(basename "${tool_dir}")"

    log_info "Running preflight on: ${tool_name}"

    if "${PYTHON}" "${COMPLIANCE_SCRIPT}" "${tool_dir}" --preflight --quiet; then
        log_success "${tool_name}: All preflight checks passed"
        return 0
    else
        log_error "${tool_name}: Preflight checks failed"
        return 1
    fi
}

main() {
    local failed=0
    local checked=0

    log_info "Detecting modified tool directories..."

    # Get list of modified tool directories
    mapfile -t tool_dirs < <(get_staged_tool_dirs)

    if [[ ${#tool_dirs[@]} -eq 0 ]]; then
        log_info "No tool directories modified, skipping compliance checks"
        exit 0
    fi

    log_info "Found ${#tool_dirs[@]} modified tool(s): ${tool_dirs[*]##*/}"
    echo ""

    # Run preflight on each modified tool
    for tool_dir in "${tool_dirs[@]}"; do
        if [[ -n "${tool_dir}" ]]; then
            if ! run_preflight "${tool_dir}"; then
                ((failed++))
            fi
            ((checked++))
        fi
    done

    echo ""
    log_info "Checked ${checked} tool(s), ${failed} failed"

    if [[ ${failed} -gt 0 ]]; then
        echo ""
        log_error "Commit blocked: Fix compliance issues before committing"
        log_info "Run 'python ${COMPLIANCE_SCRIPT} <tool-dir> --preflight' for details"
        exit 1
    fi

    log_success "All compliance checks passed"
    exit 0
}

main "$@"
