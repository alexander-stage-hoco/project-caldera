# Semgrep Code Smell Analysis Tool
# Detects code smells using Semgrep with 87 custom DD-mapped rules
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run analysis with dashboard
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup init-submodules init-elttam analyze analyze-real analyze-interactive \
        evaluate evaluate-json evaluate-quick evaluate-llm evaluate-llm-focused evaluate-combined evaluate-full \
        test test-quick test-cov clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific configuration
EVAL_REPOS := eval-repos/synthetic
GROUND_TRUTH := evaluation/ground-truth

# Offline mode: reduce pip retries/timeouts to avoid long waits
OFFLINE ?= 0
ifeq ($(OFFLINE),1)
	PIP_ARGS += --retries 0 --timeout 1
endif

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "")

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "Semgrep Code Smell Analysis Tool"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install dependencies (semgrep + python)"
	@echo "  make analyze      - Run smell analysis with dashboard"
	@echo "  make evaluate     - Run programmatic evaluation (~28 checks)"
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
	@echo "  make evaluate-llm         - Run LLM evaluation (4 judges)"
	@echo "  make evaluate-llm-focused - Run single judge (smell accuracy only)"
	@echo "  make evaluate-combined    - Combined programmatic + LLM evaluation"
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
	@echo "Environment variables for ruleset configuration:"
	@echo "  SEMGREP_USE_REGISTRY=1    - Enable official Semgrep registry rulesets"
	@echo "  SEMGREP_USE_COMMUNITY=1   - Enable community C# rules (Microsoft CA)"
	@echo "  SEMGREP_USE_MULTI_LANG=1  - Enable multi-language rulesets (JS, TS, Python, Java, Go)"
	@echo "  SEMGREP_USE_ELTTAM=1      - Enable Elttam audit rules (requires init-elttam)"
	@echo ""
	@echo "Examples:"
	@echo "  make analyze REPO_PATH=/path/to/repo REPO_NAME=my-repo"
	@echo "  make evaluate-llm LLM_MODEL=opus"
	@echo "  SEMGREP_USE_REGISTRY=1 SEMGREP_USE_MULTI_LANG=1 make analyze"

all: setup analyze evaluate
	@echo ""
	@echo "Full pipeline complete! Check:"
	@echo "  - $(OUTPUT_DIR)/output.json"
	@echo "  - $(EVAL_OUTPUT_DIR)/"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY) $(VENV)/bin/semgrep init-submodules init-elttam
	@echo "Setup complete!"

ifeq ($(SKIP_SETUP),1)
$(VENV)/bin/semgrep: $(VENV_READY)
	@echo "SKIP_SETUP=1: skipping semgrep install"
	@if [ ! -f "$(VENV)/bin/semgrep" ]; then \
		if [ -w "$(VENV)/bin" ]; then \
			touch $(VENV)/bin/semgrep; \
		else \
			echo "Venv bin not writable; skipping semgrep stub creation"; \
		fi; \
	fi
else
$(VENV)/bin/semgrep: $(VENV_READY)
	@echo "Installing Semgrep..."
	@$(PIP) install $(PIP_ARGS) semgrep -q
	@touch $(VENV)/bin/semgrep
endif

init-submodules:
	@echo "Initializing real repositories..."
	@git submodule update --init --recursive 2>/dev/null || true

init-elttam:
	@echo "Initializing Elttam audit rules..."
	@if [ ! -d "external-rules/elttam" ]; then \
		mkdir -p external-rules && \
		git clone --depth 1 https://github.com/elttam/semgrep-rules.git external-rules/elttam 2>/dev/null || \
		echo "  Elttam rules clone failed (offline or network issue), skipping"; \
	else \
		echo "  Elttam rules already present"; \
	fi

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
		$(if $(COMMIT),--commit "$(COMMIT)",)
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
			--branch "$(BRANCH)"; \
	done
endif

analyze-real: setup init-submodules
	@echo "Analyzing real repositories..."
	@for repo in eval-repos/real/*/; do \
		name=$$(basename $$repo); \
		run_id=$$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())"); \
		echo "  Analyzing $$name..."; \
		mkdir -p outputs/$$run_id; \
		$(PYTHON_VENV) -m scripts.analyze \
			--repo-path "$$repo" \
			--repo-name "$$name" \
			--output-dir "outputs/$$run_id" \
			--run-id "$$run_id" \
			--repo-id "$(REPO_ID)" \
			--branch "$(BRANCH)" \
			--no-color 2>/dev/null; \
	done
	@echo "Results saved to outputs/"

analyze-interactive: setup
	@echo "Running interactive multi-repo analysis..."
	@$(PYTHON_VENV) scripts/smell_analyzer.py eval-repos --interactive

# =============================================================================
# Evaluation
# =============================================================================

# Run programmatic evaluation
evaluate: setup
	@echo "Running programmatic evaluation (~28 checks)..."
	EVAL_OUTPUT_DIR=$(EVAL_OUTPUT_DIR) $(PYTHON_VENV) -m scripts.evaluate \
		--analysis evaluation/results/output.json \
		--ground-truth $(GROUND_TRUTH) \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-json: setup
	@$(PYTHON_VENV) -m scripts.evaluate \
		--analysis evaluation/results/output.json \
		--ground-truth $(GROUND_TRUTH) \
		--json

evaluate-quick: setup
	@echo "Running quick evaluation (no performance checks)..."
	@$(PYTHON_VENV) -m scripts.evaluate \
		--analysis evaluation/results/output.json \
		--ground-truth $(GROUND_TRUTH) \
		--quick

# Run LLM evaluation (4 judges)
evaluate-llm: setup analyze
	@echo "Running LLM evaluation (4 judges)..."
	$(PYTHON_VENV) -m scripts.llm_evaluate \
		--analysis outputs \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model $(LLM_MODEL)
	@mkdir -p evaluation/results
	@if [ -w evaluation/results ]; then cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json; fi
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

evaluate-llm-focused: setup
	@echo "Running focused LLM evaluation (smell accuracy only)..."
	@$(PYTHON_VENV) -m scripts.llm_evaluate \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation_focused.json \
		--model $(LLM_MODEL) \
		--skip-judge rule_coverage \
		--skip-judge false_positive_rate \
		--skip-judge actionability

evaluate-combined: setup analyze evaluate
	@echo "Running combined programmatic + LLM evaluation..."
	@$(PYTHON_VENV) -m scripts.llm_evaluate \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/combined_evaluation.json \
		--model $(LLM_MODEL) \
		--programmatic-score 0.687
	@echo ""
	@echo "Combined results saved to $(EVAL_OUTPUT_DIR)/combined_evaluation.json"

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

test-quick: _common-test-quick

test-cov: $(VENV_READY)
	$(PYTHON_VENV) -m pytest tests/ --cov=scripts --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean
	@rm -rf evaluation/llm/results/*
	@rm -f evaluation/scorecard.md

clean-all: _common-clean-all
