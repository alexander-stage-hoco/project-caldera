# DevSkim Security Linter

Microsoft's regex-based security analysis tool for detecting security vulnerabilities in code. Works on **non-compiling code** - ideal for due diligence scenarios with partial or incomplete codebases.

## Key Advantage

Unlike Roslyn-based tools, DevSkim uses regex patterns and doesn't require compilation, making it suitable for:
- Due diligence on incomplete codebases
- Code review without full build environment
- Quick security scans during development
- Multi-language security analysis

## Quick Start

```bash
# Setup DevSkim CLI and Python environment
make setup

# Run analysis
make analyze REPO_PATH=/path/to/repo REPO_NAME=myrepo

# Run evaluation
make evaluate

# View results
cat output/runs/myrepo.json | jq '.summary'
```

## Supported Languages

- C# (.NET)
- Python
- JavaScript/TypeScript
- Java
- Go
- C/C++
- COBOL

## Security Categories Detected

| Category | Description | Example Rules |
|----------|-------------|---------------|
| SQL Injection | SQL command construction vulnerabilities | DS126858, DS104456 |
| Hardcoded Secrets | Passwords, API keys, tokens in code | DS134411, DS114352 |
| Insecure Crypto | Weak algorithms (MD5, SHA1, DES, ECB) | DS161085, DS144436 |
| Path Traversal | Directory traversal vulnerabilities | DS175862, DS162155 |
| XSS | Cross-site scripting vulnerabilities | DS137138, DS126188 |
| Deserialization | Insecure deserialization (BinaryFormatter) | DS113853, DS162963 |
| XXE | XML external entity injection | DS131307, DS132956 |
| Command Injection | OS command injection | DS112860, DS117840 |

## Output Schema (v2.0)

```json
{
  "metadata": {
    "schema_version": "2.0",
    "run_id": "devskim-20260118-143000",
    "timestamp": "2026-01-18T14:30:00Z",
    "devskim_version": "1.0.0",
    "rules_used": ["DS126858", "DS134411", ...]
  },
  "summary": {
    "total_files": 43,
    "files_with_issues": 15,
    "total_issues": 87,
    "issues_by_category": {
      "sql_injection": 12,
      "hardcoded_secret": 8
    },
    "issues_by_severity": {
      "CRITICAL": 20,
      "HIGH": 35
    }
  },
  "directories": [...],
  "files": [...],
  "statistics": {...}
}
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `setup` | Install DevSkim CLI and Python dependencies |
| `analyze` | Run DevSkim on target repository |
| `evaluate` | Run programmatic evaluation against ground truth |
| `test` | Run pytest suite |
| `clean` | Remove generated files |

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | `eval-repos/synthetic` | Path to repository |
| `REPO_NAME` | `synthetic` | Repository name for output |
| `OUTPUT_DIR` | `output/runs` | Output directory |

## Evaluation Framework

28 programmatic checks across 4 categories:

### Accuracy (AC-1 to AC-8)
- SQL injection detection
- Hardcoded secrets detection
- Insecure crypto detection
- Path traversal detection
- XSS detection
- Deserialization detection
- False positive rate
- Overall precision/recall

### Coverage (CV-1 to CV-8)
- C# coverage
- Python coverage
- JavaScript coverage
- Java coverage
- Go coverage
- C/C++ coverage
- Multi-language support
- DD security category coverage

### Edge Cases (EC-1 to EC-8)
- Empty files handling
- Large files handling
- Mixed content files
- Nested code handling
- Comment handling
- String literal handling
- Minified code handling
- Non-UTF8 encoding handling

### Performance (PF-1 to PF-4)
- Analysis duration
- Files per second throughput
- Lines per second throughput
- Result completeness

## Comparison with Semgrep

| Aspect | DevSkim | Semgrep |
|--------|---------|---------|
| Detection Method | Regex patterns | AST patterns |
| Build Required | No | No |
| C# Support | Full | Full |
| Custom Rules | JSON/Regex | YAML/Pattern |
| Focus | Security only | Security + smells |
| False Positives | Higher (regex) | Lower (AST) |
| Speed | Faster | Slower (rule download) |

**Complementary Use:** DevSkim for quick security scanning, Semgrep for comprehensive smell detection.

## Directory Structure

```
devskim/
├── Makefile
├── README.md
├── BLUEPRINT.md
├── requirements.txt
├── scripts/
│   ├── security_analyzer.py
│   ├── evaluate.py
│   └── checks/
│       ├── __init__.py
│       ├── accuracy.py
│       ├── coverage.py
│       ├── edge_cases.py
│       └── performance.py
├── eval-repos/
│   └── synthetic/csharp/
├── evaluation/
│   ├── ground-truth/
│   └── results/
└── output/
    └── runs/
```

## Installation

DevSkim CLI requires .NET SDK:

```bash
# Install .NET SDK (if not already installed)
# macOS
brew install dotnet

# Linux
wget https://dot.net/v1/dotnet-install.sh
./dotnet-install.sh --channel 6.0

# Install DevSkim CLI
dotnet tool install --global Microsoft.CST.DevSkim.CLI
```

## License

MIT (same as DevSkim)
