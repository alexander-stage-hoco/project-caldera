# Symbol Scanner

Python symbol extraction tool for Project Caldera. Extracts function/class definitions, call relationships, and imports from Python source code using the stdlib `ast` module.

## Purpose

Symbol Scanner enables:
- **Coupling analysis**: Identify tightly coupled modules via call relationships
- **Blast radius computation**: Determine what code is affected by changes
- **Dependency mapping**: Trace import relationships across files

## Quick Start

```bash
# Install dependencies
make setup

# Run analysis on default test repo
make analyze

# Run on custom repo
make analyze REPO_PATH=/path/to/repo REPO_NAME=my-repo

# Run evaluation
make evaluate

# Run tests
make test
```

## Output Format

The tool produces a JSON envelope with:

```json
{
  "metadata": {
    "tool_name": "symbol-scanner",
    "tool_version": "0.1.0",
    "run_id": "uuid",
    "repo_id": "uuid",
    "branch": "main",
    "commit": "40-char-sha",
    "timestamp": "ISO8601",
    "schema_version": "1.0.0"
  },
  "data": {
    "symbols": [...],
    "calls": [...],
    "imports": [...],
    "summary": {...}
  }
}
```

### Symbols

Each symbol entry contains:
- `path`: File path (repo-relative)
- `symbol_name`: Function/class/method name
- `symbol_type`: "function", "class", "method", or "variable"
- `line_start`, `line_end`: Source location
- `is_exported`: Whether symbol is public (no leading `_`)
- `parameters`: Number of parameters (for functions/methods)
- `parent_symbol`: Containing class name (for methods)
- `docstring`: Documentation string (if present)

### Calls

Each call entry contains:
- `caller_file`, `caller_symbol`: Where the call originates
- `callee_symbol`: What function/method is called
- `callee_file`: Resolved file (null if external/unresolved)
- `line_number`: Source location
- `call_type`: "direct", "dynamic", or "async"

### Imports

Each import entry contains:
- `file`: File path
- `imported_path`: Module path (e.g., "src.utils")
- `imported_symbols`: Comma-separated symbols (or null for `import x`)
- `import_type`: "static", "dynamic", "type_checking", or "side_effect"
- `line_number`: Source location

## Supported Languages

**Phase 1 (Current):** Python only
- Uses stdlib `ast` module for parsing
- No external dependencies for parsing

**Future Phases:**
- Phase 2: Enhanced call resolution
- Phase 3: JavaScript/TypeScript (tree-sitter)
- Phase 4: C# (Roslyn extension)
- Phase 5: Java/Go

## Evaluation

The tool includes:
- Programmatic evaluation against ground truth
- LLM judges for semantic accuracy
- Synthetic test repos covering edge cases

```bash
make evaluate        # Programmatic evaluation
make evaluate-llm    # LLM evaluation
```

## Architecture

```
symbol-scanner/
├── scripts/
│   ├── analyze.py              # CLI entry point
│   ├── evaluate.py             # Programmatic evaluation
│   └── extractors/
│       ├── base.py             # Abstract base extractor
│       └── python_extractor.py # Python AST implementation
├── schemas/
│   └── output.schema.json      # JSON schema for validation
├── evaluation/
│   ├── ground-truth/           # Expected outputs
│   └── llm/                    # LLM judge infrastructure
├── tests/
│   ├── unit/                   # Unit tests
│   └── integration/            # E2E tests
└── eval-repos/
    └── synthetic/              # Test repositories
```
