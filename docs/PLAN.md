# Plan: LLM Standardization + Repo Hygiene

Date: 2026-02-01
**Status: COMPLETED** (all items verified 2026-02-21)

## Scope
This plan addressed five architectural corrections. All items are complete.

## Phase 1: LLM Standardization — COMPLETE

### 1. Lock LLM path and model in shared base — Done
- All tools use Claude Code headless with `opus-4.5` via `src/shared/evaluation/base_judge.py`.
- Anthropic SDK guarded behind `USE_ANTHROPIC_SDK=1` flag.
- Model defaults to `opus-4.5` in `src/shared/llm/client.py` MODEL_MAP.

### 2. Standardize CLI invocation — Done
- Centralized in `src/shared/llm/client.py` `invoke()` method.
- Uses stdin (`claude --print -`) instead of file-based prompts to avoid file path misinterpretation (functionally equivalent to planned `@prompt_file` approach for ARG_MAX avoidance).
- No tool-specific CLI invokers remain; all go through shared base.

### 3. Prompt validation + JSON-only enforcement — Done
- Unresolved `{{ ... }}` placeholders cause immediate `ValueError` in `base_judge.py`.
- JSON-only response instruction auto-appended if missing.
- Response parsing with JSON extraction and text fallback in `parse_response()`.

## Phase 2: Tooling + Repo Hygiene — COMPLETE

### 4. Explorer/report replacement decision — Done (Option B)
- Insights CLI (`src/insights/`) is the supported reporting entrypoint.
- Documented in `docs/REPORTS.md`. No separate explorer CLI shipped.
- Full CLI with subcommands: `generate`, `runs`, `tables`, `schema`.

### 5. Remove build artifacts from synthetic repos — Done
- `.gitignore` rules added for `bin/`, `obj/`, `.vs/` under synthetic repos.
- No build artifacts tracked in git.

## Beyond This Plan

The following capabilities were added after this plan was completed:
- **Observability infrastructure** (`src/shared/observability/`) — LLM interaction tracing and compliance checking
- **Synthetic evaluation context** — `load_synthetic_evaluation_context()` and `get_interpretation_guidance()` in BaseJudge
- **Scorecard generation** — Automated tool evaluation scorecards (`evaluation/scorecard.json`)
- **Insights sections** — 37 report sections covering all 18 tools
- **Cloud infrastructure** — Ephemeral Hetzner VM pipeline via `make cloud-run`
- **Artifact bundle workflow** — `make collect` / `make analyze-bundle` for portable analysis
