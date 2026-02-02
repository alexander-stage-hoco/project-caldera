# Insights - Consolidated Reporting Component

Generates HTML and Markdown reports from Caldera dbt marts. This is the central reporting component for Project Caldera.

## Overview

Insights provides:
- **Report Generation**: HTML and Markdown reports from DuckDB data
- **Modular Sections**: 12 report sections (executive summary, repo health, hotspots, directories, vulnerabilities, cross-tool, languages, distributions, roslyn, IaC, module health, code inequality)
- **Evaluation Framework**: 21 programmatic checks + 3 LLM judges
- **Multi-Provider LLM Support**: Claude Code, OpenAI, Codex, Anthropic

## Quick Start

```bash
# Install
cd src/insights
make setup

# Generate a report
python -m insights generate 1 --db /path/to/caldera_sot.duckdb -f html -o report.html

# List available sections
python -m insights list-sections

# Evaluate a report
python -m insights.scripts.evaluate evaluate report.html --db /path/to/caldera_sot.duckdb
```

## Report Sections

| Section | Description | Priority |
|---------|-------------|----------|
| `executive_summary` | AI-generated insights and recommendations | 0 |
| `repo_health` | Repository health overview (files, LOC, complexity, grade) | 1 |
| `file_hotspots` | Top files by complexity, size, smells | 2 |
| `directory_analysis` | Directory-level rollups and hotspots | 3 |
| `vulnerabilities` | Security vulnerability summary | 4 |
| `cross_tool` | Compound risks from multiple tools | 5 |
| `language_coverage` | Language distribution | 6 |
| `distribution_insights` | Gini, Hoover, P95 statistical analysis | 7 |
| `roslyn_violations` | Roslyn analyzer findings for C#/.NET | 8 |
| `iac_misconfigs` | IaC misconfigurations from Trivy | 9 |
| `module_health` | Module health scores and risk factors | 10 |
| `code_inequality` | Code distribution inequality analysis | 11 |

## CLI Commands

### Generate Reports

```bash
# Full report
python -m insights generate <RUN_PK> --db <DB_PATH> -f html -o report.html

# Specific sections only
python -m insights generate <RUN_PK> --db <DB_PATH> -s repo_health,vulnerabilities

# Markdown format
python -m insights generate <RUN_PK> --db <DB_PATH> -f md -o report.md
```

### Evaluate Reports

```bash
# Full evaluation (programmatic + LLM)
python -m insights.scripts.evaluate evaluate report.html --db db.duckdb

# Skip LLM evaluation
python -m insights.scripts.evaluate evaluate report.html --db db.duckdb --skip-llm

# Use different LLM provider
python -m insights.scripts.evaluate evaluate report.html --provider openai --model gpt-4o
```

### List Available Components

```bash
# List sections
python -m insights list-sections

# List programmatic checks
python -m insights.scripts.evaluate list-checks

# List LLM judges
python -m insights.scripts.evaluate list-judges
```

## Programmatic API

```python
from insights import InsightsGenerator

generator = InsightsGenerator(db_path=Path("/path/to/caldera_sot.duckdb"))

# Generate full report
html = generator.generate(run_pk=1, format="html")

# Generate specific sections
md = generator.generate(
    run_pk=1,
    format="md",
    sections=["repo_health", "vulnerabilities"],
)

# Generate single section
section = generator.generate_section("repo_health", run_pk=1, format="html")
```

## Evaluation Framework

### Scoring

- **Programmatic Checks**: 60% weight (21 checks across 4 dimensions)
- **LLM Judges**: 40% weight (3 judges)

### Pass Thresholds

| Status | Score Range |
|--------|-------------|
| STRONG_PASS | >= 4.0 |
| PASS | >= 3.5 |
| WEAK_PASS | >= 3.0 |
| FAIL | < 3.0 |

### Programmatic Check Dimensions

| Dimension | Checks | Description |
|-----------|--------|-------------|
| Accuracy | IN-AC-1 to IN-AC-6 | Data matches database |
| Completeness | IN-CM-1 to IN-CM-5 | Required sections/fields present |
| Format Quality | IN-FQ-1 to IN-FQ-5 | HTML/MD well-formed |
| Data Integrity | IN-DI-1 to IN-DI-5 | Internal consistency |

### LLM Judges

| Judge | Weight | Sub-dimensions |
|-------|--------|----------------|
| Clarity | 30% | Structure, Language, Data Presentation |
| Actionability | 40% | Prioritization, Locations, Remediation |
| Accuracy | 30% | Consistency, Plausibility, Completeness |

### LLM Providers

| Provider | Default Model | Notes |
|----------|---------------|-------|
| `claude_code` | claude-opus-4-5 | Default, recommended |
| `openai` | gpt-4o | Requires OPENAI_API_KEY |
| `codex` | codex | Requires Codex CLI |
| `anthropic` | claude-3-5-sonnet | Requires ANTHROPIC_API_KEY |

### LLM Observability

All LLM judge calls are automatically logged with full request/response data for debugging.

**CLI Options:**
```bash
# Enable verbose console logging
python -m insights.scripts.evaluate evaluate report.html --verbose

# Custom log directory
python -m insights.scripts.evaluate evaluate report.html --log-dir /tmp/llm_logs
```

**Log Location:** `output/llm_logs/{YYYY-MM-DD}/interactions.jsonl`

**Query Logs Programmatically:**
```python
from insights.evaluation.llm.observability import FileStore

store = FileStore()
interactions = store.query_by_trace("trace-id-from-output")
for i in interactions:
    print(f"{i.judge_name}: {i.duration_ms}ms, status={i.status}")
```

## Directory Structure

```
src/insights/
├── __init__.py           # Public API
├── generator.py          # InsightsGenerator main class
├── data_fetcher.py       # SQL query execution
├── cli.py                # CLI entry point
├── formatters/           # HTML and Markdown formatters
├── sections/             # Report section implementations
├── queries/              # SQL query files
├── templates/            # Jinja2 templates
├── evaluation/           # Evaluation framework
│   ├── ground-truth/     # Test scenarios
│   └── llm/              # LLM providers and judges
│       ├── judges/       # Judge implementations
│       ├── providers/    # LLM provider adapters
│       └── observability/# Logging and tracing
├── scripts/
│   ├── checks/           # Programmatic checks
│   └── evaluate.py       # Evaluation orchestrator
├── tests/                # Unit tests
├── Makefile
└── README.md
```

## Data Sources

Insights queries the following Caldera dbt marts:

| Mart | Purpose |
|------|---------|
| `unified_file_metrics` | Per-file LOC, complexity |
| `stg_trivy_vulnerabilities` | CVE findings |
| `stg_semgrep_file_metrics` | Code smell aggregations |
| `stg_lz_tool_runs` | Tool run metadata |
| `rollup_*` | Pre-computed directory rollups |
| `stg_roslyn_file_metrics` | Roslyn analyzer findings |
| `stg_trivy_iac_misconfigs` | IaC misconfiguration findings |
| `unified_run_summary` | Repository-level summaries |
| `repo_health_summary` | Git-sizer health grades |

See [EVAL_STRATEGY.md](EVAL_STRATEGY.md) for the full evaluation strategy.
