# gitleaks - Secret Detection Tool
# Caldera-compliant Makefile
#
# Quick start:
#   make setup        - Install gitleaks and Python dependencies
#   make analyze      - Run analysis
#   make evaluate     - Run programmatic evaluation
#   make evaluate-llm - Run LLM evaluation
#   make test         - Run all tests
#   make clean        - Remove generated files

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup analyze evaluate evaluate-llm test test-quick clean clean-all build-repos

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific variables
GITLEAKS_VERSION := 8.18.4

# Platform detection for binary download
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Darwin)
    ifeq ($(UNAME_M),arm64)
        GITLEAKS_PLATFORM := darwin_arm64
    else
        GITLEAKS_PLATFORM := darwin_x64
    endif
else
    ifeq ($(UNAME_M),x86_64)
        GITLEAKS_PLATFORM := linux_x64
    else ifeq ($(UNAME_M),aarch64)
        GITLEAKS_PLATFORM := linux_arm64
    else
        GITLEAKS_PLATFORM := linux_x32
    endif
endif

GITLEAKS_URL := https://github.com/gitleaks/gitleaks/releases/download/v$(GITLEAKS_VERSION)/gitleaks_$(GITLEAKS_VERSION)_$(GITLEAKS_PLATFORM).tar.gz

REPO_PATH ?= eval-repos/synthetic
REPO_NAME ?= synthetic
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

help:  ## Show this help message
	@echo "gitleaks - Secret Detection Tool"
	@echo ""
	@echo "Usage: make <target> [REPO_PATH=<path>] [REPO_NAME=<name>]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ============================================
# Setup targets
# ============================================

setup: setup-gitleaks $(VENV_READY)  ## Set up gitleaks and virtual environment
	@echo "Setup complete"

# SHA256 checksums per platform (gitleaks v8.18.4)
GITLEAKS_SHA256_darwin_arm64 := a480d8593acd8215b22402cf0f3f88b01dcd3610c63b5391db640f7767e62104
GITLEAKS_SHA256_darwin_x64   := 1a69e5666b13cd374889cbcb1939ed1573b63b551251283d5d2329a53cf58e2f
GITLEAKS_SHA256_linux_x64    := ba6dbb656933921c775ee5a2d1c13a91046e7952e9d919f9bac4cec61d628e7d
GITLEAKS_SHA256_linux_arm64  := bf5f7f466ebfade1296c8bd32cf7d3f592c2aa78836aa9980ffbe2cadca7a861

setup-gitleaks:
	@echo "Installing gitleaks $(GITLEAKS_VERSION)..."
	@mkdir -p bin
	@EXPECTED="$(GITLEAKS_SHA256_$(GITLEAKS_PLATFORM))"; \
	curl -sL $(GITLEAKS_URL) -o /tmp/gitleaks.tar.gz; \
	if [ -n "$$EXPECTED" ]; then \
		echo "$$EXPECTED  /tmp/gitleaks.tar.gz" | $(SHA256_CMD) -c - || { echo "ERROR: checksum mismatch"; rm -f /tmp/gitleaks.tar.gz; exit 1; }; \
	else \
		echo "WARNING: no checksum configured for $(GITLEAKS_PLATFORM), skipping verification"; \
	fi; \
	tar -xz -C bin gitleaks < /tmp/gitleaks.tar.gz; \
	rm -f /tmp/gitleaks.tar.gz
	@chmod +x bin/gitleaks
	@echo "gitleaks installed at bin/gitleaks"
	@bin/gitleaks version

build-repos:  ## Create synthetic test repositories
	@echo "Building synthetic test repositories..."
	@$(PYTHON_VENV) scripts/create_synthetic_repos.py
	@echo "Synthetic repos created in eval-repos/synthetic/"

# ============================================
# Analysis targets
# ============================================

analyze: $(VENV_READY)  ## Run secret analysis on a repository
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

# ============================================
# Evaluation targets
# ============================================

evaluate: $(VENV_READY)  ## Run programmatic evaluation
	@mkdir -p $(EVAL_OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.evaluate \
		--analysis-dir outputs/runs \
		--ground-truth-dir evaluation/ground-truth \
		--output $(EVAL_OUTPUT_DIR)
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-llm: $(VENV_READY)  ## Run LLM evaluation
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@mkdir -p evaluation/results
	$(PYTHON_VENV) -m evaluation.llm.orchestrator \
		--working-dir . \
		--programmatic-results evaluation/results/evaluation_report.json \
		--model $(LLM_MODEL) \
		--evaluation-mode synthetic
	@echo "LLM evaluation complete"

# ============================================
# Test targets
# ============================================

test: _common-test  ## Run all tests

test-quick: _common-test-quick  ## Run quick tests (stop on first failure)

# ============================================
# Cleanup targets
# ============================================

clean: _common-clean  ## Clean build artifacts
	@rm -rf eval-repos/synthetic/*/

clean-all: _common-clean-all  ## Clean all including venv
	@rm -rf bin/gitleaks
