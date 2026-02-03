# Plan: LLM Standardization + Repo Hygiene

Date: 2026-02-01

## Scope
This plan addresses five architectural corrections:
1) Lock LLM path/model in shared base
2) Standardize CLI invocation
3) Prompt validation and JSON-only enforcement
4) Explorer/report replacement decision
5) Remove build artifacts from synthetic repos

## Phase 1: LLM Standardization (High Priority)
### 1. Lock LLM path and model in shared base
- **Goal:** Ensure all tools use Claude Code headless with `opus-4.5`.
- **Changes:**
  - Disable Anthropic SDK usage or guard behind an explicit `USE_ANTHROPIC_SDK=1` flag.
  - Set shared base default model to `opus-4.5` and enforce when not explicitly overridden.
- **Files:**
  - `src/shared/evaluation/base_judge.py`
- **Acceptance:**
  - Any LLM judge run uses Claude CLI only.
  - Model defaults to `opus-4.5` unless override provided.
 - **Status:** Done

### 2. Standardize CLI invocation
- **Goal:** Avoid ARG_MAX and prompt truncation; unify invocation.
- **Changes:**
  - Use file-based prompt: `claude --print @prompt_file ...`.
  - Centralize invocation logic in shared base and remove tool-specific variants.
- **Files:**
  - `src/shared/evaluation/base_judge.py`
  - Tool-specific base judges: remove/align custom invokers.
- **Acceptance:**
  - All tools invoke through shared base logic.
  - No tool passes prompt directly as a CLI arg.
 - **Status:** Done

### 3. Prompt validation + JSON-only enforcement
- **Goal:** Ensure prompts are complete and response format is consistent.
- **Changes:**
  - Validate prompt string has no unresolved `{{ ... }}` placeholders before invocation.
  - Enforce JSON-only response instruction in shared base (append if missing).
- **Files:**
  - `src/shared/evaluation/base_judge.py`
  - Prompts under `src/tools/*/evaluation/llm/prompts/` (if needed)
- **Acceptance:**
  - LLM runs fail fast if placeholders remain.
  - Responses are JSON-only (parseable) across tools.
 - **Status:** Done

## Phase 2: Tooling + Repo Hygiene (Medium Priority)
### 4. Explorer/report replacement decision
- **Goal:** Either restore a minimal DB explorer/report CLI or explicitly remove it from docs.
- **Options:**
  - **Option A:** Add a minimal explorer CLI (list tables, run query, show schema) under `src/explorer/`.
  - **Option B:** Remove references to explorer/report commands from docs/Makefile and document that feature is removed.
- **Acceptance:**
  - Docs and Makefile are aligned with whichever option is chosen.
 - **Status:** Done (insights CLI is the supported entrypoint)

### 5. Remove build artifacts from synthetic repos
- **Goal:** Eliminate tracked build outputs (`bin/`, `obj/`, `.dll`, `.pdb`, etc.).
- **Changes:**
  - Add ignore rules for synthetic repo build outputs.
  - Remove tracked artifacts from git index.
- **Files:**
  - `.gitignore` (or tool-specific ignores)
  - Synthetic repo directories under `src/tools/roslyn-analyzers/eval-repos/synthetic/`
- **Acceptance:**
  - No build artifacts remain tracked.
  - Synthetic repos contain source-only fixtures.
 - **Status:** Done

## Testing/Validation
- Run tool compliance after Phase 1.
- Run relevant unit tests for LLM evaluation code.
- For Phase 2, ensure docs/Makefile targets are consistent.

## Dependencies / Risks
- Claude CLI authentication must be valid for LLM runs.
- Removing artifacts may require `git rm --cached` and a full clean.
