# Decision Framework: Evidence, Lenses, Claims & IC Outputs

**Version:** 3.0
**Purpose:** Complete, auditable, IC-grade decision framework for technical due diligence. This document is the **single source of truth** for methodology, fully superseding all prior methodology documents.

---

## Document Structure

```
PART I: CORE FRAMEWORK
  1. Information Architecture
  2. Evidence Specification
  3. Axes (Decision Surfaces)
  4. Lenses (Full Specification)
  5. Claims Specification
  6. Cross-Axis Constraints

PART II: EXECUTION
  7. Process Phases & Timeline
  8. Interview Protocol
  9. Quality Gates
  10. IC Output Specification

PART III: WORKED EXAMPLE
  11. End-to-End Walkthrough

APPENDICES
  A. Evidence Categories & Thresholds
  B. Full Interview Question Bank
  C. Tool-to-Lens Mapping
  D. IC Report Templates
  E. Process Checklists
  F. Quick Reference
```

---

# PART I: CORE FRAMEWORK

---

## 1. Information Architecture

This framework is built as a **closed, ordered information system**. No step may be skipped or reordered.

### 1.1 Canonical Flow

```
Tool Output / Code Analysis / Interviews
        |
        v
     Evidence
        |
        v
       Lens
        |
        v
      Claim
        |
        v
   Axis Decision
        |
        v
 Roadmap / CAPEX / IC Output
```

### 1.2 Core Principles

* **Inputs never produce claims** - Tools, humans, and AI agents only produce evidence
* **Evidence is pre-interpretive** - What is observed, not what it means
* **Lenses constrain interpretation** - What kind of claim is allowed
* **Claims are axis-specific assertions** - Decision-relevant, falsifiable
* **Axis decisions are the only inputs to IC outputs**

### 1.3 Non-Negotiable Enforcement Rules

1. No claim without a lens
2. No lens without admissible evidence
3. No IC decision without claims
4. No roadmap item without axis linkage

### 1.4 What Each Source Reveals

| Automated Analysis Shows | Interviews Reveal |
|--------------------------|-------------------|
| High complexity (CCN metrics) | Why it's complex (intentional trade-off vs. accidental debt) |
| Single author on critical files | Whether knowledge transfer has occurred informally |
| Tight coupling between modules | Whether coupling is by design or a historical constraint |
| Security vulnerabilities exist | Whether they're known, tracked, or actively ignored |
| Low test coverage | Whether manual testing or operational workarounds exist |
| Code smells and anti-patterns | Whether refactoring is planned or blocked by constraints |
| File churn and change frequency | What drives changes - bugs, features, or fire-fighting |

**Core insight:** Code tells us WHAT exists. Engineers tell us WHY it exists and WHAT it means.

---

## 2. Evidence Specification

### 2.1 What Evidence Is

Evidence is a **structured observation** grounded in a concrete artefact.

Evidence answers:
* What was observed?
* Where was it observed?
* How reliable is the observation?

Evidence does **not** argue, judge, or decide.

### 2.2 Evidence Sources

| Source Type | Examples | Reliability Range |
|-------------|----------|-------------------|
| **Tool output** | Dependency graphs, complexity metrics, CVE scans | High (objective) |
| **Code inspection** | Manual review, architecture analysis | Medium-High |
| **Data inspection** | Schema review, reconciliation attempts | High |
| **Interview** | Engineer and stakeholder conversations | Medium (firsthand) to Low (secondhand) |
| **Document review** | Architecture docs, runbooks, contracts | Medium |

### 2.3 Evidence Template

```markdown
Evidence ID: E-{axis}-{seq}
Source Type: Tool | Code Inspection | Interview | Data Inspection | Document
Source Detail: (tool + version, repo + commit, interviewee + role + date)
Anchor: (repo, file path, module, schema, process)
Observation: (factual statement - no interpretation)
Scope: Local | Cross-module | Systemic
Reliability: High | Medium | Low
Validity Period: (when this evidence becomes stale)
Notes: (optional context, no interpretation)
```

### 2.4 Evidence ID Convention

Evidence IDs follow the pattern: `E-{CATEGORY}-{SEQUENCE}` or `E-{TYPE}-{CATEGORY}-{SEQUENCE}`

| Type Code | Description |
|-----------|-------------|
| AUTO | Automated tool finding |
| MAN | Manual inspection |
| INT | Interview-derived |
| HARD | Hardened after triangulation |

| Category Code | Category | Primary Tools |
|---------------|----------|---------------|
| CMPLX | Complexity | lizard, scc |
| COUP | Coupling | semgrep, symbol-scanner |
| SEC | Security | trivy, gitleaks |
| QUAL | Quality | semgrep, roslyn |
| DIST | Distribution | rollups |
| KNOW | Knowledge | git-blame |
| OPS | Operational | git-sizer, interview |
| ARCH | Architectural | layout, symbol-scanner |

### 2.5 Evidence Rejection Rules

**Reject evidence if:**

| Rejection Reason | Example |
|------------------|---------|
| Cannot be anchored to concrete artefact | "The architecture is messy" |
| Mixes multiple decision dimensions | "The code is complex and the team is small" |
| Implies a decision or recommendation | "We should modernize the pricing engine" |
| Relies on single uncorroborated interview | "Alice said it's a problem" (no other source) |
| Uses subjective language without operationalization | "The code quality is poor" |

### 2.6 Evidence Lifecycle & Staleness

| Source Type | Default Validity | Staleness Trigger |
|-------------|------------------|-------------------|
| Tool output (commit-anchored) | Until new commit analyzed | Any commit to analyzed paths |
| Tool output (full repo) | 7 days | Major release, merge to main |
| Code inspection | 14 days | Code change to inspected area |
| Schema/data inspection | 30 days | Schema migration, data process change |
| Interview (firsthand) | 30 days | Organizational change, interviewee departure |
| Interview (secondhand) | 14 days | Should be corroborated within window |
| Document review | Until document updated | Explicit document version change |

**Refresh Protocol:**

```
Staleness Detected:
1. Mark evidence as STALE (do not delete)
2. Determine refresh method:
   - Tool: Re-run on current commit
   - Inspection: Re-inspect with diff focus
   - Interview: Re-validate key claims
3. Compare fresh vs stale:
   - If same: Restore validity, update timestamp
   - If different: Create new evidence, link to stale predecessor
4. Re-evaluate affected claims
```

### 2.7 Evidence Quality Criteria

| Criterion | Strong Evidence | Weak Evidence |
|-----------|-----------------|---------------|
| **Specificity** | file:line reference | "somewhere in the codebase" |
| **Reproducibility** | Query or tool command | Manual observation only |
| **Objectivity** | Metric-based | Opinion-based |
| **Corroboration** | Multiple sources agree | Single source |
| **Recency** | Current commit | Historical/undated |
| **Relevance** | Directly impacts changeability | Tangential observation |

---

## 3. Axes (Decision Surfaces)

An **axis** is a single IC-relevant decision surface. Axes are mostly independent and constrain each other.

### 3.1 Axis 1 - Structural Platform Fitness

**IC Question:** Is the current platform structurally fit to support the investment thesis, or does it impose unavoidable constraints?

| In Scope | Out of Scope |
|----------|--------------|
| Architectural boundaries | Code quality |
| Domain separation | Team skill |
| Data ownership semantics | Delivery speed |
| Runtime isolation | |
| Structural extensibility | |

**Decision States:**
* **Extend** - Platform supports planned growth
* **Modernise** - Constraints exist but are addressable with investment
* **Replace** - Structural constraints block evolution

---

### 3.2 Axis 2 - Changeability & Cost-of-Change

**IC Question:** How expensive, risky, and predictable is incremental change over the next 6-12 months?

| In Scope | Out of Scope |
|----------|--------------|
| Change amplification | Platform direction decisions |
| Hotspot concentration | |
| Test and release friction | |
| Delivery predictability | |

**Decision States:**
* **Low cost-of-change** - Changes proceed predictably
* **High cost-of-change** - Roadmap must be constrained
* **Unpredictable** - Buffered / staged execution required

---

### 3.3 Axis 3 - Execution System & Delivery Control

**IC Question:** Can the organisation reliably execute a non-trivial roadmap under PE constraints?

| In Scope | Out of Scope |
|----------|--------------|
| Decision rights | Code structure |
| Governance | |
| Knowledge concentration | |
| Vendor leverage | |
| Operational discipline | |

**Decision States:**
* **Proceed** - Organisation can execute
* **Proceed with guardrails** - Specific controls required
* **Do not proceed** - Execution risk too high until remediation

---

### 3.4 Axis 4 - Data Integrity & Steering Readiness

**IC Question:** Can management reliably steer the business post-close?

| In Scope | Out of Scope |
|----------|--------------|
| Revenue reconstructability | Advanced analytics |
| Data completeness | |
| Data correctness | |
| Forward integrity | |

**Decision States:**
* **Steering ready** - Data supports management decisions
* **MVP required** - Minimum viable data investment needed
* **Steering risk disclosed** - Material data gaps acknowledged

---

### 3.5 Axis 5 - Investment Leverage & Sequencing

**IC Question:** Where does capital most effectively reduce risk or unlock value in 6-12 months?

| In Scope | Out of Scope |
|----------|--------------|
| Risk reduction leverage | Feature prioritization |
| Value asymmetry | |
| Reversibility | |
| Dependency resolution | |

**Decision States:**
* **Invest now** - Clear ROI, proceed
* **Stage / tranche** - Phase investment to manage risk
* **Defer** - Insufficient leverage or clarity

---

## 4. Lenses (Full Specification)

A **lens** routes evidence into a decision-relevant interpretation domain.

Lenses:
* Sit between evidence and claims
* Restrict admissible claim vocabulary
* Prevent cross-axis contamination

**Lens Selection Order:**

```
Evidence
  |
Axis Selection
  |
Primary Lens Selection
  |
(Secondary Lens - optional)
  |
Claim Eligibility
```

If evidence cannot be assigned to exactly **one primary axis and one primary lens**, it is not claim-eligible.

---

### AXIS 1 Lenses - Structural Platform Fitness

#### Lens 1.1 - Architectural Boundaries

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Tool (dependency analyzer), Code inspection, Interview |
| **Admissibility Criteria** | Evidence must reference specific module/package boundaries and cross-boundary interactions |
| **Inadmissible** | General quality complaints, performance concerns, team opinions without code reference |
| **Example Admissible** | "NDepend shows 14 cyclic dependencies between `Orders.Core` and `Billing.Core`" |
| **Example Rejected** | "The architecture is messy" (no anchor, subjective) |

#### Lens 1.2 - Data Architecture Semantics

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Schema inspection, Code inspection, Data inspection |
| **Admissibility Criteria** | Evidence must reference specific entities, ownership patterns, or temporal semantics |
| **Inadmissible** | Database performance issues, query optimization, data volume |
| **Example Admissible** | "`ContractState` entity is written by 4 services with no single owner" |
| **Example Rejected** | "The database is slow" (performance, not semantics) |

#### Lens 1.3 - Runtime Topology

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Infrastructure inspection, Deployment config, Interview (ops) |
| **Admissibility Criteria** | Evidence must reference service boundaries, failure domains, or scaling units |
| **Inadmissible** | Code quality, test coverage, team structure |
| **Example Admissible** | "Single Redis instance serves all 12 services; no failover configured" |
| **Example Rejected** | "The team doesn't do code reviews" (execution, not topology) |

#### Lens 1.4 - Structural Extensibility

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Code inspection, Interview, Business requirements |
| **Admissibility Criteria** | Evidence must reference limits to adding entities (suppliers, products, etc.) |
| **Inadmissible** | Current feature gaps, UI limitations, team bandwidth |
| **Example Admissible** | "Adding a new supplier type requires modifying 23 switch statements" |
| **Example Rejected** | "We don't have a supplier portal yet" (feature gap, not structural limit) |

---

### AXIS 2 Lenses - Changeability & Cost-of-Change

#### Lens 2.1 - Change Coupling

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Tool (co-change analysis), Git history, Code inspection |
| **Admissibility Criteria** | Evidence must show files/modules that change together |
| **Inadmissible** | Complexity metrics alone, single-file observations |
| **Example Admissible** | "87% of commits to `PricingEngine` also touch `OrderProcessor`" |
| **Example Rejected** | "`PricingEngine` has high CCN" (complexity, not coupling) |

#### Lens 2.2 - Hotspot Economics

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Tool (complexity x churn), Git history |
| **Admissibility Criteria** | Evidence must combine complexity AND change frequency |
| **Inadmissible** | Complexity alone, churn alone |
| **Example Admissible** | "`OrderProcessor.cs` (CCN=47) modified 34 times in 6 months" |
| **Example Rejected** | "`OrderProcessor.cs` has CCN=47" (no churn dimension) |

#### Lens 2.3 - Test & Release Friction

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | CI/CD inspection, Interview (dev, ops), Deployment history |
| **Admissibility Criteria** | Evidence must reference feedback latency, rollback capability, or release gates |
| **Inadmissible** | Test coverage numbers alone, code quality |
| **Example Admissible** | "Full test suite takes 4 hours; developers skip tests locally" |
| **Example Rejected** | "Test coverage is 32%" (coverage alone, not friction) |

#### Lens 2.4 - Predictability

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Delivery history, Interview (PM, lead), Sprint data |
| **Admissibility Criteria** | Evidence must show plan vs actual variance patterns |
| **Inadmissible** | Single sprint data, team opinions without data |
| **Example Admissible** | "Last 6 releases: 4 delayed by 2+ weeks, 2 rolled back" |
| **Example Rejected** | "We're usually late" (no data) |

---

### AXIS 3 Lenses - Execution System & Delivery Control

#### Lens 3.1 - Decision Rights

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Interview (leadership), Governance docs, Meeting records |
| **Admissibility Criteria** | Evidence must identify who decides architecture, scope, and technology |
| **Inadmissible** | Code patterns, team preferences |
| **Example Admissible** | "Architecture decisions require vendor sign-off; 3-week approval cycle" |
| **Example Rejected** | "The code uses Spring Boot" (technology fact, not decision rights) |

#### Lens 3.2 - Knowledge Distribution

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Git blame, Interview, Team structure |
| **Admissibility Criteria** | Evidence must identify key-person dependency for specific areas |
| **Inadmissible** | General team size, hiring plans |
| **Example Admissible** | "Alice is sole committer to `Settlement.*` (12K LOC) for 3 years" |
| **Example Rejected** | "The team is small" (no specific dependency) |

#### Lens 3.3 - Vendor Leverage

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Contract review, Interview, Integration inspection |
| **Admissibility Criteria** | Evidence must show asymmetric external control |
| **Inadmissible** | Vendor feature gaps, pricing concerns |
| **Example Admissible** | "Core pricing logic in vendor-controlled stored procedures; no source access" |
| **Example Rejected** | "The vendor is expensive" (commercial, not control) |

#### Lens 3.4 - Operational Discipline

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Incident history, Runbooks, Interview (ops) |
| **Admissibility Criteria** | Evidence must show release control and incident management patterns |
| **Inadmissible** | Code quality, architecture patterns |
| **Example Admissible** | "No documented rollback procedure; last 3 rollbacks were manual and took 4+ hours" |
| **Example Rejected** | "The code is hard to read" (quality, not operational) |

---

### AXIS 4 Lenses - Data Integrity & Steering Readiness

#### Lens 4.1 - Revenue Reconstructability

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Data inspection, Schema review, Finance interview |
| **Admissibility Criteria** | Evidence must show ability/inability to rebuild historical revenue |
| **Inadmissible** | Data volume, query performance |
| **Example Admissible** | "Order line items missing unit prices for 2019-2022; revenue not reconstructable" |
| **Example Rejected** | "The finance database has 50M rows" (volume, not reconstructability) |

#### Lens 4.2 - Data Completeness

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Data inspection, Schema review, ETL inspection |
| **Admissibility Criteria** | Evidence must show missing or partial data histories |
| **Inadmissible** | Data quality issues, duplicates |
| **Example Admissible** | "Customer acquisition date null for 34% of customers (pre-2020 imports)" |
| **Example Rejected** | "Some customer names have typos" (quality, not completeness) |

#### Lens 4.3 - Data Correctness

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Data inspection, Reconciliation attempts, Interview |
| **Admissibility Criteria** | Evidence must show conflicting values or unexplained overrides |
| **Inadmissible** | Schema design preferences, normalization |
| **Example Admissible** | "Contract value in `contracts` table differs from `invoices` sum by >10% for 23% of contracts" |
| **Example Rejected** | "The schema isn't normalized" (design, not correctness) |

#### Lens 4.4 - Forward Integrity

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Schema inspection, Process review, Interview |
| **Admissibility Criteria** | Evidence must show mechanisms (or lack thereof) preventing future data loss |
| **Inadmissible** | Historical data issues, current state |
| **Example Admissible** | "No audit trail on contract modifications; changes overwrite previous values" |
| **Example Rejected** | "Historical data is incomplete" (past, not forward) |

---

### AXIS 5 Lenses - Investment Leverage & Sequencing

#### Lens 5.1 - Risk Reduction Leverage

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Cross-reference to Axis 1-4 claims, Investment analysis |
| **Admissibility Criteria** | Evidence must quantify risk reduction per unit investment |
| **Inadmissible** | General improvement ideas, feature requests |
| **Example Admissible** | "Decoupling settlement reduces 3 P1 risks at 2 PM effort" |
| **Example Rejected** | "We should modernize the UI" (no risk linkage) |

#### Lens 5.2 - Value Asymmetry

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Business case, Revenue analysis, Market data |
| **Admissibility Criteria** | Evidence must show asymmetric upside/downside |
| **Inadmissible** | Cost estimates alone, effort estimates alone |
| **Example Admissible** | "Supplier onboarding bottleneck blocks $2M ARR; removal costs $200K" |
| **Example Rejected** | "This feature would cost $200K" (no value dimension) |

#### Lens 5.3 - Reversibility

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Technical analysis, Investment structure |
| **Admissibility Criteria** | Evidence must assess ability to undo or pivot from investment |
| **Inadmissible** | Investment cost alone |
| **Example Admissible** | "Platform replacement is irreversible once data migrated; API modernization is reversible" |
| **Example Rejected** | "This costs $500K" (no reversibility assessment) |

#### Lens 5.4 - Dependency Resolution

| Attribute | Specification |
|-----------|---------------|
| **Admissible Sources** | Cross-reference to other axes, Roadmap analysis |
| **Admissibility Criteria** | Evidence must show blocking dependencies between investments |
| **Inadmissible** | Standalone investment analysis |
| **Example Admissible** | "Settlement decoupling must complete before supplier expansion can proceed" |
| **Example Rejected** | "We should decouple settlement" (no dependency context) |

---

## 5. Claims Specification

### 5.1 What a Claim Is

A **claim** is a decision-relevant assertion derived from evidence through a lens.

Claims:
* Are axis-specific
* Are falsifiable
* Are confidence-rated

### 5.2 Claim Template

```markdown
Claim ID: A{axis}-C-{seq}
Axis: (1-5)
Lens: (lens number and name)
Claim Statement: (decision-relevant, falsifiable assertion)
Decision Relevance: (what decision this informs)
Supporting Evidence IDs: (E-* references)
Confidence: High | Medium | Low
Claim Reversibility: Hard | Medium | Easy
If Unaddressed: (consequence of ignoring this claim)
```

### 5.3 Claim ID Convention

Claim IDs follow the pattern: `CLM-{CATEGORY}-{SEQ}` or `A{axis}-C-{seq}`

| Category | Code | Example |
|----------|------|---------|
| Complexity | CMPLX | CLM-CMPLX-001 |
| Coupling | COUP | CLM-COUP-001 |
| Security | SEC | CLM-SEC-001 |
| Quality | QUAL | CLM-QUAL-001 |
| Distribution | DIST | CLM-DIST-001 |
| Knowledge | KNOW | CLM-KNOW-001 |
| Operational | OPS | CLM-OPS-001 |
| Architectural | ARCH | CLM-ARCH-001 |

### 5.4 Confidence Calculation

```
Confidence Level = f(evidence_count, reliability_profile, source_diversity, corroboration)
```

#### Decision Table

| Evidence Count | Min Reliability | Source Types | Corroboration | Confidence |
|----------------|-----------------|--------------|---------------|------------|
| >=3 | >=2 High | >=2 types | Full | **HIGH** |
| >=3 | >=1 High | >=2 types | Partial | **HIGH** |
| 2 | >=1 High | >=2 types | Full | **HIGH** |
| 2 | >=1 High | 1 type | - | **MEDIUM** |
| 2 | All Medium | >=2 types | Full | **MEDIUM** |
| 1 | High | - | - | **MEDIUM** |
| 1 | Medium/Low | - | - | **LOW** |
| Any | Conflicting | - | - | **LOW** |

#### Corroboration Rules

| Level | Criteria |
|-------|----------|
| **Full** | Tool + Interview agree on same observation; Code + Data inspection agree; Multiple interviews (>=2) independently report same pattern |
| **Partial** | Single interview confirms tool finding; Code inspection extends tool finding |
| **None** | Single source only; Sources address different aspects |

### 5.5 Falsifiability Criteria

Every claim must pass this checklist:

```
[ ] OBSERVABLE: Claim references observable state or behavior
   OK: "Module A calls Module B synchronously"
   BAD: "The architecture is fragile"

[ ] SPECIFIC: Claim specifies scope and boundaries
   OK: "Settlement processing cannot be deployed independently of onboarding"
   BAD: "The system has coupling issues"

[ ] TESTABLE: A procedure exists to verify or disprove
   OK: "Adding a new supplier type requires modifying >=20 files" (can count)
   BAD: "The code is hard to change" (no test)

[ ] OBJECTIVE: No subjective adjectives without operationalization
   OK: "Change coupling: 87% of PricingEngine commits also touch OrderProcessor"
   BAD: "PricingEngine and OrderProcessor are tightly coupled" (what's tight?)

[ ] DISPROOF DEFINED: Claim states what would disprove it
   OK: "Claim is false if settlement can be deployed without onboarding restart"
   BAD: (no disproof condition stated)
```

#### Claim Rewriting Examples

| Unfalsifiable | Falsifiable |
|---------------|-------------|
| "The architecture is bad" | "The platform has 14 cyclic dependencies between core modules, preventing independent deployment" |
| "The team has knowledge silos" | "Alice is sole committer to Settlement (12K LOC); no commits from others in 3 years" |
| "Changes are risky" | "87% of PricingEngine commits require same-day changes to OrderProcessor" |
| "Data quality is poor" | "Contract values in `contracts` differ from `invoices` sum by >10% for 23% of records" |

### 5.6 Reversibility Semantics

#### Claim Reversibility

**Definition:** "If we are wrong about this claim, how hard is it to course-correct?"

| Level | Definition | Examples |
|-------|------------|----------|
| **Hard** | Architectural decision locked; unwinding requires major rework | "Platform is structurally fit" - discovered it's not after 6 months of building |
| **Medium** | Code changes required but scope is bounded | "Modules can be independently deployed" - discovered they can't, need 2-month decoupling |
| **Easy** | Configuration, process, or minor code change | "Settlement logic is correct" - found bug, fixed in 2 days |

#### Investment Reversibility

**Definition:** "If this investment doesn't achieve expected outcomes, how much is recoverable?"

| Level | Definition | Examples |
|-------|------------|----------|
| **Low** | Sunk cost; cannot revert or repurpose | Platform replacement once data migrated; team restructuring |
| **Medium** | Partial recovery; some value retained | Feature build (code remains); team training (skills remain) |
| **High** | Mostly recoverable; can pivot | POC/spike (learning gained); tool evaluation (knowledge gained) |

#### Relationship

```
Claim Reversibility informs Investment Reversibility:

If HIGH reversibility claim -> LOW reversibility investment: CAUTION
  (Investing heavily on uncertain claim)

If LOW reversibility claim -> HIGH reversibility investment: OK
  (Testing claim with recoverable investment)
```

### 5.7 Priority Scoring

```
priority_score = (severity x 0.30) +
                 (changeability_impact x 0.25) +
                 (business_exposure x 0.25) +
                 (remediation_effort x 0.10) +
                 (evidence_strength x 0.10)
```

#### Priority Tiers

| Tier | Score Range | Definition | Action |
|------|-------------|------------|--------|
| **P1 (Must Address)** | 0.75 - 1.00 | High severity + high business exposure | Pre-close remediation or deal condition |
| **P2 (Should Address)** | 0.50 - 0.74 | High severity OR high business exposure | First 90-day remediation plan |
| **P3 (Track)** | 0.25 - 0.49 | Medium severity, medium exposure | Technical debt backlog |
| **P4 (Monitor)** | 0.00 - 0.24 | Low severity, informational | No action required |

---

## 6. Cross-Axis Constraints

### 6.1 Constraint Types

| Type | Definition | Example |
|------|------------|---------|
| **BLOCKS** | Downstream axis decision cannot be finalized until upstream axis resolves | Axis 3 "Do not proceed" blocks all other axis implementations |
| **CONSTRAINS** | Downstream axis decision must acknowledge and incorporate upstream state | Axis 2 "High cost-of-change" constrains Axis 5 sequencing timelines |
| **REQUIRES** | Upstream axis decision mandates specific allocation in downstream | Axis 4 "MVP required" requires Axis 5 to allocate data investment |

### 6.2 Constraint Matrix

```
FROM v / TO ->    | Axis 1 | Axis 2 | Axis 3 | Axis 4 | Axis 5 |
------------------+--------+--------+--------+--------+--------+
Axis 1 (Platform) |   -    |CONSTRAINS|   -   |   -    |REQUIRES|
Axis 2 (Change)   |   -    |   -    |   -    |   -    |CONSTRAINS|
Axis 3 (Execution)| BLOCKS | BLOCKS |   -   | BLOCKS | BLOCKS |
Axis 4 (Data)     |   -    |   -    |   -    |   -    |REQUIRES|
Axis 5 (Invest)   |   -    |   -    |   -    |   -    |   -    |
```

### 6.3 Constraint Resolution Protocol

```
1. Evaluate Axis 3 (Execution) FIRST
   - If "Do not proceed": STOP, no further axis decisions until remediated
   - If "Guardrails required": Document guardrails, continue

2. Evaluate Axis 1 (Platform) SECOND
   - Decision (Extend/Modernize/Replace) gates platform-level investments

3. Evaluate Axis 2 (Change) and Axis 4 (Data) IN PARALLEL
   - Axis 2 constrains timelines
   - Axis 4 mandates data investments

4. Evaluate Axis 5 (Investment) LAST
   - Must incorporate all upstream constraints and requirements
```

---

# PART II: EXECUTION

---

## 7. Process Phases & Timeline

### 7.1 Six-Phase Workflow

```
+-----------------------------------------------------------------------------+
|                         TECHNICAL DUE DILIGENCE PROCESS                      |
+-----------------------------------------------------------------------------+
|                                                                             |
|  PHASE 1: Automated Facts (0.5-1 day)                                       |
|      | Tools: scc, lizard, trivy, gitleaks, semgrep, roslyn, git-sizer      |
|      | Output: E-AUTO-* evidence items                                      |
|      v                                                                      |
|  PHASE 2: Manual + AI Code Inspection (1-2 days)                            |
|      | Risk-ranked sampling, AI-assisted analysis                           |
|      | Output: E-MAN-* evidence items                                       |
|      v                                                                      |
|  PHASE 3: Engineer Interviews (1-2 days)                                    |
|      | Per Interview Protocol (48 questions, 5 roles)                       |
|      | Output: E-INT-* evidence items                                       |
|      v                                                                      |
|  PHASE 4: Triangulation (0.5 day)                                           |
|      | Compare automated/manual vs interview evidence                       |
|      | Output: Validation matrix, conflict register                         |
|      |                                                                      |
|      +---- Conflicts? ----> Loop back for resolution                        |
|      v                                                                      |
|  PHASE 5: Second Iteration (0.5-1 day)                                      |
|      | Resolve conflicts, gather additional evidence                        |
|      | Output: E-HARD-* hardened evidence                                   |
|      v                                                                      |
|  PHASE 6: Claim & Decision Generation (0.5-1 day)                           |
|      | Claims -> Risks/Opportunities -> Investments -> Decisions            |
|      | Output: IC Report, Roadmap, Capex/Opex                               |
|      v                                                                      |
|  +========================================================================+ |
|  ||                      IC REPORT DELIVERED                             || |
|  +========================================================================+ |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### 7.2 Base Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Week 0-1 | 1 week | Setup, tool runs, interviews scheduled |
| Week 2 | 1 week | Evidence construction, inspection |
| Week 3 | 1 week | Lens routing, claim drafting |
| Week 4 | 1 week | Axis decisions, cross-axis checks |
| Week 5-6 | 1-2 weeks | Roadmap, CAPEX, IC packaging |
| **Total** | **5-7 weeks** | |

### 7.3 Scaling Adjustments

| Factor | Threshold | Adjustment | Phase Affected |
|--------|-----------|------------|----------------|
| **Codebase size** | >500K LOC | +1 day per 250K LOC | Week 1-2 |
| **Codebase size** | >1M LOC | +1 week | Week 1-2 |
| **Interview count** | >5 interviews | +1 day per 2 interviews | Week 1-2 |
| **Data domains** | >3 major domains | +3 days per domain | Week 2 |
| **External integrations** | >5 integrations | +2 days per integration | Week 2 |
| **Multi-repo** | >3 repositories | +1 week | Week 1-3 |
| **Organizational complexity** | >3 teams | +3 days | Week 3-4 |
| **IC timeline pressure** | <4 weeks available | Reduce scope, not quality | All |

### 7.4 Parallelization Guide

| Activity | Parallelizable? | Dependencies |
|----------|----------------|--------------|
| Tool runs | Yes (all tools) | Repo access |
| Code inspection | Partial (by area) | Tool outputs |
| Interviews | Partial (3/day max) | Scheduling |
| Evidence construction | Yes (by source type) | Raw inputs |
| Lens routing | Partial (by axis) | All evidence |
| Claim drafting | Partial (by axis) | Lens routing |
| Axis decisions | Limited (Axis 3 first) | All claims for axis |
| Cross-axis checks | Sequential | All axis decisions |
| Roadmap derivation | Sequential | Cross-axis resolution |
| IC packaging | Sequential | All above |

### 7.5 Phase 1: Automated Facts

**Objective:** Collect objective, reproducible metrics from the codebase using automated tools.

**Activities:**

1. **Repository Setup**
   - Clone repository at specified commit
   - Configure tool environments
   - Verify access and permissions

2. **Tool Execution**
   ```bash
   # Run orchestrator for full pipeline
   python src/sot-engine/orchestrator.py --repo-path <path> --commit <sha>

   # Or run individual tools
   cd src/tools/scc && make analyze
   cd src/tools/lizard && make analyze
   cd src/tools/trivy && make analyze
   cd src/tools/gitleaks && make analyze
   cd src/tools/semgrep && make analyze
   ```

3. **Query Evidence Items**
   - Execute evidence extraction queries
   - Apply thresholds (see Appendix A)
   - Generate E-AUTO-* evidence items

**Tool Coverage:**

| Tool | Evidence Types | Key Metrics |
|------|---------------|-------------|
| **scc** | E-CMPLX-*, E-DIST-* | Lines, blanks, comments, code per file |
| **lizard** | E-CMPLX-*, E-DIST-* | CCN, NLOC, parameter count per function |
| **trivy** | E-SEC-* | CVEs by severity, IaC misconfigurations |
| **gitleaks** | E-SEC-* | Exposed secrets with location and type |
| **semgrep** | E-QUAL-*, E-COUP-* | Code smells, coupling patterns |
| **roslyn** | E-QUAL-* | .NET-specific violations |
| **git-sizer** | E-OPS-*, E-ARCH-* | Repository health, scale indicators |
| **layout-scanner** | E-ARCH-*, E-DIST-* | Directory structure, boundaries |

### 7.6 Phase 2: Manual + AI Code Inspection

**Objective:** Supplement automated findings with expert analysis of high-risk areas.

**Activities:**

1. **Risk-Ranked Sampling**
   - Prioritize files by automated risk score
   - Focus on: High CCN, single-author, high churn, concentration hotspots
   - Sample representative files from each category

2. **Code Inspection**
   - Review architecture vs. code reality
   - Identify patterns not detectable by tools
   - Assess business logic placement
   - Check for hidden coupling (database triggers, configs)

3. **AI-Assisted Analysis**
   - Use LLM for code summarization
   - Pattern recognition across large codebases
   - Dependency graph interpretation

4. **Document Findings**
   - Create E-MAN-* evidence items
   - Link to related E-AUTO-* items
   - Capture expert interpretation

### 7.7 Phase 3: Engineer Interviews

**Objective:** Validate automated and manual findings through stakeholder conversations.

See Section 8 for complete interview protocol.

### 7.8 Phase 4: Triangulation

**Objective:** Compare evidence from all sources to identify agreements, conflicts, and gaps.

**Triangulation Logic:**

```
+-----------------------------------------------------------------------------+
|                         TRIANGULATION OUTCOMES                               |
+-----------------------------------------------------------------------------+
|                                                                             |
|  CODE + METRICS + INTERVIEW AGREE                                           |
|      -> HIGH confidence                                                      |
|      -> Proceed to claim generation                                          |
|                                                                             |
|  CODE + METRICS AGREE, INTERVIEW CONTEXTUALIZES                             |
|      -> MEDIUM-HIGH confidence                                               |
|      -> Adjust severity per interview context                                |
|                                                                             |
|  CODE + METRICS AGREE, INTERVIEW CHALLENGES                                 |
|      -> INVESTIGATE                                                          |
|      -> Seek additional evidence before proceeding                           |
|                                                                             |
|  CODE + METRICS ONLY (no interview data)                                    |
|      -> MEDIUM confidence                                                    |
|      -> Flag for validation if possible                                      |
|                                                                             |
|  INTERVIEW ONLY (new finding)                                               |
|      -> MEDIUM confidence                                                    |
|      -> Seek corroboration if possible                                       |
|      -> Document as interview-sourced                                        |
|                                                                             |
|  SOURCES CONFLICT                                                           |
|      -> LOW confidence                                                       |
|      -> Add to conflict register                                             |
|      -> MUST resolve before proceeding                                       |
|                                                                             |
+-----------------------------------------------------------------------------+
```

**Validation Matrix Template:**

| Evidence ID | Type | Finding Summary | Interview Validation | Adjusted Confidence | Notes |
|-------------|------|-----------------|---------------------|---------------------|-------|
| E-CMPLX-001 | AUTO | CCN=47 in OrderProcessor | CONFIRMED | HIGH | Team calls it "the blob" |
| E-SEC-003 | AUTO | Exposed AWS key | CONFIRMED | HIGH | Known, rotation planned |
| E-QUAL-007 | AUTO | Magic numbers in 47% files | CONTEXTUALIZED | MEDIUM | Intentional for performance |
| E-OWN-012 | AUTO | Single author on core module | CHALLENGED | LOW | Informal knowledge transfer |

### 7.9 Phase 5: Second Iteration

**Objective:** Resolve conflicts and gather additional evidence for uncertain findings.

**Trigger Criteria:**
- Conflicts in conflict register remain unresolved
- HIGH severity items have only single-source evidence
- Interview revealed areas requiring code verification

**Conflict Resolution Protocol:**

```
1. DOCUMENT both perspectives
   - Evidence IDs from each source
   - Specific assertions that conflict
   - Why they might conflict

2. INVESTIGATE for resolution
   - Additional code inspection
   - Follow-up interview questions
   - Commit messages / PR descriptions
   - External documentation

3. RESOLVE or ESCALATE
   If Resolvable:
   - Document resolution rationale
   - Update validation outcome
   - Adjust confidence
   - Create E-HARD-* item

   If Unresolvable:
   - Mark confidence as LOW
   - Include both perspectives in report
   - Flag for client discussion
   - DO NOT suppress either source

4. NEVER silently discard evidence
```

### 7.10 Phase 6: Claim & Decision Generation

**Objective:** Transform evidence into claims, risks, investments, and platform decisions.

**Claim Generation Flow:**

```
Evidence Clusters               Technical Claims              Execution Risks
----------------               ----------------              ---------------
E-CMPLX-001 -+
E-CMPLX-002 -+-->  CLM-CMPLX-001 --+
E-INT-001 ---+                      |
                                    +-->  RISK-001: Complexity Hotspot
E-DIST-001 --+                      |
E-DIST-002 --+-->  CLM-DIST-001  --+
E-MAN-003 ---+

E-SEC-001 ---+
E-SEC-002 ---+--->  CLM-SEC-001 --->  RISK-002: Security Exposure
E-SEC-003 ---+

E-COUP-001 --+
E-COUP-002 --+--->  CLM-COUP-001 --+
E-INT-007 ---+                      |
                                    +-->  RISK-003: Change Amplification
E-ARCH-001 --+                      |
E-INT-042 ---+--->  CLM-ARCH-001 --+
E-MAN-005 ---+
```

---

## 8. Interview Protocol

### 8.1 Evidence Triangulation Principle

Technical due diligence achieves highest confidence when multiple sources align:

```
+-----------------------------------------------------------------------------+
|                         EVIDENCE TRIANGULATION                               |
+-----------------------------------------------------------------------------+
|                                                                             |
|    CODE ANALYSIS              METRICS                  INTERVIEWS          |
|    -------------              -------                  ----------          |
|    What exists               How much                 Why it exists        |
|    Structure                 Distribution             Intent               |
|    Patterns                  Concentration            Constraints          |
|    Dependencies              Trends                   History              |
|                                                                             |
|                         +-----------+                                       |
|                         |  HARDENED |                                       |
|                         |   CLAIMS  |                                       |
|                         +-----------+                                       |
|                                                                             |
|    When all three sources agree -> HIGH CONFIDENCE                          |
|    When sources conflict -> INVESTIGATE FURTHER                             |
|    When only code/metrics exist -> MEDIUM CONFIDENCE (flag for interview)   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### 8.2 Core Principles

1. **Validate, Don't Lead:** Ask open questions before revealing findings
2. **Seek Disconfirmation:** Actively look for reasons our analysis might be wrong
3. **Capture Uncertainty:** Record what engineers don't know or aren't sure about
4. **Distinguish Fact from Opinion:** Note when responses are firsthand knowledge vs. speculation
5. **Preserve Context:** Record the reasoning, not just the conclusion

### 8.3 Who to Interview

**Minimum viable coverage:** 3-5 engineers for typical engagement

| Role | Why | Questions Focus |
|------|-----|-----------------|
| **Tech Lead / Architect** | Strategic decisions, historical context, system-wide view | Categories 1, 3, 6 |
| **Senior Developer (long tenure)** | Deep technical knowledge, evolution history | Categories 1, 2, 3, 4 |
| **Senior Developer (newer)** | Fresh perspective, onboarding experience | Categories 2, 5 |
| **DevOps / SRE** | Operational reality, deployment, monitoring | Category 2 |
| **Recent Joiner (if available)** | Onboarding pain points, documentation gaps | Category 5 |

**Selection criteria:**
- At least one person with 2+ years on the system
- At least one person with <1 year (fresh perspective)
- Coverage of different subsystems if large codebase
- Mix of builders and operators

### 8.4 Interview Duration

- **Target:** 45-60 minutes per interview
- **Structure:**
  - 5 min: Introduction and context setting
  - 35-40 min: Core questions
  - 10-15 min: Open discussion and follow-ups

### 8.5 Interview Flow

```
[0-5 min]   Introduction & Context
            - Explain purpose (technical assessment, not performance review)
            - Assure confidentiality: findings attributed to "engineers" not names
            - Set expectations: looking for honest assessment, not sales pitch
            - Ask permission to take notes

[5-15 min]  Architecture & Mental Model
            - Questions 1.1, 1.2 (establish baseline)
            - Let them draw/describe the system
            - Note what they emphasize vs. skip

[15-35 min] Deep Dive (tailored to role)
            - Tech Lead: Design intent, history, constraints
            - Developer: Change difficulty, coupling, debt
            - DevOps: Operations, incidents, deployment

[35-50 min] Risk & Knowledge
            - Category 5 (knowledge distribution)
            - Category 6 (risk perception)
            - "What should I have asked that I didn't?"

[50-60 min] Validation & Wrap-up
            - Share 2-3 preliminary findings, ask for reaction
            - "Does this match your experience?"
            - Thank and explain next steps
```

### 8.6 Validation Outcomes

| Outcome | Definition | Action |
|---------|------------|--------|
| **CONFIRMED** | Engineer testimony aligns with automated finding | Increase confidence level; cite both sources |
| **CONTEXTUALIZED** | Finding is accurate but severity should adjust | Add context to claim; adjust severity/confidence |
| **CHALLENGED** | Engineer provides evidence that contradicts finding | Investigate further; may revise or remove claim |
| **EXPANDED** | Interview reveals risk not visible in code analysis | Create new evidence item; generate new claim |

### 8.7 Confidence Markers

Interview evidence carries a confidence marker based on the interviewee's relationship to the information:

| Marker | Definition | Weight |
|--------|------------|--------|
| **Firsthand** | Interviewee has direct experience with the code/system | High |
| **Secondhand** | Interviewee heard about it from someone else | Medium |
| **Speculation** | Interviewee is guessing or extrapolating | Low (note in evidence) |

### 8.8 Note-Taking Template

```markdown
## Interview: [Role]
**Date:** YYYY-MM-DD
**Duration:** XX minutes
**Interviewee Tenure:** X years

### Context
- Primary areas: [components they work on]
- Team size/structure: [relevant context]
- Recent focus: [what they've been working on]

### Architecture & Design
[Notes from questions 1.1-1.7]

Key quote: "[direct quote if notable]"

### Operational Reality
[Notes from questions 2.1-2.8]

Key quote: "[direct quote if notable]"

### Technical Debt & History
[Notes from questions 3.1-3.8]

Key quote: "[direct quote if notable]"

### Change & Coupling
[Notes from questions 4.1-4.8]

Key quote: "[direct quote if notable]"

### Knowledge Distribution
[Notes from questions 5.1-5.8]

Key quote: "[direct quote if notable]"

### Risk Perception
[Notes from questions 6.1-6.8]

Key quote: "[direct quote if notable]"

### Key Findings
1. [Finding with validation outcome and confidence marker]
2. [Finding with validation outcome and confidence marker]
3. [Finding with validation outcome and confidence marker]

### Contradictions with Other Interviews
- [ ] [Note any contradictions with previous interviews]

### Follow-up Needed
- [ ] Verify X with code inspection
- [ ] Ask [other role] about Y
- [ ] Check Z in documentation
```

### 8.9 Interview Evidence Template

```markdown
### E-INT-XXX: [Brief Title]

- **Type:** interview
- **Source:** [Role - not name]
- **Question Category:** architecture | operational | debt | coupling | knowledge | risk
- **Date:** YYYY-MM-DD

**Observation:**
[Paraphrased response - what was said]

**Direct Quote:** (optional)
"[Verbatim quote if captured]"

**Validation Outcome:** CONFIRMED | CONTEXTUALIZED | CHALLENGED | EXPANDED

**Related Evidence:**
- E-XXX-NNN: [linked automated evidence]

**Confidence Marker:** firsthand | secondhand | speculation
**Why It Matters:** [Business impact interpretation]
```

### 8.10 Anti-Patterns to Avoid

#### Leading Questions

| Bad | Better |
|-----|--------|
| "This module looks really complex - is it a problem?" | "Tell me about this module. What's your experience working with it?" |
| "We found 47 CCN which is very high - why is that?" | "Walk me through this function. What does it do?" |
| "Don't you think the test coverage is too low?" | "How confident are you deploying changes to this area?" |
| "This coupling must cause problems, right?" | "How do changes in this area affect other parts of the system?" |

#### Confirmation Bias Traps

- Don't only interview people who will confirm your findings
- Actively ask "What might we have gotten wrong?"
- Include at least one skeptic or contrarian voice
- Present findings neutrally before asking for validation
- Ask about areas where you found nothing - might be something there

---

## 9. Quality Gates

### 9.1 Gate Definitions & Ownership

| Gate | Owner | Verification Method | On Failure |
|------|-------|---------------------|------------|
| Every evidence item has required fields | Technical Lead | Template validation | Return to analyst for completion |
| Every evidence item is anchored | Technical Lead | Anchor existence check | Reject evidence |
| Evidence passes rejection rules | Technical Lead | Rule checklist | Reject or reframe evidence |
| Every claim references >=1 evidence | Principal | Cross-reference audit | Reject claim |
| Every claim passes falsifiability | Principal | Falsifiability checklist | Rewrite claim |
| Every claim assigned to one axis | Principal | Axis assignment review | Reclassify or split claim |
| Every claim has one primary lens | Principal | Lens routing review | Reassign lens |
| Every axis has explicit decision | Engagement Lead | Axis decision review | Escalate or defer |
| Cross-axis constraints resolved | Engagement Lead | Constraint matrix check | Resolve or document |
| Every roadmap item links to axis | Engagement Lead | Traceability audit | Link or defer item |
| No claim without IC presentation | Engagement Lead | Deck review | Add to deck or justify omission |

### 9.2 Gate Sequence

```
Evidence Gates (Technical Lead)
    |
    v
Claim Gates (Principal)
    |
    v
Axis Gates (Principal + Engagement Lead)
    |
    v
Output Gates (Engagement Lead)
    |
    v
IC Review
```

### 9.3 Quality Gates Before IC

Before anything reaches IC, verify:

- [ ] Every claim references admissible evidence
- [ ] Every claim belongs to exactly one axis
- [ ] Every axis has an explicit decision state
- [ ] Every roadmap item traces back to an axis decision
- [ ] Uncertainty and deferrals are explicit

---

## 10. IC Output Specification

### 10.1 Axis Decision Slide Canon

Each axis is presented on **one slide** using this structure:

| Element | Content |
|---------|---------|
| **IC Question** | The question this axis answers |
| **Decision** | Decided / Conditional / Deferred |
| **Claims Synthesis** | 3-6 bullets summarizing key claims |
| **Rationalisation** | 2-3 sentences explaining the decision |
| **Enables / Blocks** | What this decision unlocks or prevents |
| **If Wrong** | Downside + trigger condition |

### 10.2 From Axis Decisions to Roadmap

* Axis 1 defines platform direction
* Axis 2 constrains roadmap scope and confidence
* Axis 3 gates execution
* Axis 4 defines minimum data investment
* Axis 5 defines sequencing and staging

### 10.3 Roadmap & CAPEX Linkage

Every roadmap item and CAPEX/OPEX allocation must reference:
* Originating axis decision
* Underlying claims

**Roadmap Item Template:**

```markdown
Roadmap Item: R-{seq}
Objective: (what this achieves)
Linked Axis: (axis number and decision)
Linked Claims: (claim IDs)
Scope: (what's included)
Timeframe: (months)
Dependencies: (other roadmap items)
Risk Reduced: (specific risks addressed)
```

### 10.4 Investment Entity

```markdown
Investment ID: INV-{seq}
Title: (short title)
Description: (full description)
Rationale: (why this investment is needed)
Investment Type: remediation | modernization | capacity | tooling
Urgency: pre-close | 90-day | 6-month | 12-month

Effort Range: (min-max person-months)
Team Size: (min-max engineers)
Duration: (min-max months)
Cost Type: CAPEX | OPEX | mixed

Addresses Risks: (risk IDs)
Enables Opportunities: (opportunity IDs)
Blocked By: (investment IDs)

Scope: (what's included)
Success Criteria:
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2

Cost Factors:
- Factor that could increase cost
- Factor that could decrease cost
```

### 10.5 Decision Entity

```markdown
Decision ID: DEC-{seq}
Decision Type: EXTEND | MODERNIZE | REPLACE
Recommendation: (full recommendation statement)
Go/No-Go: GO | NO-GO | CONDITIONAL

Conditions:
- Condition 1
- Condition 2

Pre-Close Requirements:
- Requirement 1

Post-Close Investments:
- INV-XXX: Investment title

Dimension Assessments:
| Dimension | Rating |
|-----------|--------|
| Technical Viability | GREEN/YELLOW/RED |
| Security Posture | GREEN/YELLOW/RED |
| Operational Stability | GREEN/YELLOW/RED |
| Change Velocity | GREEN/YELLOW/RED |
| Knowledge Continuity | GREEN/YELLOW/RED |
| Remediation Cost | HIGH/MEDIUM/LOW |
| Rewrite Risk | HIGH/MEDIUM/LOW |

Supporting Risks: (risk IDs)
Supporting Claims: (claim IDs)
Investment IDs: (investment IDs)

Acknowledged Risks:
- Risk being accepted 1
- Risk being accepted 2
```

---

# PART III: WORKED EXAMPLE

---

## 11. End-to-End Walkthrough

### 11.1 Scenario Context

* **Context:** Energy platform with multiple suppliers
* **Focus area:** Supplier onboarding & settlement processing
* **IC concern:** Can the platform support onboarding additional suppliers post-close without destabilising operations?

---

### 11.2 Step 1 - Raw Inputs

**Tool Output:**
* NDepend shows cyclic dependencies between `Onboarding.Core` and `Settlement.Core`
* SCC analysis shows that onboarding-related commits touch 22-30 files on average

**Code Analysis:**
* Shared persistence entity `ContractState` used by onboarding, settlement, and billing
* Business rules for settlement embedded in onboarding workflows

**Interviews:**
* Lead engineer: "Any new supplier change usually requires touching settlement logic."
* CTO: "We never really separated onboarding and settlement cleanly."

---

### 11.3 Step 2 - Evidence Construction

**Evidence E-01:**
* **Source Type:** Tool (NDepend)
* **Anchor:** `Onboarding.Core <-> Settlement.Core`
* **Observation:** Cyclic dependency between onboarding and settlement modules
* **Scope:** Systemic
* **Reliability:** High

**Evidence E-02:**
* **Source Type:** Code Inspection
* **Anchor:** `ContractState` entity
* **Observation:** Shared persistence model across onboarding and settlement
* **Scope:** Cross-module
* **Reliability:** High

**Evidence E-03:**
* **Source Type:** Interview
* **Anchor:** Lead Engineer (2026-02-XX)
* **Observation:** Supplier onboarding changes regularly require settlement changes
* **Scope:** Systemic
* **Reliability:** Medium

---

### 11.4 Step 3 - Axis and Lens Selection

**Axis Selection:** The evidence speaks to **structural properties of the platform**, not effort or governance.
-> **Axis 1 - Structural Platform Fitness**

**Lens Selection:**
* Cyclic dependencies -> **Lens 1.1 Architectural Boundaries**
* Shared persistence semantics -> **Lens 1.2 Data Architecture Semantics**

**Primary lens selected:** Lens 1.1 Architectural Boundaries

---

### 11.5 Step 4 - Claim Construction

**Claim A1-C-01:**
* **Axis:** Structural Platform Fitness
* **Lens:** Architectural Boundaries
* **Claim Statement:** The platform enforces implicit coupling between supplier onboarding and settlement processing, preventing independent evolution of either domain.
* **Decision Relevance:** Platform direction (extend vs modernise vs replace)
* **Supporting Evidence:** E-01, E-02, E-03
* **Confidence:** High
* **Claim Reversibility:** Hard
* **If Unaddressed:** Supplier growth will trigger escalating change risk and potential forced rewrite

---

### 11.6 Step 5 - Axis Decision Synthesis

**Axis 1 - Structural Platform Fitness:**
* **Claims Considered:** A1-C-01 (and related supporting claims)
* **Decision:** **Modernise (with constraints)**

**Rationalisation:** Structural boundaries exist but are violated by shared persistence and cyclic dependencies. While not yet irrepairable, extension without boundary enforcement will amplify risk. Targeted modernisation is required.

---

### 11.7 Step 6 - Cross-Axis Constraint Check

* **Axis 2 (Cost-of-Change):** High change amplification -> roadmap must be constrained
* **Axis 3 (Execution Control):** Guardrails required to enforce boundary changes
* **Axis 4 (Data Steering):** Shared persistence also affects revenue traceability -> analytics MVP justified

No axis contradicts the Axis 1 decision.

---

### 11.8 Step 7 - Roadmap Derivation

**Roadmap Item R-01:**
* **Objective:** Decouple onboarding from settlement
* **Linked Axis:** Axis 1, Axis 2
* **Linked Claim:** A1-C-01
* **Scope:** Introduce explicit domain boundary and persistence separation
* **Timeframe:** Months 1-4
* **Dependency:** Architecture ownership (Axis 3)
* **Risk Reduced:** Hidden rewrite risk

---

### 11.9 Step 8 - CAPEX / OPEX Implication

* **CAPEX:** Medium (bounded refactoring, no full rebuild)
* **OPEX:** Incremental (architecture leadership, governance)
* **Staging:** Approved as part of first 6-12 month plan

---

### 11.10 Step 9 - IC Output (Condensed)

**Decision:** Modernise platform with explicit boundary enforcement

**Why:** Structural coupling between onboarding and settlement prevents safe growth

**Enables:** Controlled supplier expansion

**Blocks:** Rapid onboarding without restructuring

**If Wrong:** Escalation to full replacement required

---

# APPENDICES

---

## Appendix A: Evidence Categories & Thresholds

### A.1 Complexity (E-CMPLX)

**Definition:** Measures of code intricacy that affect understandability, testability, and change cost.

**Purpose:** Identify code that requires disproportionate effort to change safely.

**What to Look For:**
- Functions with cyclomatic complexity (CCN) > 15
- Files with excessive lines of code (> 500 LOC)
- Deeply nested control structures (> 4 levels)
- High parameter counts (> 5 parameters)
- Functions with many local variables

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| lizard | CCN per function, NLOC, parameter count, token count |
| scc | Lines, blanks, comments, code lines per file |

**Threshold Definitions:**

| Metric | Low | Medium | High | Critical |
|--------|-----|--------|------|----------|
| CCN | 5-10 | 11-15 | 16-30 | >30 |
| File LOC | 200-500 | 501-1000 | 1001-2000 | >2000 |
| Function NLOC | 20-50 | 51-100 | 101-200 | >200 |
| Parameters | 3-4 | 5-6 | 7-10 | >10 |

**Example Evidence Items:**
```
E-CMPLX-001: OrderProcessor.ProcessOrder() has CCN=47, 152 NLOC, 12 parameters
E-CMPLX-002: src/core/ directory has Gini=0.78 for CCN distribution (concentrated)
E-CMPLX-003: PaymentService.cs has 2,341 lines; 67% of module LOC
```

---

### A.2 Coupling (E-COUP)

**Definition:** Measures of interconnection between components that affect change isolation.

**Purpose:** Identify where changes propagate unexpectedly (change amplification risk).

**What to Look For:**
- High fan-out (calls to many external components)
- High fan-in (called by many other components)
- Shared database access patterns across services
- Direct cross-module dependencies
- Implicit coupling via shared state or config
- God classes that everything depends on

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| semgrep | Pattern-based coupling detection |
| symbol-scanner | Fan-in, fan-out, call graphs |

**Threshold Definitions:**

| Metric | Low | Medium | High | Critical |
|--------|-----|--------|------|----------|
| Fan-out | 5-10 | 11-20 | 21-50 | >50 |
| Fan-in | 10-20 | 21-50 | 51-100 | >100 |
| Shared DB accessors | 1-2 | 3-5 | 6-10 | >10 |

**Example Evidence Items:**
```
E-COUP-001: OrderService has fan_out=89 (calls 89 distinct external symbols)
E-COUP-002: 12 services directly access orders.* tables without abstraction
E-COUP-003: PricingEngine changes require coordinated deployment of 4 services
```

---

### A.3 Security (E-SEC)

**Definition:** Vulnerabilities, exposures, and security misconfigurations that create breach risk.

**Purpose:** Identify immediate security remediations and systemic security posture issues.

**What to Look For:**
- Known CVEs in dependencies (especially CRITICAL/HIGH)
- Exposed secrets (API keys, passwords, tokens)
- Infrastructure as Code misconfigurations
- Missing security headers or controls
- Outdated dependencies with known vulnerabilities
- Hardcoded credentials in source

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| trivy | CVEs by severity, IaC misconfigurations |
| gitleaks | Exposed secrets with location and type |

**Threshold Definitions:**

| Metric | Low | Medium | High | Critical |
|--------|-----|--------|------|----------|
| CVE Severity | LOW | MEDIUM | HIGH | CRITICAL |
| Secret exposure | - | - | Any | Any |
| IaC misconfig | LOW | MEDIUM | HIGH | CRITICAL |

**Example Evidence Items:**
```
E-SEC-001: log4j@2.14.0 - CVE-2021-44228 (CRITICAL) in pom.xml
E-SEC-002: AWS access key exposed in src/config/deploy.py:42
E-SEC-003: 23 HIGH severity IaC misconfigurations in terraform/
```

---

### A.4 Quality (E-QUAL)

**Definition:** Code smell density and violation patterns that indicate maintainability issues.

**Purpose:** Identify systemic patterns that increase maintenance burden.

**What to Look For:**
- Repeated code smell patterns
- Violation density by category
- Anti-patterns (god classes, feature envy, long methods)
- Missing error handling
- Inconsistent coding standards
- Dead code or unused imports

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| semgrep | Code smells by category and severity |
| roslyn-analyzers | .NET-specific violations |
| sonarqube | Issues, duplication, code smells |

**Threshold Definitions:**

| Metric | Low | Medium | High | Critical |
|--------|-----|--------|------|----------|
| Smell density (per 100 LOC) | <0.5 | 0.5-1 | 1-2 | >2 |
| Pattern occurrence | <10% | 10-30% | 30-50% | >50% |

**Example Evidence Items:**
```
E-QUAL-001: "magic-number" smell in 47% of files (systemic pattern)
E-QUAL-002: src/services/ has smell density of 3.2 per 100 LOC
E-QUAL-003: 156 Roslyn CA1062 violations (null check missing)
```

---

### A.5 Distribution (E-DIST)

**Definition:** Statistical patterns showing concentration or inequality in code metrics.

**Purpose:** Identify hotspots and imbalances that create single points of failure.

**What to Look For:**
- High Gini coefficient (> 0.6) indicating concentration
- High Palma ratio (> 2.0) indicating top-heavy distribution
- Extreme top-10% share (> 50% of total)
- Outlier files (> p99 for any metric)
- Skewed distributions indicating structural imbalance

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| All rollup models | Gini, Palma, Theil, Hoover indices |
| Distribution stats | p25-p99 percentiles, skewness, kurtosis |

**Threshold Definitions:**

| Metric | Low | Medium | High | Critical |
|--------|-----|--------|------|----------|
| Gini | <0.4 | 0.4-0.6 | 0.6-0.8 | >0.8 |
| Palma | <1.5 | 1.5-2.5 | 2.5-4 | >4 |
| Top 10% share | <30% | 30-50% | 50-70% | >70% |

**Example Evidence Items:**
```
E-DIST-001: CCN Gini=0.82 in src/services/; top 5 files contain 67% of complexity
E-DIST-002: Palma ratio=4.3 for LOC; top 10% has 4.3x the lines of bottom 40%
E-DIST-003: Vulnerability Gini=0.91; 3 packages contain 89% of CVEs
```

---

### A.6 Knowledge (E-KNOW)

**Definition:** Patterns indicating knowledge concentration and bus factor risk.

**Purpose:** Identify areas where personnel changes create continuity risk.

**What to Look For:**
- Single-author files for critical code
- Low author count on large/complex files
- Recent departure of key contributors
- Long tenure concentration (one person for years)
- Undocumented critical paths

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| git-blame-scanner | Author concentration, churn, bus factor |

**Threshold Definitions:**

| Metric | Low | Medium | High | Critical |
|--------|-----|--------|------|----------|
| Bus factor | >=3 | 2 | 1 | 1 (departing) |
| Single author LOC | <500 | 500-1000 | 1000-2000 | >2000 |
| Ownership % | <50% | 50-70% | 70-90% | >90% |

**Example Evidence Items:**
```
E-KNOW-001: OrderProcessor.cs (4,500 LOC) has single author; no pair programming
E-KNOW-002: src/core/ has bus factor=1; Alice authored 89% of commits
E-KNOW-003: Lead architect departing Q2; no documented succession plan
```

---

### A.7 Operational (E-OPS)

**Definition:** Indicators of production reliability, deployment risk, and operational burden.

**Purpose:** Identify risks that only manifest in production operation.

**What to Look For:**
- Deployment complexity and frequency
- Rollback capability and testing
- Manual processes in release pipeline
- Incident frequency and mean time to recovery
- Monitoring and alerting coverage
- On-call burden indicators

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| git-sizer | Repository health, blob sizes, commit patterns |
| layout-scanner | Structure, configuration file presence |

**Example Evidence Items:**
```
E-OPS-001: Deployment requires 3-hour manual process with 12 steps
E-OPS-002: Monthly incidents in OrderProcessor averaging 4hr MTTR
E-OPS-003: Pricing config changes require direct database manipulation
```

---

### A.8 Architectural (E-ARCH)

**Definition:** Structural patterns that constrain evolution or indicate technical boundaries.

**Purpose:** Identify where incremental change breaks down and rewrites may be required.

**What to Look For:**
- Monolithic structures without internal boundaries
- Missing abstraction layers
- Cross-cutting concerns embedded in business logic
- Circular dependencies between modules
- Technology constraints (framework lock-in)
- Integration patterns that resist change

**Primary Tools:**
| Tool | Metrics Provided |
|------|------------------|
| layout-scanner | Directory structure, component boundaries |
| git-sizer | Repository scale and health |
| symbol-scanner | Dependency graphs, module boundaries |

**Example Evidence Items:**
```
E-ARCH-001: OrderProcessor class handles 4 distinct responsibilities; no seams
E-ARCH-002: Two failed decomposition attempts documented (2023, 2024)
E-ARCH-003: Framework upgrade blocked by 45 deprecated API usages
```

---

## Appendix B: Full Interview Question Bank

### B.1 Category 1: Architecture & Design Intent (7 questions)

**Purpose:** Understand WHY the system is structured as it is. Distinguish intentional complexity from accidental complexity.

| # | Question | What It Reveals | Primary Lens |
|---|----------|-----------------|--------------|
| 1.1 | "Walk me through the high-level architecture. What are the major components and how do they interact?" | Mental model vs. actual structure; what they emphasize reveals priorities | 1.1, 1.2 |
| 1.2 | "What constraints shaped this architecture? (legacy systems, performance, team size, deadlines)" | Whether architecture is intentional or accidental | 1.1, 1.4 |
| 1.3 | "If you could redesign one part of the system, what would it be and why?" | Known pain points and technical debt awareness | 1.1, 1.4 |
| 1.4 | "What technology choices would you make differently today?" | Outdated decisions that create friction | 1.4 |
| 1.5 | "Are there parts of the system where the code doesn't match your mental model?" | Areas where documentation or understanding has drifted | 1.1 |
| 1.6 | "What parts of the architecture are you most proud of?" | Good patterns worth preserving | 1.4 |
| 1.7 | "How has the architecture evolved over the past 2-3 years? What drove those changes?" | Trajectory and stability | 1.1 |

---

### B.2 Category 2: Operational Reality (8 questions)

**Purpose:** Learn how the system ACTUALLY behaves in production, which often differs from what code suggests.

| # | Question | What It Reveals | Primary Lens |
|---|----------|-----------------|--------------|
| 2.1 | "What breaks most often? What's your most common production incident?" | Real reliability risks vs. theoretical concerns | 1.3, 3.4 |
| 2.2 | "Walk me through your deployment process. What could go wrong?" | Release risk and operational maturity | 2.3, 3.4 |
| 2.3 | "How do you monitor the system? What alerts wake you up at night?" | Observability gaps and known fragile areas | 3.4 |
| 2.4 | "What's your rollback process if a deployment goes wrong?" | Recovery capability and blast radius of changes | 2.3 |
| 2.5 | "Are there manual processes that should be automated but aren't?" | Operational debt and undocumented dependencies | 3.4 |
| 2.6 | "What's your on-call rotation like? What keeps people busy?" | Maintenance burden and firefighting load | 3.4 |
| 2.7 | "Are there features that are 'turned off' but still in the codebase?" | Dead code and feature flag debt | 2.2 |
| 2.8 | "When was the last major outage? What caused it? How was it resolved?" | Systemic weaknesses and recovery capability | 1.3, 3.4 |

---

### B.3 Category 3: Technical Debt & History (8 questions)

**Purpose:** Uncover the story behind code patterns. Code archaeology shows what exists, not why.

| # | Question | What It Reveals | Primary Lens |
|---|----------|-----------------|--------------|
| 3.1 | "What's on your 'should fix someday' list that never gets prioritized?" | Known debt that analysis might miss | 2.2 |
| 3.2 | "Tell me about a shortcut taken under deadline pressure. Is it still there?" | Intentional debt and its status | 2.2, 1.1 |
| 3.3 | "Are there areas of the code that people avoid touching? Why?" | Fear zones and change resistance | 2.2, 3.2 |
| 3.4 | "What would break if you upgraded [major dependency]?" | Hidden coupling and version constraints | 1.4, 2.1 |
| 3.5 | "Is there code that 'works but nobody knows why'?" | Tribal knowledge dependencies | 3.2 |
| 3.6 | "What documentation exists? How accurate is it?" | Documentation debt | 3.2, 3.4 |
| 3.7 | "Have there been any significant rewrites or migrations? How did they go?" | History of change capability | 1.1 |
| 3.8 | "Is there any 'clever' code that you wish was simpler?" | Complexity that even authors regret | 2.2 |

---

### B.4 Category 4: Change Difficulty & Coupling (8 questions)

**Purpose:** Understand WHERE and WHY change is hard. Coupling metrics show connections; engineers know which ones matter.

| # | Question | What It Reveals | Primary Lens |
|---|----------|-----------------|--------------|
| 4.1 | "If I asked you to change how pricing works, what would you need to touch?" | Change amplification and coupling | 2.1, 1.1 |
| 4.2 | "What's the hardest change you've had to make recently? Why was it hard?" | Real coupling vs. metric-based coupling | 2.1, 2.2 |
| 4.3 | "Are there 'don't touch' modules? What happens if you modify them?" | Risk zones and blast radius | 2.2, 1.1 |
| 4.4 | "How do changes in [component A] affect [component B]?" | Dependency understanding | 2.1 |
| 4.5 | "What takes longer to change than you'd expect?" | Hidden complexity | 2.1, 2.4 |
| 4.6 | "Do you have to coordinate with other teams for certain changes?" | Organizational coupling | 2.1, 3.1 |
| 4.7 | "What would make this codebase easier to modify?" | Change friction insights | 1.4, 2.1 |
| 4.8 | "How do you test changes before deployment? What gives you confidence?" | Change safety mechanisms | 2.3 |

---

### B.5 Category 5: Knowledge Distribution (8 questions)

**Purpose:** Identify bus factor and knowledge silos. Git blame shows authorship; engineers know who actually understands code.

| # | Question | What It Reveals | Primary Lens |
|---|----------|-----------------|--------------|
| 5.1 | "If I have a question about [complex area], who do I ask?" | Knowledge concentration | 3.2 |
| 5.2 | "Who understands the most about how [critical component] works?" | Single points of knowledge failure | 3.2 |
| 5.3 | "What happens when [key person] goes on vacation?" | Actual vs. documented knowledge transfer | 3.2 |
| 5.4 | "Are there areas where only one person has made changes?" | Code ownership silos | 3.2 |
| 5.5 | "How does a new developer get up to speed? How long does it take?" | Onboarding difficulty and documentation quality | 3.2 |
| 5.6 | "What would you tell your replacement on day one?" | Critical undocumented knowledge | 3.2 |
| 5.7 | "Have you lost team members recently? What knowledge left with them?" | Knowledge loss events | 3.2 |
| 5.8 | "What areas of the codebase are underdocumented but critical?" | Documentation debt | 3.2 |

---

### B.6 Category 6: Risk Perception (8 questions)

**Purpose:** Surface concerns that aren't visible in code. Engineers have intuitions we should capture.

| # | Question | What It Reveals | Primary Lens |
|---|----------|-----------------|--------------|
| 6.1 | "What keeps you up at night about this system?" | Deepest concerns | ALL (screening) |
| 6.2 | "What's the biggest risk that leadership doesn't know about?" | Hidden risks | ALL (screening) |
| 6.3 | "If something catastrophic happened to this system, what would it be?" | Failure mode awareness | 1.3 |
| 6.4 | "Are there fragile parts of the system that haven't broken... yet?" | Latent risk | 1.3, 2.2 |
| 6.5 | "What would happen if traffic suddenly 10x'd?" | Scalability concerns | 1.3 |
| 6.6 | "Are there security concerns you've raised that haven't been addressed?" | Security debt visibility | 1.3 |
| 6.7 | "What assumptions about the business is the code making that might change?" | Business coupling | 1.4 |
| 6.8 | "If you had 3 months and 2 engineers to improve the system, where would you focus?" | Prioritization insight | 5.1, 5.2 |

---

### B.7 Question-to-Lens Mapping Summary

| Question Category | Primary Axis | Primary Lenses |
|-------------------|--------------|----------------|
| Category 1 (Architecture) | Axis 1 | 1.1, 1.2, 1.4 |
| Category 2 (Operational) | Axis 2, Axis 3 | 1.3, 2.3, 3.4 |
| Category 3 (Technical Debt) | Axis 2 | 1.1, 2.2, 3.2 |
| Category 4 (Change) | Axis 2 | 2.1, 2.2, 2.4 |
| Category 5 (Knowledge) | Axis 3 | 3.2 |
| Category 6 (Risk) | All | All (screening) |

---

## Appendix C: Tool-to-Lens Mapping

### C.1 Complete Tool Coverage Matrix

| Tool | Primary Lens | Secondary Lens | Evidence Types |
|------|--------------|----------------|----------------|
| **NDepend / symbol-scanner** | 1.1 Architectural Boundaries | 2.1 Change Coupling | Dependency cycles, boundary violations |
| **lizard** | 2.2 Hotspot Economics | - | CCN per function (combine with churn) |
| **scc** | 2.2 Hotspot Economics | 1.4 Structural Extensibility | LOC distribution, file concentration |
| **Git history analysis** | 2.1 Change Coupling | 3.2 Knowledge Distribution | Co-change patterns, author concentration |
| **trivy** | 1.3 Runtime Topology | - | Dependency vulnerabilities, IaC misconfig |
| **gitleaks** | 3.4 Operational Discipline | - | Exposed secrets (process failure) |
| **semgrep** | 2.3 Test & Release Friction | - | Code smell patterns, anti-patterns |
| **roslyn-analyzers** | 2.3 Test & Release Friction | - | .NET-specific violations |
| **Data profiler** | 4.1-4.4 (all data lenses) | - | Completeness, correctness, reconstructability |
| **CI/CD inspection** | 2.3 Test & Release Friction | 3.4 Operational Discipline | Pipeline structure, test timing, deployment gates |
| **git-sizer** | 1.1 Architectural Boundaries | 3.4 Operational Discipline | Repository health, scale indicators |
| **layout-scanner** | 1.1 Architectural Boundaries | - | Directory structure, component boundaries |

### C.2 Evidence Generation by Tool

#### lizard -> E-CMPLX, E-DIST

```sql
-- E-CMPLX: High complexity functions
SELECT * FROM stg_lizard_function_metrics WHERE max_ccn > 15;

-- E-DIST: Complexity distribution
SELECT * FROM rollup_lizard_directory_distribution_recursive WHERE gini_ccn > 0.6;
```

#### trivy -> E-SEC

```sql
-- E-SEC: Vulnerabilities
SELECT * FROM stg_trivy_vulnerabilities WHERE severity IN ('CRITICAL', 'HIGH');

-- E-SEC: IaC misconfigs
SELECT * FROM stg_trivy_iac_misconfigs WHERE severity IN ('CRITICAL', 'HIGH');
```

#### gitleaks -> E-SEC

```sql
-- E-SEC: Exposed secrets
SELECT * FROM stg_gitleaks_secrets;
```

---

## Appendix D: IC Report Templates

### D.1 Executive Summary Template

```markdown
# Executive Summary

## Platform Assessment Matrix

| Dimension | Rating | Key Evidence |
|-----------|--------|--------------|
| Technical Viability | [GREEN/YELLOW/RED] | [1-line summary] |
| Security Posture | [GREEN/YELLOW/RED] | [1-line summary] |
| Operational Stability | [GREEN/YELLOW/RED] | [1-line summary] |
| Change Velocity | [GREEN/YELLOW/RED] | [1-line summary] |
| Knowledge Continuity | [GREEN/YELLOW/RED] | [1-line summary] |
| Remediation Cost | [HIGH/MEDIUM/LOW] | [1-line summary] |
| Rewrite Risk | [HIGH/MEDIUM/LOW] | [1-line summary] |

## Platform Decision

**Recommendation:** [EXTEND / MODERNIZE / REPLACE]

**Decision Type:** [GO / NO-GO / CONDITIONAL]

**Conditions:**
1. [Pre-close requirement 1]
2. [Pre-close requirement 2]
3. [Post-close requirement]

## Risk Summary

| Priority | Count | Top Risk |
|----------|-------|----------|
| P1 (Must Address) | X | [Top P1 risk title] |
| P2 (Should Address) | Y | [Top P2 risk title] |
| P3 (Track) | Z | - |
| P4 (Monitor) | W | - |

## Top 5 Risks

1. **[RISK-XXX]:** [Title] - [Severity] - [1-line description]
2. **[RISK-XXX]:** [Title] - [Severity] - [1-line description]
3. **[RISK-XXX]:** [Title] - [Severity] - [1-line description]
4. **[RISK-XXX]:** [Title] - [Severity] - [1-line description]
5. **[RISK-XXX]:** [Title] - [Severity] - [1-line description]

## Investment Requirements Summary

| Urgency | Count | Total Effort Range |
|---------|-------|-------------------|
| Pre-Close | X | [min-max] person-months |
| 90-Day | Y | [min-max] person-months |
| 6-Month | Z | [min-max] person-months |
| 12-Month | W | [min-max] person-months |

## Confidence Statement

This assessment is based on:
- [X] automated evidence items
- [Y] manual inspection findings
- [Z] engineer interviews
- Confidence: [HIGH/MEDIUM/LOW]
```

---

### D.2 Evidence Pack Template

```markdown
# Technical Evidence Pack

## Evidence Index

| ID | Type | Category | Location | Confidence | Hardened |
|----|------|----------|----------|------------|----------|
| E-AUTO-CMPLX-001 | code | CMPLX | src/services/OrderProcessor.cs:L147 | HIGH | Yes |
| E-AUTO-SEC-001 | vuln | SEC | pom.xml (log4j@2.14.0) | HIGH | Yes |
| E-INT-007 | interview | COUP | Interview: Tech Lead | HIGH | Yes |
| E-MAN-003 | manual | ARCH | Database: orders.* tables | MEDIUM | Yes |

## Evidence Statistics

| Category | AUTO | MAN | INT | HARD | Total |
|----------|------|-----|-----|------|-------|
| CMPLX | X | X | X | X | X |
| COUP | X | X | X | X | X |
| SEC | X | X | X | X | X |
| QUAL | X | X | X | X | X |
| DIST | X | X | X | X | X |
| KNOW | X | X | X | X | X |
| OPS | X | X | X | X | X |
| ARCH | X | X | X | X | X |
| **Total** | X | X | X | X | X |

## Evidence Details

### E-AUTO-CMPLX-001

- **Type:** code
- **Category:** CMPLX
- **Location:** src/services/OrderProcessor.cs:L147-L298
- **Excerpt:** ProcessOrder() - CCN=47, NLOC=152, params=12
- **Observation:** Function exceeds complexity threshold (CCN > 15)
- **Why It Matters:** 47 independent paths; high change risk and testing burden
- **Confidence:** HIGH
- **Source:** lizard
- **Validation:** CONFIRMED (E-INT-001)
- **Hardened:** Yes

[Continue for all evidence items...]
```

---

### D.3 Claim Register Template

```markdown
# Claim Register

## Claims by Priority

### P1 Claims (Must Address)

#### CLM-SEC-001: Critical Vulnerability Exposure

- **Statement:** Platform has 3 CRITICAL vulnerabilities requiring immediate remediation
- **Evidence:** E-AUTO-SEC-001, E-AUTO-SEC-002, E-AUTO-SEC-003
- **Implication:** Exploitation risk is high; compliance violation likely
- **Triggered By:** Security audit, penetration test, or compliance review
- **Confidence:** HIGH
- **Priority Score:** 0.92

[Continue for all claims...]

## Claim Statistics

| Category | P1 | P2 | P3 | P4 | Total |
|----------|----|----|----|----|-------|
| Security | X | X | X | X | X |
| Architectural | X | X | X | X | X |
| Complexity | X | X | X | X | X |
| Coupling | X | X | X | X | X |
| Knowledge | X | X | X | X | X |
| Quality | X | X | X | X | X |
| Operational | X | X | X | X | X |
| Distribution | X | X | X | X | X |
| **Total** | X | X | X | X | X |
```

---

### D.4 Component Inventory Template

```markdown
# Component Inventory

## Component Map

[ASCII diagram or reference to visual]

## Component Details

### OrderService (src/services/orders/)

**Metrics:**
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Total Files | 47 | - | - |
| Total LOC | 12,450 | - | - |
| Avg CCN | 14.3 | < 10 | YELLOW |
| Max CCN | 47 | < 15 | RED |
| Test Coverage | 32% | > 80% | RED |

**Dependencies:**
- Calls: PricingEngine, SupplierService, ContractService
- Called By: OrderAPI, BatchProcessor, ReportingService
- Database: orders.*, pricing.*, suppliers.*

**Complexity Hotspots:**
| File | CCN | LOC | Notes |
|------|-----|-----|-------|
| OrderProcessor.cs | 47 | 4,500 | P1 - Structural constraint |
| OrderValidator.cs | 23 | 890 | P2 - Complex validation |
| OrderMapper.cs | 18 | 560 | P3 - Mapping logic |

**Risk Signals:**
- [ ] Single author on OrderProcessor.cs (E-KNOW-001)
- [ ] 67% of module complexity in one file (E-DIST-001)
- [ ] Two failed decomposition attempts (E-INT-042)

**Interview Insights:**
> "This is where all the magic happens, for better or worse" - Tech Lead

[Continue for all components...]
```

---

### D.5 Risk Register Template

```markdown
# Risk Register

## Critical Risks

### RISK-001: Security Vulnerability Exposure

- **Severity:** CRITICAL
- **Type:** security
- **Description:** Platform has 3 CRITICAL CVEs and exposed credentials
- **Technical Cause:** Outdated dependencies; secrets committed to repository
- **Manifests In:** pom.xml, package.json, deploy.py
- **Triggered By:** Security audit, compliance review, or active attack
- **Claims:** CLM-SEC-001, CLM-SEC-002
- **Mitigation:** Upgrade dependencies; rotate credentials
- **Investment Required:** INV-001 (Pre-Close)

[Continue for all risks...]

## Risk Summary Matrix

| Risk ID | Title | Severity | Type | Addressable | Investment |
|---------|-------|----------|------|-------------|------------|
| RISK-001 | Security Exposure | CRITICAL | security | Yes | INV-001 |
| RISK-002 | Order Structural Constraint | HIGH | structural | Partial | INV-003 |
| RISK-003 | Knowledge Concentration | HIGH | knowledge | Yes | INV-002 |
| RISK-004 | Operational Fragility | MEDIUM | operational | Yes | INV-004 |
```

---

### D.6 Rewrite Risk Memo Template

```markdown
# Implicit Rewrite Risk Assessment

## Executive Summary

Based on structural analysis, **[incremental modernisation is viable with constraints / significant rewrite risk exists]**. [N] areas present significant rewrite risk if requirements change substantially.

## Where Incremental Evolution Breaks Down

### 1. [Component Name] (HIGH/MEDIUM REWRITE RISK)

**Constraint Type:** Structural (not addressable incrementally) / Addressable (with investment)

**Evidence:**
- [E-XXX-001]: [Evidence description]
- [E-XXX-002]: [Evidence description]

**Assumption That Would Fail:**
> "[Assumption statement]"

**Why It Fails:** [Explanation]

**Trigger Condition:** [What change would expose this]

[Continue for all areas...]

## Constraints Summary

| Constraint | Type | Rewrite Risk | Addressable? |
|------------|------|--------------|--------------|
| [Constraint 1] | Structural | High | No - requires rewrite |
| [Constraint 2] | Architectural | Medium | Yes - with API layer |
| [Constraint 3] | Organizational | Low | Yes - with documentation |

## Recommendation

Proceed with "[extend/modernize/replace]" strategy **with the following constraints:**

1. [Constraint 1]
2. [Constraint 2]
3. [Constraint 3]
```

---

## Appendix E: Process Checklists

### E.1 Phase 1 Checklist: Automated Facts

```markdown
## Phase 1: Automated Facts

### Setup
- [ ] Repository cloned at specified commit
- [ ] Tool environments configured
- [ ] Access and permissions verified
- [ ] Output directories created

### Tool Execution
- [ ] scc completed successfully
- [ ] lizard completed successfully
- [ ] trivy completed successfully
- [ ] gitleaks completed successfully
- [ ] semgrep completed successfully
- [ ] roslyn-analyzers completed (if .NET)
- [ ] git-sizer completed successfully
- [ ] layout-scanner completed successfully
- [ ] dbt models run successfully

### Evidence Generation
- [ ] Evidence extraction queries executed
- [ ] Thresholds applied
- [ ] E-AUTO-* items created and indexed
- [ ] Initial statistics documented

### Quality Check
- [ ] No tool execution errors unresolved
- [ ] Evidence items have required fields
- [ ] Locations are verifiable
- [ ] Risk ranking prepared for Phase 2

### Exit
- [ ] All outputs stored
- [ ] Summary statistics documented
- [ ] Ready for Phase 2
```

---

### E.2 Phase 2 Checklist: Manual Inspection

```markdown
## Phase 2: Manual + AI Code Inspection

### Preparation
- [ ] Risk-ranked file list generated
- [ ] High-priority areas identified
- [ ] Inspection scope defined

### Architecture Review
- [ ] Module boundaries assessed
- [ ] Abstraction layers reviewed
- [ ] Cross-cutting concerns identified
- [ ] Integration patterns documented

### Code Inspection
- [ ] Top CCN functions reviewed
- [ ] Single-author files assessed
- [ ] High fan-out modules traced
- [ ] Database triggers/stored procedures checked

### Infrastructure Review
- [ ] CI/CD pipelines reviewed
- [ ] Database schemas analyzed
- [ ] Environment configs reviewed
- [ ] Secrets management assessed

### Evidence Generation
- [ ] E-MAN-* items created
- [ ] Links to E-AUTO-* items added
- [ ] Confidence levels assigned
- [ ] Interview questions prepared

### Exit
- [ ] All high-risk files inspected
- [ ] Manual evidence documented
- [ ] Interview prep complete
- [ ] Ready for Phase 3
```

---

### E.3 Phase 3 Checklist: Interviews

```markdown
## Phase 3: Engineer Interviews

### Preparation
- [ ] Interview schedule confirmed
- [ ] Role-specific question sets prepared
- [ ] Findings to validate identified
- [ ] Note-taking templates ready

### Interview Execution
- [ ] Tech Lead / Architect interviewed
- [ ] Senior Developer (tenured) interviewed
- [ ] Senior Developer (newer) interviewed
- [ ] DevOps / SRE interviewed
- [ ] Recent Joiner interviewed (optional)

### Evidence Generation
- [ ] E-INT-* items created for all interviews
- [ ] Validation outcomes assigned
- [ ] Confidence markers noted
- [ ] Direct quotes captured

### Documentation
- [ ] Interview notes transcribed
- [ ] Key findings synthesized
- [ ] Contradictions noted
- [ ] New risks documented

### Exit
- [ ] Minimum 3 interviews completed
- [ ] All evidence documented
- [ ] Validation outcomes assigned
- [ ] Ready for Phase 4
```

---

### E.4 Phase 4 Checklist: Triangulation

```markdown
## Phase 4: Triangulation

### Validation Matrix
- [ ] All E-AUTO-* items mapped
- [ ] All E-MAN-* items mapped
- [ ] Interview validation outcomes assigned
- [ ] Confidence levels adjusted

### Conflict Identification
- [ ] Conflicts identified between sources
- [ ] Conflicts documented in register
- [ ] Investigation actions assigned

### Assessment
- [ ] HIGH confidence items identified
- [ ] MEDIUM confidence items flagged
- [ ] LOW confidence items investigated
- [ ] INVESTIGATE items listed

### Decision
- [ ] Conflicts requiring Phase 5 identified
- [ ] Go/No-Go for Phase 5 decided
- [ ] If no conflicts, proceed to Phase 6

### Exit
- [ ] Validation matrix complete
- [ ] Conflict register documented
- [ ] Phase 5/6 decision made
- [ ] Ready for next phase
```

---

### E.5 Phase 5 Checklist: Second Iteration

```markdown
## Phase 5: Second Iteration

### Conflict Resolution
- [ ] Additional code inspection for challenged items
- [ ] Follow-up interviews scheduled/completed
- [ ] Commit messages/PR descriptions reviewed
- [ ] External documentation checked

### Gap Filling
- [ ] Interview-only findings investigated in code
- [ ] Targeted tool queries executed
- [ ] Resolution rationale documented

### Evidence Hardening
- [ ] E-HARD-* items created
- [ ] Confidence levels finalized
- [ ] Evidence index updated
- [ ] Conflict register updated

### Exit
- [ ] All P1/P2 conflicts resolved
- [ ] High-severity items validated
- [ ] E-HARD-* items complete
- [ ] Ready for Phase 6
```

---

### E.6 Phase 6 Checklist: Claim & Decision

```markdown
## Phase 6: Claim & Decision Generation

### Claim Formulation
- [ ] Claim templates applied
- [ ] Evidence references added
- [ ] Confidence levels assigned
- [ ] Priority scores calculated
- [ ] Priority tiers assigned

### Risk Aggregation
- [ ] Related claims grouped
- [ ] Compound risks identified
- [ ] Risk severity assessed
- [ ] Risk types assigned

### Opportunity Identification
- [ ] Modernization opportunities surfaced
- [ ] Value propositions documented
- [ ] Required investments linked

### Investment Planning
- [ ] Remediation investments defined
- [ ] Urgency tiers assigned
- [ ] Effort ranges estimated
- [ ] Capex/Opex categorized

### Decision Generation
- [ ] 7 dimensions assessed
- [ ] Decision matrix applied
- [ ] Platform recommendation generated
- [ ] Conditions defined

### Report Assembly
- [ ] Executive Summary complete
- [ ] Technical Evidence Pack complete
- [ ] Claim Register complete
- [ ] Component Inventory complete
- [ ] Risk Register complete
- [ ] Rewrite Risk Memo complete
- [ ] Investment Roadmap complete
- [ ] Methodology section complete

### Quality Check
- [ ] All claims trace to evidence
- [ ] All risks have supporting claims
- [ ] All investments address risks
- [ ] All sections proofread

### Exit
- [ ] IC Report ready for delivery
- [ ] Supporting materials prepared
- [ ] Presentation ready (if required)
```

---

## Appendix F: Quick Reference

### F.1 Evidence ID Patterns

| Pattern | Example | Source |
|---------|---------|--------|
| E-AUTO-{CAT}-{SEQ} | E-AUTO-CMPLX-001 | Automated tool |
| E-MAN-{CAT}-{SEQ} | E-MAN-ARCH-001 | Manual inspection |
| E-INT-{SEQ} | E-INT-007 | Interview |
| E-HARD-{CAT}-{SEQ} | E-HARD-CMPLX-001 | Hardened evidence |
| E-{CAT}-{SEQ} | E-CMPLX-001 | General (any source) |

### F.2 Claim ID Patterns

| Pattern | Example |
|---------|---------|
| CLM-{CAT}-{SEQ} | CLM-CMPLX-001 |
| A{axis}-C-{seq} | A1-C-001 |

### F.3 Risk/Opportunity/Investment/Decision IDs

| Entity | Pattern | Example |
|--------|---------|---------|
| Risk | RISK-{SEQ} | RISK-001 |
| Opportunity | OPP-{SEQ} | OPP-001 |
| Investment | INV-{SEQ} | INV-001 |
| Decision | DEC-{SEQ} | DEC-001 |
| Roadmap Item | R-{SEQ} | R-001 |

### F.4 Validation Outcomes

| Outcome | Meaning | Action |
|---------|---------|--------|
| CONFIRMED | Sources agree | Increase confidence |
| CONTEXTUALIZED | Severity adjustment needed | Adjust per context |
| CHALLENGED | Sources disagree | Investigate further |
| EXPANDED | New finding from interview | Create new evidence |

### F.5 Confidence Levels

| Level | Criteria |
|-------|----------|
| HIGH | Multi-source validation |
| MEDIUM | Single authoritative source |
| LOW | Speculation or conflict |

### F.6 Priority Tiers

| Tier | Score | Action |
|------|-------|--------|
| P1 | 0.75-1.00 | Must Address (pre-close or 90-day) |
| P2 | 0.50-0.74 | Should Address (90-day to 6-month) |
| P3 | 0.25-0.49 | Track (backlog) |
| P4 | 0.00-0.24 | Monitor (no action) |

### F.7 Dimension Ratings

| Rating | Meaning |
|--------|---------|
| GREEN | No significant concerns |
| YELLOW | Concerns exist but addressable |
| RED | Significant concerns requiring action |

### F.8 Decision Types

| Type | Meaning |
|------|---------|
| EXTEND | Continue with current platform |
| MODERNIZE | Invest in remediation |
| REPLACE | Plan for replacement |

### F.9 Axis Decision States

| Axis | Decision States |
|------|-----------------|
| Axis 1 (Platform) | Extend / Modernise / Replace |
| Axis 2 (Change) | Low cost-of-change / High cost-of-change / Unpredictable |
| Axis 3 (Execution) | Proceed / Proceed with guardrails / Do not proceed |
| Axis 4 (Data) | Steering ready / MVP required / Steering risk disclosed |
| Axis 5 (Investment) | Invest now / Stage/tranche / Defer |

### F.10 Lens Quick Lookup

| Lens | Axis | Focus |
|------|------|-------|
| 1.1 | Axis 1 | Architectural Boundaries |
| 1.2 | Axis 1 | Data Architecture Semantics |
| 1.3 | Axis 1 | Runtime Topology |
| 1.4 | Axis 1 | Structural Extensibility |
| 2.1 | Axis 2 | Change Coupling |
| 2.2 | Axis 2 | Hotspot Economics |
| 2.3 | Axis 2 | Test & Release Friction |
| 2.4 | Axis 2 | Predictability |
| 3.1 | Axis 3 | Decision Rights |
| 3.2 | Axis 3 | Knowledge Distribution |
| 3.3 | Axis 3 | Vendor Leverage |
| 3.4 | Axis 3 | Operational Discipline |
| 4.1 | Axis 4 | Revenue Reconstructability |
| 4.2 | Axis 4 | Data Completeness |
| 4.3 | Axis 4 | Data Correctness |
| 4.4 | Axis 4 | Forward Integrity |
| 5.1 | Axis 5 | Risk Reduction Leverage |
| 5.2 | Axis 5 | Value Asymmetry |
| 5.3 | Axis 5 | Reversibility |
| 5.4 | Axis 5 | Dependency Resolution |

---

*Framework Version: 3.0*
*Last Updated: 2026-02-03*
*This document supersedes: EVIDENCE_METHODOLOGY.md, INTERVIEW_FRAMEWORK.md, DUE_DILIGENCE_PROCESS.md*
