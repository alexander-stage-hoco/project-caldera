---
name: promote
description: Automated branch promotion with tiered local validation, CI monitoring, and chain promotion. Handles feature→develop→release→main→tag. Use when the user says /promote, "open a PR", or "promote this branch".
allowed-tools: Bash(git *), Bash(make compliance*), Bash(make dbt-*), Bash(make test*), Bash(make promote*), Bash(make release*), Bash(.venv/bin/python -m pytest*), Bash(.venv/bin/python scripts/check_observability*), Bash(gh pr *), Bash(gh run *)
---

# Automated Promotion Pipeline

Push the current branch, run tiered local validation, create a PR, monitor CI, and offer chain promotion.

## Phase 1 — Pre-flight

1. Check that the working tree is clean:
   ```
   git status --porcelain
   ```
   If dirty, stop and tell the user to commit or stash first.

2. Detect the current branch and target:
   ```
   git rev-parse --abbrev-ref HEAD
   ```

3. Determine the promotion target using this map:

   | Current branch pattern | PR target |
   |------------------------|-----------|
   | `feature/*`, `fix/*`, `tool/*/**`, `infra/*` | `develop` |
   | `develop` | `release` |
   | `release` | `main` |
   | `main` | Error — cannot promote main (offer `make release` for tagging instead) |

4. Check commits ahead of target:
   ```
   git rev-list --count origin/<target>..HEAD
   ```
   If 0 commits ahead, stop — nothing to promote.

5. Show a summary to the user:
   - Current branch → target branch
   - Number of commits ahead
   - One-line log of those commits: `git log --oneline origin/<target>..HEAD`

## Phase 2 — Local Validation (tiered)

Run checks based on the target branch. Stop on the **first failure** — report which check failed and its output.

### Target: `develop` (full QA — new code entering integration)

Run these checks in order, stopping on first failure:

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

4. **dbt run + dbt test** (~1min):
   ```
   make dbt-migrate
   make dbt-run
   make dbt-test
   ```

5. **Observability compliance** (~5s):
   ```
   .venv/bin/python scripts/check_observability_compliance.py
   ```

6. **Full compliance** (~10s):
   ```
   make compliance
   ```

### Target: `release` (lighter — Gate A already passed on feature→develop)

1. **Compliance preflight**:
   ```
   make compliance-preflight
   ```

2. **Fast pytest**:
   ```
   .venv/bin/python -m pytest -m "not slow and not integration" --tb=short -q
   ```

3. **Full compliance**:
   ```
   make compliance
   ```

### Target: `main` (lightest — Gate C smoke already passed on develop→release)

1. **Compliance preflight**:
   ```
   make compliance-preflight
   ```

2. **Observability compliance**:
   ```
   .venv/bin/python scripts/check_observability_compliance.py
   ```

## Phase 3 — Push & PR

1. Push the branch:
   ```
   git push -u origin HEAD
   ```

2. Check for an existing PR from this branch to the target:
   ```
   gh pr list --head <branch> --base <target> --state open --json url,number --jq '.[0]'
   ```
   If a PR already exists, report its URL and skip PR creation. Continue to Phase 4.

3. Create the PR. Build the title from the branch name (strip prefix, humanize). Include a validation summary in the body:

   ```
   gh pr create --base <target> --title "<title>" --body "$(cat <<'EOF'
   ## Summary
   <brief description based on commits>

   ## Local Validation
   | Check | Result |
   |-------|--------|
   | Compliance preflight | Passed |
   | Fast pytest | Passed |
   | ... | ... |

   All <N> local checks passed before PR creation.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

4. Report the PR URL to the user.

## Phase 4 — CI Monitoring

1. Watch CI checks with a 20-minute timeout:
   ```
   gh pr checks <pr-number> --watch --fail-fast 2>&1
   ```
   Use a timeout of 1200 seconds (20 minutes) on the bash command.

2. Expected CI checks by target:

   | Target | Expected checks |
   |--------|----------------|
   | `develop` | Gate A — Quality |
   | `release` | Gate A — Quality, Gate B — Compliance Report, Gate C — Production Smoke |
   | `main` | Gate A — Quality, Gate B — Compliance Report, Promotion Policy |

3. Report results:
   - **All passed**: Report success, proceed to Phase 5.
   - **Any failed**: Report which checks failed. Do NOT offer chain promotion.
   - **Timeout**: Stop, give the PR URL for manual monitoring.

## Phase 5 — Chain Promotion

Only offer this if CI passed in Phase 4.

1. Based on the current promotion, offer the next step:

   | Just completed | Offer next |
   |---------------|------------|
   | feature → develop | "Merge the PR, then run `/promote` from `develop` to continue to release" |
   | develop → release | "Merge the PR, then run `/promote` from `release` to continue to main" |
   | release → main | "Merge the PR, then run `/promote` from `main` to create a release tag" |

2. For `main` (tagging): If the user is on `main` and asks to promote, offer:
   ```
   make release
   ```
   This creates and pushes a version tag. Ask the user for `RELEASE_TYPE=major|minor|patch` (default: `patch`).

## Error Handling

| Condition | Action |
|-----------|--------|
| Dirty working tree | Stop, tell user to commit or stash |
| Detached HEAD | Stop, tell user to checkout a branch |
| No commits ahead of target | Stop, nothing to promote |
| Cannot detect target branch | Stop, show branch naming conventions |
| Local check fails | Stop, name the check, show its output |
| Existing open PR | Show URL, skip to Phase 4 (CI monitoring) |
| CI check fails | Report which checks failed, do NOT offer chain promotion |
| CI timeout (20 min) | Stop, give PR URL for manual monitoring |
| `gh` CLI not installed | Stop, tell user to install: `brew install gh` |
| Not authenticated with `gh` | Stop, tell user to run `gh auth login` |

## Important Notes

- Always run phases sequentially — do not skip validation
- Show progress as you go: name each check before running it, report pass/fail after
- For chain promotion, the user must merge the PR themselves first — do not merge PRs automatically
- When on `main`, the only valid action is `make release` for tagging
- Pass `--fail-fast` to `gh pr checks --watch` so it stops as soon as any check fails
