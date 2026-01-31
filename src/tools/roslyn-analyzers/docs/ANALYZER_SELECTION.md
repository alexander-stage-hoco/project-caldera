# Roslyn Analyzer Package Selection for DD Lenses

## Overview

This document summarizes the analysis of Roslyn analyzer packages from [awesome-analyzers](https://github.com/Cybermaxs/awesome-analyzers) and their mapping to the 9 DD Analyzer lenses.

## The 9 DD Lenses

| Lens | Core Question | Static Analysis Coverage |
|------|---------------|-------------------------|
| **L1** Structural Integrity | Is the codebase modular and maintainable? | **YES** - Complexity, coupling, design rules |
| **L2** Technical Debt | How much debt exists and is it improving? | **YES** - Disposal, async patterns, code quality |
| **L3** Change Risk | How far does change impact spread? | NO - Requires git history |
| **L4** Delivery Flow | Can the team ship reliably? | NO - Requires commit/PR patterns |
| **L5** Knowledge Distribution | Where is knowledge concentrated? | NO - Requires authorship data |
| **L6** Engineering Quality | Does the system prevent defects? | **YES** - Threading, test quality, correctness |
| **L7** Security & License | What latent liabilities exist? | **YES** - OWASP vulnerabilities, unsafe patterns |
| **L8** Cost of Change | How expensive is it to change? | NO - Requires historical trends |
| **L9** Contribution Dynamics | Where is individual leverage? | NO - Requires author analysis |

**Key Insight**: Roslyn analyzers can only cover 4 of 9 lenses directly (L1, L2, L6, L7). The other 5 lenses require git/VCS analysis.

---

## Priority Tiers

### TIER 1: CRITICAL (P0) - Include in PoC

| Analyzer | Lenses | Rationale |
|----------|--------|-----------|
| **SecurityCodeScan** | L7 | Comprehensive .NET security vulnerability detection (OWASP Top 10) |
| **IDisposableAnalyzers** | L2, L6 | Resource leak detection - critical for maintainability |
| **Roslynator** | L1, L2, L6 | 500+ analyzers covering design, quality, performance |
| **Microsoft.VisualStudio.Threading.Analyzers** | L2, L6 | Threading/async correctness - common .NET pitfall |

### TIER 2: HIGH VALUE (P1) - Recommended

| Analyzer | Lenses | Rationale |
|----------|--------|-----------|
| AsyncFixer | L2, L6 | Async/await anti-patterns |
| ErrorProne.NET | L2, L6 | Correctness rules for common mistakes |
| Meziantou.Analyzer | L1, L2, L6 | Good practices enforcement |
| SmartAnalyzers.ExceptionAnalyzer | L2 | Exception handling patterns |
| AspNetCoreAnalyzers | L7 | ASP.NET Core security patterns |
| SonarLint/sonar-dotnet | L1, L2, L6, L7 | Comprehensive multi-lens coverage |

### TIER 3: SUPPLEMENTARY (P2) - Consider

| Analyzer | Lenses | Rationale |
|----------|--------|-----------|
| StyleCopAnalyzers | L1 | Code structure consistency |
| xunit.analyzers | L6 | Test quality (if using xUnit) |
| Moq.Analyzers | L6 | Mock usage quality (if using Moq) |
| BlowinCleanCode | L1, L2 | Code simplification |
| .NET Project File Analyzers | L1, L6 | Build configuration issues |

### NOT RECOMMENDED (Deprecated)

| Analyzer | Reason |
|----------|--------|
| Code Cracker | Deprecated |
| CSharpEssentials | Deprecated |
| RefactoringEssentials | Deprecated |
| VSDiagnostics | Deprecated |
| RoslynClrHeapAllocationAnalyzer | Deprecated |
| Mews.Analyzers | Deprecated |

---

## Lens Coverage Analysis

### L1 - Structural Integrity

**Goal**: Detect modularity issues, complexity, coupling, duplication

| Analyzer | Rules | Coverage |
|----------|-------|----------|
| Roslynator | Complexity metrics, design patterns | HIGH |
| StyleCopAnalyzers | Naming, layout, structure | MEDIUM |
| Meziantou.Analyzer | Design guidelines | MEDIUM |

**Key Rules**:
- `RCS1021` - Simplify if-else
- `CA1502` - Excessive complexity
- `CA1506` - Excessive coupling

### L2 - Technical Debt

**Goal**: Detect complexity debt, resource issues, test gaps

| Analyzer | Rules | Coverage |
|----------|-------|----------|
| IDisposableAnalyzers | Disposal patterns | HIGH |
| AsyncFixer | Async anti-patterns | HIGH |
| ErrorProne.NET | Common mistakes | MEDIUM |

**Key Rules**:
- `IDISP001` - Dispose created
- `IDISP004` - Don't ignore return value
- `AsyncFixer01-05` - Async patterns
- `CA2000` - Dispose objects before losing scope

### L6 - Engineering Quality

**Goal**: Detect test quality issues, correctness problems

| Analyzer | Rules | Coverage |
|----------|-------|----------|
| Microsoft.VisualStudio.Threading.Analyzers | Threading correctness | HIGH |
| xunit.analyzers | Test quality | HIGH (if applicable) |
| ErrorProne.NET | Correctness | MEDIUM |

**Key Rules**:
- `VSTHRD001-200` - Threading rules
- `xUnit1000+` - Test correctness

### L7 - Security

**Goal**: Detect vulnerabilities, secrets, unsafe patterns

| Analyzer | Rules | Coverage |
|----------|-------|----------|
| SecurityCodeScan | OWASP vulnerabilities | HIGH |
| AspNetCoreAnalyzers | Web security | MEDIUM |
| Microsoft.CodeAnalysis.NetAnalyzers | Built-in security | MEDIUM |

**Key Rules**:
- `SCS0001` - SQL Injection
- `SCS0002` - XSS
- `SCS0005` - Weak random
- `SCS0018` - Path traversal
- `CA3001` - SQL Injection
- `CA2300-CA2315` - Deserialization

---

## P0 Package Configuration (Implemented ✅)

```xml
<ItemGroup>
  <!-- Built-in (already included) -->
  <PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="9.0.0" />

  <!-- Security (L7) -->
  <PackageReference Include="SecurityCodeScan.VS2019" Version="5.6.7" />

  <!-- Resource Management (L2) -->
  <PackageReference Include="IDisposableAnalyzers" Version="4.0.8" />

  <!-- Async/Threading (L2, L6) -->
  <PackageReference Include="Microsoft.VisualStudio.Threading.Analyzers" Version="17.11.20" />

  <!-- Comprehensive Quality (L1, L2, L6) -->
  <PackageReference Include="Roslynator.Analyzers" Version="4.12.9" />
</ItemGroup>
```

**Estimated rule count**: ~700+ rules
**Lens coverage**: L1, L2, L6, L7 (4/9 lenses)

---

## P1 Package Configuration (Implemented ✅)

```xml
<ItemGroup>
  <!-- Async Anti-Patterns (L2, L6) -->
  <PackageReference Include="AsyncFixer" Version="1.6.0" />

  <!-- Correctness Rules (L2, L6) -->
  <PackageReference Include="ErrorProne.NET.CoreAnalyzers" Version="0.6.1-beta.1" />

  <!-- Good Practices (L1, L2, L6) -->
  <PackageReference Include="Meziantou.Analyzer" Version="2.0.169" />

  <!-- Exception Handling (L2) -->
  <PackageReference Include="SmartAnalyzers.ExceptionAnalyzer" Version="1.0.10" />

  <!-- Comprehensive Coverage (L1, L2, L6, L7) -->
  <PackageReference Include="SonarAnalyzer.CSharp" Version="10.4.0.108396" />
</ItemGroup>
```

**Additional rule count**: ~770+ rules
**Total rules (P0+P1)**: ~1500+ rules

---

## P2 Package Configuration (Implemented ✅)

```xml
<ItemGroup>
  <!-- Code Style Consistency (L1) -->
  <PackageReference Include="StyleCop.Analyzers" Version="1.1.118" />

  <!-- Test Quality (L6) -->
  <PackageReference Include="xunit.analyzers" Version="1.17.0" />

  <!-- Mock Usage Quality (L6) -->
  <PackageReference Include="Moq.Analyzers" Version="0.0.9" />

  <!-- Code Simplification (L1, L2) -->
  <PackageReference Include="BlowinCleanCode" Version="1.9.0" />

  <!-- Build Configuration Issues (L1, L6) -->
  <PackageReference Include="DotNetProjectFile.Analyzers" Version="1.5.0" />
</ItemGroup>
```

**Additional rule count**: ~320+ rules
**Total rules (P0+P1+P2)**: ~1800+ rules

---

## Current Analysis Results

With P0+P1+P2 packages enabled:

| Metric | Value |
|--------|-------|
| Total Violations | 2206 |
| Files Analyzed | 68 |
| Unique Rules Triggered | 150+ |
| Analysis Duration | ~7.6 seconds |

### Violations by Category

| Category | Count |
|----------|-------|
| Design | 1700 |
| Performance | 192 |
| Dead Code | 152 |
| Resource | 101 |
| Security | 61 |

### Evaluation Results (P0+P1+P2)

| Category | Pass Rate |
|----------|-----------|
| Coverage | 100% (8/8) |
| Performance | 100% (4/4) |
| Edge Cases | 87.5% (7/8) |
| Accuracy | 60% (6/10) |
| **Overall** | 83.3% (25/30) |

**Note**: The accuracy category shows lower scores because:
1. XSS detection (CA3002) and hardcoded secrets (CA5390) require specific patterns not in synthetic files
2. P1+P2 analyzers find many more legitimate issues than originally expected in ground truth
3. "Clean" test files trigger quality rules (SA1633, SA1200, MA0048, S1144, etc.) that are valid findings
4. StyleCop adds ~779 additional style violations (SA prefix rules)

### LLM Evaluation Results (Claude Opus 4.5)

| Judge | Weight | Score | Notes |
|-------|--------|-------|-------|
| Detection Accuracy | 35% | 3/5 | 100% recall, but precision metric misleading due to expanded ground truth |
| Security Coverage | 25% | 4/5 | Strong OWASP coverage (4+ categories), good .NET security rules |
| False Positive Rate | 20% | 2/5 | High style noise on clean files, but no security false positives |
| Actionability | 20% | 4/5 | Clear messages, documentation links, good prioritization |
| **LLM Total** | 100% | **3.25/5** | WEAK_PASS |

### Combined Evaluation

| Component | Score | Weight |
|-----------|-------|--------|
| Programmatic | 0.815 | 60% |
| LLM | 0.650 (3.25/5) | 40% |
| **Combined** | **0.749** | **PASS** |

**Decision**: PASS (>= 0.70 threshold)

---

## Rule Category Mapping

Rules are mapped via exact match in `DD_CATEGORY_MAP` and prefix match in `DD_CATEGORY_PREFIX_MAP`:

### Prefix-Based Mapping (P0 + P1 + P2)

```python
DD_CATEGORY_PREFIX_MAP = {
    # Roslynator (P0)
    "RCS0": "design",       # Formatting rules
    "RCS1": "design",       # Analyzer rules
    "RCS9": "design",       # Refactoring rules

    # AsyncFixer (P1)
    "AsyncFixer": "resource",  # Async anti-patterns

    # ErrorProne.NET (P1)
    "EPC": "design",        # Core rules
    "ERP": "design",        # Struct rules

    # Meziantou.Analyzer (P1)
    "MA0": "design",        # Good practices

    # SmartAnalyzers.ExceptionAnalyzer (P1)
    "EX0": "design",        # Exception handling

    # SonarAnalyzer.CSharp (P1)
    "S1": "design",         # Code smells
    "S2": "design",         # Bugs
    "S3": "design",         # Code smells
    "S4": "security",       # Vulnerabilities
    "S5": "security",       # Security hotspots
    "S6": "design",         # Code smells

    # IDE Analyzers
    "IDE0": "design",       # IDE rules

    # StyleCop.Analyzers (P2)
    "SA0": "design",        # Special rules
    "SA1": "design",        # Spacing rules
    "SA2": "design",        # Readability rules
    "SA3": "design",        # Ordering rules
    "SA4": "design",        # Maintainability rules
    "SA5": "design",        # Layout rules
    "SA6": "design",        # Documentation rules
    "SX0": "design",        # Alternative rules

    # xunit.analyzers (P2)
    "xUnit": "design",      # Test quality rules

    # Moq.Analyzers (P2)
    "Moq": "design",        # Mock quality rules

    # BlowinCleanCode (P2)
    "BCC": "design",        # Code simplification

    # DotNetProjectFile.Analyzers (P2)
    "Proj": "design",       # Project file rules
}
```

### Key Exact Mappings

```python
DD_CATEGORY_MAP = {
    # SecurityCodeScan rules (L7)
    "SCS0001": "security",  # SQL Injection
    "SCS0002": "security",  # XSS
    "SCS0005": "security",  # Weak Random
    "SCS0018": "security",  # Path Traversal
    "SCS0026": "security",  # LDAP Injection
    "SCS0028": "security",  # Insecure Deserialization

    # IDisposableAnalyzers rules (L2)
    "IDISP001": "resource",  # Dispose created
    "IDISP006": "resource",  # Implement IDisposable
    "IDISP017": "resource",  # Prefer using

    # VS Threading Analyzers (L6)
    "VSTHRD100": "design",   # Avoid async void methods
    "VSTHRD110": "design",   # Observe result of async calls
    "VSTHRD111": "design",   # Use ConfigureAwait(bool)

    # See roslyn_analyzer.py for complete mapping (~150 rules)
}
```

---

## Source

Analyzers evaluated from: https://github.com/Cybermaxs/awesome-analyzers

**Total analyzers reviewed**: 41
**Implemented in PoC**: 14 (P0: 4, P1: 5, P2: 5)
**Total rules**: ~1800+
**Total violations detected**: 2206
**Last updated**: 2026-01-06
