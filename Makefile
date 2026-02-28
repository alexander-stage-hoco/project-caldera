.PHONY: help setup setup-core analyze status doctor list-runs report clean-db \
	compliance compliance-preflight compliance-full \
	tools-setup tools-analyze tools-evaluate \
	tools-evaluate-llm tools-test tools-clean dbt-migrate dbt-run dbt-test \
	orchestrate test test-all test-unit test-integration pipeline-eval arch-review \
	collect analyze-bundle prune-outputs export-results \
	cloud-setup cloud-run cloud-status cloud-destroy cloud-cleanup \
	docker-build-base docker-build-tool docker-build-tools docker-test-tool \
	docker-build-runner docker-build-orchestrator docker-build-all \
	docker-pull-all docker-test-all \
	github-setup github-plan github-apply \
	promote promote-develop promote-release promote-main

# ---------------------------------------------------------------------------
# Secrets: load from .env if present (see .env.example)
# ---------------------------------------------------------------------------
-include .env
ifdef ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY
endif
ifdef HCLOUD_TOKEN
export HCLOUD_TOKEN
export TF_VAR_hcloud_token := $(HCLOUD_TOKEN)
endif
ifdef ANTHROPIC_API_KEY
export TF_VAR_anthropic_api_key := $(ANTHROPIC_API_KEY)
endif
ifdef GITHUB_TOKEN
export GITHUB_TOKEN
endif
ifdef SONAR_TOKEN
export SONAR_TOKEN
endif
ifdef RESULTS_REPO_URL
export RESULTS_REPO_URL
endif

TOOLS_DIR := src/tools
TOOL ?=
TOOL_DIRS := $(shell find $(TOOLS_DIR) -maxdepth 1 -type d -not -path $(TOOLS_DIR) -exec test -f {}/Makefile ';' -print | sort)
REPO ?=
ARCH_REVIEW_TARGET ?=
ARCH_REVIEW_TYPE ?= tool_implementation
COMPLIANCE_OUT_JSON ?= docs/tool_compliance_report.json
COMPLIANCE_OUT_MD ?= docs/tool_compliance_report.md
DBT_BIN ?= .venv/bin/dbt
DBT_PROFILES_DIR ?= src/sot-engine/dbt
DBT_PROJECT_DIR ?= src/sot-engine/dbt
DB_PATH ?= $(HOME)/.caldera/caldera_sot.duckdb
SKIP_TOOLS ?=
PIPELINE_LLM ?= 1
PIPELINE_PROVIDER ?= claude_code
CONTINUE_ON_TOOL_FAILURE ?= 0
COLLECTION_RUN_ID ?=
BUNDLE ?=
BUNDLE_DIR ?= artifacts
BUNDLE_TAR ?= 1
CLONE_DEPTH ?=
RESULTS_REPO_URL ?=
ORCH_REPO_PATH ?=
ORCH_REPO_ID ?=
ORCH_RUN_ID ?=
ORCH_BRANCH ?=
ORCH_COMMIT ?=
ORCH_DB_PATH ?= $(DB_PATH)
ORCH_LAYOUT_OUTPUT ?=
ORCH_SCC_OUTPUT ?=
ORCH_LIZARD_OUTPUT ?=
ORCH_LOG_PATH ?=
ORCH_DBT_TARGET_PATH ?=
ORCH_DBT_LOG_PATH ?=
ORCH_REPLACE ?=

define pass_var
$(if $($(1)),$(1)=$($(1)),)
endef

MAKE_VARS := \
	$(call pass_var,VENV) \
	$(call pass_var,REPO_PATH) \
	$(call pass_var,REPO_NAME) \
	$(call pass_var,OUTPUT_DIR) \
	$(call pass_var,EVAL_OUTPUT_DIR) \
	$(call pass_var,RUN_ID) \
	$(call pass_var,REPO_ID) \
	$(call pass_var,BRANCH) \
	$(call pass_var,COMMIT)

define run_tools
@set -e; \
if [ -n "$(TOOL)" ]; then \
  tools="$(TOOLS_DIR)/$(TOOL)"; \
  if [ ! -f "$$tools/Makefile" ]; then \
    echo "Tool not found or missing Makefile: $$tools"; \
    exit 1; \
  fi; \
else \
  tools="$(TOOL_DIRS)"; \
fi; \
for tool in $$tools; do \
  echo "==> $$tool: $(1)"; \
  $(MAKE) -C $$tool $(1) $(MAKE_VARS); \
done
endef

help:
	@echo "Caldera — Code Analysis Pipeline"
	@echo ""
	@echo "  Quick start:"
	@echo "    make setup                  One-time project setup"
	@echo "    make analyze REPO=<path>    Analyze a repository (local path or GitHub URL)"
	@echo "    make report                 Regenerate report from last run"
	@echo "    make list-runs              Show all analysis runs"
	@echo "    make status                 Check prerequisites and health"
	@echo ""
	@echo "  Advanced:"
	@echo "    make orchestrate            Run orchestrator (requires ORCH_* variables)"
	@echo "    make pipeline-eval          Full E2E with LLM evaluation"
	@echo "    make compliance             Structural compliance checks (all tools)"
	@echo "    make compliance-preflight   Fast structure checks only (~100ms)"
	@echo "    make compliance-full        Full compliance with tool execution"
	@echo "    make arch-review            Architecture review (ARCH_REVIEW_TARGET=<tool>)"
	@echo "    make dbt-run / dbt-test     Run dbt models / tests"
	@echo "    make tools-setup / analyze / evaluate / test / clean"
	@echo "    make collect REPO=<path|url>            Collect tool artifacts bundle only"
	@echo "    make analyze-bundle REPO=<path> BUNDLE=<bundle>  Ingest + report from bundle"
	@echo "    make prune-outputs CONFIRM=1            Delete generated tool/report outputs"
	@echo "    make export-results                     Export latest run to results repo"
	@echo "    make clean-db               Remove database and start fresh"
	@echo "    make test                   Run fast unit tests (default)"
	@echo "    make test-all               Run full suite (unit + tools + dbt)"
	@echo ""
	@echo "  Variables:"
	@echo "    REPO=<path|url>   Repository to analyze (for 'analyze' target)"
	@echo "    REPLACE=1         Replace existing run for same repo+commit"
	@echo "    DB_PATH=<path>    Database path (default: $$HOME/.caldera/caldera_sot.duckdb)"
	@echo "    COLLECTION_RUN_ID=<uuid>  Specific collection run for 'report' target"
	@echo "    CLONE_DEPTH=N     Shallow clone depth for remote URLs (default: full clone)"
	@echo "    TOOL=<name>       Limit tools-* targets to a single tool"
	@echo "    SKIP_TOOLS=a,b    Skip tools in orchestrator (comma-separated)"
	@echo "    PIPELINE_LLM=0    Skip LLM eval + top3 extraction"
	@echo "    CONTINUE_ON_TOOL_FAILURE=1  Continue running tools after a failure (partial results)"
	@echo "    BUNDLE_DIR=<dir>  Bundle output dir (default: artifacts)"
	@echo "    BUNDLE_TAR=0      Do not create .tar.gz bundle"
	@echo "    RESULTS_REPO_URL=<url>  Git URL for results repo (make export-results)"
	@echo "    PUSH=1            Push to remote after export (make export-results)"
	@echo ""
	@echo "  Cloud (Hetzner):"
	@echo "    make cloud-setup              One-time: terraform init"
	@echo "    make cloud-run REPO=<url>     Spin up VM, analyze, download results, destroy"
	@echo "    make cloud-status             Check status of cloud servers and results"
	@echo "    make cloud-destroy            Destroy cloud server (if --keep-server was used)"
	@echo "    make cloud-cleanup            Destroy orphaned VMs older than TTL"
	@echo "    CLOUD_SERVER=cx42             Override server type or preset (default: medium/cx33)"
	@echo "    MAX_DURATION=1800             Max analysis duration in seconds"
	@echo "    MAX_COST=0.05                 Max estimated cost in EUR"
	@echo "    TTL_HOURS=2                   TTL for cloud-cleanup (default: 4)"
	@echo "    DRY_RUN=1                     Dry run for cloud-cleanup"
	@echo ""
	@echo "  GitHub IaC (branch protection, environments):"
	@echo "    make github-setup             One-time: terraform init for infra/github"
	@echo "    make github-plan              Preview GitHub settings changes"
	@echo "    make github-apply             Apply GitHub settings (requires GITHUB_TOKEN)"
	@echo ""
	@echo "  Promote:"
	@echo "    make promote                  Push + open PR to correct base branch"
	@echo "    make promote PROMOTE_TITLE=.. With explicit PR title"
	@echo "    make promote-develop          Promote current -> develop"
	@echo "    make promote-release          Promote develop -> release"
	@echo "    make promote-main             Promote release -> main"

# Cloud variables
CLOUD_SERVER ?= cx33
CLOUD_RESULTS ?= $(CURDIR)/infra/results
MAX_DURATION ?=
MAX_COST ?=

# =============================================================================
# User-Facing Targets
# =============================================================================

setup:
	@echo "=== Setting up Project Caldera ==="
	@$(MAKE) setup-core
	@echo "Project venv ready. Setting up tools..."
	@$(MAKE) tools-setup
	@echo ""
	@echo "Setup complete! Run: make analyze REPO=/path/to/repo"

setup-core: ## Set up project venv only (no tool venvs/binaries)
	@echo "==> Setting up project virtual environment..."
	@python3 -c "import sys; assert sys.version_info >= (3, 12), f'Python 3.12+ required, got {sys.version}'"
	@if [ ! -f .venv/bin/activate ]; then python3 -m venv .venv; fi
	@.venv/bin/pip install --upgrade pip -q
	@.venv/bin/pip install -r requirements.txt -q
	@.venv/bin/pip install -e . -q
	@echo "==> Core setup complete"

cli-install: ## Install caldera CLI in editable mode
	@.venv/bin/pip install -e . -q
	@echo "caldera CLI installed. Run: caldera --help"

analyze:
	@test -n "$(REPO)" || (echo "Usage: make analyze REPO=/path/to/repo"; echo "       make analyze REPO=https://github.com/user/project"; exit 1)
	@if echo "$(REPO)" | grep -qE '^https?://'; then \
	  CLONE_DIR=$$(mktemp -d /tmp/caldera-repo-XXXXXX); \
	  echo "Cloning $(REPO) to $$CLONE_DIR ..."; \
	  git clone $(if $(CLONE_DEPTH),--depth $(CLONE_DEPTH)) "$(REPO)" "$$CLONE_DIR" || (rm -rf "$$CLONE_DIR"; exit 1); \
	  REPO_ID=$$(python3 -c 'import sys,hashlib,urllib.parse; u=sys.argv[1]; p=urllib.parse.urlparse(u); name=p.path.rstrip("/").split("/")[-1]; name=name[:-4] if name.endswith(".git") else name; h=hashlib.sha1(u.encode()).hexdigest()[:10]; print(f"{name}-{h}")' "$(REPO)" 2>/dev/null || echo "remote-repo"); \
	  $(MAKE) _analyze-local REPO_DIR="$$CLONE_DIR" ORCH_REPO_ID="$$REPO_ID" $(if $(REPLACE),ORCH_REPLACE=1,); \
	  echo "Cleaning up clone..."; \
	  rm -rf "$$CLONE_DIR"; \
	else \
	  $(MAKE) _analyze-local REPO_DIR="$(REPO)" $(if $(REPLACE),ORCH_REPLACE=1,); \
	fi

_analyze-local:
	@$(MAKE) pipeline-eval \
		ORCH_REPO_PATH=$(REPO_DIR) \
		ORCH_DB_PATH=$(ORCH_DB_PATH) \
		$(if $(ORCH_REPO_ID),ORCH_REPO_ID=$(ORCH_REPO_ID),) \
		$(if $(ORCH_REPLACE),ORCH_REPLACE=1,) \
		$(if $(filter 1,$(CONTINUE_ON_TOOL_FAILURE)),CONTINUE_ON_TOOL_FAILURE=1,)

report:
	@COLL_RUN_ID="$(COLLECTION_RUN_ID)"; \
	  if [ -z "$$COLL_RUN_ID" ]; then \
	    COLL_RUN_ID=$$($(PYTHON_VENV) scripts/get_latest_collection_run_id.py --db "$(ORCH_DB_PATH)"); \
	  fi; \
	  test -n "$$COLL_RUN_ID" || (echo "No runs found in database. Run 'make analyze' first."; exit 1); \
	  echo "Generating report for collection_run_id=$$COLL_RUN_ID..."; \
	  mkdir -p $(CURDIR)/$(PIPELINE_OUTPUT_DIR); \
	  (cd src && $(PYTHON_VENV) -m insights generate \
	    --collection-run-id $$COLL_RUN_ID \
	    --db $(ORCH_DB_PATH) \
	    --format html \
	    --output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/report.html); \
	  echo "Report: $(PIPELINE_OUTPUT_DIR)/report.html"

list-runs:
	@.venv/bin/python scripts/list_runs.py --db "$(ORCH_DB_PATH)"

status:
	@echo "=== Caldera Status ==="
	@printf "Python 3.12+:  "; python3 -c "import sys; v=sys.version_info; print(f'OK ({v.major}.{v.minor}.{v.micro})')" 2>/dev/null || echo "MISSING"
	@printf "Project venv:  "; test -f .venv/bin/activate && echo "OK" || echo "MISSING (run: make setup)"
	@printf "duckdb (py):   "; test -f .venv/bin/python && .venv/bin/python -c "import duckdb" >/dev/null 2>&1 && echo "OK" || echo "MISSING (run: make setup)"
	@printf "duckdb CLI:    "; command -v duckdb >/dev/null && echo "OK (optional)" || echo "MISSING (optional)"
	@printf "git:           "; command -v git >/dev/null && echo "OK" || echo "MISSING"
	@printf "Database:      "; test -f $(ORCH_DB_PATH) && echo "OK ($(ORCH_DB_PATH))" || echo "No database yet"
	@if test -f $(ORCH_DB_PATH); then \
	  printf "Runs:          "; \
	  .venv/bin/python scripts/count_collection_runs.py --db "$(ORCH_DB_PATH)" 2>/dev/null || echo "0"; \
	fi

doctor:
	@echo "=== Caldera Doctor ==="
	@printf "Python 3.12+:  "; python3 -c "import sys; v=sys.version_info; print(f'OK ({v.major}.{v.minor}.{v.micro})')" 2>/dev/null || echo "MISSING"
	@printf "Project venv:  "; test -f .venv/bin/activate && echo "OK" || echo "MISSING (run: make setup)"
	@printf "duckdb (py):   "; test -f .venv/bin/python && .venv/bin/python -c "import duckdb" >/dev/null 2>&1 && echo "OK" || echo "MISSING"
	@printf "dbt:           "; test -x .venv/bin/dbt && echo "OK" || echo "MISSING"
	@printf "git:           "; command -v git >/dev/null && echo "OK" || echo "MISSING"
	@printf "Database:      "; test -f $(ORCH_DB_PATH) && echo "OK ($(ORCH_DB_PATH))" || echo "No database yet"
	@printf "dbt profile:   "; \
	  CALDERA_DB_PATH=$(ORCH_DB_PATH) .venv/bin/dbt debug --project-dir src/sot-engine/dbt --profiles-dir src/sot-engine/dbt 2>&1 | grep -q "Connection test:.*OK" \
	    && echo "OK (connects to $(ORCH_DB_PATH))" \
	    || echo "FAILED — dbt cannot connect to $(ORCH_DB_PATH)"
	@printf "Secrets (.env): "; test -f .env && echo "OK" || echo "NOT FOUND (cp .env.example .env)"
	@printf "ANTHROPIC_API_KEY: "; \
	  test -n "$$ANTHROPIC_API_KEY" && echo "OK (set)" || echo "NOT SET (LLM eval will be skipped)"
	@printf "docker:        "; command -v docker >/dev/null && echo "OK" || echo "MISSING (sonarqube needs it)"
	@printf "go:            "; command -v go >/dev/null && echo "OK (optional)" || echo "MISSING (git-sizer needs it)"
	@printf "dotnet:        "; command -v dotnet >/dev/null && echo "OK (optional)" || echo "MISSING (roslyn/devskim/dotcover need it)"

clean-db:
	@echo "Removing database at $(ORCH_DB_PATH)..."
	@rm -f $(ORCH_DB_PATH)
	@echo "Database removed. Next 'make analyze' will create a fresh one."

prune-outputs:
	@test "$(CONFIRM)" = "1" || (echo "Refusing to delete outputs without CONFIRM=1"; exit 1)
	@echo "Pruning generated outputs..."
	@rm -rf src/insights/output/pipeline/*
	@find src/tools -maxdepth 2 -type d -name outputs -exec sh -c 'rm -rf "$$1"/*' _ {} ';'
	@echo "Done."

export-results:  ## Export latest run to results repository
	@test -n "$(RESULTS_REPO_URL)" || (echo "ERROR: RESULTS_REPO_URL not set. See .env.example"; exit 1)
	@COLL_RUN_ID="$(COLLECTION_RUN_ID)"; \
	  if [ -z "$$COLL_RUN_ID" ]; then \
	    COLL_RUN_ID=$$($(PYTHON_VENV) scripts/get_latest_collection_run_id.py --db "$(ORCH_DB_PATH)"); \
	  fi; \
	  test -n "$$COLL_RUN_ID" || (echo "No runs found. Run 'make analyze' first."; exit 1); \
	  RUN_DIR=$(PIPELINE_OUTPUT_DIR)/runs; \
	  MATCH=$$(find $$RUN_DIR -name run_manifest.json -path "*/$$COLL_RUN_ID/*" 2>/dev/null | head -1); \
	  test -n "$$MATCH" || (echo "Run directory not found for $$COLL_RUN_ID"; exit 1); \
	  RUN_PATH=$$(dirname "$$MATCH"); \
	  $(PYTHON_VENV) scripts/export_results.py \
	    --run-dir "$$RUN_PATH" \
	    --db "$(ORCH_DB_PATH)" \
	    --results-repo "$(RESULTS_REPO_URL)" \
	    $(if $(PUSH),--push,)

# =============================================================================
# Tool and Infrastructure Targets
# =============================================================================

compliance:
	@.venv/bin/python src/tool-compliance/tool_compliance.py \
		--root $(CURDIR) \
		--out-json $(COMPLIANCE_OUT_JSON) \
		--out-md $(COMPLIANCE_OUT_MD)

compliance-preflight:
	@.venv/bin/python src/tool-compliance/tool_compliance.py \
		--root $(CURDIR) \
		--preflight \
		--out-json $(COMPLIANCE_OUT_JSON) \
		--out-md $(COMPLIANCE_OUT_MD)

compliance-full:
	@.venv/bin/python src/tool-compliance/tool_compliance.py \
		--root $(CURDIR) \
		--out-json $(COMPLIANCE_OUT_JSON) \
		--out-md $(COMPLIANCE_OUT_MD) \
		--run-analysis --run-evaluate --run-llm --run-coverage

tools-setup:
	$(call run_tools,setup)

tools-analyze:
	$(call run_tools,analyze)

tools-evaluate:
	$(call run_tools,evaluate)

tools-evaluate-llm:
	$(call run_tools,evaluate-llm)

tools-test:
	$(call run_tools,test)

tools-clean:
	$(call run_tools,clean)

dbt-migrate:
	@$(PYTHON_VENV) -c "import duckdb; c=duckdb.connect('$(ORCH_DB_PATH)'); c.execute('ALTER TABLE lz_layout_files ADD COLUMN IF NOT EXISTS stable_fingerprint VARCHAR'); c.close()" 2>/dev/null || true

dbt-run: dbt-migrate
	@CALDERA_DB_PATH=$(ORCH_DB_PATH) DBT_PROFILES_DIR=$(DBT_PROFILES_DIR) $(DBT_BIN) run --project-dir $(DBT_PROJECT_DIR) --target-path /tmp/dbt_target --log-path /tmp/dbt_logs

dbt-test:
	@CALDERA_DB_PATH=$(ORCH_DB_PATH) DBT_PROFILES_DIR=$(DBT_PROFILES_DIR) $(DBT_BIN) test --project-dir $(DBT_PROJECT_DIR) --target-path /tmp/dbt_target --log-path /tmp/dbt_logs

dbt-test-reports:
	@CALDERA_DB_PATH=$(ORCH_DB_PATH) DBT_PROFILES_DIR=$(DBT_PROFILES_DIR) $(DBT_BIN) test --project-dir $(DBT_PROJECT_DIR) --target-path /tmp/dbt_target --log-path /tmp/dbt_logs --select test_report_repo_health_snapshot_ccn_present test_report_repo_health_snapshot_scc_present

MAX_PARALLEL ?= 1
MODE ?= local

orchestrate:
	@test -n "$(ORCH_REPO_PATH)" || (echo "ORCH_REPO_PATH is required"; exit 1)
	@test -n "$(ORCH_REPO_ID)" || (echo "ORCH_REPO_ID is required"; exit 1)
	@test -n "$(ORCH_RUN_ID)" || (echo "ORCH_RUN_ID is required"; exit 1)
	@test -n "$(ORCH_BRANCH)" || (echo "ORCH_BRANCH is required"; exit 1)
	@test -n "$(ORCH_COMMIT)" || (echo "ORCH_COMMIT is required"; exit 1)
	@.venv/bin/python src/sot-engine/orchestrator.py \
		--repo-path $(ORCH_REPO_PATH) \
		--repo-id $(ORCH_REPO_ID) \
		--run-id $(ORCH_RUN_ID) \
		--branch $(ORCH_BRANCH) \
		--commit $(ORCH_COMMIT) \
		--db-path $(ORCH_DB_PATH) \
		--schema-path src/sot-engine/persistence/schema.sql \
		--mode $(MODE) \
		--max-parallel $(MAX_PARALLEL) \
		$(if $(ORCH_OUTPUT_ROOT),--output-root $(ORCH_OUTPUT_ROOT),) \
		$(if $(ORCH_SKIP_TOOLS),--skip-tools $(ORCH_SKIP_TOOLS),) \
		$(if $(ORCH_LAYOUT_OUTPUT),--layout-output $(ORCH_LAYOUT_OUTPUT),) \
		$(if $(ORCH_SCC_OUTPUT),--scc-output $(ORCH_SCC_OUTPUT),) \
		$(if $(ORCH_LIZARD_OUTPUT),--lizard-output $(ORCH_LIZARD_OUTPUT),) \
		--run-tools --run-dbt \
		--dbt-bin .venv/bin/dbt \
		--dbt-project-dir src/sot-engine/dbt \
			--dbt-profiles-dir src/sot-engine/dbt \
			$(if $(ORCH_DBT_TARGET_PATH),--dbt-target-path $(ORCH_DBT_TARGET_PATH),) \
			$(if $(ORCH_DBT_LOG_PATH),--dbt-log-path $(ORCH_DBT_LOG_PATH),) \
			$(if $(ORCH_LOG_PATH),--log-path $(ORCH_LOG_PATH),) \
			$(if $(filter 1,$(CONTINUE_ON_TOOL_FAILURE)),--continue-on-tool-failure,) \
			$(if $(ORCH_REPLACE),--replace,)

arch-review:
	@test -n "$(ARCH_REVIEW_TARGET)" || (echo "ARCH_REVIEW_TARGET is required"; exit 1)
	@.venv/bin/python src/architecture-review/reviewer.py \
		--target $(ARCH_REVIEW_TARGET) \
		--review-type $(ARCH_REVIEW_TYPE)

test-unit:
	@.venv/bin/python -m pytest -q

test-integration:
	@$(MAKE) tools-test
	@$(MAKE) dbt-run
	@$(MAKE) dbt-test

test: test-unit  ## Run fast unit tests (default)

test-all: test-unit test-integration  ## Run full suite (unit + tools + dbt)

# =============================================================================
# Full E2E Pipeline: Repo -> Orchestrate -> Insights -> LLM Eval -> Top 3
# =============================================================================
# Usage: make pipeline-eval ORCH_REPO_PATH=/path/to/repo
#
# This target runs the complete analysis pipeline:
# 1. Orchestrate: Run tools + dbt transforms
# 2. Generate: Create insights report from dbt marts
# 3. Evaluate: LLM evaluation with InsightQualityJudge
# 4. Extract: Top 3 insights with improvement proposals
#
# Simplified usage (auto-generates IDs from repo path):
#   make pipeline-eval ORCH_REPO_PATH=/path/to/repo
#
# Full control:
#   make pipeline-eval \
#     ORCH_REPO_PATH=/path/to/repo \
#     ORCH_REPO_ID=my-repo \
#     ORCH_RUN_ID=run-001 \
#     ORCH_BRANCH=main \
#     ORCH_COMMIT=abc123...
# =============================================================================

PIPELINE_OUTPUT_DIR ?= src/insights/output/pipeline
PYTHON_VENV := $(CURDIR)/.venv/bin/python

pipeline-eval:
	@test -n "$(ORCH_REPO_PATH)" || (echo "ORCH_REPO_PATH is required"; exit 1)
	$(eval AUTO_REPO_ID := $(or $(ORCH_REPO_ID),$(shell python3 -c 'import sys,hashlib,pathlib; p=str(pathlib.Path(sys.argv[1]).resolve()); h=hashlib.sha1(p.encode()).hexdigest()[:10]; print(f"{pathlib.Path(p).name}-{h}")' "$(ORCH_REPO_PATH)" 2>/dev/null || basename "$(ORCH_REPO_PATH)")))
	$(eval AUTO_RUN_ID := $(or $(ORCH_RUN_ID),$(shell python3 -c 'import uuid; print(uuid.uuid4())' 2>/dev/null || date +%Y%m%d_%H%M%S)))
	$(eval AUTO_BRANCH := $(or $(ORCH_BRANCH),$(shell cd $(ORCH_REPO_PATH) && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")))
	$(eval AUTO_COMMIT := $(or $(ORCH_COMMIT),$(shell cd $(ORCH_REPO_PATH) && git rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")))
	@mkdir -p $(dir $(ORCH_DB_PATH))
	$(eval PIPELINE_RUN_DIR := $(PIPELINE_OUTPUT_DIR)/runs/$(AUTO_REPO_ID)/$(AUTO_RUN_ID))
	@mkdir -p $(PIPELINE_RUN_DIR)
	@echo ""
	@echo "=============================================="
	@echo "PIPELINE EVALUATION"
	@echo "=============================================="
	@echo "Repository: $(ORCH_REPO_PATH)"
	@echo "Repo ID:    $(AUTO_REPO_ID)"
	@echo "Run ID:     $(AUTO_RUN_ID)"
	@echo "Branch:     $(AUTO_BRANCH)"
	@echo "Commit:     $(AUTO_COMMIT)"
	@echo "Database:   $(ORCH_DB_PATH)"
	@echo "Artifacts:  $(PIPELINE_RUN_DIR)"
	@echo "=============================================="
	@echo ""
	@echo "=== Phase 1: Orchestrate (Tools + dbt) ==="
	@$(MAKE) orchestrate \
		ORCH_REPO_PATH=$(ORCH_REPO_PATH) \
		ORCH_REPO_ID=$(AUTO_REPO_ID) \
		ORCH_RUN_ID=$(AUTO_RUN_ID) \
		ORCH_BRANCH=$(AUTO_BRANCH) \
		ORCH_COMMIT=$(AUTO_COMMIT) \
		ORCH_DB_PATH=$(ORCH_DB_PATH) \
		ORCH_LOG_PATH=$(PIPELINE_RUN_DIR)/orchestrator.log \
		ORCH_DBT_TARGET_PATH=$(PIPELINE_RUN_DIR)/dbt_target \
		ORCH_DBT_LOG_PATH=$(PIPELINE_RUN_DIR)/dbt_logs \
		$(if $(SKIP_TOOLS),ORCH_SKIP_TOOLS=$(SKIP_TOOLS),) \
		$(if $(ORCH_REPLACE),ORCH_REPLACE=1,) \
		$(if $(filter 1,$(CONTINUE_ON_TOOL_FAILURE)),CONTINUE_ON_TOOL_FAILURE=1,)
	@echo ""; \
	  echo "=== Phase 2: Generate Insights Report ==="; \
	  RESOLVED_RUN_ID=$(AUTO_RUN_ID); \
	  if [ -n "$(ORCH_REPLACE)" ]; then \
	    echo "Resolving actual collection_run_id after --replace..."; \
	    RESOLVED_RUN_ID=$$($(PYTHON_VENV) scripts/get_latest_collection_run_id.py --db "$(ORCH_DB_PATH)"); \
	  fi; \
	  (cd src && $(PYTHON_VENV) -m insights generate \
	    --collection-run-id $$RESOLVED_RUN_ID \
	    --db $(ORCH_DB_PATH) \
	    --format html \
	    --output $(CURDIR)/$(PIPELINE_RUN_DIR)/report.html); \
	  cp -f $(CURDIR)/$(PIPELINE_RUN_DIR)/report.html $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/report.html; \
	  if [ "$(PIPELINE_LLM)" = "1" ]; then \
	    RUN_PK=$$($(PYTHON_VENV) scripts/get_run_pk.py --db "$(ORCH_DB_PATH)" --run-id "$$RESOLVED_RUN_ID"); \
	    echo ""; \
	    echo "=== Phase 3: LLM Evaluation with InsightQualityJudge ==="; \
	    (cd src && $(PYTHON_VENV) -m insights.scripts.evaluate evaluate \
	      $(CURDIR)/$(PIPELINE_RUN_DIR)/report.html \
	      --db $(ORCH_DB_PATH) \
	      --run-pk $$RUN_PK \
	      --include-insight-quality \
	      --provider $(PIPELINE_PROVIDER) \
	      --output $(CURDIR)/$(PIPELINE_RUN_DIR)/evaluation.json); \
	    cp -f $(CURDIR)/$(PIPELINE_RUN_DIR)/evaluation.json $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/evaluation.json; \
	    echo ""; \
	    echo "=== Phase 4: Extract Top 3 Insights ==="; \
	    (cd src && $(PYTHON_VENV) -m insights.scripts.extract_top_insights extract \
	      $(CURDIR)/$(PIPELINE_RUN_DIR)/evaluation.json \
	      --output $(CURDIR)/$(PIPELINE_RUN_DIR)/top3_insights.json \
	      --format rich); \
	    cp -f $(CURDIR)/$(PIPELINE_RUN_DIR)/top3_insights.json $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/top3_insights.json; \
	  else \
	    echo ""; \
	    echo "=== Skipping LLM phases (PIPELINE_LLM=$(PIPELINE_LLM)) ==="; \
	  fi; \
	  $(PYTHON_VENV) scripts/write_run_manifest.py \
	    --db "$(ORCH_DB_PATH)" \
	    --collection-run-id "$$RESOLVED_RUN_ID" \
	    --out "$(CURDIR)/$(PIPELINE_RUN_DIR)/run_manifest.json" \
	    --report "$(CURDIR)/$(PIPELINE_RUN_DIR)/report.html"; \
	  cp -f $(CURDIR)/$(PIPELINE_RUN_DIR)/run_manifest.json $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/run_manifest.json
	@echo ""
	@echo "=============================================="
	@echo "PIPELINE COMPLETE"
	@echo "=============================================="
	@echo "Report (this run): $(PIPELINE_RUN_DIR)/report.html"
	@echo "Report (latest):   $(PIPELINE_OUTPUT_DIR)/report.html"
	@if [ "$(PIPELINE_LLM)" = "1" ]; then \
	  echo "Evaluation (this run): $(PIPELINE_RUN_DIR)/evaluation.json"; \
	  echo "Top 3 (this run):      $(PIPELINE_RUN_DIR)/top3_insights.json"; \
	fi
	@echo "Manifest (this run): $(PIPELINE_RUN_DIR)/run_manifest.json"
	@echo "=============================================="

# =============================================================================
# Artifact Bundle Workflow (Artifacts-only collection + later ingest)
# =============================================================================

collect:
	@test -n "$(REPO)" || (echo "Usage: make collect REPO=/path/to/repo"; echo "       make collect REPO=https://github.com/user/project"; exit 1)
	@if echo "$(REPO)" | grep -qE '^https?://'; then \
	  CLONE_DIR=$$(mktemp -d /tmp/caldera-repo-XXXXXX); \
	  echo "Cloning $(REPO) to $$CLONE_DIR ..."; \
	  git clone $(if $(CLONE_DEPTH),--depth $(CLONE_DEPTH)) "$(REPO)" "$$CLONE_DIR" || (rm -rf "$$CLONE_DIR"; exit 1); \
	  REPO_ID=$$(python3 -c 'import sys,hashlib,urllib.parse; u=sys.argv[1]; p=urllib.parse.urlparse(u); name=p.path.rstrip("/").split("/")[-1]; name=name[:-4] if name.endswith(".git") else name; h=hashlib.sha1(u.encode()).hexdigest()[:10]; print(f"{name}-{h}")' "$(REPO)" 2>/dev/null || echo "remote-repo"); \
	  .venv/bin/python scripts/collect_artifacts.py --repo-path "$$CLONE_DIR" --repo-id "$$REPO_ID" --output-dir "$(BUNDLE_DIR)" $(if $(filter 1,$(BUNDLE_TAR)),--tar,) $(if $(SKIP_TOOLS),--skip-tools "$(SKIP_TOOLS)",); \
	  echo "Cleaning up clone..."; \
	  rm -rf "$$CLONE_DIR"; \
	else \
	  .venv/bin/python scripts/collect_artifacts.py --repo-path "$(REPO)" --output-dir "$(BUNDLE_DIR)" $(if $(filter 1,$(BUNDLE_TAR)),--tar,) $(if $(SKIP_TOOLS),--skip-tools "$(SKIP_TOOLS)",); \
	fi

analyze-bundle:
	@test -n "$(REPO)" || (echo "Usage: make analyze-bundle REPO=/path/to/repo BUNDLE=/path/to/bundle"; exit 1)
	@test -n "$(BUNDLE)" || (echo "BUNDLE is required (directory or .tar.gz)"; exit 1)
	@mkdir -p $(dir $(ORCH_DB_PATH))
	@.venv/bin/python scripts/analyze_bundle.py \
		--repo-path "$(REPO)" \
		--bundle "$(BUNDLE)" \
		--db-path "$(ORCH_DB_PATH)" \
		--report-out "$(PIPELINE_OUTPUT_DIR)/report.html" \
		--llm $(PIPELINE_LLM)

# =============================================================================
# Cloud Targets (Hetzner + Terraform)
# =============================================================================

cloud-setup:
	@command -v terraform >/dev/null 2>&1 || (echo "ERROR: terraform not installed. Run: brew install terraform"; exit 1)
	@test -f infra/terraform.tfvars || (echo "ERROR: infra/terraform.tfvars not found."; echo "  cp infra/terraform.tfvars.example infra/terraform.tfvars"; echo "  # Then fill in your Hetzner API token and caldera_repo_url"; exit 1)
	cd infra && terraform init

cloud-run: PIPELINE_LLM = 0
cloud-run:
	@test -n "$(REPO)" || (echo "Usage: make cloud-run REPO=https://github.com/org/repo"; exit 1)
	bash scripts/cloud-run.sh "$(REPO)" \
		--server "$(CLOUD_SERVER)" \
		--results "$(CLOUD_RESULTS)" \
		$(if $(SKIP_TOOLS),--skip "$(SKIP_TOOLS)",) \
		$(if $(filter 1,$(PIPELINE_LLM)),--llm,) \
		$(if $(CLONE_DEPTH),--clone-depth "$(CLONE_DEPTH)",) \
		$(if $(KEEP_SERVER),--keep-server,) \
		$(if $(MAX_DURATION),--max-duration "$(MAX_DURATION)",) \
		$(if $(MAX_COST),--max-cost "$(MAX_COST)",)

cloud-status:  ## Check status of cloud servers
	@cd $(CURDIR)/infra && \
	if [ ! -f terraform.tfstate ] || [ ! -s terraform.tfstate ]; then \
		echo "No Terraform state found. No cloud servers have been created."; \
	else \
		TF_JSON=$$(terraform output -json 2>/dev/null); \
		SERVER_IP=$$(echo "$$TF_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('server_ip',{}).get('value',''))" 2>/dev/null); \
		if [ -z "$$SERVER_IP" ]; then \
			echo "No active cloud servers."; \
		else \
			SERVER_NAME=$$(echo "$$TF_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('server_name',{}).get('value','unknown'))" 2>/dev/null); \
			echo "Active cloud server:"; \
			echo "  Name:   $$SERVER_NAME"; \
			echo "  IP:     $$SERVER_IP"; \
			echo "  SSH:    ssh root@$$SERVER_IP"; \
			echo "  Destroy: make cloud-destroy"; \
		fi; \
	fi; \
	echo ""; \
	RESULTS="$(CLOUD_RESULTS)"; \
	MANIFEST=$$(find "$$RESULTS" -name manifest.json -maxdepth 4 2>/dev/null | head -1); \
	if [ -n "$$MANIFEST" ]; then \
		echo "Latest results: $$MANIFEST"; \
	else \
		echo "No results downloaded yet."; \
	fi

cloud-destroy:
	@if [ ! -f infra/terraform.tfvars ]; then \
		echo "WARNING: infra/terraform.tfvars not found."; \
		echo "Terraform destroy needs tfvars. If a server is still running,"; \
		echo "delete it manually via the Hetzner console: https://console.hetzner.cloud"; \
		echo "Or install hcloud CLI: brew install hcloud"; \
		echo "  hcloud server list"; \
		echo "  hcloud server delete <id>"; \
		exit 1; \
	fi
	cd infra && terraform destroy -auto-approve \
		-var="repo_url=placeholder" \
		-var="server_type=$(CLOUD_SERVER)"

cloud-cleanup:  ## Destroy orphaned cloud VMs older than TTL
	.venv/bin/python scripts/cloud_cleanup.py $(if $(TTL_HOURS),--ttl-hours $(TTL_HOURS),) $(if $(DRY_RUN),--dry-run,)

# =============================================================================
# Docker Targets (Tool Containerization)
# =============================================================================

docker-build-base:  ## Build all base Docker images (Python, Java, .NET)
	docker build -f docker/caldera-python-base/Dockerfile -t caldera-python-base .
	docker build -f docker/caldera-java-base/Dockerfile -t caldera-java-base .
	docker build -f docker/caldera-dotnet-base/Dockerfile -t caldera-dotnet-base .

DOCKER_TOOLS := layout-scanner scc lizard semgrep symbol-scanner scancode \
	git-blame-scanner git-fame dependensee coverage-ingest \
	trivy gitleaks git-sizer pmd-cpd roslyn-analyzers devskim dotcover

docker-build-tools: docker-build-base  ## Build all tool Docker images
	@for tool in $(DOCKER_TOOLS); do \
		echo "=== Building caldera-tool-$$tool ==="; \
		$(MAKE) docker-build-tool TOOL=$$tool; \
	done

docker-build-tool: docker-build-base  ## Build a single tool image (TOOL=<name>)
	@test -n "$(TOOL)" || (echo "Usage: make docker-build-tool TOOL=<name>"; exit 1)
	@test -f src/tools/$(TOOL)/Dockerfile || (echo "No Dockerfile for $(TOOL)"; exit 1)
	docker build -f src/tools/$(TOOL)/Dockerfile -t caldera-tool-$(TOOL) .

docker-build-runner:  ## Build the Caldera runner Docker image
	docker build -f docker/caldera-runner/Dockerfile -t caldera-runner .

docker-build-orchestrator:  ## Build the Caldera orchestrator Docker image
	docker build -f docker/caldera-orchestrator/Dockerfile -t caldera-orchestrator .

docker-build-all: docker-build-tools docker-build-runner docker-build-orchestrator  ## Build all Docker images (bases + tools + runner + orchestrator)

GHCR_REGISTRY ?= ghcr.io/alexander-stage-hoco

docker-pull-all:  ## Pull all images from GHCR and tag locally
	@echo "=== Pulling base images ==="
	@for img in caldera-python-base caldera-java-base caldera-dotnet-base; do \
		echo "  $$img"; \
		docker pull $(GHCR_REGISTRY)/$$img:latest && \
		docker tag $(GHCR_REGISTRY)/$$img:latest $$img:latest; \
	done
	@echo "=== Pulling tool images ==="
	@for tool in $(DOCKER_TOOLS); do \
		echo "  caldera-tool-$$tool"; \
		docker pull $(GHCR_REGISTRY)/caldera-tool-$$tool:latest && \
		docker tag $(GHCR_REGISTRY)/caldera-tool-$$tool:latest caldera-tool-$$tool:latest; \
	done
	@echo "=== Pulling infra images ==="
	@for img in caldera-runner caldera-orchestrator; do \
		echo "  $$img"; \
		docker pull $(GHCR_REGISTRY)/$$img:latest && \
		docker tag $(GHCR_REGISTRY)/$$img:latest $$img:latest; \
	done
	@echo "Done. All images tagged locally."

COMPARE_FLAGS ?=

docker-test-tool: docker-build-tool  ## Build + test a tool image against native (TOOL=<name> REPO=<path>)
	@test -n "$(TOOL)" || (echo "TOOL is required"; exit 1)
	@test -n "$(REPO)" || (echo "REPO is required"; exit 1)
	@NATIVE_OUT=$$(mktemp -d /tmp/caldera-native-XXXXXX); \
	  DOCKER_OUT=$$(mktemp -d /tmp/caldera-docker-XXXXXX); \
	  REPO_ABS=$$(cd "$(REPO)" && pwd); \
	  COMMIT_SHA=$$(git -C "$$REPO_ABS" rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000"); \
	  echo "=== Native run ==="; \
	  $(MAKE) -C src/tools/$(TOOL) analyze \
	    REPO_PATH="$$REPO_ABS" REPO_NAME=docker-test \
	    OUTPUT_DIR="$$NATIVE_OUT" RUN_ID=native-test \
	    REPO_ID=docker-test BRANCH=main COMMIT="$$COMMIT_SHA"; \
	  echo "=== Docker run ==="; \
	  docker run --rm \
	    -v "$$REPO_ABS":/repo:ro \
	    -v "$$DOCKER_OUT":/output \
	    caldera-tool-$(TOOL) \
	    RUN_ID=docker-test REPO_ID=docker-test \
	    REPO_NAME=docker-test BRANCH=main COMMIT="$$COMMIT_SHA"; \
	  echo "=== Compare ==="; \
	  $(PYTHON_VENV) scripts/compare_tool_outputs.py \
	    --native "$$NATIVE_OUT/output.json" \
	    --docker "$$DOCKER_OUT/output.json" \
	    --sort-arrays \
	    --ignore-language-diffs \
	    --tool "$(TOOL)" \
	    --repo-name "$$(basename "$$REPO_ABS")" $(COMPARE_FLAGS); \
	  rm -rf "$$NATIVE_OUT" "$$DOCKER_OUT"

DOCKER_TEST_SKIP ?= coverage-ingest,git-blame-scanner

docker-test-all:  ## Run Docker vs native parity for all tools (REPO=<path>)
	@./scripts/docker_test_all.sh --repo "$(or $(REPO),.)" --skip "$(DOCKER_TEST_SKIP)"

# =============================================================================
# GitHub IaC (branch protection, environments, long-lived branches)
# =============================================================================

github-setup:
	@command -v terraform >/dev/null 2>&1 || (echo "ERROR: terraform not installed. Run: brew install terraform"; exit 1)
	@test -n "$$GITHUB_TOKEN" || (echo "ERROR: GITHUB_TOKEN env var not set."; echo "  export GITHUB_TOKEN=ghp_..."; exit 1)
	@test -f infra/github/terraform.tfvars || (echo "ERROR: infra/github/terraform.tfvars not found."; echo "  cp infra/github/terraform.tfvars.example infra/github/terraform.tfvars"; echo "  # Then fill in your GitHub owner and repository name"; exit 1)
	cd infra/github && terraform init

github-plan:
	@command -v terraform >/dev/null 2>&1 || (echo "ERROR: terraform not installed. Run: brew install terraform"; exit 1)
	@test -n "$$GITHUB_TOKEN" || (echo "ERROR: GITHUB_TOKEN env var not set."; echo "  export GITHUB_TOKEN=ghp_..."; exit 1)
	@test -f infra/github/terraform.tfvars || (echo "ERROR: infra/github/terraform.tfvars not found."; echo "  cp infra/github/terraform.tfvars.example infra/github/terraform.tfvars"; exit 1)
	cd infra/github && terraform plan

github-apply:
	@command -v terraform >/dev/null 2>&1 || (echo "ERROR: terraform not installed. Run: brew install terraform"; exit 1)
	@test -n "$$GITHUB_TOKEN" || (echo "ERROR: GITHUB_TOKEN env var not set."; echo "  export GITHUB_TOKEN=ghp_..."; exit 1)
	@test -f infra/github/terraform.tfvars || (echo "ERROR: infra/github/terraform.tfvars not found."; echo "  cp infra/github/terraform.tfvars.example infra/github/terraform.tfvars"; exit 1)
	cd infra/github && terraform apply

# =============================================================================
# Branch Promotion (PR creation via gh CLI)
# =============================================================================

PROMOTE_TITLE ?=
PROMOTE_BASE ?=

promote: ## Push current branch and open PR to correct base branch
	@set -e; \
	command -v gh >/dev/null 2>&1 || { echo "ERROR: gh CLI not installed. Run: brew install gh"; exit 1; }; \
	if [ -n "$$(git status --porcelain)" ]; then \
		echo "ERROR: Working tree is not clean. Commit or stash changes first."; exit 1; \
	fi; \
	BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" = "HEAD" ]; then \
		echo "ERROR: Detached HEAD state. Check out a branch first."; exit 1; \
	fi; \
	if [ "$$BRANCH" = "main" ]; then \
		echo "ERROR: Cannot promote main."; exit 1; \
	fi; \
	if [ -n "$(PROMOTE_BASE)" ]; then \
		BASE="$(PROMOTE_BASE)"; \
	elif echo "$$BRANCH" | grep -qE '^(feature|fix|tool|infra)/'; then \
		BASE="develop"; \
	elif [ "$$BRANCH" = "develop" ]; then \
		BASE="release"; \
	elif [ "$$BRANCH" = "release" ]; then \
		BASE="main"; \
	else \
		echo "ERROR: Cannot auto-detect base branch for '$$BRANCH'."; \
		echo "Use: make promote PROMOTE_BASE=<branch>"; exit 1; \
	fi; \
	REF=$$(git rev-parse --verify $$BASE 2>/dev/null || git rev-parse --verify origin/$$BASE 2>/dev/null || true); \
	if [ -z "$$REF" ]; then \
		echo "ERROR: Neither $$BASE nor origin/$$BASE exists."; exit 1; \
	fi; \
	AHEAD=$$(git rev-list --count $$REF..HEAD 2>/dev/null || echo 0); \
	if [ "$$AHEAD" = "0" ]; then \
		echo "ERROR: No commits ahead of $$BASE. Nothing to promote."; exit 1; \
	fi; \
	echo "Pushing $$BRANCH to origin..."; \
	git push -u origin HEAD; \
	if [ -n "$(PROMOTE_TITLE)" ]; then \
		TITLE="$(PROMOTE_TITLE)"; \
	else \
		TITLE=$$(echo "$$BRANCH" | sed 's|^[^/]*/||' | tr '-' ' ' | tr '_' ' ' | \
			awk '{for(i=1;i<=NF;i++) $$i=toupper(substr($$i,1,1)) substr($$i,2)}1'); \
	fi; \
	COMMITS=$$(git log --oneline $$BASE..HEAD | head -20); \
	BODY=$$(printf '## Summary\n\nPromote **%s** to **%s**.\n\n### Commits\n\n%s\n\n### Checklist\n\n- [ ] CI gates pass\n- [ ] Changes reviewed\n\n---\nGenerated with `make promote`' "$$BRANCH" "$$BASE" "$$COMMITS"); \
	echo "Creating PR: $$BRANCH -> $$BASE"; \
	gh pr create --base "$$BASE" --title "$$TITLE" --body "$$BODY"

RELEASE_TYPE ?= minor

release: ## Create and push a new version tag (RELEASE_TYPE=major|minor|patch)
	@set -e; \
	BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" != "main" ]; then \
		echo "ERROR: Releases must be tagged from main (currently on $$BRANCH)"; exit 1; \
	fi; \
	if ! git diff-index --quiet HEAD; then \
		echo "ERROR: Working tree has uncommitted changes. Commit or stash first."; exit 1; \
	fi; \
	git fetch origin main --quiet; \
	if ! git diff HEAD origin/main --quiet; then \
		echo "ERROR: Local main differs from origin/main. Pull or push first."; exit 1; \
	fi; \
	LATEST=$$(git tag --sort=-v:refname | grep '^v' | head -1); \
	if [ -z "$$LATEST" ]; then LATEST="v0.0.0"; fi; \
	MAJOR=$$(echo $$LATEST | sed 's/^v//' | cut -d. -f1); \
	MINOR=$$(echo $$LATEST | sed 's/^v//' | cut -d. -f2); \
	PATCH=$$(echo $$LATEST | sed 's/^v//' | cut -d. -f3); \
	case "$(RELEASE_TYPE)" in \
		major) MAJOR=$$((MAJOR+1)); MINOR=0; PATCH=0 ;; \
		minor) MINOR=$$((MINOR+1)); PATCH=0 ;; \
		patch) PATCH=$$((PATCH+1)) ;; \
		*) echo "ERROR: RELEASE_TYPE must be major, minor, or patch"; exit 1 ;; \
	esac; \
	NEXT="v$$MAJOR.$$MINOR.$$PATCH"; \
	if git rev-parse --verify "$$NEXT" >/dev/null 2>&1; then \
		echo "ERROR: Tag $$NEXT already exists"; exit 1; \
	fi; \
	echo "Latest tag: $$LATEST"; \
	echo "Next tag:   $$NEXT ($(RELEASE_TYPE))"; \
	echo ""; \
	echo "Commits since $$LATEST:"; \
	git log --oneline $$LATEST..HEAD | head -20; \
	echo ""; \
	echo "Creating tag $$NEXT..."; \
	git tag -a "$$NEXT" -m "Release $$NEXT"; \
	echo "Pushing tag $$NEXT to origin..."; \
	if ! git push origin "$$NEXT"; then \
		echo "Push failed — rolling back local tag $$NEXT"; \
		git tag -d "$$NEXT"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "Done. GitHub Release will be created automatically."

promote-develop: ## Promote current branch -> develop
	@$(MAKE) promote PROMOTE_BASE=develop $(if $(PROMOTE_TITLE),PROMOTE_TITLE="$(PROMOTE_TITLE)",)

promote-release: ## Promote develop -> release
	@$(MAKE) promote PROMOTE_BASE=release $(if $(PROMOTE_TITLE),PROMOTE_TITLE="$(PROMOTE_TITLE)",)

promote-main: ## Promote release -> main
	@$(MAKE) promote PROMOTE_BASE=main $(if $(PROMOTE_TITLE),PROMOTE_TITLE="$(PROMOTE_TITLE)",)
