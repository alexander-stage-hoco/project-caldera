# Layout Scanner Evaluation Strategy

This document describes the comprehensive evaluation framework for the Layout Scanner tool, including the complete check catalog, scoring methodology, weight allocation, and decision thresholds.

## Philosophy & Approach

The Layout Scanner is the **canonical source of file IDs** for all downstream analysis tools. Its evaluation is critical because errors here propagate to every other tool in the pipeline. The scanner provides:

- **File discovery and enumeration** - Complete inventory of all files in a repository
- **Language detection** - Programming language identification for each file
- **File classification** - Categorization into source, test, config, generated, docs, vendor
- **Directory hierarchy analysis** - Parent-child relationships and recursive rollups
- **Git metadata enrichment** (optional) - Commit history, authors, dates
- **Content metadata extraction** (optional) - Hashes, line counts, binary detection

### Version History

| Version | Dimensions | Programmatic Checks | LLM Judges | Core Weight | Extended Weight |
|---------|------------|---------------------|------------|-------------|-----------------|
| v1.0 (Original) | 5 | 32 | 0 | 100% | - |
| v2.0 (Extended) | 7 | 51 | 4 | 70% | 30% |

### Key Changes in v2.0

1. **New Dimensions Added:**
   - Git Metadata (GT-1 to GT-6) - Optional dimension
   - Content Metadata (CT-1 to CT-6) - Optional dimension
   - SCC Comparison (SCC-1 to SCC-4) - Cross-tool validation

2. **LLM-as-Judge Integration:**
   - 4 LLM judges added for semantic evaluation
   - 70% programmatic / 30% LLM hybrid scoring

3. **Enhanced Classification Checks:**
   - Added CL-7 (Shebang Detection), CL-8 (Content Disambiguation), CL-9 (Detection Capabilities)

---

## Why Hybrid Evaluation?

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 70% | Objective, reproducible, fast |
| LLM Judges | 30% | Semantic understanding of classification choices |

This hybrid approach validates both technical accuracy and practical usefulness.

### Rationale for 70/30 Split

**Programmatic checks (70%)** ensure:
- Deterministic, reproducible results across runs
- Fast feedback during development
- Clear pass/fail criteria for CI/CD gates
- Objective measurement against ground truth

**LLM judges (30%)** provide:
- Semantic understanding of classification decisions
- Assessment of directory taxonomy quality
- Nuanced evaluation of edge cases
- Detection of subtle hierarchy issues

### Canonical File Registry Guarantees

Layout Scanner provides these guarantees to downstream tools:

1. **Unique file IDs**: Every file has a unique, stable identifier (format: `f-XXXXXXXXXXXX`)
2. **Consistent paths**: All paths are normalized (relative, forward-slash, no `.` or `..`)
3. **Complete hierarchy**: Parent-child relationships are bidirectional and consistent
4. **Accurate counts**: Statistics match actual data in all sections
5. **Deterministic output**: Same input always produces same output

---

## Dimension Summary

All evaluation dimensions with their check counts and weights:

| Dimension | Code | Checks | Weight | Category | Focus Area |
|-----------|------|--------|--------|----------|------------|
| Output Quality | OQ | 8 | 25% | Core | JSON structure, schema compliance |
| Accuracy | AC | 8 | 25% | Core | File/directory counts, paths |
| Classification | CL | 9 | 20% | Core | Category assignment, language detection |
| Performance | PF | 5 | 15% | Core | Execution speed, throughput |
| Edge Cases | EC | 6 | 15% | Core | Robustness, error handling |
| Git Metadata | GT | 6 | 0%* | Optional | Git information enrichment |
| Content Metadata | CT | 6 | 0%* | Optional | File content analysis |
| SCC Comparison | SCC | 4 | Validation | Cross-tool | Language detection agreement |

**Total**: 52 programmatic checks + 4 LLM judges

*Git Metadata and Content Metadata are optional dimensions, weighted separately when their passes are enabled.

---

## Complete Check Catalog

### 1. Output Quality (OQ) - 25% Weight

Validates JSON structure, schema compliance, and data integrity.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| OQ-1 | JSON Valid | Output has all required top-level keys | Keys: `schema_version`, `tool`, `tool_version`, `run_id`, `timestamp`, `repository`, `statistics`, `files`, `directories`, `hierarchy` |
| OQ-2 | Schema Compliant | Output validates against JSON schema | Zero validation errors |
| OQ-3 | Files Present | Files section exists with valid structure | All files have `id`, `path`, `name`, `classification` |
| OQ-4 | Directories Present | Directories section exists with valid structure | All directories have `id`, `path`, `name`, `classification` |
| OQ-5 | Hierarchy Valid | Parent-child relationships are consistent | All referenced IDs exist, no orphans |
| OQ-6 | IDs Unique | All file and directory IDs unique | No duplicate IDs across files and directories |
| OQ-7 | IDs Format | IDs follow expected format | Files: `f-XXXXXXXXXXXX`, Directories: `d-XXXXXXXXXXXX` (14 chars) |
| OQ-8 | Statistics Accurate | Statistics match actual data | `total_files == len(files)`, `total_directories == len(directories)`, classification sums match |

**Scoring Table:**

| Checks Passed | Score |
|---------------|-------|
| 8 | 5.0 |
| 7 | 4.0 |
| 5-6 | 3.0 |
| 3-4 | 2.0 |
| 0-2 | 1.0 |

---

### 2. Accuracy (AC) - 25% Weight

Validates counts, paths, and structural accuracy against ground truth.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| AC-1 | File Count | Total files matches ground truth | `actual == expected` (with tolerance if specified) |
| AC-2 | Directory Count | Total directories matches ground truth | `actual == expected` (with tolerance if specified) |
| AC-3 | Path Normalization | All paths are normalized | Relative paths, forward slashes, no `.`, `..`, or leading `/` |
| AC-4 | Size Accuracy | File sizes are valid and totals match | All sizes >= 0, sum matches statistics |
| AC-5 | Depth Calculation | Nesting depths are correct | `depth == path.count('/')` for all items |
| AC-6 | Parent Links | Parent references are correct | All files have valid `parent_directory_id` |
| AC-7 | Child Lists | Child lists are complete and accurate | `child_file_ids` and `child_directory_ids` match actual children |
| AC-8 | Recursive Counts | Recursive counts sum correctly | `recursive_file_count >= direct_file_count` for all directories |

**Scoring Table:**

| Checks Passed | Score |
|---------------|-------|
| 8 | 5.0 |
| 7 | 4.0 |
| 5-6 | 3.0 |
| 3-4 | 2.0 |
| 0-2 | 1.0 |

---

### 3. Classification (CL) - 20% Weight

Validates file classification into categories and language detection accuracy.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| CL-1 | Test Detection | Test files correctly classified | Files in `tests/`, `test/`, `__tests__/` with test patterns detected |
| CL-2 | Config Detection | Config files correctly classified | `Makefile`, `Dockerfile`, `.gitignore`, `package.json`, etc. |
| CL-3 | Generated Detection | Generated files correctly classified | `.g.cs`, `.generated.`, `.min.js`, `_pb2.py`, lock files |
| CL-4 | Vendor Detection | Vendor directories correctly classified | `node_modules/`, `vendor/`, `third_party/` |
| CL-5 | Docs Detection | Documentation files correctly classified | `README.md`, `CHANGELOG.md`, files in `docs/` |
| CL-6 | Language Detection | Languages detected from extensions | `.py`->Python, `.js`->JavaScript, `.cs`->C#, etc. |
| CL-7 | Shebang Detection | Language detected from shebang lines | `#!/usr/bin/env python` -> Python (requires enry) |
| CL-8 | Content Disambiguation | Ambiguous extensions resolved by content | `.h` files -> C vs C++ vs Objective-C (requires enry) |
| CL-9 | Detection Capabilities | Language detection strategies available | Reports enry/tree-sitter availability |

**Scoring Table:**

| Checks Passed | Score |
|---------------|-------|
| 9 | 5.0 |
| 8 | 4.5 |
| 7 | 4.0 |
| 5-6 | 3.0 |
| 3-4 | 2.0 |
| 0-2 | 1.0 |

---

### 4. Performance (PF) - 15% Weight

Validates execution speed and efficiency.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| PF-1 | Small Repo Speed | <1K files scanned in <0.5s | `duration_ms < 500` for files < 1000 |
| PF-2 | Medium Repo Speed | 1K-10K files scanned in <2s | `duration_ms < 2000` for files 1K-10K |
| PF-3 | Large Repo Speed | 10K-100K files scanned in <10s | `duration_ms < 10000` for files 10K-100K |
| PF-4 | Files Per Second | Reasonable throughput maintained | >= 1000 files/second for large repos, tiered for smaller |
| PF-5 | Deep Nesting Performance | Handles >20 levels efficiently | O(n) complexity maintained, no exponential slowdown |

**Performance Thresholds:**

| Repo Size | Files | Max Time | Min Files/Sec |
|-----------|-------|----------|---------------|
| Small | < 1,000 | 500ms | 25* |
| Medium | 1K - 10K | 2,000ms | 500 |
| Large | 10K - 100K | 10,000ms | 1,000 |

*Small repos have higher overhead due to startup costs.

**Scoring Table:**

| Checks Passed | Score |
|---------------|-------|
| 5 | 5.0 |
| 4 | 4.0 |
| 3 | 3.0 |
| 2 | 2.0 |
| 0-1 | 1.0 |

---

### 5. Edge Cases (EC) - 15% Weight

Validates handling of special cases and unusual inputs.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| EC-1 | Empty Directories | Empty directories included with 0 counts | Empty dirs have `direct_file_count=0`, `recursive_file_count=0` |
| EC-2 | Hidden Files | Dotfiles processed correctly | `.gitignore`, `.env` detected with valid structure |
| EC-3 | Symlinks | Symbolic links detected and marked | `is_symlink` field present on all items, symlinks detected |
| EC-4 | Unicode Paths | Unicode filenames handled | No encoding errors, valid structure maintained |
| EC-5 | Deep Nesting | Deep directories (20+ levels) handled | Depth values correct for deeply nested items |
| EC-6 | Special Characters | Spaces and special chars in paths | Paths with `' " & ( ) [ ] { } $ # @ !` handled correctly |

**Scoring Table:**

| Checks Passed | Score |
|---------------|-------|
| 6 | 5.0 |
| 5 | 4.0 |
| 4 | 3.0 |
| 2-3 | 2.0 |
| 0-1 | 1.0 |

---

### 6. Git Metadata (GT) - Optional Dimension

Validates git metadata enrichment when the `git` pass is enabled. Only runs when `"git"` is in `passes_completed`.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| GT-1 | Git Pass Recorded | Pass recorded in `passes_completed` | `"git"` in passes list |
| GT-2 | Dates Valid ISO 8601 | All git dates are valid format | Matches `YYYY-MM-DDTHH:MM:SS` with optional timezone |
| GT-3 | Date Ordering | `first_commit_date <= last_commit_date` | Chronological ordering for all files |
| GT-4 | Commit Count Valid | `commit_count` is positive integer or null | Non-negative integer for tracked files |
| GT-5 | Author Count Valid | `author_count` is positive integer or null | Non-negative integer for tracked files |
| GT-6 | Git Coverage | >50% of files have git metadata | `files_with_git / total_files >= 0.5` |

**Scoring Table:**

| Checks Passed | Score |
|---------------|-------|
| 6 | 5.0 |
| 5 | 4.0 |
| 4 | 3.0 |
| 2-3 | 2.0 |
| 0-1 | 1.0 |

---

### 7. Content Metadata (CT) - Optional Dimension

Validates content metadata enrichment when the `content` pass is enabled. Only runs when `"content"` is in `passes_completed`.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| CT-1 | Content Pass Recorded | Pass recorded in `passes_completed` | `"content"` in passes list |
| CT-2 | Hashes Valid Hex | All `content_hash` values are valid | SHA-256 (64 chars), SHA-1 (40 chars), or MD5 (32 chars) |
| CT-3 | Line Counts Valid | `line_count` is non-negative or null | Integer >= 0 or null for binary files |
| CT-4 | Binary/Text Consistency | Binary files have null line_count | Binary: `line_count=null`, Text: `line_count >= 0` |
| CT-5 | Text File Coverage | >90% of text files have line counts | High coverage for `is_binary=false` files |
| CT-6 | Hash Consistency | Content hashes are unique per content | Duplicate hashes only for identical files |

**Scoring Table:**

| Checks Passed | Score |
|---------------|-------|
| 6 | 5.0 |
| 5 | 4.0 |
| 4 | 3.0 |
| 2-3 | 2.0 |
| 0-1 | 1.0 |

---

### 8. SCC Comparison (SCC) - Validation Dimension

Cross-validates Layout Scanner output against SCC (Succinct Code Counter) for language detection agreement.

| Check ID | Name | Description | Pass Criteria |
|----------|------|-------------|---------------|
| SCC-1 | Total File Count | Layout counts >= SCC counts | Layout may count more (includes non-code files) |
| SCC-2 | Language Detection Coverage | All SCC languages detected | No languages in SCC missing from Layout |
| SCC-3 | Language Count Accuracy | Counts within 10% tolerance | 80%+ of common languages within tolerance |
| SCC-4 | Major Language Agreement | Languages >5% of files have exact match | Major languages (>5% of files) match exactly |

**Note:** SCC comparison is a validation dimension, not weighted in the primary score. It validates agreement with an industry-standard code counter.

---

## LLM Judge Dimensions (4 Judges)

### Judge Weights

| Judge | Weight | Focus |
|-------|--------|-------|
| Directory Taxonomy | 25% | Classification accuracy, distribution rollups |
| Hierarchy Consistency | 25% | Parent-child relationships, tree integrity |
| Language Detection | 25% | Programming language identification accuracy |
| Classification Reasoning | 25% | Source/test/config decision quality |

### Directory Taxonomy Judge (25%)

**Sub-dimensions:**
- **Classification Accuracy (40%)**: Do directory classifications match content?
- **Distribution Rollups (30%)**: Are `classification_distribution` counts accurate?
- **Language Distribution (30%)**: Are `language_distribution` counts accurate?

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | All directories correctly classified, distributions accurate, rollups consistent |
| 4 | 95%+ directories correct, minor distribution discrepancies |
| 3 | 85%+ directories correct, some rollup issues |
| 2 | 70%+ directories correct, significant distribution errors |
| 1 | <70% correct, distributions unreliable |

### Hierarchy Consistency Judge (25%)

**Sub-dimensions:**
- **Bidirectional Links (40%)**: Parent-child relationships consistent both ways
- **Root Integrity (30%)**: Single root, complete tree from root
- **No Orphans (30%)**: All files reachable from root

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Perfect consistency, complete hierarchy, no orphans |
| 4 | Minor link issues, tree otherwise complete |
| 3 | Some orphaned nodes, tree mostly navigable |
| 2 | Significant hierarchy gaps |
| 1 | Broken hierarchy, navigation unreliable |

### Language Detection Judge (25%)

**Sub-dimensions:**
- **Primary Language Correct (50%)**: Main language of each file identified
- **Secondary Languages (30%)**: Multi-language files handled (e.g., `.vue`, `.jsx`)
- **Edge Cases (20%)**: Polyglot files, generated code, uncommon languages

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | All languages correctly identified, edge cases handled |
| 4 | Primary correct, minor secondary issues |
| 3 | Primary correct, secondary gaps |
| 2 | Primary language misidentified for some files |
| 1 | Language detection unreliable |

### Classification Reasoning Judge (25%)

**Sub-dimensions:**
- **Source/Test Separation (50%)**: Correct distinction between source and test files
- **Config Identification (30%)**: Build, deploy, environment configs detected
- **Documentation (20%)**: READMEs, docs, inline comments recognized

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | All categories correctly assigned with clear reasoning |
| 4 | Minor misclassifications, reasoning mostly sound |
| 3 | Some confusion between categories |
| 2 | Systematic misclassification patterns |
| 1 | Classification not useful for downstream tools |

---

## Scoring Methodology

### Per-Dimension Score Calculation

1. Run all checks for the dimension
2. Count passed checks
3. Map to 1-5 score using dimension-specific scoring table
4. Multiply by dimension weight to get weighted score

```python
dimension_score = SCORING_TABLES[category][passed_count]
weighted_score = dimension_score * DIMENSION_WEIGHTS[category]
```

### Total Score Calculation

```python
# For programmatic dimensions
programmatic_score = sum(d.score * d.weight for d in core_dimensions)

# Normalize to 1-5 scale (programmatic is 0-1 weighted)
programmatic_normalized = 1 + (programmatic_score * 4)  # 0-1 -> 1-5

# LLM judge score (already 1-5)
llm_score = sum(j.score * j.weight for j in judges)

# Combined score (70/30 split)
combined_score = (0.70 * programmatic_normalized) + (0.30 * llm_score)
```

### Optional Dimension Handling

When optional passes (git, content) are enabled:

```python
# Recalculate weights to include optional dimensions
if has_git_pass:
    # Redistribute weights: core dimensions reduce proportionally
    # Git metadata gets 10% of total weight

if has_content_pass:
    # Content metadata gets 10% of total weight
```

---

## Decision Thresholds

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| **STRONG_PASS** | >= 4.0 | Excellent, production-ready, approved for immediate use |
| **PASS** | >= 3.5 | Good, minor improvements needed, approved with reservations |
| **WEAK_PASS** | >= 3.0 | Acceptable with caveats, review failing checks |
| **FAIL** | < 3.0 | Significant issues, does not meet requirements |

### Decision Logic

```python
def get_decision(overall_score: float) -> str:
    if overall_score >= 4.0:
        return "STRONG_PASS"
    elif overall_score >= 3.5:
        return "PASS"
    elif overall_score >= 3.0:
        return "WEAK_PASS"
    else:
        return "FAIL"
```

---

## Weight Allocation Rationale

### Core Dimensions (100% when LLM disabled, 70% when enabled)

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Output Quality | 25% | Highest priority - unusable if output is malformed |
| Accuracy | 25% | Critical for downstream tools - counts must match |
| Classification | 20% | Important for filtering and routing in pipeline |
| Performance | 15% | Must meet latency requirements for large repos |
| Edge Cases | 15% | Production stability requires robust edge case handling |

### LLM Judge Dimensions (30% when enabled)

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Directory Taxonomy | 25% | Semantic validation of classification choices |
| Hierarchy Consistency | 25% | Tree integrity for navigation |
| Language Detection | 25% | Accurate language identification for scc/lizard |
| Classification Reasoning | 25% | Quality of category assignments |

---

## Ground Truth Requirements

### Ground Truth Schema

```json
{
  "schema_version": "1.0",
  "scenario": "polyglot",
  "repository": "polyglot-project",
  "description": "Multi-language repository with various file types",
  "expected": {
    "total_files": 25,
    "total_directories": 8,
    "classifications": {
      "source": 15,
      "test": 5,
      "config": 3,
      "docs": 2
    },
    "languages": {
      "python": 8,
      "javascript": 7,
      "typescript": 5
    },
    "specific_files": {
      "src/main.py": {
        "classification": "source",
        "language": "python"
      },
      "tests/test_main.py": {
        "classification": "test",
        "language": "python"
      }
    }
  },
  "thresholds": {
    "count_tolerance": 0,
    "classification_f1_min": 0.9,
    "max_scan_time_seconds": 1.0
  },
  "required_paths": [
    "src/main.py",
    "README.md",
    "package.json"
  ]
}
```

### Synthetic Test Repositories

| Repo | Type | Purpose | Expected |
|------|------|---------|----------|
| minimal | Basic | Minimal valid structure | 5 files, 2 dirs |
| polyglot | Multi-lang | Multiple programming languages | Language detection |
| deep-nesting | Stress | 25-level deep directories | Performance test |
| unicode-paths | Edge | Unicode in file/dir names | Encoding handling |
| large-repo | Scale | 10,000+ files | Throughput test |
| monorepo | Complex | Multiple packages/projects | Classification accuracy |
| edge-cases | Robustness | Symlinks, empty dirs, special chars | Error handling |

### Ground Truth Location

```
evaluation/ground-truth/
  minimal.json
  polyglot.json
  deep-nesting.json
  unicode-paths.json
  large-repo.json
  monorepo.json
  edge-cases.json
```

---

## Running Evaluation

### Setup

```bash
cd src/tools/layout-scanner
make setup
```

### Run Analysis on Synthetic Repos

```bash
# Analyze all synthetic repos
make analyze

# Analyze specific repo
make analyze REPO_PATH=eval-repos/synthetic/polyglot REPO_NAME=polyglot
```

### Run Programmatic Evaluation

```bash
# Run full evaluation
make evaluate

# Verbose output
make evaluate VERBOSE=1

# With ground truth
make evaluate GROUND_TRUTH=evaluation/ground-truth/polyglot.json
```

### Run LLM Evaluation

```bash
# Full LLM evaluation (4 judges)
make evaluate-llm

# Specific model
make evaluate-llm MODEL=sonnet

# Single judge
make evaluate-llm JUDGE=directory_taxonomy
```

### Combined Evaluation

```bash
# Run both programmatic and LLM evaluation
make evaluate-all

# Generate combined scorecard
make scorecard
```

---

## Evaluation Outputs

### Output Files

```
evaluation/results/
  output.json              # Envelope output for evaluation runs
  raw_layout_output.json   # Raw layout scanner output
  checks.json              # Programmatic checks (JSON)
  scorecard.md             # Human-readable scorecard
  scorecard.json           # Machine-readable scorecard
  llm_evaluation.json      # LLM judge results
  scc_comparison.json      # SCC comparison results
```

### Scorecard Format

```markdown
# Layout Scanner Evaluation Scorecard

## Summary
- **Overall Score**: 4.2 / 5.0
- **Decision**: STRONG_PASS
- **Programmatic Score**: 4.5 (70%)
- **LLM Score**: 3.6 (30%)

## Dimension Breakdown

| Dimension | Passed | Total | Score | Weighted |
|-----------|--------|-------|-------|----------|
| Output Quality | 8/8 | 100% | 5.0 | 1.25 |
| Accuracy | 7/8 | 87.5% | 4.0 | 1.00 |
| Classification | 8/9 | 88.9% | 4.5 | 0.90 |
| Performance | 5/5 | 100% | 5.0 | 0.75 |
| Edge Cases | 5/6 | 83.3% | 4.0 | 0.60 |

## Failed Checks
- AC-3: Path Normalization - 2 paths contain backslashes

## LLM Judge Scores
| Judge | Score | Confidence |
|-------|-------|------------|
| Directory Taxonomy | 4.0 | 0.85 |
| Hierarchy Consistency | 5.0 | 0.92 |
| Language Detection | 3.5 | 0.78 |
| Classification Reasoning | 4.0 | 0.88 |
```

---

## Rollup Validation

Layout Scanner produces rollups that are validated by dbt tests:

Rollups:
- directory_counts_direct
- directory_counts_recursive

Tests:
- src/sot-engine/dbt/tests/test_rollup_layout_direct_vs_recursive.sql

### Validation Rules

1. `recursive_file_count >= direct_file_count` for all directories
2. `sum(child_recursive_counts) == parent_recursive_count - parent_direct_count`
3. `sum(classification_distribution.values()) == recursive_file_count`
4. `sum(language_distribution.values()) == recursive_file_count` (excluding unknown)

---

## Extending Evaluation

### Adding New Checks

1. Create check function in appropriate `scripts/checks/*.py` module
2. Add `@register_check("XX-N")` decorator
3. Include in `run_*_checks()` function
4. Update scoring table if needed (in `scripts/checks/__init__.py`)
5. Update this documentation

Example:

```python
@register_check("EC-7")
def check_long_paths(output: Dict[str, Any]) -> CheckResult:
    """EC-7: Paths > 260 characters handled."""
    files = output.get("files", {})
    long_paths = [p for p in files.keys() if len(p) > 260]

    return CheckResult(
        check_id="EC-7",
        name="Long Paths",
        category=CheckCategory.EDGE_CASES,
        passed=True,  # No errors during scan
        score=1.0,
        message=f"{len(long_paths)} long paths handled",
        evidence={"long_path_count": len(long_paths)},
    )
```

### Adding New LLM Judges

1. Create judge class in `evaluation/llm/judges/`
2. Inherit from `BaseJudge`
3. Implement `get_default_prompt()` and `collect_evidence()`
4. Register in `evaluation/llm/judges/__init__.py`
5. Update dimension weights if needed

### Adding New Test Scenarios

1. Create synthetic repo in `eval-repos/synthetic/`
2. Create ground truth file in `evaluation/ground-truth/`
3. Run analysis and evaluation
4. Verify expected results

---

## Appendix: Data Structures

### CheckResult

```python
@dataclass
class CheckResult:
    check_id: str           # e.g., "OQ-1"
    name: str               # e.g., "JSON Valid"
    category: CheckCategory # e.g., CheckCategory.OUTPUT_QUALITY
    passed: bool            # True/False
    score: float            # 0.0 to 1.0
    message: str            # Human-readable result
    evidence: dict          # Supporting data
```

### DimensionResult

```python
@dataclass
class DimensionResult:
    category: CheckCategory
    checks: List[CheckResult]
    passed_count: int
    total_count: int
    score: float            # 1.0 to 5.0
```

### EvaluationResult

```python
@dataclass
class EvaluationResult:
    run_id: str
    timestamp: str          # ISO 8601
    dimensions: List[DimensionResult]
    total_score: float      # 0.0 to 5.0
    decision: str           # STRONG_PASS, PASS, WEAK_PASS, FAIL
    summary: dict           # Aggregate statistics
```

### CheckCategory Enum

```python
class CheckCategory(Enum):
    OUTPUT_QUALITY = "output_quality"
    ACCURACY = "accuracy"
    CLASSIFICATION = "classification"
    PERFORMANCE = "performance"
    EDGE_CASES = "edge_cases"
    GIT_METADATA = "git_metadata"
    CONTENT_METADATA = "content_metadata"
```

### Scoring Tables

```python
SCORING_TABLES = {
    CheckCategory.OUTPUT_QUALITY: {8: 5.0, 7: 4.0, 5: 3.0, 3: 2.0, 0: 1.0},
    CheckCategory.ACCURACY: {8: 5.0, 7: 4.0, 5: 3.0, 3: 2.0, 0: 1.0},
    CheckCategory.CLASSIFICATION: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
    CheckCategory.PERFORMANCE: {4: 5.0, 3: 4.0, 2: 3.0, 1: 2.0, 0: 1.0},
    CheckCategory.EDGE_CASES: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
    CheckCategory.GIT_METADATA: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
    CheckCategory.CONTENT_METADATA: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
}
```

### Dimension Weights

```python
DIMENSION_WEIGHTS = {
    CheckCategory.OUTPUT_QUALITY: 0.25,
    CheckCategory.ACCURACY: 0.25,
    CheckCategory.CLASSIFICATION: 0.20,
    CheckCategory.PERFORMANCE: 0.15,
    CheckCategory.EDGE_CASES: 0.15,
    CheckCategory.GIT_METADATA: 0.0,      # Optional
    CheckCategory.CONTENT_METADATA: 0.0,   # Optional
}
```

---

## References

- [Layout Scanner README](README.md)
- [BLUEPRINT](BLUEPRINT.md)
- [Output Schema](schemas/output.schema.json)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
