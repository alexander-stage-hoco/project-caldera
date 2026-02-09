# git-blame-scanner - Analysis Tool
# Caldera-compliant Makefile
#
# Quick start:
#   make setup        - Install dependencies
#   make analyze      - Run analysis
#   make evaluate     - Run programmatic evaluation
#   make evaluate-llm - Run LLM evaluation
#   make test         - Run all tests
#   make clean        - Remove generated files

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup analyze evaluate evaluate-llm test test-quick clean clean-all

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

help:  ## Show this help message
	@echo "git-blame-scanner - Analysis Tool"
	@echo ""
	@echo "Usage: make <target> [REPO_PATH=<path>] [REPO_NAME=<name>]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ============================================
# Setup targets
# ============================================

setup: $(VENV_READY)  ## Set up virtual environment
	@echo "Setup complete"

# ============================================
# Analysis targets
# ============================================

analyze: $(VENV_READY)  ## Run analysis on a repository
	@mkdir -p $(OUTPUT_DIR)
	@echo "Analyzing $(REPO_PATH) as project '$(REPO_NAME)'"
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT)

# ============================================
# Evaluation targets
# ============================================

evaluate: $(VENV_READY)  ## Run programmatic evaluation
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.evaluate \
		--results-dir $(OUTPUT_DIR) \
		--ground-truth-dir evaluation/ground-truth \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-llm: $(VENV_READY)  ## Run LLM evaluation
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		$(OUTPUT_DIR) \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model $(LLM_MODEL)
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

# ============================================
# Test targets
# ============================================

test: _common-test  ## Run all tests

test-quick: _common-test-quick  ## Run quick tests (stop on first failure)

# ============================================
# Cleanup targets
# ============================================

clean: _common-clean  ## Clean build artifacts

clean-all: _common-clean-all  ## Clean all including venv
