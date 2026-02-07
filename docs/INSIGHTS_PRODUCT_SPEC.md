# Insights Product Specification

## Technical Due Diligence Platform for PE Investment Decisions

**Version:** 1.0.0
**Status:** Draft
**Last Updated:** 2026-02-02

---

## Executive Summary

Project Caldera's Insights component delivers automated technical due diligence reports for Private Equity transactions. The platform produces **evidence-based technical assessments** that enable CTOs to make defensible platform decisions (extend / modernise / replace) and communicate them to Investment Committees.

**Core Principle:** Every technical claim must follow the structure:

```
Claim → Evidence → Implication → Confidence
```

If we cannot point to concrete evidence, the claim does not belong in the output.

---

## Table of Contents

1. [Stakeholder Requirements](#1-stakeholder-requirements)
2. [Current Capabilities](#2-current-capabilities)
3. [Gap Analysis](#3-gap-analysis)
4. [Target Architecture](#4-target-architecture)
5. [New Tools Required](#5-new-tools-required)
6. [Evidence & Claim Framework](#6-evidence--claim-framework)
7. [Deliverable Specifications](#7-deliverable-specifications)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Success Criteria](#9-success-criteria)

---

## 1. Stakeholder Requirements

### 1.1 CTO / VP Engineering

**Purpose:** Assess maintainability, technical debt, and execution risk for platform decisions.

| Need | Question Answered |
|------|-------------------|
| Complexity hotspots | "Which files/modules require the most effort to change safely?" |
| Coupling assessment | "Where would the system resist us if we needed to change supplier logic?" |
| Architecture health | "Which modules are well-structured vs. problematic?" |
| Security posture | "What vulnerabilities require immediate attention?" |
| Knowledge concentration | "Where is tribal knowledge creating bus factor risk?" |
| Test safety | "Which complex areas lack test coverage?" |

**Output Requirements:**
- Detailed technical evidence with file:line references
- Sampling rationale explaining what was analyzed and why
- Pattern observations (good and bad) with concrete examples
- Actionable risk register with technical causes

### 1.2 PE Investor / Investment Committee

**Purpose:** Risk quantification, investment thesis validation, deal-breaker identification.

| Need | Question Answered |
|------|-------------------|
| Risk score | "What is the overall technical risk level (0-100)?" |
| Deal blockers | "Are there issues that should stop the transaction?" |
| Hidden costs | "What technical debt will require investment post-close?" |
| Scalability | "Can the platform grow with the business?" |
| Security exposure | "What regulatory or breach risks exist?" |
| Rewrite probability | "Will 'modernisation' silently become a rewrite?" |

**Output Requirements:**
- Single-page executive summary with traffic light status
- Quantified risk scores with confidence levels
- Investment requirements (pre-close and post-close)
- Top 3-5 findings ranked by business impact

### 1.3 CEO / Business Leader

**Purpose:** Go/no-go signals, business risk translation, investment planning.

| Need | Question Answered |
|------|-------------------|
| Overall status | "Red/Yellow/Green—should we proceed?" |
| Business impact | "How does technical risk affect time-to-market?" |
| Cost implications | "What remediation investment is required?" |
| Competitive position | "Does the technology enable or constrain growth?" |
| Team implications | "Are there key-person dependencies?" |

**Output Requirements:**
- Non-technical summary with business context
- Clear recommendation with conditions
- Risk-to-business translation
- Timeline implications (without specific estimates)

---

## 2. Current Capabilities

### 2.1 Data Assets (9 Tools Integrated)

| Tool | Data Produced | Landing Zone Tables |
|------|---------------|---------------------|
| **layout-scanner** | File inventory, directory structure | `lz_layout_files`, `lz_layout_directories` |
| **scc** | LOC, complexity, comment ratios | `lz_scc_file_metrics` |
| **lizard** | Function-level CCN, NLOC | `lz_lizard_file_metrics`, `lz_lizard_function_metrics` |
| **semgrep** | Code smells by category | `lz_semgrep_smells` |
| **roslyn-analyzers** | .NET violations | `lz_roslyn_violations` |
| **sonarqube** | Issues, duplication | `lz_sonarqube_issues`, `lz_sonarqube_metrics` |
| **trivy** | CVEs, IaC misconfigs | `lz_trivy_vulnerabilities`, `lz_trivy_iac_misconfigs` |
| **gitleaks** | Exposed secrets | `lz_gitleaks_secrets` |
| **git-sizer** | Repository health | `lz_git_sizer_metrics`, `lz_git_sizer_violations` |

### 2.2 Aggregation Capabilities

**Directory Rollups:** Every tool produces recursive and direct rollups with 22 distribution statistics:

- Basic: count, min, max, mean, median, stddev
- Percentiles: p25, p50, p75, p90, p95, p99
- Inequality: gini, palma_ratio, hoover_index, theil_index
- Concentration: top_10_share, top_20_share, bottom_10_share
- Shape: skewness, kurtosis, coefficient_of_variation, iqr

### 2.3 Current Insight Sections (12)

| Section | Purpose | Data Sources |
|---------|---------|--------------|
| ExecutiveSummary | Top 3 prioritized insights | All tools |
| RepoHealth | Overview metrics, health grade | git-sizer, scc, lizard |
| FileHotspots | Top files by complexity, LOC, smells | lizard, scc, semgrep |
| DirectoryAnalysis | Directory-level hotspots | All rollups |
| Vulnerabilities | Security vulnerability summary | trivy |
| Secrets | Exposed credentials | gitleaks |
| CrossTool | Compound risks (complex + smelly) | Cross-tool joins |
| LanguageCoverage | Language distribution | layout, scc |
| RoslynViolations | .NET specific findings | roslyn |
| IacMisconfigs | Infrastructure issues | trivy |
| ModuleHealth | Composite health scores | All rollups |
| CodeInequality | Distribution analysis | Gini, Palma metrics |

---

## 3. Gap Analysis

### 3.1 Capability Gaps

| Requirement | Current State | Impact |
|-------------|---------------|--------|
| **Evidence chains** | Produce summaries, not traceable evidence | CTO cannot audit claims |
| **Claim-Evidence linking** | No structured claim register | Findings lack defensibility |
| **Component boundaries** | See files, not logical components | Cannot assess coupling |
| **Interaction patterns** | No call graph or dependency analysis | Cannot identify change amplification |
| **Sampling rationale** | Analyze everything equally | No risk-driven focus |
| **Changeability assessment** | Measure complexity, not change cost | Cannot answer "where will the system resist us?" |
| **Rewrite risk signals** | No detection of structural constraints | Cannot identify hidden rewrite triggers |
| **Code ownership** | No git blame integration | Cannot assess knowledge concentration |
| **Test coverage** | No coverage data ingestion | Cannot identify risk zones |

### 3.2 Deliverable Gaps

| Brief Deliverable | Current Coverage | Missing |
|-------------------|------------------|---------|
| Technical Evidence Pack | 40% | Evidence IDs, location references, "why it matters" |
| Claim Register | 0% | Entire capability |
| Component Inventory | 30% | Responsibilities, interactions, data ownership |
| Code Quality Report | 60% | Sampling rationale, pattern narrative |
| Risk Register | 40% | "Triggered by" reasoning, technical causes |
| Rewrite Risk Memo | 20% | Structural vs addressable assessment |

---

## 4. Target Architecture

### 4.1 Layered Evidence Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RAW DATA LAYER                                   │
│  Layout │ SCC │ Lizard │ Semgrep │ Trivy │ Gitleaks │ Git-sizer            │
│  + NEW: Symbol Scanner │ Git Blame │ Coverage Ingest                       │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                          EVIDENCE LAYER                                     │
│  EvidenceItem: id, type, location, excerpt, observation, why_it_matters    │
│  Every finding becomes an auditable evidence item with unique ID           │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                            CLAIM LAYER                                      │
│  TechnicalClaim: id, statement, evidence_ids[], implication, confidence    │
│  Pattern-based claim generation from metrics                               │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                            RISK LAYER                                       │
│  ExecutionRisk: id, description, claim_ids[], triggered_by, severity       │
│  Aggregated risks with business impact                                     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                        DELIVERABLE LAYER                                    │
│  Evidence Pack │ Claim Register │ Component Inventory │ Risk Register      │
│  Stakeholder-specific reports (CTO, Investor, CEO)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Cross-Tool Analysis Queries

**Blast Radius (from architecture proposal):**

```sql
-- Transitive callers of a symbol—measures impact of changes
WITH RECURSIVE call_chain AS (
    SELECT caller_name, callee_name, file_path, 1 AS depth
    FROM symbol_calls
    WHERE run_id = ? AND callee_name = ?  -- Target symbol

    UNION ALL

    SELECT sc.caller_name, sc.callee_name, sc.file_path, cc.depth + 1
    FROM symbol_calls sc
    JOIN call_chain cc ON sc.callee_name = cc.caller_name
    WHERE cc.depth < 5 AND sc.run_id = ?
)
SELECT caller_name, file_path, MIN(depth) AS min_depth, COUNT(*) AS path_count
FROM call_chain
GROUP BY caller_name, file_path;
```

**Coupling Metrics:**

```sql
-- Symbol coupling: fan-in and fan-out with instability metric
SELECT
    cs.symbol_name,
    cs.symbol_type,
    cs.file_path,
    COALESCE(fan_out.count, 0) AS fan_out,
    COALESCE(fan_in.count, 0) AS fan_in,
    -- Instability: fan_out / (fan_in + fan_out)
    CASE
        WHEN COALESCE(fan_out.count, 0) + COALESCE(fan_in.count, 0) = 0 THEN 0
        ELSE COALESCE(fan_out.count, 0)::DOUBLE /
             (COALESCE(fan_out.count, 0) + COALESCE(fan_in.count, 0))
    END AS instability
FROM code_symbols cs
LEFT JOIN (SELECT caller_name, COUNT(DISTINCT callee_name) AS count FROM symbol_calls GROUP BY caller_name) fan_out
    ON cs.symbol_name = fan_out.caller_name
LEFT JOIN (SELECT callee_name, COUNT(DISTINCT caller_name) AS count FROM symbol_calls GROUP BY callee_name) fan_in
    ON cs.symbol_name = fan_in.callee_name;
```

**Coverage Gap Analysis:**

```sql
-- Files with low coverage AND high complexity = critical risk
SELECT
    fm.file_path,
    fm.line_coverage_pct,
    fm.max_ccn,
    CASE
        WHEN fm.line_coverage_pct < 50 AND fm.max_ccn > 15 THEN 'critical'
        WHEN fm.line_coverage_pct < 70 AND fm.max_ccn > 10 THEN 'high'
        WHEN fm.line_coverage_pct < 80 THEN 'medium'
        ELSE 'low'
    END AS risk_level
FROM unified_file_metrics fm
WHERE fm.max_ccn > 5 AND fm.line_coverage_pct IS NOT NULL
ORDER BY risk_level, fm.max_ccn DESC;
```

**Composite Risk Scoring:**

```sql
-- Weighted risk score: complexity 30%, coupling 25%, vulns 30%, coverage 15%
SELECT
    file_path,
    ROUND(
        ccn_norm * 0.30 +
        fan_in_norm * 0.25 +
        vuln_norm * 0.30 +
        coverage_gap * 0.15,
        3
    ) AS risk_score
FROM (
    SELECT
        file_path,
        COALESCE(max_ccn, 0)::DOUBLE / NULLIF(MAX(max_ccn) OVER(), 0) AS ccn_norm,
        COALESCE(total_fan_in, 0)::DOUBLE / NULLIF(MAX(total_fan_in) OVER(), 0) AS fan_in_norm,
        COALESCE(vuln_count, 0)::DOUBLE / NULLIF(MAX(vuln_count) OVER(), 0) AS vuln_norm,
        (100 - COALESCE(line_coverage_pct, 100)) / 100.0 AS coverage_gap
    FROM unified_file_metrics
) metrics
WHERE ccn_norm > 0 OR fan_in_norm > 0 OR vuln_norm > 0
ORDER BY risk_score DESC;
```

---

## 5. New Tools Required

### 5.1 Symbol Scanner (Priority: P1)

**Purpose:** Extract function/class definitions and call relationships for coupling analysis.

**Languages:** Python, JavaScript/TypeScript, C#, Java, Go

**Schema:**

```sql
CREATE TABLE lz_code_symbols (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    symbol_name VARCHAR NOT NULL,
    symbol_type VARCHAR NOT NULL,  -- function, class, method, variable
    line_start INTEGER,
    line_end INTEGER,
    is_exported BOOLEAN DEFAULT FALSE,
    parameters INTEGER,
    PRIMARY KEY (run_pk, file_id, symbol_name)
);

CREATE TABLE lz_symbol_calls (
    run_pk BIGINT NOT NULL,
    caller_file_id VARCHAR NOT NULL,
    caller_symbol VARCHAR NOT NULL,
    callee_symbol VARCHAR NOT NULL,
    callee_file_id VARCHAR,  -- NULL if external/unresolved
    line_number INTEGER,
    call_type VARCHAR,  -- direct, dynamic, async
    PRIMARY KEY (run_pk, caller_file_id, caller_symbol, callee_symbol, line_number)
);

CREATE TABLE lz_file_imports (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    imported_path VARCHAR NOT NULL,
    imported_symbols VARCHAR,  -- comma-separated or NULL for *
    import_type VARCHAR,  -- static, dynamic, side-effect
    line_number INTEGER,
    PRIMARY KEY (run_pk, file_id, imported_path)
);
```

**Extractors:**

| Language | Extraction Method |
|----------|-------------------|
| Python | `ast` module (stdlib) |
| JavaScript/TypeScript | tree-sitter or TypeScript Compiler API |
| C# | Roslyn (extend existing tool) |
| Java | JavaParser or jdeps |
| Go | go/ast package |

**dbt Models:**

- `stg_code_symbols` - Staging layer
- `stg_symbol_calls` - Staging layer
- `rollup_symbols_directory_counts` - Symbol count per directory
- `rollup_coupling_directory_metrics` - Fan-in/fan-out per directory

### 5.2 Git Blame Scanner (Priority: P2)

**Purpose:** Determine code ownership and knowledge concentration.

**Schema:**

```sql
CREATE TABLE lz_git_blame_summary (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    total_lines INTEGER,
    unique_authors INTEGER,
    top_author VARCHAR,
    top_author_lines INTEGER,
    top_author_pct DOUBLE,
    last_modified DATE,
    churn_30d INTEGER,
    churn_90d INTEGER,
    PRIMARY KEY (run_pk, file_id)
);

CREATE TABLE lz_git_author_stats (
    run_pk BIGINT NOT NULL,
    author_email VARCHAR NOT NULL,
    total_files INTEGER,
    total_lines INTEGER,
    exclusive_files INTEGER,  -- files where they're only author
    avg_ownership_pct DOUBLE,
    PRIMARY KEY (run_pk, author_email)
);
```

**Implementation:**

```bash
# Per-file author summary (fast)
git log --format='%ae' --follow -- <file> | sort | uniq -c | sort -rn

# Churn metrics
git log --oneline --since="30 days ago" -- <file> | wc -l
```

### 5.3 Coverage Ingest (Priority: P2)

**Purpose:** Ingest existing test coverage reports for gap analysis.

**Supported Formats:** lcov, cobertura, jacoco, istanbul

**Schema:**

```sql
CREATE TABLE lz_coverage_summary (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,
    line_coverage_pct DOUBLE,
    branch_coverage_pct DOUBLE,
    lines_total INTEGER,
    lines_covered INTEGER,
    lines_missed INTEGER,
    source_format VARCHAR,
    PRIMARY KEY (run_pk, file_id)
);
```

---

## 6. Evidence & Claim Framework

### 6.1 Evidence Item Structure

```python
@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str              # E-CCN-001, E-SEC-042, etc.
    evidence_type: str            # code, config, schema, runtime, metric
    location: str                 # file:line or directory or metric query
    excerpt: str                  # Short snippet or value
    observation: str              # What we see
    why_it_matters: str           # Why CTO should care
    tool_source: str              # Which tool produced this
    run_pk: int                   # Link to collection run
    confidence: str               # High/Medium/Low
```

**Example:**

```json
{
  "evidence_id": "E-CCN-042",
  "evidence_type": "code",
  "location": "src/services/OrderProcessor.cs:L147-L298",
  "excerpt": "ProcessOrder() - 47 CCN, 152 NLOC, 12 parameters",
  "observation": "Function exceeds complexity threshold (CCN > 20)",
  "why_it_matters": "High CCN increases change risk: modifications require understanding 47 independent paths through this function",
  "tool_source": "lizard",
  "confidence": "High"
}
```

### 6.2 Technical Claim Structure

```python
@dataclass(frozen=True)
class TechnicalClaim:
    claim_id: str                 # CLM-COUP-001, CLM-SEC-012, etc.
    category: str                 # coupling, complexity, security, coverage, ownership
    statement: str                # Precise technical claim
    evidence_ids: list[str]       # Links to evidence
    implication: str              # What this means for changeability
    confidence: str               # High/Medium/Low based on evidence breadth
    triggered_by: str | None      # What change would expose this risk
```

**Example:**

```json
{
  "claim_id": "CLM-COUP-003",
  "category": "coupling",
  "statement": "The platform exhibits tight coupling via shared database access patterns in the OrderService module",
  "evidence_ids": ["E-SYM-014", "E-SYM-022", "E-SQL-008"],
  "implication": "Changes to order data model require coordinated updates across 4 services; high change amplification risk",
  "confidence": "High",
  "triggered_by": "Any modification to order schema or OrderService interfaces"
}
```

### 6.3 Claim Generation Patterns

| Pattern | Detection Query | Claim Template |
|---------|-----------------|----------------|
| Complexity concentration | `gini_ccn > 0.7 AND file_count > 10` | "Complexity is concentrated in directory {path} (Gini={value})" |
| High coupling | `fan_out > fan_in * 3` | "Module {path} exhibits high outbound coupling ({fan_out} external calls)" |
| Knowledge silo | `unique_authors = 1 AND code_lines > 500` | "File {path} ({loc} LOC) has single author—bus factor risk" |
| Coverage gap | `coverage < 50 AND ccn > 15` | "File {path} is high-risk: {ccn} CCN with {coverage}% coverage" |
| Security exposure | `critical_vulns > 0` | "Platform has {count} critical vulnerabilities requiring immediate remediation" |
| Pervasive debt | `smell_ratio > 0.5` | "Code smell {type} affects {pct}% of files—systemic pattern" |

### 6.4 Execution Risk Structure

```python
@dataclass(frozen=True)
class ExecutionRisk:
    risk_id: str                  # RISK-001, RISK-002, etc.
    description: str              # Human-readable risk description
    technical_cause: str          # What creates this risk
    claim_ids: list[str]          # Claims that support this risk
    manifests_in: list[str]       # Directories/files affected
    triggered_by: str             # What change activates risk
    severity: str                 # Critical/High/Medium/Low
```

**Example:**

```json
{
  "risk_id": "RISK-007",
  "description": "Supplier integration changes require coordinated updates across 4 services",
  "technical_cause": "Shared database schema acts as implicit API between services",
  "claim_ids": ["CLM-COUP-003", "CLM-COUP-008"],
  "manifests_in": ["src/services/supplier/", "src/services/pricing/", "src/services/contracts/", "src/services/orders/"],
  "triggered_by": "Any change to supplier data model or integration logic",
  "severity": "High"
}
```

---

## 7. Deliverable Specifications

### 7.1 Technical Evidence Pack

**Purpose:** Proof repository backing all technical claims.

**Format:**

```markdown
# Technical Evidence Pack

## Evidence Index

| ID | Type | Location | Tool |
|----|------|----------|------|
| E-CCN-001 | code | src/services/OrderProcessor.cs:L147 | lizard |
| E-SEC-042 | vuln | package.json (lodash@4.17.15) | trivy |
| E-OWN-003 | metric | src/core/ directory | git-blame |

## Evidence Items

### E-CCN-001: High Complexity Function

- **Type:** code
- **Location:** src/services/OrderProcessor.cs:L147-L298
- **Excerpt:** `ProcessOrder() - 47 CCN, 152 NLOC, 12 parameters`
- **Observation:** Function exceeds complexity threshold (CCN > 20)
- **Why It Matters:** High CCN increases change risk: modifications require understanding 47 independent paths
- **Confidence:** High

[... additional evidence items ...]
```

### 7.2 Claim Register

**Purpose:** Structured list of substantive technical claims linked to evidence.

**Format:**

```markdown
# Claim Register

## Claims by Category

### Coupling (4 claims)

#### CLM-COUP-001: Shared Database Coupling

- **Statement:** The platform exhibits tight coupling via shared database access
- **Evidence:** E-SYM-014, E-SYM-022, E-SQL-008
- **Implication:** High change amplification risk
- **Confidence:** High
- **Triggered By:** Any modification to shared data model

[... additional claims ...]

## Summary Statistics

| Category | Count | High Confidence | Medium | Low |
|----------|-------|-----------------|--------|-----|
| Coupling | 4 | 3 | 1 | 0 |
| Complexity | 7 | 5 | 2 | 0 |
| Security | 3 | 3 | 0 | 0 |
| Coverage | 2 | 1 | 1 | 0 |
| Ownership | 2 | 2 | 0 | 0 |
```

### 7.3 Component & Interaction Inventory

**Purpose:** System map grounded in repository reality.

**Format:**

```markdown
# Component Inventory

## Major Components

### 1. OrderService (src/services/orders/)

- **Responsibilities:** Order creation, validation, lifecycle management
- **Files:** 23 | **LOC:** 4,521 | **Avg CCN:** 12.3
- **Health Grade:** C (68/100)

**Dependencies (Outbound):**
| Target | Type | Call Count |
|--------|------|------------|
| SupplierService | sync | 47 |
| PricingEngine | sync | 32 |
| Database (orders.*) | data | 156 |

**Dependents (Inbound):**
| Source | Type | Call Count |
|--------|------|------------|
| APIController | sync | 28 |
| BatchProcessor | async | 12 |

**Hotspots:**
- OrderProcessor.cs (47 CCN, single author)
- ValidationRules.cs (23 CCN, 12 code smells)

**Risk Signals:**
- High outbound coupling (fan_out = 235)
- Knowledge concentration (top author = 78%)

[... additional components ...]
```

### 7.4 Code Quality & Changeability Sampling Report

**Purpose:** Summarize sampled findings with explicit rationale.

**Format:**

```markdown
# Code Quality Sampling Report

## Sampling Strategy

We selected files for detailed review based on composite risk score:

```
risk_score = (ccn_norm × 0.30) + (coupling_norm × 0.25) + (vuln_norm × 0.30) + (coverage_gap × 0.15)
```

**Files Sampled:** 20 (top 5% by risk score)
**Total LOC Sampled:** 8,421 (12% of codebase)

## Sampling Targets

| File | Risk Score | Rationale |
|------|------------|-----------|
| OrderProcessor.cs | 0.87 | High CCN (47) + low coverage (32%) |
| SupplierIntegration.cs | 0.82 | High coupling (fan_out=89) + critical vulns |
| PricingEngine.cs | 0.76 | High complexity + knowledge silo |

## Pattern Observations

### Good Patterns Observed

1. **Consistent error handling in API layer** (Evidence: E-PAT-001)
   - Location: src/api/controllers/
   - Pattern: Centralized exception middleware with structured logging
   - Implication: Errors are traceable; debugging is efficient

2. **Clear separation in data access layer** (Evidence: E-PAT-002)
   - Location: src/data/repositories/
   - Pattern: Repository pattern with interface abstraction
   - Implication: Database technology could be changed with bounded impact

### Bad/Risky Patterns Observed

1. **God class with mixed responsibilities** (Evidence: E-PAT-010)
   - Location: src/services/OrderProcessor.cs
   - Pattern: Single class handles validation, pricing, fulfillment, and notifications
   - Implication: Changes to any responsibility risk breaking others
   - Example: Lines 147-298 contain 47 CCN function mixing 4 concerns

2. **Business logic in database triggers** (Evidence: E-PAT-011)
   - Location: Database schema (not in repo)
   - Pattern: Pricing recalculation happens in SQL trigger
   - Implication: Business rules are hidden from code review; testing is difficult

3. **Hardcoded configuration in code** (Evidence: E-PAT-012)
   - Location: src/services/SupplierIntegration.cs:L42
   - Pattern: API endpoints and credentials embedded in source
   - Implication: Environment changes require code deployment

## Changeability Assessment

| Area | Changeability | Rationale |
|------|---------------|-----------|
| API Layer | High | Clear boundaries, good test coverage |
| Order Processing | Low | High complexity, tight coupling, single author |
| Supplier Integration | Low | External dependencies, hardcoded config |
| Data Layer | Medium | Good abstraction, but schema coupling |
```

### 7.5 Engineering Execution Risk Register

**Purpose:** Prioritized list of risks with technical causes.

**Format:**

```markdown
# Execution Risk Register

## Critical Risks

### RISK-001: Security Vulnerability Exposure

- **Description:** 5 critical CVEs in production dependencies require immediate patching
- **Technical Cause:** Outdated dependency versions (lodash@4.17.15, log4j@2.14.0)
- **Manifests In:** package.json, pom.xml
- **Triggered By:** Any security audit or penetration test
- **Supporting Claims:** CLM-SEC-001, CLM-SEC-002
- **Evidence:** E-SEC-001 through E-SEC-005

### RISK-002: Change Amplification in Order Domain

- **Description:** Modifications to order logic require coordinated changes across 4 services
- **Technical Cause:** Shared database schema acts as implicit API; no service boundaries
- **Manifests In:** src/services/orders/, src/services/pricing/, src/services/suppliers/, src/services/contracts/
- **Triggered By:** Any change to order data model, pricing rules, or supplier integration
- **Supporting Claims:** CLM-COUP-001, CLM-COUP-003
- **Evidence:** E-SYM-014, E-SYM-022, E-SQL-008

## High Risks

[... additional risks ...]

## Risk Summary

| Severity | Count | Top Category |
|----------|-------|--------------|
| Critical | 2 | Security |
| High | 5 | Coupling |
| Medium | 8 | Complexity |
| Low | 4 | Coverage |
```

### 7.6 Implicit Rewrite Risk Memo

**Purpose:** Identify where incremental evolution breaks down.

**Format:**

```markdown
# Implicit Rewrite Risk Assessment

## Executive Summary

Based on structural analysis, **incremental modernisation is viable with constraints**. Two areas present significant rewrite risk if requirements change substantially.

## Where Incremental Evolution Breaks Down

### 1. Order Processing Core (HIGH REWRITE RISK)

**Constraint Type:** Structural (not addressable incrementally)

**Evidence:**
- Single 4,500 LOC module handles 4 distinct responsibilities (E-STRUCT-001)
- 67% of order-related complexity in one file (Gini = 0.78) (E-DIST-003)
- No clear seams for decomposition (E-ARCH-002)

**Assumption That Would Fail:**
> "We can incrementally extract microservices from the monolith"

**Why It Fails:** The OrderProcessor class has no internal boundaries. Extracting any single responsibility requires understanding and modifying all others. This is not incremental; it's a rewrite of the order domain.

**Trigger Condition:** Any requirement to independently scale or deploy order processing components.

### 2. Database Schema Coupling (MEDIUM REWRITE RISK)

**Constraint Type:** Addressable, but requires coordinated effort

**Evidence:**
- 12 services directly access `orders.*` tables (E-SQL-008)
- No abstraction layer between services and schema (E-ARCH-005)
- Schema changes require coordinated deployment of all services (E-OPS-003)

**Assumption That Would Fail:**
> "We can evolve the data model incrementally with backward compatibility"

**Why It Fails:** Current direct access pattern means any schema change is a breaking change for multiple services. Adding abstraction (API layer, event sourcing) is a prerequisite for incremental evolution.

**Trigger Condition:** Any requirement to modify order, customer, or product data models.

## Constraints Summary

| Constraint | Type | Rewrite Risk | Addressable? |
|------------|------|--------------|--------------|
| OrderProcessor monolith | Structural | High | No - requires rewrite |
| Database coupling | Architectural | Medium | Yes - with API layer |
| Single author knowledge | Organizational | Low | Yes - with documentation |
| Test coverage gaps | Process | Low | Yes - incrementally |

## Recommendation

Proceed with "extend" strategy **with the following constraints:**

1. **Ring-fence OrderProcessor:** Do not plan features requiring changes to order processing logic until rewrite is scoped
2. **Add database abstraction:** Implement API layer before any schema evolution
3. **Knowledge transfer:** Document critical paths before any team changes
```

---

## 8. Implementation Roadmap

### Phase 1: Evidence Architecture (Weeks 1-2)

**Goal:** Transform existing data into auditable evidence chains. No new tools required.

| Task | Output |
|------|--------|
| Create Evidence/Claim entities | `persistence/entities.py` additions |
| Add evidence generation queries | `insights/queries/evidence_*.sql` |
| Implement ClaimGenerator | Pattern-based claim generation |
| Create EvidencePackSection | New insight section |
| Create ClaimRegisterSection | New insight section |
| Create RiskRegisterSection | New insight section |

**Success Criteria:**
- Every existing finding has an evidence ID
- Claims link to evidence with confidence levels
- CTO can trace any claim to source data

### Phase 2: Symbol & Dependency Analysis (Weeks 3-6)

**Goal:** Enable coupling and blast radius analysis.

| Task | Output |
|------|--------|
| Create symbol-scanner tool | `src/tools/symbol-scanner/` |
| Python AST extractor | Function/class extraction |
| TypeScript extractor | Import/export analysis |
| Add landing zone tables | `lz_code_symbols`, `lz_symbol_calls` |
| Create dbt models | Fan-in/fan-out aggregation |
| Implement blast radius queries | Change impact analysis |
| Create ComponentInventorySection | New insight section |

**Success Criteria:**
- Can answer "what calls this function?"
- Can compute blast radius for any symbol
- Can identify module boundaries by coupling patterns

### Phase 3: Ownership & Coverage (Weeks 7-8)

**Goal:** Enable knowledge concentration and test gap analysis.

| Task | Output |
|------|--------|
| Create git-blame-scanner tool | `src/tools/git-blame-scanner/` |
| Create coverage-ingest tool | `src/tools/coverage-ingest/` |
| Add landing zone tables | `lz_git_blame_summary`, `lz_coverage_summary` |
| Create dbt models | Ownership rollups, coverage gaps |
| Create OwnershipSection | New insight section |
| Create CoverageGapSection | New insight section |

**Success Criteria:**
- Can identify single-author files
- Can compute bus factor per module
- Can identify high-complexity/low-coverage files

### Phase 4: Integrated Deliverables (Weeks 9-10)

**Goal:** Generate brief-compliant stakeholder reports.

| Task | Output |
|------|--------|
| Technical Evidence Pack template | Export format |
| Claim Register export | Structured output |
| Component Inventory report | Module-level analysis |
| Sampling Report generator | Risk-ranked file selection |
| Execution Risk Register | Prioritized risks |
| Rewrite Risk Memo template | Structural assessment |
| Stakeholder report variants | CTO, Investor, CEO formats |

**Success Criteria:**
- CTO can write platform decision paper from outputs
- IC member can verify claims independently
- All deliverables match brief specifications

---

## 9. Success Criteria

### 9.1 Evidence Quality

- [ ] Every technical claim links to ≥1 evidence item
- [ ] Evidence items include file:line location references
- [ ] "Why it matters" explains business impact, not just technical observation
- [ ] Confidence levels (High/Medium/Low) are justified by evidence breadth

### 9.2 Claim Defensibility

- [ ] A third party can inspect evidence and reach the same conclusion
- [ ] Claims follow pattern: Statement → Evidence → Implication → Confidence
- [ ] No claims rely on "engineering taste" or intuition
- [ ] Sampling rationale is explicit and reproducible

### 9.3 Risk Completeness

- [ ] Every significant risk has "triggered by" condition
- [ ] Risks link to supporting claims
- [ ] Severity is justified by business impact
- [ ] Rewrite risks are explicitly identified

### 9.4 Stakeholder Utility

- [ ] CTO can write platform decision paper without redoing analysis
- [ ] Investor gets quantified risk score with confidence interval
- [ ] CEO gets Red/Yellow/Green status with clear conditions
- [ ] All stakeholders can drill down from summary to evidence

### 9.5 Operational Metrics

| Metric | Target |
|--------|--------|
| Evidence coverage | ≥90% of findings have evidence IDs |
| Claim traceability | 100% of claims link to evidence |
| Report generation time | <5 minutes for full pipeline |
| False positive rate | <10% on manual validation |

---

## Appendix A: Stakeholder Report Templates

### A.1 CTO Report Structure

```
1. Executive Summary (1 page)
   - Overall assessment (Extend/Modernise/Replace recommendation factors)
   - Top 5 risks by severity
   - Key constraints on evolution

2. Technical Evidence Pack (reference)
   - Full evidence index
   - Detailed evidence items

3. Claim Register (5-10 pages)
   - Claims by category
   - Evidence linkage
   - Confidence assessment

4. Component Inventory (5-10 pages)
   - Module-by-module analysis
   - Dependency mapping
   - Hotspot identification

5. Code Quality Report (3-5 pages)
   - Sampling strategy
   - Pattern observations
   - Changeability assessment

6. Risk Register (3-5 pages)
   - Prioritized risks
   - Technical causes
   - Trigger conditions

7. Rewrite Risk Memo (2-3 pages)
   - Structural constraints
   - Evolution boundaries
   - Recommendations
```

### A.2 Investor Report Structure

```
1. Executive Summary (1 page)
   - Traffic light status
   - Risk score (0-100) with confidence
   - Investment requirements

2. Deal Considerations (1-2 pages)
   - Potential blockers
   - Due diligence findings summary
   - Comparable benchmarks

3. Risk Quantification (2-3 pages)
   - Security exposure
   - Technical debt indicators
   - Scalability assessment

4. Financial Implications (1 page)
   - Pre-close requirements
   - Post-close investment
   - Ongoing maintenance cost signals

5. Supporting Evidence (appendix)
   - Key evidence items
   - Methodology note
```

### A.3 CEO Report Structure

```
1. Bottom Line (1 page)
   - Go/No-Go/Conditional recommendation
   - Top 3 considerations
   - Required actions

2. Business Impact Translation (1 page)
   - Time-to-market implications
   - Team risk factors
   - Competitive position signals

3. Investment Summary (1 page)
   - What needs fixing and why
   - Rough magnitude (not estimates)
   - Timeline factors

4. Questions for Technical Team (reference)
   - Areas requiring clarification
   - Decision points
```

---

## Appendix B: Query Reference

See `src/insights/queries/` for full query implementations:

- `evidence_complexity.sql` - Generate complexity evidence items
- `evidence_security.sql` - Generate security evidence items
- `evidence_coupling.sql` - Generate coupling evidence items
- `claims_from_distributions.sql` - Generate claims from Gini/Palma metrics
- `claims_from_patterns.sql` - Generate claims from code patterns
- `risk_aggregation.sql` - Aggregate claims into risks
- `blast_radius.sql` - Compute change impact
- `component_boundaries.sql` - Identify module boundaries
- `coverage_gaps.sql` - Find high-risk untested code
- `ownership_concentration.sql` - Identify knowledge silos

---

## Appendix C: Tool Integration Matrix

| Deliverable | layout | scc | lizard | semgrep | trivy | gitleaks | git-sizer | symbol | blame | coverage |
|-------------|--------|-----|--------|---------|-------|----------|-----------|--------|-------|----------|
| Evidence Pack | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Claim Register | | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ |
| Component Inventory | ✓ | ✓ | ✓ | | | | | ✓ | ✓ | |
| Quality Report | | ✓ | ✓ | ✓ | | | | | | ✓ |
| Risk Register | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ |
| Rewrite Memo | ✓ | ✓ | ✓ | | | | | ✓ | | |

**Legend:** ✓ = primary data source, (empty) = not used

---

*Document maintained by: Project Caldera Team*
*Next review: After Phase 1 completion*
