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

.PHONY: all setup analyze analyze-synthetic evaluate evaluate-llm test test-quick clean clean-all help

# =============================================================================
# Configuration
# =============================================================================

VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
GIT_SIZER := bin/git-sizer

# Required Caldera variables
REPO_PATH ?= eval-repos/synthetic/healthy
REPO_NAME ?= healthy
OUTPUT_DIR ?= output/$(RUN_ID)
RUN_ID ?= $(shell python3 -c "import uuid; print(str(uuid.uuid4()))")
REPO_ID ?= $(shell python3 -c "import uuid; print(str(uuid.uuid4()))")
BRANCH ?= main
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000")

# Evaluation directories
EVAL_OUTPUT_DIR ?= evaluation/results
GROUND_TRUTH_DIR ?= evaluation/ground-truth
LLM_MODEL ?= sonnet

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
	@echo "  - output/"
	@echo "  - evaluation/results/"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV)/bin/activate $(GIT_SIZER) init-synthetic-repos
	@echo "Setup complete!"

$(VENV)/bin/activate: requirements.txt
	@echo "Creating Python virtual environment..."
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip -q
	@$(PIP) install -r requirements.txt -q
	@touch $(VENV)/bin/activate

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

analyze: $(VENV)/bin/activate $(GIT_SIZER)
	@echo "Running repository analysis..."
	@echo "  REPO_PATH: $(REPO_PATH)"
	@echo "  RUN_ID:    $(RUN_ID)"
	@echo "  REPO_ID:   $(REPO_ID)"
	@echo "  BRANCH:    $(BRANCH)"
	@echo "  COMMIT:    $(COMMIT)"
	@mkdir -p $(OUTPUT_DIR)
	@$(PYTHON) -m scripts.analyze \
		--repo-path $(REPO_PATH) \
		--repo-name $(REPO_NAME) \
		--output-dir $(OUTPUT_DIR) \
		--run-id $(RUN_ID) \
		--repo-id $(REPO_ID) \
		--branch $(BRANCH) \
		--commit $(COMMIT) \
		--exit-zero

# Analyze all synthetic repos
analyze-synthetic: $(VENV)/bin/activate $(GIT_SIZER)
	@echo "Analyzing all synthetic repositories..."
	@mkdir -p evaluation/results
	@for repo in eval-repos/synthetic/*/; do \
		if [ -d "$$repo/.git" ]; then \
			name=$$(basename $$repo); \
			rid=$$(python3 -c "import uuid; print(str(uuid.uuid4()))"); \
			repoid=$$(python3 -c "import uuid; print(str(uuid.uuid4()))"); \
			commit=$$(git -C $$repo rev-parse HEAD 2>/dev/null || echo "0000000000000000000000000000000000000000"); \
			echo "  Analyzing $$name..."; \
			$(PYTHON) -m scripts.analyze \
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

evaluate: $(VENV)/bin/activate
	@echo "Running programmatic evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	@$(PYTHON) -m scripts.evaluate \
		--results-dir $(OUTPUT_DIR) \
		--ground-truth-dir $(GROUND_TRUTH_DIR) \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-llm: $(VENV)/bin/activate
	@echo "Running LLM evaluation..."
	@mkdir -p evaluation/llm/results
	@$(PYTHON) -m evaluation.llm.orchestrator \
		evaluation/results/healthy \
		--output evaluation/llm/results/llm_evaluation.json \
		--model $(LLM_MODEL)
	@mkdir -p evaluation/results
	@cp evaluation/llm/results/llm_evaluation.json evaluation/results/llm_evaluation.json
	@echo ""
	@echo "Results saved to evaluation/llm/results/llm_evaluation.json"

# =============================================================================
# Testing
# =============================================================================

test: $(VENV)/bin/activate
	@echo "Running all tests..."
	@$(PYTHON) -m pytest tests/ -v --tb=short
	@echo "All tests complete!"

test-quick: $(VENV)/bin/activate
	@echo "Running quick tests..."
	@$(PYTHON) -m pytest tests/ -v --tb=short -x
	@echo "Quick tests complete!"

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning generated files..."
	@rm -rf output/
	@rm -rf evaluation/results/
	@rm -rf .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

clean-all: clean
	@echo "Removing venv and binary..."
	@rm -rf $(VENV)
	@rm -rf bin/
	@echo "Full clean complete!"
