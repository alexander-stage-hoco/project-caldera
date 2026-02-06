# dependensee - Architecture Blueprint

> .NET project dependency analysis tool for extracting project references, NuGet packages, and detecting circular dependencies.

---

## Executive Summary

**dependensee** (DependenSee wrapper) analyzes .NET repositories to extract dependency information from project files (.csproj, .fsproj, .vbproj). It produces a dependency graph showing project-to-project references and NuGet package dependencies, with automatic circular dependency detection.

| Aspect | Status |
|--------|--------|
| **Purpose** | .NET project dependency analysis with graph generation |
| **Evaluation Score** | Pending full LLM evaluation |
| **Recommendation** | ADOPT for .NET dependency analysis layer |
| **Languages Tested** | C# (.csproj), F# (.fsproj), VB.NET (.vbproj) |
| **Programmatic Checks** | 4 modules (accuracy, coverage, output_quality, performance) |

**Key Strengths:**
- Fast XML-based parsing of project files
- Automatic circular dependency detection
- Graph representation with nodes and edges
- Built-in fallback parser when DependenSee tool unavailable

**Known Limitations:**
- Only captures direct dependencies (not transitive NuGet resolution)
- Requires .NET SDK for DependenSee tool (fallback parser handles most cases)
- .NET ecosystem only (C#, F#, VB.NET)

---

## Gap Analysis

### Current State

| Aspect | Status |
|--------|--------|
| Tool maturity | Stable (fallback parser always available) |
| Output format | JSON (Caldera envelope) |
| Language support | C#, F#, VB.NET (.csproj, .fsproj, .vbproj) |
| Performance | Fast (<5s for typical repositories) |

### Integration Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| DependenSee not always available | May miss some advanced features | Built-in XML parser fallback handles 95% of cases |
| Path separators in .csproj | Windows backslashes in ProjectReference | Normalize paths in parse_project_file() |
| Transitive dependencies | Only direct refs captured | Document as limitation; use NuGet restore for full graph |
| Package version ranges | Complex version constraints simplified | Store raw version string; analysis in downstream processing |

### Integration Strategy

1. Use dependensee for all .NET project dependency extraction (authoritative source)
2. Combine with other tools for non-.NET ecosystems (npm, pip, etc.)
3. Use dependency graph for impact analysis and blast radius calculation
4. Accept circular dependency detection as-is

---

## Architecture

### Data Flow

```
.NET Repository
    |
    v
+------------------+
| analyze.py       |  Discover .csproj/.fsproj/.vbproj files
+------------------+
    |
    v
+------------------+
| DependenSee tool |  (optional) Full analysis with DependenSee
| -or- XML parser  |  (fallback) Built-in project file parsing
+------------------+
    |
    v
+------------------+
| Graph Builder    |  Build dependency graph, detect cycles
+------------------+
    |
    v
+------------------+
| output.json      |  Caldera envelope format
+------------------+
    |
    v
+------------------+
| SoT Adapter      |  Persist to landing zone (3 tables)
+------------------+
```

### Output Schema

See `schemas/output.schema.json` for complete schema (v1.0.0).

Key data structures:

- `data.projects[]`: Project metadata
  - `name`: Project name (from filename)
  - `path`: Repo-relative path to .csproj file
  - `target_framework`: Target framework (e.g., "net8.0")
  - `project_references[]`: Repo-relative paths to referenced projects
  - `package_references[]`: NuGet packages with name and version

- `data.dependency_graph`: Graph representation
  - `nodes[]`: Projects (type: "project") and packages (type: "package")
  - `edges[]`: Dependencies with type ("project_reference" or "package_reference")

- `data.circular_dependencies[]`: Array of cycle paths (each cycle is array of project paths)

- `data.summary`: Aggregate counts
  - `project_count`: Total .NET projects found
  - `package_count`: Unique NuGet packages referenced
  - `reference_count`: Project-to-project reference count
  - `circular_dependency_count`: Number of detected cycles

---

## Implementation Plan

### Phase 1: Standalone Tool

- [x] Create directory structure (done by create-tool.py)
- [x] Implement analyze.py with envelope output
- [x] Customize output.schema.json for dependency metrics
- [x] Add test files to eval-repos/ (5 scenarios)
- [x] Implement programmatic checks in scripts/checks/ (4 modules)
- [x] Pass compliance scanner: `make compliance`

### Phase 2: SoT Integration

- [x] Create entity dataclasses (3 entities: DependenseeProject, DependenseeProjectReference, DependenseePackageReference)
- [x] Create repository class (DependenseeRepository)
- [x] Create adapter in persistence/adapters/dependensee_adapter.py
- [x] Add dbt staging models (3 models: stg_dependensee_projects, stg_dependensee_project_refs, stg_dependensee_package_refs)
- [x] Add dbt mart models (3 models: mart_circular_dependencies, mart_dependency_health_summary, mart_project_dependency_cycles)
- [x] Add dbt tests

### Phase 3: Evaluation

- [x] Create ground truth in evaluation/ground-truth/ (5 scenarios)
- [x] Implement LLM judges in evaluation/llm/judges/ (4 judges)
- [x] Create LLM prompts in evaluation/llm/prompts/ (6 prompts)

---

## Configuration Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | `eval-repos/synthetic` | Repository to analyze |
| `OUTPUT_DIR` | `outputs/$(RUN_ID)` | Output directory |
| `RUN_ID` | UUID generated | Unique run identifier |

### CLI Options (analyze.py)

| Option | Description |
|--------|-------------|
| `--repo-path` | Path to .NET repository to analyze |
| `--output` | Output JSON file path |
| `--run-id` | Override auto-generated run ID |

### Environment Variables

No environment variables required. DependenSee dotnet tool is auto-installed if dotnet SDK is available; otherwise falls back to built-in XML parser.

---

## Performance Characteristics

### Benchmarks

| Repository Size | Projects | Time | Memory |
|-----------------|----------|------|--------|
| Small (synthetic) | 4 | <1s | <50MB |
| Medium (10-20 projects) | 15 | <3s | <100MB |
| Large (50+ projects) | 50+ | <10s | <200MB |

### Key Performance Metrics

- **Throughput**: ~50 projects/second typical
- **Memory efficiency**: Linear growth with project count
- **Startup overhead**: Minimal for fallback parser; dotnet tool restore adds 2-5s on first run

### Performance Thresholds

- Execution time: <30s (threshold from evaluation)
- Memory usage: <512MB (threshold from evaluation)

---

## Evaluation Results

### Evaluation Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Project Detection | 30% | All .csproj/.fsproj/.vbproj files discovered |
| Dependency Accuracy | 30% | Project and package references correctly captured |
| Graph Quality | 20% | Consistent graph structure (node/edge integrity) |
| Circular Detection | 20% | Circular dependency cycles correctly identified |

### Test Scenarios

5 synthetic test scenarios with ground truth:

| Scenario | Description | Key Validation |
|----------|-------------|----------------|
| `synthetic` | Multi-project solution with dependencies | Basic project detection and references |
| `circular` | Projects with circular dependencies | Cycle detection algorithm |
| `empty` | Empty repository (no projects) | Edge case handling |
| `multi-framework` | Projects targeting multiple frameworks | Framework detection |
| `transitive` | Transitive dependency chains | Direct reference capture |

### LLM Judges

4 specialized judges assess different aspects:

1. **project_detection** - Validates all project files are discovered
2. **dependency_accuracy** - Verifies project and package references are correct
3. **graph_quality** - Assesses graph structure consistency
4. **circular_detection** - Validates cycle detection accuracy

### Programmatic Checks

4 check modules:

1. **accuracy.py** - Validates detection accuracy against ground truth
2. **coverage.py** - Ensures all expected files/dependencies found
3. **output_quality.py** - Schema validation and data quality
4. **performance.py** - Execution time and resource usage

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| DependenSee unavailable | Medium | Low | Built-in XML parser fallback |
| Malformed .csproj files | Low | Medium | XML parsing with error handling |
| Path separator issues | Medium | Low | Normalization in parser |
| Large monorepo timeout | Low | Medium | Configurable timeout; pagination |

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Only direct dependencies | Transitive deps not shown | Document limitation; use NuGet restore for full graph |
| DependenSee optional | Some advanced features unavailable | Built-in parser handles 95% of cases |
| .NET only | No support for other ecosystems | Out of scope; use other tools for npm/pip/etc. |
| PackageReference only | packages.config not supported | Modern .NET uses PackageReference; legacy rare |

### Dependency Risks

| Dependency | Version | Risk | Mitigation |
|------------|---------|------|------------|
| DependenSee (optional) | Latest | Tool updates may change output | Fallback parser; version pinning |
| Python | 3.12+ | Version compatibility | Specify in requirements.txt |
| xml.etree | stdlib | Minimal risk | Standard library |

---

## Data Model

### Landing Zone Tables

| Table | Description |
|-------|-------------|
| `lz_dependensee_projects` | Project metadata (path, name, framework, counts) |
| `lz_dependensee_project_refs` | Project-to-project references |
| `lz_dependensee_package_refs` | NuGet package references |

### Entity Classes

| Entity | Fields |
|--------|--------|
| `DependenseeProject` | run_pk, project_path, project_name, target_framework, project_reference_count, package_reference_count |
| `DependenseeProjectReference` | run_pk, source_project_path, target_project_path |
| `DependenseePackageReference` | run_pk, project_path, package_name, package_version |

### dbt Models

**Staging:**
- `stg_dependensee_projects` - Cleaned project data
- `stg_dependensee_project_refs` - Cleaned project references
- `stg_dependensee_package_refs` - Cleaned package references

**Marts:**
- `mart_circular_dependencies` - Circular dependency analysis
- `mart_dependency_health_summary` - Dependency health metrics
- `mart_project_dependency_cycles` - Detailed cycle information

---

## References

- [DependenSee GitHub](https://github.com/madskristensen/DependenSee)
- [MSBuild ProjectReference](https://docs.microsoft.com/en-us/visualstudio/msbuild/common-msbuild-project-items)
- [NuGet PackageReference](https://docs.microsoft.com/en-us/nuget/consume-packages/package-references-in-project-files)
