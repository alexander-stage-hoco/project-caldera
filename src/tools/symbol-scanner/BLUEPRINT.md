# Symbol Scanner Blueprint

## Executive Summary

Symbol Scanner extracts function/class definitions, call relationships, and imports from source code. This enables coupling analysis, blast radius computation, and dependency mapping for Python and C# codebases.

**Key Capabilities:**
- Extract symbols (functions, classes, methods, properties, fields, events)
- Track function/method calls
- Map import relationships
- Support for Python and C#

## Overview

Symbol Scanner extracts function/class definitions, call relationships, and imports from source code. This enables coupling analysis, blast radius computation, and dependency mapping.

## Architecture

### Extraction Pipeline

```
Source Files → Language Extractor → Raw Entities → Normalizer → Output Envelope
```

1. **Source Files**: Python files discovered via glob patterns
2. **Language Extractor**: AST-based parsing (Python stdlib `ast` module)
3. **Raw Entities**: Symbols, calls, imports with source locations
4. **Normalizer**: Path normalization, deduplication
5. **Output Envelope**: Standard metadata + data structure

### Entity Model

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ CodeSymbol  │    │ SymbolCall  │    │ FileImport  │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ path        │◄───│ caller_file │    │ file        │
│ symbol_name │◄───│ caller_sym  │    │ imported_   │
│ symbol_type │    │ callee_sym  │───▶│ path        │
│ line_start  │    │ callee_file │    │ imported_   │
│ line_end    │    │ line_number │    │ symbols     │
│ is_exported │    │ call_type   │    │ import_type │
│ parameters  │    └─────────────┘    │ line_number │
│ parent_sym  │                       └─────────────┘
│ docstring   │
└─────────────┘
```

### Call Resolution Strategy

The CallResolver implements import graph traversal to resolve `callee_file`:
- Same-file calls resolve to the caller's file
- Cross-file calls resolve via import bindings (from X import Y)
- Star imports are searched for matching symbols
- Builtins (133) and stdlib (400+ modules) return `null`
- Dynamic calls (`obj.method()`) return `null` (requires type inference)

## Design Decisions

### Why AST over Regex?

1. **Accuracy**: AST understands language syntax
2. **Robustness**: Handles edge cases (strings, comments)
3. **Semantics**: Can distinguish function calls from other uses

### Why Python stdlib `ast`?

1. **No dependencies**: Works out of the box
2. **Maintained**: Part of Python core
3. **Sufficient**: Covers our extraction needs

### Symbol Type Classification

| Type | Criteria |
|------|----------|
| `function` | Top-level `def` |
| `class` | Top-level `class` |
| `method` | `def` inside class |
| `variable` | Module-level assignment (future) |

### Call Type Classification

| Type | Criteria |
|------|----------|
| `direct` | Simple name call: `foo()` |
| `dynamic` | Attribute call: `obj.method()` |
| `async` | Await expression: `await foo()` |

### Import Type Classification

| Type | Criteria |
|------|----------|
| `static` | Regular import: `import x` or `from x import y` |
| `dynamic` | `__import__()` or `importlib.import_module()` |
| `side_effect` | Import for side effects (detected heuristically) |

## Data Flow

### Persistence Path

```
analyze.py → output.json
                ↓
    SymbolScannerAdapter
                ↓
    ┌───────────┬───────────┬───────────┐
    │ CodeSymbol│SymbolCall │FileImport │
    └─────┬─────┴─────┬─────┴─────┬─────┘
          ↓           ↓           ↓
    lz_code_symbols  lz_symbol_calls  lz_file_imports
```

### dbt Transformation Path

```
lz_* tables
      ↓
stg_lz_code_symbols
stg_lz_symbol_calls
stg_lz_file_imports
      ↓
rollup_symbols_directory_counts_direct
rollup_coupling_directory_metrics_direct
```

## Quality Gates

1. **Schema Validation**: JSON Schema against output
2. **Path Validation**: All paths repo-relative
3. **Line Range Validation**: start <= end, values >= 1
4. **Entity Validation**: Required fields present

## Implementation Plan

### Phase 1 ✅ Python + C# Complete
- Python symbol extraction using stdlib `ast`
- C# symbol extraction using tree-sitter and Roslyn
- Basic call tracking for both languages
- Import extraction (Python) and using directive extraction (C#)

### Phase 2 ✅ Call Resolution Complete
- Resolve `callee_file` for local imports via CallResolver
- Build import graph for cross-file calls
- Resolution statistics tracking

### C# Extractor Architecture

Three extractor strategies for C#:
- **tree-sitter**: Fast AST-based extraction, ~ms per file
- **roslyn**: Semantic analysis via .NET 8 tool, slower but more accurate
- **hybrid** (default): Combines tree-sitter syntax with Roslyn semantics

Validated on TShock (107 files, 2,815 symbols, 9,853 calls).

### Future Enhancements

#### Phase 3: JavaScript/TypeScript
- Add tree-sitter parser
- Support modern JS features

#### Phase 4: Java/Go
- Additional tree-sitter grammars
- Language-specific semantics

## Configuration

Symbol Scanner has minimal configuration:

| Setting | Default | Description |
|---------|---------|-------------|
| Exclude patterns | `__pycache__`, `.git`, `.venv` | Directories to skip |
| File extensions | `.py` | Files to analyze |

## Performance

- **Parsing**: ~1000 lines/ms using Python AST
- **Memory**: O(n) where n is file count
- **Parallelization**: Supported via directory scanning

## Evaluation

See EVAL_STRATEGY.md for detailed evaluation methodology.

Evaluation dimensions:
- Symbol extraction accuracy
- Call relationship accuracy
- Import completeness
- Integration quality

## Risk

| Risk | Mitigation |
|------|------------|
| Syntax errors in source | Graceful handling, continue with other files |
| Large files | Memory-efficient streaming (future) |
| Dynamic code | Document limitations, focus on static analysis |
| Encoding issues | UTF-8 with fallback handling |
