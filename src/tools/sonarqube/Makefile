# SonarQube Analysis Tool
# Runs SonarQube analysis using Docker and extracts comprehensive metrics
#
# Quick start:
#   make setup        - Install dependencies and pull Docker images
#   make analyze      - Run analysis with default eval repo
#   make evaluate     - Run programmatic evaluation
#   make test         - Run all tests

.PHONY: all setup docker-pull docker-up docker-down docker-down-volumes docker-status \
        analyze analyze-skip-scan analyze-keep \
        analyze-csharp-clean analyze-csharp-complex analyze-java-security \
        analyze-typescript-duplication analyze-python-mixed analyze-all-evals \
        evaluate evaluate-json evaluate-quick evaluate-llm evaluate-combined evaluate-full \
        test test-quick test-integration test-all test-cov \
        clean clean-all clean-docker validate-output lint format help

# Include shared configuration (provides VENV, RUN_ID, REPO_ID, OUTPUT_DIR, etc.)
include ../Makefile.common

# Tool-specific configuration
EVAL_REPOS := eval-repos/synthetic
GROUND_TRUTH := evaluation/ground-truth

# Docker images (pinned versions)
SONARQUBE_IMAGE := sonarqube:10.7.0-community
SCANNER_IMAGE := sonarsource/sonar-scanner-cli:5.0.1

# SonarQube settings
SONARQUBE_URL ?= http://localhost:9000
SONAR_TOKEN ?=

# Tool-specific defaults
REPO_PATH ?= eval-repos/synthetic/csharp-clean
REPO_NAME ?= csharp-clean
COMMIT ?= $(shell git -C $(REPO_PATH) rev-parse HEAD 2>/dev/null || echo "")

# =============================================================================
# Primary Targets
# =============================================================================

help:
	@echo "SonarQube Analysis Tool"
	@echo ""
	@echo "Quick start:"
	@echo "  make setup        - Install dependencies and pull Docker images"
	@echo "  make analyze      - Run analysis with dashboard"
	@echo "  make evaluate     - Run programmatic evaluation"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "Analysis targets:"
	@echo "  make analyze-csharp-clean        - Analyze csharp-clean eval repo"
	@echo "  make analyze-csharp-complex      - Analyze csharp-complex eval repo"
	@echo "  make analyze-java-security       - Analyze java-security eval repo"
	@echo "  make analyze-typescript-duplication - Analyze typescript-duplication"
	@echo "  make analyze-all-evals           - Analyze all eval repos"
	@echo ""
	@echo "Evaluation targets:"
	@echo "  make evaluate       - Full evaluation with verbose output"
	@echo "  make evaluate-json  - Output evaluation as JSON only"
	@echo "  make evaluate-quick - Quick evaluation without performance checks"
	@echo ""
	@echo "LLM Evaluation targets:"
	@echo "  make evaluate-llm      - Run LLM evaluation (3 judges)"
	@echo "  make evaluate-combined - Combined programmatic + LLM evaluation"
	@echo ""
	@echo "Docker targets:"
	@echo "  make docker-up      - Start SonarQube container"
	@echo "  make docker-down    - Stop SonarQube container"
	@echo "  make docker-status  - Check container status"
	@echo ""
	@echo "Variables:"
	@echo "  REPO_PATH=<path>    - Repository to analyze"
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

all: setup analyze evaluate
	@echo ""
	@echo "Full pipeline complete! Check:"
	@echo "  - $(OUTPUT_DIR)/output.json"
	@echo "  - $(EVAL_OUTPUT_DIR)/"

# =============================================================================
# Setup
# =============================================================================

setup: $(VENV_READY) docker-pull
	@echo "Setup complete!"

docker-pull:
	@echo "Pulling Docker images..."
	@docker pull $(SONARQUBE_IMAGE) || true
	@docker pull $(SCANNER_IMAGE) || true

# =============================================================================
# Docker Lifecycle
# =============================================================================

docker-up: $(VENV_READY)
	docker-compose up -d
	@echo "Waiting for SonarQube to become healthy..."
	@$(PYTHON_VENV) -c "from scripts.docker_lifecycle import wait_for_healthy; wait_for_healthy()"
	@echo "SonarQube is ready at $(SONARQUBE_URL)"

docker-down:
	docker-compose down

docker-down-volumes:
	docker-compose down -v

docker-status: $(VENV_READY)
	@$(PYTHON_VENV) -c "from scripts.docker_lifecycle import is_container_running; print('Running' if is_container_running() else 'Not running')"

# =============================================================================
# Analysis
# =============================================================================

# Run analysis with envelope output format
analyze: $(VENV_READY)
	@mkdir -p $(OUTPUT_DIR)
	@echo "Analyzing $(REPO_NAME)..."
	$(PYTHON_VENV) -m scripts.analyze $(REPO_PATH) \
		--project-key $(REPO_NAME) \
		--output $(OUTPUT_DIR)/output.json \
		--sonarqube-url $(SONARQUBE_URL) \
		--run-id "$(RUN_ID)" \
		--repo-id "$(REPO_ID)" \
		--branch "$(BRANCH)" \
		$(if $(COMMIT),--commit "$(COMMIT)",) \
		$(if $(SONAR_TOKEN),--token $(SONAR_TOKEN),) \
		$(if $(NATIVE_SCANNER),--native-scanner,) \
		$(if $(KEEP_CONTAINER),--keep-container,)

analyze-skip-scan: $(VENV_READY)
	@mkdir -p $(OUTPUT_DIR)
	$(PYTHON_VENV) -m scripts.analyze $(REPO_PATH) \
		--project-key $(REPO_NAME) \
		--output $(OUTPUT_DIR)/output.json \
		--sonarqube-url $(SONARQUBE_URL) \
		--run-id "$(RUN_ID)" \
		--repo-id "$(REPO_ID)" \
		--branch "$(BRANCH)" \
		$(if $(SONAR_TOKEN),--token $(SONAR_TOKEN),) \
		--skip-scan \
		--keep-container

analyze-keep: KEEP_CONTAINER=1
analyze-keep: analyze

# Analysis shortcuts for eval repos
analyze-csharp-clean:
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/csharp-clean REPO_NAME=csharp-clean

analyze-csharp-complex:
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/csharp-complex REPO_NAME=csharp-complex

analyze-java-security:
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/java-security REPO_NAME=java-security

analyze-typescript-duplication:
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/typescript-duplication REPO_NAME=typescript-duplication

analyze-python-mixed:
	$(MAKE) analyze REPO_PATH=eval-repos/synthetic/python-mixed REPO_NAME=python-mixed

analyze-all-evals: analyze-csharp-clean analyze-csharp-complex analyze-java-security analyze-typescript-duplication

# =============================================================================
# Evaluation
# =============================================================================

# Run programmatic evaluation
evaluate: $(VENV_READY)
	@echo "Running programmatic evaluation..."
	@mkdir -p $(EVAL_OUTPUT_DIR)
	EVAL_OUTPUT_DIR=$(EVAL_OUTPUT_DIR) $(PYTHON_VENV) -m scripts.evaluate \
		--analysis $(OUTPUT_DIR)/output.json \
		--ground-truth $(GROUND_TRUTH) \
		--output $(EVAL_OUTPUT_DIR)/evaluation_report.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/evaluation_report.json"

evaluate-json: $(VENV_READY)
	@$(PYTHON_VENV) -m scripts.evaluate \
		--analysis $(OUTPUT_DIR)/output.json \
		--ground-truth $(GROUND_TRUTH) \
		--json

evaluate-quick: $(VENV_READY)
	@echo "Running quick evaluation (no performance checks)..."
	@$(PYTHON_VENV) -m scripts.evaluate \
		--analysis $(OUTPUT_DIR)/output.json \
		--ground-truth $(GROUND_TRUTH) \
		--quick

# Run LLM evaluation (3 judges)
evaluate-llm: $(VENV_READY)
	@echo "Running LLM evaluation (3 judges)..."
	$(PYTHON_VENV) -m scripts.llm_evaluate \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/llm_evaluation.json \
		--model $(LLM_MODEL)
	@mkdir -p evaluation/results
	@cp $(EVAL_OUTPUT_DIR)/llm_evaluation.json evaluation/results/llm_evaluation.json
	@echo ""
	@echo "Results saved to $(EVAL_OUTPUT_DIR)/llm_evaluation.json"

evaluate-combined: $(VENV_READY) analyze evaluate
	@echo "Running combined programmatic + LLM evaluation..."
	@$(PYTHON_VENV) -m scripts.llm_evaluate \
		--analysis $(OUTPUT_DIR)/output.json \
		--output $(EVAL_OUTPUT_DIR)/combined_evaluation.json \
		--model $(LLM_MODEL) \
		--programmatic-score 0.75
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

test: $(VENV_READY)
	@echo "Running unit tests..."
	@$(PYTHON_VENV) -m pytest tests/ -m "not integration" -v --tb=short
	@echo "All unit tests complete!"

test-quick: $(VENV_READY)
	@echo "Running quick tests..."
	@$(PYTHON_VENV) -m pytest tests/ -v --tb=short -x -m "not integration"
	@echo "Quick tests complete!"

test-integration: $(VENV_READY)
	@echo "Running integration tests (requires Docker)..."
	@$(PYTHON_VENV) -m pytest tests/ -m "integration" -v --tb=long

test-all: $(VENV_READY)
	@echo "Running all tests..."
	@$(PYTHON_VENV) -m pytest tests/ -v
	@echo "All tests complete!"

test-cov: $(VENV_READY)
	$(PYTHON_VENV) -m pytest tests/ -m "not integration" --cov=scripts --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

# =============================================================================
# Cleanup
# =============================================================================

clean: _common-clean
	@rm -rf evaluation/llm/results/*
	@rm -f evaluation/scorecard.json evaluation/scorecard.md
	@rm -rf .ruff_cache

clean-all: _common-clean-all docker-down-volumes
	@echo "Cleaned all artifacts and Docker volumes"

clean-docker: docker-down-volumes
	docker image prune -f
	@echo "Docker cleanup complete"

# =============================================================================
# Utility
# =============================================================================

validate-output: $(VENV_READY)
	$(PYTHON_VENV) -c "import json, jsonschema; \
		data = json.load(open('$(OUTPUT_DIR)/output.json')); \
		schema = json.load(open('schemas/output.schema.json')); \
		jsonschema.validate(data, schema); \
		print('Validation passed')"

lint: $(VENV_READY)
	$(PYTHON_VENV) -m ruff check scripts/
	$(PYTHON_VENV) -m ruff format --check scripts/

format: $(VENV_READY)
	$(PYTHON_VENV) -m ruff format scripts/
