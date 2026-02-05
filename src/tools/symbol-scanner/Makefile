# Symbol Scanner: Python symbol extraction tool
# Extracts function/class definitions, call relationships, and imports
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run analysis
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup analyze evaluate evaluate-llm test clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific configuration
TOOL_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(abspath $(TOOL_ROOT)/../../..)

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic/simple-functions
REPO_NAME ?= simple-functions
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || git -C $(PROJECT_ROOT) rev-parse HEAD 2>/dev/null)
COMMIT_ARG := $(if $(COMMIT),--commit $(COMMIT),)

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "Symbol Scanner: Python symbol extraction tool"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install Python dependencies"
	@echo "  make analyze      - Run symbol extraction"
	@echo "  make evaluate     - Run programmatic evaluation"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Analysis targets:"
	@echo "  make analyze             - Analyze default repo (simple-functions)"
	@echo "  make analyze REPO_PATH=. - Analyze custom repo"
	@echo ""
	@echo "Evaluation targets:"
	@echo "  make evaluate       - Full evaluation with verbose output"
	@echo "  make evaluate-llm   - Run LLM evaluation (4 judges)"
	@echo ""
	@echo "Additional targets:"
	@echo "  make test-quick   - Run fast tests only"
	@echo "  make clean        - Remove generated files"
	@echo "  make all          - Full pipeline (setup + analyze + evaluate)"

all: setup analyze evaluate
	@echo ""
	@echo "Symbol Scanner complete! Check:"
	@echo "  - outputs/<run-id>/output.json"
	@echo "  - evaluation/results/scorecard.md"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY)
	@echo "Setup complete!"

# =============================================================================
# Analysis
# =============================================================================

analyze: $(VENV_READY)
	@echo "Running symbol extraction on $(REPO_NAME)..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/analyze.py \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		$(COMMIT_ARG)

# =============================================================================
# Evaluation
# =============================================================================

evaluate: $(VENV_READY)
	@echo "Running programmatic evaluation..."
	@$(PYTHON_VENV) scripts/analyze.py \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(EVAL_OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		$(COMMIT_ARG)
	@$(PYTHON_VENV) -m scripts.evaluate \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json \
		--scorecard $(EVAL_OUTPUT_DIR) \
		--verbose
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"
	@echo "Scorecard saved to $(EVAL_OUTPUT_DIR)/scorecard.md"

evaluate-llm: $(VENV_READY)
	@echo "Running LLM evaluation (4 judges)..."
	@$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		--working-dir . \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--programmatic-results evaluation/results/evaluation_report.json \
		--model $(LLM_MODEL)
	@mkdir -p evaluation/results
	@if [ -w evaluation/results ]; then cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json; fi
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-quick: $(VENV_READY)
	@echo "Running quick tests..."
	@$(PYTHON_VENV) -m pytest tests/ -v --tb=short -x
	@echo "Quick tests complete!"

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean

clean-all: _common-clean-all
