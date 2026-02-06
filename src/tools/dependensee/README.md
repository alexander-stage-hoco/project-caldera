# dependensee

> Brief description of what this tool does.

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
    "files": [...],
    "summary": { ... }
  }
}
```

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
