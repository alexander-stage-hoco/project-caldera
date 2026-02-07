# dotcover - Analysis Tool
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

.PHONY: help setup analyze analyze-docker analyze-coverlet docker-build evaluate evaluate-llm test test-quick clean clean-all

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

help:  ## Show this help message
	@echo "dotcover - Analysis Tool"
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

# Docker image for ARM64 workaround
DOCKER_IMAGE ?= dotcover-runner

docker-build:  ## Build Docker image for dotCover (bypasses ARM64 bug)
	@echo "Building Docker image (linux/amd64)..."
	docker build --platform linux/amd64 -t $(DOCKER_IMAGE) .

analyze-docker: docker-build $(VENV_READY)  ## Run analysis in Docker (bypasses ARM64 bug)
	@mkdir -p $(OUTPUT_DIR)
	@echo "Analyzing $(REPO_PATH) as project '$(REPO_NAME)' via Docker"
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT) \
		--docker

analyze-coverlet: $(VENV_READY)  ## Run analysis with Coverlet backend (ARM64 native)
	@mkdir -p $(OUTPUT_DIR)
	@echo "Analyzing $(REPO_PATH) as project '$(REPO_NAME)' with Coverlet"
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT) \
		--backend coverlet

# ============================================
# Evaluation targets
# ============================================

# Synthetic test run output (stable path for compliance checking)
SYNTHETIC_OUTPUT_DIR ?= outputs/dotcover-test-run

evaluate: $(VENV_READY)  ## Run programmatic evaluation
	@if [ ! -f "$(SYNTHETIC_OUTPUT_DIR)/output.json" ]; then \
		echo "Synthetic output not found at $(SYNTHETIC_OUTPUT_DIR)"; \
		echo "Running analysis on synthetic repo first..."; \
		$(MAKE) analyze REPO_PATH=eval-repos/synthetic RUN_ID=dotcover-test-run; \
	fi
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.evaluate \
		--results-dir $(SYNTHETIC_OUTPUT_DIR) \
		--ground-truth-dir evaluation/ground-truth \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-llm: $(VENV_READY)  ## Run LLM evaluation
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@mkdir -p evaluation/results
	$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		$(OUTPUT_DIR) \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model $(LLM_MODEL) \
		--programmatic-results evaluation/results/evaluation_report.json
	@if [ -w evaluation/results ]; then cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json; fi
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
