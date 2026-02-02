# E2E Pipeline Verification Guide

This document describes how to verify the Insights E2E Pipeline with LLM Report Evaluation.

## Overview

The E2E pipeline consists of 4 phases:
1. **Collection**: Run analysis tools against a repository
2. **Report Generation**: Generate insights report from collected data
3. **LLM Evaluation**: Evaluate report quality using InsightQualityJudge
4. **Insight Extraction**: Extract top 3 insights with improvement proposals

## Files Involved

| File | Purpose |
|------|---------|
| `evaluation/llm/judges/insight_quality.py` | LLM judge for insight quality scoring |
| `evaluation/llm/judges/__init__.py` | Judge exports |
| `evaluation/llm/orchestrator.py` | Evaluation orchestration |
| `scripts/evaluate.py` | CLI evaluation script |
| `scripts/extract_top_insights.py` | Top insights extraction |
| `Makefile` | Build targets for pipeline |

## Verification Steps

### Step 1: Verify Python Syntax

```bash
cd /path/to/Project-Caldera

python3 -m py_compile src/insights/evaluation/llm/judges/insight_quality.py
python3 -m py_compile src/insights/scripts/extract_top_insights.py
python3 -m py_compile src/insights/evaluation/llm/orchestrator.py
python3 -m py_compile src/insights/scripts/evaluate.py
```

**Expected**: No output (all files compile successfully)

### Step 2: Verify Imports

```bash
cd /path/to/Project-Caldera

.venv/bin/python3 -c "
from src.insights.evaluation.llm.judges import InsightQualityJudge, InsightQualityResult
print('InsightQualityJudge imported successfully')
print(f'  name: {InsightQualityJudge.name}')
print(f'  weight: {InsightQualityJudge.weight}')
print(f'  sub_dimensions: {InsightQualityJudge.sub_dimensions}')
"
```

**Expected Output**:
```
InsightQualityJudge imported successfully
  name: insight_quality
  weight: 0.5
  sub_dimensions: {'evidence_grounding': 0.3, 'prioritization_quality': 0.25, 'actionability': 0.25, 'completeness': 0.2}
```

### Step 3: Run Unit Tests

```bash
cd src/insights
.venv/bin/pytest tests/ -v --tb=short
```

**Expected**: All 86 tests pass

### Step 4: Full E2E Test with Real Repository

This step runs the complete pipeline against a real C# repository (bloxstrap).

#### Prerequisites
- Docker running (for SonarQube)
- Network access to GitHub

#### 4a. Start SonarQube

```bash
cd src/tools/sonarqube
docker-compose up -d

# Wait for SonarQube to be ready (can take 1-2 minutes)
until curl -s http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do
    echo "Waiting for SonarQube..."
    sleep 5
done
echo "SonarQube is ready"
```

#### 4b. Clone Test Repository

```bash
cd /tmp
git clone --depth 1 https://github.com/bloxstraplabs/bloxstrap.git
```

#### 4c. Run Full Pipeline

```bash
cd /path/to/Project-Caldera
make pipeline-eval ORCH_REPO_PATH=/tmp/bloxstrap ORCH_DB_PATH=/tmp/bloxstrap_test.duckdb
```

#### 4d. Verify Outputs

Check that all phases completed:

```bash
# Check database was created
ls -la /tmp/bloxstrap_test.duckdb

# Check insights report was generated
ls -la src/insights/output/

# Check LLM evaluation results
cat src/insights/output/evaluation_results.json | jq '.insight_quality'

# Check top insights extraction
cat src/insights/output/top_insights.json | jq '.insights | length'
```

**Expected**:
- Database file exists (~50MB+)
- Report file exists in output/
- `insight_quality` score present in evaluation results
- Top insights JSON contains 3 insights

### Step 5: Run Without SonarQube (Optional)

If Docker is unavailable, run the pipeline without SonarQube:

```bash
make pipeline-eval \
    ORCH_REPO_PATH=/tmp/bloxstrap \
    ORCH_DB_PATH=/tmp/bloxstrap_test.duckdb \
    ORCH_SKIP_SONAR=1
```

This runs 6 tools instead of 7 (layout, scc, lizard, semgrep, trivy, gitleaks).

## Success Criteria

| Criterion | Status |
|-----------|--------|
| All Python files compile without syntax errors | |
| InsightQualityJudge imports with correct attributes | |
| All 86 unit tests pass | |
| Full E2E pipeline completes on bloxstrap repository | |
| LLM evaluation produces insight_quality score | |
| Top 3 insights extracted with improvement proposals | |

## Troubleshooting

### Docker Connection Issues

If you see `Cannot connect to the Docker daemon`:
```bash
# macOS: Start Docker Desktop application
open -a Docker

# Wait for Docker to start
until docker info &>/dev/null; do sleep 1; done
```

### SonarQube Timeout

If SonarQube takes too long to start:
```bash
# Check container logs
docker logs sonarqube-sonarqube-1

# Restart container
cd src/tools/sonarqube && docker-compose restart
```

### Import Errors

If imports fail, ensure you're using the correct Python environment:
```bash
# Create/activate virtual environment
cd src/insights
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Verification Results

Last verified: ____________

| Step | Result | Notes |
|------|--------|-------|
| 1. Syntax verification | | |
| 2. Import verification | | |
| 3. Unit tests | | |
| 4. E2E pipeline | | |
