# Trivy Vulnerability Scanner Makefile
# Standard interface for Project Caldera tools

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup install-trivy analyze analyze-vulnerable-npm analyze-iac-terraform analyze-all-evals \
        evaluate evaluate-llm evaluate-single validate-output \
        test test-unit test-integration clean clean-all

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic/vulnerable-npm
REPO_NAME ?= vulnerable-npm
# OUTPUT_DIR inherited from Makefile.common: outputs/$(RUN_ID)
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

# Trivy settings
TRIVY_VERSION ?= 0.58.0
TRIVY_TIMEOUT ?= 600
TRIVY_INSTALL_URL := https://raw.githubusercontent.com/aquasecurity/trivy/v$(TRIVY_VERSION)/contrib/install.sh
TRIVY_INSTALL_SH_SHA256 := 2304dcc0c1883e802d376eae1b514c923b7427a7d88091dfcaf83967e6f55a7c

help:  ## Show this help message
	@echo "Trivy Vulnerability Scanner"
	@echo ""
	@echo "Usage: make <target> [REPO_PATH=<path>] [REPO_NAME=<name>]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ============================================
# Setup targets
# ============================================

setup: $(VENV_READY) install-trivy  ## Set up virtual environment and install trivy
	@echo "Setup complete"

install-trivy:  ## Install trivy binary
	@if ! command -v trivy &> /dev/null; then \
		echo "Installing trivy..."; \
		if [ "$$(uname)" = "Darwin" ]; then \
			brew install trivy || { \
				curl -sfL $(TRIVY_INSTALL_URL) -o /tmp/trivy-install.sh && \
				echo "$(TRIVY_INSTALL_SH_SHA256)  /tmp/trivy-install.sh" | $(SHA256_CMD) -c - || \
					{ echo "ERROR: checksum mismatch for trivy install script"; rm -f /tmp/trivy-install.sh; exit 1; }; \
				sh /tmp/trivy-install.sh -b /usr/local/bin v$(TRIVY_VERSION) && \
				rm -f /tmp/trivy-install.sh; \
			}; \
		else \
			curl -sfL $(TRIVY_INSTALL_URL) -o /tmp/trivy-install.sh && \
			echo "$(TRIVY_INSTALL_SH_SHA256)  /tmp/trivy-install.sh" | $(SHA256_CMD) -c - || \
				{ echo "ERROR: checksum mismatch for trivy install script"; rm -f /tmp/trivy-install.sh; exit 1; }; \
			sh /tmp/trivy-install.sh -b /usr/local/bin v$(TRIVY_VERSION) && \
			rm -f /tmp/trivy-install.sh; \
		fi \
	else \
		echo "trivy already installed: $$(trivy --version | head -1)"; \
	fi

# ============================================
# Analysis targets
# ============================================

analyze: $(VENV_READY)  ## Run trivy analysis on a repository
	@mkdir -p $(OUTPUT_DIR)
	@echo "Analyzing $(REPO_PATH) as project '$(REPO_NAME)'"
	$(PYTHON_VENV) -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT) \
		--timeout $(TRIVY_TIMEOUT)

# Analysis shortcuts for eval repos
analyze-vulnerable-npm:  ## Analyze vulnerable-npm eval repo
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/vulnerable-npm REPO_NAME=vulnerable-npm

analyze-iac-terraform:  ## Analyze iac-terraform eval repo
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/iac-terraform REPO_NAME=iac-terraform

analyze-all-evals: analyze-vulnerable-npm analyze-iac-terraform  ## Analyze all eval repos

# ============================================
# Evaluation targets
# ============================================

evaluate: $(VENV_READY)  ## Run evaluation on analysis outputs
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) scripts/evaluate.py --output $(EVAL_OUTPUT_DIR)/

evaluate-llm: $(VENV_READY)  ## Run LLM evaluation on analysis outputs
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@mkdir -p evaluation/results
	$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--programmatic-results evaluation/results/evaluation_report.json
	@if [ "$(EVAL_OUTPUT_DIR)" != "evaluation/results" ] && [ -w evaluation/results ]; then cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json; fi

evaluate-single: $(VENV_READY)  ## Evaluate a single analysis output
	$(PYTHON_VENV) scripts/evaluate.py \
		--input $(OUTPUT_DIR)/output.json \
		--ground-truth evaluation/ground-truth/$(REPO_NAME).json \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json

# ============================================
# Validation targets
# ============================================

validate-output: $(VENV_READY)  ## Validate output JSON against schema
	$(PYTHON_VENV) -c "import json, jsonschema; \
		data = json.load(open('$(OUTPUT_DIR)/output.json')); \
		schema = json.load(open('schemas/output.schema.json')); \
		jsonschema.validate(data, schema); \
		print('Validation passed')"

# ============================================
# Test targets
# ============================================

test: _common-test  ## Run all tests

test-unit: $(VENV_READY)  ## Run unit tests only
	$(PYTHON_VENV) -m pytest tests/unit/ -v

test-integration: $(VENV_READY)  ## Run integration tests only
	$(PYTHON_VENV) -m pytest tests/integration/ -v

# ============================================
# Cleanup targets
# ============================================

clean: _common-clean  ## Clean build artifacts
	@rm -rf evaluation/llm/results/*
	@rm -rf .ruff_cache
	@find . -name "*.pyc" -delete

clean-all: _common-clean-all  ## Clean all including venv
	@rm -rf evaluation/llm/results/*
