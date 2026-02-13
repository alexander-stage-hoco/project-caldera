# Evaluation Strategy: Symbol Scanner

This document describes the evaluation methodology for the symbol-scanner tool, which extracts function/class definitions, call relationships, and import statements from Python and C# source code.

## Evaluation Philosophy

The symbol-scanner evaluation uses a **hybrid programmatic + LLM-as-a-Judge** approach. Three categories of extraction output -- symbols, calls, and imports -- are evaluated independently using precision/recall/F1 metrics, then combined into an aggregate score.

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible precision/recall/F1 against ground truth |
| LLM Judges | 40% | Semantic understanding, edge case assessment, cross-file coherence |

This hybrid approach ensures that:

1. **Correctness is measured objectively** via set-based comparison of extracted entities against ground truth, producing exact precision, recall, and F1 numbers.
2. **Semantic quality is assessed by LLM judges** that can evaluate cross-file consistency, metadata completeness, and edge-case handling that raw matching cannot capture.
3. **Regression detection** is supported through baseline comparison, alerting when aggregate F1 drops beyond a configurable threshold (default 2%).

The evaluation supports two extraction languages (Python, C#) and three extractor strategies per language (Python: `ast`, `treesitter`, `hybrid`; C#: `treesitter`, `roslyn`, `hybrid`). The `hybrid` strategy is the default for compliance evaluation.

---

## Dimension Summary

### Programmatic Dimensions

Programmatic evaluation operates across three core extraction categories, each measured by precision, recall, and F1:

| Dimension | Category | Focus | Primary Metric |
|-----------|----------|-------|----------------|
| Symbol Extraction | Accuracy | Functions, classes, methods detected correctly | F1 (per-type + aggregate) |
| Call Extraction | Accuracy | Caller/callee pairs, call types | F1 (per-type + aggregate) |
| Import Extraction | Accuracy | Import paths, imported symbols | F1 (per-type + aggregate) |
| Integration Checks | Structural | Path normalization, envelope, summary counts | Pass/Fail |

The aggregate F1 is computed by pooling true positives, false positives, and false negatives across all three categories (micro-average).

### LLM Judge Dimensions

| Judge | Weight | Focus |
|-------|--------|-------|
| Symbol Accuracy | 30% | Completeness and correctness of symbol extraction |
| Call Relationship | 30% | Accuracy of function/method call relationships |
| Import Completeness | 20% | Completeness of import extraction |
| Integration Quality | 20% | Data consistency, metadata quality, path normalization |

### Combined Weight Distribution

| Component | Effective Weight |
|-----------|-----------------|
| Programmatic evaluation (60% of total) | 60% |
| LLM Symbol Accuracy (30% of 40%) | 12% |
| LLM Call Relationship (30% of 40%) | 12% |
| LLM Import Completeness (20% of 40%) | 8% |
| LLM Integration Quality (20% of 40%) | 8% |
| **Total** | **100%** |

---

## Check Catalog

### Symbol Accuracy Checks (SA-1 to SA-3)

These checks compare extracted symbols against ground truth on a per-repo basis.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| SA-1 | Symbol Count | Accuracy | `len(actual) == len(expected)` | Expected count, actual count |
| SA-2 | Symbol Types | Accuracy | All `(path, symbol_name)` pairs have matching `symbol_type` | Total expected, number of matches |
| SA-3 | Line Numbers | Accuracy | All `(path, symbol_name)` pairs have matching `line_start` | Total expected, number of matches |

**Matching strategy (evaluate.py):** Symbols are matched using fuzzy keys `(path, symbol_name)` with a `LINE_TOLERANCE = 2` (lines +/- 2). When multiple symbols share the same fuzzy key (e.g., overloaded `__init__` methods), the matcher selects the closest line match within tolerance. Exact matching is also available but fuzzy is the default.

**Weighted F1:** Symbol matching also supports a weighted mode where exported symbols receive weight 1.0 and private symbols (`_prefix`) receive weight 0.5, reflecting that public API accuracy matters more.

### Call Accuracy Checks (CA-1 to CA-3)

These checks compare extracted call relationships against ground truth.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| CA-1 | Call Count | Accuracy | `len(actual) == len(expected)` | Expected count, actual count |
| CA-2 | Caller/Callee Pairs | Accuracy | All `(caller_file, caller_symbol, callee_symbol)` triples match | Total expected, number of matches |
| CA-3 | Call Types | Accuracy | All triples have matching `call_type` (direct, dynamic, async) | Total expected, number of matches |

**Matching strategy:** Calls are matched on `(caller_file, caller_symbol, callee_symbol, line_number)` for exact comparison. Per-type metrics are computed by grouping on `call_type`.

### Import Accuracy Checks (IA-1 to IA-3)

These checks compare extracted imports against ground truth.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| IA-1 | Import Count | Accuracy | `len(actual) == len(expected)` | Expected count, actual count |
| IA-2 | Import Paths | Accuracy | All `(file, imported_path)` pairs match | Total expected, number of matches |
| IA-3 | Import Symbols | Accuracy | All `(file, imported_path)` pairs have matching `imported_symbols` | Total expected, number of matches |

**Matching strategy:** Imports are matched on `(file, imported_path, line_number)` for exact comparison. Per-type metrics are computed by grouping on `import_type` (static, dynamic).

### Integration Checks (INT-1 to INT-3)

These checks validate structural integrity of the output envelope.

| Check ID | Name | Category | Severity | Pass Criteria | Evidence Collected |
|----------|------|----------|----------|---------------|-------------------|
| INT-1 | Path Normalization | Structural | High | All paths in symbols, calls, and imports are repo-relative (no leading `/`, `./`, or `\`) | List of path issues found |
| INT-2 | Envelope Structure | Structural | Critical | Output has `metadata` with 8 required fields and `data` with `symbols`, `calls`, `imports`, `summary` | List of missing fields |
| INT-3 | Summary Accuracy | Structural | High | `summary.total_symbols == len(symbols)`, `summary.total_calls == len(calls)`, `summary.total_imports == len(imports)` | List of count mismatches |

**Required metadata fields:** `tool_name`, `tool_version`, `run_id`, `repo_id`, `branch`, `commit`, `timestamp`, `schema_version`.

**Required data fields:** `symbols`, `calls`, `imports`, `summary`.

### Total Check Count

| Category | Checks | Per-Repo | Notes |
|----------|--------|----------|-------|
| Symbol Accuracy | 3 | Per ground truth repo | SA-1 to SA-3 |
| Call Accuracy | 3 | Per ground truth repo | CA-1 to CA-3 |
| Import Accuracy | 3 | Per ground truth repo | IA-1 to IA-3 |
| Integration | 3 | Per output file | INT-1 to INT-3 |
| **Total** | **12 check types** | **9 per-repo + 3 structural** | |

With 23 Python ground truth repos, this produces 9 x 23 = 207 per-repo checks plus 3 structural checks per evaluation run.

---

## Scoring

### Programmatic Scoring

The programmatic evaluation computes precision, recall, and F1 for each extraction category (symbols, calls, imports) and an aggregate across all categories.

#### Precision / Recall / F1 Formula

```python
@dataclass
class Metrics:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 1.0 if self.false_negatives == 0 else 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 1.0 if self.false_positives == 0 else 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)
```

#### Aggregate F1 (Overall Score)

The overall F1 pools all true positives, false positives, and false negatives across symbols, calls, and imports into a single micro-averaged score:

```python
@property
def overall_f1(self) -> float:
    combined = self.symbols.total + self.calls.total + self.imports.total
    return combined.f1
```

This micro-average gives more weight to categories with more items, which naturally emphasizes symbols (the most numerous category).

#### Weighted F1 for Symbols

An optional weighted F1 mode adjusts for symbol visibility:

```python
SYMBOL_WEIGHTS = {
    "exported": 1.0,   # Public symbols (full weight)
    "private": 0.5,    # Private symbols (_prefix, half weight)
}
```

This reflects the principle that correctly extracting public API symbols is more important than internal helpers.

### LLM Scoring

Each LLM judge produces a score on a 1-5 scale. The weighted LLM score is:

```python
llm_total_score = sum(judge.weight * judge.score for judge in judges)
# = 0.30 * symbol_accuracy + 0.30 * call_relationship
#   + 0.20 * import_completeness + 0.20 * integration
```

### Combined Score Calculation

The programmatic and LLM scores are combined using a 60/40 weighting:

```python
# Normalize programmatic score from 0-1 to 1-5 scale
if prog_score_raw <= 1.0:
    prog_score = 1.0 + prog_score_raw * 4.0  # Maps 0 -> 1, 1 -> 5

# Weighted combination (both on 5-point scale)
PROGRAMMATIC_WEIGHT = 0.60
LLM_WEIGHT = 0.40
combined_score = programmatic_score * PROGRAMMATIC_WEIGHT + llm_score * LLM_WEIGHT
```

---

## Decision Thresholds

### Combined Score Decisions

The combined score (on a 5-point scale) determines the final decision:

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent, production-ready output |
| PASS | >= 3.5 | Good, minor improvements possible |
| WEAK_PASS | >= 3.0 | Acceptable with caveats |
| FAIL | < 3.0 | Significant issues, not ready |

### Programmatic-Only Decisions

When running programmatic evaluation alone (without LLM judges), a simpler three-tier system applies based on aggregate F1:

| Decision | F1 Score | Interpretation |
|----------|----------|----------------|
| PASS | >= 0.95 (95%) | Excellent extraction accuracy |
| WARN | >= 0.85 (85%) | Acceptable but needs attention |
| FAIL | < 0.85 (85%) | Below minimum extraction quality |

These thresholds are defined as constants in `evaluate.py`:

```python
PASS_THRESHOLD = 0.95  # >= 95% = PASS
WARN_THRESHOLD = 0.85  # 85-95% = WARN, < 85% = FAIL
```

### Regression Detection

The evaluation supports baseline-based regression detection. When a baseline exists, the evaluator compares the current aggregate F1 against the stored baseline:

```python
threshold = 0.02  # Maximum allowed regression (2%)

delta = baseline_score - current_score
if delta > threshold:
    # REGRESSION: Score dropped significantly
elif delta > 0:
    # Minor regression within threshold
```

Baselines are stored at `evaluation/baseline.json` and contain the timestamp, aggregate F1, per-category F1, and repo counts from the baseline run.

---

## LLM Judge Details

### Symbol Accuracy Judge (30% weight)

**Dimension name:** `symbol_accuracy`

**Sub-dimensions:**

| Sub-dimension | Focus |
|---------------|-------|
| Function Extraction | Top-level functions detected with correct names and types |
| Class Extraction | All classes detected with proper hierarchy |
| Line Accuracy | Start line numbers match source code |

**Evaluation criteria breakdown:**
- **Completeness (40%):** All top-level functions, classes, and methods extracted
- **Accuracy (40%):** Symbol types correctly identified, line numbers accurate, export status correct
- **Edge Cases (20%):** Async functions handled, decorators do not interfere

**Scoring rubric (synthetic repos):**

| Score | Criteria |
|-------|----------|
| 5 | All symbols captured, types correct, line numbers exact |
| 4 | Core symbols captured with minor omissions |
| 3 | Most symbols captured, some type misclassifications |
| 2 | Missing important symbols or incorrect types |
| 1 | Incomplete extraction, systematic errors |

**Scoring rubric (real-world repos):**

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, symbols consistent with source structure |
| 4 | Minor gaps but symbols match visible code structure |
| 3 | Schema issues OR questionable symbol classifications |
| 2 | Multiple issues AND inconsistent data |
| 1 | Broken output, missing required fields |

**Evidence collected:**
- Sample of up to 50 extracted symbols (JSON)
- Symbol counts by type (function, class, method, etc.)
- Up to 3 source code samples (first 2000 characters each)
- Total symbol count
- Evaluation mode (synthetic or real_world)
- Synthetic baseline context (for real-world evaluation)

### Call Relationship Judge (30% weight)

**Dimension name:** `call_relationship`

**Sub-dimensions:**

| Sub-dimension | Focus |
|---------------|-------|
| Direct Calls | Standard function-to-function call detection |
| Cross-File Calls | Calls spanning multiple source files |
| Line Accuracy | Call line numbers match source code |

**Evaluation criteria breakdown:**
- **Completeness (40%):** All function calls, method calls, and cross-file calls captured
- **Accuracy (40%):** Caller/callee pairs correct, line numbers accurate, call types classified
- **Edge Cases (20%):** Async/await calls, method chaining, dynamic calls

**Scoring rubric (synthetic repos):**

| Score | Criteria |
|-------|----------|
| 5 | All calls captured, caller/callee pairs correct, line numbers exact |
| 4 | Core calls captured with minor omissions |
| 3 | Most calls captured, some incorrect pairings |
| 2 | Missing important calls or incorrect relationships |
| 1 | Incomplete extraction, systematic errors |

**Evidence collected:**
- Sample of up to 50 extracted calls (JSON)
- Call counts by type (direct, dynamic, async)
- Symbol names sample (up to 20) for cross-referencing callers to known symbols
- Up to 3 source code samples
- Total call and symbol counts

### Import Completeness Judge (20% weight)

**Dimension name:** `import_completeness`

**Sub-dimensions:**

| Sub-dimension | Focus |
|---------------|-------|
| Import Capture | All import/from-import statements detected |
| Path Accuracy | Import paths correctly resolved |
| Symbol Listing | Imported symbols correctly listed |

**Evaluation criteria breakdown:**
- **Completeness (40%):** All `import x` and `from x import y` statements captured
- **Accuracy (40%):** Import paths correct, imported symbols listed, line numbers accurate
- **Edge Cases (20%):** Relative imports, star imports, dynamic imports

**Scoring rubric (synthetic repos):**

| Score | Criteria |
|-------|----------|
| 5 | All imports captured, paths correct, symbols listed |
| 4 | Core imports captured with minor omissions |
| 3 | Most imports captured, some path issues |
| 2 | Missing important imports or incorrect paths |
| 1 | Incomplete extraction, systematic errors |

**Evidence collected:**
- Sample of up to 50 extracted imports (JSON)
- Import counts by type (static, dynamic)
- Up to 3 source code samples
- Total import count

### Integration Quality Judge (20% weight)

**Dimension name:** `integration`

**Sub-dimensions:**

| Sub-dimension | Focus |
|---------------|-------|
| Summary Accuracy | Summary counts match actual array lengths |
| Metadata Completeness | All 8 required metadata fields present |
| Path Normalization | All paths repo-relative with POSIX separators |

**Evaluation criteria breakdown:**
- **Data Consistency (40%):** Summary counts match actual data, cross-file references valid, no orphaned entries
- **Metadata Quality (30%):** All required fields present, values properly formatted, schema version correct
- **Path Normalization (30%):** All paths repo-relative, consistent separator usage, no absolute paths

**Scoring rubric (synthetic repos):**

| Score | Criteria |
|-------|----------|
| 5 | Perfect coherence, all cross-references valid, metadata complete |
| 4 | Coherent data with minor issues |
| 3 | Mostly coherent, some inconsistencies |
| 2 | Multiple coherence or consistency issues |
| 1 | Broken output structure |

**Evidence collected:**
- Full metadata object
- Summary statistics object
- Summary validation results (symbols_match, calls_match, imports_match)
- Metadata completeness map (field -> present boolean)
- Path issues found (up to 10)
- Total counts for symbols, calls, imports

---

## LLM Judge Response Format

All judges return structured JSON with the following fields:

```json
{
  "dimension": "<dimension_name>",
  "score": 4,
  "confidence": 0.92,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<key evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "<sub_dimension_1>": 5,
    "<sub_dimension_2>": 4,
    "<sub_dimension_3>": 4
  }
}
```

The shared `JudgeResult` dataclass standardizes this across all judges:

| Field | Type | Description |
|-------|------|-------------|
| `dimension` | str | Evaluation dimension name |
| `score` | int | Score from 1-5 |
| `confidence` | float | Confidence level 0.0-1.0 |
| `reasoning` | str | Explanation of score |
| `evidence_cited` | list[str] | Evidence points used |
| `recommendations` | list[str] | Improvement suggestions |
| `sub_scores` | dict[str, int] | Per-sub-dimension scores |
| `raw_response` | str | Raw LLM response text |

### LLM Judge Confidence Levels

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review recommended |

---

## Evidence Collection

### Programmatic Evidence

Each programmatic check returns a result dict with evidence:

```python
{
    "name": "symbol_count",
    "passed": True,
    "expected": 42,
    "actual": 42,
}
```

For integration checks, evidence includes issue lists:

```python
{
    "name": "path_normalization",
    "passed": True,
    "issues": [],
}
```

### Evidence Types by Check Category

| Check Category | Evidence Collected |
|---------------|-------------------|
| Symbol Accuracy (SA-*) | Expected count, actual count, per-symbol match details |
| Call Accuracy (CA-*) | Expected count, actual count, caller/callee pair matches |
| Import Accuracy (IA-*) | Expected count, actual count, import path matches |
| Integration (INT-*) | Issue lists (bad paths, missing fields, count mismatches) |

### LLM Judge Evidence

Each LLM judge collects tailored evidence before invoking the model:

| Judge | Evidence Sources |
|-------|-----------------|
| Symbol Accuracy | Extracted symbols (50 sample), symbol type distribution, source code (3 files, 2000 chars each) |
| Call Relationship | Extracted calls (50 sample), call type distribution, symbol names (20 sample), source code |
| Import Completeness | Extracted imports (50 sample), import type distribution, source code |
| Integration | Full metadata, summary stats, summary validation, metadata completeness map, path issues |

For real-world evaluation mode, judges additionally load synthetic baseline context to calibrate their expectations.

---

## Ground Truth

### Methodology

Ground truth files define the expected symbols, calls, and imports for each synthetic repository. They are located in `evaluation/ground-truth/*.json` for Python and `evaluation/ground-truth-csharp/*.json` for C#.

### Generation Process

1. **Run extractors** on synthetic repositories to get baseline values
2. **Cross-extractor validation** to verify consistency across AST, tree-sitter, and hybrid extractors
3. **Manual verification** by inspecting source code and verifying extracted entities
4. **Calibration** to adjust line numbers and handle edge cases (documented via `calibrated_date` field)

### Ground Truth Schema (Python)

Each ground truth file follows this structure:

```json
{
  "metadata": {
    "repo": "<repo-name>",
    "created": "2026-02-03",
    "version": "1.1-calibrated",
    "category": "<basic|real-world|error>",
    "description": "<what this repo tests>",
    "calibrated_date": "2026-02-03"
  },
  "expected": {
    "symbols": [
      {
        "path": "main.py",
        "symbol_name": "greet",
        "symbol_type": "function",
        "line_start": 4,
        "is_exported": true,
        "parameters": 1
      }
    ],
    "calls": [
      {
        "caller_file": "main.py",
        "caller_symbol": "main",
        "callee_symbol": "greet",
        "callee_file": "main.py",
        "line_number": 19,
        "call_type": "direct"
      }
    ],
    "imports": [
      {
        "file": "main.py",
        "imported_path": "os",
        "import_type": "static",
        "line_number": 1,
        "imported_symbols": null
      }
    ],
    "summary": {
      "total_files": 1,
      "total_symbols": 3,
      "total_calls": 7,
      "total_imports": 0
    }
  },
  "notes": {}
}
```

### Ground Truth Schema (C# -- TShock variant)

The C# ground truth for large real-world repos uses a summary-based schema:

```json
{
  "schema_version": "2.0",
  "description": "Auto-seeded ground truth from tshock-roslyn-...",
  "verification_status": "verified",
  "verification": {
    "method": "cross_extractor_validation",
    "cross_validated_with": ["tree-sitter", "roslyn", "hybrid"],
    "validation_results": {
      "symbol_parity": "100%",
      "performance": "1.6s"
    }
  },
  "summary_expectations": {
    "total_files": 107,
    "total_symbols": 2815,
    "total_calls": 9853,
    "total_imports": 632
  },
  "symbol_expectations": {
    "by_type": { "class": 258, "property": 624, "method": 1159, "field": 749, "event": 25 },
    "total": 2815
  }
}
```

### Expected Value Formats

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Repo-relative POSIX path (e.g., `"main.py"`, `"models.py"`) |
| `symbol_name` | string | Bare function/class/method name |
| `symbol_type` | string | One of: `function`, `class`, `method`, `property`, `field`, `event` |
| `line_start` | integer | 1-based line number |
| `is_exported` | boolean | `true` for public, `false` for `_`-prefixed |
| `parameters` | integer or null | Number of parameters (excluding `self`/`cls`) |
| `caller_file` | string | Repo-relative path of calling file |
| `caller_symbol` | string | Name of calling function/method, or `<module>` for module-level |
| `callee_symbol` | string | Name of called function/method |
| `callee_file` | string or null | Repo-relative path of callee, `null` for builtins/externals |
| `call_type` | string | One of: `direct`, `dynamic`, `async`, `constructor`, `event`, `using_static` |
| `imported_path` | string | Module path (e.g., `"os"`, `"json"`) |
| `import_type` | string | One of: `static`, `dynamic` |
| `imported_symbols` | list[string] or null | Specific symbols imported, `null` for module imports |

### Synthetic Repository Inventory (Python -- 23 repos)

| Repository | Category | Focus | Language Features Tested |
|------------|----------|-------|--------------------------|
| simple-functions | basic | Top-level functions | Functions, calls, module-level invocation |
| class-hierarchy | basic | Inheritance | Classes, methods, `__init__`, `super()` |
| cross-module-calls | basic | Multi-file | Cross-file calls, imports between modules |
| import-patterns | basic | Import types | `import x`, `from x import y`, dynamic imports |
| nested-structures | basic | Nesting | Nested functions, nested classes |
| async-patterns | real-world | Async/await | `async def`, `await`, `async with`, `async for` |
| circular-imports | real-world | Circular deps | Mutual imports between modules |
| confusing-names | real-world | Name collisions | Overloaded names, shadowing |
| dataclasses-protocols | real-world | Modern typing | `@dataclass`, `Protocol`, type annotations |
| decorators-advanced | real-world | Decorators | `@property`, `@staticmethod`, custom decorators |
| deep-hierarchy | real-world | Deep inheritance | Multi-level class hierarchies |
| generators-comprehensions | real-world | Iterators | Generators, list/dict/set comprehensions |
| metaprogramming | real-world | Meta-classes | `__init_subclass__`, descriptors, metaclasses |
| modern-syntax | real-world | Python 3.10+ | Walrus operator, match-case, union types |
| type-checking-imports | real-world | TYPE_CHECKING | Conditional imports under `if TYPE_CHECKING:` |
| unresolved-externals | real-world | External deps | Calls to uninstalled third-party libraries |
| web-framework-patterns | real-world | Flask/Django | Route decorators, view functions, middleware |
| deep-nesting-stress | stress | Deep nesting | Deeply nested functions and classes |
| large-file | stress | Large file | Single file with many symbols |
| encoding-edge-cases | error | Unicode | UTF-8 encoding, non-ASCII identifiers, emoji |
| partial-syntax-errors | error | Error recovery | Files with syntax errors mixed with valid code |
| dynamic-code-generation | error | Dynamic code | `exec()`, `eval()`, runtime class creation |
| csharp-tshock | real-world | C# real project | 107 files, 2815 symbols, cross-extractor validated |

### C# Synthetic Repository Inventory (6 repos)

| Repository | Focus |
|------------|-------|
| static-members | Static fields, methods, properties |
| extension-methods | C# extension method patterns |
| nested-types | Nested classes, structs, enums |
| nullable-reference-types | C# 8.0+ nullable references |
| pattern-matching | C# pattern matching expressions |
| records | C# 9.0+ record types |

---

## Evaluation Workflow

### Running Programmatic Evaluation

```bash
# Full evaluation pipeline (analyze + evaluate)
cd src/tools/symbol-scanner
make evaluate

# Evaluation with verbose output against all ground truth repos
.venv/bin/python -m scripts.evaluate \
    --analysis evaluation/results/output.json \
    --ground-truth evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json \
    --scorecard evaluation/results \
    --verbose

# Single repo evaluation
.venv/bin/python -m scripts.evaluate \
    --repo simple-functions \
    --strategy hybrid \
    --verbose

# Compare AST vs tree-sitter strategies
.venv/bin/python -m scripts.evaluate \
    --compare \
    --ground-truth evaluation/ground-truth

# JSON output for automation
.venv/bin/python -m scripts.evaluate \
    --all --strategy hybrid --json

# Save current scores as new baseline
.venv/bin/python -m scripts.evaluate \
    --analysis evaluation/results/output.json \
    --ground-truth evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json \
    --save-baseline

# C# evaluation
.venv/bin/python -m scripts.evaluate \
    --analysis evaluation/results/output.json \
    --ground-truth evaluation/ground-truth-csharp \
    --language csharp
```

### Running LLM Evaluation

```bash
# Full LLM evaluation (4 judges)
make evaluate-llm

# Or directly:
.venv/bin/python -m evaluation.llm.orchestrator \
    --analysis evaluation/results/output.json \
    --output evaluation/results/llm_evaluation.json \
    --programmatic-results evaluation/results/evaluation_report.json \
    --model opus-4.5

# Focused evaluation (2 judges: symbol accuracy + call relationship)
.venv/bin/python -m evaluation.llm.orchestrator \
    --analysis evaluation/results/output.json \
    --output evaluation/results/llm_evaluation.json \
    --focused
```

### End-to-End Pipeline

```bash
# Full pipeline: setup + analyze + evaluate
make all
```

### Evaluation Outputs

Evaluation artifacts are written to a fixed location:

```
evaluation/results/
  output.json               # Envelope output for evaluation runs
  evaluation_report.json    # Programmatic evaluation report
  scorecard.md              # Programmatic scorecard (markdown)
  llm_evaluation.json       # LLM judge results (if run)
```

### Programmatic Report Structure

```json
{
  "timestamp": "2026-02-03T12:00:00Z",
  "decision": "PASS",
  "score": 0.9712,
  "checks": [
    {
      "check_id": "repo.simple-functions",
      "name": "Repository: simple-functions",
      "passed": true,
      "message": "F1=98.50%, PASS",
      "expected": ">= 85%",
      "actual": "98.50%",
      "evidence": {
        "symbols_f1": 1.0,
        "calls_f1": 0.97,
        "imports_f1": 1.0,
        "overall_f1": 0.985,
        "decision": "PASS"
      }
    }
  ],
  "summary": {
    "total_repos": 22,
    "passed": 20,
    "warned": 2,
    "failed": 0,
    "average_f1": 0.9712
  },
  "aggregate": {
    "symbols": { "precision": 0.98, "recall": 0.97, "f1": 0.975 },
    "calls": { "precision": 0.95, "recall": 0.94, "f1": 0.945 },
    "imports": { "precision": 0.99, "recall": 0.98, "f1": 0.985 },
    "overall_f1": 0.9712
  },
  "per_repo_results": [...]
}
```

---

## Extending the Evaluation

### Adding a New Programmatic Check

1. Create a new check function in the appropriate module under `scripts/checks/`:
   - `symbol_accuracy.py` for symbol-related checks
   - `call_accuracy.py` for call-related checks
   - `import_accuracy.py` for import-related checks
   - `integration.py` for structural/integration checks

2. Add the check to the `run_checks()` function in that module.

3. Return a dict with at minimum `name`, `passed`, and evidence fields.

4. Run `make evaluate` to verify the new check.

### Adding a New Ground Truth Repository

1. Create the synthetic repo directory under `eval-repos/synthetic/<repo-name>/`.

2. Populate with source files that exercise the target pattern.

3. Run the hybrid extractor to generate initial ground truth:
   ```bash
   .venv/bin/python -m scripts.evaluate --repo <repo-name> --strategy hybrid --json
   ```

4. Manually verify and adjust the output, then save as `evaluation/ground-truth/<repo-name>.json` following the ground truth schema.

5. Set `metadata.version` to `"1.1-calibrated"` and `metadata.calibrated_date` to the current date.

6. Run `make evaluate` to include the new repo in the suite.

### Adding a New LLM Judge

1. Create a new judge class in `evaluation/llm/judges/` inheriting from `BaseJudge`.

2. Implement required properties: `dimension_name`, `weight`.

3. Implement `collect_evidence()` to gather relevant data from the output.

4. Implement `get_default_prompt()` as a fallback.

5. Create a prompt template in `evaluation/llm/prompts/<dimension_name>.md` with `{{ evidence }}` placeholders.

6. Register the judge in `evaluation/llm/orchestrator.py` in the `register_all_judges()` method.

7. Export the judge from `evaluation/llm/judges/__init__.py`.

8. Ensure all judge weights sum to 1.0.

### Updating Decision Thresholds

Programmatic thresholds are defined in `scripts/evaluate.py`:

```python
PASS_THRESHOLD = 0.95  # >= 95% = PASS
WARN_THRESHOLD = 0.85  # 85-95% = WARN, < 85% = FAIL
```

Combined score thresholds are defined in `shared/evaluation/orchestrator.py`:

```python
STRONG_PASS_THRESHOLD = 4.0
PASS_THRESHOLD = 3.5
WEAK_PASS_THRESHOLD = 3.0
```

---

## Real-World vs Synthetic Evaluation

The evaluation system supports two modes:

| Mode | Ground Truth | Judge Behavior |
|------|-------------|----------------|
| Synthetic | Full per-entity ground truth with exact matches | Strict: score against exact expected values |
| Real-world | Summary-level expectations only | Lenient: validate schema compliance and internal consistency |

For real-world evaluation, LLM judges receive synthetic baseline context showing the tool's validated accuracy on synthetic repos. This calibrates the judge: if the tool scores well on synthetic ground truth, the judge gives benefit of the doubt on real-world outputs where exact ground truth is unavailable.

---

## Test Mode

For CI and testing, the `SYMBOL_SCANNER_TEST_MODE` environment variable causes judges to return mock responses without calling the LLM API:

```python
if os.getenv("SYMBOL_SCANNER_TEST_MODE"):
    return json.dumps({
        "dimension": self.dimension_name,
        "score": 4,
        "confidence": 0.85,
        "reasoning": "Mock response for testing",
        "evidence_cited": [],
        "recommendations": [],
        "sub_scores": {}
    })
```

---

## References

- [Project Caldera CLAUDE.md](/CLAUDE.md)
- [Shared Evaluation Infrastructure](/src/shared/evaluation/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
- [Python AST module](https://docs.python.org/3/library/ast.html)
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
