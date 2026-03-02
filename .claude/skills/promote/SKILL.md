---
name: promote
description: Fully automated promotion pipeline. Creates feature branches when needed, runs tiered validation, creates PRs, watches CI, merges, and chains through develop→release→main. Only stops on failures or when review is needed.
allowed-tools: Bash(git *), Bash(make compliance*), Bash(make dbt-*), Bash(make test*), Bash(make release*), Bash(.venv/bin/python -m pytest*), Bash(.venv/bin/python scripts/check_observability*), Bash(gh pr *), Bash(gh run *), Bash(sleep *)
---

# Fully Automated Promotion Pipeline

Single invocation takes code from wherever it is all the way through to `main`, only stopping on failures or when human review is needed (PR to main).

## Phase 1 — Pre-flight & State Detection

Print `=== Phase 1: Pre-flight & State Detection ===`

1. Verify `gh` is installed and authenticated:
   ```
   gh auth status
   ```
   If not installed → STOP: "Install gh: `brew install gh`"
   If not authenticated → STOP: "Run `gh auth login`"

2. Verify clean working tree:
   ```
   git status --porcelain
   ```
   If dirty → STOP: "Commit or stash your changes first."

3. Detect current branch:
   ```
   git rev-parse --abbrev-ref HEAD
   ```
   If detached HEAD → STOP: "Checkout a branch first."

4. Fetch latest:
   ```
   git fetch origin --prune --quiet
   ```

5. Determine starting scenario and set `SOURCE` and `TARGET`:

   | Condition | Action |
   |-----------|--------|
   | On `main` | Ask user for `RELEASE_TYPE` (major/minor/patch, default patch), run `make release RELEASE_TYPE=<choice>`, STOP |
   | On `release`, `origin/release` ahead of `origin/main` | SOURCE=`release`, TARGET=`main` |
   | On `develop`, commits ahead of `origin/develop` | Create branch `promote/<YYYYMMDD-HHMMSS>` from HEAD, push it, SOURCE=`promote/*`, TARGET=`develop` |
   | On `develop`, synced with origin, `origin/develop` ahead of `origin/release` | SOURCE=`develop`, TARGET=`release` |
   | On `feature/*`, `fix/*`, `tool/*/**`, `infra/*` | SOURCE=current branch, TARGET=`develop` |
   | None of the above | STOP: "Nothing to promote." |

   To check "commits ahead":
   ```
   git rev-list --count origin/<target>..HEAD
   ```
   or for cross-branch:
   ```
   git rev-list --count origin/release..origin/develop
   ```

6. Print summary and proceed immediately (no confirmation):
   - `SOURCE → TARGET`
   - Number of commits
   - `git log --oneline origin/<target>..HEAD` (or equivalent for cross-branch)

## Phase 2 — Local Validation (tiered by target)

Print `=== Phase 2: Local Validation (target: <TARGET>) ===`

Run checks in order. Stop on **first failure**. Print `[N/M] <check name>...` before each, then `PASSED` or `FAILED` after.

### Target: `develop` (full QA)

1. **Compliance preflight** (~1s):
   ```
   make compliance-preflight
   ```

2. **Fast pytest** (~30s):
   ```
   .venv/bin/python -m pytest -m "not slow and not integration" --tb=short -q
   ```

3. **Full pytest** (~2min):
   ```
   .venv/bin/python -m pytest --tb=short -q
   ```

4. **dbt run + test** (~1min):
   ```
   make dbt-migrate && make dbt-run && make dbt-test
   ```

5. **Observability compliance** (~5s):
   ```
   .venv/bin/python scripts/check_observability_compliance.py
   ```

6. **Full compliance** (~10s):
   ```
   make compliance
   ```

### Target: `release` (full regression)

1. **Compliance preflight** (~1s):
   ```
   make compliance-preflight
   ```

2. **Fast pytest** (~30s):
   ```
   .venv/bin/python -m pytest -m "not slow and not integration" --tb=short -q
   ```

3. **Full pytest** (~2min):
   ```
   .venv/bin/python -m pytest --tb=short -q
   ```

4. **dbt run + test** (~1min):
   ```
   make dbt-migrate && make dbt-run && make dbt-test
   ```

5. **Observability compliance** (~5s):
   ```
   .venv/bin/python scripts/check_observability_compliance.py
   ```

6. **Full compliance** (~10s):
   ```
   make compliance
   ```

### Target: `main` (smoke only)

1. **Compliance preflight** (~1s):
   ```
   make compliance-preflight
   ```

2. **Observability compliance** (~5s):
   ```
   .venv/bin/python scripts/check_observability_compliance.py
   ```

## Phase 3 — Push & PR

Print `=== Phase 3: Push & PR ===`

1. Push the branch:
   ```
   git push -u origin HEAD
   ```

2. Check for existing open PR:
   ```
   gh pr list --head <branch> --base <target> --state open --json number --jq '.[0].number'
   ```
   If a PR exists, print `PR #<N> already exists: <url>` and skip creation.

3. If no existing PR, create one. Build the title from the branch name (strip prefix, humanize). Include a validation summary table in the body:
   ```
   gh pr create --base <target> --title "<title>" --body "$(cat <<'EOF'
   ## Summary
   <brief description based on commits>

   ## Local Validation
   | Check | Result |
   |-------|--------|
   | Compliance preflight | PASSED |
   | Fast pytest | PASSED |
   | ... | ... |

   All <N> local checks passed before PR creation.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

4. Print `PR #<N>: <url>`

5. **For `main` target**: Print "PR to main requires review before merging. After merge, run `/promote` from main to tag a release." → **STOP here. Do NOT watch CI or merge.**

6. **For `develop` and `release` targets**: proceed to Phase 4.

## Phase 4 — CI Watch & Merge

Print `=== Phase 4: CI Watch & Merge (PR #<N>) ===`

Only for PRs to `develop` and `release`. Never for `main`.

1. Print `Watching CI (timeout: 20min)...`

2. Watch CI checks:
   ```
   gh pr checks <number> --watch --fail-fast
   ```
   Use a Bash timeout of 1200000 ms (20 minutes).

3. **If checks pass** → merge immediately:
   ```
   gh pr merge <number> --squash --delete-branch
   ```
   Print `PR #<N> merged.`

4. **If checks fail** → print which checks failed + PR URL → **STOP**

5. **If timeout** → print PR URL, say "CI still running" → **STOP**

6. **If merge fails** (conflicts, etc.) → print error + PR URL → **STOP**

## Phase 5 — Chain Promotion

Print `--- Continuing: <next source> → <next target> ---`

After successful merge, determine the next leg:

| Just merged | Next action |
|-------------|-------------|
| `<feature>` or `promote/*` → `develop` | `git checkout develop && git pull origin develop` → check if `origin/develop` ahead of `origin/release` → if yes, promote `develop` → `release` (loop to Phase 2) |
| `develop` → `release` | `git checkout release && git pull origin release` → check if `origin/release` ahead of `origin/main` → if yes, promote `release` → `main` (loop to Phase 2) |
| `release` → `main` | N/A — handled in Phase 3 (stops at PR creation) |

If the next target has no new commits → print "Chain complete. Nothing more to promote." → **STOP**

If there are commits → set new SOURCE/TARGET, loop back to Phase 2 with the new target's validation tier.

## Final Summary

At the very end (whether stopped early or completed), print a summary:

```
=== Promotion Summary ===
PRs created: #X (<source> → <target>), #Y (...)
PRs merged:  #X, #Y
Stopped: <reason or "Chain complete">
```

## Error Handling

| Condition | Action |
|-----------|--------|
| Dirty working tree | STOP: "Commit or stash your changes first." |
| Detached HEAD | STOP: "Checkout a branch first." |
| No commits ahead | STOP: "Nothing to promote." |
| Local check fails | STOP: show check name + output |
| Push fails | STOP: show git error |
| CI fails | STOP: show failed checks + PR URL |
| Merge fails | STOP: show error + PR URL |
| CI timeout (20 min) | STOP: show PR URL, say "CI still running" |
| `gh` not installed | STOP: "Install gh: `brew install gh`" |
| `gh` not authenticated | STOP: "Run `gh auth login`" |

## Important Notes

- Always run phases sequentially — never skip validation
- Show progress as you go with phase headers and check counters
- **Auto-merge PRs to `develop` and `release`** — do NOT ask for confirmation
- **Never auto-merge PRs to `main`** — stop at PR creation, require human review
- Proceed immediately after state detection — no user confirmation needed
- When creating a `promote/*` branch from `develop`, use timestamp format: `promote/YYYYMMDD-HHMMSS`
- Chain promotion is automatic: after merging to `develop`, immediately start promoting to `release`, etc.
