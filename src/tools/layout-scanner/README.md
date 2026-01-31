# Layout Scanner (Tool 0)

Fast filesystem-based repository layout scanner that creates a canonical registry of all files and directories with sophisticated file classification.

## Overview

The Layout Scanner is the foundational tool (Tool 0) in the Project Vulcan analysis pipeline. It runs before all other tools to establish:

- **Canonical File Registry**: Stable IDs for all files and directories
- **File Classification**: Multi-signal categorization (source, test, config, generated, docs, vendor, etc.)
- **Language Detection**: Programming language identification from extensions
- **Directory Metrics**: Direct and recursive counts, size rollups
- **Hierarchy Information**: Parent-child relationships, depth distribution

## Quick Start

```bash
# Setup environment
make setup

# Build synthetic test repositories
make build-repos

# Run layout scanner
make analyze

# Run evaluation
make evaluate
```

## Usage

### Command Line

```bash
# Basic scan
python -m scripts.layout_scanner /path/to/repo -o output.json

# With custom ignores
python -m scripts.layout_scanner /path/to/repo --ignore "*.log" --ignore "tmp/"

# With config file
python -m scripts.layout_scanner /path/to/repo --config .layout-scanner.json

# With custom rules (YAML)
python -m scripts.layout_scanner /path/to/repo --rules my-rules.yaml

# Enable git metadata enrichment
python -m scripts.layout_scanner /path/to/repo --git -o output.json

# Enable content metadata enrichment
python -m scripts.layout_scanner /path/to/repo --content -o output.json

# With validation
python -m scripts.layout_scanner /path/to/repo --validate --strict -o output.json

# Quiet mode (suppress progress)
python -m scripts.layout_scanner /path/to/repo -q
```

### CLI Reference

| Flag | Description |
|------|-------------|
| `-o, --output FILE` | Output JSON file path (default: stdout) |
| `--config FILE` | Path to JSON configuration file |
| `--rules FILE` | Path to YAML classification rules file |
| `--ignore PATTERN` | Additional patterns to ignore (repeatable) |
| `--no-gitignore` | Don't respect .gitignore |
| `--git` | Enable git metadata enrichment (commit dates, authors) |
| `--content` | Enable content metadata enrichment (line counts, hashes) |
| `--validate` | Validate output against JSON schema |
| `--strict` | Exit with error if validation fails (requires --validate) |
| `-v, --verbose` | Show detailed progress (classification/language distribution) |
| `-q, --quiet` | Suppress progress output to stderr |
| `--version` | Show version information |

### Python API

```python
from scripts import scan_repository

output, duration_ms = scan_repository("/path/to/repo")
print(f"Scanned {output['statistics']['total_files']} files in {duration_ms}ms")
```

## Configuration

Configuration can be provided via `.layout-scanner.json` in the repository root:

```json
{
  "classification": {
    "confidence_threshold": 0.5,
    "custom_rules": {
      "path": {
        "internal": ["internal/", "private/"]
      },
      "filename": {
        "test": ["*_spec.rb"]
      }
    },
    "override": {
      "src/legacy/": "source",
      "tools/codegen/": "generated"
    }
  },
  "ignore": {
    "additional_patterns": ["*.tmp", "*.bak"],
    "respect_gitignore": true
  }
}
```

### Config Priority

1. CLI flags (highest)
2. `.layout-scanner.json` in repo root
3. `~/.config/layout-scanner/config.json`
4. Built-in defaults (lowest)

## Rules Customization

For advanced classification customization, create a `.layout-scanner-rules.yaml` file in your repository root (auto-discovered) or use the `--rules` flag.

### YAML Rules Format

```yaml
version: "1.0"

# Override default signal weights
weights:
  path: 0.95
  filename: 0.85
  extension: 0.45

# Define subcategories for finer-grained classification
subcategories:
  test:
    - unit
    - integration
    - e2e
  config:
    - build
    - lint

# Path-based rules (supports subcategories)
path_rules:
  test::unit:
    - "tests/unit/"
    - "test/unit/"
  test::integration:
    - "tests/integration/"

# Filename patterns (regex)
filename_rules:
  test::benchmark:
    - "^benchmark_.*\\.py$"

# Extension rules
extension_rules:
  config:
    - ".toml"
    - ".cfg"
```

### Subcategories

Classifications can include subcategories using `::` syntax:

| Classification | Description |
|---------------|-------------|
| `test::unit` | Unit tests |
| `test::integration` | Integration tests |
| `test::e2e` | End-to-end tests |
| `config::build` | Build configuration |
| `config::lint` | Linter configuration |

Subcategory patterns are checked before base category patterns, so files in `tests/unit/` will be classified as `test::unit` rather than just `test`.

### Example Rules

See `examples/rules/` for language-specific rule files:
- `python-rules.yaml` - pytest, fixtures, benchmarks
- `javascript-rules.yaml` - Jest, Cypress, Playwright
- `dotnet-rules.yaml` - xUnit, NUnit, Designer files

## Output Schema

See `schemas/output.schema.json` for the envelope schema and `schemas/layout.json`
for the data section. `docs/SCHEMA.md` documents the data fields in detail.

### Envelope Structure

```json
{
  "metadata": {
    "tool_name": "layout-scanner",
    "tool_version": "1.0.0",
    "run_id": "11111111-1111-1111-1111-111111111111",
    "repo_id": "22222222-2222-2222-2222-222222222222",
    "branch": "main",
    "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "timestamp": "2026-01-10T14:30:52Z",
    "schema_version": "1.0.0"
  },
  "data": {
    "schema_version": "1.0",
    "tool": "layout-scanner",
    "tool_version": "1.0.0",
    "run_id": "layout-20260110-143052-myrepo",
    "timestamp": "2026-01-10T14:30:52Z",
    "repository": "myrepo",
    "repository_path": "/path/to/myrepo",
    "passes_completed": ["filesystem"],
    "statistics": { ... },
    "files": { ... },
    "directories": { ... },
    "hierarchy": { ... }
  }
}
```

### File Object

```json
{
  "id": "f-a3b2c1d4e5f6",
  "path": "src/main.py",
  "name": "main.py",
  "extension": ".py",
  "size_bytes": 2048,
  "modified_time": "2026-01-09T10:30:00Z",
  "is_symlink": false,
  "language": "python",
  "classification": "source",
  "classification_reason": "extension:.py",
  "classification_confidence": 0.95,
  "parent_directory_id": "d-123456789abc",
  "depth": 1
}
```

### Directory Object

```json
{
  "id": "d-123456789abc",
  "path": "src",
  "name": "src",
  "classification": "source",
  "classification_reason": "majority source (85%)",
  "direct_file_count": 5,
  "direct_directory_count": 2,
  "recursive_file_count": 150,
  "recursive_directory_count": 12,
  "direct_size_bytes": 10240,
  "recursive_size_bytes": 512000,
  "classification_distribution": {
    "source": 140,
    "test": 8,
    "config": 2
  },
  "language_distribution": {
    "python": 120,
    "javascript": 20,
    "json": 8
  }
}
```

## Classification Categories

| Category | Description | Example Signals |
|----------|-------------|-----------------|
| `source` | Production source code | Default for code extensions |
| `test` | Test files and fixtures | `tests/`, `*_test.py`, `*.spec.ts` |
| `config` | Configuration files | `.json`, `.yaml`, `Makefile` |
| `generated` | Auto-generated code | `*.g.cs`, `*.min.js`, `dist/` |
| `docs` | Documentation | `docs/`, `README.md`, `.md` |
| `vendor` | Third-party dependencies | `node_modules/`, `vendor/` |
| `build` | Build artifacts | `build/`, `out/`, `bin/` |
| `ci` | CI/CD configuration | `.github/`, `.gitlab-ci/` |
| `other` | Unclassified | Fallback |

## Multi-Signal Classification

The classifier uses multiple signals with weighted scoring:

1. **Path Rules** (weight 0.9): `vendor/`, `tests/`, `docs/`
2. **Filename Patterns** (weight 0.8): `test_*.py`, `*.spec.ts`
3. **Extension Rules** (weight 0.5): `.json`, `.md`

Confidence scores range from 0.0 to 1.0.

## Language Detection

The scanner uses multi-strategy language detection with fallback mechanisms.

### Detection Strategies (in priority order)

1. **go-enry** (optional): Full-featured detection using GitHub Linguist algorithms
   - Modeline detection (vim/emacs markers)
   - Filename matching (Makefile, Dockerfile)
   - Shebang parsing (`#!/usr/bin/env python`)
   - Extension matching
   - Content heuristics and Bayesian classifier

2. **Built-in Fallback**: When enry is unavailable
   - Extension-based mapping (50+ extensions)
   - Filename-based detection (Makefile, Dockerfile, etc.)
   - Shebang parsing for extensionless scripts

### Confidence Scoring

| Scenario | Confidence | Example |
|----------|------------|---------|
| Unambiguous extension | 0.95 | `.py` → Python |
| Filename match | 0.90 | `Makefile` → Makefile |
| Shebang detection | 0.90 | `#!/usr/bin/env ruby` → Ruby |
| Ambiguous extension | 0.60 | `.h` → C (alternatives: C++, Objective-C) |
| Unknown | 0.00 | `.xyz123` → unknown |

### Special File Detection

| Function | Description |
|----------|-------------|
| `is_binary_file()` | Detects binary files via magic bytes (PNG, JPEG, PDF, ELF, etc.) or null bytes |
| `is_vendor_file()` | Detects vendor paths (`node_modules/`, `vendor/`, `third_party/`) |
| `is_generated_file()` | Detects generated files (`.min.js`, `_pb2.py`, `package-lock.json`) |

### Supported Languages (50+)

Python, JavaScript, TypeScript, C#, Java, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, C, C++, Shell, PowerShell, Perl, Lua, R, SQL, HTML, CSS, SCSS, JSON, YAML, XML, Markdown, HCL, and more.

See `scripts/language_detector.py` for the complete extension mapping and `docs/LANGUAGE_DETECTION.md` for detailed documentation.

## Performance

| Repository Size | Expected Time | Files/Second |
|-----------------|---------------|--------------|
| < 1K files | < 0.1s | 10,000+ |
| 10K files | < 2s | 5,000+ |
| 100K files | < 10s | 10,000+ |

## Evaluation Framework

28 programmatic checks across 5 dimensions:

| Dimension | Checks | Focus |
|-----------|--------|-------|
| Output Quality | OQ-1 to OQ-8 | JSON validity, schema compliance |
| Accuracy | AC-1 to AC-8 | ID stability, counts, paths |
| Classification | CL-1 to CL-6 | File type detection |
| Performance | PF-1 to PF-4 | Speed benchmarks |
| Edge Cases | EC-1 to EC-6 | Unicode, symlinks, deep nesting |

Run evaluation with:

```bash
make evaluate
```

## Directory Structure

```
src/layout-scanner/
├── Makefile
├── README.md
├── pyproject.toml
├── scripts/
│   ├── __init__.py
│   ├── layout_scanner.py      # Main entry point
│   ├── tree_walker.py         # os.scandir traversal
│   ├── id_generator.py        # SHA-256 ID generation
│   ├── ignore_filter.py       # .gitignore parsing
│   ├── classifier.py          # Multi-signal classification
│   ├── language_detector.py   # Language detection (enry + fallback)
│   ├── hierarchy_builder.py   # Tree computation
│   ├── config_loader.py       # Config file parsing
│   ├── rule_loader.py         # YAML rules loading
│   ├── output_writer.py       # JSON serialization
│   ├── schema_validator.py    # Output validation
│   ├── evaluate.py            # Evaluation orchestrator
│   └── checks/                # Evaluation checks
├── rules/
│   └── default.yaml           # Default classification rules
├── schemas/
│   └── layout.json            # JSON Schema
├── docs/
│   └── SCHEMA.md              # Schema documentation
├── examples/
│   ├── configs/               # Example JSON configs
│   ├── rules/                 # Example YAML rules
│   └── outputs/               # Example output files
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── eval-repos/synthetic/      # Synthetic test repositories
├── evaluation/
│   ├── ground-truth/          # Expected values
│   └── results/               # Evaluation results
└── output/                    # Scanner output
```

## Integration with Collector

The Layout Scanner is designed to run as Phase 0 in the collector pipeline:

```python
from scripts import scan_repository

# Run layout scan first
layout, _ = scan_repository(repo_path)

# Pass file IDs to other tools
file_ids = {f["path"]: f["id"] for f in layout["files"].values()}
```

## References

- [Design Document](../../docs/core/LAYOUT_SCANNER_DESIGN.md)
- [Tool Catalog](../../docs/tools/TOOL_CATALOG.md)
