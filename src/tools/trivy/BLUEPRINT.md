# Trivy Blueprint: Vulnerability Scanner Integration

This document captures the design decisions, implementation details, and lessons learned for the Trivy integration in the DD Platform.

---

## Executive Summary

**Trivy** is a comprehensive vulnerability scanner integrated for package vulnerability and IaC misconfiguration detection.

| Aspect | Status |
|--------|--------|
| **Purpose** | Vulnerability scanning for packages and IaC |
| **Scan Types** | Package vulnerabilities, IaC misconfigurations |
| **Languages** | All (dependency-based) |
| **Severity Levels** | CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN |

**Key Strengths:**
- Fast scanning with local vulnerability database
- Comprehensive package ecosystem support (20+ formats)
- IaC misconfiguration detection for Terraform, K8s, etc.
- CVSS scores and fix availability information

**Known Limitations:**
- No source code analysis (dependency-only)
- False positives for indirect dependencies
- Database updates required for latest CVEs

---

## Gap Analysis

### Gaps Between Trivy Output and Collector Requirements

| Requirement | Trivy Capability | Gap | Mitigation |
|-------------|-----------------|-----|------------|
| File-level vulnerabilities | Per-target vulnerabilities | None | Map targets to files |
| Severity classification | CRITICAL/HIGH/etc | None | Direct mapping |
| Fix availability | fixed_version field | None | Direct mapping |
| CVSS scores | cvss.nvd.V3Score | None | Extract from nested object |
| IaC misconfigurations | Separate output section | None | Handle as separate entity |
| Line numbers | IaC only (not package vulns) | Partial | Use -1 sentinel for package vulns |

### Integration Strategy

1. Use Trivy for package vulnerability detection (authoritative)
2. Combine with semgrep for code-level security issues
3. Use IaC misconfigurations for infrastructure security
4. Aggregate severity counts at target level

---

## What Was Built

### Core Analysis Pipeline

| Component | Description | Lines of Code |
|-----------|-------------|---------------|
| `analyze.py` | Main orchestrator | ~300 |
| `evaluate.py` | Evaluation runner | ~200 |
| `checks/` | Evaluation checks | ~300 |

### Output Schema (v1.0.0)

```
1.0.0
├── metadata
│   ├── tool_name
│   ├── tool_version
│   ├── run_id
│   ├── repo_id
│   ├── branch
│   ├── commit
│   ├── timestamp
│   └── schema_version
└── data
    ├── tool
    ├── tool_version
    ├── targets[]
    │   ├── path
    │   ├── type
    │   ├── vulnerability_count
    │   └── severity_counts
    ├── vulnerabilities[]
    │   ├── id (CVE-XXXX-XXXXX)
    │   ├── package
    │   ├── installed_version
    │   ├── fixed_version
    │   ├── severity
    │   ├── cvss_score
    │   └── title
    └── iac_misconfigurations
        ├── count
        └── misconfigurations[]
```

### Test Repository Structure

```
eval-repos/synthetic/
├── vulnerable-npm/       # Node.js with known CVEs
│   ├── package.json
│   └── package-lock.json
└── iac-terraform/        # Terraform with misconfigurations
    └── main.tf
```

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Analysis Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  trivy CLI  │───▶│  JSON Output    │───▶│  analyze.py     │ │
│  │  fs scan    │    │  (raw)          │    │  (transform)    │ │
│  └─────────────┘    └─────────────────┘    └─────────────────┘ │
│                              │                       │           │
│                              ▼                       ▼           │
│                     ┌─────────────────┐    ┌─────────────────┐ │
│                     │  Envelope JSON  │    │  Validation     │ │
│                     │  (output.json)  │    │  (schema)       │ │
│                     └─────────────────┘    └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Evaluation Framework                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  evaluate.py│───▶│  checks/        │───▶│  Scorecard      │ │
│  │             │    │  (programmatic) │    │  (JSON)         │ │
│  └─────────────┘    └─────────────────┘    └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Scan**: Run `trivy fs --format json` on repository
2. **Transform**: Convert raw trivy JSON to envelope format
3. **Validate**: Check output against JSON schema
4. **Export**: Write to `output/<run-id>/output.json`

---

## Key Decisions

### Decision 1: Filesystem Scanning Mode

**Choice**: Use `trivy fs` (filesystem) mode, not container mode.
**Rationale**: Analyzing source repositories, not built containers.
**Outcome**: Scans lockfiles and manifests directly.

### Decision 2: Multi-Table Output

**Choice**: Separate targets, vulnerabilities, and IaC misconfigs.
**Rationale**: Different data shapes, different aggregation needs.
**Outcome**: Three landing zone tables in sot-engine.

### Decision 3: Target-Level Aggregation

**Choice**: Pre-aggregate severity counts at target level.
**Rationale**: Reduces join complexity for common queries.
**Outcome**: Quick dashboard queries without aggregating vulnerabilities.

### Decision 4: Sentinel Values for Missing Line Numbers

**Choice**: Use -1 for missing line numbers (package vulnerabilities).
**Rationale**: DuckDB primary keys cannot be NULL.
**Outcome**: Consistent handling in landing zone tables.

---

## What Worked Well

### Fast Local Scanning

- Trivy's local database enables fast scans
- No network calls during analysis
- Consistent results across environments

### Comprehensive Package Support

- 20+ package formats supported
- Automatic detection of lockfiles
- No configuration needed per language

### Structured Output

- JSON format with nested severity information
- CVSS scores included where available
- Fix availability clearly indicated

---

## What Could Be Improved

### Database Updates

**Issue**: Local database may be outdated.
**Lesson**: Document update frequency requirements.
**Mitigation**: Run `trivy image --download-db-only` before scans.

### Indirect Dependencies

**Issue**: Transitive dependencies may be flagged.
**Lesson**: Document that not all vulns are directly exploitable.
**Mitigation**: Use severity filtering for actionable results.

### Large Repositories

**Issue**: Scanning large monorepos can be slow.
**Lesson**: Consider parallel scanning by directory.
**Mitigation**: Use `--skip-dirs` for known safe directories.

---

## Performance Characteristics

### Timing Benchmarks

| Repository Size | Files | Scan Time | Transform Time | Total |
|-----------------|-------|-----------|----------------|-------|
| Small (10 deps) | 2 | ~5s | ~1s | ~6s |
| Medium (100 deps) | 5 | ~15s | ~2s | ~17s |
| Large (500 deps) | 10+ | ~45s | ~5s | ~50s |

### Resource Usage

| Metric | Value | Notes |
|--------|-------|-------|
| Memory | 200-500MB | Database loading |
| CPU | 1 core | Single-threaded scan |
| Disk | 500MB | Vulnerability database |

---

## Lessons Learned

### What Worked

- **JSON output mode**: Direct parsing, no scraping needed
- **Severity aggregation**: Pre-computed counts simplify queries
- **Target-based grouping**: Natural organization for results

### What to Improve

- **Database freshness**: Add `--download-db-only` step in CI
- **Large repos**: Consider incremental scanning
- **False positives**: Document filtering strategies

### Recommendations for Future PoCs

1. Always use JSON output mode for CLI tools
2. Pre-aggregate metrics at natural grouping levels
3. Handle missing data with sentinel values, not NULLs
4. Document database/index update requirements

---

## Implementation Plan

### Phase 1: Standalone Tool (Complete)

- [x] Create directory structure following Caldera conventions
- [x] Implement analyze.py with envelope output format
- [x] Create output.schema.json with 8 metadata fields
- [x] Add synthetic eval-repos (vulnerable-npm, iac-terraform)
- [x] Implement programmatic evaluation checks
- [x] Pass compliance scanner

### Phase 2: SoT Integration (Complete)

- [x] Create entity dataclasses (TrivyTarget, TrivyVulnerability, TrivyMisconfiguration)
- [x] Create repository class (TrivyRepository)
- [x] Create adapter (TrivyAdapter)
- [x] Add landing zone tables to schema.sql
- [x] Create dbt staging models

### Phase 3: Evaluation (Complete)

- [x] Create ground truth files for synthetic repos
- [x] Implement LLM judges (vulnerability_accuracy, coverage, actionability)
- [x] Create LLM prompts
- [x] Generate scorecard

---

## Evaluation

### Evaluation Approach

The evaluation uses a hybrid approach with 60% programmatic checks and 40% LLM-as-a-Judge:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective accuracy, coverage, completeness |
| LLM Judges | 40% | Semantic understanding, actionability |

### Evaluation Dimensions

| Dimension | Checks | Weight | Focus |
|-----------|--------|--------|-------|
| Accuracy | TR-AC-1 to TR-AC-5 | 40% | Vulnerability counts, severity classification |
| Coverage | TR-CV-1 to TR-CV-3 | 30% | Target and package detection |
| Completeness | TR-CM-1 to TR-CM-4 | 30% | Data structure integrity |

### Running Evaluation

```bash
# Programmatic evaluation
make evaluate

# LLM evaluation
make evaluate-llm

# Single repo evaluation
make evaluate-single REPO_NAME=vulnerable-npm
```

See `EVAL_STRATEGY.md` for detailed check catalog and scoring methodology.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Database staleness | Medium | High | Run `trivy image --download-db-only` before scans |
| False positives | Medium | Medium | Document filtering strategies, use severity thresholds |
| Large repo timeout | Medium | Low | Configurable timeout (600s default), --skip-dirs option |
| Transitive dependencies | Low | Medium | Document that not all vulns are directly exploitable |
| Schema migration | Low | Medium | Versioned schema (1.0.0) |

---

## Configuration Reference

### Makefile Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | `eval-repos/synthetic/vulnerable-npm` | Repository to scan |
| `REPO_NAME` | `vulnerable-npm` | Project name |
| `OUTPUT_DIR` | `output/runs` | Output directory |
| `TRIVY_TIMEOUT` | `600` | Scan timeout in seconds |

### CLI Options (analyze.py)

| Option | Description |
|--------|-------------|
| `--repo-path` | Path to repository to analyze |
| `--repo-name` | Project name |
| `--output-dir` | Output directory |
| `--run-id` | Unique run identifier |
| `--repo-id` | Repository identifier |
| `--branch` | Git branch name |
| `--commit` | Git commit SHA |
| `--timeout` | Scan timeout in seconds |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TRIVY_DB_REPOSITORY` | Custom vulnerability database location |
| `TRIVY_CACHE_DIR` | Cache directory for database |

---

## References

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Trivy GitHub](https://github.com/aquasecurity/trivy)
- [NVD CVE Database](https://nvd.nist.gov/)
- [CVSS Scoring](https://www.first.org/cvss/)
