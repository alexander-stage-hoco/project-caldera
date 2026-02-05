# git-sizer - Repository Health Analysis Tool
# Caldera-compliant Makefile
#
# Quick start:
#   make setup        - Install dependencies and download git-sizer binary
#   make analyze      - Run repository analysis
#   make evaluate     - Run programmatic evaluation
#   make evaluate-llm - Run LLM evaluation
#   make test         - Run all tests
#   make clean        - Remove generated files

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: all setup analyze analyze-synthetic evaluate evaluate-llm test test-quick clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# =============================================================================
# Configuration
# =============================================================================

GIT_SIZER := bin/git-sizer

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic/healthy
REPO_NAME ?= healthy
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

# Evaluation directories
GROUND_TRUTH_DIR ?= evaluation/ground-truth
LLM_TIMEOUT ?= 300

# Platform detection for binary download
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Darwin)
    ifeq ($(UNAME_M),arm64)
        GIT_SIZER_URL := https://github.com/github/git-sizer/releases/download/v1.5.0/git-sizer-1.5.0-darwin-arm64.zip
    else
        GIT_SIZER_URL := https://github.com/github/git-sizer/releases/download/v1.5.0/git-sizer-1.5.0-darwin-amd64.zip
    endif
else
    ifeq ($(UNAME_M),x86_64)
        GIT_SIZER_URL := https://github.com/github/git-sizer/releases/download/v1.5.0/git-sizer-1.5.0-linux-amd64.zip
    else
        GIT_SIZER_URL := https://github.com/github/git-sizer/releases/download/v1.5.0/git-sizer-1.5.0-linux-386.zip
    endif
endif

# =============================================================================
# Help
# =============================================================================

help:
	@echo "git-sizer - Repository Health Analysis Tool (Caldera)"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install dependencies and download git-sizer"
	@echo "  make analyze      - Run repository analysis"
	@echo "  make evaluate     - Run programmatic evaluation"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Analysis targets:"
	@echo "  make analyze REPO_PATH=/path/to/repo REPO_NAME=myrepo"
	@echo "  make analyze-synthetic  - Analyze all synthetic test repos"
	@echo ""
	@echo "Evaluation targets:"
	@echo "  make evaluate      - Full programmatic evaluation"
	@echo "  make evaluate-llm  - Run LLM evaluation"
	@echo ""
	@echo "Required variables for analyze:"
	@echo "  REPO_PATH  - Path to repository (default: eval-repos/synthetic/healthy)"
	@echo "  RUN_ID     - UUID for collection run (auto-generated)"
	@echo "  REPO_ID    - UUID for repository (auto-generated)"
	@echo "  BRANCH     - Git branch (default: main)"
	@echo "  COMMIT     - Git commit SHA (auto-detected from REPO_PATH)"

all: setup analyze-synthetic evaluate
	@echo ""
	@echo "Pipeline complete! Check:"
	@echo "  - outputs/"
	@echo "  - evaluation/results/"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY) $(GIT_SIZER) init-synthetic-repos
	@echo "Setup complete!"

$(GIT_SIZER):
	@echo "Downloading git-sizer..."
	@mkdir -p bin
	@curl -sL $(GIT_SIZER_URL) -o bin/git-sizer.zip
	@unzip -q -o bin/git-sizer.zip -d bin/
	@chmod +x bin/git-sizer
	@rm -f bin/git-sizer.zip
	@echo "git-sizer installed to bin/git-sizer"

init-synthetic-repos:
	@echo "Synthetic test repositories should be created manually or via scripts."
	@echo "See eval-repos/synthetic/ for test repositories."

# =============================================================================
# Analysis
# =============================================================================

analyze: $(VENV_READY) $(GIT_SIZER)
	@echo "Running repository analysis..."
	@echo "  REPO_PATH: $(REPO_PATH)"
	@echo "  RUN_ID:    $(RUN_ID)"
	@echo "  REPO_ID:   $(REPO_ID)"
	@echo "  BRANCH:    $(BRANCH)"
	@echo "  COMMIT:    $(COMMIT)"
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT) \
		--exit-zero

# Analyze all synthetic repos
analyze-synthetic: $(VENV_READY) $(GIT_SIZER)
	@echo "Analyzing all synthetic repositories..."
	@mkdir -p evaluation/results
	@for repo in eval-repos/synthetic/*/; do \
		if [ -d "$$repo/.git" ]; then \
			name=$$(basename $$repo); \
			rid=$$(python3 -c "import uuid; print(str(uuid.uuid4()))"); \
			repoid=$$(python3 -c "import uuid; print(str(uuid.uuid4()))"); \
			commit=$$(git -C $$repo rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000"); \
			echo "  Analyzing $$name..."; \
			$(PYTHON_VENV) -m scripts.analyze \
				--repo-path $$repo \
				--repo-name $$name \
				--output-dir evaluation/results/$$name \
				--run-id $$rid \
				--repo-id $$repoid \
				--branch main \
				--commit $$commit \
				--exit-zero || true; \
		fi; \
	done
	@echo "Analysis complete! Results in evaluation/results/"

# =============================================================================
# Evaluation
# =============================================================================

evaluate: $(VENV_READY)
	@echo "Running programmatic evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON_VENV) -m scripts.evaluate \
		--results-dir $(OUTPUT_DIR) \
		--ground-truth-dir $(GROUND_TRUTH_DIR) \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-llm: $(VENV_READY)
	@echo "Running LLM evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		$(OUTPUT_DIR) \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model $(LLM_MODEL) \
		--timeout $(LLM_TIMEOUT) \
		--programmatic-results $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@mkdir -p evaluation/results
	@cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: _common-test  ## Run all tests

test-quick: _common-test-quick  ## Run quick tests (stop on first failure)

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean  ## Clean build artifacts
	@rm -rf bin/git-sizer.zip

clean-all: _common-clean-all  ## Clean all including venv
	@rm -rf bin/
