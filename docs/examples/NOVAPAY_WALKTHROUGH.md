# Decision Framework Walkthrough: NovaPay Acquisition

**Purpose:** This document demonstrates the complete Decision Framework flow using a hypothetical technical due diligence scenario. It serves as training material for practitioners and validation that the framework is practical.

**Framework Version:** 3.0

---

## Table of Contents

1. [Scenario Overview](#1-scenario-overview)
2. [Phase 1: Simulated Tool Outputs](#2-phase-1-simulated-tool-outputs)
3. [Phase 2: Evidence Items](#3-phase-2-evidence-items)
4. [Phase 3: Lens Routing](#4-phase-3-lens-routing)
5. [Phase 4: Claims](#5-phase-4-claims)
6. [Phase 5: Axis Decisions](#6-phase-5-axis-decisions)
7. [Phase 6: Cross-Axis Constraints](#7-phase-6-cross-axis-constraints)
8. [Phase 7: Sample IC Output](#8-phase-7-sample-ic-output)
9. [Key Takeaways](#9-key-takeaways)

---

## 1. Scenario Overview

### 1.1 Target Company Profile

| Attribute | Value |
|-----------|-------|
| **Company** | NovaPay |
| **Business** | B2B payments platform |
| **Primary Function** | Payment processing and settlement for enterprise clients |
| **Codebase Age** | 8 years |
| **Primary Technology** | .NET/C# |
| **Total LOC** | ~400K across 3 repositories |
| **Team Size** | 12 engineers |
| **Architecture** | Single monolith with emerging microservices |
| **Transaction Volume** | ~$50M/month |

### 1.2 Investment Context

| Attribute | Value |
|-----------|-------|
| **Acquirer** | Private equity firm |
| **Deal Type** | Platform acquisition |
| **Investment Thesis** | Expand into new markets by onboarding additional payment providers |
| **Key Growth Vector** | Provider ecosystem expansion |
| **Timeline Pressure** | IC meeting in 4 weeks |

### 1.3 Critical IC Questions

The IC will need to decide:

1. **Platform Fitness:** Can the current platform support 5-10 new payment providers without structural changes?
2. **Execution Risk:** Can the existing team execute a growth roadmap under PE constraints?
3. **Cost-of-Change:** What will it cost to make changes, and how predictable are those costs?
4. **Data Integrity:** Can management reliably track revenue by provider post-close?
5. **Investment Sequencing:** Where should capital be deployed first?

---

## 2. Phase 1: Simulated Tool Outputs

The following findings represent outputs from automated analysis tools run against the NovaPay codebase.

### 2.1 Tool Findings Summary

| Tool | Finding | Location | Raw Value |
|------|---------|----------|-----------|
| **lizard** | Extreme complexity function | `PaymentProcessor.cs:ProcessTransaction()` | CCN=52, 3,200 LOC |
| **lizard** | High complexity cluster | `Providers.Integration/` | 7 functions with CCN > 25 |
| **symbol-scanner** | Cross-module coupling | `Payments.Core` ↔ `Providers.Integration` | 89 direct calls |
| **symbol-scanner** | High fan-in class | `TransactionState.cs` | Fan-in = 147 |
| **trivy** | Critical CVE in payment SDK | `Stripe.NET@4.2.0` | CVE-2024-1234 (CRITICAL) |
| **trivy** | Critical CVE in payment SDK | `Adyen.SDK@3.1.0` | CVE-2024-5678 (CRITICAL) |
| **git-blame** | Knowledge concentration | `Providers/*` | Alice: 78% of commits over 3 years |
| **git-blame** | Single author on critical file | `PaymentProcessor.cs` | Bob: 94% of commits |
| **gitleaks** | Exposed AWS credential | `deploy/staging.config:42` | AWS_SECRET_ACCESS_KEY |
| **scc** | LOC concentration | `Payments.Core/` | 67% of total LOC in one directory |
| **layout-scanner** | Missing test directories | `Providers.Integration/` | 0 test files |
| **semgrep** | Anti-pattern density | `PaymentProcessor.cs` | 23 "switch-statement-smell" matches |

### 2.2 Interview Findings Summary

| Role | Key Finding | Category |
|------|-------------|----------|
| **Tech Lead (Marcus)** | "Adding a new provider takes 3-4 weeks and touches everything" | Change Coupling |
| **Tech Lead (Marcus)** | "Alice built the provider layer; she's the only one who really understands it" | Knowledge |
| **Senior Dev (Alice)** | "The PaymentProcessor grew organically; nobody wants to touch it" | Complexity |
| **Senior Dev (Alice)** | "We've had two failed attempts to decompose it" | Architectural |
| **DevOps (Chen)** | "Rollbacks are manual and take 4+ hours" | Operational |
| **DevOps (Chen)** | "We rotate credentials quarterly but staging was missed last cycle" | Security |
| **Recent Hire (Jordan)** | "It took me 3 months to make my first meaningful commit" | Knowledge |

---

## 3. Phase 2: Evidence Items

Each tool finding and interview observation is converted into a structured evidence item following the template from DECISION_FRAMEWORK.md §2.3.

### 3.1 Complexity Evidence

#### E-CMPLX-001

```
Evidence ID: E-CMPLX-001
Source Type: Tool
Source Detail: lizard v1.17.10, novapay-core@abc123, 2026-01-15
Anchor: src/Payments.Core/PaymentProcessor.cs:ProcessTransaction():L147-L3347
Observation: ProcessTransaction() function has CCN=52 and 3,200 NLOC with 14 parameters
Scope: Local (single function)
Reliability: High
Validity Period: Until commit changes to this file
Notes: Function handles all transaction types (card, ACH, wire) in single method
```

**Why This Passes Evidence Admission:**
- ✓ Anchored to specific file, function, and line range
- ✓ Observation is factual (CCN=52, LOC=3200)
- ✓ No interpretation of "good" or "bad"
- ✓ Reproducible via tool rerun

---

#### E-CMPLX-002

```
Evidence ID: E-CMPLX-002
Source Type: Tool
Source Detail: lizard v1.17.10, novapay-core@abc123, 2026-01-15
Anchor: src/Providers.Integration/
Observation: 7 functions in Providers.Integration directory have CCN > 25; average CCN for directory is 18.3
Scope: Cross-module
Reliability: High
Validity Period: Until commit changes to this directory
Notes: All 7 functions are provider-specific transaction handlers
```

---

### 3.2 Coupling Evidence

#### E-COUP-001

```
Evidence ID: E-COUP-001
Source Type: Tool
Source Detail: symbol-scanner v2.1.0, novapay-core@abc123, 2026-01-15
Anchor: Payments.Core <-> Providers.Integration
Observation: 89 direct function calls from Payments.Core to Providers.Integration; 34 calls in reverse direction
Scope: Systemic
Reliability: High
Validity Period: Until architectural changes
Notes: Bidirectional coupling between payment processing and provider integration
```

---

#### E-COUP-002

```
Evidence ID: E-COUP-002
Source Type: Tool
Source Detail: symbol-scanner v2.1.0, novapay-core@abc123, 2026-01-15
Anchor: src/Payments.Core/Models/TransactionState.cs
Observation: TransactionState class has fan-in=147 (referenced by 147 distinct callers across all modules)
Scope: Systemic
Reliability: High
Validity Period: Until class refactored
Notes: Class serves as shared state object across entire payment flow
```

---

#### E-COUP-003

```
Evidence ID: E-COUP-003
Source Type: Interview
Source Detail: Tech Lead (Marcus), 2026-01-18
Anchor: Provider onboarding process
Observation: "Adding a new payment provider requires changes to PaymentProcessor, TransactionState, and at least 4 provider-specific files. Last three provider additions each touched 20+ files."
Scope: Systemic
Reliability: Medium (firsthand)
Validity Period: 30 days
Notes: Directly confirms coupling visible in E-COUP-001, E-COUP-002
```

---

### 3.3 Security Evidence

#### E-SEC-001

```
Evidence ID: E-SEC-001
Source Type: Tool
Source Detail: trivy v0.48.0, novapay-core@abc123, 2026-01-15
Anchor: packages.config (Stripe.NET@4.2.0)
Observation: Stripe.NET version 4.2.0 has CRITICAL severity CVE-2024-1234 (authentication bypass in webhook validation)
Scope: Systemic
Reliability: High
Validity Period: Until dependency upgraded
Notes: This SDK processes all Stripe webhook callbacks for payment confirmation
```

---

#### E-SEC-002

```
Evidence ID: E-SEC-002
Source Type: Tool
Source Detail: trivy v0.48.0, novapay-core@abc123, 2026-01-15
Anchor: packages.config (Adyen.SDK@3.1.0)
Observation: Adyen.SDK version 3.1.0 has CRITICAL severity CVE-2024-5678 (signature validation bypass)
Scope: Systemic
Reliability: High
Validity Period: Until dependency upgraded
Notes: Adyen is second-largest provider by transaction volume
```

---

#### E-SEC-003

```
Evidence ID: E-SEC-003
Source Type: Tool
Source Detail: gitleaks v8.18.0, novapay-core@abc123, 2026-01-15
Anchor: deploy/staging.config:42
Observation: AWS_SECRET_ACCESS_KEY credential exposed in committed configuration file
Scope: Local
Reliability: High
Validity Period: Until credential rotated and file cleaned
Notes: Staging environment credential; production uses different mechanism
```

---

#### E-SEC-004

```
Evidence ID: E-SEC-004
Source Type: Interview
Source Detail: DevOps Engineer (Chen), 2026-01-19
Anchor: Credential rotation process
Observation: "Credentials are rotated quarterly. The staging config in E-SEC-003 was missed in Q4 rotation. It's a known issue but hasn't been prioritized."
Scope: Local
Reliability: Medium (firsthand)
Validity Period: 30 days
Notes: Confirms E-SEC-003 is known but unaddressed; provides process context
```

---

### 3.4 Knowledge Evidence

#### E-KNOW-001

```
Evidence ID: E-KNOW-001
Source Type: Tool
Source Detail: git-blame analysis, novapay-core@abc123, 2026-01-15
Anchor: src/Providers.Integration/*
Observation: Alice authored 78% of commits (312/400) to Providers.Integration directory over 3-year period (2023-2026)
Scope: Cross-module
Reliability: High
Validity Period: Until new contributors join
Notes: Second highest contributor has only 8% of commits
```

---

#### E-KNOW-002

```
Evidence ID: E-KNOW-002
Source Type: Tool
Source Detail: git-blame analysis, novapay-core@abc123, 2026-01-15
Anchor: src/Payments.Core/PaymentProcessor.cs
Observation: Bob authored 94% of commits (156/166) to PaymentProcessor.cs since file creation (2018)
Scope: Local
Reliability: High
Validity Period: Until new contributors
Notes: Third-largest file by LOC with single dominant author
```

---

#### E-KNOW-003

```
Evidence ID: E-KNOW-003
Source Type: Interview
Source Detail: Tech Lead (Marcus), 2026-01-18
Anchor: Provider integration knowledge
Observation: "Alice built the provider integration layer. She's the only one who really understands how the routing logic works. When she's out, we avoid provider-related changes."
Scope: Cross-module
Reliability: Medium (firsthand)
Validity Period: 30 days
Notes: Directly confirms E-KNOW-001 represents real knowledge risk, not just commit history
```

---

#### E-KNOW-004

```
Evidence ID: E-KNOW-004
Source Type: Interview
Source Detail: Recent Hire (Jordan), 2026-01-19
Anchor: Onboarding experience
Observation: "It took me 3 months to make my first meaningful commit. The PaymentProcessor is a black box - I still don't fully understand it after 8 months."
Scope: Systemic
Reliability: Medium (firsthand)
Validity Period: 30 days
Notes: Indicates high barrier to entry; knowledge not transferring
```

---

### 3.5 Architectural Evidence

#### E-ARCH-001

```
Evidence ID: E-ARCH-001
Source Type: Interview
Source Detail: Senior Developer (Alice), 2026-01-18
Anchor: PaymentProcessor decomposition attempts
Observation: "We've had two failed attempts to decompose PaymentProcessor - once in 2023 and again in 2024. Both times we couldn't untangle the transaction state without breaking provider integrations."
Scope: Systemic
Reliability: Medium (firsthand)
Validity Period: 30 days
Notes: Documents historical attempts; explains current structure as intentional (after failed alternatives)
```

---

#### E-ARCH-002

```
Evidence ID: E-ARCH-002
Source Type: Code Inspection
Source Detail: Manual review, 2026-01-17
Anchor: src/Payments.Core/PaymentProcessor.cs:L147-L3347
Observation: ProcessTransaction() contains 23 switch statements dispatching on provider type, transaction type, and payment method combinations. Each new provider requires additions to 12+ switch statements.
Scope: Systemic
Reliability: High
Validity Period: 14 days
Notes: Confirms structural limit to adding new providers incrementally
```

---

### 3.6 Operational Evidence

#### E-OPS-001

```
Evidence ID: E-OPS-001
Source Type: Interview
Source Detail: DevOps Engineer (Chen), 2026-01-19
Anchor: Deployment and rollback process
Observation: "Rollbacks are manual and take 4+ hours. We have a runbook but it requires database state restoration. Last rollback was 3 weeks ago after a provider update broke settlements."
Scope: Systemic
Reliability: Medium (firsthand)
Validity Period: 30 days
Notes: High recovery time indicates operational risk during changes
```

---

#### E-OPS-002

```
Evidence ID: E-OPS-002
Source Type: Tool
Source Detail: layout-scanner v1.0.0, novapay-core@abc123, 2026-01-15
Anchor: src/Providers.Integration/
Observation: Providers.Integration directory contains 0 test files; no *Test.cs, *Tests.cs, or tests/ subdirectory found
Scope: Cross-module
Reliability: High
Validity Period: Until tests added
Notes: Provider integration layer has no automated test coverage visible in repository
```

---

### 3.7 Distribution Evidence

#### E-DIST-001

```
Evidence ID: E-DIST-001
Source Type: Tool
Source Detail: scc + rollup analysis, novapay-core@abc123, 2026-01-15
Anchor: Repository structure
Observation: Payments.Core directory contains 67% of total repository LOC (268K of 400K); Gini coefficient for LOC distribution across directories is 0.81
Scope: Systemic
Reliability: High
Validity Period: Until structural changes
Notes: Extreme concentration indicates monolithic structure
```

---

## 4. Phase 3: Lens Routing

Each evidence item is routed through the appropriate lens to determine claim eligibility. This section demonstrates the lens selection process.

### 4.1 Lens Routing Summary

| Evidence ID | Primary Axis | Primary Lens | Secondary Lens | Admissible? |
|-------------|--------------|--------------|----------------|-------------|
| E-CMPLX-001 | Axis 2 | 2.2 Hotspot Economics | - | Yes |
| E-CMPLX-002 | Axis 2 | 2.2 Hotspot Economics | - | Yes |
| E-COUP-001 | Axis 1 | 1.1 Architectural Boundaries | 2.1 Change Coupling | Yes |
| E-COUP-002 | Axis 1 | 1.1 Architectural Boundaries | - | Yes |
| E-COUP-003 | Axis 2 | 2.1 Change Coupling | - | Yes |
| E-SEC-001 | Axis 1 | 1.3 Runtime Topology | - | Yes |
| E-SEC-002 | Axis 1 | 1.3 Runtime Topology | - | Yes |
| E-SEC-003 | Axis 3 | 3.4 Operational Discipline | - | Yes |
| E-SEC-004 | Axis 3 | 3.4 Operational Discipline | - | Yes |
| E-KNOW-001 | Axis 3 | 3.2 Knowledge Distribution | - | Yes |
| E-KNOW-002 | Axis 3 | 3.2 Knowledge Distribution | - | Yes |
| E-KNOW-003 | Axis 3 | 3.2 Knowledge Distribution | - | Yes |
| E-KNOW-004 | Axis 3 | 3.2 Knowledge Distribution | - | Yes |
| E-ARCH-001 | Axis 1 | 1.4 Structural Extensibility | - | Yes |
| E-ARCH-002 | Axis 1 | 1.4 Structural Extensibility | - | Yes |
| E-OPS-001 | Axis 3 | 3.4 Operational Discipline | 2.3 Test & Release Friction | Yes |
| E-OPS-002 | Axis 2 | 2.3 Test & Release Friction | - | Yes |
| E-DIST-001 | Axis 2 | 2.2 Hotspot Economics | 1.1 Architectural Boundaries | Yes |

---

### 4.2 Lens Selection Demonstrations

#### Example 1: E-CMPLX-001 (PaymentProcessor complexity)

**Evidence:** `ProcessTransaction() has CCN=52 and 3,200 NLOC`

**Lens Selection Process:**

1. **What does this evidence speak to?**
   - High complexity in a single function
   - This affects *cost-of-change* because high complexity = high change risk

2. **Which axis?**
   - Not Axis 1 (complexity alone doesn't determine platform fitness)
   - **Axis 2 (Changeability & Cost-of-Change)** - complexity directly impacts change cost
   - Not Axis 3 (not about governance or knowledge)

3. **Which lens?**
   - Lens 2.1 (Change Coupling)? No - evidence doesn't show co-change patterns
   - **Lens 2.2 (Hotspot Economics)** - Yes, complexity metric that creates change cost
   - Lens 2.3 (Test & Release Friction)? No - doesn't reference feedback latency

4. **Admissibility check for Lens 2.2:**
   - ✓ Combines complexity (CCN=52)
   - ⚠ Missing change frequency - will need churn data for full hotspot analysis
   - Still admissible as partial evidence

**Routed to:** Axis 2, Lens 2.2

---

#### Example 2: E-COUP-001 (Cross-module calls)

**Evidence:** `89 direct calls from Payments.Core to Providers.Integration; 34 in reverse`

**Lens Selection Process:**

1. **What does this evidence speak to?**
   - Bidirectional coupling between major modules
   - This affects *architectural boundaries* - modules are not independent

2. **Which axis?**
   - **Axis 1 (Structural Platform Fitness)** - coupling determines whether modules can evolve independently
   - Also relevant to Axis 2 - coupling creates change amplification

3. **Which lens?**
   - **Lens 1.1 (Architectural Boundaries)** - Primary, shows boundary violations
   - Lens 2.1 (Change Coupling) - Secondary, explains why changes propagate

4. **Admissibility check for Lens 1.1:**
   - ✓ References specific module/package boundaries
   - ✓ Shows cross-boundary interactions (call counts)
   - ✓ Not a general quality complaint

**Routed to:** Axis 1, Lens 1.1 (primary); Axis 2, Lens 2.1 (secondary)

---

#### Example 3: E-SEC-003 (Exposed AWS key)

**Evidence:** `AWS_SECRET_ACCESS_KEY credential exposed in deploy/staging.config`

**Lens Selection Process:**

1. **What does this evidence speak to?**
   - Security vulnerability (exposed credential)
   - But also: *process failure* - credentials should never be committed

2. **Which axis?**
   - Axis 1 (Runtime Topology)? Partially - it's a security issue
   - **Axis 3 (Execution & Delivery Control)** - More precisely, this shows operational discipline failure

3. **Why Axis 3 over Axis 1?**
   - The credential exposure is a *process failure*, not a *runtime topology* issue
   - The tool-to-lens mapping (DECISION_FRAMEWORK.md Appendix C) routes gitleaks → Lens 3.4
   - This tells us more about how the organization operates than about the runtime architecture

4. **Admissibility check for Lens 3.4:**
   - ✓ Shows release control failure (credential committed)
   - ✓ References incident management pattern (quarterly rotation missed)

**Routed to:** Axis 3, Lens 3.4

---

### 4.3 Rejection Examples

The following hypothetical evidence items would be **rejected** at the lens routing stage:

#### Rejected Example 1: "The architecture is messy"

```
Evidence ID: [REJECTED]
Source Type: Interview
Observation: "The architecture is messy and hard to work with"
```

**Rejection Reason:** Cannot be anchored to concrete artefact; uses subjective language without operationalization.

**Fix:** Ask follow-up: "What specifically is messy? Which modules? What happens when you try to change them?"

---

#### Rejected Example 2: "The code is complex and Alice is the only one who knows it"

```
Evidence ID: [REJECTED]
Source Type: Interview
Observation: "The code is complex and Alice is the only one who knows it"
```

**Rejection Reason:** Mixes multiple decision dimensions (Axis 2 complexity + Axis 3 knowledge).

**Fix:** Split into two evidence items:
- E-CMPLX-X: Specific complexity metrics for specific code
- E-KNOW-X: Alice's exclusive knowledge of specific area

---

#### Rejected Example 3: "We should refactor the PaymentProcessor"

```
Evidence ID: [REJECTED]
Source Type: Interview
Observation: "We should refactor the PaymentProcessor"
```

**Rejection Reason:** Implies a decision or recommendation.

**Fix:** Capture the underlying observation: "Interviewee stated that PaymentProcessor changes frequently cause unintended side effects in settlement logic."

---

## 5. Phase 4: Claims

Evidence items are synthesized into falsifiable claims. Each claim is axis-specific, references supporting evidence, and includes confidence calculation.

### 5.1 Claim: CLM-CMPLX-001

```
Claim ID: CLM-CMPLX-001
Axis: 2 (Changeability & Cost-of-Change)
Lens: 2.2 Hotspot Economics

Claim Statement: PaymentProcessor.ProcessTransaction() is a complexity hotspot with
CCN=52 and 3,200 LOC. Changes to payment processing logic carry high defect risk
and require extensive manual testing due to 52 independent execution paths.

Decision Relevance: Axis 2 decision on cost-of-change; impacts Axis 5 investment
sequencing for refactoring work.

Supporting Evidence IDs:
  - E-CMPLX-001 (CCN=52, LOC=3200)
  - E-ARCH-002 (23 switch statements)
  - E-KNOW-002 (single author = limited review)

Confidence: HIGH
  - Evidence count: 3
  - Reliability profile: 2 High, 1 High
  - Source types: 2 types (Tool, Code Inspection)
  - Corroboration: Full (tool + inspection agree)

Claim Reversibility: Medium
  - If wrong: Bounded refactoring effort to simplify
  - Not catastrophic if we overestimate complexity

If Unaddressed: Payment processing changes will continue to be high-risk,
slow, and error-prone. Each new provider integration amplifies this burden.

Falsification Condition: Claim is false if ProcessTransaction can be modified
with confidence in <2 days with no regression bugs. Test with actual change attempt.
```

**Falsifiability Checklist:**
- [x] OBSERVABLE: References specific CCN=52, LOC=3200
- [x] SPECIFIC: Scope limited to ProcessTransaction() function
- [x] TESTABLE: Can measure change time and defect rate
- [x] OBJECTIVE: Uses numeric metrics
- [x] DISPROOF DEFINED: States what would falsify (2-day confident change)

---

### 5.2 Claim: CLM-COUP-001

```
Claim ID: CLM-COUP-001
Axis: 1 (Structural Platform Fitness)
Lens: 1.1 Architectural Boundaries

Claim Statement: Payments.Core and Providers.Integration have no meaningful
architectural boundary. Bidirectional coupling (89 calls outbound, 34 calls
inbound) prevents independent evolution of payment processing and provider
integration domains.

Decision Relevance: Platform fitness decision (Extend vs. Modernize). Provider
expansion cannot proceed without addressing this coupling.

Supporting Evidence IDs:
  - E-COUP-001 (89 + 34 cross-boundary calls)
  - E-COUP-002 (TransactionState fan-in=147)
  - E-COUP-003 (interview: "touches everything")

Confidence: HIGH
  - Evidence count: 3
  - Reliability profile: 2 High, 1 Medium
  - Source types: 2 types (Tool, Interview)
  - Corroboration: Full (tool + interview agree)

Claim Reversibility: Hard
  - Architectural decision based on this claim is expensive to reverse
  - If wrong: We may invest in decoupling that wasn't necessary

If Unaddressed: Each new provider addition will require coordinated changes
across both domains. Change amplification will increase as provider count grows.

Falsification Condition: Claim is false if a new provider can be added by
modifying only files in Providers.Integration/ without touching Payments.Core/.
```

---

### 5.3 Claim: CLM-SEC-001

```
Claim ID: CLM-SEC-001
Axis: 1 (Structural Platform Fitness)
Lens: 1.3 Runtime Topology

Claim Statement: The platform has 2 CRITICAL severity vulnerabilities in
payment SDK dependencies (Stripe.NET CVE-2024-1234, Adyen.SDK CVE-2024-5678)
that expose webhook validation and signature verification to bypass attacks.

Decision Relevance: Pre-close remediation requirement. Cannot proceed with
acquisition until these are addressed.

Supporting Evidence IDs:
  - E-SEC-001 (Stripe CVE)
  - E-SEC-002 (Adyen CVE)

Confidence: HIGH
  - Evidence count: 2
  - Reliability profile: 2 High
  - Source types: 1 type (Tool)
  - Corroboration: N/A (CVEs are binary facts)

Claim Reversibility: Easy
  - Claim is technical fact; reversibility is about remediation
  - Remediation = dependency upgrade; reversible if issues arise

If Unaddressed: Platform is vulnerable to payment fraud via webhook/signature
bypass. Compliance violation likely upon audit.

Falsification Condition: Claim is false if CVE records are invalid or
dependencies are not actually in production code paths.
```

---

### 5.4 Claim: CLM-KNOW-001

```
Claim ID: CLM-KNOW-001
Axis: 3 (Execution System & Delivery Control)
Lens: 3.2 Knowledge Distribution

Claim Statement: The Providers.Integration module has bus factor = 1. Alice
has authored 78% of commits over 3 years and is the only team member who
understands the provider routing logic. Alice's departure would halt provider-
related development.

Decision Relevance: Execution risk assessment. Guardrails required around
knowledge transfer before aggressive provider expansion.

Supporting Evidence IDs:
  - E-KNOW-001 (78% commits)
  - E-KNOW-003 (interview: "only one who understands")
  - E-KNOW-004 (new hire: 3 months to first commit)

Confidence: HIGH
  - Evidence count: 3
  - Reliability profile: 1 High, 2 Medium
  - Source types: 2 types (Tool, Interview)
  - Corroboration: Full (git data + multiple interviews agree)

Claim Reversibility: Medium
  - Knowledge concentration can be addressed with documentation + pair programming
  - Not immediately reversible but bounded investment

If Unaddressed: Provider expansion roadmap has single-person dependency.
Vacation, departure, or illness creates immediate roadblock.

Falsification Condition: Claim is false if another team member can successfully
add a new provider without Alice's involvement or consultation.
```

---

### 5.5 Claim: CLM-KNOW-002

```
Claim ID: CLM-KNOW-002
Axis: 3 (Execution System & Delivery Control)
Lens: 3.2 Knowledge Distribution

Claim Statement: PaymentProcessor.cs has bus factor = 1. Bob has authored 94%
of commits. Combined with complexity (CCN=52), this creates critical-path
dependency on Bob for any payment processing changes.

Decision Relevance: Execution risk; informs guardrail requirements.

Supporting Evidence IDs:
  - E-KNOW-002 (94% commits)
  - E-CMPLX-001 (CCN=52)
  - E-ARCH-001 (two failed decomposition attempts)

Confidence: HIGH
  - Evidence count: 3
  - Reliability profile: 2 High, 1 Medium
  - Source types: 2 types (Tool, Interview)
  - Corroboration: Full

Claim Reversibility: Medium

If Unaddressed: Core payment processing has single-person dependency for a
3,200 LOC file that nobody else understands.

Falsification Condition: Claim is false if another developer can successfully
modify ProcessTransaction() without Bob's review or consultation.
```

---

### 5.6 Claim: CLM-OPS-001

```
Claim ID: CLM-OPS-001
Axis: 3 (Execution System & Delivery Control)
Lens: 3.4 Operational Discipline

Claim Statement: Deployment rollback capability is inadequate. Rollbacks are
manual, require database state restoration, and take 4+ hours. This creates
unacceptable blast radius for rapid iteration.

Decision Relevance: Execution guardrails required; impacts Axis 2 cost-of-change.

Supporting Evidence IDs:
  - E-OPS-001 (4+ hour rollbacks)
  - E-OPS-002 (no test coverage in Providers.Integration)

Confidence: MEDIUM
  - Evidence count: 2
  - Reliability profile: 1 Medium, 1 High
  - Source types: 2 types (Interview, Tool)
  - Corroboration: Partial

Claim Reversibility: Easy
  - Rollback process can be improved with investment
  - Not architectural constraint

If Unaddressed: Each deployment carries multi-hour recovery risk. Team will
be conservative with changes, slowing velocity.

Falsification Condition: Claim is false if rollback can be completed in <30
minutes with documented, tested procedure.
```

---

### 5.7 Claim: CLM-ARCH-001

```
Claim ID: CLM-ARCH-001
Axis: 1 (Structural Platform Fitness)
Lens: 1.4 Structural Extensibility

Claim Statement: Adding a new payment provider requires modifying 12+ switch
statements in PaymentProcessor.cs. The platform cannot extend provider
support without touching core payment processing logic. Two previous
decomposition attempts have failed.

Decision Relevance: Platform direction (Modernize required). Cannot safely
extend without addressing extensibility.

Supporting Evidence IDs:
  - E-ARCH-002 (23 switch statements, 12+ require changes)
  - E-ARCH-001 (two failed decomposition attempts)
  - E-COUP-003 ("adding provider touches everything")

Confidence: HIGH
  - Evidence count: 3
  - Reliability profile: 1 High, 2 Medium
  - Source types: 3 types (Code, Interview)
  - Corroboration: Full

Claim Reversibility: Hard
  - Structural extensibility requires significant refactoring to improve
  - Investment decision based on this is consequential

If Unaddressed: Provider expansion will continue to require changes to
monolithic PaymentProcessor. Risk increases with each addition.

Falsification Condition: Claim is false if a new provider can be added by
creating only new files (strategy/plugin pattern) without modifying
PaymentProcessor.cs.
```

---

## 6. Phase 5: Axis Decisions

Each axis synthesizes its claims into a decision state using the framework's defined decision states.

### 6.1 Axis 3 Decision (Evaluated FIRST per protocol)

**Axis:** Execution System & Delivery Control

**IC Question:** Can the organisation reliably execute a non-trivial roadmap under PE constraints?

#### Claims Considered

| Claim ID | Statement Summary | Confidence |
|----------|-------------------|------------|
| CLM-KNOW-001 | Provider integration has bus factor = 1 (Alice) | HIGH |
| CLM-KNOW-002 | PaymentProcessor has bus factor = 1 (Bob) | HIGH |
| CLM-OPS-001 | Rollbacks take 4+ hours, inadequate capability | MEDIUM |
| (E-SEC-003/004) | Credential rotation process has gaps | MEDIUM |

#### Decision

```
Axis 3 Decision: PROCEED WITH GUARDRAILS

Rationalisation: The organisation can execute but has critical single-person
dependencies and operational gaps that create execution risk. These are
addressable with defined guardrails and investment, not fundamental blockers.

Guardrails Required:
1. Knowledge transfer program for Alice (Providers) and Bob (PaymentProcessor)
2. Pair programming mandate for critical paths
3. Rollback automation investment within 90 days
4. Credential rotation audit within 30 days

Enables: Provider expansion roadmap can proceed
Blocks: Aggressive timeline without knowledge distribution first

If Wrong: We may underestimate execution risk and hit velocity wall when
key personnel are unavailable. Trigger: First instance of blocked work due
to knowledge concentration.
```

**Decision State:** `Proceed with guardrails`

---

### 6.2 Axis 1 Decision (Evaluated SECOND)

**Axis:** Structural Platform Fitness

**IC Question:** Is the current platform structurally fit to support the investment thesis (provider expansion)?

#### Claims Considered

| Claim ID | Statement Summary | Confidence |
|----------|-------------------|------------|
| CLM-COUP-001 | Payments.Core and Providers.Integration have no meaningful boundary | HIGH |
| CLM-SEC-001 | 2 CRITICAL CVEs in payment SDKs | HIGH |
| CLM-ARCH-001 | Adding providers requires 12+ switch statement modifications | HIGH |

#### Decision

```
Axis 1 Decision: MODERNISE

Rationalisation: The platform has structural constraints that prevent safe
extension. Bidirectional coupling between payment processing and provider
integration creates change amplification. The switch-statement-based
extensibility model has reached its limits after 8 years and 2 failed
refactoring attempts. However, the platform is not broken - it processes
$50M/month reliably. Replacement is not justified; targeted modernisation is.

Modernisation Scope:
1. Decouple Payments.Core from Providers.Integration
2. Introduce provider strategy pattern to eliminate switch statements
3. Remediate CRITICAL CVEs (pre-close)

Enables: Sustainable provider expansion (5-10 new providers)
Blocks: Rapid provider onboarding without architectural investment

If Wrong: We may invest in modernisation that wasn't necessary, or
underestimate the effort required. Trigger: Modernisation effort exceeds
12 person-months without measurable decoupling.
```

**Decision State:** `Modernise`

---

### 6.3 Axis 2 Decision (Evaluated in PARALLEL with Axis 4)

**Axis:** Changeability & Cost-of-Change

**IC Question:** How expensive, risky, and predictable is incremental change?

#### Claims Considered

| Claim ID | Statement Summary | Confidence |
|----------|-------------------|------------|
| CLM-CMPLX-001 | PaymentProcessor has CCN=52, high defect risk | HIGH |
| CLM-COUP-001 | Changes propagate across module boundaries | HIGH |
| CLM-OPS-001 | No test coverage in Providers.Integration | MEDIUM |

#### Decision

```
Axis 2 Decision: HIGH COST-OF-CHANGE

Rationalisation: Change cost is high due to:
- Complexity hotspot in core payment processing (CCN=52)
- Change amplification from bidirectional coupling
- No automated test coverage in provider integration layer
- 4+ hour rollback time creates risk aversion

This is consistent with interview data: "Adding a provider takes 3-4 weeks
and touches everything."

Impact on Roadmap:
- Budget 3-4 weeks per provider addition (not 1-2)
- Include buffer for defect resolution
- Sequence modernisation work before aggressive expansion

Enables: Realistic planning for provider expansion
Blocks: Aggressive timeline assumptions

If Wrong: We may be overly conservative in roadmap. Trigger: First provider
addition completes in <2 weeks with no regressions.
```

**Decision State:** `High cost-of-change`

---

### 6.4 Axis 4 Decision (Evaluated in PARALLEL with Axis 2)

**Axis:** Data Integrity & Steering Readiness

**IC Question:** Can management reliably steer the business post-close?

#### Claims Considered

*Note: Our simulated evidence set did not include data integrity findings. In a real engagement, data inspection would generate E-DATA-* evidence items.*

For this walkthrough, assume:
- Revenue is reconstructable by provider
- Transaction data is complete
- No data correctness issues identified
- Forward integrity mechanisms exist (audit tables)

#### Decision

```
Axis 4 Decision: STEERING READY

Rationalisation: Data inspection did not reveal material gaps in revenue
reconstructability, completeness, or correctness. Management can reliably
track revenue by provider. Forward integrity mechanisms exist.

Note: This decision is based on limited evidence. A full engagement would
include deeper data profiling.

Enables: Post-close steering and provider-level P&L tracking
Blocks: Nothing

If Wrong: Management discovers they cannot reliably attribute revenue
post-close. Trigger: Finance flags discrepancies in first quarterly close.
```

**Decision State:** `Steering ready`

---

### 6.5 Axis 5 Decision (Evaluated LAST)

**Axis:** Investment Leverage & Sequencing

**IC Question:** Where does capital most effectively reduce risk or unlock value?

#### Claims Feeding Investment Decisions

| From Axis | Input | Investment Implication |
|-----------|-------|------------------------|
| Axis 1 | Modernise decision | Decoupling investment required |
| Axis 1 | CRITICAL CVEs | Pre-close security remediation |
| Axis 2 | High cost-of-change | Complexity reduction investment |
| Axis 3 | Knowledge concentration | Knowledge transfer investment |
| Axis 3 | Rollback inadequacy | DevOps investment |

#### Decision

```
Axis 5 Decision: STAGE / TRANCHE

Rationalisation: Multiple investments required with dependencies. Staging
allows risk management and learning.

Investment Sequence:
TRANCHE 1 (Pre-Close / 90 Days):
  - INV-001: Security remediation (CRITICAL CVEs) - 2 PM
  - INV-002: Knowledge transfer program kickoff - 1 PM
  - INV-003: Credential rotation audit - 0.5 PM

TRANCHE 2 (Months 3-9):
  - INV-004: PaymentProcessor refactoring - 6-9 PM
  - INV-005: Provider interface extraction - 4-6 PM
  - INV-006: Rollback automation - 2 PM

TRANCHE 3 (Months 9-12):
  - INV-007: First new provider onboarding (test of improvements)
  - INV-008: Provider #2-5 (if Tranche 2 succeeds)

Risk Reduction Leverage:
- INV-001 addresses immediate security exposure (P1)
- INV-002 reduces bus factor risk (P1)
- INV-004+005 enable sustainable provider expansion (thesis enablement)

Value Asymmetry:
- Provider expansion unlocks $5-10M ARR potential
- Investment required: ~$1.5M (15 PM at $100K loaded)
- Leverage ratio: 5-7x

Enables: Phased provider expansion with risk management
Blocks: Simultaneous parallel tracks

If Wrong: Tranched approach may be too conservative. Trigger: Tranche 1
completes 50% under budget with no issues.
```

**Decision State:** `Stage / tranche`

---

## 7. Phase 6: Cross-Axis Constraints

Apply the constraint matrix from DECISION_FRAMEWORK.md §6 to verify decisions are consistent.

### 7.1 Constraint Matrix Application

```
FROM v / TO ->    | Axis 1 | Axis 2 | Axis 3 | Axis 4 | Axis 5 |
------------------+--------+--------+--------+--------+--------+
Axis 1 (Platform) |   -    |CONSTRAINS|   -   |   -    |REQUIRES|
Axis 2 (Change)   |   -    |   -    |   -    |   -    |CONSTRAINS|
Axis 3 (Execution)| BLOCKS | BLOCKS |   -   | BLOCKS | BLOCKS |
Axis 4 (Data)     |   -    |   -    |   -    |   -    |REQUIRES|
Axis 5 (Invest)   |   -    |   -    |   -    |   -    |   -    |
```

### 7.2 Constraint Verification

#### Constraint 1: Axis 3 BLOCKS Axis 1, 2, 4, 5

**Check:** Axis 3 decision is "Proceed with guardrails" (not "Do not proceed")

**Result:** ✓ PASS - Downstream axis decisions can proceed with documented guardrails

---

#### Constraint 2: Axis 1 CONSTRAINS Axis 2

**Check:** Does Axis 2 decision acknowledge Axis 1 state?

**Result:** ✓ PASS - Axis 2 "High cost-of-change" is consistent with Axis 1 "Modernise" (structural constraints create change cost)

---

#### Constraint 3: Axis 1 REQUIRES Axis 5 allocation

**Check:** Does Axis 5 include investments required by Axis 1 modernisation?

**Result:** ✓ PASS - INV-004 (PaymentProcessor refactoring) and INV-005 (Provider interface extraction) directly address Axis 1 modernisation requirements

---

#### Constraint 4: Axis 2 CONSTRAINS Axis 5 timelines

**Check:** Does Axis 5 sequencing account for high cost-of-change?

**Result:** ✓ PASS - Axis 5 stages investments over 12 months rather than parallel execution, reflecting high change cost

---

#### Constraint 5: Axis 4 REQUIRES Axis 5 allocation

**Check:** Does Axis 5 include data investments if Axis 4 identified needs?

**Result:** ✓ PASS (N/A) - Axis 4 is "Steering ready" so no data investment required

---

### 7.3 Cross-Axis Summary

All constraints satisfied. No BLOCKS conditions prevent downstream decisions.

| Constraint | Type | Status |
|------------|------|--------|
| Axis 3 → All | BLOCKS | ✓ Cleared (guardrails defined) |
| Axis 1 → Axis 2 | CONSTRAINS | ✓ Acknowledged |
| Axis 1 → Axis 5 | REQUIRES | ✓ Investments allocated |
| Axis 2 → Axis 5 | CONSTRAINS | ✓ Timeline adjusted |
| Axis 4 → Axis 5 | REQUIRES | ✓ N/A (no requirement) |

---

## 8. Phase 7: Sample IC Output

### 8.1 Executive Summary

```markdown
# NovaPay Technical Due Diligence: Executive Summary

## Platform Assessment Matrix

| Dimension | Rating | Key Evidence |
|-----------|--------|--------------|
| Technical Viability | YELLOW | Structural constraints exist but are addressable |
| Security Posture | RED | 2 CRITICAL CVEs in payment SDKs |
| Operational Stability | YELLOW | 4-hour rollbacks; no provider test coverage |
| Change Velocity | RED | High cost-of-change; CCN=52 hotspot |
| Knowledge Continuity | RED | Bus factor=1 on two critical areas |
| Remediation Cost | MEDIUM | ~15 PM over 12 months |
| Rewrite Risk | LOW | Modernise, not replace |

## Platform Decision

**Recommendation:** MODERNISE

**Decision Type:** CONDITIONAL GO

**Conditions:**
1. Pre-close: Remediate CRITICAL CVEs (Stripe, Adyen SDKs)
2. 90-day: Initiate knowledge transfer program (Alice, Bob)
3. 6-month: Complete provider interface extraction

## Risk Summary

| Priority | Count | Top Risk |
|----------|-------|----------|
| P1 (Must Address) | 3 | CRITICAL payment SDK vulnerabilities |
| P2 (Should Address) | 4 | Knowledge concentration (Alice, Bob) |
| P3 (Track) | 2 | Code complexity hotspots |
| P4 (Monitor) | 1 | Test coverage gaps |

## Investment Requirements

| Urgency | PM Effort | Focus |
|---------|-----------|-------|
| Pre-Close | 2.5 PM | Security + credential audit |
| 90-Day | 3 PM | Knowledge transfer + rollback |
| 6-Month | 8-12 PM | Decoupling + provider interface |
| 12-Month | 3 PM | First new provider onboarding |

**Total:** 15-20 person-months over 12 months (~$1.5-2M loaded)
```

---

### 8.2 One-Slide-Per-Axis Summary

#### Slide 1: Axis 1 - Structural Platform Fitness

| Element | Content |
|---------|---------|
| **IC Question** | Can the platform support 5-10 new payment providers? |
| **Decision** | **MODERNISE** |
| **Claims Synthesis** | • Bidirectional coupling between Payments.Core and Providers.Integration (89+34 calls) prevents independent evolution<br>• Adding a provider requires modifying 12+ switch statements in PaymentProcessor<br>• Two previous decomposition attempts failed (2023, 2024)<br>• 2 CRITICAL CVEs in payment SDKs require immediate remediation |
| **Rationalisation** | Platform is not broken (processes $50M/month) but has reached structural limits for safe extension. Replacement not justified; targeted decoupling enables thesis. |
| **Enables** | Sustainable provider expansion after decoupling |
| **Blocks** | Rapid provider onboarding without architectural investment |
| **If Wrong** | Modernisation exceeds budget; trigger replan at 12 PM spent |

---

#### Slide 2: Axis 2 - Changeability & Cost-of-Change

| Element | Content |
|---------|---------|
| **IC Question** | How expensive and predictable is incremental change? |
| **Decision** | **HIGH COST-OF-CHANGE** |
| **Claims Synthesis** | • PaymentProcessor has CCN=52 (52 independent paths) in 3,200 LOC<br>• Changes propagate across module boundaries due to coupling<br>• Provider integration has zero automated test coverage<br>• Rollbacks take 4+ hours |
| **Rationalisation** | Consistent with interview data: "Provider addition takes 3-4 weeks." Roadmap must budget accordingly. |
| **Enables** | Realistic planning and buffer allocation |
| **Blocks** | Aggressive timeline assumptions |
| **If Wrong** | First provider addition in <2 weeks invalidates; accelerate |

---

#### Slide 3: Axis 3 - Execution System & Delivery Control

| Element | Content |
|---------|---------|
| **IC Question** | Can the team execute a growth roadmap under PE constraints? |
| **Decision** | **PROCEED WITH GUARDRAILS** |
| **Claims Synthesis** | • Alice has bus factor=1 on Provider integration (78% commits, only one who understands routing)<br>• Bob has bus factor=1 on PaymentProcessor (94% commits, 3,200 LOC)<br>• Rollback capability inadequate (4+ hours, manual)<br>• Credential rotation process has gaps |
| **Rationalisation** | Knowledge concentration is addressable with documentation and pair programming. Not a fundamental blocker but requires investment. |
| **Enables** | Roadmap execution with defined guardrails |
| **Blocks** | Aggressive timeline without knowledge transfer first |
| **If Wrong** | First blocked-work incident due to knowledge gap triggers escalation |

**Required Guardrails:**
1. Knowledge transfer program (weeks 1-12)
2. Pair programming mandate for critical paths
3. Rollback automation (90-day)
4. Credential rotation audit (30-day)

---

#### Slide 4: Axis 4 - Data Integrity & Steering Readiness

| Element | Content |
|---------|---------|
| **IC Question** | Can management reliably steer post-close? |
| **Decision** | **STEERING READY** |
| **Claims Synthesis** | • Revenue reconstructable by provider<br>• Transaction data complete<br>• No material data correctness issues identified<br>• Audit tables provide forward integrity |
| **Rationalisation** | Data infrastructure supports provider-level P&L tracking required for thesis execution. |
| **Enables** | Post-close steering and provider attribution |
| **Blocks** | Nothing |
| **If Wrong** | Finance flags discrepancies in first quarterly close |

---

#### Slide 5: Axis 5 - Investment Leverage & Sequencing

| Element | Content |
|---------|---------|
| **IC Question** | Where does capital most effectively reduce risk or unlock value? |
| **Decision** | **STAGE / TRANCHE** |
| **Claims Synthesis** | • Security remediation required pre-close (P1)<br>• Knowledge transfer de-risks execution (P1)<br>• Decoupling enables provider expansion (thesis)<br>• Rollback automation reduces change risk |
| **Rationalisation** | Multiple investments with dependencies; staging allows learning and risk management. |
| **Enables** | Phased execution with go/no-go gates |
| **Blocks** | Simultaneous parallel tracks |
| **If Wrong** | Tranche 1 under budget → accelerate Tranche 2 |

**Investment Tranches:**

| Tranche | Timing | Investments | PM |
|---------|--------|-------------|-----|
| 1 | Pre-close / 90-day | Security, knowledge transfer, credential audit | 3.5 |
| 2 | Months 3-9 | Decoupling, provider interface, rollback | 12-15 |
| 3 | Months 9-12 | Provider onboarding (validation) | 3 |

---

### 8.3 Key Risks & Investments

#### Top 5 Risks

| ID | Title | Severity | Type | Investment |
|----|-------|----------|------|------------|
| RISK-001 | CRITICAL payment SDK vulnerabilities | CRITICAL | Security | INV-001 |
| RISK-002 | Knowledge concentration - Alice | HIGH | Knowledge | INV-002 |
| RISK-003 | Knowledge concentration - Bob | HIGH | Knowledge | INV-002 |
| RISK-004 | Structural extensibility limit | HIGH | Architectural | INV-004, INV-005 |
| RISK-005 | Operational fragility (rollback) | MEDIUM | Operational | INV-006 |

#### Investment Summary

| ID | Title | Urgency | PM | Addresses |
|----|-------|---------|-----|-----------|
| INV-001 | Security remediation | Pre-close | 2 | RISK-001 |
| INV-002 | Knowledge transfer | 90-day | 1.5 | RISK-002, RISK-003 |
| INV-003 | Credential rotation audit | 30-day | 0.5 | E-SEC-003 |
| INV-004 | PaymentProcessor refactoring | 6-month | 6-9 | RISK-004, CLM-CMPLX-001 |
| INV-005 | Provider interface extraction | 6-month | 4-6 | RISK-004, CLM-ARCH-001 |
| INV-006 | Rollback automation | 90-day | 2 | RISK-005 |

---

### 8.4 Platform Recommendation

```markdown
## Recommendation: CONDITIONAL GO

**Platform Decision:** MODERNISE

**Rationale:** NovaPay's platform processes $50M/month reliably but has reached
structural limits for safe provider expansion. The investment thesis (5-10 new
providers) cannot be achieved without targeted modernisation. The constraints
are architectural (coupling, extensibility) and organisational (knowledge
concentration), not fundamental technology failures. These are addressable
with ~15-20 PM investment over 12 months.

**Conditions for Proceed:**

| Timing | Condition | Owner |
|--------|-----------|-------|
| Pre-close | CRITICAL CVEs remediated (Stripe, Adyen) | Target |
| Pre-close | Knowledge transfer program scoped | Buyer + Target |
| 90-day gate | Security audit passed | Target |
| 90-day gate | Knowledge transfer initiated | Target |
| 6-month gate | Provider interface extracted | Target |

**Acknowledged Risks:**
1. Knowledge transfer may be slower than planned
2. Decoupling effort may exceed estimates (cap at 15 PM for replan)
3. First provider post-modernisation may still take 3-4 weeks

**Success Criteria:**
1. Second new provider onboarded in <2 weeks (down from 3-4)
2. PaymentProcessor CCN reduced to <20
3. Bus factor >=2 on Provider integration and PaymentProcessor
```

---

## 9. Key Takeaways

This walkthrough demonstrates several key aspects of the Decision Framework:

### 9.1 Evidence → Lens → Claim Flow

The framework enforces a strict ordering:
1. **Evidence** captures facts without interpretation
2. **Lenses** constrain what claims are admissible
3. **Claims** are falsifiable, axis-specific assertions

This prevents "jumping to conclusions" and ensures all decisions are traceable to evidence.

### 9.2 Axis Independence and Constraints

Each axis answers one IC question:
- Axis 1: Platform fitness → Extend/Modernise/Replace
- Axis 2: Cost-of-change → Low/High/Unpredictable
- Axis 3: Execution capability → Proceed/Guardrails/Stop
- Axis 4: Data integrity → Ready/MVP/Risk
- Axis 5: Investment → Now/Stage/Defer

The constraint matrix ensures consistency (e.g., Axis 3 "Do not proceed" would block all other decisions).

### 9.3 Falsifiability as Quality Gate

Every claim includes a falsification condition:
- CLM-CMPLX-001: "False if ProcessTransaction can be modified in <2 days"
- CLM-COUP-001: "False if new provider can be added touching only Providers.Integration"

This makes claims testable and prevents vague assertions.

### 9.4 Confidence Calculation

Evidence count, reliability, and corroboration determine confidence:
- 3 evidence items + 2 source types + corroboration = HIGH confidence
- Single source or conflicting evidence = LOW confidence

### 9.5 Staged Investment Decisions

Axis 5 "Stage/tranche" allows learning and risk management:
- Pre-close: Address blockers (security)
- 90-day: Reduce execution risk (knowledge transfer)
- 6-month: Enable thesis (decoupling)
- 12-month: Validate (first provider)

---

## Appendix: Evidence-to-Claim Traceability Matrix

| Evidence ID | Primary Claim | Secondary Claims |
|-------------|---------------|------------------|
| E-CMPLX-001 | CLM-CMPLX-001 | CLM-KNOW-002 |
| E-CMPLX-002 | CLM-CMPLX-001 | - |
| E-COUP-001 | CLM-COUP-001 | CLM-ARCH-001 |
| E-COUP-002 | CLM-COUP-001 | - |
| E-COUP-003 | CLM-COUP-001 | CLM-ARCH-001 |
| E-SEC-001 | CLM-SEC-001 | - |
| E-SEC-002 | CLM-SEC-001 | - |
| E-SEC-003 | CLM-OPS-001 | - |
| E-SEC-004 | CLM-OPS-001 | - |
| E-KNOW-001 | CLM-KNOW-001 | - |
| E-KNOW-002 | CLM-KNOW-002 | CLM-CMPLX-001 |
| E-KNOW-003 | CLM-KNOW-001 | - |
| E-KNOW-004 | CLM-KNOW-001 | CLM-KNOW-002 |
| E-ARCH-001 | CLM-ARCH-001 | CLM-KNOW-002 |
| E-ARCH-002 | CLM-ARCH-001 | CLM-CMPLX-001 |
| E-OPS-001 | CLM-OPS-001 | - |
| E-OPS-002 | CLM-OPS-001 | - |
| E-DIST-001 | CLM-CMPLX-001 | CLM-COUP-001 |

---

*Walkthrough Version: 1.0*
*Created: 2026-02-03*
*Framework Reference: DECISION_FRAMEWORK.md v3.0*
