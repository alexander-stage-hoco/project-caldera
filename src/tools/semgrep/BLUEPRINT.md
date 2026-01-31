# BLUEPRINT: Semgrep PoC Lessons Learned

PoC #4 for evaluating [Semgrep](https://semgrep.dev/) as a code quality and smell detection tool for the DD Platform.

## Executive Summary

**Tool:** Semgrep v1.146.0+
**Purpose:** Pattern-based static analysis for security vulnerabilities and code smells
**Recommendation:** ADOPT for security scanning

| Metric | Result |
|--------|--------|
| Programmatic Checks | 34 (6 dimensions) |
| Pass Rate | 96.4% |
| Overall Score | 69.0% |
| Languages Tested | 7 (Python, JavaScript, TypeScript, C#, Java, Go, Rust) |
| Decision | PASS |

**Key Strengths:**
- Syntax-aware pattern matching (not text grep)
- Multi-language support with unified rule syntax
- Security-focused rule library
- Good performance (6-8 seconds for synthetic repos)
- Zero false positives on clean files

**Key Limitations:**
- Limited DD category coverage (security-focused)
- Empty catch detection: 0% (requires custom rules)
- Async void detection: 0% (requires custom rules)
- Complexity metrics: Not supported (use Lizard)

---

## Summary

| Metric | Value |
|--------|-------|
| Tool | Semgrep v1.146.0 |
| Languages Tested | 7 (Python, JavaScript, TypeScript, C#, Java, Go, Rust) |
| Programmatic Checks | 34 |
| Pass Rate | 96.4% (27/28) |
| Overall Score | 69.0% |
| Synthetic Files | 18 |
| Real Repos | 3 (click, express, Humanizer) |

---

## What Worked

### 1. Security-Focused Detection
Semgrep excels at security-related smell detection:
- SQL injection: 100% detection (AC-1)
- HTTP client security issues: 100% detection (AC-5)
- XSS vulnerabilities: Detected in Express examples
- Cookie session issues: Comprehensive coverage

### 2. Language Support
All 7 target languages are supported with `semgrep --config auto`:
- Python (.py) - Security rules, compatibility checks
- JavaScript (.js, .jsx) - Express-specific rules, XSS detection
- TypeScript (.ts, .tsx) - TypeScript-aware patterns
- C# (.cs) - Memory safety, SSRF detection
- Java (.java) - Security audit rules
- Go (.go) - SQL injection, string formatting
- Rust (.rs) - Basic security rules

### 3. Pattern-Based Analysis
Semgrep's pattern matching is:
- Syntax-aware (not text grep)
- Language-specific tokenization
- Handles metavariables (`$X`, `$FUNC`)
- Supports taint tracking

### 4. Performance
Good performance characteristics:
- Synthetic repos (18 files): ~6-8 seconds
- click (62 files): 8.5 seconds
- express (142 files): 6.6 seconds
- Humanizer (524 files): 6.9 seconds

### 5. JSON Output Format
Comprehensive output includes:
- Per-file smell lists with line numbers
- Rule IDs and severity levels
- Message text explaining the issue
- Metadata for analysis tracking

### 6. Edge Case Handling
- Empty files: Correctly handled (0 smells)
- Unicode content: No encoding errors
- Large files: No timeouts
- Syntax errors: Gracefully ignored
- Clean files: No false positives (EC-6: 100%)

---

## What Didn't Work

### 1. DD Category Mapping
Semgrep's `auto` config focuses on security rules, not DD smell categories. None of the 9 DD categories were mapped:

| DD Category | Semgrep Coverage |
|-------------|------------------|
| error_handling | Limited (no empty catch detection) |
| async_concurrency | None (no async void detection) |
| resource_management | Limited (HTTP client only) |
| size_complexity | None (use lizard instead) |
| dependency | None |
| nullability | None |
| api_design | None |
| dead_code | None |
| refactoring | None |

**Recommendation**: Continue using lizard for complexity and jscpd for duplication. Semgrep complements for security.

### 2. Empty Catch Detection (0%)
The `auto` config doesn't include empty catch block detection:

```python
# This is NOT detected by semgrep --config auto:
try:
    risky_operation()
except Exception:
    pass  # Empty catch - should be flagged
```

**Workaround**: Create custom rules for DD-specific smells.

### 3. Async Void Detection (0%)
C# async void patterns not detected:

```csharp
// This is NOT detected by semgrep --config auto:
public async void ProcessAsync() {  // Should be Task, not void
    await DoWork();
}
```

**Workaround**: Use Roslyn-based analysis for C#-specific patterns.

### 4. High Complexity Detection (50%)
Complexity-based smells require structural analysis, not pattern matching:

```python
# Detected: Nested complexity patterns
# Not detected: Cyclomatic complexity thresholds
```

**Workaround**: Use lizard for complexity metrics.

### 5. Startup Overhead
Semgrep has notable startup time (~30% of total):
- Downloads/caches rules on first run
- Initializes language parsers
- Subsequent runs faster due to caching

---

## Design Decisions

### 1. Use `--config auto`
Started with `auto` config for broadest coverage. This uses Semgrep's curated ruleset focusing on security and correctness.

### 2. Severity Mapping
Semgrep severity maps to DD severity:

| Semgrep | DD | Description |
|---------|-----|-------------|
| ERROR | CRITICAL | Security vulnerabilities |
| WARNING | HIGH | Potential issues |
| INFO | MEDIUM | Recommendations |

### 3. DD Smell ID Assignment
Attempted to map Semgrep rules to DD smell IDs:

```python
DD_SMELL_MAP = {
    "sql-injection": "SEC_SQL_INJECTION",
    "command-injection": "SEC_CMD_INJECTION",
    "empty-catch": "D1_EMPTY_CATCH",  # Would need custom rule
}
```

### 4. Schema v1.0
Output schema includes:
- `files` array with per-file smell counts
- `smells` array with detailed findings
- `metadata` with run info and timing
- `summary` with aggregated metrics

### 5. 16-Section Dashboard
Matched poc-lizard/poc-jscpd pattern:
1. Run Metadata
2. Overall Summary
3. Smells by DD Category
4. Smells by Severity
5. Top Smell Types
6. Language Coverage
7. Files with Most Smells
8. Clean Files Summary
9. Distribution Statistics
10. Sample Findings
11. Category Distribution
12. Severity Breakdown
13. Rule Usage Stats
14. Performance Metrics
15. Configuration Summary
16. Final Summary

---

## Gap Analysis

### Current vs Required Capabilities

| Capability | Status | Gap | Mitigation |
|------------|--------|-----|------------|
| SQL injection | ✅ Full | None | N/A |
| XSS detection | ✅ Full | None | N/A |
| Command injection | ✅ Full | None | N/A |
| Empty catch detection | ⚠️ Missing | Not in auto config | Add custom rules |
| Async void detection | ⚠️ Missing | C# specific, not in auto | Add custom rules |
| Complexity metrics | ⚠️ Missing | Not pattern-based | Use Lizard |
| Code duplication | ⚠️ Missing | Not supported | Use jscpd |
| God class detection | ⚠️ Missing | Requires structural analysis | Use Lizard |
| Dead code detection | ⚠️ Missing | Requires data flow | Future enhancement |

### DD Category Coverage Matrix

| DD Category | Semgrep Coverage | Notes |
|-------------|------------------|-------|
| security | ✅ 100% | Core strength |
| error_handling | ⚠️ Limited | Catch-all only, empty catch needs custom rules |
| resource_management | ⚠️ Limited | HTTP client only |
| size_complexity | ❌ 0% | Use Lizard |
| dependency | ❌ 0% | Use depends |
| nullability | ❌ 0% | Limited pattern support |
| api_design | ❌ 0% | Not pattern-based |
| dead_code | ❌ 0% | Requires data flow |
| refactoring | ❌ 0% | Use jscpd for duplication |

### Recommended Custom Rules

```yaml
# .semgrep/dd-empty-catch.yaml
rules:
  - id: dd-empty-catch-python
    pattern: |
      try:
        ...
      except $EXC:
        pass
    message: "Empty catch block swallows exceptions"
    severity: WARNING
    languages: [python]
    metadata:
      dd_category: error_handling
      dd_smell_id: D1_EMPTY_CATCH

  - id: dd-empty-catch-javascript
    pattern: |
      try { ... } catch ($E) { }
    message: "Empty catch block swallows exceptions"
    severity: WARNING
    languages: [javascript, typescript]
    metadata:
      dd_category: error_handling
      dd_smell_id: D1_EMPTY_CATCH

  - id: dd-async-void-csharp
    pattern: async void $FUNC(...) { ... }
    message: "Async void methods cannot be awaited and exceptions will crash"
    severity: ERROR
    languages: [csharp]
    metadata:
      dd_category: async_concurrency
      dd_smell_id: E2_ASYNC_VOID
```

---

## Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DD Platform                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Collector  │───▶│  Semgrep    │───▶│  Analyzer   │───▶│   DuckDB    │  │
│  │             │    │   CLI       │    │   (Python)  │    │   Storage   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                 │                   │                   │         │
│         │                 ▼                   ▼                   │         │
│         │          ┌─────────────┐    ┌─────────────┐            │         │
│         │          │  Source     │    │   Ground    │            │         │
│         │          │  Code       │    │   Truth     │            │         │
│         │          └─────────────┘    └─────────────┘            │         │
│         │                                    │                    │         │
│         ▼                                    ▼                    │         │
│  ┌─────────────┐                     ┌─────────────┐            │         │
│  │  Evaluation │◀────────────────────│   Checks    │            │         │
│  │   Report    │                     │  (34 total) │            │         │
│  └─────────────┘                     └─────────────┘            │         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Flow

```
1. Input: Repository Path
         ↓
2. Semgrep CLI (Python)
   └── Download/cache rules (first run)
   └── Parse source files (per-language parser)
   └── Match patterns against AST
   └── Output: JSON findings
         ↓
3. Python Analyzer (smell_analyzer.py)
   └── Parse Semgrep JSON
   └── Map Semgrep rule IDs to DD smell IDs
   └── Map Semgrep severity to DD severity
   └── Compute per-file aggregates
   └── Compute directory rollups
   └── Generate dashboard sections
         ↓
4. Evaluation Framework
   └── 34 programmatic checks (6 dimensions)
   └── 4 LLM judges
   └── Scorecard generation
         ↓
5. Output: Analysis JSON + Evaluation Report
```

### Data Transformation Pipeline

```
Semgrep Finding                    DD Smell Entry
┌─────────────────────┐           ┌─────────────────────┐
│ check_id            │ ─────────▶│ dd_smell_id         │
│ path                │ ─────────▶│ file_path           │
│ start.line          │ ─────────▶│ line_start          │
│ end.line            │ ─────────▶│ line_end            │
│ extra.severity      │ ─────────▶│ severity (mapped)   │
│ extra.message       │ ─────────▶│ message             │
│ extra.metadata      │ ─────────▶│ dd_category         │
└─────────────────────┘           └─────────────────────┘
```

---

## Performance Characteristics

### Benchmark Results

| Repository | Files | LOC | Scan Time | LOC/s |
|------------|-------|-----|-----------|-------|
| Synthetic (18 files) | 18 | ~500 | 6-8s | ~70 |
| click (62 files) | 62 | ~8,000 | 8.5s | ~940 |
| express (142 files) | 142 | ~15,000 | 6.6s | ~2,270 |
| Humanizer (524 files) | 524 | ~50,000 | 6.9s | ~7,250 |

### Performance Breakdown

| Phase | First Run | Subsequent Runs |
|-------|-----------|-----------------|
| Rule download | 3-5s | 0s (cached) |
| Parser init | 1-2s | ~0.5s |
| Pattern matching | Varies | ~80% of time |
| JSON output | ~0.2s | ~0.2s |
| **Total (small repo)** | **6-8s** | **2-4s** |

### Performance Thresholds

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Max total time | 45s | Includes first-run rule download |
| Max per-file time | 1000ms | Linear scaling expectation |
| Min throughput | 100 LOC/s | Minimum acceptable speed |
| Startup overhead | < 90% | Analysis should dominate |

### Optimization Tips

1. **Pre-cache rules** - Run `semgrep --config auto --validate` during setup
2. **Use `--jobs`** - Parallelize for large repos
3. **Filter languages** - Use `--include` to skip irrelevant files
4. **Custom config** - Smaller ruleset = faster scanning

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| False negatives (security) | Low | High | Complement with specialized tools |
| False positives | Very Low | Low | Clean file verification |
| Rule update breaks detection | Low | Medium | Pin Semgrep version |
| Performance on large repos | Medium | Medium | Use `--jobs` for parallelism |
| Custom rules maintenance | Medium | Low | Document and test rules |
| Missing DD categories | High | Medium | Use Lizard, jscpd for gaps |

### Security Considerations

1. **Output Security**
   - No sensitive data in output (only rule matches)
   - File paths may reveal project structure

2. **Network Access**
   - First run downloads rules from semgrep.dev
   - Can use `--config <local-path>` for airgapped environments
   - No telemetry by default

3. **Resource Usage**
   - Memory scales with file size
   - CPU usage parallelizable
   - Disk: ~100MB for rule cache

### Compliance Notes

- Semgrep has rules for OWASP Top 10
- Supports PCI-DSS relevant checks
- Can export findings in SARIF format
- Integrates with CI/CD for gate enforcement

---

## Language-Specific Findings

### Python
- Good security coverage (subprocess, SQL, pickle)
- Compatibility checks (Python 2 vs 3)
- Dangerous globals detection

### JavaScript
- Express-specific rules (cookie, XSS)
- DOM manipulation security
- Prototype pollution detection

### TypeScript
- Same rules as JavaScript
- Type-aware patterns (limited)

### C#
- Memory safety (MemoryMarshal)
- SSRF detection (HttpClient)
- Missing: async patterns, LINQ issues

### Java
- SQL injection patterns
- Serialization security
- Missing: resource leaks

### Go
- SQL injection (string formatting)
- Command injection
- Missing: error handling patterns

### Rust
- Basic security rules
- Limited coverage compared to other languages

---

## Integration Recommendations

### 1. Combine with Other Tools

| Tool | Purpose | Layer |
|------|---------|-------|
| scc | File-level LOC, language detection | L1 |
| lizard | Function-level complexity (CCN) | L1 |
| jscpd | Code duplication detection | L1 |
| **Semgrep** | Security and pattern-based smells | L1 |

### 2. Semgrep Role in DD Platform
Use Semgrep specifically for:
- Security vulnerability detection
- Language-specific anti-patterns
- Custom rule enforcement

Use other tools for:
- Complexity metrics (lizard)
- Duplication detection (jscpd)
- C# AST analysis (Roslyn)

### 3. Custom Rules for DD Catalogue
To improve DD category coverage, create custom rules:

```yaml
# .semgrep/dd-rules.yaml
rules:
  - id: dd-empty-catch
    pattern: |
      try:
        ...
      except $EXC:
        pass
    message: "Empty catch block swallows exceptions"
    severity: WARNING
    languages: [python]
    metadata:
      dd_category: error_handling
      dd_smell_id: D1_EMPTY_CATCH
```

### 4. Thresholds and Alerts

| Level | Threshold | Action |
|-------|-----------|--------|
| Critical | Any CRITICAL finding | Block deployment |
| High | >5 HIGH findings | Review required |
| Medium | >10 total findings | Monitor |
| Low | <10 findings | Acceptable |

---

## Configuration Reference

### Recommended Settings

```bash
# Basic analysis
semgrep --config auto --json <target>

# With custom rules
semgrep --config auto --config .semgrep/ --json <target>

# Performance tuning
semgrep --config auto --jobs 4 --timeout 30 <target>
```

### Severity Filtering

```bash
# High severity only
semgrep --config auto --severity ERROR --severity WARNING

# Exclude info-level
semgrep --config auto --exclude-rule "*info*"
```

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/smell_analyzer.py` | Main analysis script (~800 lines) |
| `scripts/evaluate.py` | Evaluation orchestrator |
| `scripts/llm_evaluate.py` | LLM judge orchestrator |
| `scripts/checks/__init__.py` | Check utilities and dataclasses |
| `scripts/checks/accuracy.py` | AC-1 to AC-8 accuracy checks |
| `scripts/checks/coverage.py` | CV-1 to CV-8 coverage checks |
| `scripts/checks/edge_cases.py` | EC-1 to EC-8 edge case checks |
| `scripts/checks/performance.py` | PF-1 to PF-4 performance checks |
| `evaluation/ground-truth/*.json` | 5 language ground truth files |
| `evaluation/llm/judges/*.py` | 4 LLM judges |

---

## Evaluation Results

### Programmatic Evaluation

| Category | Score | Passed |
|----------|-------|--------|
| Accuracy | 47.8% | 8/8 |
| Coverage | 67.5% | 7/8 |
| Edge Cases | 93.8% | 8/8 |
| Performance | 64.8% | 4/4 |
| **Overall** | **69.0%** | **27/28** |

### Key Findings
- SQL injection detection: 100%
- Empty catch detection: 0% (needs custom rules)
- Async void detection: 0% (needs custom rules)
- False positive rate: 0% on clean files
- Performance: Within thresholds

### LLM Evaluation
4 judges configured (35%/25%/20%/20% weights):
- Smell Accuracy
- Rule Coverage
- False Positive Rate
- Actionability

---

## Conclusion

Semgrep is a valuable addition to the DD Platform toolchain for **security-focused smell detection**. However, it should not replace complexity (lizard) or duplication (jscpd) tools.

**Recommended approach**:
1. Use Semgrep's `auto` config for security scanning
2. Create custom rules for DD-specific smells
3. Combine with other tools for comprehensive analysis

**Final Decision**: PASS (69.0%)

Semgrep complements the existing toolchain but does not achieve STRONG PASS due to limited DD category coverage. Consider it a security-focused addition rather than a comprehensive smell detector.

---

## References

- [Semgrep Documentation](https://semgrep.dev/docs/)
- [Semgrep Rules Registry](https://semgrep.dev/explore)
- [Custom Rules Guide](https://semgrep.dev/docs/writing-rules/overview/)
- [PoC #1: scc](../poc-scc/BLUEPRINT.md)
- [PoC #2: lizard](../poc-lizard/BLUEPRINT.md)
- [PoC #3: jscpd](../poc-jscpd/BLUEPRINT.md)
