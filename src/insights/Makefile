# Insights Component Makefile

.PHONY: setup test evaluate clean lint format generate help \
       seed-test-db run-dbt test-report test-e2e quick-report \
       pipeline-eval extract-insights check-venv

PYTHON := python3
PIP := pip3
PYTEST := pytest
VENV := .venv

# Python from venv (for targets that need installed packages)
VENV_PYTHON := $(VENV)/bin/python

# Default database path
DB_PATH ?= /tmp/caldera_sot.duckdb
OUTPUT_DIR := output

# E2E Testing paths
SOT_ENGINE := ../sot-engine
DBT_DIR := $(SOT_ENGINE)/dbt
TEST_DB := /tmp/caldera_insights_test.duckdb
FIXTURES_DIR := $(SOT_ENGINE)/persistence/fixtures

# Project root venv (for duckdb access)
PROJECT_VENV := $(CURDIR)/../../.venv

help:
	@echo "Insights Component"
	@echo ""
	@echo "Targets:"
	@echo "  setup        - Install dependencies"
	@echo "  test         - Run unit tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  generate     - Generate a sample report"
	@echo "  evaluate     - Evaluate a report"
	@echo "  clean        - Clean build artifacts"
	@echo ""
	@echo "E2E Testing:"
	@echo "  seed-test-db - Create test DB from JSON fixtures (fast, no orchestrator)"
	@echo "  run-dbt      - Run dbt transformations on test DB"
	@echo "  test-report  - Generate HTML report and open in browser"
	@echo "  test-e2e     - Full E2E: seed DB -> run dbt -> generate report"
	@echo "  quick-report - Generate report from existing DB (requires DB_PATH, RUN_PK)"
	@echo ""
	@echo "Pipeline Evaluation:"
	@echo "  pipeline-eval    - Full pipeline: generate report -> evaluate with insight quality -> extract top 3"
	@echo "  extract-insights - Extract top 3 insights from existing evaluation results"
	@echo ""
	@echo "Variables:"
	@echo "  DB_PATH   - Path to DuckDB database (default: /tmp/caldera_sot.duckdb)"
	@echo "  RUN_PK    - Run PK for report generation"
	@echo "  REPORT    - Path to report for evaluation"
	@echo "  EVAL_FILE - Path to evaluation JSON for insight extraction"

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTEST) tests/ -v --tb=short

test-coverage:
	$(PYTEST) tests/ -v --cov=insights --cov-report=html --cov-report=term

lint:
	ruff check .
	mypy . --ignore-missing-imports

format:
	ruff format .
	ruff check --fix .

generate: check-venv
ifndef RUN_PK
	$(error RUN_PK is required. Usage: make generate RUN_PK=1)
endif
	@mkdir -p $(OUTPUT_DIR)
	$(VENV_PYTHON) -m insights generate $(RUN_PK) \
		--db $(DB_PATH) \
		--format html \
		--output $(OUTPUT_DIR)/report_$(RUN_PK).html
	@echo "Report generated: $(OUTPUT_DIR)/report_$(RUN_PK).html"

generate-md: check-venv
ifndef RUN_PK
	$(error RUN_PK is required. Usage: make generate-md RUN_PK=1)
endif
	@mkdir -p $(OUTPUT_DIR)
	$(VENV_PYTHON) -m insights generate $(RUN_PK) \
		--db $(DB_PATH) \
		--format md \
		--output $(OUTPUT_DIR)/report_$(RUN_PK).md
	@echo "Report generated: $(OUTPUT_DIR)/report_$(RUN_PK).md"

evaluate: check-venv
ifndef REPORT
	$(error REPORT is required. Usage: make evaluate REPORT=output/report.html)
endif
	$(VENV_PYTHON) -m insights.scripts.evaluate evaluate $(REPORT) \
		--db $(DB_PATH) \
		$(if $(RUN_PK),--run-pk $(RUN_PK),) \
		--output evaluation/results/eval_$(shell date +%Y%m%d_%H%M%S).json

evaluate-no-llm: check-venv
ifndef REPORT
	$(error REPORT is required. Usage: make evaluate-no-llm REPORT=output/report.html)
endif
	$(VENV_PYTHON) -m insights.scripts.evaluate evaluate $(REPORT) \
		--db $(DB_PATH) \
		$(if $(RUN_PK),--run-pk $(RUN_PK),) \
		--skip-llm \
		--output evaluation/results/eval_$(shell date +%Y%m%d_%H%M%S).json

list-sections: check-venv
	$(VENV_PYTHON) -m insights list-sections

list-checks: check-venv
	$(VENV_PYTHON) -m insights.scripts.evaluate list-checks

list-judges: check-venv
	$(VENV_PYTHON) -m insights.scripts.evaluate list-judges

validate-db: check-venv
	$(VENV_PYTHON) -m insights validate --db $(DB_PATH)

clean:
	rm -rf $(VENV)
	rm -rf $(OUTPUT_DIR)
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf *.egg-info
	find . -type f -name "*.pyc" -delete

# =============================================================================
# E2E Testing Targets
# =============================================================================

# Seed test database from JSON fixtures (fast, no orchestrator needed)
seed-test-db:
	@echo "Creating test database from fixtures..."
	@rm -f $(TEST_DB)
	cd $(SOT_ENGINE) && $(PROJECT_VENV)/bin/python -c "\
import duckdb; \
import json; \
from pathlib import Path; \
from datetime import datetime; \
conn = duckdb.connect('$(TEST_DB)'); \
conn.execute(Path('persistence/schema.sql').read_text()); \
conn.execute(\"INSERT INTO lz_collection_runs VALUES ('coll-001', 'test-repo', 'run-001', 'main', 'abc123def456abc123def456abc123def456abcd', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'completed')\"); \
conn.execute(\"INSERT INTO lz_tool_runs VALUES (1, 'coll-001', 'test-repo', 'run-001', 'scc', '1.0', '1.0', 'main', 'abc123def456abc123def456abc123def456abcd', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)\"); \
conn.execute(\"INSERT INTO lz_tool_runs VALUES (2, 'coll-001', 'test-repo', 'run-001', 'lizard', '1.0', '1.0', 'main', 'abc123def456abc123def456abc123def456abcd', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)\"); \
conn.execute(\"INSERT INTO lz_tool_runs VALUES (3, 'coll-001', 'test-repo', 'run-001', 'layout', '1.0', '1.0', 'main', 'abc123def456abc123def456abc123def456abcd', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)\"); \
print('Test database created: $(TEST_DB)'); \
"
	@echo "Note: Run 'make run-dbt' to create mart tables"

# Run dbt transformations
run-dbt:
	@echo "Running dbt transformations..."
	@test -f $(TEST_DB) || (echo "Error: Run 'make seed-test-db' first" && exit 1)
	cd $(DBT_DIR) && dbt run --profiles-dir . --target dev

# Generate test report
test-report:
	@test -f $(TEST_DB) || (echo "Error: Run 'make seed-test-db' first" && exit 1)
	$(eval TEST_RUN_PK := $(shell duckdb $(TEST_DB) -csv -noheader "SELECT run_pk FROM lz_tool_runs LIMIT 1" 2>/dev/null || echo "1"))
	@mkdir -p $(OUTPUT_DIR)
	$(VENV)/bin/python -m insights generate $(TEST_RUN_PK) \
		--db $(TEST_DB) \
		--format html \
		--output $(OUTPUT_DIR)/test_report.html || true
	@echo "Report generated: $(OUTPUT_DIR)/test_report.html"
	@command -v open >/dev/null && open $(OUTPUT_DIR)/test_report.html || echo "Open manually: $(OUTPUT_DIR)/test_report.html"

# Full E2E test pipeline
test-e2e: seed-test-db run-dbt test-report
	@echo ""
	@echo "=== E2E Test Complete ==="
	@echo "Report: $(OUTPUT_DIR)/test_report.html"
	@echo ""
	@echo "To evaluate: make evaluate-no-llm REPORT=$(OUTPUT_DIR)/test_report.html DB_PATH=$(TEST_DB)"

# Quick report from existing DB (user provides DB_PATH and RUN_PK)
quick-report:
ifndef DB_PATH
	$(error DB_PATH required. Usage: make quick-report DB_PATH=/path/to/db.duckdb RUN_PK=1)
endif
ifndef RUN_PK
	$(error RUN_PK required. Usage: make quick-report DB_PATH=/path/to/db.duckdb RUN_PK=1)
endif
	@mkdir -p $(OUTPUT_DIR)
	$(VENV)/bin/python -m insights generate $(RUN_PK) \
		--db $(DB_PATH) \
		--format html \
		--output $(OUTPUT_DIR)/report_$(RUN_PK).html
	@command -v open >/dev/null && open $(OUTPUT_DIR)/report_$(RUN_PK).html

# =============================================================================
# Pipeline Evaluation Targets
# =============================================================================

# Check that venv exists and has insights installed
check-venv:
	@test -f $(VENV_PYTHON) || (echo "Error: venv not found. Run 'make setup' first." && exit 1)
	@$(VENV_PYTHON) -c "import insights" 2>/dev/null || (echo "Error: insights not installed. Run 'make setup' first." && exit 1)

# Full pipeline: Generate report -> Evaluate with InsightQualityJudge -> Extract top 3
pipeline-eval: check-venv
ifndef DB_PATH
	$(error DB_PATH required. Usage: make pipeline-eval DB_PATH=/path/to/db.duckdb RUN_PK=1)
endif
ifndef RUN_PK
	$(error RUN_PK required. Usage: make pipeline-eval DB_PATH=/path/to/db.duckdb RUN_PK=1)
endif
	@echo "=== Phase 1: Generate Insights Report ==="
	@mkdir -p $(OUTPUT_DIR)/pipeline
	$(VENV_PYTHON) -m insights generate $(RUN_PK) \
		--db $(DB_PATH) \
		--format html \
		--output $(OUTPUT_DIR)/pipeline/report.html
	@echo ""
	@echo "=== Phase 2: LLM Evaluation with InsightQualityJudge ==="
	$(VENV_PYTHON) -m insights.scripts.evaluate evaluate \
		$(OUTPUT_DIR)/pipeline/report.html \
		--db $(DB_PATH) \
		--run-pk $(RUN_PK) \
		--include-insight-quality \
		--output $(OUTPUT_DIR)/pipeline/evaluation.json
	@echo ""
	@echo "=== Phase 3: Extract Top 3 Insights ==="
	$(VENV_PYTHON) -m insights.scripts.extract_top_insights extract \
		$(OUTPUT_DIR)/pipeline/evaluation.json \
		--output $(OUTPUT_DIR)/pipeline/top3_insights.json \
		--format rich
	@echo ""
	@echo "=== Pipeline Complete ==="
	@echo "Report:     $(OUTPUT_DIR)/pipeline/report.html"
	@echo "Evaluation: $(OUTPUT_DIR)/pipeline/evaluation.json"
	@echo "Top 3:      $(OUTPUT_DIR)/pipeline/top3_insights.json"

# Extract top 3 insights from existing evaluation results
extract-insights: check-venv
ifndef EVAL_FILE
	$(error EVAL_FILE required. Usage: make extract-insights EVAL_FILE=output/evaluation.json)
endif
	$(VENV_PYTHON) -m insights.scripts.extract_top_insights extract $(EVAL_FILE) --format rich
