#!/usr/bin/env bash
# Insights test runner for pre-commit hook
#
# Runs insights unit tests when src/insights/ files are modified to catch
# regressions before they reach CI (Gate A).
#
# Exit codes:
#   0 - All tests passed (or no insights files modified)
#   1 - One or more tests failed

set -euo pipefail

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

# Colors for output (disabled if not a terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    BLUE=''
    NC=''
fi

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
}

# Check if venv Python exists
if [[ ! -f "${VENV_PYTHON}" ]]; then
    log_error "Virtual environment not found: ${VENV_PYTHON}"
    log_info "Run 'make setup' to create the virtual environment"
    exit 1
fi

# Check for staged insights files
has_insights_changes() {
    # Check staged changes first
    if git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep -q '^src/insights/'; then
        return 0
    fi

    # Fall back to working tree changes (for manual runs)
    if git diff --name-only --diff-filter=ACMR 2>/dev/null | grep -q '^src/insights/'; then
        return 0
    fi

    return 1
}

main() {
    if ! has_insights_changes; then
        log_info "No insights files modified, skipping tests"
        exit 0
    fi

    log_info "Running insights tests..."
    echo ""

    if "${VENV_PYTHON}" -m pytest src/insights/tests \
        -m "not slow and not integration" \
        --tb=short -q; then
        echo ""
        log_success "All insights tests passed"
        exit 0
    else
        echo ""
        log_error "Commit blocked: Insights tests failed"
        log_info "Run 'pytest src/insights/tests -m \"not slow and not integration\"' for details"
        exit 1
    fi
}

main "$@"
