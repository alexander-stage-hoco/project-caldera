# PoC #2: Lizard (Function-Level Complexity Analysis)
# Makefile for evaluating Lizard tool
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run analysis with dashboard
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup init-submodules analyze analyze-real analyze-interactive \
        evaluate evaluate-json evaluate-quick evaluate-llm evaluate-llm-focused evaluate-combined \
        test test-quick clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific configuration
TOOL_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(abspath $(TOOL_ROOT)/../../..)

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || git -C $(PROJECT_ROOT) rev-parse HEAD 2>/dev/null)
COMMIT_ARG := $(if $(COMMIT),--commit $(COMMIT),)

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "PoC #2: Lizard (Function-Level Complexity Analysis)"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install Python dependencies (lizard)"
	@echo "  make analyze      - Run function analysis with dashboard"
	@echo "  make evaluate     - Run programmatic evaluation (76 checks)"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Analysis targets:"
	@echo "  make analyze-real        - Analyze real OSS repositories"
	@echo "  make analyze-interactive - Interactive multi-repo analysis"
	@echo ""
	@echo "Evaluation targets:"
	@echo "  make evaluate       - Full evaluation with verbose output"
	@echo "  make evaluate-json  - Output evaluation as JSON only"
	@echo "  make evaluate-quick - Quick evaluation without performance checks"
	@echo ""
	@echo "LLM Evaluation targets:"
	@echo "  make evaluate-llm         - Run LLM evaluation (4 judges, opus)"
	@echo "  make evaluate-llm-focused - Run single judge (CCN accuracy, opus)"
	@echo "  make evaluate-combined    - Combined programmatic + LLM evaluation"
	@echo ""
	@echo "Additional targets:"
	@echo "  make test-quick   - Run fast tests only"
	@echo "  make clean        - Remove generated files"
	@echo "  make all          - Full pipeline (setup + analyze + evaluate)"

all: setup analyze evaluate
	@echo ""
	@echo "PoC complete! Check:"
	@echo "  - outputs/<run-id>/output.json"
	@echo "  - evaluation/results/scorecard.md"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY) init-submodules
	@echo "Setup complete!"

init-submodules:
	@echo "Initializing real repositories..."
	@git submodule update --init --recursive 2>/dev/null || true

# =============================================================================
# Analysis
# =============================================================================

analyze: $(VENV_READY)
	@echo "Running function analysis on $(REPO_NAME)..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/analyze.py \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		$(COMMIT_ARG) \
		--no-color

analyze-real: $(VENV_READY) init-submodules
	@echo "Analyzing real repositories..."
	@mkdir -p $(OUTPUT_DIR)/real
	@for repo in eval-repos/real/*/; do \
		name=$$(basename $$repo); \
		echo "  Analyzing $$name..."; \
		$(PYTHON) scripts/function_analyzer.py $$repo \
			--output $(OUTPUT_DIR)/real/$${name}.json \
			--no-color 2>/dev/null; \
	done
	@echo "Results saved to $(OUTPUT_DIR)/real/"

analyze-interactive: $(VENV_READY)
	@echo "Running interactive multi-repo analysis..."
	@$(PYTHON) scripts/function_analyzer.py eval-repos --interactive

# =============================================================================
# Evaluation
# =============================================================================

evaluate: $(VENV_READY)
	@echo "Running programmatic evaluation (76 checks)..."
	@$(PYTHON_VENV) scripts/analyze.py \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(EVAL_OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		$(COMMIT_ARG) \
		--no-color
	@$(PYTHON) scripts/evaluate.py \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json \
		--scorecard $(EVAL_OUTPUT_DIR) \
		--verbose
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"
	@echo "Scorecard saved to $(EVAL_OUTPUT_DIR)/scorecard.md"

evaluate-json: $(VENV_READY)
	@$(PYTHON) scripts/evaluate.py \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth \
		--json

evaluate-quick: $(VENV_READY)
	@echo "Running quick evaluation (no performance checks)..."
	@$(PYTHON) scripts/evaluate.py \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth

evaluate-llm: $(VENV_READY)
	@echo "Running LLM evaluation (4 judges)..."
	@$(PYTHON) -m evaluation.llm.orchestrator \
		--working-dir . \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model opus
	@mkdir -p evaluation/results
	@cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

evaluate-llm-focused: $(VENV_READY)
	@echo "Running focused LLM evaluation (CCN accuracy only)..."
	@$(PYTHON) -m evaluation.llm.orchestrator \
		--working-dir . \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation_focused.json \
		--model opus \
		--judges ccn_accuracy

evaluate-combined: $(VENV_READY) evaluate evaluate-llm
	@echo "Running combined evaluation (programmatic + LLM)..."
	@$(PYTHON) -m evaluation.llm.orchestrator \
		--working-dir . \
		--analysis $(EVAL_OUTPUT_DIR)/output.json \
		--programmatic-results $(EVAL_OUTPUT_DIR)/evaluation_report.json \
		--output $(EVAL_OUTPUT_DIR)/combined_evaluation.json \
		--model opus
	@echo ""
	@echo "Combined results saved to $(EVAL_OUTPUT_DIR)/combined_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-quick: $(VENV_READY)
	@echo "Running quick tests..."
	@$(PYTHON_VENV) -m pytest tests/scripts/ -v --tb=short -x
	@echo "Quick tests complete!"

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean

clean-all: _common-clean-all
