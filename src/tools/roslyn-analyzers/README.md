# PoC #20: Roslyn Analyzers (.NET Code Quality Analysis)

Proof of concept for evaluating Roslyn Analyzers for .NET code quality and security analysis in due diligence workflows.

## Overview

Roslyn Analyzers are built into the .NET SDK and provide 200+ rules for:
- **Security vulnerabilities** (SQL injection, XSS, weak crypto, insecure deserialization)
- **Design violations** (visible fields, empty interfaces, god classes)
- **Resource management** (undisposed objects, missing cancellation tokens)
- **Dead code** (unused imports, parameters, fields, locals)
- **Performance** (inefficient LINQ, unnecessary allocations)

## Quick Start

```bash
# Prerequisites: .NET SDK 8.0+
dotnet --version

# Setup and run
make setup    # Install Python dependencies
make build    # Build synthetic C# project
make analyze  # Run analysis with dashboard
make evaluate # Run programmatic evaluation
```

## DD Analyzer Lens Coverage

| Lens | Coverage | Roslyn Rules |
|------|----------|--------------|
| L1 (Structural) | Design violations | CA1051, CA1040, CA1502, CA1506 |
| L2 (Tech Debt) | Dead code + resources | IDE0005, IDE0060, CA2000, CA1001 |
| L6 (Quality) | Comprehensive rules | 44 rules across 5 categories |
| L7 (Security) | OWASP Top 10 | CA3001, CA3002, CA5350, CA2300-2315 |

## Evaluation Framework

### Dual-Track Evaluation (60% Programmatic + 40% LLM)

**Programmatic (28 checks):**
- Accuracy: 10 checks (SQL injection, XSS, secrets, crypto, deserialization, disposal, dead code, design, precision, recall)
- Coverage: 8 checks (rule coverage per category, file coverage, line precision)
- Edge Cases: 8 checks (empty files, unicode, large files, false positives)
- Performance: 4 checks (speed, efficiency, throughput, memory)

**LLM Judges (4 dimensions):**
- Detection Accuracy (35%): Security/design/resource/dead_code accuracy
- Security Coverage (25%): OWASP coverage, .NET-specific patterns
- False Positive Rate (20%): Clean file analysis, safe pattern recognition
- Actionability (20%): Message clarity, fix suggestions, prioritization

### Decision Thresholds

| Decision | Combined Score |
|----------|----------------|
| STRONG_PASS | >= 0.80 |
| PASS | >= 0.70 |
| WEAK_PASS | >= 0.60 |
| FAIL | < 0.60 |

## Directory Structure

```
poc-roslyn-analyzers/
├── Makefile                     # Primary interface
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── eval-repos/
│   ├── synthetic/csharp/        # Controlled test files
│   │   ├── security/            # SQL injection, XSS, crypto, etc.
│   │   ├── design/              # God class, visible fields, etc.
│   │   ├── resource/            # Undisposed objects, etc.
│   │   ├── performance/         # Inefficient LINQ, etc.
│   │   ├── dead_code/           # Unused imports, fields, etc.
│   │   └── clean/               # False positive tests
│   └── real/                    # Real OSS repos (submodules)
├── evaluation/
│   ├── ground-truth/            # Expected violations
│   │   └── csharp.json
│   └── llm/
│       ├── judges/              # LLM judge implementations
│       ├── prompts/             # Judge prompt templates
│       └── results/             # Evaluation outputs
├── scripts/
│   ├── roslyn_analyzer.py       # Main analysis script
│   ├── evaluate.py              # Programmatic evaluation
│   ├── llm_evaluate.py          # LLM evaluation orchestrator
│   └── checks/                  # Programmatic check implementations
└── output/runs/                 # Analysis outputs
```

## Roslyn Rules Covered (44 rules)

### Security (15 rules)
| Rule | Description | Severity |
|------|-------------|----------|
| CA3001 | SQL Injection | CRITICAL |
| CA3002 | XSS | CRITICAL |
| CA2100 | SQL (legacy) | CRITICAL |
| CA5350 | Weak Crypto (DES, 3DES) | HIGH |
| CA5351 | Broken Crypto (MD5) | HIGH |
| CA5385 | RSA Key Size < 2048 | HIGH |
| CA5390 | Hardcoded Keys | HIGH |
| CA5364 | Deprecated TLS | HIGH |
| CA5397 | Deprecated SSL | HIGH |
| CA2300-CA2315 | Insecure Deserialization | CRITICAL |
| CA3147 | Missing CSRF | MEDIUM |
| CA5391 | Missing Antiforgery | MEDIUM |

### Design (12 rules)
| Rule | Description | Severity |
|------|-------------|----------|
| CA1051 | Visible Instance Fields | HIGH |
| CA1040 | Empty Interfaces | MEDIUM |
| CA1001 | Missing IDisposable | HIGH |
| CA1063 | Improper IDisposable | HIGH |
| CA1502 | Excessive Complexity | HIGH |
| CA1506 | Excessive Coupling | HIGH |

### Resource Management (6 rules)
| Rule | Description | Severity |
|------|-------------|----------|
| CA2000 | Objects Not Disposed | HIGH |
| CA2016 | Missing CancellationToken | MEDIUM |
| CA2007 | Task Await Issues | MEDIUM |

### Dead Code (6 rules)
| Rule | Description | Severity |
|------|-------------|----------|
| IDE0005 | Unused Imports | MEDIUM |
| IDE0060 | Unused Parameters | MEDIUM |
| CA1801 | Unused Parameters | MEDIUM |
| IDE0052 | Unused Private Members | MEDIUM |
| IDE0059 | Unused Locals | LOW |
| CA1812 | Uninstantiated Classes | LOW |

### Performance (5 rules)
| Rule | Description | Severity |
|------|-------------|----------|
| CA1826 | LINQ Alternatives | LOW |
| CA1829 | Length/Count Property | LOW |
| CA1825 | Empty Array Allocation | LOW |

## Output Format

Analysis outputs are in JSON format compatible with DD Analyzer:

```json
{
  "metadata": {
    "tool": "roslyn-analyzers",
    "timestamp": "2026-01-06T10:30:00Z",
    "target_path": "/path/to/project"
  },
  "summary": {
    "total_files_analyzed": 25,
    "total_violations": 113,
    "violations_by_category": {
      "security": 31,
      "design": 22,
      "resource": 22,
      "performance": 16,
      "dead_code": 22
    }
  },
  "files": [...]
}
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make setup` | Install dependencies |
| `make build` | Build synthetic C# project |
| `make analyze` | Run Roslyn analysis |
| `make evaluate` | Run programmatic evaluation |
| `make evaluate-llm` | Run LLM evaluation (Claude CLI, model = opus-4.5) |
| `make evaluate-combined` | Combined evaluation |
| `make clean` | Remove generated files |

## Evaluation Results

### Programmatic Evaluation: 100% (30/30 checks)

All checks passing across security, design, resource management, dead code, and performance.

### LLM Evaluation (Claude Opus 4.5): 4.45/5.0 STRONG_PASS

| Judge | Weight | Score | Confidence |
|-------|--------|-------|------------|
| security_detection | 35% | 4/5 | 90% |
| design_analysis | 25% | 4/5 | 85% |
| resource_management | 20% | 5/5 | 95% |
| overall_quality | 20% | 5/5 | 92% |

**Key Findings:**
- Excellent resource management detection (undisposed objects, cancellation tokens)
- Strong security detection (SQL injection, XSS, weak crypto)
- Comprehensive design violation coverage
- Minor gaps in some C#-specific async patterns

**Decision: STRONG_PASS** - Approved for DD Platform integration.

## CLI Options

The analyzer script supports the following options:

```bash
python scripts/roslyn_analyzer.py <target_path> [options]

Options:
  --output, -o         Output JSON file path
  --no-color           Disable colored output
  --build-timeout      Build timeout in seconds (default: 900 = 15 min)
  --interactive        Interactive mode (not yet implemented)
```

### Build Timeout Configuration

For large .NET solutions, the default 900-second (15 min) build timeout may need adjustment:

```bash
# Via CLI
python scripts/roslyn_analyzer.py /path/to/repo --output result.json --build-timeout 1800

# Via Makefile
make analyze BUILD_TIMEOUT=1800
```

### Error Handling

The analyzer now provides detailed feedback on build failures:
- **Build failure warnings**: Shows truncated build output when a project fails
- **SARIF missing warnings**: Indicates when no analyzer output was generated
- **Build summary**: Reports how many projects failed out of total

## Prerequisites

- .NET SDK 8.0 or later
- Python 3.10+
- (Optional) Anthropic API key for LLM evaluation
