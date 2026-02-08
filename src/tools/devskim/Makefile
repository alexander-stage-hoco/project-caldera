# DevSkim Security Linter
# Detects security vulnerabilities using Microsoft's regex-based analyzer
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run analysis with dashboard
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup analyze evaluate evaluate-llm test test-quick test-coverage clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific configuration
EVAL_REPOS := eval-repos/synthetic
GROUND_TRUTH := evaluation/ground-truth
CUSTOM_RULES ?= rules/custom

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "")

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "DevSkim Security Linter - Project Caldera Tool"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup         - Install DevSkim CLI and Python dependencies"
	@echo "  make analyze       - Run security analysis with dashboard"
	@echo "  make evaluate      - Run programmatic evaluation (~28 checks)"
	@echo "  make test          - Run all tests"
	@echo "  make test-coverage - Run tests with coverage report (generates coverage.json)"
	@echo ""
	@echo "Analysis targets:"
	@echo "  make analyze            - Run analysis on default eval repo"
	@echo ""
	@echo "Evaluation targets:"
	@echo "  make evaluate           - Full evaluation with verbose output"
	@echo "  make evaluate-llm       - Run LLM evaluation"
	@echo ""
	@echo "Variables:"
	@echo "  REPO_PATH=<path>    - Repository to analyze (default: eval-repos/synthetic)"
	@echo "  REPO_NAME=<name>    - Repository name for output naming"
	@echo "  RUN_ID=<uuid>       - Run identifier (auto-generated if not set)"
	@echo "  REPO_ID=<uuid>      - Repository identifier (auto-generated if not set)"
	@echo "  BRANCH=<branch>     - Branch being analyzed (default: main)"
	@echo "  COMMIT=<sha>        - Commit SHA (auto-detected from git)"
	@echo "  OUTPUT_DIR=<path>   - Output directory (default: outputs/<run-id>)"
	@echo "  CUSTOM_RULES=<path> - Custom rules directory (default: rules/custom)"
	@echo "  LLM_MODEL=<model>   - Model for LLM evaluation (sonnet, opus, haiku)"
	@echo ""
	@echo "Examples:"
	@echo "  make analyze REPO_PATH=/path/to/repo REPO_NAME=my-repo"
	@echo "  make evaluate-llm LLM_MODEL=opus"

all: setup analyze evaluate
	@echo ""
	@echo "Full pipeline complete! Check:"
	@echo "  - $(OUTPUT_DIR)/output.json"
	@echo "  - $(EVAL_OUTPUT_DIR)/"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY) _check-devskim
	@echo "Setup complete!"

_check-devskim:
	@echo "Checking DevSkim CLI installation..."
	@which devskim > /dev/null 2>&1 || (echo "Installing DevSkim CLI..." && dotnet tool install --global Microsoft.CST.DevSkim.CLI)
	@DOTNET_ROLL_FORWARD=LatestMajor devskim --version

# =============================================================================
# Analysis
# =============================================================================

# Run analysis with envelope output format
analyze: setup
	@mkdir -p $(OUTPUT_DIR)
ifdef REPO_PATH
	@echo "Analyzing $(REPO_NAME)..."
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path "$(REPO_PATH)" \
		--repo-name "$(REPO_NAME)" \
		--output-dir "$(OUTPUT_DIR)" \
		--run-id "$(RUN_ID)" \
		--repo-id "$(REPO_ID)" \
		--branch "$(BRANCH)" \
		$(if $(COMMIT),--commit "$(COMMIT)",) \
		$(if $(CUSTOM_RULES),--custom-rules "$(CUSTOM_RULES)",)
else
	@for repo in $(EVAL_REPOS)/*/; do \
		name=$$(basename $$repo); \
		run_id=$$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())"); \
		echo "Analyzing $$name..."; \
		mkdir -p outputs/$$run_id; \
		$(PYTHON_VENV) -m scripts.analyze \
			--repo-path "$$repo" \
			--repo-name "$$name" \
			--output-dir "outputs/$$run_id" \
			--run-id "$$run_id" \
			--repo-id "$(REPO_ID)" \
			--branch "$(BRANCH)" \
			$(if $(CUSTOM_RULES),--custom-rules "$(CUSTOM_RULES)",); \
	done
endif

# =============================================================================
# Evaluation
# =============================================================================

# Run programmatic evaluation
evaluate: setup
	@echo "Running programmatic evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/evaluate.py --output $(EVAL_OUTPUT_DIR)/evaluation_report.json

# Run LLM evaluation
evaluate-llm: setup analyze
	@echo "Running LLM evaluation..."
	@$(PYTHON_VENV) -m evaluation.llm.orchestrator --model $(LLM_MODEL)
	@echo "LLM evaluation complete. See evaluation/llm/results/"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-quick: _common-test-quick

# Run tests with coverage report generation
# Note: --cov-fail-under=50 is a baseline; aim for 80%+ over time
test-coverage: $(VENV_READY)
	@echo "Running tests with coverage..."
	@$(PYTHON_VENV) -m pytest tests/ -v --tb=short \
		--cov=scripts \
		--cov-report=json \
		--cov-report=term-missing \
		--cov-fail-under=50
	@echo "Coverage report generated: coverage.json"

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean
	@rm -rf evaluation/llm/results/*
	@rm -rf evaluation/results/
	@rm -f coverage.json .coverage

clean-all: _common-clean-all
