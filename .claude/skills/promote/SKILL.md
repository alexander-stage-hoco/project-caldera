---
name: promote
description: Push current branch and open a PR to the correct base branch following Caldera's promotion strategy (feature -> develop -> release -> main). Use when the user says /promote, "open a PR", or "promote this branch".
disable-model-invocation: true
allowed-tools: Bash(make promote*), Bash(git status*), Bash(git log*), Bash(git rev-parse*), Bash(git diff*)
---

# Promote Current Branch

Push the current branch and open a pull request to the correct base branch.

## Steps

1. Check that the working tree is clean:
   ```
   git status --porcelain
   ```
   If there are uncommitted changes, tell the user to commit or stash first.

2. Run the promote target. If the user provided arguments (e.g., a PR title), pass them as `PROMOTE_TITLE`:
   ```
   make promote PROMOTE_TITLE="<arguments>"
   ```
   If no arguments were provided, just run:
   ```
   make promote
   ```

3. Report the resulting PR URL to the user.

## Promotion Map

| Current branch pattern | PR target |
|------------------------|-----------|
| `feature/*`, `fix/*`, `tool/*/**`, `infra/*` | `develop` |
| `develop` | `release` |
| `release` | `main` |
| `main` | Error |
