# Layout Scanner Makefile
# Fast filesystem-based repository layout scanner
# Provides canonical file registry for all other tools

.PHONY: help setup build-repos analyze evaluate evaluate-llm evaluate-full \
        test test-cov test-unit test-integration clean clean-all all

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific configuration
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "")
EVAL_REPOS := eval-repos/synthetic
GROUND_TRUTH := evaluation/ground-truth

# Default target
help:
	@echo "Layout Scanner - Available targets:"
	@echo ""
	@echo "  make setup          - Create virtual environment and install dependencies"
	@echo "  make build-repos    - Create synthetic test repositories"
	@echo "  make analyze        - Run layout scanner on repository"
	@echo "  make evaluate       - Run programmatic evaluation"
	@echo "  make evaluate-llm   - Run LLM evaluation (4 judges)"
	@echo "  make test           - Run all pytest tests"
	@echo "  make clean          - Remove generated files"
	@echo "  make all            - Run full pipeline (build-repos, analyze, evaluate)"
	@echo ""
	@echo "Variables:"
	@echo "  REPO_PATH=<path>    - Repository to analyze (default: eval-repos/synthetic)"
	@echo "  REPO_NAME=<name>    - Repository name for output naming"
	@echo "  RUN_ID=<uuid>       - Run identifier (auto-generated if not set)"
	@echo "  REPO_ID=<uuid>      - Repository identifier (auto-generated if not set)"
	@echo "  BRANCH=<branch>     - Branch being analyzed (default: main)"
	@echo "  COMMIT=<sha>        - Commit SHA (auto-detected from git)"
	@echo "  OUTPUT_DIR=<path>   - Output directory (default: outputs/<run-id>)"
	@echo "  LLM_MODEL=<model>   - Model for LLM evaluation (sonnet, opus, haiku)"
	@echo ""
	@echo "Examples:"
	@echo "  make analyze REPO_PATH=/path/to/repo REPO_NAME=my-repo"
	@echo "  make evaluate-llm LLM_MODEL=opus"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY)
	@echo "Setup complete!"

# Build synthetic test repositories
build-repos: setup
	$(PYTHON_VENV) scripts/build_repos.py

# =============================================================================
# Analysis
# =============================================================================

# Run layout scanner with envelope output format
analyze: setup
	@mkdir -p $(OUTPUT_DIR)
ifdef REPO_PATH
	@echo "Scanning $(REPO_NAME)..."
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path "$(REPO_PATH)" \
		--repo-name "$(REPO_NAME)" \
		--output-dir "$(OUTPUT_DIR)" \
		--run-id "$(RUN_ID)" \
		--repo-id "$(REPO_ID)" \
		--branch "$(BRANCH)" \
		$(if $(NO_GITIGNORE),--no-gitignore,) \
		$(if $(COMMIT),--commit "$(COMMIT)",)
else
	@for repo in $(EVAL_REPOS)/*/; do \
		name=$$(basename $$repo); \
		run_id=$$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())"); \
		echo "Scanning $$name..."; \
		mkdir -p outputs/$$run_id; \
		$(PYTHON_VENV) -m scripts.analyze \
			--repo-path "$$repo" \
			--repo-name "$$name" \
			--output-dir "outputs/$$run_id" \
			--run-id "$$run_id" \
			--repo-id "$(REPO_ID)" \
			--branch "$(BRANCH)"; \
	done
endif

# =============================================================================
# Evaluation
# =============================================================================

# Run programmatic evaluation
evaluate: setup
	EVAL_OUTPUT_DIR=$(EVAL_OUTPUT_DIR) $(PYTHON_VENV) -m scripts.evaluate

# Run LLM evaluation (4 judges)
evaluate-llm: setup
	$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		--working-dir $(CURDIR) \
		--analysis $(OUTPUT_DIR)/output.json \
		--model $(LLM_MODEL) \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--programmatic-results evaluation/results/evaluation_report.json
	@mkdir -p evaluation/results
	@if [ "$(EVAL_OUTPUT_DIR)" != "evaluation/results" ] && [ -w evaluation/results ]; then cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json; fi

# Run both programmatic and LLM evaluation
evaluate-full: evaluate evaluate-llm
	@echo ""
	@echo "Full evaluation complete. Results in:"
	@echo "  - $(EVAL_OUTPUT_DIR)/evaluation_report.json (programmatic)"
	@echo "  - $(EVAL_OUTPUT_DIR)/llm_evaluation.json (LLM)"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-cov: $(VENV_READY)
	$(PYTHON_VENV) -m pytest tests/ --cov=scripts --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

test-unit: $(VENV_READY)
	$(PYTHON_VENV) -m pytest tests/unit/ -v

test-integration: $(VENV_READY) build-repos
	$(PYTHON_VENV) -m pytest tests/integration/ -v

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean

clean-all: _common-clean-all

# Full pipeline
all: build-repos analyze evaluate
