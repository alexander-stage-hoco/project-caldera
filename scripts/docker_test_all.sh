#!/usr/bin/env bash
# Batch Docker vs native parity test runner for all Caldera tools.
#
# Usage:
#   ./scripts/docker_test_all.sh [--repo <path>] [--skip <comma-list>] [--parallel <N>]
#
# Defaults:
#   --repo .  --skip coverage-ingest  --parallel 1
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
REPO="."
SKIP="coverage-ingest"
PARALLEL=1
RESULTS_DIR=""

# ── All tools (same order as Makefile DOCKER_TOOLS) ───────────────────────────
ALL_TOOLS=(
  layout-scanner scc lizard semgrep symbol-scanner scancode
  git-blame-scanner git-fame dependensee coverage-ingest
  trivy gitleaks git-sizer pmd-cpd roslyn-analyzers devskim dotcover
)

# ── .NET tools auto-skip if dotnet not found ──────────────────────────────────
DOTNET_TOOLS="roslyn-analyzers devskim dotcover"

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)    REPO="$2"; shift 2 ;;
    --skip)    SKIP="$2"; shift 2 ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    --results-dir) RESULTS_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

REPO_ABS="$(cd "$REPO" && pwd)"
COMMIT_SHA="$(git -C "$REPO_ABS" rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")"

# Create results directory
if [[ -z "$RESULTS_DIR" ]]; then
  RESULTS_DIR="$(mktemp -d /tmp/caldera-parity-XXXXXX)"
fi
mkdir -p "$RESULTS_DIR"

PYTHON_VENV="$(pwd)/.venv/bin/python"

echo "=============================================="
echo "DOCKER vs NATIVE PARITY TEST"
echo "=============================================="
echo "Repository: $REPO_ABS"
echo "Commit:     $COMMIT_SHA"
echo "Skip:       $SKIP"
echo "Parallel:   $PARALLEL"
echo "Results:    $RESULTS_DIR"
echo "=============================================="
echo ""

# ── Build skip set ────────────────────────────────────────────────────────────
declare -A SKIP_SET
IFS=',' read -ra SKIP_ARRAY <<< "$SKIP"
for s in "${SKIP_ARRAY[@]}"; do
  s="$(echo "$s" | xargs)"  # trim whitespace
  [[ -n "$s" ]] && SKIP_SET["$s"]=1
done

# Auto-skip .NET tools if dotnet is not available
if ! command -v dotnet >/dev/null 2>&1; then
  echo "NOTE: dotnet not found — auto-skipping .NET tools ($DOTNET_TOOLS)"
  for tool in $DOTNET_TOOLS; do
    SKIP_SET["$tool"]=1
  done
  echo ""
fi

# ── Per-tool test function ────────────────────────────────────────────────────
run_tool_test() {
  local tool="$1"
  local native_out docker_out start_time end_time duration status

  native_out="$(mktemp -d /tmp/caldera-native-XXXXXX)"
  docker_out="$(mktemp -d /tmp/caldera-docker-XXXXXX)"
  start_time="$(date +%s)"

  echo "--- $tool ---"

  # Check Docker image exists
  if ! docker image inspect "caldera-tool-${tool}" >/dev/null 2>&1; then
    echo "  SKIP: Docker image caldera-tool-${tool} not found (build with: make docker-build-tool TOOL=${tool})"
    end_time="$(date +%s)"
    duration=$((end_time - start_time))
    printf '{"tool":"%s","status":"skip","diff_count":0,"diffs":[],"error":"Docker image not found","duration_seconds":%d}\n' \
      "$tool" "$duration" > "$RESULTS_DIR/${tool}.json"
    rm -rf "$native_out" "$docker_out"
    return 0
  fi

  # Native run
  echo "  Native run..."
  if ! make -C "src/tools/${tool}" analyze \
    REPO_PATH="$REPO_ABS" REPO_NAME=parity-test \
    OUTPUT_DIR="$native_out" RUN_ID=native-parity \
    REPO_ID=parity-test BRANCH=main COMMIT="$COMMIT_SHA" \
    >/dev/null 2>&1; then
    echo "  ERROR: Native run failed"
    end_time="$(date +%s)"
    duration=$((end_time - start_time))
    printf '{"tool":"%s","status":"error","diff_count":0,"diffs":[],"error":"Native run failed","duration_seconds":%d}\n' \
      "$tool" "$duration" > "$RESULTS_DIR/${tool}.json"
    rm -rf "$native_out" "$docker_out"
    return 0
  fi

  # Docker run
  echo "  Docker run..."
  if ! docker run --rm \
    -v "${REPO_ABS}":/repo:ro \
    -v "${docker_out}":/output \
    "caldera-tool-${tool}" \
    RUN_ID=docker-parity REPO_ID=parity-test \
    REPO_NAME=parity-test BRANCH=main COMMIT="$COMMIT_SHA" \
    >/dev/null 2>&1; then
    echo "  ERROR: Docker run failed"
    end_time="$(date +%s)"
    duration=$((end_time - start_time))
    printf '{"tool":"%s","status":"error","diff_count":0,"diffs":[],"error":"Docker run failed","duration_seconds":%d}\n' \
      "$tool" "$duration" > "$RESULTS_DIR/${tool}.json"
    rm -rf "$native_out" "$docker_out"
    return 0
  fi

  # Compare
  echo "  Comparing..."
  if $PYTHON_VENV scripts/compare_tool_outputs.py \
    --native "$native_out/output.json" \
    --docker "$docker_out/output.json" \
    --sort-arrays \
    --ignore-language-diffs \
    --tool "$tool" \
    --repo-name "$(basename "$REPO_ABS")" \
    --output-json "$RESULTS_DIR/${tool}.json"; then
    status="PASS"
  else
    status="FAIL"
  fi

  end_time="$(date +%s)"
  duration=$((end_time - start_time))

  # Patch duration into the JSON result
  if [[ -f "$RESULTS_DIR/${tool}.json" ]]; then
    $PYTHON_VENV -c "
import json, sys
p = sys.argv[1]
d = json.loads(open(p).read())
d['duration_seconds'] = int(sys.argv[2])
open(p, 'w').write(json.dumps(d, indent=2) + '\n')
" "$RESULTS_DIR/${tool}.json" "$duration"
  fi

  echo "  $status (${duration}s)"
  echo ""

  rm -rf "$native_out" "$docker_out"
}

# ── Run tests ─────────────────────────────────────────────────────────────────
pass=0; fail=0; skip=0; error=0

for tool in "${ALL_TOOLS[@]}"; do
  if [[ -n "${SKIP_SET[$tool]+x}" ]]; then
    echo "--- $tool ---"
    echo "  SKIP (user-requested)"
    printf '{"tool":"%s","status":"skip","diff_count":0,"diffs":[],"error":"Skipped by user"}\n' \
      "$tool" > "$RESULTS_DIR/${tool}.json"
    skip=$((skip + 1))
    echo ""
    continue
  fi

  run_tool_test "$tool"

  # Tally from JSON result
  if [[ -f "$RESULTS_DIR/${tool}.json" ]]; then
    tool_status="$($PYTHON_VENV -c "import json; print(json.load(open('$RESULTS_DIR/${tool}.json'))['status'])")"
    case "$tool_status" in
      pass)  pass=$((pass + 1)) ;;
      fail)  fail=$((fail + 1)) ;;
      skip)  skip=$((skip + 1)) ;;
      error) error=$((error + 1)) ;;
    esac
  fi
done

# ── Aggregate results ─────────────────────────────────────────────────────────
$PYTHON_VENV -c "
import json, glob, sys

results = []
for f in sorted(glob.glob(sys.argv[1] + '/*.json')):
    if f.endswith('parity-results.json'):
        continue
    results.append(json.load(open(f)))

aggregate = {
    'summary': {
        'total': len(results),
        'pass': sum(1 for r in results if r['status'] == 'pass'),
        'fail': sum(1 for r in results if r['status'] == 'fail'),
        'skip': sum(1 for r in results if r['status'] == 'skip'),
        'error': sum(1 for r in results if r['status'] == 'error'),
    },
    'tools': results,
}

out = sys.argv[1] + '/parity-results.json'
open(out, 'w').write(json.dumps(aggregate, indent=2) + '\n')
print(f'Aggregate results: {out}')
" "$RESULTS_DIR"

# ── Summary table ─────────────────────────────────────────────────────────────
total=$((pass + fail + skip + error))

echo ""
echo "=============================================="
echo "PARITY TEST SUMMARY"
echo "=============================================="
printf "%-25s %s\n" "Tool" "Status"
printf "%-25s %s\n" "-------------------------" "--------"

for tool in "${ALL_TOOLS[@]}"; do
  if [[ -f "$RESULTS_DIR/${tool}.json" ]]; then
    tool_status="$($PYTHON_VENV -c "import json; print(json.load(open('$RESULTS_DIR/${tool}.json'))['status'].upper())")"
    printf "%-25s %s\n" "$tool" "$tool_status"
  fi
done

echo "=============================================="
printf "Total: %d  |  Pass: %d  |  Fail: %d  |  Skip: %d  |  Error: %d\n" \
  "$total" "$pass" "$fail" "$skip" "$error"
echo "=============================================="
echo ""
echo "Detailed results: $RESULTS_DIR/parity-results.json"

# Exit with failure if any tool failed
if [[ $fail -gt 0 ]] || [[ $error -gt 0 ]]; then
  exit 1
fi
exit 0
