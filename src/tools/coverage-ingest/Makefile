# coverage-ingest: Multi-format test coverage ingestion
# Supports LCOV, Cobertura, JaCoCo, Istanbul formats
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run coverage ingestion
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup analyze evaluate evaluate-llm test test-quick clean clean-all help

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

# Coverage file to ingest (required for analyze)
COVERAGE_FILE ?=
FORMAT ?= auto

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "coverage-ingest: Multi-format test coverage ingestion"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install Python dependencies"
	@echo "  make analyze      - Run coverage ingestion"
	@echo "  make evaluate     - Run programmatic evaluation"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Analyze usage:"
	@echo "  make analyze COVERAGE_FILE=/path/to/coverage.xml"
	@echo "  make analyze COVERAGE_FILE=/path/to/lcov.info FORMAT=lcov"
	@echo ""
	@echo "Supported formats: lcov, cobertura, jacoco, istanbul, auto"
	@echo ""
	@echo "Additional targets:"
	@echo "  make evaluate-llm - Run LLM-based quality evaluation"
	@echo "  make test-quick   - Run fast tests only"
	@echo "  make clean        - Remove generated files"
	@echo "  make all          - Full pipeline (setup + analyze + evaluate)"

all: setup analyze evaluate
	@echo ""
	@echo "Coverage ingestion complete! Check:"
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
ifndef COVERAGE_FILE
	@echo "Error: COVERAGE_FILE is required."
	@echo "Usage: make analyze COVERAGE_FILE=/path/to/coverage.xml"
	@exit 1
endif
	@echo "Ingesting coverage from $(COVERAGE_FILE)..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/analyze.py \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		$(COMMIT_ARG) \
		--coverage-file $(COVERAGE_FILE) \
		--format $(FORMAT)

# =============================================================================
# Evaluation
# =============================================================================

evaluate: $(VENV_READY)
	@echo "Running programmatic evaluation..."
	@EVAL_OUTPUT_DIR=$(EVAL_OUTPUT_DIR) $(PYTHON_VENV) scripts/evaluate.py
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/scorecard.md"

# LLM model for evaluation (default: opus-4.5)
LLM_MODEL ?= opus-4.5

evaluate-llm: $(VENV_READY)
	@echo "Running LLM evaluation..."
	@$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		$(OUTPUT_DIR) \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model $(LLM_MODEL)

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
