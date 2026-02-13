# PMD CPD (Copy/Paste Detector) Tool
# Token-based code duplication detection with semantic comparison
#
# Quick start:
#   make setup    - Download PMD 7.0.0, create venv, install requirements
#   make analyze  - Run CPD analysis on target repository
#   make evaluate - Run programmatic evaluation (28 checks)
#   make test     - Run all tests

.PHONY: all setup analyze analyze-semantic evaluate evaluate-json evaluate-quick evaluate-llm evaluate-combined test test-quick clean clean-all help

# Include shared configuration
include ../Makefile.common

# =============================================================================
# Tool-specific configuration
# =============================================================================

PMD_VERSION := 7.0.0
PMD_HOME := $(CURDIR)/.pmd
PMD := $(PMD_HOME)/pmd-bin-$(PMD_VERSION)/bin/pmd

# Repository path (can be overridden by orchestrator)
REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= $(shell basename $(REPO_PATH))

# Compute COMMIT from REPO_PATH if not provided
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "PMD CPD (Copy/Paste Detector) Tool"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Download PMD 7.0.0 and install Python dependencies"
	@echo "  make analyze      - Run duplication analysis"
	@echo "  make evaluate     - Run programmatic evaluation (~28 checks)"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Analysis targets:"
	@echo "  make analyze          - Standard token-based detection"
	@echo "  make analyze-semantic - Semantic mode (--ignore-identifiers --ignore-literals)"
	@echo ""
	@echo "Evaluation targets:"
	@echo "  make evaluate       - Full evaluation with verbose output"
	@echo "  make evaluate-json  - Output evaluation as JSON only"
	@echo "  make evaluate-quick - Quick evaluation without performance checks"
	@echo ""
	@echo "LLM Evaluation targets:"
	@echo "  make evaluate-llm      - Run LLM evaluation (4 judges)"
	@echo "  make evaluate-combined - Combined programmatic + LLM evaluation"
	@echo ""
	@echo "Additional targets:"
	@echo "  make test-quick   - Run fast tests only"
	@echo "  make clean        - Remove generated files"
	@echo "  make all          - Full pipeline (setup + analyze + evaluate)"

all: setup analyze evaluate
	@echo ""
	@echo "PMD CPD analysis complete! Check:"
	@echo "  - $(OUTPUT_DIR)/output.json"
	@echo "  - evaluation/results/evaluation_report.json"

# =============================================================================
# Setup
# =============================================================================

setup: check-java $(VENV_READY) $(PMD)
	@echo "Setup complete! PMD CPD $(PMD_VERSION) is ready."

# Detect Java - check standard path first, then Homebrew locations
JAVA_CMD := $(shell which java 2>/dev/null || echo "")
JAVA_VERSION_OK := $(shell java -version 2>&1 | grep -q "version" && echo "ok" || echo "")
JAVA_OK := $(shell [ -n "$(JAVA_CMD)" ] && $(JAVA_CMD) -version >/dev/null 2>&1 && echo "ok" || echo "")
ifneq ($(JAVA_OK),ok)
  # Prefer Homebrew OpenJDK if system Java is missing or broken
  ifneq ($(wildcard /opt/homebrew/opt/openjdk@17/bin/java),)
    JAVA_CMD := /opt/homebrew/opt/openjdk@17/bin/java
    export PATH := /opt/homebrew/opt/openjdk@17/bin:$(PATH)
  else ifneq ($(wildcard /usr/local/opt/openjdk@17/bin/java),)
    JAVA_CMD := /usr/local/opt/openjdk@17/bin/java
    export PATH := /usr/local/opt/openjdk@17/bin:$(PATH)
  else ifneq ($(wildcard /opt/homebrew/opt/openjdk/bin/java),)
    JAVA_CMD := /opt/homebrew/opt/openjdk/bin/java
    export PATH := /opt/homebrew/opt/openjdk/bin:$(PATH)
  else ifneq ($(wildcard /usr/local/opt/openjdk/bin/java),)
    JAVA_CMD := /usr/local/opt/openjdk/bin/java
    export PATH := /usr/local/opt/openjdk/bin:$(PATH)
  endif
endif

check-java:
ifeq ($(JAVA_CMD),)
	@echo "Error: Java is required for PMD CPD. Please install Java 11+ first:"
	@echo "  brew install openjdk@17"
	@echo "  # or: brew install temurin"
	@exit 1
else
	@$(JAVA_CMD) -version > /dev/null 2>&1 || (echo "Error: Java found at $(JAVA_CMD) but not working." && exit 1)
	@echo "Java found: $(JAVA_CMD)"
endif

$(PMD):
	@echo "Downloading PMD $(PMD_VERSION)..."
	@mkdir -p $(PMD_HOME)
	@curl -sL "https://github.com/pmd/pmd/releases/download/pmd_releases%2F$(PMD_VERSION)/pmd-dist-$(PMD_VERSION)-bin.zip" -o /tmp/pmd-$(PMD_VERSION).zip
	@unzip -q /tmp/pmd-$(PMD_VERSION).zip -d $(PMD_HOME)
	@rm /tmp/pmd-$(PMD_VERSION).zip
	@chmod +x $(PMD)
	@echo "PMD $(PMD_VERSION) installed to $(PMD_HOME)"

# =============================================================================
# Analysis
# =============================================================================

analyze: check-java $(VENV_READY) $(PMD)
	@echo "Running CPD analysis on $(REPO_NAME)..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/analyze.py $(REPO_PATH) \
		--output-dir $(OUTPUT_DIR) \
		--pmd-home $(PMD_HOME)/pmd-bin-$(PMD_VERSION) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT)

analyze-semantic: check-java $(VENV_READY) $(PMD)
	@echo "Running semantic CPD analysis on $(REPO_NAME)..."
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/analyze.py $(REPO_PATH) \
		--output-dir $(OUTPUT_DIR) \
		--pmd-home $(PMD_HOME)/pmd-bin-$(PMD_VERSION) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT) \
		--ignore-identifiers \
		--ignore-literals

# =============================================================================
# Evaluation
# =============================================================================

# Synthetic test run output (stable path for compliance checking)
SYNTHETIC_OUTPUT ?= outputs/cpd-test-run/output.json

evaluate: $(VENV_READY)
	@echo "Running programmatic evaluation (~28 checks)..."
	@if [ ! -f "$(SYNTHETIC_OUTPUT)" ]; then \
		echo "Synthetic output not found at $(SYNTHETIC_OUTPUT)"; \
		echo "Running analysis on synthetic repo first..."; \
		$(MAKE) analyze REPO_PATH=eval-repos/synthetic RUN_ID=cpd-test-run; \
	fi
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/evaluate.py \
		--analysis $(SYNTHETIC_OUTPUT) \
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
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/llm_evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model $(LLM_MODEL) \
		--programmatic-results evaluation/results/evaluation_report.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

evaluate-combined: $(VENV_READY) analyze evaluate
	@echo "Running combined programmatic + LLM evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON_VENV) scripts/llm_evaluate.py \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/combined_evaluation.json \
		--model $(LLM_MODEL) \
		--programmatic-results evaluation/results/evaluation_report.json
	@echo ""
	@echo "Combined results saved to $(EVAL_OUTPUT_DIR)/combined_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: _common-test

test-quick: _common-test-quick

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean

clean-all: _common-clean-all
	@echo "Removing PMD installation..."
	@rm -rf $(PMD_HOME)
	@echo "Full clean complete!"

# =============================================================================
# Ground Truth Seeding
# =============================================================================

seed-ground-truth: _common-seed-ground-truth
