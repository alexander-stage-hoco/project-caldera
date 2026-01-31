# Roslyn Analyzers (.NET Code Quality Analysis)
# Makefile for Project Caldera
#
# Quick start:
#   make setup    - Install dependencies (one-time)
#   make analyze  - Run analysis with dashboard
#   make evaluate - Run programmatic evaluation
#   make test     - Run all tests

.PHONY: all setup check-dotnet init-submodules build build-external \
        analyze analyze-real analyze-interactive \
        evaluate evaluate-json evaluate-quick evaluate-llm evaluate-llm-focused evaluate-combined \
        test test-quick clean clean-all help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic/csharp
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")
SYNTHETIC_DIR := eval-repos/synthetic/csharp

# Performance tuning
BUILD_TIMEOUT ?= 900

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "Roslyn Analyzers (.NET Code Quality Analysis)"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install dependencies (python + dotnet check)"
	@echo "  make build        - Build synthetic C# project"
	@echo "  make analyze      - Run Roslyn analysis with dashboard"
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
	@echo "  make evaluate-llm         - Run LLM evaluation (4 judges, opus)"
	@echo "  make evaluate-llm-focused - Run single judge (detection accuracy, opus)"
	@echo "  make evaluate-combined    - Combined programmatic + LLM evaluation"
	@echo ""
	@echo "Additional targets:"
	@echo "  make test-quick   - Run fast tests only"
	@echo "  make clean        - Remove generated files"
	@echo "  make all          - Full pipeline (setup + analyze + evaluate)"

all: setup build analyze evaluate
	@echo ""
	@echo "Complete! Check:"
	@echo "  - $(OUTPUT_DIR)/output.json"
	@echo "  - evaluation/scorecard.md"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY) check-dotnet init-submodules
	@echo "Setup complete!"

check-dotnet:
	@echo "Checking .NET SDK installation..."
	@which dotnet > /dev/null 2>&1 || (echo "ERROR: .NET SDK not found. Install from https://dotnet.microsoft.com/download" && exit 1)
	@dotnet --version
	@echo ".NET SDK found!"

init-submodules:
	@echo "Initializing real repositories..."
	@git submodule update --init --recursive 2>/dev/null || true

# =============================================================================
# Build
# =============================================================================

build: $(SYNTHETIC_DIR)/SyntheticSmells.csproj
	@echo "Building synthetic C# project..."
	@mkdir -p output/runs
	@cd $(SYNTHETIC_DIR) && dotnet restore -v q
	@cd $(SYNTHETIC_DIR) && dotnet build -v q /p:TreatWarningsAsErrors=false || true
	@echo "Build complete (warnings expected for smell detection)"

# =============================================================================
# Analysis
# =============================================================================

# Check if external repo is provided (not default synthetic path)
IS_EXTERNAL_REPO := $(if $(filter-out eval-repos/synthetic/csharp,$(REPO_PATH)),yes,)

# Build external repo if needed
build-external:
ifeq ($(IS_EXTERNAL_REPO),yes)
	@echo "Building external repo: $(REPO_PATH)..."
	@cd $(REPO_PATH) && dotnet restore -v q || true
	@cd $(REPO_PATH) && dotnet build -v q -c Release /p:TreatWarningsAsErrors=false || echo "Build completed (some errors may be expected)"
else
	@echo "Using synthetic repo, running standard build..."
	@$(MAKE) build
endif

analyze: $(VENV_READY) build-external
	@echo "Running Roslyn analysis..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/analyze.py \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT) \
		--output-dir $(OUTPUT_DIR) \
		--build-timeout $(BUILD_TIMEOUT)

analyze-real: $(VENV_READY) init-submodules
	@echo "Analyzing real repositories..."
	@mkdir -p $(OUTPUT_DIR)/real
	@for repo in eval-repos/real/*/; do \
		name=$$(basename $$repo); \
		echo "  Analyzing $$name..."; \
		$(PYTHON_VENV) scripts/roslyn_analyzer.py $$repo \
			--output $(OUTPUT_DIR)/real/$${name}.json \
			--no-color 2>/dev/null || true; \
	done
	@echo "Results saved to $(OUTPUT_DIR)/real/"

analyze-interactive: $(VENV_READY)
	@echo "Running interactive multi-repo analysis..."
	@$(PYTHON_VENV) scripts/roslyn_analyzer.py eval-repos --interactive

# =============================================================================
# Evaluation
# =============================================================================

evaluate: $(VENV_READY) analyze
	@echo "Running programmatic evaluation (~28 checks)..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-json: $(VENV_READY)
	@$(PYTHON_VENV) scripts/evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth \
		--json

evaluate-quick: $(VENV_READY)
	@echo "Running quick evaluation (no performance checks)..."
	@$(PYTHON_VENV) scripts/evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth \
		--quick

evaluate-llm: $(VENV_READY) analyze
	@echo "Running LLM evaluation (4 judges)..."
	@$(PYTHON_VENV) scripts/llm_evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model opus
	@mkdir -p evaluation/results
	@cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

evaluate-llm-focused: $(VENV_READY)
	@echo "Running focused LLM evaluation (detection accuracy only)..."
	@$(PYTHON_VENV) scripts/llm_evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(OUTPUT_DIR)/llm_evaluation_focused.json \
		--model opus \
		--skip-judge security_coverage \
		--skip-judge false_positive_rate \
		--skip-judge actionability

evaluate-combined: $(VENV_READY) analyze evaluate
	@echo "Running combined programmatic + LLM evaluation..."
	@$(PYTHON_VENV) scripts/llm_evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(OUTPUT_DIR)/combined_evaluation.json \
		--model opus \
		--programmatic-score 0.857
	@echo ""
	@echo "Combined results saved to $(OUTPUT_DIR)/combined_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-quick: _common-test-quick

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean
	@rm -rf evaluation/llm/results/*
	@rm -f evaluation/scorecard.md
	@rm -rf $(SYNTHETIC_DIR)/bin $(SYNTHETIC_DIR)/obj

clean-all: _common-clean-all
	@rm -rf $(SYNTHETIC_DIR)/bin $(SYNTHETIC_DIR)/obj
