# PoC #1: scc (Sloc Cloc Code)

Proof-of-concept for evaluating [scc](https://github.com/boyter/scc) as a size/LOC analysis tool for the DD Platform.

## Quick Start

```bash
make setup              # Install scc and Python dependencies
make analyze            # Run analysis on synthetic repos
make analyze-interactive # Interactive multi-repo analysis
```

## Repo Identity

`repo_id` is provided by the orchestrator/app alongside `repo_path`. The tool analyzes `repo_path` directly; `repo_id` is emitted in the output for correlation in the SoT engine. If `commit` is not supplied, the tool resolves the repository HEAD when `repo_path` is a git repo; otherwise it falls back to the project repo HEAD. Supplied commits are validated against the repo before use.

Production readiness gates are defined in `docs/COMPLIANCE.md`.

## Features

### v2.0 Dashboard (18 Sections)

Rich terminal dashboard with comprehensive analysis:

| Section | Description |
|---------|-------------|
| Executive Summary | Key findings, concerns, recommendations |
| Code Distribution | LOC distribution with Gini coefficient |
| Language Breakdown | Per-language stats and complexity |
| Codebase Health | Ratios, density, test coverage |
| File Classifications | Test/config/docs/build/CI breakdown |
| Top Files | By LOC, complexity, and density |
| Directory Tree | Recursive AND direct stats per directory |
| COCOMO Estimates | 8 presets from startup to enterprise |
| Distribution Stats | 22 metrics including inequality measures |

### Interactive Multi-Repo Analysis

Analyze 16 repositories interactively:
- 7 synthetic repos (Python, C#, Java, JavaScript, TypeScript, Go, Rust)
- 9 real OSS repos (click, Humanizer, picocli, dayjs, etc.)

```bash
make analyze-interactive
```

### Output Files (Envelope Format)

The tool writes a single envelope JSON output for downstream ingestion:

```
outputs/<run-id>/
├── output.json               # Envelope output (metadata + data)
├── raw_scc_output.json       # Raw scc output (evaluation only)
└── directory_analysis.json   # Optional directory analysis output
```

Programmatic and LLM evaluation outputs are written to a fixed location and overwrite the previous run:

```
evaluation/results/
├── output.json               # Envelope output for evaluation runs
├── raw_scc_output.json       # Raw scc output (evaluation)
├── evaluation_report.json    # Programmatic evaluation (JSON)
├── scorecard.md              # Programmatic scorecard
└── llm_evaluation.json       # LLM judge results (if run)
```

### 22 Distribution Metrics

Statistical analysis including inequality measures:
- Basic: min, max, mean, median, stddev, percentiles (p25, p50, p75, p90, p95, p99)
- Shape: skewness, kurtosis, coefficient of variation, IQR
- Inequality: Gini, Theil, Hoover, Palma ratio, concentration shares

### 8 COCOMO Presets

Effort estimation for different organization sizes:

| Preset | Hourly Rate | Overhead | Use Case |
|--------|-------------|----------|----------|
| open_source | $0 | 0% | Open source projects |
| early_startup | $75 | 10% | Pre-seed/seed startups |
| growth_startup | $100 | 20% | Series A-B startups |
| scale_up | $125 | 30% | Series C+ scale-ups |
| sme | $150 | 40% | Small-medium enterprises |
| mid_market | $175 | 50% | Mid-market companies |
| large_enterprise | $200 | 60% | Large enterprises |
| regulated | $250 | 80% | Regulated industries |

## Make Targets

```bash
make help               # Show all targets
make setup              # Install scc and Python dependencies
make analyze            # Run analysis with v2.0 dashboard
make analyze-interactive # Interactive multi-repo selection
make analyze-real       # Analyze real OSS repositories
make evaluate           # Run programmatic evaluation (63 checks)
make evaluate-llm       # Run LLM-as-a-Judge evaluation (Claude CLI, model = opus-4.5)
make test               # Run all tests
make test-quick         # Run fast tests only
make clean              # Remove generated files
```

## Directory Structure

```
poc-scc/
├── Makefile                  # Primary interface
├── README.md                 # This file
├── BLUEPRINT.md              # Lessons learned for next PoC
├── requirements.txt          # Python dependencies
│
├── scripts/
│   ├── directory_analyzer.py # Main analysis script (v2.0 dashboard)
│   ├── evaluate.py           # Programmatic evaluation (63 checks)
│   ├── validate.py           # JSON schema validation
│   └── checks/               # Individual evaluation checks
│
├── eval-repos/
│   ├── synthetic/            # 7 languages, 63 files
│   │   ├── python/           # 9 files: simple, complex, massive, edge cases
│   │   ├── csharp/           # 9 files
│   │   ├── java/             # 9 files
│   │   ├── javascript/       # 9 files
│   │   ├── typescript/       # 9 files
│   │   ├── go/               # 9 files
│   │   └── rust/             # 9 files
│   └── real/                 # Git submodules to OSS projects
│       ├── click/            # Python CLI toolkit
│       ├── Humanizer/        # C# string manipulation
│       ├── picocli/          # Java CLI framework
│       └── ...               # 9 repos total
│
├── outputs/                  # Generated analysis (gitignored)
│   └── <run-id>/             # One folder per run
│       ├── output.json       # Envelope output
│       └── raw_scc_output.json # Raw scc output (evaluation)
│
├── evaluation/               # Evaluation framework
│   ├── EVAL_STRATEGY.md      # Evaluation methodology
│   ├── ground-truth/         # Expected values
│   ├── results/              # Evaluation outputs (overwritten each run)
│   └── llm/                  # LLM-as-a-Judge prompts and judges
│
├── schemas/                  # JSON schemas
│   └── output.schema.json    # Envelope schema
│
├── docs/                     # Technical documentation
│   ├── SCC_DEEP_DIVE.md      # scc capabilities deep dive
│   └── COCOMO_REFERENCE.md   # COCOMO estimation reference
│
└── tests/                    # Test suite
    ├── scripts/              # Script tests
    └── evaluation/           # Evaluation tests
```

## Evaluation Repositories

### Synthetic (7 languages, 63 files)

Each language has identical structure for consistent testing:

```
{language}/
├── simple.{ext}           # Low complexity (CCN ~1-3)
├── complex.{ext}          # Medium complexity (CCN ~10-20)
├── massive.{ext}          # High complexity (CCN ~30+), 500+ LOC
├── module/
│   └── nested.{ext}       # Tests imports/modules
└── edge_cases/
    ├── empty.{ext}        # 0 bytes
    ├── comments_only.{ext}
    ├── single_line.{ext}
    ├── unicode.{ext}
    └── deep_nesting.{ext} # 10+ levels
```

### Real OSS Repositories (9 projects, ~3,200 files)

| Repository | Language | Files | Description |
|------------|----------|-------|-------------|
| envconfig | Go | 18 | Environment variable config |
| click | Python | 147 | CLI toolkit |
| chalk | JS/TS | 35 | Terminal styling |
| Humanizer | C# | 699 | String manipulation |
| hashids.net | C# | 24 | URL-safe ID encoding |
| dayjs | JavaScript | 380 | Date library |
| nanoid | JavaScript | 39 | Unique ID generator |
| joda-money | Java | 69 | Money/currency handling |
| picocli | Java | 1,735 | CLI framework |

Initialize with `make setup` (uses git submodules).

## Output Schema (Envelope)

```json
{
  "metadata": {
    "tool_name": "scc",
    "tool_version": "3.6.0",
    "run_id": "uuid",
    "repo_id": "uuid",
    "branch": "main",
    "commit": "40-hex",
    "timestamp": "2026-01-04T16:35:55Z",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "scc",
    "tool_version": "3.6.0",
    "summary": { ... },
    "languages": [ ... ],
    "files": [ ... ],
    "directories": [ ... ]
  }
}
```

## Latest Evaluation (2026-01-25)

**Programmatic:** 5.00/5.0 (STRONG_PASS) — Run ID: `eval-20260125-101837`  
**LLM-as-Judge:** 4.32/5.0 (STRONG_PASS) — Run ID: `llm-eval-20260125-104034`  
**Combined:** 4.73/5.0 (STRONG_PASS)

See:
- `evaluation/results/scorecard.md`
- `evaluation/results/combined_scorecard.md`
- `evaluation/results/llm_evaluation.md`

## Tool Information

- **Tool**: scc (Sloc Cloc Code)
- **Version**: 3.6.0
- **GitHub**: https://github.com/boyter/scc
- **License**: MIT/Unlicense
- **Languages**: 100+

## Known Limitations

### WeightedComplexity Always 0 in JSON

The `WeightedComplexity` field in scc's JSON output is always 0. This is a known limitation - the calculation only happens in text output mode.

**Workaround**: Calculate it from the JSON:
```python
weighted_complexity = (complexity / code) * 100 if code > 0 else 0
```

## Troubleshooting

### scc not found
```bash
make setup  # Downloads binary to ./bin/scc
```

### Real repos not initialized
```bash
git submodule update --init --recursive
```

### Python issues
```bash
make clean && make setup
```

## License

This PoC is part of the DD Platform project.
