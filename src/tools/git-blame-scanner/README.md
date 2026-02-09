# git-blame-scanner

Per-file authorship metrics for knowledge concentration and bus factor analysis at the file level.

This tool analyzes git blame data to identify:
- Knowledge silos (files owned primarily by a single author)
- Bus factor risks (files with concentrated ownership)
- Code churn patterns (recent change activity)
- Author statistics across the repository

## Quick Start

```bash
# Setup
make setup

# Run analysis
make analyze REPO_PATH=/path/to/repo

# Run evaluation
make evaluate
```

## Output

Analysis produces `outputs/<run-id>/output.json` with:

```json
{
  "metadata": { ... },
  "data": {
    "files": [
      {
        "path": "src/main.py",
        "total_lines": 100,
        "unique_authors": 2,
        "top_author": "alice@example.com",
        "top_author_lines": 75,
        "top_author_pct": 75.0,
        "last_modified": "2026-01-15",
        "churn_30d": 5,
        "churn_90d": 15
      }
    ],
    "authors": [
      {
        "author_email": "alice@example.com",
        "total_files": 10,
        "total_lines": 500,
        "exclusive_files": 3,
        "avg_ownership_pct": 65.0
      }
    ],
    "summary": {
      "total_files_analyzed": 50,
      "total_authors": 5,
      "knowledge_silo_count": 8
    }
  }
}
```

## Key Metrics

| Metric | Description |
|--------|-------------|
| `top_author_pct` | Percentage of lines owned by the top contributor |
| `unique_authors` | Number of distinct authors for a file |
| `exclusive_files` | Files where an author is the only contributor |
| `churn_30d` / `churn_90d` | Line changes in the last 30/90 days |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| REPO_PATH | eval-repos/synthetic | Repository to analyze |
| OUTPUT_DIR | outputs/$(RUN_ID) | Output directory |

## Development

```bash
# Run tests
make test

# Run quick tests (stop on first failure)
make test-quick

# Clean outputs
make clean
```
