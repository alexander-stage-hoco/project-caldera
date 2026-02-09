# coverage-ingest

Multi-format test coverage ingestion tool for Project Caldera. Normalizes coverage reports from various formats into a unified schema for gap analysis.

## Supported Formats

| Format | Extension | Structure | Primary Use |
|--------|-----------|-----------|-------------|
| **LCOV** | `.info`, `.lcov` | Line-oriented text | C/C++, Python, Go |
| **Cobertura** | `.xml` | XML hierarchy | Java, Python, multi-language CI |
| **JaCoCo** | `.xml` | XML with instruction counts | Java |
| **Istanbul** | `.json` | JSON with statement/branch maps | JavaScript/TypeScript |

## Quick Start

```bash
# Install dependencies
make setup

# Ingest a coverage report
make analyze COVERAGE_FILE=/path/to/coverage.xml

# Run with specific format (auto-detection is default)
make analyze COVERAGE_FILE=/path/to/lcov.info FORMAT=lcov

# Run tests
make test
```

## CLI Usage

```bash
python scripts/analyze.py \
    --repo-path /path/to/repo \
    --repo-id my-project \
    --run-id $(uuidgen) \
    --coverage-file /path/to/coverage.xml \
    --format auto
```

## Output Schema

The tool produces per-file coverage metrics:

```json
{
  "metadata": {
    "tool_name": "coverage-ingest",
    "tool_version": "1.0.0",
    ...
  },
  "data": {
    "files": [
      {
        "relative_path": "src/main.py",
        "line_coverage_pct": 85.5,
        "branch_coverage_pct": 72.0,
        "lines_total": 100,
        "lines_covered": 85,
        "lines_missed": 15,
        "branches_total": 25,
        "branches_covered": 18,
        "source_format": "cobertura"
      }
    ],
    "summary": {
      "total_files": 42,
      "files_with_coverage": 38,
      "overall_line_coverage_pct": 78.5,
      "overall_branch_coverage_pct": 65.2
    }
  }
}
```

## Gap Analysis

Coverage data is combined with complexity metrics (from lizard/scc) to identify high-risk files:

- High complexity + Low coverage = Priority testing target
- Risk score: `(ccn_norm * 0.6) + ((100 - coverage_pct) * 0.4)`

See `mart_coverage_gap_analysis` dbt model for the join logic.
