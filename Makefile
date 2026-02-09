.PHONY: help compliance tools-setup tools-analyze tools-evaluate \
	tools-evaluate-llm tools-test tools-clean dbt-run dbt-test \
	orchestrate test pipeline-eval

TOOLS_DIR := src/tools
TOOL ?=
TOOL_DIRS := $(shell find $(TOOLS_DIR) -maxdepth 1 -type d -not -path $(TOOLS_DIR) -exec test -f {}/Makefile ';' -print | sort)
COMPLIANCE_OUT_JSON ?= docs/tool_compliance_report.json
COMPLIANCE_OUT_MD ?= docs/tool_compliance_report.md
COMPLIANCE_FLAGS ?= --run-analysis --run-evaluate --run-llm
DBT_BIN ?= .venv/bin/dbt
DBT_PROFILES_DIR ?= src/sot-engine/dbt
DBT_PROJECT_DIR ?= src/sot-engine/dbt
ORCH_REPO_PATH ?=
ORCH_REPO_ID ?=
ORCH_RUN_ID ?=
ORCH_BRANCH ?=
ORCH_COMMIT ?=
ORCH_DB_PATH ?= /tmp/caldera_sot.duckdb
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
	@echo "Caldera top-level targets:"
	@echo "  compliance         Run tool compliance scanner"
	@echo "  tools-setup        Run 'make setup' for tools"
	@echo "  tools-analyze      Run 'make analyze' for tools"
	@echo "  tools-evaluate     Run 'make evaluate' for tools"
	@echo "  tools-evaluate-llm Run 'make evaluate-llm' for tools"
	@echo "  tools-test         Run 'make test' for tools"
	@echo "  tools-clean        Run 'make clean' for tools"
	@echo "  test              Run all project tests"
	@echo "  dbt-run           Run dbt models (staging + marts)"
	@echo "  dbt-test          Run dbt tests"
	@echo "  dbt-test-reports  Run report-specific dbt tests"
	@echo "  orchestrate       Run orchestrator (REPO_PATH, REPO_ID, RUN_ID, BRANCH, COMMIT)"
	@echo "  pipeline-eval     Full E2E: orchestrate -> insights -> LLM eval -> top 3"
	@echo ""
	@echo "Variables:"
	@echo "  TOOL=<name>        Limit to a single tool directory"
	@echo "  VENV=<path>        Pass through to tool Makefiles"
	@echo "  REPO_PATH, REPO_NAME, OUTPUT_DIR, EVAL_OUTPUT_DIR, RUN_ID, REPO_ID, BRANCH, COMMIT"
	@echo "  COMPLIANCE_FLAGS=\"--run-analysis --run-evaluate --run-llm\""
	@echo "  DBT_BIN, DBT_PROFILES_DIR, DBT_PROJECT_DIR"
	@echo "  ORCH_REPO_PATH, ORCH_REPO_ID, ORCH_RUN_ID, ORCH_BRANCH, ORCH_COMMIT, ORCH_DB_PATH"
	@echo "  ORCH_LAYOUT_OUTPUT (optional, override layout output path)"
	@echo "  ORCH_SCC_OUTPUT (optional, override scc output path)"
	@echo "  ORCH_LIZARD_OUTPUT (optional, override lizard output path)"
	@echo "  ORCH_LOG_PATH (optional, defaults to /tmp/caldera_orchestrator_<run_id>.log)"
	@echo "  ORCH_REPLACE=1 (optional, replace existing repo+commit run)"
	@echo "  ORCH_OUTPUT_ROOT (optional, override tool output root)"
	@echo "  ORCH_SKIP_TOOLS (optional, comma-separated tool names to skip)"

compliance:
	@.venv/bin/python src/tool-compliance/tool_compliance.py \
		--root $(CURDIR) \
		--out-json $(COMPLIANCE_OUT_JSON) \
		--out-md $(COMPLIANCE_OUT_MD) \
		$(COMPLIANCE_FLAGS)

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
# 1. Orchestrate: Run 7 tools + dbt transforms
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
	$(eval REPO_NAME := $(shell basename $(ORCH_REPO_PATH)))
	$(eval AUTO_REPO_ID := $(or $(ORCH_REPO_ID),$(REPO_NAME)))
	$(eval AUTO_RUN_ID := $(or $(ORCH_RUN_ID),$(shell date +%Y%m%d_%H%M%S)))
	$(eval AUTO_BRANCH := $(or $(ORCH_BRANCH),$(shell cd $(ORCH_REPO_PATH) && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")))
	$(eval AUTO_COMMIT := $(or $(ORCH_COMMIT),$(shell cd $(ORCH_REPO_PATH) && git rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")))
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
		$(if $(ORCH_REPLACE),ORCH_REPLACE=1,)
	$(eval RUN_PK := $(shell duckdb $(ORCH_DB_PATH) -csv -noheader "SELECT run_pk FROM lz_tool_runs WHERE run_id='$(AUTO_RUN_ID)' LIMIT 1" 2>/dev/null || echo "1"))
	@echo ""
	@echo "=== Phase 2: Generate Insights Report ==="
	@mkdir -p $(PIPELINE_OUTPUT_DIR)
	cd src/insights && $(PYTHON_VENV) -m insights generate $(RUN_PK) \
		--db $(ORCH_DB_PATH) \
		--format html \
		--output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/report.html
	@echo ""
	@echo "=== Phase 3: LLM Evaluation with InsightQualityJudge ==="
	cd src/insights && $(PYTHON_VENV) -m insights.scripts.evaluate evaluate \
		$(CURDIR)/$(PIPELINE_OUTPUT_DIR)/report.html \
		--db $(ORCH_DB_PATH) \
		--run-pk $(RUN_PK) \
		--include-insight-quality \
		--output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/evaluation.json
	@echo ""
	@echo "=== Phase 4: Extract Top 3 Insights ==="
	cd src/insights && $(PYTHON_VENV) -m insights.scripts.extract_top_insights extract \
		$(CURDIR)/$(PIPELINE_OUTPUT_DIR)/evaluation.json \
		--output $(CURDIR)/$(PIPELINE_OUTPUT_DIR)/top3_insights.json \
		--format rich
	@echo ""
	@echo "=============================================="
	@echo "PIPELINE COMPLETE"
	@echo "=============================================="
	@echo "Report:     $(PIPELINE_OUTPUT_DIR)/report.html"
	@echo "Evaluation: $(PIPELINE_OUTPUT_DIR)/evaluation.json"
	@echo "Top 3:      $(PIPELINE_OUTPUT_DIR)/top3_insights.json"
	@echo "=============================================="
