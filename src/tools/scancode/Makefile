# scancode - License Analysis Tool
# Analyzes repositories for license detection and compliance risk assessment
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run license analysis
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup analyze build-repos evaluate evaluate-llm test test-quick clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific configuration
TOOL_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(abspath $(TOOL_ROOT)/../../..)

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
# Strip trailing slash from REPO_PATH before extracting name
REPO_NAME ?= $(notdir $(patsubst %/,%,$(REPO_PATH)))
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || git -C $(PROJECT_ROOT) rev-parse HEAD 2>/dev/null)
COMMIT_ARG := $(if $(COMMIT),--commit $(COMMIT),)

# LLM timeout (seconds) for compliance runs
LLM_TIMEOUT ?= 300

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "scancode - License Analysis Tool"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install Python dependencies"
	@echo "  make analyze      - Run license analysis"
	@echo "  make evaluate     - Run programmatic evaluation"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Additional targets:"
	@echo "  make build-repos  - Create synthetic test repositories"
	@echo "  make evaluate-llm - Run LLM-as-a-Judge evaluation"
	@echo "  make test-quick   - Run fast tests only"
	@echo "  make clean        - Remove generated files"
	@echo "  make all          - Full pipeline (setup + analyze + evaluate)"

all: setup analyze evaluate
	@echo ""
	@echo "Pipeline complete! Check:"
	@echo "  - outputs/<run-id>/output.json"
	@echo "  - evaluation/results/"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY)
	@echo "Setup complete!"

# =============================================================================
# Build Synthetic Repos
# =============================================================================

build-repos: $(VENV_READY)
	@echo "Building synthetic test repositories..."
	@$(PYTHON_VENV) scripts/create_synthetic_repos.py
	@echo "Synthetic repos created in eval-repos/synthetic/"

# =============================================================================
# Analysis
# =============================================================================

analyze: $(VENV_READY)
	@echo "Running license analysis on $(REPO_NAME)..."
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
	@EVAL_OUTPUT_DIR=$(EVAL_OUTPUT_DIR) $(PYTHON_VENV) scripts/evaluate.py
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/"

evaluate-llm: $(VENV_READY)
	@echo "Running LLM-as-a-Judge evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@LLM_TIMEOUT=$(LLM_TIMEOUT) $(PYTHON_VENV) scripts/llm_evaluate.py --mode full --model $(LLM_MODEL) --output $(EVAL_OUTPUT_DIR)/llm_evaluation.json
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-quick: $(VENV_READY)
	@echo "Running quick tests..."
	@$(PYTHON_VENV) -m pytest tests/unit/ -v --tb=short -x
	@echo "Quick tests complete!"

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean
	@rm -rf eval-repos/synthetic/*/

clean-all: _common-clean-all
	@rm -rf eval-repos/synthetic/*/
