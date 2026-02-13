# Layout Scanner Blueprint: Tool 0 Foundation

This document captures what was built, key decisions made, and provides a template for understanding the Layout Scanner's architecture and evaluation methodology.

---

## Executive Summary

**Layout Scanner** is the foundational tool (Tool 0) in the Project Vulcan analysis pipeline, providing canonical file registration and multi-signal classification for all subsequent analysis tools.

| Aspect | Status |
|--------|--------|
| **Purpose** | File registry, classification, language detection, hierarchy building |
| **Evaluation Score** | Pending full evaluation |
| **Recommendation** | ADOPT as Tool 0 foundation |
| **Languages Supported** | 50+ via extension mapping, go-enry fallback |
| **Programmatic Checks** | 51 checks across 8 categories |
| **Test Coverage** | 750+ tests across 18 test files |

**Key Strengths:**
- Fast filesystem traversal with os.scandir
- Multi-signal classification (path, filename, extension)
- Stable canonical IDs based on SHA-256
- Customizable rules via YAML configuration
- Optional git and content enrichment passes

**Known Limitations:**
- Language detection confidence for ambiguous files
- Large repository memory usage during full traversal
- No incremental scan mode (yet)

---

## Gap Analysis

### Gaps Between Layout Scanner and Collector Requirements

| Requirement | Scanner Capability | Gap | Mitigation |
|-------------|-------------------|-----|------------|
| Canonical file IDs | SHA-256 based IDs | None | Direct mapping |
| File classification | Multi-signal classifier | None | Path/filename/extension signals |
| Language detection | Extension + go-enry | Minor | Fallback for ambiguous files |
| Git metadata | Optional --git pass | None | Enriches with commit dates/authors |
| Directory metrics | Direct + recursive counts | None | Full rollup computation |
| Test file detection | Path + filename rules | None | `tests/`, `*_test.py` patterns |
| Vendor detection | Path-based rules | None | `node_modules/`, `vendor/` |

### Integration Strategy
1. Layout Scanner runs as Phase 0 before all other tools
2. Provides canonical file IDs for cross-tool correlation
3. Classification enables tool selection (skip vendor files in analysis)
4. Language detection feeds into language-specific tools

---

## 1. PoC Objectives

### Primary Goal
Establish a reliable file registry and classification system that serves as the foundation for all subsequent analysis tools.

### Success Criteria
1. **Output Quality** - Does the tool produce valid, complete file registry?
2. **Accuracy** - Are file counts, sizes, and metrics correct?
3. **Classification** - Are files correctly categorized?
4. **Performance** - Can it handle large repositories?
5. **Reliability** - Does it handle edge cases gracefully?
6. **Integration** - Does output map to collector schema?

### Success Metrics
- 51 programmatic checks passing
- 750+ unit and integration tests
- Sub-second performance for typical repositories (<10K files)
- Stable IDs across multiple runs
- Consistent classification with documented reasoning

---

## 2. What Was Built

### Core Analysis Pipeline

| Component | Description | Lines of Code |
|-----------|-------------|---------------|
| `layout_scanner.py` | Main entry point and orchestration | ~400 |
| `tree_walker.py` | os.scandir-based traversal | ~250 |
| `classifier.py` | Multi-signal file classification | ~350 |
| `language_detector.py` | Language identification | ~400 |
| `hierarchy_builder.py` | Directory tree computation | ~200 |
| `id_generator.py` | SHA-256 stable ID generation | ~100 |
| `ignore_filter.py` | .gitignore parsing | ~200 |
| `config_loader.py` | JSON configuration loading | ~150 |
| `rule_loader.py` | YAML rules parsing | ~200 |
| `statistics.py` | Statistics computation | ~150 |
| `output_writer.py` | JSON serialization | ~100 |
| `schema_validator.py` | Output validation | ~100 |
| `evaluate.py` | Programmatic evaluation | ~350 |
| `report_formatter.py` | Evaluation report formatting | ~200 |

### Optional Enrichment Passes

| Component | Description | Trigger |
|-----------|-------------|---------|
| `git_enricher.py` | Git metadata (commits, authors) | `--git` flag |
| `content_enricher.py` | Content analysis (line counts, hashes) | `--content` flag |

### Output Schema Features

| Feature | Description |
|---------|-------------|
| Schema Version | 1.0 with validation |
| File Objects | ID, path, size, language, classification, parent_id, depth |
| Directory Objects | Direct/recursive counts, classification distribution, language distribution |
| Hierarchy | Root ID, max depth, depth distribution |
| Statistics | Total files/dirs, size totals, language breakdown |

### Check Dimensions

| Dimension | Checks | Focus |
|-----------|--------|-------|
| Output Quality | OQ-1 to OQ-8 | JSON validity, schema compliance, required fields |
| Accuracy | AC-1 to AC-8 | ID stability, counts, paths, sizes |
| Classification | CL-1 to CL-6 | Category assignment accuracy |
| Performance | PF-1 to PF-4 | Speed benchmarks for various repo sizes |
| Edge Cases | EC-1 to EC-6 | Unicode, symlinks, deep nesting, empty files |
| Git Metadata | GM-1 to GM-6 | Commit dates, authors (optional) |
| Content Metadata | CM-1 to CM-6 | Line counts, hashes (optional) |
| SCC Comparison | SC-1 to SC-6 | Cross-validation with scc tool |

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Layout Scanner                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ tree_walker │───▶│   classifier    │───▶│ hierarchy_      │ │
│  │ (os.scandir)│    │ (multi-signal)  │    │ builder         │ │
│  └─────────────┘    └─────────────────┘    └─────────────────┘ │
│         │                   │                       │           │
│         ▼                   ▼                       ▼           │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ignore_filter│    │language_detector│    │  statistics     │ │
│  │(.gitignore) │    │(ext+enry+shebang│    │                 │ │
│  └─────────────┘    └─────────────────┘    └─────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│                     ┌─────────────────┐                         │
│                     │  output_writer  │                         │
│                     │  (JSON output)  │                         │
│                     └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Optional Enrichment                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                        ┌─────────────────┐     │
│  │git_enricher │                        │content_enricher │     │
│  │(--git flag) │                        │(--content flag) │     │
│  └─────────────┘                        └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Evaluation Framework                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  evaluate.py│───▶│  checks/        │───▶│  Scorecard      │ │
│  │             │    │  (51 checks)    │    │  (MD/JSON)      │ │
│  └─────────────┘    └─────────────────┘    └─────────────────┘ │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  LLM Judges     │───▶│  orchestrator   │                    │
│  │  (4 judges)     │    │                 │                    │
│  └─────────────────┘    └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Repository path passed to `layout_scanner.py`
2. **Traversal**: tree_walker scans filesystem with ignore filtering
3. **Classification**: Each file classified with confidence score
4. **Language Detection**: Language identified via extension/enry/shebang
5. **Hierarchy**: Directory tree computed with rollup metrics
6. **Output**: JSON with files, directories, hierarchy, statistics

---

## 3. Key Decisions

### Decision 1: Multi-Signal Classification
**Choice**: Use weighted signals (path, filename, extension) rather than single-signal classification.
**Rationale**: Files like `tests/conftest.py` need path context to classify correctly.
**Outcome**: Excellent - handles edge cases well with explainable reasoning.

### Decision 2: Stable Canonical IDs
**Choice**: SHA-256 hash of repository + relative path for stable IDs.
**Rationale**: IDs must be consistent across runs for cross-tool correlation.
**Outcome**: Essential - enables file tracking across analysis tools.

### Decision 3: Optional Enrichment Passes
**Choice**: Separate git and content enrichment into optional passes.
**Rationale**: Not all use cases need full enrichment; keep base scan fast.
**Outcome**: Good - base scan is fast, enrichment available when needed.

### Decision 4: YAML-Based Custom Rules
**Choice**: Support YAML rule files for classification customization.
**Rationale**: Different projects have different conventions (e.g., `spec/` vs `test/`).
**Outcome**: Flexible - users can adapt to any project structure.

### Decision 5: Direct + Recursive Metrics
**Choice**: Compute both direct (immediate children) and recursive (all descendants) counts.
**Rationale**: Both views are useful for different analyses.
**Outcome**: Complete - supports both local and aggregate views.

---

## 4. What Worked Well

### os.scandir-Based Traversal
- Extremely fast filesystem access
- Lazy evaluation reduces memory pressure
- DirEntry provides file metadata without extra syscalls

### Multi-Signal Classification
- Path rules catch directory-based patterns
- Filename patterns handle test_*.py, *.spec.ts
- Extension rules provide baseline classification
- Confidence scores indicate certainty

### Comprehensive Test Suite
- 750+ tests across unit and integration
- Synthetic repos with controlled structure
- Real repo validation (DnsServer)
- Edge case coverage (unicode, symlinks, deep nesting)

### Customizable Rules
- YAML format is human-readable
- Subcategory support (test::unit, test::integration)
- Override mechanism for special cases

---

## 5. What Could Be Improved

### Incremental Scan Mode
**Issue**: Full scan required even when few files changed.
**Lesson**: Large repositories benefit from incremental updates.
**For Next Version**: Add --incremental flag with change detection.

### Memory Usage for Very Large Repos
**Issue**: In-memory file registry grows with repository size.
**Lesson**: Streaming output may be needed for million-file repos.
**For Next Version**: Consider streaming JSON output option.

### Language Detection for Polyglot Files
**Issue**: Files with multiple languages (embedded SQL, JSX) need special handling.
**Lesson**: Single-language model doesn't capture all cases.
**For Next Version**: Add secondary_language field for polyglot files.

---

## 6. Implementation Plan

### Completed Phases

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1: Core Scanning** | Complete | tree_walker, ignore_filter, id_generator |
| **Phase 2: Classification** | Complete | classifier, language_detector |
| **Phase 3: Hierarchy** | Complete | hierarchy_builder, statistics |
| **Phase 4: Enrichment** | Complete | git_enricher, content_enricher |
| **Phase 5: Evaluation** | Complete | 51 programmatic checks, 4 LLM judges |
| **Phase 6: Documentation** | Complete | README, BLUEPRINT, EVAL_STRATEGY |

### Integration with Collector

```python
# Example collector integration
from scripts import scan_repository

# Run layout scan as Phase 0
layout, duration_ms = scan_repository(repo_path)

# Pass file IDs to other tools
file_ids = {f["path"]: f["id"] for f in layout["files"].values()}

# Use classification for tool selection
source_files = [
    f["path"] for f in layout["files"].values()
    if f["classification"] == "source"
]
```

---

## 7. Template for Tool Integration

### Using Layout Scanner Output

```python
# Load layout scanner output
with open("output/runs/repo.json") as f:
    layout = json.load(f)

# Access file registry
files = layout["files"]
for file_id, file_info in files.items():
    print(f"{file_info['path']}: {file_info['classification']}")

# Access directory metrics
directories = layout["directories"]
for dir_id, dir_info in directories.items():
    print(f"{dir_info['path']}: {dir_info['recursive_file_count']} files")

# Filter by classification
test_files = [
    f for f in files.values()
    if f["classification"] == "test"
]
```

---

## 8. Configuration Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | `eval-repos/synthetic` | Repository to scan |
| `REPO_NAME` | `synthetic` | Output file naming |
| `OUTPUT_DIR` | `output/runs` | Output directory |

### CLI Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output JSON file path |
| `--config` | JSON configuration file |
| `--rules` | YAML classification rules |
| `--ignore` | Additional ignore patterns |
| `--git` | Enable git metadata enrichment |
| `--content` | Enable content enrichment |
| `--validate` | Validate output against schema |
| `-v, --verbose` | Verbose output |
| `-q, --quiet` | Suppress progress output |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `NO_COLOR` | Disable colored output |

---

## 9. Performance Characteristics

### Benchmarks

| Repository Size | Files | Expected Time | Memory |
|-----------------|-------|---------------|--------|
| Small | < 100 | < 100ms | < 20MB |
| Medium | 1,000 | < 500ms | < 50MB |
| Large | 10,000 | < 2s | < 100MB |
| Very Large | 100,000 | < 20s | < 500MB |

### Key Performance Metrics

- **Throughput**: ~10,000+ files/second typical
- **Memory**: Linear growth with file count
- **Parallelization**: Single-threaded (os.scandir is fast enough)
- **Startup**: Minimal (pure Python)

---

## 10. LLM Evaluation

The layout-scanner evaluation combines 51 programmatic checks (8 categories) with 4 LLM judges. Programmatic pass rate: 98.0% with overall confidence of 0.85 across evaluation dimensions.

### Judge Roster

| Judge | Weight | Focus |
|-------|--------|-------|
| Classification Reasoning | 30% | Quality of classification explanations |
| Directory Taxonomy | 25% | Directory classifications match content |
| Hierarchy Consistency | 25% | Parent-child relationships coherent |
| Language Detection | 20% | Language identification accuracy |

### Running LLM Evaluation

```bash
# Full LLM evaluation
make llm-evaluate

# Combined evaluation (programmatic + LLM)
make evaluate-full
```

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Large repo memory exhaustion | Low | Medium | Implement streaming output for million-file repos |
| Incorrect language detection | Low | Low | go-enry fallback for ambiguous files |
| Symlink cycles | Very Low | Low | Cycle detection in tree_walker |
| .gitignore parsing errors | Very Low | Low | Graceful fallback to include file |
| Unicode path handling | Low | Low | UTF-8 normalization throughout |

### Security Considerations

1. **Path Traversal**: All paths validated as repo-relative; no absolute paths in output
2. **Symlink Safety**: External symlinks excluded by default
3. **File Content**: Only metadata extracted; no file content in base scan

### Operational Risks

- **Performance**: Sub-second for typical repos; larger repos may need --incremental mode (future)
- **Disk Space**: Output JSON typically <1% of repo size
- **Memory**: Linear growth with file count; ~100KB per 1000 files

---

## References

- [Design Document](../../docs/core/LAYOUT_SCANNER_DESIGN.md)
- [Tool Catalog](../../docs/tools/TOOL_CATALOG.md)
- [JSON Schema](schemas/layout.json)
- [EVAL_STRATEGY.md](evaluation/EVAL_STRATEGY.md)
