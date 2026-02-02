# PoC #1: scc (Size/LOC Analysis)
# Simplified Makefile for evaluating scc tool
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run analysis with v2.0 dashboard
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup analyze analyze-real analyze-interactive evaluate evaluate-llm \
        test test-quick clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# LLM timeout (seconds) for compliance runs
LLM_TIMEOUT ?= 300

# Tool-specific configuration
TOOL_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(abspath $(TOOL_ROOT)/../../..)
SCC_VERSION := 3.6.0
SCC_BIN := ./bin/scc

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || git -C $(PROJECT_ROOT) rev-parse HEAD 2>/dev/null)
COMMIT_ARG := $(if $(COMMIT),--commit $(COMMIT),)

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "PoC #1: scc (Size/LOC Analysis)"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install scc binary and Python dependencies"
	@echo "  make analyze      - Run directory analysis with v2.0 dashboard"
	@echo "  make evaluate     - Run programmatic evaluation (45 checks)"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Additional targets:"
	@echo "  make analyze-real        - Analyze real OSS repositories"
	@echo "  make analyze-interactive - Interactive multi-repo analysis"
	@echo "  make evaluate-llm - Run LLM-as-a-Judge evaluation"
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

setup: $(SCC_BIN) $(VENV_READY)
	@echo "Setup complete!"

$(SCC_BIN):
	@echo "Installing scc $(SCC_VERSION)..."
	@mkdir -p bin
	@OS=$$(uname -s); \
	ARCH=$$(uname -m); \
	URL="https://github.com/boyter/scc/releases/download/v$(SCC_VERSION)/scc_$${OS}_$${ARCH}.tar.gz"; \
	echo "Downloading from $$URL"; \
	curl -sL "$$URL" | tar xz -C bin scc; \
	chmod +x $(SCC_BIN)
	@$(SCC_BIN) --version

# =============================================================================
# Analysis
# =============================================================================

analyze: $(SCC_BIN) $(VENV_READY)
	@echo "Running directory analysis on $(REPO_NAME)..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/analyze.py \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		$(COMMIT_ARG) \
		--cocomo-preset sme \
		--no-color

analyze-real: $(SCC_BIN) $(VENV_READY)
	@echo "Initializing real repositories..."
	@git submodule update --init --recursive 2>/dev/null || true
	@echo "Analyzing real repositories..."
	@mkdir -p $(OUTPUT_DIR)/real
	@for repo in eval-repos/real/*/; do \
		name=$$(basename $$repo); \
		echo "  Analyzing $$name..."; \
		$(PYTHON) scripts/directory_analyzer.py $$repo \
			--cocomo-preset sme \
			--output $(OUTPUT_DIR)/real/$${name}.json \
			--no-color 2>/dev/null; \
	done
	@echo "Results saved to $(OUTPUT_DIR)/real/"

analyze-interactive: $(SCC_BIN) $(VENV_READY)
	@echo "Running interactive multi-repo analysis..."
	@$(PYTHON) scripts/directory_analyzer.py eval-repos --interactive

# =============================================================================
# Evaluation
# =============================================================================

evaluate: $(VENV_READY) $(SCC_BIN)
	@echo "Running programmatic evaluation..."
	@EVAL_OUTPUT_DIR=$(EVAL_OUTPUT_DIR) $(PYTHON_VENV) scripts/evaluate.py
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/scorecard.md"

evaluate-llm: $(VENV_READY)
	@echo "Running LLM-as-a-Judge evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@LLM_TIMEOUT=$(LLM_TIMEOUT) $(PYTHON_VENV) scripts/llm_evaluate.py --mode full --model $(LLM_MODEL) --output $(EVAL_OUTPUT_DIR)/llm_evaluation.json
	@mkdir -p evaluation/results
	@cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-quick: $(VENV_READY)
	@echo "Running quick tests..."
	@$(PYTHON_VENV) -m pytest tests/scripts/ tests/evaluation/llm/judges/ -v --tb=short -x
	@echo "Quick tests complete!"

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean
	@rm -f evaluation/timing.md
	@rm -rf bin

clean-all: _common-clean-all
	@rm -rf bin
