.PHONY: help compliance tools-setup tools-analyze tools-evaluate \
	tools-evaluate-llm tools-test tools-clean dbt-run dbt-test explore \
	report-health report-hotspots report-health-latest report-hotspots-latest \
	orchestrate test

TOOLS_DIR := src/tools
TOOL ?=
TOOL_DIRS := $(shell find $(TOOLS_DIR) -maxdepth 1 -type d -not -path $(TOOLS_DIR) -exec test -f {}/Makefile ';' -print | sort)
COMPLIANCE_OUT_JSON ?= /tmp/tool_compliance_report.json
COMPLIANCE_OUT_MD ?= /tmp/tool_compliance_report.md
COMPLIANCE_FLAGS ?= --run-analysis --run-evaluate --run-llm
DBT_BIN ?= .venv/bin/dbt
DBT_PROFILES_DIR ?= src/sot-engine/dbt
DBT_PROJECT_DIR ?= src/sot-engine/dbt
EXPLORER_DB ?= /tmp/caldera_sot.duckdb
EXPLORER_PY ?= .venv/bin/python
RUN_PK ?=
REPORT_LIMIT ?= 10
REPORT_FORMAT ?= table
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
	@echo "  explore           List DuckDB tables (default /tmp/caldera_sot.duckdb)"
	@echo "  explore-query     Run a SQL query (QUERY=...)"
	@echo "  report-health     Repo health snapshot report"
	@echo "  report-hotspots   Hotspot directories report"
	@echo "  report-atlas      Combined health + drill-downs report"
	@echo "  report-health-latest  Repo health (latest run for REPO_ID)"
	@echo "  report-hotspots-latest Hotspots (latest run for REPO_ID)"
	@echo "  report-atlas-latest   Combined report (latest run for REPO_ID)"
	@echo "  report-runs       Collection run status report"
	@echo "  orchestrate       Run orchestrator (REPO_PATH, REPO_ID, RUN_ID, BRANCH, COMMIT)"
	@echo ""
	@echo "Variables:"
	@echo "  TOOL=<name>        Limit to a single tool directory"
	@echo "  VENV=<path>        Pass through to tool Makefiles"
	@echo "  REPO_PATH, REPO_NAME, OUTPUT_DIR, EVAL_OUTPUT_DIR, RUN_ID, REPO_ID, BRANCH, COMMIT"
	@echo "  COMPLIANCE_FLAGS=\"--run-analysis --run-evaluate --run-llm\""
	@echo "  DBT_BIN, DBT_PROFILES_DIR, DBT_PROJECT_DIR, EXPLORER_DB, EXPLORER_PY, RUN_PK, REPORT_LIMIT, REPORT_FORMAT, REPO_ID"
	@echo "  ORCH_REPO_PATH, ORCH_REPO_ID, ORCH_RUN_ID, ORCH_BRANCH, ORCH_COMMIT, ORCH_DB_PATH"
	@echo "  ORCH_LAYOUT_OUTPUT (optional, override layout output path)"
	@echo "  ORCH_SCC_OUTPUT (optional, override scc output path)"
	@echo "  ORCH_LIZARD_OUTPUT (optional, override lizard output path)"
	@echo "  ORCH_LOG_PATH (optional, defaults to /tmp/caldera_orchestrator_<run_id>.log)"
	@echo "  ORCH_REPLACE=1 (optional, replace existing repo+commit run)"
	@echo "  ORCH_OUTPUT_ROOT (optional, override tool output root)"
	@echo "  ORCH_SKIP_TOOLS (optional, comma-separated tool names to skip)"

compliance:
	@$(EXPLORER_PY) src/tool-compliance/tool_compliance.py \
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

explore:
	@$(EXPLORER_PY) src/explorer/explorer.py --db $(EXPLORER_DB) list

explore-query:
	@test -n "$(QUERY)" || (echo "QUERY is required, e.g. QUERY=\"select 1\""; exit 1)
	@$(EXPLORER_PY) src/explorer/explorer.py --db $(EXPLORER_DB) query "$(QUERY)"

report-health:
	@$(EXPLORER_PY) src/explorer/report_runner.py repo-health --db $(EXPLORER_DB) --run-pk $(RUN_PK) --format $(REPORT_FORMAT) $(if $(REPORT_OUT),--out $(REPORT_OUT),)

report-hotspots:
	@$(EXPLORER_PY) src/explorer/report_runner.py hotspots --db $(EXPLORER_DB) --run-pk $(RUN_PK) --limit $(REPORT_LIMIT) --format $(REPORT_FORMAT) $(if $(REPORT_OUT),--out $(REPORT_OUT),)

report-atlas:
	@$(EXPLORER_PY) src/explorer/report_runner.py atlas --db $(EXPLORER_DB) --run-pk $(RUN_PK) --limit $(REPORT_LIMIT) --format $(REPORT_FORMAT) $(if $(REPORT_OUT),--out $(REPORT_OUT),)

report-health-latest:
	@$(EXPLORER_PY) src/explorer/report_runner.py repo-health --db $(EXPLORER_DB) --repo-id $(REPO_ID) --format $(REPORT_FORMAT) $(if $(REPORT_OUT),--out $(REPORT_OUT),)

report-hotspots-latest:
	@$(EXPLORER_PY) src/explorer/report_runner.py hotspots --db $(EXPLORER_DB) --repo-id $(REPO_ID) --limit $(REPORT_LIMIT) --format $(REPORT_FORMAT) $(if $(REPORT_OUT),--out $(REPORT_OUT),)

report-atlas-latest:
	@$(EXPLORER_PY) src/explorer/report_runner.py atlas --db $(EXPLORER_DB) --repo-id $(REPO_ID) --limit $(REPORT_LIMIT) --format $(REPORT_FORMAT) $(if $(REPORT_OUT),--out $(REPORT_OUT),)

report-runs:
	@$(EXPLORER_PY) src/explorer/report_runner.py runs --db $(EXPLORER_DB) --format $(REPORT_FORMAT) $(if $(REPORT_OUT),--out $(REPORT_OUT),)

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
	@$(MAKE) tools-test VENV=$(CURDIR)/.venv SKIP_SETUP=1
	@$(MAKE) dbt-run
	@$(MAKE) dbt-test
