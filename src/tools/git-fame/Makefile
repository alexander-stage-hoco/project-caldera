# git-fame Makefile
# Line-level authorship attribution via git blame
#
# Quick start:
#   make setup        - Install dependencies
#   make build-repos  - Create synthetic test repositories
#   make analyze      - Run analysis on eval-repos
#   make evaluate     - Run programmatic evaluation
#   make evaluate-llm - Run LLM evaluation
#   make test         - Run all tests
#   make clean        - Remove generated files

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup build-repos analyze evaluate evaluate-llm test test-quick clean clean-all

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

help:  ## Show this help message
	@echo "git-fame - Authorship Attribution Analysis"
	@echo ""
	@echo "Usage: make <target> [REPO_PATH=<path>] [REPO_NAME=<name>]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ============================================
# Setup targets
# ============================================

setup: $(VENV_READY)  ## Set up virtual environment
	@echo "Verifying git-fame installation..."
	@$(PYTHON_VENV) -m gitfame --version || $(PYTHON_VENV) -c "import gitfame; print('gitfame module installed successfully')"
	@echo "Setup complete!"

# ============================================
# Build targets
# ============================================

build-repos: $(VENV_READY)  ## Build synthetic test repositories
	@echo "Building synthetic test repositories..."
	$(PYTHON_VENV) scripts/build_repos.py
	@echo "Synthetic repos created in eval-repos/synthetic/"

# ============================================
# Analysis targets
# ============================================

analyze: $(VENV_READY)  ## Run analysis on eval-repos
	@echo "Running authorship analysis on $(REPO_NAME)..."
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path "$(REPO_PATH)" \
		--repo-name "$(REPO_NAME)" \
		--output-dir "$(OUTPUT_DIR)" \
		--run-id "$(RUN_ID)" \
		--repo-id "$(REPO_ID)" \
		--branch "$(BRANCH)" \
		--commit "$(COMMIT)"
	@echo "Analysis complete. Results in $(OUTPUT_DIR)/"

# Run analysis on specific repo
analyze-%: $(VENV_READY)
	@echo "Running analysis on eval-repos/synthetic/$*..."
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/$* REPO_NAME=$*

# ============================================
# Evaluation targets
# ============================================

evaluate: $(VENV_READY)  ## Run programmatic evaluation
	@echo "Running programmatic evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) scripts/evaluate.py --output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo "Evaluation complete. See evaluation/scorecard.md"

evaluate-llm: $(VENV_READY)  ## Run LLM-as-a-Judge evaluation
	@echo "Running LLM-as-a-Judge evaluation..."
	$(PYTHON_VENV) -m evaluation.llm.orchestrator --model $(LLM_MODEL) --output evaluation/results/llm_evaluation.json
	@echo "LLM evaluation complete. See evaluation/results/llm_evaluation.json"

# ============================================
# Test targets
# ============================================

test: $(VENV_READY)  ## Run all tests
	@echo "Running all tests..."
	$(PYTHON_VENV) -m pytest tests/ -v
	@echo "All tests complete!"

test-quick: $(VENV_READY)  ## Run quick tests (stop on first failure)
	@echo "Running quick tests..."
	$(PYTHON_VENV) -m pytest tests/scripts/ -v -x
	@echo "Quick tests complete!"

# ============================================
# Ground truth seeding
# ============================================

seed-ground-truth: _common-seed-ground-truth  ## Seed ground truth from analysis output

# ============================================
# Cleanup targets
# ============================================

clean: _common-clean  ## Clean build artifacts
	@rm -rf evaluation/results/*
	@rm -rf evaluation/llm/results/*

clean-all: _common-clean-all  ## Clean all including venv
	@rm -rf evaluation/results/*
	@rm -rf evaluation/llm/results/*
