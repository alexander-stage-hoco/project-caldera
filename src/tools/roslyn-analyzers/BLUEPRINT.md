# Blueprint: Roslyn Analyzers - .NET Code Quality Analysis

## Executive Summary

**Tool:** .NET SDK Roslyn Analyzers (built-in)
**Purpose:** .NET code quality and security analysis with 200+ rules
**Recommendation:** ADOPT for L6 Engineering Quality and L7 Security lenses

| Metric | Result |
|--------|--------|
| Programmatic Score | 100% (30/30 checks) |
| LLM Score | 4.45/5.0 STRONG_PASS |
| Rule Coverage | 44 rules across 5 categories |
| Integration | Built into .NET SDK |

**Key Strengths:**
- Built-in to .NET SDK (no extra dependencies)
- OWASP security coverage (SQL injection, XSS, crypto)
- Design violation detection (god classes, coupling)
- Resource management (undisposed objects)
- Dead code identification
- SARIF output for tool integration

**Key Limitations:**
- .NET/C# specific
- Some rules require project compilation
- Limited custom rule creation

---

## 1. PoC Objectives

### Primary Goal
Evaluate built-in Roslyn Analyzers for comprehensive .NET code quality assessment.

### Evaluation Criteria
1. **Security Detection** - OWASP Top 10 coverage
2. **Design Analysis** - God classes, coupling violations
3. **Resource Management** - Undisposed objects
4. **Dead Code** - Unused imports, parameters, fields
5. **False Positive Rate** - Clean file accuracy

### Success Metrics
- SQL injection detection rate: >90%
- XSS detection rate: >85%
- False positive rate: <5%
- Design violation coverage: 100%

---

## 2. What Was Built

### Core Analysis Pipeline

| Component | Description |
|-----------|-------------|
| `roslyn_analyzer.py` | Main analysis with SARIF parsing |
| `evaluate.py` | Programmatic evaluation (28 checks) |
| `llm_evaluate.py` | LLM evaluation orchestrator |

### Rules Covered (44 Rules)

| Category | Count | Key Rules |
|----------|-------|-----------|
| Security | 15 | CA3001, CA3002, CA5350, CA2300-2315 |
| Design | 12 | CA1051, CA1040, CA1001, CA1502 |
| Resource | 6 | CA2000, CA2016, CA2007 |
| Dead Code | 6 | IDE0005, IDE0060, IDE0052 |
| Performance | 5 | CA1826, CA1829, CA1825 |

### Test Categories

| Category | Files | Expected Violations |
|----------|-------|---------------------|
| security/ | SQL, XSS, crypto, deserialize | 31 |
| design/ | God class, visible fields | 22 |
| resource/ | Undisposed objects | 22 |
| dead_code/ | Unused imports, fields | 22 |
| clean/ | False positive tests | 0 |

---

## 3. Key Decisions

### Decision 1: Built-in Analyzers
**Choice**: Use .NET SDK built-in analyzers rather than third-party
**Rationale**: No extra dependencies, maintained by Microsoft
**Outcome**: Reliable, up-to-date analysis

### Decision 2: SARIF Output
**Choice**: Parse SARIF output format
**Rationale**: Industry standard, rich metadata
**Outcome**: Structured results with precise locations

### Decision 3: Category Mapping
**Choice**: Map CA/IDE codes to DD security categories
**Rationale**: Consistent categorization across tools
**Outcome**: Unified reporting

---

## 4. DD Lens Coverage

| Lens | Coverage | Rules |
|------|----------|-------|
| L1 Structural | MEDIUM | CA1051, CA1040, CA1502, CA1506 |
| L2 Tech Debt | HIGH | IDE0005, IDE0060, CA2000, CA1001 |
| L6 Quality | HIGH | 44 rules across 5 categories |
| L7 Security | HIGH | CA3001, CA3002, CA5350, CA2300-2315 |

---

## 5. Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Analysis Pipeline                    │
│                                                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ C# Files │───>│  dotnet  │───>│  SARIF   │         │
│  │          │    │  build   │    │  Output  │         │
│  └──────────┘    └──────────┘    └──────────┘         │
│                                        │               │
│                                        v               │
│  ┌──────────────────────────────────────────────────┐ │
│  │              roslyn_analyzer.py                   │ │
│  │  - Parse SARIF                                    │ │
│  │  - Map rule IDs to categories                     │ │
│  │  - Compute aggregates                             │ │
│  │  - Directory rollups                              │ │
│  └──────────────────────────────────────────────────┘ │
│                        │                               │
│                        v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │                    JSON Output                     │ │
│  │  summary, violations, files, rollups              │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

---

## 6. Output Schema

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

---

## 7. Evaluation Framework

### Dual-Track Evaluation

**Programmatic (28 checks):**
- Accuracy: 10 checks (security, design, resource, precision, recall)
- Coverage: 8 checks (rule coverage per category)
- Edge Cases: 8 checks (empty files, unicode, large files)
- Performance: 4 checks (speed, efficiency)

**LLM Judges (4 dimensions):**
- Detection Accuracy (35%)
- Security Coverage (25%)
- False Positive Rate (20%)
- Actionability (20%)

### Decision Thresholds

| Decision | Combined Score |
|----------|----------------|
| STRONG_PASS | >= 0.80 |
| PASS | >= 0.70 |
| WEAK_PASS | >= 0.60 |
| FAIL | < 0.60 |

---

## 8. References

- [.NET Roslyn Analyzers](https://docs.microsoft.com/en-us/dotnet/fundamentals/code-analysis/)
- [CA Rules Reference](https://docs.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/)
- [IDE Rules Reference](https://docs.microsoft.com/en-us/dotnet/fundamentals/code-analysis/style-rules/)
