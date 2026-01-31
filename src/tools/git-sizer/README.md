# git-sizer - Repository Health Analysis

Analyzes Git repositories for size, health, and scaling issues using [git-sizer](https://github.com/github/git-sizer).

## Overview

| Property | Value |
|----------|-------|
| Tool | git-sizer v1.5.0 |
| Purpose | Repository health, size metrics, LFS candidate detection |
| Output | Caldera envelope format (JSON) |
| License | MIT (open source) |

## Quick Start

```bash
# Setup (one-time)
make setup

# Run analysis
make analyze REPO_PATH=/path/to/repo

# Run evaluation
make evaluate

# Run LLM evaluation
make evaluate-llm

# Run tests
make test
```

## What git-sizer Measures

| Category | Metrics | Purpose |
|----------|---------|---------|
| Blobs | count, total_size, max_size | Identify LFS candidates |
| Trees | count, max_entries | Directory structure issues |
| Commits | count, depth, max_parents | History complexity |
| Paths | max_depth, max_length | Path anti-patterns |
| References | branch_count, tag_count | Reference overhead |

## Output Format

git-sizer outputs Caldera envelope format:

```json
{
  "metadata": {
    "tool_name": "git-sizer",
    "tool_version": "1.5.0",
    "run_id": "uuid",
    "repo_id": "uuid",
    "branch": "main",
    "commit": "40-character-sha",
    "timestamp": "2026-01-30T12:00:00Z",
    "schema_version": "1.0.0"
  },
  "data": {
    "tool": "git-sizer",
    "tool_version": "1.5.0",
    "health_grade": "A",
    "duration_ms": 150,
    "metrics": {
      "commit_count": 500,
      "blob_count": 1200,
      "max_blob_size": 102400,
      ...
    },
    "violations": [...],
    "lfs_candidates": [...],
    "raw_output": {...}
  }
}
```

## Health Grades

| Grade | Meaning | Typical Violations |
|-------|---------|-------------------|
| A, A+ | Healthy repository | None |
| B, B+ | Minor issues | 1-2 level 1 violations |
| C, C+ | Moderate issues | Level 2 violations |
| D, D+ | Significant issues | Level 3 violations |
| F | Critical issues | Level 4 violations |

## Violation Levels

| Level | Severity | Example |
|-------|----------|---------|
| 1 | Acceptable concern | Blob > 1 MiB |
| 2 | Somewhat concerning | Blob > 10 MiB |
| 3 | Very concerning | Blob > 50 MiB |
| 4 | Alarm bells | Blob > 100 MiB |

## Evaluation Framework

### Programmatic Checks (28 total)

| Category | Count | Focus |
|----------|-------|-------|
| Accuracy (AC) | 8 | Size detection, threshold violations |
| Coverage (CV) | 8 | Metric completeness |
| Edge Cases (EC) | 8 | Unusual repository structures |
| Performance (PF) | 4 | Analysis speed |

### LLM Judges (4 judges)

| Judge | Weight | Focus |
|-------|--------|-------|
| Size Accuracy | 35% | Blob/tree/commit sizing |
| Threshold Quality | 25% | Violation detection |
| Actionability | 20% | Report usefulness |
| Integration Fit | 20% | Caldera compatibility |

## Directory Structure

```
git-sizer/
├── Makefile                    # Primary interface
├── README.md                   # This file
├── BLUEPRINT.md                # Integration architecture
├── EVAL_STRATEGY.md            # Evaluation methodology
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Test configuration
│
├── bin/                        # git-sizer binary (downloaded)
├── scripts/
│   ├── analyze.py              # Main analysis script
│   ├── evaluate.py             # Evaluation orchestrator
│   ├── binary_manager.py       # Binary download
│   └── checks/                 # Programmatic checks
│       ├── __init__.py
│       ├── accuracy.py
│       ├── coverage.py
│       ├── edge_cases.py
│       └── performance.py
│
├── schemas/
│   └── output.schema.json      # Caldera envelope schema
│
├── eval-repos/
│   └── synthetic/              # Test repositories
│       ├── healthy/
│       ├── bloated/
│       ├── deep-history/
│       ├── wide-tree/
│       └── multi-branch/
│
├── evaluation/
│   ├── ground-truth/           # Expected values
│   └── llm/                    # LLM judges
│       ├── run_judges.py
│       └── judges/
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── output/                     # Generated (gitignored)
```

## SoT Engine Integration

git-sizer data is persisted to three landing zone tables:

| Table | Purpose |
|-------|---------|
| `lz_git_sizer_metrics` | Repository-level health metrics |
| `lz_git_sizer_violations` | Threshold violations |
| `lz_git_sizer_lfs_candidates` | LFS migration candidates |

## Makefile Targets

| Target | Description |
|--------|-------------|
| `setup` | Create venv, install deps, download binary |
| `analyze` | Run git-sizer analysis |
| `evaluate` | Run programmatic evaluation |
| `evaluate-llm` | Run LLM judge evaluation |
| `test` | Run pytest |
| `clean` | Remove generated files |

## Documentation

- [BLUEPRINT.md](BLUEPRINT.md) - Integration architecture and lessons learned
- [EVAL_STRATEGY.md](EVAL_STRATEGY.md) - Evaluation methodology

## References

- [git-sizer GitHub](https://github.com/github/git-sizer)
- [Git LFS](https://git-lfs.github.com/)
