.PHONY: help setup analyze status list-runs report clean-db \
	compliance compliance-preflight compliance-full \
	tools-setup tools-analyze tools-evaluate \
	tools-evaluate-llm tools-test tools-clean dbt-run dbt-test \
	orchestrate test pipeline-eval arch-review \
	collect analyze-bundle prune-outputs

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
BUNDLE ?=
BUNDLE_DIR ?= artifacts
BUNDLE_TAR ?= 1
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
	@echo "    make clean-db               Remove database and start fresh"
	@echo "    make test                   Run all project tests"
	@echo ""
	@echo "  Variables:"
	@echo "    REPO=<path|url>   Repository to analyze (for 'analyze' target)"
	@echo "    REPLACE=1         Replace existing run for same repo+commit"
	@echo "    DB_PATH=<path>    Database path (default: $$HOME/.caldera/caldera_sot.duckdb)"
	@echo "    RUN_PK=<id>       Specific run to report on (for 'report' target)"
	@echo "    TOOL=<name>       Limit tools-* targets to a single tool"
	@echo "    SKIP_TOOLS=a,b    Skip tools in orchestrator (comma-separated)"
	@echo "    PIPELINE_LLM=0    Skip LLM eval + top3 extraction"
	@echo "    BUNDLE_DIR=<dir>  Bundle output dir (default: artifacts)"
	@echo "    BUNDLE_TAR=0      Do not create .tar.gz bundle"

# =============================================================================
# User-Facing Targets
# =============================================================================

setup:
	@echo "=== Setting up Project Caldera ==="
	@python3 -c "import sys; assert sys.version_info >= (3, 12), f'Python 3.12+ required, got {sys.version}'"
	@if [ ! -f .venv/bin/activate ]; then python3 -m venv .venv; fi
	@.venv/bin/pip install --upgrade pip -q
	@.venv/bin/pip install -r requirements.txt -q
	@echo "Project venv ready. Setting up tools..."
	@$(MAKE) tools-setup
	@echo ""
	@echo "Setup complete! Run: make analyze REPO=/path/to/repo"

analyze:
	@test -n "$(REPO)" || (echo "Usage: make analyze REPO=/path/to/repo"; echo "       make analyze REPO=https://github.com/user/project"; exit 1)
	@if echo "$(REPO)" | grep -qE '^https?://'; then \
	  CLONE_DIR=$$(mktemp -d /tmp/caldera-repo-XXXXXX); \
	  echo "Cloning $(REPO) to $$CLONE_DIR ..."; \
	  git clone --depth 1 "$(REPO)" "$$CLONE_DIR" || (rm -rf "$$CLONE_DIR"; exit 1); \
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
		$(if $(ORCH_REPLACE),ORCH_REPLACE=1,)

report:
	$(eval RUN_PK ?= $(shell duckdb $(ORCH_DB_PATH) -csv -noheader \
	  "SELECT run_pk FROM lz_tool_runs ORDER BY run_pk DESC LIMIT 1" 2>/dev/null))
	@test -n "$(RUN_PK)" || (echo "No runs found in database. Run 'make analyze' first."; exit 1)
	@echo "Generating report for run_pk=$(RUN_PK)..."
	@mkdir -p $(PIPELINE_OUTPUT_DIR)
	cd src/insights && $(PYTHON_VENV) -m insights generate $(RUN_PK) \
		--db $(ORCH_DB_PATH) \
		--format html \
		--output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/report.html
	@echo "Report: $(PIPELINE_OUTPUT_DIR)/report.html"

list-runs:
	@duckdb $(ORCH_DB_PATH) -markdown \
	  "SELECT cr.collection_run_id, cr.repo_id, cr.commit, cr.status, \
	   cr.started_at, count(tr.run_pk) as tool_count \
	   FROM lz_collection_runs cr \
	   LEFT JOIN lz_tool_runs tr ON tr.collection_run_id = cr.collection_run_id \
	   GROUP BY 1,2,3,4,5 \
	   ORDER BY cr.started_at DESC" 2>/dev/null \
	  || echo "No database found at $(ORCH_DB_PATH). Run 'make analyze' first."

status:
	@echo "=== Caldera Status ==="
	@printf "Python 3.12+:  "; python3 -c "import sys; v=sys.version_info; print(f'OK ({v.major}.{v.minor}.{v.micro})')" 2>/dev/null || echo "MISSING"
	@printf "Project venv:  "; test -f .venv/bin/activate && echo "OK" || echo "MISSING (run: make setup)"
	@printf "duckdb CLI:    "; command -v duckdb >/dev/null && echo "OK" || echo "MISSING (brew install duckdb)"
	@printf "git:           "; command -v git >/dev/null && echo "OK" || echo "MISSING"
	@printf "Database:      "; test -f $(ORCH_DB_PATH) && echo "OK ($(ORCH_DB_PATH))" || echo "No database yet"
	@if test -f $(ORCH_DB_PATH); then \
	  printf "Runs:          "; \
	  duckdb $(ORCH_DB_PATH) -csv -noheader "SELECT count(*) FROM lz_collection_runs" 2>/dev/null || echo "0"; \
	fi

clean-db:
	@echo "Removing database at $(ORCH_DB_PATH)..."
	@rm -f $(ORCH_DB_PATH)
	@echo "Database removed. Next 'make analyze' will create a fresh one."

prune-outputs:
	@test "$(CONFIRM)" = "1" || (echo "Refusing to delete outputs without CONFIRM=1"; exit 1)
	@echo "Pruning generated outputs..."
	@rm -rf src/insights/output/pipeline/*
	@find src/tools -maxdepth 2 -type d -name outputs -exec rm -rf {}/\* ';'
	@echo "Done."

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
		--preflight

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

dbt-run:
	@DBT_PROFILES_DIR=$(DBT_PROFILES_DIR) $(DBT_BIN) run --project-dir $(DBT_PROJECT_DIR) --target-path /tmp/dbt_target --log-path /tmp/dbt_logs

dbt-test:
	@DBT_PROFILES_DIR=$(DBT_PROFILES_DIR) $(DBT_BIN) test --project-dir $(DBT_PROJECT_DIR) --target-path /tmp/dbt_target --log-path /tmp/dbt_logs

dbt-test-reports:
	@DBT_PROFILES_DIR=$(DBT_PROFILES_DIR) $(DBT_BIN) test --project-dir $(DBT_PROJECT_DIR) --target-path /tmp/dbt_target --log-path /tmp/dbt_logs --select test_report_repo_health_snapshot_ccn_present test_report_repo_health_snapshot_scc_present

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
		$(if $(ORCH_OUTPUT_ROOT),--output-root $(ORCH_OUTPUT_ROOT),) \
		$(if $(ORCH_SKIP_TOOLS),--skip-tools $(ORCH_SKIP_TOOLS),) \
		$(if $(ORCH_LAYOUT_OUTPUT),--layout-output $(ORCH_LAYOUT_OUTPUT),) \
		$(if $(ORCH_SCC_OUTPUT),--scc-output $(ORCH_SCC_OUTPUT),) \
		$(if $(ORCH_LIZARD_OUTPUT),--lizard-output $(ORCH_LIZARD_OUTPUT),) \
		--run-tools --run-dbt \
		--dbt-bin .venv/bin/dbt \
		--dbt-project-dir src/sot-engine/dbt \
		--dbt-profiles-dir src/sot-engine/dbt \
		$(if $(ORCH_LOG_PATH),--log-path $(ORCH_LOG_PATH),) \
		$(if $(ORCH_REPLACE),--replace,)

arch-review:
	@test -n "$(ARCH_REVIEW_TARGET)" || (echo "ARCH_REVIEW_TARGET is required"; exit 1)
	@.venv/bin/python src/architecture-review/reviewer.py \
		--target $(ARCH_REVIEW_TARGET) \
		--review-type $(ARCH_REVIEW_TYPE)

test:
	@.venv/bin/python -m pytest -q
	@$(MAKE) tools-test
	@$(MAKE) dbt-run
	@$(MAKE) dbt-test

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
PYTHON_VENV := .venv/bin/python

pipeline-eval:
	@test -n "$(ORCH_REPO_PATH)" || (echo "ORCH_REPO_PATH is required"; exit 1)
	$(eval AUTO_REPO_ID := $(or $(ORCH_REPO_ID),$(shell python3 -c 'import sys,hashlib,pathlib; p=str(pathlib.Path(sys.argv[1]).resolve()); h=hashlib.sha1(p.encode()).hexdigest()[:10]; print(f"{pathlib.Path(p).name}-{h}")' "$(ORCH_REPO_PATH)" 2>/dev/null || basename "$(ORCH_REPO_PATH)")))
	$(eval AUTO_RUN_ID := $(or $(ORCH_RUN_ID),$(shell python3 -c 'import uuid; print(uuid.uuid4())' 2>/dev/null || date +%Y%m%d_%H%M%S)))
	$(eval AUTO_BRANCH := $(or $(ORCH_BRANCH),$(shell cd $(ORCH_REPO_PATH) && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")))
	$(eval AUTO_COMMIT := $(or $(ORCH_COMMIT),$(shell cd $(ORCH_REPO_PATH) && git rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")))
	@mkdir -p $(dir $(ORCH_DB_PATH))
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
		$(if $(SKIP_TOOLS),ORCH_SKIP_TOOLS=$(SKIP_TOOLS),) \
		$(if $(ORCH_REPLACE),ORCH_REPLACE=1,)
	$(eval RUN_PK := $(shell duckdb $(ORCH_DB_PATH) -csv -noheader "SELECT run_pk FROM lz_tool_runs WHERE run_id='$(AUTO_RUN_ID)' LIMIT 1" 2>/dev/null || echo "1"))
	@echo ""
	@echo "=== Phase 2: Generate Insights Report ==="
	@mkdir -p $(PIPELINE_OUTPUT_DIR)
	cd src/insights && $(PYTHON_VENV) -m insights generate $(RUN_PK) \
		--db $(ORCH_DB_PATH) \
		--format html \
		--output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/report.html
	@if [ "$(PIPELINE_LLM)" = "1" ]; then \
	  echo ""; \
	  echo "=== Phase 3: LLM Evaluation with InsightQualityJudge ==="; \
	  cd src/insights && $(PYTHON_VENV) -m insights.scripts.evaluate evaluate \
	    $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/report.html \
	    --db $(ORCH_DB_PATH) \
	    --run-pk $(RUN_PK) \
	    --include-insight-quality \
	    --output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/evaluation.json; \
	  echo ""; \
	  echo "=== Phase 4: Extract Top 3 Insights ==="; \
	  cd src/insights && $(PYTHON_VENV) -m insights.scripts.extract_top_insights extract \
	    $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/evaluation.json \
	    --output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/top3_insights.json \
	    --format rich; \
	else \
	  echo ""; \
	  echo "=== Skipping LLM phases (PIPELINE_LLM=$(PIPELINE_LLM)) ==="; \
	fi
	@echo ""
	@echo "=============================================="
	@echo "PIPELINE COMPLETE"
	@echo "=============================================="
	@echo "Report:     $(PIPELINE_OUTPUT_DIR)/report.html"
	@if [ "$(PIPELINE_LLM)" = "1" ]; then \
	  echo "Evaluation: $(PIPELINE_OUTPUT_DIR)/evaluation.json"; \
	  echo "Top 3:      $(PIPELINE_OUTPUT_DIR)/top3_insights.json"; \
	fi
	@echo "=============================================="

# =============================================================================
# Artifact Bundle Workflow (Artifacts-only collection + later ingest)
# =============================================================================

collect:
	@test -n "$(REPO)" || (echo "Usage: make collect REPO=/path/to/repo"; echo "       make collect REPO=https://github.com/user/project"; exit 1)
	@if echo "$(REPO)" | grep -qE '^https?://'; then \
	  CLONE_DIR=$$(mktemp -d /tmp/caldera-repo-XXXXXX); \
	  echo "Cloning $(REPO) to $$CLONE_DIR ..."; \
	  git clone --depth 1 "$(REPO)" "$$CLONE_DIR" || (rm -rf "$$CLONE_DIR"; exit 1); \
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
