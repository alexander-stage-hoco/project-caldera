# Insights Product Specification

## Technical Due Diligence Platform for PE Investment Decisions

**Version:** 2.0.0
**Status:** Implemented
**Last Updated:** 2026-03-06

---

## Executive Summary

Project Caldera's Insights component delivers automated technical due diligence reports for Private Equity transactions. The platform produces **evidence-based technical assessments** that enable CTOs to make defensible platform decisions (extend / modernise / replace) and communicate them to Investment Committees.

**Core Principle:** Every technical claim must follow the structure:

```
Claim → Evidence → Implication → Confidence
```

If we cannot point to concrete evidence, the claim does not belong in the output.

**Implementation Status:** All 6 deliverables are implemented with 43 report sections, 95 SQL queries, 84 Jinja2 templates, and a full evidence chain (evidence → claims → risks → actions). Three stakeholder profiles (CTO, Investor, CEO) produce tailored reports.

---

## Table of Contents

1. [Stakeholder Requirements](#1-stakeholder-requirements)
2. [Current Capabilities](#2-current-capabilities)
3. [Implementation Status](#3-implementation-status)
4. [Architecture](#4-architecture)
5. [Evidence & Claim Framework](#6-evidence--claim-framework)
6. [Deliverable Specifications](#7-deliverable-specifications)
7. [Remaining Gaps](#7-remaining-gaps)
8. [Success Criteria](#8-success-criteria)

---

## 1. Stakeholder Requirements

### 1.1 CTO / VP Engineering

**Purpose:** Assess maintainability, technical debt, and execution risk for platform decisions.

| Need | Question Answered | Status |
|------|-------------------|--------|
| Complexity hotspots | "Which files/modules require the most effort to change safely?" | Implemented |
| Coupling assessment | "Where would the system resist us if we needed to change supplier logic?" | Implemented |
| Architecture health | "Which modules are well-structured vs. problematic?" | Implemented |
| Security posture | "What vulnerabilities require immediate attention?" | Implemented |
| Knowledge concentration | "Where is tribal knowledge creating bus factor risk?" | Implemented |
| Test safety | "Which complex areas lack test coverage?" | Implemented |

**Output Requirements:**
- Detailed technical evidence with file:line references
- Sampling rationale explaining what was analyzed and why
- Pattern observations (good and bad) with concrete examples
- Actionable risk register with technical causes

### 1.2 PE Investor / Investment Committee

**Purpose:** Risk quantification, investment thesis validation, deal-breaker identification.

| Need | Question Answered | Status |
|------|-------------------|--------|
| Risk score | "What is the overall technical risk level (0-100)?" | Implemented (trust score) |
| Deal blockers | "Are there issues that should stop the transaction?" | Implemented |
| Hidden costs | "What technical debt will require investment post-close?" | Implemented |
| Scalability | "Can the platform grow with the business?" | Implemented |
| Security exposure | "What regulatory or breach risks exist?" | Implemented |
| Rewrite probability | "Will 'modernisation' silently become a rewrite?" | Implemented |

**Output Requirements:**
- Single-page executive summary with traffic light status
- Quantified risk scores with confidence levels
- Investment requirements (pre-close and post-close)
- Top 3-5 findings ranked by business impact

### 1.3 CEO / Business Leader

**Purpose:** Go/no-go signals, business risk translation, investment planning.

| Need | Question Answered | Status |
|------|-------------------|--------|
| Overall status | "Red/Yellow/Green—should we proceed?" | Implemented |
| Business impact | "How does technical risk affect time-to-market?" | Implemented |
| Cost implications | "What remediation investment is required?" | Implemented |
| Competitive position | "Does the technology enable or constrain growth?" | Implemented |
| Team implications | "Are there key-person dependencies?" | Implemented |

**Output Requirements:**
- Non-technical summary with business context
- Clear recommendation with conditions
- Risk-to-business translation
- Timeline implications (without specific estimates)

---

## 2. Current Capabilities

### 2.1 Data Assets (18 Tools Integrated)

| Tool | Data Produced | Landing Zone Tables |
|------|---------------|---------------------|
| **layout-scanner** | File inventory, directory structure | `lz_layout_files`, `lz_layout_directories` |
| **scc** | LOC, complexity, comment ratios | `lz_scc_file_metrics` |
| **lizard** | Function-level CCN, NLOC | `lz_lizard_file_metrics`, `lz_lizard_function_metrics` |
| **semgrep** | Code smells by category | `lz_semgrep_smells` |
| **roslyn-analyzers** | .NET violations | `lz_roslyn_violations` |
| **sonarqube** | Issues, duplication, cognitive complexity | `lz_sonarqube_issues`, `lz_sonarqube_metrics` |
| **trivy** | CVEs, IaC misconfigs | `lz_trivy_vulnerabilities`, `lz_trivy_iac_misconfigs` |
| **gitleaks** | Exposed secrets | `lz_gitleaks_secrets` |
| **git-sizer** | Repository health | `lz_git_sizer_metrics`, `lz_git_sizer_violations` |
| **symbol-scanner** | Code symbols, call graphs, imports | `lz_symbol_scanner_symbols`, `lz_symbol_scanner_calls`, `lz_symbol_scanner_imports` |
| **git-blame-scanner** | Per-file authorship, knowledge risk | `lz_git_blame_scanner_file_summary`, `lz_git_blame_scanner_author_stats` |
| **coverage-ingest** | Test coverage (LCOV, Cobertura, JaCoCo, Istanbul) | `lz_coverage_ingest_file_coverage` |
| **git-fame** | Contributor statistics | `lz_git_fame_contributors` |
| **pmd-cpd** | Copy-paste detection | `lz_pmd_cpd_duplications` |
| **devskim** | Security linting rules | `lz_devskim_findings` |
| **dotcover** | .NET code coverage (Coverlet) | `lz_dotcover_assemblies`, `lz_dotcover_namespaces`, `lz_dotcover_files` |
| **dependensee** | Dependency visualization | `lz_dependensee_dependencies` |
| **scancode** | License and copyright detection | `lz_scancode_licenses`, `lz_scancode_copyrights` |

### 2.2 Aggregation Capabilities

**Directory Rollups:** Every tool produces recursive and direct rollups with 22 distribution statistics:

- Basic: count, min, max, mean, median, stddev
- Percentiles: p25, p50, p75, p90, p95, p99
- Inequality: gini, palma_ratio, hoover_index, theil_index
- Concentration: top_10_share, top_20_share, bottom_10_share
- Shape: skewness, kurtosis, coefficient_of_variation, iqr

**Unified Marts:**
- `unified_file_metrics` — File-level metrics joined across all 18 tools
- `unified_directory_metrics` — Directory-level aggregations with layout-scanner spine
- `unified_run_summary` — Run-level summary with tool completeness
- `unified_repo_metrics` — Repository-level aggregate metrics

**dbt Warehouse:** 168 models (51 staging, 117 marts), 2 SCD Type 2 snapshots, 23 analyses.

### 2.3 Insight Sections (43)

| # | Section | Purpose | Data Sources |
|---|---------|---------|--------------|
| 1 | ExecutiveSummary | Top 3 prioritized insights with LLM narrative | All tools |
| 2 | DeltaSummary | Run-over-run change detection | Cross-run comparison |
| 3 | RiskRegister | Aggregated execution risks with SLA dates | Evidence framework |
| 4 | RewriteRisk | Structural vs addressable constraint detection | Complexity, coupling, ownership |
| 5 | ToolReadiness | Tool coverage and completeness | All tool runs |
| 6 | ToolCoverageDashboard | Which tools ran and their coverage | All tool runs |
| 7 | RepoHealth | Overview metrics, health grade | git-sizer, scc, lizard |
| 8 | FileHotspots | Top files by complexity, LOC, smells | lizard, scc, semgrep |
| 9 | FunctionComplexity | Function-level CCN hotspots | lizard |
| 10 | CodeSizeHotspots | Largest files by LOC | scc |
| 11 | DirectoryAnalysis | Directory-level hotspots | All rollups |
| 12 | DirectoryStructure | Layout and structure analysis | layout-scanner |
| 13 | ModuleHealth | Composite health scores per directory | All rollups |
| 14 | CompositeRisk | Weighted multi-signal risk scoring | Cross-tool joins |
| 15 | TechnicalDebtSummary | Aggregated technical debt indicators | Complexity, smells, duplication |
| 16 | Vulnerabilities | Security vulnerability summary (CVEs) | trivy |
| 17 | IacMisconfigs | Infrastructure misconfigurations | trivy |
| 18 | Secrets | Exposed credentials | gitleaks |
| 19 | DevskimSecurity | Security linting findings | devskim |
| 20 | CrossTool | Compound risks (complex+smelly, complex+vulnerable) | Cross-tool joins |
| 21 | CouplingAnalysis | Symbol-level fan-in/fan-out, instability | symbol-scanner |
| 22 | CouplingDebt | Weighted coupling debt per directory | symbol-scanner, scc |
| 23 | BlastRadius | Symbol-level change impact analysis | symbol-scanner |
| 24 | ComponentInventory | Directory-as-component health analysis | symbol-scanner, scc, lizard |
| 25 | ImportDependencies | File import/dependency graph | symbol-scanner |
| 26 | CircularDependencies | Circular import detection | symbol-scanner |
| 27 | AuthorshipRisk | Per-file authorship concentration | git-blame-scanner |
| 28 | KnowledgeRisk | Knowledge silo and bus factor analysis | git-blame-scanner, git-fame |
| 29 | CoverageGap | High-complexity + low-coverage risk zones | coverage-ingest, lizard |
| 30 | DotcoverCoverage | .NET code coverage (assembly/namespace/file) | dotcover |
| 31 | CodeDuplication | Copy-paste detection hotspots | pmd-cpd |
| 32 | DependencyHealth | Dependency freshness and risk | dependensee |
| 33 | LicenseCompliance | License detection and compliance | scancode |
| 34 | LanguageCoverage | Language distribution analysis | layout-scanner, scc |
| 35 | CodeQualityRules | Code smell patterns by rule/category | semgrep |
| 36 | RoslynViolations | .NET Roslyn analyzer findings | roslyn-analyzers |
| 37 | SonarQubeDeepDive | SonarQube issue and metric analysis | sonarqube |
| 38 | GitSizer | Repository health violations and LFS candidates | git-sizer |
| 39 | DistributionInsights | Statistical distribution analysis | All rollups |
| 40 | CodeInequality | Inequality metrics (Gini, Palma, Hoover) | All rollups |
| 41 | SamplingRationale | Risk-ranked file selection with composite scoring | Cross-tool joins |
| 42 | EvidencePack | Reference index of all collected evidence items | Evidence framework |
| 43 | ClaimRegister | Technical claims grouped by category | Evidence framework |

### 2.4 Evidence & Claim Pipeline

Fully implemented end-to-end:

```
SQL Queries (6 categories) → EvidenceCollector → EvidenceItems
                                                      ↓
ClaimGenerator (7 rules + LLM synthesis) ← ──────────┘
        ↓
TechnicalClaims → RiskAggregator (5 patterns) → ExecutionRisks
                                                       ↓
                        EvidenceRegistry → Report Sections (Evidence Pack, Claim Register, Risk Register)
                                                       ↓
                        Persistence (lz_evidence, lz_claims, lz_risks, lz_warnings)
```

**Evidence categories:** complexity, security, coupling, coverage, ownership, quality

**Claim rules:** ComplexityConcentration, HighCoupling, KnowledgeSilo, CoverageGap, SecurityExposure, PervasiveDebt, LLMSynthesis (cross-signal compound-risk detection)

**Risk patterns:** Security exposure, Change amplification, Knowledge concentration, Untested complexity, Systemic debt

### 2.5 Stakeholder Profiles

Three stakeholder profiles produce tailored reports with section selection:

| Profile | Sections | Focus |
|---------|----------|-------|
| CTO | ~35 sections | Full technical detail, evidence pack, claim register |
| Investor | ~20 sections | Risk scoring, executive summary, key metrics |
| CEO | ~12 sections | Traffic light status, business impact, top actions |

### 2.6 Output Formats

| Format | Status | Description |
|--------|--------|-------------|
| HTML | Implemented | Full interactive report with navigation |
| Markdown | Implemented | Portable text format |
| Pack | Implemented | JSON data export for programmatic consumption |
| PDF | Not started | Formal deliverable format (planned) |

---

## 3. Implementation Status

### 3.1 Capability Coverage

All capabilities originally identified as gaps are now implemented:

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Evidence chains** | **Complete** | EvidenceCollector extracts items from 6 categories with unique IDs |
| **Claim-Evidence linking** | **Complete** | ClaimGenerator with 7 rules links claims to evidence IDs |
| **Component boundaries** | **Complete** | ComponentInventorySection with directory-as-component analysis |
| **Interaction patterns** | **Complete** | Symbol-scanner call graphs, blast radius, coupling analysis |
| **Sampling rationale** | **Complete** | SamplingRationaleSection with composite risk scoring |
| **Changeability assessment** | **Complete** | RewriteRiskSection with structural vs addressable constraints |
| **Rewrite risk signals** | **Complete** | Structural constraint detection with trigger conditions |
| **Code ownership** | **Complete** | git-blame-scanner + AuthorshipRisk + KnowledgeRisk sections |
| **Test coverage** | **Complete** | coverage-ingest (LCOV, Cobertura, JaCoCo, Istanbul) + CoverageGap section |

### 3.2 Deliverable Coverage

| Brief Deliverable | Coverage | Implementation |
|-------------------|----------|----------------|
| Technical Evidence Pack | **95%** | EvidencePackSection with category-grouped evidence, IDs, locations, observations, "why it matters" |
| Claim Register | **95%** | ClaimRegisterSection with category grouping, confidence distribution, evidence linkage |
| Component Inventory | **90%** | ComponentInventorySection + ImportDependencies + CircularDependencies + CouplingAnalysis |
| Code Quality Report | **95%** | SamplingRationale + CompositeRisk + TechnicalDebtSummary + CodeQualityRules + CrossTool |
| Risk Register | **95%** | RiskRegisterSection with severity tiers, claims, SLA dates, remediation actions, LLM narratives |
| Rewrite Risk Memo | **90%** | RewriteRiskSection with structural vs addressable constraint detection |

### 3.3 Original Roadmap Completion

| Phase | Goal | Status |
|-------|------|--------|
| Phase 1: Evidence Architecture | Auditable evidence chains | **Complete** |
| Phase 2: Symbol & Dependency Analysis | Coupling and blast radius | **Complete** |
| Phase 3: Ownership & Coverage | Knowledge concentration and test gaps | **Complete** |
| Phase 4: Integrated Deliverables | Stakeholder-ready reports | **Complete** |

---

## 4. Architecture

### 4.1 Layered Evidence Model (Implemented)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RAW DATA LAYER (18 tools)                        │
│  Layout │ SCC │ Lizard │ Semgrep │ Trivy │ Gitleaks │ Git-sizer            │
│  Symbol-scanner │ Git-blame-scanner │ Coverage-ingest │ Git-fame           │
│  PMD-CPD │ DevSkim │ DotCover │ Dependensee │ ScanCode │ Roslyn │ SonarQube│
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                          EVIDENCE LAYER                                     │
│  EvidenceItem: id, type, location, excerpt, observation, why_it_matters    │
│  6 categories: complexity, security, coupling, coverage, ownership, quality│
│  SQL-driven extraction from existing dbt marts                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                            CLAIM LAYER                                      │
│  TechnicalClaim: id, statement, evidence_ids[], implication, confidence    │
│  7 deterministic rules + LLM synthesis for compound risks                  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                            RISK LAYER                                       │
│  ExecutionRisk: id, description, claim_ids[], triggered_by, severity       │
│  5 risk patterns with severity escalation + action enrichment (SLA dates)  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                        DELIVERABLE LAYER                                    │
│  Evidence Pack │ Claim Register │ Component Inventory │ Risk Register      │
│  Sampling Rationale │ Rewrite Risk Memo │ Delta Summary                    │
│  Stakeholder-specific reports (CTO, Investor, CEO)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Cross-Tool Analysis Queries (Implemented)

All cross-tool compound queries are implemented in `src/insights/queries/`:

| Query | Purpose | Tools Joined |
|-------|---------|--------------|
| `symbol_blast_radius.sql` | Transitive change impact analysis | symbol-scanner |
| `coupling_hotspots.sql` | Fan-in/fan-out with instability and coupling patterns | symbol-scanner |
| `coverage_gap_hotspots.sql` | High complexity + low coverage risk zones | lizard, coverage-ingest |
| `composite_risk_hotspots.sql` | Weighted multi-signal risk scoring | All tools via unified_file_metrics |
| `cross_tool_complex_smelly.sql` | Files that are both complex and smelly | lizard, semgrep |
| `cross_tool_complex_vulnerable.sql` | Files that are complex with vulnerabilities | lizard, trivy |
| `knowledge_risk_hotspots.sql` | Ownership concentration analysis | git-blame-scanner |
| `module_health_scores.sql` | Composite directory health grades | All rollups |
| `rewrite_risk_constraints.sql` | Structural vs addressable constraint detection | Complexity, coupling, ownership |

---

## 5. Evidence & Claim Framework

### 5.1 Evidence Item Structure

```python
@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str              # E-CCN-001, E-SEC-042, etc.
    evidence_type: str            # code, config, schema, runtime, metric
    category: EvidenceCategory    # complexity, security, coupling, coverage, ownership, quality
    location: str                 # file:line or directory or metric query
    excerpt: str                  # Short snippet or value (max 500 chars)
    observation: str              # What we see (max 500 chars)
    why_it_matters: str           # Why CTO should care (max 500 chars)
    tool_source: str              # Which tool produced this
    run_pk: int                   # Link to collection run
    confidence: ConfidenceLevel   # high, medium, low
```

### 5.2 Technical Claim Structure

```python
@dataclass(frozen=True)
class TechnicalClaim:
    claim_id: str                 # CLM-COUP-001, CLM-SEC-012, etc.
    category: ClaimCategory       # coupling, complexity, security, coverage, ownership, quality
    statement: str                # Precise technical claim
    evidence_ids: tuple[str, ...] # Links to evidence
    implication: str              # What this means for changeability
    confidence: ConfidenceLevel   # high, medium, low
    triggered_by: str             # What change would expose this risk
    severity: RiskSeverity | None # critical, high, medium, low (optional)
```

### 5.3 Claim Generation Rules

| Rule | Category | Detection | Claim Template |
|------|----------|-----------|----------------|
| ComplexityConcentration | complexity | `gini_ccn > 0.7 AND file_count > 10` | "Complexity concentrated in {path} (Gini={value})" |
| HighCoupling | coupling | `fan_out > fan_in * 3 AND fan_out > 5` | "Module {path} exhibits high outbound coupling" |
| KnowledgeSilo | ownership | `unique_authors = 1 AND total_lines > 500` | "File {path} has single author — bus factor risk" |
| CoverageGap | coverage | `coverage < 50 AND ccn > 15` | "File {path} is high-risk: {ccn} CCN with {coverage}% coverage" |
| SecurityExposure | security | `critical_vulns > 0` | "Platform has {count} critical security finding(s)" |
| PervasiveDebt | quality | `affected_pct > 50` | "Code smell '{type}' affects {pct}% of files" |
| LLMSynthesis | quality | `3+ evidence categories per file` | LLM-generated compound risk description |

### 5.4 Execution Risk Structure

```python
@dataclass(frozen=True)
class ExecutionRisk:
    risk_id: str                  # RISK-001, RISK-002, etc.
    description: str              # Human-readable risk description
    technical_cause: str          # What creates this risk
    claim_ids: tuple[str, ...]    # Claims that support this risk
    manifests_in: tuple[str, ...] # Directories/files affected
    triggered_by: str             # What change activates risk
    severity: RiskSeverity        # critical, high, medium, low
    owner: str | None             # Assigned owner
    action: str | None            # Remediation action
    sla_date: str | None          # Target remediation date
    status: RiskStatus            # open, mitigating, accepted, resolved
```

### 5.5 Risk Aggregation Patterns

| Pattern | Categories | Min Claims | Default Severity |
|---------|-----------|------------|------------------|
| Security exposure | security | 1 | high |
| Change amplification | coupling | 2 | high |
| Knowledge concentration | ownership | 2 | high |
| Untested complexity | coverage + complexity | 2 (both) | high |
| Systemic debt | quality | 3 | medium |

### 5.6 Warning Budget

Evidence collection classifies warnings into categories with configurable budgets:

| Category | Default Budget | Purpose |
|----------|---------------|---------|
| `expected_missing` | 10 | Tool was not run or not applicable |
| `regression` | 0 | Query that previously worked now fails |
| `degraded` | 3 | Partial results returned |

---

## 6. Deliverable Specifications

### 6.1 Technical Evidence Pack

**Status:** Implemented (`EvidencePackSection`)

Renders evidence index table grouped by category (top 50 per category). Each evidence item includes: evidence_id, evidence_type, location, excerpt, observation, why_it_matters, tool_source, confidence.

### 6.2 Claim Register

**Status:** Implemented (`ClaimRegisterSection`)

Renders claims grouped by category with evidence linkage, confidence distribution, and triggered_by reasoning.

### 6.3 Component & Interaction Inventory

**Status:** Implemented (`ComponentInventorySection`, `ImportDependenciesSection`, `CircularDependenciesSection`)

Directory-as-component analysis with LOC, complexity, symbol counts, coupling metrics, and health grades. Import dependency graph with circular dependency detection.

### 6.4 Code Quality & Changeability Sampling Report

**Status:** Implemented (`SamplingRationaleSection`, `CompositeRiskSection`)

Risk-ranked file selection using composite scoring (complexity 30%, coupling 25%, vulnerabilities 30%, coverage gap 15%). Sampling targets with explicit rationale for why each file was selected.

### 6.5 Engineering Execution Risk Register

**Status:** Implemented (`RiskRegisterSection`)

Risks grouped by severity with technical causes, supporting claims, manifests_in locations, action recommendations, SLA dates, and optional LLM narrative enrichment.

### 6.6 Implicit Rewrite Risk Memo

**Status:** Implemented (`RewriteRiskSection`)

Structural vs addressable constraint detection. Identifies where incremental evolution breaks down and quantifies rewrite risk with specific trigger conditions.

---

## 7. Remaining Gaps

### 7.1 Output Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| PDF report generation | Stakeholders need formal deliverables; HTML-only blocks PE use case | P1 |
| Incremental pipeline | Every tool runs every time; no skip-unchanged capability | P2 |

### 7.2 Platform Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| Policy Layer | No configurable quality gates, waivers, or drift tracking | P3 |
| Portfolio Layer | Single-repo only; no multi-repo dashboards or cross-repo comparison | P3 |

### 7.3 Operational Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| Multi-platform Docker | arm64 builds for M-series Macs not available | P3 |
| LLM provider abstraction | Only Claude supported for judge evaluations | P3 |

---

## 8. Success Criteria

### 8.1 Evidence Quality

- [x] Every technical claim links to >=1 evidence item
- [x] Evidence items include file:line location references
- [x] "Why it matters" explains business impact, not just technical observation
- [x] Confidence levels (High/Medium/Low) are justified by evidence breadth

### 8.2 Claim Defensibility

- [x] A third party can inspect evidence and reach the same conclusion
- [x] Claims follow pattern: Statement -> Evidence -> Implication -> Confidence
- [x] No claims rely on "engineering taste" or intuition
- [x] Sampling rationale is explicit and reproducible

### 8.3 Risk Completeness

- [x] Every significant risk has "triggered by" condition
- [x] Risks link to supporting claims
- [x] Severity is justified by business impact
- [x] Rewrite risks are explicitly identified

### 8.4 Stakeholder Utility

- [x] CTO can write platform decision paper without redoing analysis
- [x] Investor gets quantified risk score with confidence interval
- [x] CEO gets Red/Yellow/Green status with clear conditions
- [x] All stakeholders can drill down from summary to evidence

### 8.5 Operational Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Evidence coverage | >=90% of findings have evidence IDs | Implemented |
| Claim traceability | 100% of claims link to evidence | Implemented |
| Report generation time | <5 minutes for full pipeline | Achieved |
| False positive rate | <10% on manual validation | Target |

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

See `src/insights/queries/` for full query implementations (95 queries total).

**Evidence queries:**
- `evidence_complexity.sql` — Complexity evidence items from lizard/scc
- `evidence_security.sql` — Security evidence items from trivy/gitleaks/devskim
- `evidence_coupling.sql` — Coupling evidence items from symbol-scanner
- `evidence_coverage.sql` — Coverage evidence items from coverage-ingest
- `evidence_ownership.sql` — Ownership evidence items from git-blame-scanner
- `evidence_quality.sql` — Quality evidence items from semgrep/sonarqube

**Claim queries:**
- `claim_complexity_concentration.sql` — Directories with concentrated complexity (Gini)
- `claim_pervasive_smells.sql` — Code smells affecting >50% of files

**Cross-tool queries:**
- `symbol_blast_radius.sql` — Symbol-level change impact analysis
- `coupling_hotspots.sql` — Fan-in/fan-out with instability and coupling patterns
- `coverage_gap_hotspots.sql` — High complexity + low coverage risk zones
- `composite_risk_hotspots.sql` — Weighted multi-signal risk scoring
- `cross_tool_complex_smelly.sql` — Complex + smelly file intersection
- `cross_tool_complex_vulnerable.sql` — Complex + vulnerable file intersection
- `module_health_scores.sql` — Composite directory health grades
- `rewrite_risk_constraints.sql` — Structural constraint detection
- `sampling_targets.sql` — Risk-ranked file selection

---

## Appendix C: Tool Integration Matrix

| Deliverable | layout | scc | lizard | semgrep | trivy | gitleaks | git-sizer | symbol | blame | coverage | git-fame | pmd-cpd | devskim | dotcover | dependensee | scancode | roslyn | sonarqube |
|-------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Evidence Pack | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | ✓ | | | | ✓ | ✓ |
| Claim Register | | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | | | | | | | | |
| Component Inventory | ✓ | ✓ | ✓ | | | | | ✓ | ✓ | | | | | | ✓ | | | |
| Quality Report | | ✓ | ✓ | ✓ | | | | ✓ | | ✓ | | ✓ | | | | | ✓ | ✓ |
| Risk Register | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | ✓ | | | | | |
| Rewrite Memo | ✓ | ✓ | ✓ | | | | | ✓ | ✓ | | | | | | | | | |

**Legend:** ✓ = primary data source

---

*Document maintained by: Project Caldera Team*
*Last major revision: 2026-03-06 — Updated from Draft to Implemented status reflecting 18 tools, 43 sections, full evidence chain*
