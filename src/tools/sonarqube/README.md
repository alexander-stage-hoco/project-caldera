# SonarQube Analysis Tool

Docker-based SonarQube Community Edition analysis tool with ephemeral container lifecycle.

## Overview

This tool:
1. Starts SonarQube Docker container on demand
2. Runs analysis via sonar-scanner
3. Extracts ALL metrics via REST APIs (paged, chunked, streaming)
4. Exports unified JSON matching the `1.2.0` schema
5. Stops container after completion (or on failure)
6. Integrates with collector and evaluation frameworks

**Supported Languages:** C#, Java, JavaScript, TypeScript

## Quick Start

```bash
# Setup (installs dependencies, pulls Docker images)
make setup

# Run analysis on a repository
make analyze REPO_PATH=/path/to/repo REPO_NAME=my-project

# Keep container running after analysis (for debugging)
make analyze-keep REPO_PATH=/path/to/repo REPO_NAME=my-project

# Extract data from existing SonarQube project (skip scanning)
make analyze-skip-scan REPO_NAME=my-project

# Run evaluation
make evaluate

# Validate output schema
make validate-output REPO_NAME=my-project
```

## Directory Structure

```
sonarqube/
├── Makefile                    # Standard orchestrator interface
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # SonarQube container definition
├── schemas/
│   └── sonar_export.schema.json   # JSON Schema v1.2
├── scripts/
│   ├── analyze.py              # Main orchestrator
│   ├── docker_lifecycle.py     # Container start/stop/health
│   ├── scanner.py              # sonar-scanner wrapper
│   ├── export.py               # Unified JSON export
│   ├── evaluate.py             # Evaluation orchestrator
│   ├── api/                    # API extraction modules
│   │   ├── client.py           # Base client (pagination, retry)
│   │   ├── module_a_task.py    # CE task polling
│   │   ├── module_b_components.py  # Component tree
│   │   ├── module_c_catalog.py # Metric catalog
│   │   ├── module_d_measures.py    # Measures (chunked)
│   │   ├── module_e_issues.py  # Issues (streaming)
│   │   ├── module_f_rules.py   # Rule metadata
│   │   ├── module_g_duplications.py  # Duplications
│   │   ├── module_h_quality_gate.py  # Quality gate
│   │   └── module_i_history.py # Analysis history
│   └── checks/                 # Evaluation checks
│       ├── accuracy.py         # SQ-AC-* checks
│       ├── coverage.py         # SQ-CV-* checks
│       └── completeness.py     # SQ-CM-* checks
├── evaluation/
│   ├── ground-truth/           # Expected results
│   └── results/                # Evaluation outputs (gitignored)
├── eval-repos/synthetic/       # Test repositories
├── output/runs/                # Analysis outputs (gitignored)
└── tests/                      # Unit tests
```

## Output Schema

The tool exports data in the `1.2.0` format:

```json
{
  "schema_version": "1.2.0",
  "generated_at": "2024-01-01T00:00:00Z",
  "repo_name": "my-project",
  "repo_path": "/path/to/my-project",
  "results": {
    "tool": "sonarqube",
    "tool_version": "10.5.0",
    "source": {
      "sonarqube_url": "http://localhost:9000",
      "project_key": "my-project",
      "analysis_id": "AX...",
      "revision": "abc123",
      "repo_name": "my-project",
      "repo_path": "/path/to/my-project"
    },
    "metric_catalog": [...],
    "components": {
      "root_key": "my-project",
      "by_key": {...},
      "children": {...}
    },
    "measures": {
      "by_component_key": {...}
    },
    "issues": {
      "items": [...],
      "rollups": {...}
    },
    "rules": { "by_key": {...} },
    "duplications": {...},
    "quality_gate": {...},
    "analyses": [...],
    "derived_insights": {
      "hotspots": [...],
      "directory_rollups": {...}
    },
    "limitations": {...}
  }
}
```

## API Modules

| Module | Endpoint | Description |
|--------|----------|-------------|
| A (Task) | `/api/ce/task` | Poll until SUCCESS/FAILED |
| B (Components) | `/api/components/tree` | Build component hierarchy |
| C (Catalog) | `/api/metrics/search` | Enumerate available metrics |
| D (Measures) | `/api/measures/component_tree` | Chunk by 15 metrics |
| E (Issues) | `/api/issues/search` | Stream with rollups |
| F (Rules) | `/api/rules/show` | Cache by rule key |
| G (Duplications) | `/api/duplications/show` | Top-N by density |
| H (Quality Gate) | `/api/qualitygates/project_status` | Single call |
| I (History) | `/api/project_analyses/search` | Last N analyses |

## Evaluation Checks

| ID | Name | Description |
|----|------|-------------|
| SQ-AC-1 | Issue count accuracy | Total issues in expected range |
| SQ-AC-2 | Bug count accuracy | Bug count in expected range |
| SQ-AC-3 | Vuln count accuracy | Vulnerability count in range |
| SQ-AC-4 | Smell count accuracy | Code smell count in range |
| SQ-AC-5 | Quality gate match | QG status matches expected |
| SQ-CV-1 | Metric presence | All required metrics present |
| SQ-CV-2 | Rule coverage | Triggered rules >= threshold |
| SQ-CV-3 | File coverage | % files with measures >= 95% |
| SQ-CV-4 | Language coverage | Expected languages detected |
| SQ-CM-1 | Component tree complete | TRK, DIR, FIL all present |
| SQ-CM-2 | Issue locations | Issues have file+line |
| SQ-CM-3 | Rules hydrated | All rule metadata fetched |
| SQ-CM-4 | Duplications present | Duplication data extracted |
| SQ-CM-5 | Quality gate conditions | QG has condition details |
| SQ-CM-6 | Derived insights present | Hotspots and rollups computed |

## Docker Management

```bash
# Start SonarQube container manually
make docker-up

# Check status
make docker-status

# Stop container
make docker-down

# Stop and remove volumes
make docker-down-volumes
```

Docker Desktop memory: set at least 4GB in Settings -> Resources -> Memory. SonarQube may be OOM-killed with lower limits.

## Collector Integration

The tool is registered in the collector's tool registry:

```python
"sonarqube": ToolDefinition(
    name="sonarqube",
    description="SonarQube static analysis",
    phase=ExecutionPhase.LANGUAGE_SPECIFIC,
    tool_dir="sonarqube",
    languages=["csharp", "java", "javascript", "typescript"],
    output_file="output/runs/{repo}.json",
    timeout_seconds=1200,
)
```

Use with collector:
```bash
collector collect /path/to/repo --tools sonarqube
```

## CLI Options

```bash
python -m scripts.analyze REPO_PATH \
    --project-key my-project \
    --output output.json \
    --sonarqube-url http://localhost:9000 \
    --token $SONAR_TOKEN \
    --keep-container \
    --skip-scan \
    --native-scanner \
    --timeout 600 \
    --verbose
```

| Option | Description |
|--------|-------------|
| `--project-key` | SonarQube project key (required) |
| `--output` | Output JSON file path |
| `--sonarqube-url` | SonarQube server URL |
| `--token` | Authentication token |
| `--keep-container` | Don't stop container after analysis |
| `--skip-scan` | Extract from existing project |
| `--native-scanner` | Use native sonar-scanner (not Docker) |
| `--timeout` | Analysis timeout in seconds |
| `--verbose` | Enable debug logging |

## Synthetic Test Repos

| Repo | Language | Purpose |
|------|----------|---------|
| csharp-clean | C# | Baseline, minimal issues |
| csharp-complex | C# | High complexity, many smells |
| java-security | Java | SQL injection, hardcoded secrets |
| typescript-duplication | TypeScript | High duplication % |

Run all eval repos:
```bash
make analyze-all-evals
```

## Development

```bash
# Run tests
make test

# Run tests with coverage
make test-coverage

# Lint code
make lint

# Format code
make format

# Start Python shell with modules loaded
make shell
```

## Troubleshooting

### Container won't start
- Check Docker is running: `docker info`
- Check port 9000 is free: `lsof -i :9000`
- Check logs: `docker logs vulcan-sonarqube`
 - If it exits with code 137, increase Docker Desktop memory (Settings -> Resources -> Memory) or lower JVM heaps in `src/tools/sonarqube/docker-compose.yml`

### Analysis timeout
- Increase timeout: `--timeout 1200`
- Check SonarQube logs for errors
- Ensure adequate memory (SonarQube needs 2GB+)

### Scanner fails
- Check scanner logs in terminal output
- Verify project has supported languages
- Check sonar-project.properties was generated correctly
- C# requires `dotnet sonarscanner` with a .csproj/.sln; install via `dotnet tool install --global dotnet-sonarscanner`

### Missing metrics
- Some metrics only available for certain languages
- Check metric_catalog in output for available metrics
- Ensure files are being analyzed (check components.files)
