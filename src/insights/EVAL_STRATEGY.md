# Insights Evaluation Strategy

## Overview

The Insights component uses a two-tier evaluation approach:
1. **Programmatic Checks (60% weight)**: Fast, deterministic validations
2. **LLM Judges (40% weight)**: Semantic quality assessment

## Evaluation Dimensions

### Programmatic Checks (21 checks)

#### Accuracy (IN-AC-*)
Verify reported metrics match source database.

| ID | Name | Weight | Description |
|----|------|--------|-------------|
| IN-AC-1 | Total Files Accuracy | 1.0 | File count matches database |
| IN-AC-2 | Total LOC Accuracy | 1.0 | LOC matches database |
| IN-AC-3 | Hotspot Count Accuracy | 0.8 | Hotspot count reasonable |
| IN-AC-4 | Vulnerability Count Accuracy | 1.0 | Vuln count matches |
| IN-AC-5 | Average Complexity Accuracy | 0.8 | Avg CCN matches |
| IN-AC-6 | Severity Distribution Accuracy | 0.8 | Severity breakdown matches |

#### Completeness (IN-CM-*)
Verify all required sections and fields are present.

| ID | Name | Weight | Description |
|----|------|--------|-------------|
| IN-CM-1 | Required Sections Present | 1.0 | repo_health, file_hotspots, vulnerabilities |
| IN-CM-2 | Repo Health Metrics Complete | 1.0 | All key metrics present |
| IN-CM-3 | Hotspot Details Complete | 0.8 | Path, complexity for each |
| IN-CM-4 | Vulnerability Details Complete | 0.8 | CVE, severity, package |
| IN-CM-5 | Directory Rollups Present | 0.6 | Hotspots and largest dirs |

#### Format Quality (IN-FQ-*)
Verify HTML/Markdown output quality.

| ID | Name | Weight | Description |
|----|------|--------|-------------|
| IN-FQ-1 | HTML Well-Formed | 1.0 | Valid HTML structure |
| IN-FQ-2 | Required HTML Elements | 0.8 | Header, nav, main, footer |
| IN-FQ-3 | No Forbidden Patterns | 0.6 | No scripts, unrendered vars |
| IN-FQ-4 | Markdown Headers Valid | 1.0 | Proper header hierarchy |
| IN-FQ-5 | Markdown Tables Valid | 0.8 | Valid table syntax |

#### Data Integrity (IN-DI-*)
Verify internal consistency.

| ID | Name | Weight | Description |
|----|------|--------|-------------|
| IN-DI-1 | File Counts Consistent | 1.0 | Counts match across sections |
| IN-DI-2 | LOC Sums Consistent | 1.0 | Code + comments <= total |
| IN-DI-3 | Severity Counts Sum | 1.0 | Breakdown sums to total |
| IN-DI-4 | Hotspots Sorted | 0.6 | Ordered by severity desc |
| IN-DI-5 | No Duplicate Entries | 0.8 | Unique file paths |

### LLM Judges (3 judges)

#### Clarity Judge (30% weight)
Evaluates report presentation quality.

| Sub-dimension | Weight | Focus |
|---------------|--------|-------|
| Structure | 40% | Logical organization, section flow |
| Language | 30% | Clear writing, terminology |
| Data Presentation | 30% | Tables, numbers, hierarchy |

#### Actionability Judge (40% weight)
Evaluates how actionable findings are.

| Sub-dimension | Weight | Focus |
|---------------|--------|-------|
| Prioritization | 35% | Clear issue ranking |
| Locations | 35% | Specific file/line refs |
| Remediation | 30% | Fix guidance |

#### Accuracy Judge (30% weight)
Evaluates content accuracy and consistency.

| Sub-dimension | Weight | Focus |
|---------------|--------|-------|
| Consistency | 40% | Numbers add up |
| Plausibility | 30% | Values reasonable |
| Completeness | 30% | No missing data |

## Scoring

### Score Scale
All scores use a 1-5 scale:
- 5: Excellent
- 4: Good
- 3: Adequate
- 2: Poor
- 1: Very Poor

### Pass Thresholds

| Status | Score Range | Description |
|--------|-------------|-------------|
| STRONG_PASS | >= 4.0 | Excellent quality |
| PASS | >= 3.5 | Acceptable |
| WEAK_PASS | >= 3.0 | Needs improvement |
| FAIL | < 3.0 | Unacceptable |

### Overall Score Calculation

```
overall = (programmatic_score * 0.6) + (llm_score * 0.4)
```

Where:
- `programmatic_score` = weighted average of check results (0-1 normalized to 1-5)
- `llm_score` = weighted average of judge scores (1-5)

## LLM Provider Configuration

### Default: Claude Code Headless
```bash
python -m insights.scripts.evaluate evaluate report.html
```

### OpenAI
```bash
export OPENAI_API_KEY=sk-...
python -m insights.scripts.evaluate evaluate report.html --provider openai --model gpt-4o
```

### Anthropic API
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m insights.scripts.evaluate evaluate report.html --provider anthropic
```

## LLM Observability & Debugging

### Trace Correlation

Each evaluation run generates a unique `trace_id` that links all judge interactions. The trace ID is:
- Displayed in CLI output after evaluation
- Included in the JSON output as `llm_trace_id`
- Used to query all related interactions

### Log Storage

LLM interactions are persisted to JSON-Lines files:
```
output/llm_logs/
└── 2026-02-01/
    └── interactions.jsonl
```

Each log entry contains:
- Full system and user prompts
- Complete LLM response
- Token usage (prompt, completion, total)
- Timing (start, end, duration_ms)
- Status (success, error, timeout)
- Judge name and provider

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_OBSERVABILITY_ENABLED` | `true` | Master switch |
| `LLM_OBSERVABILITY_LOG_DIR` | `output/llm_logs` | Log directory |
| `LLM_OBSERVABILITY_CONSOLE` | `false` | Console logging |
| `LLM_OBSERVABILITY_INCLUDE_PROMPTS` | `true` | Log full prompts |
| `LLM_OBSERVABILITY_INCLUDE_RESPONSES` | `true` | Log full responses |

### Querying Logs

```python
from insights.evaluation.llm.observability import FileStore

store = FileStore()

# Query by trace ID (from evaluation output)
interactions = store.query_by_trace("abc-123")

# Query by judge
clarity_calls = store.query_by_judge("clarity")

# Query by status (find errors)
errors = store.query_by_status("error")

# Get daily statistics
stats = store.get_stats()
print(f"Total calls: {stats['total_count']}")
print(f"Unique traces: {stats['unique_traces']}")
print(f"Avg duration: {stats['avg_duration_ms']}ms")

# Build evaluation span (all judges for one run)
span = store.get_evaluation_span("trace-id")
print(f"Judges: {span.judge_count}, Success: {span.successful_judges}")
```

## Ground Truth Scenarios

Three test scenarios in `evaluation/ground-truth/`:

| Scenario | Description | Expected Grade |
|----------|-------------|----------------|
| `scenario-basic` | Standard repository | B |
| `scenario-complex` | Large, high-complexity repo | D |
| `scenario-security` | Security-focused with vulns | C |

## Running Evaluations

### Full Evaluation
```bash
make evaluate REPORT=output/report.html RUN_PK=1
```

### Programmatic Only
```bash
make evaluate-no-llm REPORT=output/report.html
```

### View Available Checks
```bash
make list-checks
make list-judges
```

## Continuous Improvement

1. **Track metrics over time**: Store evaluation results in `evaluation/results/`
2. **Analyze failures**: Review low-scoring reports for patterns
3. **Update thresholds**: Adjust check weights based on importance
4. **Refine prompts**: Iterate on LLM judge prompts for consistency
