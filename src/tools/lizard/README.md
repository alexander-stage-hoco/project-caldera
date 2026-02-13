# PoC #2: Lizard (Function-Level Complexity Analyzer)

Proof-of-concept for evaluating [Lizard](https://github.com/terryyin/lizard) as a function-level complexity analysis tool for the DD Platform.

## Quick Start

```bash
make setup              # Install Python dependencies (lizard)
make analyze            # Run analysis with dashboard
make analyze-interactive # Interactive multi-repo analysis
```

## Repo Identity

`repo_id` is provided by the orchestrator/app alongside `repo_path`. The tool analyzes `repo_path` directly; `repo_id` is emitted in the output for correlation in the SoT engine. If `commit` is not supplied, the tool resolves the repository HEAD when `repo_path` is a git repo; otherwise it falls back to the project repo HEAD. Supplied commits are validated against the repo before use.

Production readiness gates are defined in `docs/COMPLIANCE.md`.

## Why Lizard?

PoC #1 (scc) identified a gap: **no per-function granularity**. Lizard fills this gap with:

| Metric | Description |
|--------|-------------|
| `cyclomatic_complexity` | McCabe complexity per function |
| `nloc` | Non-commenting lines of code per function |
| `token_count` | Token count per function |
| `parameter_count` | Number of parameters |
| `start_line` / `end_line` | Function location in file |
| `function_name` | Fully qualified function name |

## Features

### 16-Section Dashboard

1. **Header** - Repository, timestamp, lizard version
2. **Quick Stats** - Files, functions, total CCN
3. **CCN Distribution** - Histogram with percentiles
4. **Hotspot Functions** - Top 10 by CCN
5. **Large Functions** - Top 10 by NLOC
6. **Parameter-Heavy** - Functions with 5+ parameters
7. **Per-Language Summary** - CCN stats by language
8. **File Summary** - Per-file function counts
9. **Threshold Violations** - Functions exceeding CCN threshold
10. **Complexity Density** - CCN per NLOC ratio
11. **Function Size Distribution** - NLOC distribution
12. **Directory Structure** - Max depth, leaf count, avg functions/dir
13. **Top Directories by Recursive CCN** - Ranked by total recursive CCN
14. **Top Directories by Direct Functions** - Where functions actually live
15. **Complete Directory Tree** - Tree view with recursive AND direct stats
16. **Analysis Summary** - Key findings

### Directory Rollup (Recursive vs Direct)

Each directory has two sets of statistics:
- **Recursive**: Includes all files in directory and subdirectories
- **Direct**: Only files directly in that directory (not subdirectories)

This enables identifying where complexity concentrates in the codebase.

### Distribution Statistics (22 metrics per distribution)

For CCN, NLOC, and parameter count distributions per directory:

| Category | Metrics |
|----------|---------|
| Basic | count, min, max, mean, median, stddev |
| Percentiles | p25, p50, p75, p90, p95, p99 |
| Shape | skewness, kurtosis, cv, iqr |
| Inequality | gini, theil, hoover, palma, top_10_pct_share, top_20_pct_share, bottom_50_pct_share |

### Summary Exclusion Counts

The summary includes counts of excluded files by reason:

| Field | Description |
|-------|-------------|
| `excluded_count` | Total number of excluded files |
| `excluded_by_pattern` | Files excluded by filename pattern |
| `excluded_by_minified` | Files excluded by minification detection |
| `excluded_by_size` | Files excluded by size limit |
| `excluded_by_language` | Files excluded by unsupported language |

### Output with Traceability

Each run emits a single envelope output plus metadata:

```
outputs/<run-id>/
├── output.json    # Envelope output (schema-backed)
└── metadata.json  # Run parameters, versions
```

Programmatic and LLM evaluation outputs are written to a fixed location and overwrite the previous run:

```
evaluation/results/
├── output.json               # Envelope output for evaluation runs
├── evaluation_report.json    # Programmatic evaluation report
├── scorecard.md              # Programmatic scorecard
└── llm_evaluation.json       # LLM judge results (if run)
```

## Performance

### Thread Configuration

By default, lizard uses `min(cpu_count // 2, 4)` threads to avoid thrashing on hyperthreaded CPUs. Override via:

```bash
make analyze LIZARD_THREADS=8   # Use 8 threads
```

### O(n) Directory Aggregation

Directory rollup uses bottom-up memoized aggregation for O(n) complexity instead of O(n × depth). Directories are processed from leaves to root, with each directory's recursive stats computed by aggregating its direct stats plus cached child stats. This dramatically improves performance for deeply nested directory structures.

### Benchmarks

| Repository Size | Files | Functions | Time | Memory |
|-----------------|-------|-----------|------|--------|
| Synthetic | 63 | 524 | 0.29s | ~45MB |
| click | 62 | ~800 | 0.35s | ~50MB |
| picocli/src | ~200 | ~2000 | 1.63s | ~80MB |

## File Exclusions

### Pattern-Based Exclusions

The following files are automatically excluded based on filename patterns:

| Category | Patterns |
|----------|----------|
| Minified | `*.min.js`, `*.min.css`, `*.min.ts` |
| Bundled | `*.bundle.js`, `*.chunk.js`, `*.umd.js` |
| Vendor Libraries | `jquery*.js`, `react*.js`, `vue*.js`, `angular*.js`, `lodash*.js`, `moment*.js`, `d3*.js` |
| Generated Code | `*.designer.cs`, `*.g.cs`, `*.generated.*`, `*_pb2.py`, `*.pb.go`, `*_pb2_grpc.py`, `*.d.ts` |
| Source Maps | `*.map` |

### Content-Based Minification Detection

For JavaScript and TypeScript files, content-based heuristics detect minified files:

| Heuristic | Threshold |
|-----------|-----------|
| Average line length | > 500 characters |
| Single line length | > 1000 characters (first 10 lines) |
| Newline ratio | < 1 newline per 500 characters |

### Directory Exclusions

| Category | Directories |
|----------|-------------|
| Build artifacts | `bin`, `obj`, `dist`, `build`, `coverage`, `artifacts` |
| IDE/VCS | `.git`, `.vs`, `.idea`, `TestResults` |
| Virtual environments | `.venv`, `venv`, `env`, `virtualenv` |
| Vendor (default excluded) | `node_modules`, `vendor`, `packages`, `bower_components`, `lib`, `third_party` |

Use `--include-vendor` to include vendor directories in analysis.

### Excluded Files Tracking

Excluded files are tracked in the output with reason and details:

```json
{
  "excluded_files": [
    {"path": "vendor/jquery.min.js", "reason": "pattern", "language": "JavaScript", "details": "jquery*.js"},
    {"path": "dist/bundle.js", "reason": "minified", "language": "JavaScript", "details": "avg_line_length=1200"}
  ]
}
```

## Make Targets

```bash
make help               # Show all targets
make setup              # Install lizard and Python dependencies
make analyze            # Run analysis with dashboard
make analyze-interactive # Interactive multi-repo selection
make analyze-real       # Analyze real OSS repositories
make evaluate           # Run programmatic evaluation (76 checks)
make test               # Run all tests
make test-quick         # Run fast tests only
make clean              # Remove generated files
```

Note: If `.venv` cannot be created in this directory, set `VENV=/tmp/lizard-venv` and (optionally) symlink `.venv` to that path for integration tests.

## Directory Structure

```
poc-lizard/
├── Makefile                  # Primary interface
├── README.md                 # This file
├── requirements.txt          # Python dependencies
│
├── scripts/
│   ├── function_analyzer.py  # Main analysis script with dashboard
│   ├── evaluate.py           # Programmatic evaluation
│   └── checks/               # Individual evaluation checks
│
├── eval-repos/
│   ├── synthetic/            # 7 languages, 63 files
│   │   ├── python/
│   │   ├── csharp/
│   │   ├── java/
│   │   ├── javascript/
│   │   ├── typescript/
│   │   ├── go/
│   │   └── rust/
│   └── real/                 # 9 OSS repos (git submodules)
│
├── outputs/                  # Generated analysis (gitignored)
│   └── <run-id>/             # One folder per run
│
├── evaluation/
│   ├── ground-truth/         # Expected CCN values
│   ├── results/              # Evaluation outputs (overwritten each run)
│   └── llm/                  # LLM-based evaluation
│
├── schemas/                  # JSON schemas
│
└── tests/                    # Test suite
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

### Real OSS Repositories (9 projects)

| Repository | Language | Description |
|------------|----------|-------------|
| click | Python | CLI toolkit |
| Humanizer | C# | String manipulation |
| picocli | Java | CLI framework |
| dayjs | JavaScript | Date library |
| chalk | JavaScript | Terminal styling |
| nanoid | JavaScript | Unique ID generator |
| joda-money | Java | Money/currency handling |
| hashids.net | C# | URL-safe ID encoding |
| envconfig | Go | Environment variable config |

Initialize with `make setup` (uses git submodules).

## Output Schema (Envelope v1.0.0)

```json
{
  "metadata": {
    "tool_name": "lizard",
    "tool_version": "1.17.10",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "660e8400-e29b-41d4-a716-446655440001",
    "branch": "main",
    "commit": "abc123def456789012345678901234567890abcd",
    "timestamp": "2026-01-04T18:45:00Z",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "lizard",
    "tool_version": "1.17.10",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-01-04T18:45:00Z",
    "root_path": "eval-repos/synthetic/python",
    "lizard_version": "lizard 1.17.10",
    "summary": {
      "total_files": 4,
      "total_functions": 12,
      "total_ccn": 42
    },
    "directories": [
      {
        "path": ".",
        "name": "python",
        "direct": {"file_count": 3, "function_count": 51, "nloc": 600, "ccn": 182},
        "recursive": {"file_count": 9, "function_count": 60, "nloc": 765, "ccn": 227}
      }
    ],
    "files": [
      {
        "path": "complex.py",
        "language": "Python",
        "nloc": 150,
        "functions": [
          {"name": "process_data", "nloc": 35, "ccn": 12, "token_count": 180}
        ]
      }
    ]
  }
}
```

## Tool Information

- **Tool**: Lizard
- **GitHub**: https://github.com/terryyin/lizard
- **License**: MIT
- **Languages**: 20+ (Python, C#, Java, JavaScript, TypeScript, Go, Rust, C, C++, PHP, Ruby, etc.)

## Evaluation Results

### Programmatic Evaluation: 98.6% (76/76 checks)

All checks passing across accuracy, coverage, edge cases, and performance.

### LLM Evaluation (Claude Opus 4.5): 3.85/5.0 STRONG_PASS

| Judge | Weight | Score | Confidence |
|-------|--------|-------|------------|
| ccn_accuracy | 35% | 3/5 | 50% |
| function_detection | 25% | 4/5 | 85% |
| statistics | 20% | 5/5 | 95% |
| hotspot_ranking | 20% | 4/5 | 85% |

**Key Findings:**
- Function detection strong across languages; C# slightly over-detects functions
- Statistics are valid; parameter distribution is currently empty
- CCN accuracy is solid with occasional edge-case mismatches
- Hotspot ranking is accurate; one malformed TypeScript function name observed

### Combined Evaluation: 4.51/5.0 STRONG_PASS

Programmatic + LLM combined score based on the latest run in `evaluation/results/combined_evaluation.json`.

**Decision: STRONG_PASS** - Approved for DD Platform integration.

## See Also

- [PoC #1: scc](../poc-scc/) - Size/LOC analysis (file-level)
- [BLUEPRINT.md](BLUEPRINT.md) - Lessons learned

## License

This PoC is part of the DD Platform project.
