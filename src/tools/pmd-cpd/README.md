# PMD CPD (Copy/Paste Detector)

Token-based code duplication detection with semantic comparison capabilities for the DD Platform.

## Prerequisites

**Java 11+ is required** - PMD is a Java-based tool.

```bash
# macOS
brew install openjdk@17
# or: brew install temurin

# Ubuntu/Debian
sudo apt install openjdk-17-jdk

# Verify installation
java -version
```

## Quick Start

```bash
# One-time setup (downloads PMD 7.0.0)
make setup

# Run analysis
make analyze REPO_PATH=/path/to/repo REPO_NAME=myrepo

# Run with semantic mode (detects renamed variables)
make analyze-semantic REPO_PATH=/path/to/repo REPO_NAME=myrepo

# Run programmatic evaluation
make evaluate

# Run LLM evaluation
make evaluate-llm
```

## What PMD CPD Provides

| Metric | Description |
|--------|-------------|
| `duplications` | Array of detected duplicate blocks with token counts |
| `duplication_percentage` | Per-file and overall duplication percentage |
| `cross_file_clones` | Clones spanning multiple files |
| `files_involved` | List of files participating in each clone |
| `occurrences` | Specific locations (file, start_line, end_line) |

## Why PMD CPD?

PMD CPD offers unique advantages over string-based tools like jscpd:

| Feature | jscpd | PMD CPD |
|---------|-------|---------|
| Algorithm | String-based (Rabin-Karp) | Token-based analysis |
| Semantic Detection | No | Yes (`--ignore-identifiers`, `--ignore-literals`) |
| Type 2 Clones | Limited | Strong detection |
| Clone Types | Type 1 (exact) | Type 1 + Type 2 (renamed vars) |

**Key Capability:** PMD CPD can detect semantic duplicates where variable names differ but logic is identical - crucial for finding refactoring candidates.

## Directory Structure

```
pmd-cpd/
├── Makefile                    # Primary interface
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── scripts/
│   ├── analyze.py              # Main CPD runner + JSON normalizer
│   ├── evaluate.py             # Programmatic evaluation (28 checks)
│   ├── llm_evaluate.py         # LLM judge orchestrator
│   └── checks/                 # Evaluation checks
│       ├── __init__.py         # CheckResult dataclass
│       ├── accuracy.py         # AC-1 to AC-8
│       ├── coverage.py         # CV-1 to CV-8
│       ├── edge_cases.py       # EC-1 to EC-8
│       └── performance.py      # PF-1 to PF-4
├── eval-repos/
│   └── synthetic/              # Test files (7 languages × 7 categories)
├── evaluation/
│   ├── ground-truth/           # Expected clone data per language
│   └── llm/                    # LLM-as-a-Judge framework
│       ├── judges/             # 4 LLM judges
│       └── prompts/            # Prompt templates
└── output/                     # Generated results (gitignored)
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make setup` | Download PMD 7.0.0 and install Python deps |
| `make analyze` | Run standard CPD analysis |
| `make analyze-semantic` | Run with `--ignore-identifiers --ignore-literals` |
| `make evaluate` | Run 28 programmatic checks |
| `make evaluate-llm` | Run 4 LLM judges |
| `make test` | Run unit and integration tests |
| `make clean` | Remove generated files |

## Semantic Detection Mode

PMD CPD's unique feature is semantic duplicate detection:

```bash
# Standard mode - exact token matches only
make analyze REPO_PATH=./eval-repos/synthetic REPO_NAME=synthetic

# Semantic mode - ignores identifier names and literal values
make analyze-semantic REPO_PATH=./eval-repos/synthetic REPO_NAME=synthetic
```

**Example:** These two functions are duplicates in semantic mode:

```python
# Function A
def calculate_total(items, tax_rate):
    subtotal = sum(items)
    return subtotal * (1 + tax_rate)

# Function B (same logic, different names)
def compute_sum(products, vat):
    base = sum(products)
    return base * (1 + vat)
```

## Evaluation

### Programmatic Checks (28 total)

| Category | Checks | Weight | Focus |
|----------|--------|--------|-------|
| Accuracy (AC-1 to AC-8) | 8 | 40% | Clone count, line accuracy, cross-file, semantic |
| Coverage (CV-1 to CV-8) | 8 | 25% | 7 languages + multi-language |
| Edge Cases (EC-1 to EC-8) | 8 | 20% | Empty files, unicode, large files |
| Performance (PF-1 to PF-4) | 4 | 15% | Speed, memory, throughput |

### LLM Judges (4 total)

| Judge | Weight | Focus |
|-------|--------|-------|
| Duplication Accuracy | 35% | Are detected clones genuine? |
| Semantic Detection | 25% | Does `--ignore-identifiers` work? |
| Cross-File Detection | 20% | Are cross-file clones linked? |
| Actionability | 20% | Are reports useful for refactoring? |

## Test File Categories

Each of the 7 supported languages has these test files:

| File | Purpose | Expected |
|------|---------|----------|
| `no_duplication.*` | Clean code | 0 clones |
| `light_duplication.*` | Small clones (~15 lines) | 1-2 clones |
| `heavy_duplication.*` | Large blocks (30+ lines) | 3-5 clones |
| `cross_file_a.*` / `cross_file_b.*` | Cross-file clone | 1 clone (linked) |
| `semantic_dup_identifiers.*` | Same logic, different var names | 0 standard / 1 semantic |
| `semantic_dup_literals.*` | Same logic, different constants | 0 standard / 1 semantic |

## Output Schema

```json
{
  "metadata": {
    "version": "1.0",
    "cpd_version": "7.0.0",
    "minimum_tokens": 50,
    "semantic_mode": false
  },
  "summary": {
    "total_files": 42,
    "total_clones": 5,
    "duplication_percentage": 8.5,
    "cross_file_clone_count": 2
  },
  "files": [
    {
      "path": "src/utils.py",
      "duplicate_lines": 45,
      "duplication_percentage": 12.3,
      "duplicate_blocks": 2
    }
  ],
  "duplications": [
    {
      "clone_id": "CPD-0001",
      "lines": 25,
      "tokens": 150,
      "files_involved": ["src/a.py", "src/b.py"],
      "occurrences": [
        {"file": "src/a.py", "start_line": 10, "end_line": 34},
        {"file": "src/b.py", "start_line": 5, "end_line": 29}
      ],
      "code_fragment": "def process_data(...):\n    ..."
    }
  ],
  "statistics": {
    "cross_file_clones": 2,
    "by_language": {"python": 3, "java": 2}
  }
}
```

## Comparison with jscpd

| Aspect | jscpd | PMD CPD | Use When |
|--------|-------|---------|----------|
| Speed | Fast | Moderate | jscpd for quick scans |
| Languages | 150+ | 30+ | Either for our 7 targets |
| Type 1 Clones | Excellent | Excellent | Either |
| Type 2 Clones | Limited | Strong | CPD for semantic refactoring |
| Output Detail | Good | Detailed | CPD for in-depth analysis |

**Recommendation:** Use both tools as complementary:
- jscpd for fast initial scans and broad language coverage
- PMD CPD for semantic analysis and refactoring candidate detection

## Related Tools

- **jscpd**: String-based duplication detection (faster, wider language support)
- **scc**: File-level LOC metrics
- **lizard**: Function-level complexity (CCN)

## References

- [PMD CPD Documentation](https://pmd.github.io/latest/pmd_userdocs_cpd.html)
- [PMD GitHub](https://github.com/pmd/pmd)
- [Clone Detection Types](https://en.wikipedia.org/wiki/Duplicate_code#Types_of_code_clones)
