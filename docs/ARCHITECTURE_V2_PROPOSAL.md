# Architecture V2 Proposal: SoT-Centered Tool Architecture

**Version:** 1.4 Draft
**Status:** Draft for Review
**Author:** Architecture Discussion
**Date:** 2026-01-24

---

## Executive Summary

This document proposes a new architecture for Project Vulcan that emphasizes:
- **Tool Independence**: Each tool is self-contained with minimal shared code
- **Schema-First Design**: JSON schema validation at generation and consumption
- **JSON-Only Tools**: Tools emit JSON artifacts; the SoT engine is the sole DuckDB writer
- **Layered Data Quality**: Validation at raw JSON and SoT materialization levels
- **Flexible Execution**: System works with partial tool results
- **Grounded Evaluation**: Programmatic checks with synthetic ground truth; LLM judges are supplemental on real repos

---

## Primary Product Persona (V1)

Project Vulcan is first and foremost a **Technology Due Diligence and Execution-Risk Assessment Platform**.

The platform is optimized for **decision-relevant, evidence-backed** outputs under time pressure (hours/days, not weeks).

| Persona | Primary Focus | Platform Value |
|---------|---------------|----------------|
| **PE Tech DD Teams** | Investment risk assessment, execution risk | Objective metrics in hours, not weeks |
| **Acquirers** | Hidden technical debt, quality verification | Data-driven valuation decisions |
| **Operating Partners** | Portfolio company health, improvement tracking | Quantified health monitoring |

**Derived Consumption Modes:**
- **Engineering Health Monitoring**: Produced from the same evidence layer
- **AI-Agent Context Packs**: Structured outputs for coding assistants

**V1 Design Implications:**
- Defaults are conservative (avoid false authority)
- Missing coverage triggers confidence warnings rather than silently producing "complete-looking" outputs
- Decision thresholds are explicit and configurable

---

## Project Purpose

### The Problem We're Solving

**Technology due diligence is broken.** M&A tech assessments typically take 2-4 weeks with expensive consultants, producing subjective opinions rather than objective metrics. Engineering teams lack quantified visibility into codebase health. AI coding agents (Claude, Copilot, Cursor) lack structured context about code risk and quality.

The traditional approach fails because:
1. **Manual inspection doesn't scale** — Consultants sample 5-10% of the codebase
2. **Results are subjective** — "The code looks good" vs quantified risk scores
3. **Insights are stale** — Point-in-time snapshots that immediately decay
4. **Context is scattered** — Findings from different tools don't correlate
5. **AI agents fly blind** — No structured understanding of complexity hotspots

### Target Users and Use Cases

| User | Pain Point | How Vulcan Helps | Value Delivered |
|------|------------|------------------|-----------------|
| **PE Tech DD Teams** | 2-4 week manual assessment with $50-100K consultants | Automated analysis in hours | 10x faster, objective metrics |
| **Engineering Leaders** | No visibility into codebase health | Quantified risk scores, hotspot detection | Data-driven prioritization |
| **Platform Teams** | Inconsistent tool integration | Unified 28-tool pipeline with correlation | Single source of truth |
| **AI Coding Agents** | No structured codebase context | LLM-ready context packs with hotspots | 3x better code suggestions |
| **Security Teams** | Fragmented vulnerability data | Unified security debt scoring | Prioritized remediation |
| **Acquirers** | Hidden technical debt in targets | Objective quality metrics | Informed valuation decisions |

### Design Philosophy

The architecture follows four core principles that emerged from building and operating the system:

| Principle | Description | Rationale |
|-----------|-------------|-----------|
| **Evidence-First** | Every finding links to source data | Findings without evidence are opinions, not facts |
| **Tool-Agnostic** | Wrap any analysis tool with standard interface | Tools evolve; contracts persist |
| **Graceful Degradation** | Partial results > no results | A tool failure shouldn't block insights from 27 others |
| **LLM-Ready** | Structured outputs optimized for AI consumption | AI agents are first-class consumers |

### What Success Looks Like

A successful Vulcan analysis delivers:

1. **For Due Diligence**: A complete risk assessment with severity-ranked findings, knowledge concentration warnings, and technical debt quantification—delivered in hours, not weeks
2. **For Engineering**: Actionable hotspot lists prioritized by complexity × volatility, with specific refactoring suggestions
3. **For AI Agents**: Context packs sized for token windows (~50KB to ~400KB) with structured JSON for programmatic consumption

### Technology Due Diligence
Rapid, comprehensive codebase assessment for M&A decisions. When evaluating acquisition targets, stakeholders need objective metrics on code quality, security posture, technical debt, and maintainability—delivered in hours, not weeks.

### Quality Assessment
Comprehensive metrics for engineering teams to understand their codebase health:
- Code complexity and maintainability hotspots
- Test coverage and quality gaps
- Dependency freshness and security exposure
- Architecture conformance and coupling analysis

### Risk Identification
Automated detection of critical risks that impact business decisions:
- **Security vulnerabilities**: CVEs, exposed secrets, insecure patterns
- **License compliance**: Copyleft risks, license conflicts, attribution gaps
- **Knowledge concentration**: Bus factor, ownership silos, tribal knowledge
- **Technical debt**: Complexity accumulation, code duplication, stale dependencies

### Decision Support
Role-based context packs tailored for different stakeholders:

| Role | Focus | Output Size |
|------|-------|-------------|
| **Executive** | Risk summary, investment concerns, red flags | ~50KB |
| **Tech Lead** | Architecture issues, refactoring priorities, team risks | ~150KB |
| **Engineer** | Specific files, actionable fixes, code examples | ~400KB |

---

## Decision Semantics & Confidence

Strong metrics alone do not answer DD questions. PE users require clear thresholds, flags, and confidence semantics. Outputs must clearly distinguish between facts, derived signals, and evaluations.

### Coverage & Completeness Flags

Vulcan provides opinionated defaults for decision thresholds (configurable per run):

| Flag | Trigger Condition | Severity |
|------|-------------------|----------|
| `INCOMPLETE_LAYOUT` | Layout-scanner failed or file universe missing | Critical |
| `INCOMPLETE_TOOL_SET` | ≥ N critical tools missing (configurable, default: 3) | High |
| `LOW_FILE_COVERAGE` | < 85% of layout files referenced by SoT marts | Medium |

### Cross-Tool Consistency Flags

| Flag | Trigger Condition | Default Threshold |
|------|-------------------|-------------------|
| `METRIC_DISAGREEMENT_LOC` | LOC disagreement between primary sources | > 20% |
| `METRIC_DISAGREEMENT_COMPLEXITY` | Complexity distributions inconsistent | Beyond acceptable variance |
| `VULN_DEDUPLICATION_CONFLICT` | Duplicate findings not reconciled by SoT rules | Any unresolved |

### Decision Labels

| Label | Meaning | Example Triggers |
|-------|---------|------------------|
| `RED_FLAG` | Violates hard threshold(s) relevant to DD | Critical CVE, exposed secrets, copyleft in core |
| `YELLOW_FLAG` | Material risk requiring investment/plan | High technical debt, knowledge concentration |
| `INFO` | Notable but not decision-relevant | Style issues, minor warnings |

### Epistemic Labels

Every surfaced "claim" SHALL carry epistemic metadata:

| Field | Description | Example |
|-------|-------------|---------|
| `claim_type` | FACT \| DERIVED \| EVALUATION | `DERIVED` |
| `evidence_refs` | List of evidence pointers | `["file_id:f-a1b2c3", "tool:scc", "sot:file_metrics"]` |
| `confidence` | Numeric 0–1 with explanation | `0.85 (based on 3 concordant sources)` |
| `as_of` | Versioning context | `{run_id, commit, tool_versions}` |

**Definitions:**
- **FACT**: Measured/observed values from tool outputs or SoT materializations
- **DERIVED**: Deterministic computations on facts (risk scores, rollups, aggregations)
- **EVALUATION**: LLM-assisted judgments (advisory, versioned, reproducible)

---

## Table of Contents

1. [Current Architecture Summary](#1-current-architecture-summary)
2. [Proposed Architecture](#2-proposed-architecture)
   - 2.1 [High-Level Design](#21-high-level-design)
   - 2.2 [Core Principles](#22-core-principles)
   - 2.3 [Tool Input Contract](#23-tool-input-contract)
   - 2.4 [Tool Output Contract](#24-tool-output-contract)
   - 2.5 [Execution Modes](#25-execution-modes)
   - 2.6 [Branch and Commit Handling](#26-branch-and-commit-handling)
   - 2.7 [Tool Configuration Contract](#27-tool-configuration-contract)
3. [Component Deep Dives](#3-component-deep-dives)
   - 3.1 [Layout Scanner (Phase 0 Foundation)](#31-layout-scanner-phase-0-foundation)
     - [Stable File Identity (Phase 2)](#stable-file-identity-phase-2)
   - 3.2 [JSON Schema Validation](#32-json-schema-validation)
   - 3.3 [Source of Truth Engine](#33-source-of-truth-engine)
     - [Trend Analysis (Phase 2+)](#trend-analysis-phase-2)
   - 3.4 [LLM-Based Evaluation](#34-llm-based-evaluation)
     - [LLM Evaluation Guardrails](#llm-evaluation-guardrails)
   - 3.5 [Data Quality Framework](#35-data-quality-framework)
   - 3.6 [Out-of-Process Execution](#36-out-of-process-execution)
     - [Canonical Ingestion Rule](#canonical-ingestion-rule)
   - 3.7 [Run Lifecycle & Retention](#37-run-lifecycle--retention)
4. [Tool Building Guide](#4-tool-building-guide)
   - 4.5 [vulcan-core Package](#45-vulcan-core-package)
   - 4.6 [CI Compliance Gates](#46-ci-compliance-gates)
   - 4.7 [Tool Compliance Validation](#47-tool-compliance-validation)
5. [Data Flow](#5-data-flow)
6. [Pros and Cons](#6-pros-and-cons)
7. [Alternative Approaches](#7-alternative-approaches)
8. [Migration Strategy](#8-migration-strategy)
9. [Open Questions](#9-open-questions)
10. [Learnings & Best Practices](#10-learnings--best-practices)
    - 10.1 [What Works Well](#101-what-works-well)
    - 10.2 [Patterns That Proved Effective](#102-patterns-that-proved-effective)
    - 10.3 [What Needs Improvement](#103-what-needs-improvement)
    - 10.4 [Key Architectural Decisions](#104-key-architectural-decisions)
11. [V1 Non-Goals](#11-v1-non-goals)
12. [Change Log](#12-change-log)
- [Appendix A: Schema Examples](#appendix-a-schema-examples)
- [Appendix B: dbt Model Examples](#appendix-b-dbt-model-examples)
- [Appendix C: Compliance Checklist](#appendix-c-compliance-checklist)
- [Appendix D: SQL Query Catalog](#appendix-d-sql-query-catalog)
- [Appendix E: Success Patterns Catalog](#appendix-e-success-patterns-catalog)
- [Appendix F: Minimal Schemas (V1.1)](#appendix-f-minimal-schemas-v11)

---

## 1. Current Architecture Summary

### Current Pain Points

| Issue | Impact |
|-------|--------|
| **Tight Coupling** | Tools depend on collector's adapter layer |
| **Centralized Persistence** | All tools route through collector's persistence DSL |
| **Validation Gap** | Schema validation only at consumption, not generation |
| **Ground Truth Dependency** | Evaluation requires manually curated baselines |
| **Partial Results** | System fails if any tool fails |

### Current Data Flow

```
Tool → JSON → Collector Adapter → Persistence DSL → DuckDB
         ↓
    (validation only here)
```

---

## 2. Proposed Architecture

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR                                    │
│  • Dispatches run_id, repo_path, commit, output_path to tools               │
│  • Manages execution phases (0 → 1 → 2 → 3)                                 │
│  • Tracks tool completion status                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  TOOL (Phase 0) │         │  TOOL (Phase 1) │         │  TOOL (Phase N) │
│  layout-scanner │         │  scc, lizard... │         │  depends, ...   │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ Input:          │         │ Input:          │         │ Input:          │
│ • repo_path     │         │ • repo_path     │         │ • repo_path     │
│ • commit        │         │ • commit        │         │ • commit        │
│ • run_id        │         │ • run_id        │         │ • run_id        │
│ • output_path   │         │ • output_path   │         │ • output_path   │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ Output:         │         │ Output:         │         │ Output:         │
│ • JSON (schema) │         │ • JSON (schema) │         │ • JSON (schema) │
│ • metadata.json │         │ • metadata.json │         │ • metadata.json │
└─────────────────┘         └─────────────────┘         └─────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LANDING ZONE (DuckDB)                                │
│  • Per-tool schemas (tool_{name}_*)                                         │
│  • Raw data with run_id, repo_id correlation (repo_id injected at ingest)   │
│  • Data quality checks at ingestion                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SOURCE OF TRUTH ENGINE (dbt/dagster)                      │
│  • Transforms landing zone → unified marts                                   │
│  • Conflict resolution rules                                                 │
│  • Data quality assertions                                                   │
│  • Materialized views for queries                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SOURCE OF TRUTH (DuckDB)                             │
│  • Unified file_metrics, vulnerabilities, etc.                              │
│  • Cross-tool aggregations                                                   │
│  • Query-optimized views                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Principles

| Principle | Description |
|-----------|-------------|
| **Tool Independence** | Tools have zero knowledge of other tools |
| **Schema-First** | All data validated at generation AND consumption |
| **Correlation IDs** | `run_id` and `repo_id` are emitted by tools |
| **Graceful Degradation** | System works with partial tool results |
| **Layout as Foundation** | Layout scanner provides canonical file/directory references (SoT engine only) |
| **Single Ingestion Path** | JSON → SoT adapters → landing zone → dbt marts only |

### 2.3 Tool Input Contract

Every tool receives exactly these inputs:

```python
@dataclass
class ToolInput:
    repo_path: str                    # Absolute path to repository
    branch: str = "main"              # Branch to analyze (default: main/default branch)
    commit: str = "HEAD"              # Commit hash (default: latest on branch)
    run_id: str                       # Collection run id (stable per repo+commit)
    output_path: str                  # Directory for tool outputs
    repo_id: str                      # Repository identifier (string)
    remote_url: Optional[str]         # Remote URL (if available)
    local_path: str                   # Local checkout path
```

**Parameter Details:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `repo_path` | Yes | — | Absolute path to cloned repository |
| `branch` | No | `"main"` | Branch to analyze; auto-detected if not specified |
| `commit` | No | `"HEAD"` | Commit SHA; resolves to latest on branch if HEAD |
| `run_id` | Yes | — | Collection run id (unique per repo+commit) |
| `output_path` | Yes | — | Directory for JSON outputs (`{output_path}/{tool_name}/`) |
| `repo_id` | Yes | — | Repository identifier (provided by orchestrator) |
| `remote_url` | No | `None` | Remote repository URL if available |
| `local_path` | Yes | — | Local checkout path used for analysis |

**Notes:**
- Tools emit repo-relative paths only; they do not use layout APIs directly.
- Each repo+commit maps to one collection run; reruns require `--replace` and overwrite prior data.
- Tools should NOT assume HEAD—always resolve to actual SHA.
- Repo identity (repo_id, remote_url, local_path) is established before any tool runs.

### 2.4 Tool Output Contract

Every tool produces:

1. **JSON Output** (validated against tool schema)
   ```
   {output_path}/{tool_name}/output.json
   ```

2. **Execution Metadata**
   ```
   {output_path}/{tool_name}/metadata.json
   ```
3. **Optional Debug Artifacts**
   ```
   {output_path}/{tool_name}/logs/
   ```

The SoT engine owns persistence: for each tool and `schema_version`, an adapter maps JSON outputs into DuckDB landing tables via repositories. dbt then transforms landing tables into unified marts.

Repo IDs are generated by the orchestrator/application from the local checkout path or remote URL and passed into tools for inclusion in outputs.

### 2.4.1 Relative Path Rules (Required)

All tool outputs MUST use repo-relative paths with consistent normalization so the SoT engine can resolve file IDs deterministically:

- Paths are relative to the repository root (no leading `/`, no drive letters).
- Use `/` as the separator on all platforms.
- No `.` or `..` segments after normalization.
- No trailing `/` for files.
- Preserve case; do not lowercase paths.
- Do not include `repo_path` prefixes in output fields.

### 2.5 Execution Modes

The orchestrator supports three execution modes to balance development convenience, isolation, and scalability:

| Mode | Max Parallel | Isolation | Use Case |
|------|-------------|-----------|----------|
| **LOCAL** | 2 | None (threads) | Development, debugging, light workloads |
| **DOCKER** | 8+ | Container | Production, CI/CD, reproducible builds |
| **VM** | 16+ | Full VM | Heavy parallelization, untrusted code, full isolation |

#### ExecutionMode Enum

```python
from enum import Enum

class ExecutionMode(Enum):
    LOCAL = "local"      # Direct process execution
    DOCKER = "docker"    # Container-based execution
    VM = "vm"            # Virtual machine execution
```

#### ExecutionConfig Dataclass

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExecutionConfig:
    mode: ExecutionMode
    max_parallel: int
    timeout_seconds: int = 300
    memory_limit_mb: Optional[int] = None
    cpu_limit: Optional[float] = None

    @classmethod
    def local(cls) -> "ExecutionConfig":
        return cls(mode=ExecutionMode.LOCAL, max_parallel=2)

    @classmethod
    def docker(cls, parallel: int = 8) -> "ExecutionConfig":
        return cls(
            mode=ExecutionMode.DOCKER,
            max_parallel=parallel,
            memory_limit_mb=4096,
            cpu_limit=2.0
        )

    @classmethod
    def vm(cls, parallel: int = 16) -> "ExecutionConfig":
        return cls(
            mode=ExecutionMode.VM,
            max_parallel=parallel,
            memory_limit_mb=8192,
            cpu_limit=4.0
        )
```

#### ExecutionBackend Interface

```python
from abc import ABC, abstractmethod
from typing import List

class ExecutionBackend(ABC):
    """Abstract interface for tool execution backends."""

    @abstractmethod
    def execute(self, tool_name: str, inputs: ToolInput) -> ExecutionResult:
        """Execute a single tool and return results."""
        pass

    @abstractmethod
    def execute_batch(self, tasks: List[ToolTask]) -> List[ExecutionResult]:
        """Execute multiple tools in parallel (up to max_parallel)."""
        pass

    @abstractmethod
    def collect_outputs(self, execution_id: str) -> OutputCollection:
        """Collect outputs from execution (especially for remote modes)."""
        pass


class LocalBackend(ExecutionBackend):
    """Direct subprocess execution on local machine."""
    pass


class DockerBackend(ExecutionBackend):
    """Container-based execution with volume mounts."""
    pass


class VMBackend(ExecutionBackend):
    """VM-based execution with SSH/API communication."""
    pass
```

#### Backend Selection

```python
def get_backend(config: ExecutionConfig) -> ExecutionBackend:
    """Factory function to get appropriate backend."""
    backends = {
        ExecutionMode.LOCAL: LocalBackend,
        ExecutionMode.DOCKER: DockerBackend,
        ExecutionMode.VM: VMBackend,
    }
    return backends[config.mode](config)
```

### 2.6 Branch and Commit Handling

The orchestrator resolves branch and commit references before dispatching to tools.

#### Default Branch Detection

```python
def get_default_branch(repo_path: str) -> str:
    """Detect the repository's default branch."""
    try:
        # Try symbolic-ref first (works for cloned repos)
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=repo_path, capture_output=True, text=True
        )
        if result.returncode == 0:
            # refs/remotes/origin/main -> main
            return result.stdout.strip().split("/")[-1]
    except Exception:
        pass

    # Fallback: check for common default branches
    for branch in ["main", "master", "develop"]:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
            cwd=repo_path, capture_output=True
        )
        if result.returncode == 0:
            return branch

    # Last resort: use current HEAD
    return "HEAD"
```

#### Commit Resolution

```python
def resolve_commit(repo_path: str, ref: str = "HEAD") -> str:
    """Resolve a ref (branch, tag, HEAD) to a full commit SHA."""
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=repo_path, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ValueError(f"Cannot resolve ref: {ref}")
    return result.stdout.strip()
```

#### RepoInfo Dataclass

```python
@dataclass
class RepoInfo:
    """Repository information resolved by orchestrator."""

    repo_path: str
    repo_id: uuid.UUID
    name: str
    remote_url: Optional[str]
    branch: str
    commit: str  # Full SHA, never HEAD

    @classmethod
    def from_path(cls, repo_path: str, branch: Optional[str] = None) -> "RepoInfo":
        """Create RepoInfo from repository path."""
        repo_path = os.path.abspath(repo_path)

        # Resolve branch
        if branch is None:
            branch = get_default_branch(repo_path)

        # Always resolve to full SHA
        commit = resolve_commit(repo_path, branch)

        # Get remote URL if available
        remote_url = get_remote_url(repo_path)

        # Generate deterministic repo_id from remote_url or path
        repo_id = generate_repo_id(remote_url or repo_path)

        return cls(
            repo_path=repo_path,
            repo_id=repo_id,
            name=os.path.basename(repo_path),
            remote_url=remote_url,
            branch=branch,
            commit=commit
        )
```

#### Run ID vs Commit

```
IMPORTANT: run_id is the unique identifier, NOT commit.

The same commit can have multiple analysis runs:
- Different tool configurations
- Different analysis parameters
- Re-runs after tool updates
- Incremental vs full analysis

run_id = UUID v4 generated fresh for each collection run
commit = Git SHA identifying the code state
repo_id = Deterministic UUID based on repository identity
```

### 2.7 Tool Configuration Contract

In addition to CLI parameters, tools support configuration via JSON files with versioned schema validation. This enables programmatic tool invocation, reproducible analysis runs, and configuration management.

#### 2.7.1 Configuration File Format

Tools accept a `--config` argument pointing to a JSON configuration file:

```json
{
  "$schema": "https://vulcan.dev/schemas/tool-config/v1.json",
  "schema_version": "1.0.0",
  "tool_name": "scc",
  "parameters": {
    "repo_path": "/path/to/repo",
    "branch": "main",
    "commit": "abc123def456789012345678901234567890abcd",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "output_path": "./output",
    "tool_specific": {
      "cocomo_preset": "sme",
      "threads": 4,
      "exclude_patterns": ["vendor/**", "node_modules/**"]
    }
  }
}
```

#### 2.7.2 Configuration Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Tool Configuration Schema",
  "type": "object",
  "required": ["schema_version", "tool_name", "parameters"],
  "properties": {
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version of this schema"
    },
    "tool_name": {
      "type": "string",
      "description": "Name of the tool this config applies to"
    },
    "parameters": {
      "type": "object",
      "required": ["repo_path", "run_id", "output_path"],
      "properties": {
        "repo_path": {
          "type": "string",
          "description": "Absolute path to repository"
        },
        "branch": {
          "type": "string",
          "default": "main",
          "description": "Branch to analyze"
        },
        "commit": {
          "type": "string",
          "default": "HEAD",
          "description": "Commit SHA or HEAD"
        },
        "run_id": {
          "type": "string",
          "format": "uuid",
          "description": "UUID for this collection run"
        },
        "output_path": {
          "type": "string",
          "description": "Directory for tool outputs"
        },
        "tool_specific": {
          "type": "object",
          "description": "Tool-specific parameters (schema varies by tool)",
          "additionalProperties": true
        }
      }
    }
  }
}
```

#### 2.7.3 Schema Versioning

Configuration schemas use semantic versioning:

| Version Change | Description | Example |
|---------------|-------------|---------|
| **MAJOR** | Breaking changes (removed/renamed fields) | 1.0.0 → 2.0.0 |
| **MINOR** | New optional fields, backward compatible | 1.0.0 → 1.1.0 |
| **PATCH** | Documentation, description changes only | 1.0.0 → 1.0.1 |

**Compatibility Rules:**
- Tools MUST accept configs with matching MAJOR version
- Tools SHOULD ignore unknown fields (forward compatibility)
- Tools MUST validate required fields exist
- Tools MUST log warnings for deprecated fields

#### 2.7.4 Configuration Validation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONFIGURATION VALIDATION FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

1. LOAD
   Read config file → Parse JSON → Basic syntax validation

2. SCHEMA VERSION CHECK
   Compare config schema_version with tool's expected version
   • Same MAJOR: proceed
   • Different MAJOR: error with migration guidance

3. VALIDATE AGAINST SCHEMA
   • Required fields present (repo_path, run_id, output_path)
   • Field types correct
   • Pattern/format constraints (UUID, paths)

4. MERGE WITH CLI
   CLI arguments override config file values
   Priority: CLI > Config File > Defaults

5. VALIDATE TOOL-SPECIFIC
   • Tool validates its tool_specific section
   • Unknown fields logged as warnings

6. EXECUTE
   Tool runs with validated configuration
```

#### 2.7.5 Configuration Loading Implementation

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json

from jsonschema import validate, ValidationError

# Expected schema version (MAJOR.MINOR.PATCH)
EXPECTED_SCHEMA_VERSION = "1.0.0"

@dataclass
class ToolConfig:
    """Validated tool configuration."""
    repo_path: str
    branch: str
    commit: str
    run_id: str
    output_path: str
    tool_specific: Dict[str, Any]


class ConfigVersionError(Exception):
    """Raised when config schema version is incompatible."""
    pass


def load_and_validate_config(config_path: str) -> ToolConfig:
    """Load config file and validate against schema."""
    # Load schema
    schema_path = Path(__file__).parent / "schemas" / "config.schema.json"
    schema = json.loads(schema_path.read_text())

    # Load config
    config = json.loads(Path(config_path).read_text())

    # Check schema version compatibility (MAJOR must match)
    config_version = config.get("schema_version", "0.0.0")
    config_major = int(config_version.split(".")[0])
    expected_major = int(EXPECTED_SCHEMA_VERSION.split(".")[0])

    if config_major != expected_major:
        raise ConfigVersionError(
            f"Config schema version {config_version} incompatible with "
            f"expected version {EXPECTED_SCHEMA_VERSION}. "
            f"MAJOR version must match."
        )

    # Validate against JSON Schema
    try:
        validate(config, schema)
    except ValidationError as e:
        raise ValueError(f"Config validation failed: {e.message}")

    # Extract parameters
    params = config["parameters"]
    return ToolConfig(
        repo_path=params["repo_path"],
        branch=params.get("branch", "main"),
        commit=params.get("commit", "HEAD"),
        run_id=params["run_id"],
        output_path=params["output_path"],
        tool_specific=params.get("tool_specific", {})
    )


def merge_config_with_cli(config: Optional[ToolConfig], cli_args) -> ToolConfig:
    """Merge config file with CLI arguments. CLI takes precedence."""
    if config is None:
        # No config file, use CLI args only
        return ToolConfig(
            repo_path=cli_args.repo_path,
            branch=cli_args.branch,
            commit=cli_args.commit,
            run_id=cli_args.run_id,
            output_path=cli_args.output_path,
            tool_specific={}
        )

    # CLI overrides config where specified
    return ToolConfig(
        repo_path=cli_args.repo_path or config.repo_path,
        branch=cli_args.branch if cli_args.branch != "main" else config.branch,
        commit=cli_args.commit if cli_args.commit != "HEAD" else config.commit,
        run_id=cli_args.run_id or config.run_id,
        output_path=cli_args.output_path or config.output_path,
        tool_specific=config.tool_specific  # Tool-specific only from config
    )
```

---

## 3. Component Deep Dives

### 3.1 Layout Scanner (Phase 0 Foundation)

The layout scanner runs first and provides canonical file/directory references for the SoT engine.

#### Current Implementation

```python
# Canonical ID generation (SHA-256 based)
file_id = f"f-{sha256(relative_path)[:12]}"      # e.g., f-a1b2c3d4e5f6
directory_id = f"d-{sha256(relative_path)[:12]}" # e.g., d-1a2b3c4d5e6f
```

#### Layout API Interface

The Layout API is an internal SoT engine interface used during persistence (tools do not call it directly). It provides file and directory lookup methods:

```python
@dataclass
class FileInfo:
    """Information about a file from layout scanner."""
    file_id: str              # f-a1b2c3d4e5f6
    relative_path: str        # src/main.py
    directory_id: str         # d-1a2b3c4d5e6f
    filename: str             # main.py
    extension: str            # .py
    language: str             # Python
    category: str             # source, test, config, docs
    size_bytes: int
    line_count: int
    is_binary: bool


@dataclass
class DirectoryInfo:
    """Information about a directory from layout scanner."""
    directory_id: str         # d-1a2b3c4d5e6f
    relative_path: str        # src/
    parent_id: Optional[str]  # d-0987654321ab (None for root)
    depth: int                # 0 for root, 1 for top-level, etc.
    file_count: int           # Direct files in this directory
    total_size_bytes: int     # Total size of files in this directory


class LayoutAPI:
    """Programmatic interface to layout scanner results."""

    def __init__(self, db_path: str, run_pk: int):
        self.db_path = db_path
        self.run_pk = run_pk
        self._conn = duckdb.connect(db_path, read_only=True)

    # ─────────────────────────────────────────────────────────────
    # FILE METHODS
    # ─────────────────────────────────────────────────────────────

    def get_file_id(self, relative_path: str) -> str:
        """Get canonical file ID for a path."""
        result = self._conn.execute("""
            SELECT file_id FROM lz_layout_files
            WHERE run_pk = ? AND relative_path = ?
        """, [self.run_pk, relative_path]).fetchone()
        if not result:
            raise FileNotFoundError(f"No file found: {relative_path}")
        return result[0]

    def get_file_by_id(self, file_id: str) -> FileInfo:
        """Get file information by canonical ID."""
        row = self._conn.execute("""
            SELECT * FROM lz_layout_files
            WHERE run_pk = ? AND file_id = ?
        """, [self.run_pk, file_id]).fetchone()
        if not row:
            raise FileNotFoundError(f"No file found with ID: {file_id}")
        return FileInfo(*row[2:])  # Skip run_pk

    def get_files_by_language(self, language: str) -> List[FileInfo]:
        """Get all files of a specific language."""
        rows = self._conn.execute("""
            SELECT * FROM lz_layout_files
            WHERE run_pk = ? AND language = ?
            ORDER BY relative_path
        """, [self.run_pk, language]).fetchall()
        return [FileInfo(*row[2:]) for row in rows]

    def get_files_by_category(self, category: str) -> List[FileInfo]:
        """Get files by category (source, test, config, docs, etc.)."""
        rows = self._conn.execute("""
            SELECT * FROM lz_layout_files
            WHERE run_pk = ? AND category = ?
            ORDER BY relative_path
        """, [self.run_pk, category]).fetchall()
        return [FileInfo(*row[2:]) for row in rows]

    def get_files_in_directory(self, directory_id: str) -> List[FileInfo]:
        """Get all files directly in a directory (not recursive)."""
        rows = self._conn.execute("""
            SELECT * FROM lz_layout_files
            WHERE run_pk = ? AND directory_id = ?
            ORDER BY filename
        """, [self.run_pk, directory_id]).fetchall()
        return [FileInfo(*row[2:]) for row in rows]

    def resolve_path(self, file_id: str) -> str:
        """Resolve file ID back to relative path."""
        return self.get_file_by_id(file_id).relative_path

    # ─────────────────────────────────────────────────────────────
    # DIRECTORY METHODS
    # ─────────────────────────────────────────────────────────────

    def get_directory_id(self, relative_path: str) -> str:
        """Get canonical directory ID for a path."""
        result = self._conn.execute("""
            SELECT directory_id FROM lz_layout_directories
            WHERE run_pk = ? AND relative_path = ?
        """, [self.run_pk, relative_path]).fetchone()
        if not result:
            raise FileNotFoundError(f"No directory found: {relative_path}")
        return result[0]

    def get_directory_by_id(self, directory_id: str) -> DirectoryInfo:
        """Get directory information by canonical ID."""
        row = self._conn.execute("""
            SELECT * FROM lz_layout_directories
            WHERE run_pk = ? AND directory_id = ?
        """, [self.run_pk, directory_id]).fetchone()
        if not row:
            raise FileNotFoundError(f"No directory found with ID: {directory_id}")
        return DirectoryInfo(*row[2:])  # Skip run_pk

    def get_child_directories(self, directory_id: str) -> List[DirectoryInfo]:
        """Get immediate child directories."""
        rows = self._conn.execute("""
            SELECT * FROM lz_layout_directories
            WHERE run_pk = ? AND parent_id = ?
            ORDER BY relative_path
        """, [self.run_pk, directory_id]).fetchall()
        return [DirectoryInfo(*row[2:]) for row in rows]

    def get_root_directory(self) -> DirectoryInfo:
        """Get the root directory (depth = 0)."""
        row = self._conn.execute("""
            SELECT * FROM lz_layout_directories
            WHERE run_pk = ? AND depth = 0
        """, [self.run_pk]).fetchone()
        if not row:
            raise RuntimeError("No root directory found")
        return DirectoryInfo(*row[2:])

    def get_directory_tree(self, directory_id: Optional[str] = None) -> DirectoryNode:
        """Get full directory tree structure (recursive)."""
        if directory_id is None:
            root = self.get_root_directory()
            directory_id = root.directory_id

        dir_info = self.get_directory_by_id(directory_id)
        children = self.get_child_directories(directory_id)

        return DirectoryNode(
            info=dir_info,
            files=self.get_files_in_directory(directory_id),
            children=[self.get_directory_tree(c.directory_id) for c in children]
        )
```

#### Layout API Methods Summary

| Category | Method | Returns |
|----------|--------|---------|
| **File** | `get_file_id(path)` | `str` (file_id) |
| **File** | `get_file_by_id(file_id)` | `FileInfo` |
| **File** | `get_files_by_language(lang)` | `List[FileInfo]` |
| **File** | `get_files_by_category(cat)` | `List[FileInfo]` |
| **File** | `get_files_in_directory(dir_id)` | `List[FileInfo]` |
| **File** | `resolve_path(file_id)` | `str` (relative_path) |
| **Directory** | `get_directory_id(path)` | `str` (directory_id) |
| **Directory** | `get_directory_by_id(dir_id)` | `DirectoryInfo` |
| **Directory** | `get_child_directories(dir_id)` | `List[DirectoryInfo]` |
| **Directory** | `get_root_directory()` | `DirectoryInfo` |
| **Directory** | `get_directory_tree(dir_id)` | `DirectoryNode` |

#### Layout Scanner DuckDB Schema

```sql
-- Tool landing zone tables
CREATE SEQUENCE lz_run_pk_seq START 1;

CREATE TABLE lz_tool_runs (
    run_pk BIGINT DEFAULT nextval('lz_run_pk_seq'),
    repo_id UUID NOT NULL,
    run_id UUID NOT NULL,
    tool_name VARCHAR NOT NULL,
    tool_version VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL,
    branch VARCHAR NOT NULL,
    commit VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk)
);

CREATE TABLE lz_layout_files (
    run_pk BIGINT NOT NULL,
    file_id VARCHAR NOT NULL,           -- f-a1b2c3d4e5f6
    relative_path VARCHAR NOT NULL,
    directory_id VARCHAR NOT NULL,      -- d-1a2b3c4d5e6f
    filename VARCHAR NOT NULL,
    extension VARCHAR,
    language VARCHAR,
    category VARCHAR,                   -- source, test, config, docs, etc.
    size_bytes BIGINT,
    line_count INTEGER,
    is_binary BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_pk, file_id)
);

CREATE TABLE lz_layout_directories (
    run_pk BIGINT NOT NULL,
    directory_id VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    parent_id VARCHAR,                  -- Parent directory ID
    depth INTEGER NOT NULL,
    file_count INTEGER,
    total_size_bytes BIGINT,
    PRIMARY KEY (run_pk, directory_id)
);
```

#### Stable File Identity (Phase 2)

The current `file_id = hash(relative_path)` approach works within a single run but breaks longitudinal analysis across file moves/renames. Phase 2 introduces a stable identifier for cross-run continuity.

**New Field: `stable_file_fingerprint`**

| Field | Type | Phase | Description |
|-------|------|-------|-------------|
| `stable_file_fingerprint` | VARCHAR | Phase 2 | Content-based hash for cross-run identity |

**Schema Addition (lz_layout_files):**
```sql
-- Phase 2 addition
ALTER TABLE lz_layout_files ADD COLUMN stable_fingerprint VARCHAR;
-- Nullable in Phase 1, backfilled later
```

**Fingerprint Computation:**
- **Preferred**: Content-based hash of normalized file contents (whitespace-normalized, encoding-normalized)
- **Optional augmentation**: Git rename detection mapping between commits

**SoT Mapping Rule:**
The Source of Truth MAY map files across runs using `stable_fingerprint` when available:
```
file_id(run N) → stable_fingerprint → file_id(run N+1)
```

**Phase 1 Limitations:**
Until `stable_fingerprint` is available, trend analysis is limited to:
- Directory-level rollups
- Language-level rollups
- Repository-wide aggregates

> **Implementation Note:** Add `stable_fingerprint` schema change to layout-scanner backlog. This is a Phase 2 feature.

### 3.2 JSON Schema Validation

#### Global Envelope Schema

All tool outputs conform to a global envelope:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Tool Output Envelope",
  "type": "object",
  "required": ["metadata", "data"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["tool_name", "tool_version", "run_id", "repo_id", "branch", "commit", "timestamp"],
      "properties": {
        "tool_name": { "type": "string" },
        "tool_version": { "type": "string" },
        "run_id": { "type": "string", "format": "uuid" },
        "repo_id": { "type": "string", "format": "uuid" },
        "branch": { "type": "string", "description": "Branch analyzed (e.g., main, develop)" },
        "commit": { "type": "string", "pattern": "^[a-f0-9]{40}$", "description": "Full commit SHA (never HEAD)" },
        "timestamp": { "type": "string", "format": "date-time" },
        "duration_seconds": { "type": "number" },
        "exit_code": { "type": "integer" },
        "files_analyzed": { "type": "integer" },
        "schema_version": { "type": "string" }
      }
    },
    "data": {
      "type": "object",
      "description": "Tool-specific data (validated against tool schema)"
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code": { "type": "string" },
          "message": { "type": "string" },
          "file": { "type": "string" },
          "recoverable": { "type": "boolean" }
        }
      }
    }
  }
}
```

#### Tool-Specific Schema Example (scc)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SCC Tool Output",
  "type": "object",
  "required": ["files", "summary"],
  "properties": {
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "language", "lines"],
        "properties": {
          "path": {
            "type": "string",
            "pattern": "^[^/].*",
            "not": {
              "pattern": "(^\\./|\\.\\.|^[A-Za-z]:|/$|\\\\)"
            }
          },
          "language": { "type": "string" },
          "lines": { "type": "integer", "minimum": 0 },
          "code": { "type": "integer", "minimum": 0 },
          "comments": { "type": "integer", "minimum": 0 },
          "blanks": { "type": "integer", "minimum": 0 },
          "complexity": { "type": "integer", "minimum": 0 }
        }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_files": { "type": "integer" },
        "total_lines": { "type": "integer" },
        "languages": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "files": { "type": "integer" },
              "lines": { "type": "integer" }
            }
          }
        }
      }
    }
  }
}
```

#### Validation Points

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          VALIDATION PIPELINE                              │
└──────────────────────────────────────────────────────────────────────────┘

   [Tool Execution]
         │
         ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  VALIDATION POINT 1: JSON Generation                        │
   │  • Envelope schema validation                                │
   │  • Tool-specific schema validation                           │
   │  • File ID format validation (f-xxx pattern)                 │
   │  • Required field presence                                   │
   └─────────────────────────────────────────────────────────────┘
         │
         ▼
   [Write to Landing Zone]
         │
         ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  VALIDATION POINT 2: Landing Zone Ingestion                  │
   │  • Foreign key validation (file_id exists in layout)         │
   │  • Data type validation                                      │
   │  • Duplicate detection                                       │
   │  • Run ID consistency                                        │
   └─────────────────────────────────────────────────────────────┘
         │
         ▼
   [Source of Truth Transformation]
         │
         ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  VALIDATION POINT 3: Source of Truth                         │
   │  • Cross-tool consistency (e.g., LOC values match)           │
   │  • Completeness checks (expected files present)              │
   │  • Business rule validation                                  │
   │  • Conflict resolution logging                               │
   └─────────────────────────────────────────────────────────────┘
```

### 3.3 Source of Truth Engine

#### Technology Choice: dbt vs Dagster

| Aspect | dbt | Dagster |
|--------|-----|---------|
| **Focus** | SQL transformations | Orchestration + transformations |
| **Learning Curve** | Lower (SQL-centric) | Higher (Python-centric) |
| **Testing** | Built-in data tests | Software engineering tests |
| **Scheduling** | Requires external (Airflow) | Built-in |
| **Lineage** | Excellent | Excellent |
| **DuckDB Support** | Native (dbt-duckdb) | Via IO managers |

**Recommendation:** Start with **dbt-duckdb** for simplicity, consider Dagster for complex orchestration needs.

#### dbt Project Structure

```
src/source-of-truth/
├── dbt_project.yml
├── profiles.yml
├── models/
│   ├── staging/                    # Landing zone views
│   │   ├── stg_layout_files.sql
│   │   ├── stg_scc_files.sql
│   │   ├── stg_lizard_functions.sql
│   │   └── stg_semgrep_findings.sql
│   │
│   ├── intermediate/               # Business logic
│   │   ├── int_file_metrics.sql    # Merge scc + lizard
│   │   ├── int_vulnerabilities.sql # Dedupe trivy + semgrep
│   │   └── int_complexity_rollup.sql
│   │
│   └── marts/                      # Final tables
│       ├── file_metrics.sql        # Unified file metrics
│       ├── directory_metrics.sql   # Rolled up metrics
│       ├── vulnerabilities.sql     # All security findings
│       └── risk_indicators.sql     # Computed risk scores
│
├── tests/                          # Data quality tests
│   ├── file_metrics_has_loc.sql
│   ├── vulnerabilities_have_severity.sql
│   └── no_orphan_file_ids.sql
│
└── macros/                         # Reusable SQL
    ├── resolve_conflict.sql        # Priority-based conflict resolution
    └── compute_risk_score.sql
```

#### Conflict Resolution in dbt

```sql
-- models/intermediate/int_file_metrics.sql

WITH scc_metrics AS (
    SELECT
        file_id,
        run_id,
        lines AS loc,
        code AS sloc,
        complexity,
        1 AS priority  -- Highest priority for LOC
    FROM {{ ref('stg_scc_files') }}
),

lizard_metrics AS (
    SELECT
        file_id,
        run_id,
        nloc AS loc,
        nloc AS sloc,
        max_ccn AS complexity,
        2 AS priority  -- Fallback for LOC, highest for complexity
    FROM {{ ref('stg_lizard_functions') }}
    GROUP BY file_id, run_id
),

merged AS (
    SELECT
        COALESCE(s.file_id, l.file_id) AS file_id,
        COALESCE(s.run_id, l.run_id) AS run_id,
        -- LOC: prefer scc
        COALESCE(s.loc, l.loc) AS loc,
        -- Complexity: prefer lizard
        COALESCE(l.complexity, s.complexity) AS complexity,
        -- Track source
        CASE WHEN s.file_id IS NOT NULL THEN 'scc' ELSE 'lizard' END AS loc_source,
        CASE WHEN l.file_id IS NOT NULL THEN 'lizard' ELSE 'scc' END AS complexity_source
    FROM scc_metrics s
    FULL OUTER JOIN lizard_metrics l
        ON s.file_id = l.file_id AND s.run_id = l.run_id
)

SELECT * FROM merged
```

#### Trend Analysis (Phase 2+)

Trend analysis is a first-class feature for DD and execution risk assessment—not just current state, but trajectory.

**Supported Trends:**

| Trend Metric | Description | Use Case |
|--------------|-------------|----------|
| Technical Debt Velocity | Rate of debt increase/decrease | Investment planning |
| Hotspot Volatility | Churn × complexity over time | Risk prioritization |
| Security Debt Accumulation | New CVEs / unresolved high-severity findings | Compliance tracking |
| Coverage Trajectory | Test coverage trend | Quality assessment |

**Gating Conditions:**
Trend analysis SHALL be produced only when:
1. `stable_file_fingerprint` is present, OR
2. Trend is computed on directory/aggregate level (not file-level)

**Confidence Warnings:**
The system SHALL emit `TREND_CONFIDENCE_LOW` when:
- Identity mapping between runs is incomplete (< 80% files matched)
- Time window contains fewer than 3 comparable runs
- Significant structural changes detected (> 30% file churn)

**Implementation Note:**
Trend analysis depends on stable file identity (Phase 2). Until then, only directory-level and repo-wide trends are reliable.

### 3.4 LLM-Based Evaluation

#### Evaluation With Ground Truth + LLM Support

Evaluation is grounded in synthetic repos with explicit ground truth. Programmatic checks MUST include precision/recall where feasible. LLM judges are supplemental on real repos and must provide actionable improvement proposals on synthetic scenarios:

```python
class ToolEvaluator:
    """Hybrid evaluation for tool runs."""

    def evaluate_run(self, run_id: str) -> EvaluationResult:
        """Evaluate a complete run with programmatic checks and optional LLM judges."""

        # 1. Collect tool outputs
        outputs = self.collect_outputs(run_id)

        # 2. Build evaluation context
        context = EvaluationContext(
            repo_metadata=self.get_repo_metadata(run_id),
            tool_outputs=outputs,
            data_quality_scores=self.get_quality_scores(run_id),
            execution_metrics=self.get_execution_metrics(run_id)
        )

        # 3. Run programmatic checks (precision/recall where feasible)
        programmatic = self.run_programmatic_checks(context)

        # 4. Run dimension judges (supplemental on real repos)
        dimensions = [
            CompletenessJudge(),   # Did tools analyze expected files?
            ConsistencyJudge(),    # Do metrics agree across tools?
            PlausibilityJudge(),   # Are values reasonable?
            ActionabilityJudge(),  # Are findings actionable?
        ]

        scores = {}
        for judge in dimensions:
            scores[judge.dimension] = judge.evaluate(context)

        return EvaluationResult(
            run_id=run_id,
            overall_score=self.compute_overall(scores),
            dimension_scores=scores,
            recommendations=self.generate_recommendations(scores, programmatic)
        )
```

#### Evaluation Dimensions

| Dimension | Description | Example Checks |
|-----------|-------------|----------------|
| **Completeness** | Did tools analyze all expected files? | Files in layout vs files in tool outputs |
| **Consistency** | Do metrics agree across tools? | scc LOC vs lizard NLOC within 10% |
| **Plausibility** | Are values reasonable for this repo type? | Complexity distribution matches language norms |
| **Actionability** | Are findings specific and fixable? | Vulnerability has CVE, severity, location |

#### LLM Judge Implementation

```python
class ConsistencyJudge(BaseJudge):
    """Judge cross-tool metric consistency."""

    dimension = "consistency"

    PROMPT_TEMPLATE = """
    Evaluate the consistency of metrics across analysis tools for this repository.

    Repository: {repo_name}
    Language Distribution: {languages}

    SCC Metrics:
    - Total Files: {scc_files}
    - Total Lines: {scc_lines}

    Lizard Metrics:
    - Total Files: {lizard_files}
    - Total NLOC: {lizard_nloc}

    Consider:
    1. Are file counts consistent? (Some variance expected due to filtering)
    2. Are LOC/NLOC values comparable? (Within 20% is acceptable)
    3. Are there unexplained large discrepancies?

    Provide:
    - consistency_score: 0-100
    - issues: List any significant inconsistencies
    - explanation: Why you scored this way
    """

    def evaluate(self, context: EvaluationContext) -> JudgeResult:
        prompt = self.PROMPT_TEMPLATE.format(
            repo_name=context.repo_metadata.name,
            languages=context.repo_metadata.languages,
            scc_files=context.tool_outputs.get('scc', {}).get('file_count'),
            scc_lines=context.tool_outputs.get('scc', {}).get('total_lines'),
            lizard_files=context.tool_outputs.get('lizard', {}).get('file_count'),
            lizard_nloc=context.tool_outputs.get('lizard', {}).get('total_nloc'),
        )

        response = self.call_llm(prompt)
        return self.parse_response(response)
```

#### LLM Evaluation Guardrails

LLM evaluation can be misinterpreted as authoritative truth unless properly bounded. All LLM evaluations are **advisory** and must be reproducible.

**Required Fields for Every Judge Result:**

| Field | Type | Purpose |
|-------|------|---------|
| `judge_name` | string | Identifier for the judge type |
| `judge_version` | string | Semver for judge implementation |
| `model_id` | string | LLM model used (e.g., `claude-sonnet-4-20250514`) |
| `prompt_template_id` | string | Reference to stored prompt template |
| `prompt_resolved` | string | Actual prompt sent to LLM (with variables interpolated) |
| `inputs_digest` | string | SHA-256 hash of structured inputs |
| `output_schema_version` | string | Schema version for result structure |
| `timestamp` | ISO 8601 | When evaluation was performed |

**Guardrail Rules:**

1. **Advisory Labeling**: All LLM evaluation outputs SHALL be labeled with `claim_type: EVALUATION`
2. **Reproducibility**: Prompts and inputs SHALL be stored for replay
3. **Non-Destructive**: LLM evaluation SHALL NEVER overwrite factual marts; it only annotates them
4. **Schema Validation**: All evaluation results SHALL pass strict JSON schema validation
5. **Versioning**: Prompt templates SHALL be versioned; changes require new version

**Evaluation Result Schema (Required Structure):**

```python
@dataclass
class EvaluationResultEnvelope:
    # Identity
    run_id: UUID
    repo_id: UUID
    commit: str
    timestamp: datetime

    # Judge metadata
    judge_name: str
    judge_version: str
    model_id: str

    # Reproducibility
    prompt_template_id: str
    prompt_resolved: str  # Stored for replay
    inputs_digest: str    # SHA-256 of inputs

    # Result
    dimension: str
    score: float          # 0-5 scale
    confidence: float     # 0-1
    reasoning: str
    recommendations: List[str]
    evidence_refs: List[str]
```

> **Implementation Note:** Add evaluation result schema and prompt persistence to LLM judge framework.

### 3.5 Data Quality Framework

#### Quality Check Levels

```python
class DataQualityChecker:
    """Multi-level data quality checking."""

    def check_json_output(self, tool_name: str, output_path: str) -> QualityReport:
        """Level 1: Raw JSON validation."""
        checks = [
            SchemaValidationCheck(tool_name),      # Valid against schema
            RequiredFieldsCheck(tool_name),        # All required fields present
            FileIdFormatCheck(),                   # file_id matches f-xxx pattern
            MetadataCompletenessCheck(),           # run_id, commit, etc. present
        ]
        return self.run_checks(checks, output_path)

    def check_landing_zone(self, run_id: str, tool_name: str) -> QualityReport:
        """Level 2: Landing zone validation."""
        checks = [
            ForeignKeyCheck('file_id', 'lz_layout_files'),  # References exist
            UniqueConstraintCheck(tool_name),                  # No duplicates
            DataTypeCheck(tool_name),                          # Correct types
            RangeCheck(tool_name),                              # Values in bounds
        ]
        return self.run_checks(checks, run_id, tool_name)

    def check_source_of_truth(self, run_id: str) -> QualityReport:
        """Level 3: Source of truth validation."""
        checks = [
            CrossToolConsistencyCheck(),           # Metrics agree
            CompletenessCheck(),                   # All files covered
            ConflictResolutionCheck(),             # Conflicts logged
            BusinessRuleCheck(),                   # Domain rules pass
        ]
        return self.run_checks(checks, run_id)
```

#### Quality Score Computation

```python
@dataclass
class QualityScore:
    completeness: float    # 0-1: % of expected data present
    validity: float        # 0-1: % of data passing validation
    consistency: float     # 0-1: Cross-tool agreement
    timeliness: float      # 0-1: Data freshness

    @property
    def overall(self) -> float:
        weights = {
            'completeness': 0.3,
            'validity': 0.3,
            'consistency': 0.25,
            'timeliness': 0.15
        }
        return sum(
            getattr(self, dim) * weight
            for dim, weight in weights.items()
        )
```

### 3.6 Out-of-Process Execution

All execution modes produce artifacts only. Outputs must be collected and validated before import.

#### Canonical Ingestion Rule

> **CRITICAL:** Tools MUST NOT write to DuckDB in any mode.
> Tools MUST produce **artifacts only** (JSON + metadata).
> The SoT engine performs **all validation and ingestion** into DuckDB.

| Execution Mode | DuckDB Access | Rationale |
|----------------|---------------|-----------|
| **LOCAL** | Artifacts only → local import | Single ingestion path |
| **DOCKER** | Artifacts only → local import | Isolation, reproducibility |
| **VM** | Artifacts only → local import | Full isolation, untrusted code |

#### Execution Flow (Docker Mode)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR (Host)                                 │
│                                                                              │
│  1. Prepare inputs (repo_path, run_id, etc.)                                │
│  2. Start container with volume mounts                                       │
│  3. Wait for completion or timeout                                           │
│  4. Collect outputs from mounted volume                                      │
│  5. Validate and import locally                                              │
└─────────────────────────────────────────────────────────────────────────────┘
        │                                           ▲
        │ docker run                                │ outputs
        ▼                                           │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONTAINER                                          │
│                                                                              │
│  /repo         ← mounted (read-only)                                        │
│  /output       ← mounted (read-write)                                       │
│  /db           ← NOT mounted (isolated)                                     │
│                                                                              │
│  Tool writes:                                                                │
│  • /output/{tool}/output.json                                               │
│  • /output/{tool}/metadata.json                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Output Collection

```python
@dataclass
class OutputCollection:
    """Collected outputs from remote execution."""
    tool_name: str
    execution_id: str
    json_output: Path           # output.json
    metadata: Path              # metadata.json
    logs: Optional[Path]        # execution logs
    exit_code: int
    duration_seconds: float


class OutputCollector:
    """Collects outputs from remote execution environments."""

    def collect_from_docker(
        self,
        container_id: str,
        tool_name: str,
        local_output_dir: Path
    ) -> OutputCollection:
        """Collect outputs from a Docker container."""

        # Copy outputs from container to local
        container_output = f"/output/{tool_name}"
        subprocess.run([
            "docker", "cp",
            f"{container_id}:{container_output}",
            str(local_output_dir)
        ], check=True)

        # Parse metadata for execution info
        metadata_path = local_output_dir / tool_name / "metadata.json"
        metadata = json.loads(metadata_path.read_text())

        return OutputCollection(
            tool_name=tool_name,
            execution_id=container_id,
            json_output=local_output_dir / tool_name / "output.json",
            metadata=metadata_path,
            logs=local_output_dir / tool_name / "execution.log",
            exit_code=metadata.get("exit_code", 0),
            duration_seconds=metadata.get("duration_seconds", 0)
        )

    def collect_from_vm(
        self,
        vm_host: str,
        tool_name: str,
        local_output_dir: Path
    ) -> OutputCollection:
        """Collect outputs from a VM via SSH/SCP."""
        # Similar to Docker but uses scp/rsync
        pass
```

#### Validation Before Import

All outputs are validated locally before import:

```python
class PreImportValidator:
    """Validates collected outputs before importing to DuckDB."""

    def validate(self, collection: OutputCollection) -> ValidationResult:
        """Run all pre-import validations."""
        checks = []

        # 1. Schema validation
        checks.append(self._validate_json_schema(collection))

        # 2. Path normalization (ensure relative paths)
        checks.append(self._validate_paths(collection))

        # 3. Metadata completeness
        checks.append(self._validate_metadata(collection))

        # 4. Data integrity (no truncation, valid JSON)
        checks.append(self._validate_integrity(collection))

        return ValidationResult(
            passed=all(c.passed for c in checks),
            checks=checks
        )

    def _validate_paths(self, collection: OutputCollection) -> CheckResult:
        """Ensure all paths follow the normalization rules."""
        output = json.loads(collection.json_output.read_text())

        for file_entry in output.get("data", {}).get("files", []):
            path = file_entry.get("path", "")
            if not isinstance(path, str) or not path.strip():
                return CheckResult(
                    name="path_normalization",
                    passed=False,
                    message="Missing or empty path value"
                )
            invalid = (
                path.startswith("/")
                or path.startswith("./")
                or ".." in path
                or (len(path) >= 2 and path[1] == ":")
                or "\\" in path
                or path.endswith("/")
            )
            if invalid:
                return CheckResult(
                    name="path_normalization",
                    passed=False,
                    message=f"Invalid path format: {path}"
                )
        return CheckResult(name="path_normalization", passed=True)
```

#### Local Import Phase

The import phase always runs on the orchestrator host:

```python
class LocalImporter:
    """Imports validated outputs to local DuckDB."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)

    def import_tool_output(
        self,
        collection: OutputCollection,
        run_id: uuid.UUID,
        repo_id: uuid.UUID
    ) -> ImportResult:
        """Import a tool's output to DuckDB landing zone."""

        # 1. Parse JSON output
        output = json.loads(collection.json_output.read_text())

        # 2. Import to landing zone tables (JSON only)
        self._import_from_json(output, run_id, repo_id)

        # 3. Record import metadata
        self._record_import(collection, run_id)

        return ImportResult(
            tool_name=collection.tool_name,
            run_id=run_id,
            records_imported=len(output.get("data", {}).get("files", [])),
            import_timestamp=datetime.utcnow()
        )

```

#### Complete Out-of-Process Flow

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         OUT-OF-PROCESS FLOW                                │
└───────────────────────────────────────────────────────────────────────────┘

1. DISPATCH
   Orchestrator → Container/VM
   • repo_path (mounted)
   • run_id, commit, branch
   • output_path (mounted)

2. EXECUTE (Remote)
   Tool runs in isolation
   • Writes JSON to mounted output

3. COLLECT
   Orchestrator ← Container/VM
   • docker cp / scp
   • Retrieve all outputs

4. VALIDATE (Local)
   • Schema validation
   • Path normalization
   • Data integrity

5. IMPORT (Local)
   • Insert to DuckDB landing zone
   • Always runs on orchestrator host
   • Never remote DuckDB writes

6. CLEANUP
   • Remove container/VM
   • Archive raw outputs (optional)
```

### 3.7 Run Lifecycle & Retention

Landing zone storage scales linearly with runs × tools × artifacts. Without lifecycle management, storage costs become unsustainable.

#### Lifecycle Stages

| Stage | Contents | Retention Purpose |
|-------|----------|-------------------|
| **Stage A: Raw Artifacts** | JSON outputs, metadata, logs | Debugging, replay, audit |
| **Stage B: Landing Zone** | `tool_{name}_*` tables for each run_id | Pre-transformation data |
| **Stage C: Source of Truth** | Unified marts and rollups | Query and analysis |

#### Retention Policy (Configurable Defaults)

| Stage | Default TTL | Notes |
|-------|-------------|-------|
| Raw Artifacts | 30-90 days | Configurable per environment |
| Landing Zone | 7-30 days after SoT materialization | Eligible for deletion once SoT complete |
| Source of Truth | Per business policy (often "long") | Primary query layer |
| Evaluation Summaries | Long retention, tied to SoT | Required for historical comparison |

#### Cold Storage Strategy

Upon successful SoT materialization, landing zone data SHALL be eligible for cold storage export:

**Cold Storage Format:**
```
Parquet partitioned by:
  /{repo_id}/{run_id}/{tool_name}/{commit}/
```

**Lifecycle Flow:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    RUN LIFECYCLE FLOW                            │
│                                                                  │
│  1. COLLECTION                                                   │
│     → Raw artifacts written to Stage A                           │
│     → Landing zone tables populated (Stage B)                    │
│                                                                  │
│  2. TRANSFORMATION                                               │
│     → dbt transforms landing → SoT (Stage C)                     │
│     → Quality tests run                                          │
│                                                                  │
│  3. RETENTION EVALUATION (TTL trigger)                           │
│     → Stage A: Archive to cold storage OR delete                 │
│     → Stage B: Export to Parquet cold storage → delete tables    │
│     → Stage C: Retain per policy                                 │
│                                                                  │
│  4. COLD STORAGE QUERY (on demand)                               │
│     → DuckDB can query Parquet directly if needed                │
└─────────────────────────────────────────────────────────────────┘
```

> **Implementation Note:** Add TTL enforcement and cold storage export to orchestrator backlog.

---

## 4. Tool Building Guide

### 4.1 Tool Requirements

Every compliant tool must:

| Requirement | Description |
|-------------|-------------|
| **R1** | Accept standard inputs (repo_path, commit, run_id, output_path) |
| **R2** | Produce JSON output conforming to envelope schema |
| **R3** | Implement tool-specific JSON schema |
| **R4** | Emit repo-relative paths following the normalization rules |
| **R5** | Provide a minimal, versioned landing schema contract in the SoT engine |
| **R6** | Include a migration playbook for schema changes |
| **R7** | Include execution metadata |
| **R8** | Handle errors gracefully with partial results |

### 4.2 Tool Directory Structure

```
src/tools/{tool-name}/
├── Makefile                    # Standard targets
├── README.md                   # Usage documentation
├── BLUEPRINT.md                # Architecture decisions
├── EVAL_STRATEGY.md            # Evaluation approach
├── pyproject.toml              # Dependencies
├── schemas/
│   └── output.schema.json      # Tool-specific schema
├── scripts/
│   ├── analyze.py              # Main analysis script
│   ├── evaluate.py             # Evaluation runner
│   └── checks/                 # Programmatic checks
│       ├── __init__.py
│       ├── accuracy.py
│       └── coverage.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── eval-repos/
│   ├── synthetic/              # Generated test repos
│   └── real/                   # Real OSS repos
├── evaluation/
│   ├── ground-truth/           # Expected results
│   └── llm/
│       └── judges/             # LLM judge implementations
```

Landing schema contracts and migrations live in the SoT engine under `src/collector/collector/persistence/specs/`.

### 4.3 Makefile Template

```makefile
# Required targets
.PHONY: setup analyze evaluate clean test validate

# Tool metadata
TOOL_NAME := my-tool
TOOL_VERSION := 1.0.0
SCHEMA_VERSION := 1

# Standard inputs (provided by orchestrator)
REPO_PATH ?=
BRANCH ?= main
COMMIT ?= HEAD
RUN_ID ?= $(shell uuidgen)
OUTPUT_PATH ?= ./output
CONFIG_FILE ?=

setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .

analyze:
	@if [ -n "$(CONFIG_FILE)" ]; then \
		.venv/bin/python scripts/analyze.py --config "$(CONFIG_FILE)"; \
	else \
		test -n "$(REPO_PATH)" || (echo "REPO_PATH required" && exit 1); \
			.venv/bin/python scripts/analyze.py \
				--repo-path "$(REPO_PATH)" \
				--branch "$(BRANCH)" \
				--commit "$(COMMIT)" \
				--run-id "$(RUN_ID)" \
				--output-path "$(OUTPUT_PATH)"; \
		fi

evaluate:
	.venv/bin/python scripts/evaluate.py \
		--output-path "$(OUTPUT_PATH)" \
		--run-id "$(RUN_ID)"

test:
	.venv/bin/pytest tests/ -v

validate:
	# Validate output against schema
	.venv/bin/python -m jsonschema \
		-i "$(OUTPUT_PATH)/$(TOOL_NAME)/output.json" \
		schemas/output.schema.json
	# Run compliance checks
	python src/tool-compliance/tool_compliance.py \
		--root . \
		--out-json /tmp/tool_compliance_report.json \
		--out-md /tmp/tool_compliance_report.md

clean:
	rm -rf output/ .venv/ __pycache__/
```

**Makefile Parameters:**

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_PATH` | (required*) | Absolute path to repository |
| `BRANCH` | `main` | Branch to analyze |
| `COMMIT` | `HEAD` | Commit SHA (resolved by orchestrator) |
| `RUN_ID` | auto-generated | UUID for this run |
| `OUTPUT_PATH` | `./output` | Directory for tool outputs |
| `CONFIG_FILE` | (none) | Path to config JSON file (overrides other params) |

*`REPO_PATH` is required unless `CONFIG_FILE` is provided.

### 4.4 Analysis Script Template

```python
#!/usr/bin/env python3
"""Main analysis script for {tool-name}."""

import argparse
import json
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Optional

from jsonschema import validate, ValidationError

# Load schemas
ENVELOPE_SCHEMA = json.loads(Path("schemas/envelope.schema.json").read_text())
TOOL_SCHEMA = json.loads(Path("schemas/output.schema.json").read_text())

TOOL_NAME = "my-tool"
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "1"
EXPECTED_CONFIG_VERSION = "1.0.0"


@dataclass
class ToolConfig:
    """Validated tool configuration."""
    repo_path: str
    branch: str
    commit: str
    run_id: str
    output_path: str
    tool_specific: Dict[str, Any]


class ConfigVersionError(Exception):
    """Raised when config schema version is incompatible."""
    pass


def load_and_validate_config(config_path: str) -> ToolConfig:
    """Load config file and validate against schema."""
    schema_path = Path(__file__).parent.parent / "schemas" / "config.schema.json"
    schema = json.loads(schema_path.read_text())
    config = json.loads(Path(config_path).read_text())

    # Check schema version compatibility (MAJOR must match)
    config_version = config.get("schema_version", "0.0.0")
    config_major = int(config_version.split(".")[0])
    expected_major = int(EXPECTED_CONFIG_VERSION.split(".")[0])

    if config_major != expected_major:
        raise ConfigVersionError(
            f"Config schema version {config_version} incompatible with "
            f"expected version {EXPECTED_CONFIG_VERSION}. MAJOR version must match."
        )

    # Validate against JSON Schema
    try:
        validate(config, schema)
    except ValidationError as e:
        raise ValueError(f"Config validation failed: {e.message}")

    params = config["parameters"]
    return ToolConfig(
        repo_path=params["repo_path"],
        branch=params.get("branch", "main"),
        commit=params.get("commit", "HEAD"),
        run_id=params["run_id"],
        output_path=params["output_path"],
        tool_specific=params.get("tool_specific", {})
    )


def resolve_commit(repo_path: str, ref: str) -> str:
    """Resolve HEAD or branch name to full commit SHA."""
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=repo_path, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ValueError(f"Cannot resolve ref: {ref}")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to config JSON file")
    parser.add_argument("--repo-path", help="Absolute path to repository")
    parser.add_argument("--branch", default="main", help="Branch being analyzed")
    parser.add_argument("--commit", default="HEAD", help="Commit SHA or HEAD")
    parser.add_argument("--run-id", help="UUID for this run")
    parser.add_argument("--output-path", help="Output directory")
    args = parser.parse_args()

    # Load config file if provided
    config: Optional[ToolConfig] = None
    if args.config:
        config = load_and_validate_config(args.config)
        print(f"Loaded config from {args.config}")

    # Merge CLI args with config (CLI takes precedence)
    repo_path = args.repo_path or (config.repo_path if config else None)
    branch = args.branch if args.branch != "main" else (config.branch if config else "main")
    commit = args.commit if args.commit != "HEAD" else (config.commit if config else "HEAD")
    run_id_str = args.run_id or (config.run_id if config else None)
    output_path = args.output_path or (config.output_path if config else None)

    # Validate required fields
    if not repo_path:
        parser.error("--repo-path is required (or provide --config)")
    if not run_id_str:
        parser.error("--run-id is required (or provide --config)")
    if not output_path:
        parser.error("--output-path is required (or provide --config)")

    # Always resolve commit to full SHA (never store HEAD)
    if commit == "HEAD":
        commit = resolve_commit(repo_path, branch)

    run_id = uuid.UUID(run_id_str)
    output_dir = Path(output_path) / TOOL_NAME
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run analysis
    start_time = datetime.utcnow()
    try:
        results = analyze(repo_path, config.tool_specific if config else {})
        exit_code = 0
        errors = []
    except Exception as e:
        results = {}
        exit_code = 1
        errors = [{"code": "ANALYSIS_FAILED", "message": str(e)}]

    duration = (datetime.utcnow() - start_time).total_seconds()

    # Build output
    output = {
        "metadata": {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "run_id": str(run_id),
            "branch": branch,
            "commit": commit,  # Always full SHA, never HEAD
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration,
            "exit_code": exit_code,
            "files_analyzed": len(results.get("files", [])),
            "schema_version": SCHEMA_VERSION
        },
        "data": results,
        "errors": errors
    }

    # Validate output
    validate(output, ENVELOPE_SCHEMA)
    validate(output["data"], TOOL_SCHEMA)

    # Write JSON output
    output_file = output_dir / "output.json"
    output_file.write_text(json.dumps(output, indent=2))

    print(f"Analysis complete: {output_file}")


def analyze(repo_path: str, tool_specific: Dict[str, Any] = None) -> dict:
    """Run the actual analysis.

    Args:
        repo_path: Path to repository
        tool_specific: Tool-specific configuration from config file
    """
    files = []
    tool_specific = tool_specific or {}

    # Example: Use tool-specific config
    exclude_patterns = tool_specific.get("exclude_patterns", [])

    for file_path in Path(repo_path).rglob("*"):
        if file_path.is_dir():
            continue
        relative_path = file_path.relative_to(repo_path).as_posix()
        # Skip excluded files
        if any(fnmatch(relative_path, p) for p in exclude_patterns):
            continue

        # Analyze each file
        metrics = analyze_file(file_path)

        files.append({
            "path": relative_path,
            **metrics
        })

    return {
        "files": files,
        "summary": compute_summary(files)
    }


if __name__ == "__main__":
    main()
```

### 4.5 vulcan-core Package

Duplication of shared primitives (severity mapping, LLM client, schema helpers) across tools creates drift and slows delivery. The `vulcan-core` package provides standardized primitives with strict boundaries.

#### Allowed Contents

| Module | Purpose | Example |
|--------|---------|---------|
| `schema.py` | Schema loading + validation utilities | `load_schema()`, `validate_output()` |
| `severity.py` | Severity mapping and normalization | `SeverityMapper.normalize()` |
| `llm_client.py` | LLM client abstraction with retry/backoff | `LLMClient.invoke()` |
| `artifact_io.py` | Artifact IO helpers (JSON only) | `write_output()` |
| `dataclasses.py` | Shared dataclasses/enums | `ToolInput`, `ExecutionMetadata` |
| `logging.py` | Structured logging helpers | `get_logger()`, `log_metric()` |

#### Explicitly Excluded

| Content Type | Reason |
|--------------|--------|
| Tool-specific analysis logic | Violates tool independence |
| Orchestrator logic | Belongs in collector |
| Cross-tool "knowledge" | Tools must remain independent |
| Database models | Tools don't share DB access |

#### Usage Pattern

```python
# Tools SHOULD depend on vulcan-core for standardized primitives
from vulcan_core.schema import load_schema, validate_output
from vulcan_core.severity import SeverityMapper
from vulcan_core.llm_client import LLMClient
from vulcan_core.dataclasses import ToolInput, ExecutionMetadata
```

> **Implementation Note:** Create `vulcan-core` package with strict API boundaries. Add to `src/shared/vulcan_core/`.

### 4.6 CI Compliance Gates

Manual enforcement does not scale; contract drift will accumulate without automated gates. Every tool merge REQUIRES passing compliance checks.

#### Minimum CI Gates (Non-Negotiable)

| Gate | Validation | Failure Action |
|------|------------|----------------|
| Output Envelope Schema | JSON validates against `envelope.schema.json` | Block merge |
| Tool Schema | JSON validates against `{tool}/schemas/output.schema.json` | Block merge |
| Makefile Targets | `setup`, `analyze`, `evaluate`, `clean` exist | Block merge |
| Metadata Fields | `run_id`, `commit`, `timestamp` present | Block merge |
| Path Format | No absolute paths in outputs | Block merge |
| Path Rules | Paths follow the required normalization rules | Block merge |

#### CI Pipeline Example

```yaml
# .github/workflows/tool-compliance.yml
name: Tool Compliance
on:
  pull_request:
    paths:
      - 'src/tools/**'

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Compliance Validator
        run: |
          python src/tool-compliance/tool_compliance.py \
            --out-json /tmp/tool_compliance_report.json \
            --out-md /tmp/tool_compliance_report.md
      - name: Schema Validation
        run: |
          python -m jsonschema -i output.json schemas/envelope.schema.json
```

#### Compliance Status Badge

Tools SHOULD display compliance status:
```markdown
![Compliance](https://img.shields.io/badge/vulcan--compliance-passing-green)
```

> **Implementation Note:** Add GitHub Action for compliance validator. A tool SHALL NOT be merged unless compliant.

### 4.7 Tool Compliance Validation

```bash
# Run compliance across all tools
python src/tool-compliance/tool_compliance.py \
  --root . \
  --run-analysis --run-evaluate --run-llm \
  --out-json /tmp/tool_compliance_report.json \
  --out-md /tmp/tool_compliance_report.md
```

---

## 5. Data Flow

### 5.1 Complete Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           1. ORCHESTRATION                                   │
│                                                                              │
│  collector collect https://github.com/owner/repo --branch main              │
│                                                                              │
│  1. Clone repository                                                         │
│  2. Resolve branch → commit SHA (never store HEAD)                          │
│  3. Generate run_id, repo_id                                                │
│  4. Select execution mode (LOCAL/DOCKER/VM)                                 │
│  5. Create output directory                                                  │
│  6. Initialize DuckDB with landing zone schemas                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     2. EXECUTION MODE SELECTION                              │
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                        │
│  │   LOCAL     │   │   DOCKER    │   │     VM      │                        │
│  │  (threads)  │   │ (containers)│   │ (full VMs)  │                        │
│  ├─────────────┤   ├─────────────┤   ├─────────────┤                        │
│  │ max: 2      │   │ max: 8+     │   │ max: 16+    │                        │
│  │ isolation:  │   │ isolation:  │   │ isolation:  │                        │
│  │ none        │   │ container   │   │ full        │                        │
│  └─────────────┘   └─────────────┘   └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         3. PHASE 0: FOUNDATION                               │
│                                                                              │
│  Run layout-scanner with inputs:                                             │
│  • repo_path, branch, commit, run_id, output_path                           │
│                                                                              │
│  Outputs:                                                                    │
│  • JSON: output/layout-scanner/output.json                                  │
│  • Metadata: output/layout-scanner/metadata.json                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      4. PHASE 1-3: TOOL EXECUTION                            │
│                                                                              │
│  For each tool (parallel within mode limits):                                │
│  • Invoke: make analyze REPO_PATH=... BRANCH=... COMMIT=... RUN_ID=...      │
│  • Tool writes JSON to output/{tool}/output.json                            │
│  • Tool writes metadata to output/{tool}/metadata.json                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      5. OUTPUT COLLECTION (if remote)                        │
│                                                                              │
│  For DOCKER/VM modes:                                                        │
│  • Collect outputs from containers/VMs                                       │
│  • docker cp / scp to local output directory                                 │
│  • Retrieve JSON + metadata                                                  │
│                                                                              │
│  For LOCAL mode: Skip (outputs already local)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     6. VALIDATION (always local)                             │
│                                                                              │
│  Pre-import validation:                                                      │
│  • Schema validation (envelope + tool-specific)                              │
│  • Path normalization (ensure relative paths)                                │
│  • Data integrity checks (no truncation, valid JSON)                         │
│                                                                              │
│  Failed validation → log error, continue with other tools                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    7. LOCAL IMPORT (always local)                            │
│                                                                              │
│  For each validated tool output:                                             │
│  • Import JSON to DuckDB landing zone via adapters                          │
│  • tool_{name}_* tables                                                      │
│  • Record import metadata                                                    │
│                                                                              │
│  IMPORTANT: Import always runs on orchestrator host                          │
│  (tools never write directly to DuckDB in any mode)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    8. LANDING ZONE VALIDATION                                │
│                                                                              │
│  For each tool's landing zone tables:                                        │
│  • Validate foreign keys (file_id → lz_layout_files)                      │
│  • Check data types and constraints                                          │
│  • Detect duplicates                                                         │
│  • Compute Level 2 quality scores                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  9. SOURCE OF TRUTH TRANSFORMATION                           │
│                                                                              │
│  dbt run --select staging intermediate marts                                 │
│                                                                              │
│  Transformations:                                                            │
│  • staging: Clean/standardize landing zone data                              │
│  • intermediate: Apply conflict resolution, compute derived metrics          │
│  • marts: Create final unified tables                                        │
│                                                                              │
│  Quality tests:                                                              │
│  • dbt test (all configured assertions)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         10. LLM EVALUATION                                   │
│                                                                              │
│  collector evaluate --run-id {run_id} --llm-eval                            │
│                                                                              │
│  Dimensions:                                                                 │
│  • Completeness: Did tools cover expected files?                            │
│  • Consistency: Do metrics agree across tools?                              │
│  • Plausibility: Are values reasonable?                                     │
│  • Actionability: Are findings useful?                                      │
│                                                                              │
│  Output: evaluation_results, recommendations                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Execution Mode Comparison

```
                    LOCAL                 DOCKER                 VM
                    ─────                 ──────                 ──
Parallelism         2 threads             8+ containers          16+ VMs
Isolation           None                  Container              Full VM
DuckDB Access       Artifacts only        Artifacts only         Artifacts only
Output Location     Local filesystem      Mounted volume         Remote + copy
Use Case            Development           Production/CI          Enterprise/Security
```

### 5.3 Query Flow

```sql
-- User query: Get high-complexity files with security issues

SELECT
    f.relative_path,
    m.complexity,
    m.loc,
    v.severity,
    v.cve_id,
    v.description
FROM file_metrics m
JOIN lz_layout_files f ON m.file_id = f.file_id AND m.run_id = f.run_id
LEFT JOIN vulnerabilities v ON m.file_id = v.file_id AND m.run_id = v.run_id
WHERE m.run_id = '{run_id}'
  AND m.complexity > 20
  AND v.severity IN ('CRITICAL', 'HIGH')
ORDER BY m.complexity DESC;
```

---

## 6. Pros and Cons

### 6.1 Advantages

| Advantage | Description |
|-----------|-------------|
| **Tool Independence** | Tools can be developed, tested, and deployed independently |
| **Clear Contracts** | JSON schemas define exact input/output expectations |
| **Graceful Degradation** | System produces useful results even with tool failures |
| **Audit Trail** | Landing zones preserve original tool outputs |
| **Flexible Queries** | dbt models support complex cross-tool queries |
| **LLM-Ready** | Evaluation uses synthetic ground truth; LLM judges are supplemental |
| **Extensibility** | New tools only need to implement the standard interface |

### 6.2 Disadvantages

| Disadvantage | Description | Mitigation |
|--------------|-------------|------------|
| **Schema Maintenance** | Each tool maintains its own schema | Provide schema validation tooling |
| **Duplication** | Some code duplicated across tools | Publish shared libraries (path_normalizer, schema_validator) |
| **Complexity** | More moving parts than monolithic approach | Strong documentation, validation tools |
| **Storage** | Landing zone + source of truth = 2x storage | Use DuckDB views where possible |
| **Learning Curve** | dbt/dagster requires learning | Provide templates and examples |
| **Consistency** | Tools might diverge over time | Compliance validator in CI |

### 6.3 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema drift | Medium | High | Versioned schemas, compatibility tests |
| Tool non-compliance | Medium | Medium | Automated compliance validation in CI |
| dbt performance | Low | Medium | Incremental models, materialization strategy |
| LLM evaluation variability | Medium | Low | Multiple judges, confidence scoring |
| Layout registry bottleneck | Low | High | Caching, async access patterns |

---

- Adapters still need maintenance

### 7.2 Alternative B: Event-Driven Architecture

Tools publish events, consumers process asynchronously:

```
Tool → Event (Kafka/Redis) → Event Processor → DuckDB
```

**Pros:**
- True decoupling
- Real-time processing
- Horizontal scaling

**Cons:**
- Infrastructure overhead (Kafka/Redis)
- Eventual consistency complexity
- Overkill for batch analysis

### 7.3 Alternative C: GraphQL Federation

Each tool exposes a GraphQL API, federated for queries:

```
Tool → GraphQL Schema → Apollo Federation → Unified API
```

**Pros:**
- Rich query capabilities
- Type safety
- Schema composition

**Cons:**
- Requires tools to run as services
- Not suited for batch analysis
- Higher runtime complexity

### 7.4 Recommendation

**Proceed with the proposed architecture** (Section 2) because:

1. It addresses the core issues (coupling, validation, evaluation)
2. Complexity is manageable with good tooling
3. dbt is proven for data transformation
4. Incremental migration is possible

---

## 8. Migration Strategy

### 8.1 Phase 1: Foundation (Weeks 1-2)

1. **Define global envelope schema**
2. **Create tool-specific schema template**
3. **Implement internal layout registry interface**
4. **Set up dbt project structure**
5. **Create compliance validator**

### 8.2 Phase 2: Pilot Tools (Weeks 3-4)

1. **Migrate layout-scanner** to new architecture
2. **Migrate scc** as first consumer
3. **Implement staging and mart models for scc**
4. **Validate end-to-end flow**

### 8.3 Phase 3: Production Tools (Weeks 5-8)

1. **Migrate remaining production tools** (lizard, semgrep)
2. **Add LLM evaluation judges**
3. **Implement quality dashboard**
4. **Update collector CLI**

### 8.4 Phase 4: Full Migration (Weeks 9-12)

1. **Migrate all tools**
2. **Deprecate legacy adapters**
3. **Performance optimization**
4. **Documentation completion**

---

## 9. Open Questions

### 9.1 Technical Decisions Needed

| Question | Options | Recommendation |
|----------|---------|----------------|
| **dbt vs Dagster?** | dbt (SQL-focused) vs Dagster (Python-focused) | Start with dbt, evaluate Dagster for orchestration needs |
| **Landing zone retention?** | Keep forever vs TTL | Keep last N runs per repo (configurable) |
| **Schema versioning?** | Strict vs flexible | Strict major versions, flexible minor |
| **Layout API transport?** | In-process vs gRPC | In-process Python module initially |

### 9.2 Process Questions

| Question | Considerations |
|----------|----------------|
| **Who maintains tool schemas?** | Tool developers vs central team |
| **How often to run compliance?** | Every commit vs release gates |
| **Ground truth for evaluation?** | Required synthetic ground truth + optional real-world baselines |

### 9.3 Scope Questions

| Question | Options |
|----------|---------|
| **Which tools to migrate first?** | Production tier vs most used |
| **Incremental analysis support?** | Phase 1 vs later |
| **Real-time streaming?** | Out of scope vs Phase 2 |

---

## 10. Learnings & Best Practices

This section documents what we've learned from building and operating Project Vulcan. These learnings inform architectural decisions and should guide future development.

### 10.1 What Works Well

#### Evaluation Framework Success

The three-layer evaluation approach has proven highly effective:

| Layer | Purpose | Speed | When to Use |
|-------|---------|-------|-------------|
| **Programmatic Checks** | Fast, deterministic validation | Milliseconds | Always runs first |
| **LLM Judges** | Nuanced qualitative assessment | Seconds | When checks pass |
| **Scorecard Aggregation** | Unified PASS/FAIL decision | Milliseconds | Final verdict |

This layering provides fast feedback for obvious issues while reserving expensive LLM calls for nuanced cases.

#### Tool Registry Pattern

The metadata-driven tool registry enables flexible execution:

```python
# Tool registry metadata pattern (proven effective)
ToolMetadata(
    name="scc",
    phase=1,                    # Execution phase (0=foundation, 1=independent, 2=git-dependent)
    languages=["*"],            # Supported languages (* = all)
    timeout_seconds=60,         # Per-tool timeout
    parallel_safe=True,         # Can run concurrently
    depends_on=["layout-scanner"]  # Phase dependencies
)
```

**Why it works:** 28 tools with varied requirements can be orchestrated uniformly. Adding a new tool requires only metadata, not orchestration changes.

#### Adapter Base Infrastructure

The base adapter pattern reduces code duplication:

| Component | Purpose | Usage |
|-----------|---------|-------|
| `PathMatchStats` | Track file matching accuracy | All 22 extractors |
| `SeverityMapper` | Normalize severity levels | Security tools |
| `normalize_path()` | Canonical path handling | Cross-tool correlation |

**Lesson learned:** Provide well-designed base infrastructure and tools will use it correctly.

#### Role-Based Export Sizing

The tiered export system matches stakeholder needs:

| Role | Size Target | Content Focus | Proven Value |
|------|-------------|---------------|--------------|
| Executive | ~50KB | Red flags, investment concerns | Fits in one screen |
| Tech Lead | ~150KB | Architecture issues, priorities | Fits in Claude context |
| Engineer | ~400KB | Specific files, code examples | Actionable details |

**Why it works:** Different stakeholders have different attention budgets. One size doesn't fit all.

#### LLM Judge Framework

The standardized `JudgeResult` dataclass provides consistency:

```python
@dataclass
class JudgeResult:
    score: float           # 0-5 scale
    confidence: float      # 0-1 confidence in score
    reasoning: str         # Explanation (for debugging)
    recommendations: List[str]  # Actionable suggestions
    evidence: List[str]    # Supporting evidence
```

**Lesson learned:** Standardized outputs enable aggregation, comparison, and A/B testing of different judge implementations.

#### Guidance Engine Maturity

The guidance-engine component (90% maturity) demonstrates what "done" looks like:

| Metric | Value | Significance |
|--------|-------|--------------|
| Files | 4,038 | Comprehensive implementation |
| Documentation files | 16 | Well-documented |
| Test files | 149 | Heavily tested |
| MCP Integration | Yes | First-class AI agent support |

**What made it succeed:** Clear scope, focused purpose (hotspot detection + context packs), and dedicated investment.

### 10.2 Patterns That Proved Effective

#### Three-Layer Evaluation Pattern

The evaluation framework follows a consistent pattern across all tools:

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: Programmatic Checks              │
│  • Fast (milliseconds)                                       │
│  • Deterministic (same input → same output)                  │
│  • Catches obvious issues (missing data, schema violations)  │
│  • Always runs                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (if passed)
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 2: LLM Judges                       │
│  • Slower (seconds)                                          │
│  • Nuanced (understands context, intent)                     │
│  • Evaluates qualitative aspects (actionability, clarity)    │
│  • Runs only when programmatic checks pass                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: Scorecard Aggregation            │
│  • Weighted dimension scores                                 │
│  • Critical vs supporting dimensions                         │
│  • Unified PASS/FAIL decision                                │
│  • Threshold-based (e.g., 3.0 for production)               │
└─────────────────────────────────────────────────────────────┘
```

#### Weighted Dimension Scoring

The scorecard uses weighted dimensions:

| Dimension Type | Weight Range | Examples |
|----------------|--------------|----------|
| **Critical** | 25-35% | Accuracy, Completeness |
| **Important** | 15-25% | Actionability, Coverage |
| **Supporting** | 10-15% | Performance, Edge Cases |

**Key insight:** Not all dimensions are equal. A tool with perfect performance but broken accuracy is useless.

#### Evidence-Based LLM Judging

LLM judges collect evidence before invocation:

```python
# Pattern: Collect evidence before LLM call
evidence = {
    "sample_issues": issues[:10],
    "path_match_rate": stats.match_rate,
    "severity_distribution": severity_counts,
    "missing_required_fields": missing_fields
}

# LLM sees structured evidence, not raw data
result = judge.evaluate(evidence)
```

**Why it works:** LLMs make better judgments when presented with pre-structured evidence rather than raw data dumps.

#### Phase-Based Tool Execution

Tools execute in phases based on dependencies:

| Phase | Tools | Depends On |
|-------|-------|------------|
| **0** | layout-scanner | None (foundation) |
| **1** | scc, lizard, semgrep, trivy | layout-scanner |
| **2** | git-fame, git-of-theseus | git history |
| **3** | depends, ndepend | language-specific context |

**Why it works:** Phases enable parallelism within phases while respecting dependencies across phases.

#### Canonical File ID Pattern

The `f-{sha256-prefix}` pattern enables cross-tool correlation:

```
File: src/auth/login.py
Layout Scanner ID: f-a1b2c3d4e5f6
```

All tools reference files by this ID, not by path. This survives:
- Path changes (file moves)
- Case sensitivity differences
- Path separator variations (Windows vs Unix)

### 10.3 What Needs Improvement

#### Technical Debt Accumulation

Current state: **540+ TODOs across components**

| Component | TODO Count | Priority |
|-----------|------------|----------|
| Collector | ~150 | High |
| Aggregator | ~80 | Medium |
| Guidance Engine | ~120 | Medium |
| Tools (28 total) | ~190 | Varies |

**Recommendation:** Establish a TODO budget—new TODOs require removing old ones.

#### Shared Infrastructure Gaps

The `src/shared/` directory contains only 3 files:

| Current | Missing (Should Exist) |
|---------|------------------------|
| scorecard.py | base_adapter.py |
| | severity_mapper.py |
| | path_utils.py |
| | llm_client.py |
| | judge_base.py |

**Impact:** Each tool reimplements common patterns, leading to inconsistency and maintenance burden.

**Recommendation:** Extract proven patterns from guidance-engine and collector into shared infrastructure.

#### Ground Truth Schema Fragmentation

Each tool defines its own ground truth data but MUST conform to a shared schema:

| Tool | Ground Truth Format | Issues |
|------|---------------------|--------|
| sonarqube | Custom JSON schema | No validation |
| depends | Different custom schema | Inconsistent fields |
| semgrep | Another format | No relationship |

**Recommendation:** Define a shared ground truth schema in `src/shared/schemas/ground-truth.schema.json`.

#### LLM Invocation Inconsistency

Different tools call LLMs differently:

```python
# Tool A pattern
response = anthropic.messages.create(...)

# Tool B pattern
response = llm_client.invoke(...)

# Tool C pattern
response = await async_llm_call(...)
```

**Impact:** A/B testing prompt variants requires touching each tool individually.

**Recommendation:** Centralize LLM invocation in shared infrastructure with built-in A/B testing hooks.

#### Missing Integration Tests

Current state: No end-to-end integration tests covering the full pipeline.

| Test Type | Coverage | Gap |
|-----------|----------|-----|
| Unit tests | Good | — |
| Tool-level tests | Good | — |
| Component integration | Minimal | Needs work |
| Full pipeline E2E | None | Critical gap |

**Recommendation:** Create `tests/integration/test_full_pipeline.py` that runs a mini-repository through all 28 tools.

#### Aggregator Adoption

The aggregator has low adoption (only 7 imports across the codebase):

**Root cause:** Not packaged as an installable module.

**Recommendation:** Add `pyproject.toml` to aggregator and publish as internal package.

### 10.4 Key Architectural Decisions

This section documents decisions that worked well vs those that need revision.

#### Decisions That Worked

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **DuckDB as storage** | Embedded, fast, SQL-compatible | Excellent developer experience |
| **Makefile interface** | Universal, tool-agnostic | All 28 tools use consistently |
| **JSON Schema validation** | Catches errors at generation | Reduced debugging time |
| **Phase-based execution** | Enables parallelism | 4x faster than sequential |
| **file_id correlation** | Cross-tool data joining | Unified analysis possible |

#### Decisions That Need Revision

| Decision | Problem | Proposed Fix |
|----------|---------|--------------|
| **Adapter in collector** | Tight coupling | Move to tool-level |
| **No shared LLM client** | Inconsistent invocation | Create shared module |
| **Ground truth per-tool** | Schema fragmentation | Unified schema |
| **Manual TODO tracking** | Debt accumulates | Automated enforcement |

#### Decisions Still Under Evaluation

| Decision | Trade-off | Current Stance |
|----------|-----------|----------------|
| **dbt vs Dagster** | SQL-focused vs Python-focused | Start with dbt |
| **gRPC vs in-process** | Performance vs simplicity | In-process for now |
| **Strict vs flexible schemas** | Safety vs iteration speed | Strict major, flexible minor |

---

## 11. V1 Non-Goals

To prevent scope creep and maintain focus, the following are explicitly **out of scope** for V1:

| Non-Goal | Rationale | Future Phase |
|----------|-----------|--------------|
| **Cross-company benchmarking warehouse** | Requires stable scoring, legal review, anonymization | Phase 3+ |
| **Full longitudinal file-level trends** | Depends on stable file identity | Phase 2+ |
| **Real-time streaming ingestion** | Batch analysis sufficient for DD use case | Phase 3+ |
| **Multi-tenant hosted SaaS** | Auth, billing, tenant isolation complexity | Out of scope |
| **Agent autonomy beyond context-packs** | Focus on information production, not action | Future |

### Benchmarking Gate Conditions

Benchmarking is explicitly maturity-gated and requires:
1. Stable scoring definitions across versions
2. Robust confidence semantics
3. Legal/compliance review (anonymization, data sharing agreements)
4. Minimum 6 months of stable schema evolution

### Scope Boundaries

V1 delivers:
- ✅ Single-tenant, on-premises analysis
- ✅ Batch processing of repositories
- ✅ Evidence-backed findings with epistemic labels
- ✅ Context packs for AI agent consumption
- ✅ Decision-relevant outputs for PE DD teams

V1 does NOT deliver:
- ❌ Hosted multi-tenant service
- ❌ Real-time continuous monitoring
- ❌ Cross-company benchmarks
- ❌ Autonomous agent actions
- ❌ File-level trend analysis (directory-level only)

---

## 12. Change Log

This section documents changes introduced by the Architecture V2 Amendments (v1.0).

| Category | Amendment | Impact |
|----------|-----------|--------|
| **1. Product Anchoring** | Added Primary Product Persona (PE Tech DD) | Clarifies V1 focus |
| **2. Truth Model** | Introduced epistemic labeling (FACT/DERIVED/EVALUATION) | Prevents false authority |
| **3. Identity** | Added phase-aware stable file fingerprint | Enables future trends |
| **4. Lifecycle** | Added TTL retention and cold storage strategy | Controls storage growth |
| **5. Remote Execution** | Formalized "artifacts-only remote execution" | Resolves DuckDB ambiguity |
| **6. LLM Guardrails** | Added versioned, replayable evaluation requirements | Ensures reproducibility |
| **7. Developer Velocity** | Added `vulcan-core` utilities; enforced CI gates | Reduces drift |
| **8. Roadmap Hygiene** | Maturity-gated benchmarking; added V1 non-goals | Prevents scope creep |

### Amendment Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-24 | Initial amendment pack incorporating review feedback |

---

## Appendix A: Schema Examples

### A.1 Complete Output Example (scc)

```json
{
  "metadata": {
    "tool_name": "scc",
    "tool_version": "3.1.0",
    "run_id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "660e8400-e29b-41d4-a716-446655440001",
    "branch": "main",
    "commit": "abc123def456789012345678901234567890abcd",
    "timestamp": "2026-01-24T10:30:00Z",
    "duration_seconds": 12.5,
    "exit_code": 0,
    "files_analyzed": 150,
    "schema_version": "1"
  },
  "data": {
    "files": [
      {
        "file_id": "f-a1b2c3d4e5f6",
        "language": "Python",
        "lines": 250,
        "code": 180,
        "comments": 45,
        "blanks": 25,
        "complexity": 15
      }
    ],
    "summary": {
      "total_files": 150,
      "total_lines": 25000,
      "languages": [
        {"name": "Python", "files": 100, "lines": 20000},
        {"name": "JavaScript", "files": 50, "lines": 5000}
      ]
    }
  },
  "errors": []
}
```

### A.2 DuckDB Landing Zone Schema (scc, SoT Engine)

```sql
-- collector persistence landing schema for scc

CREATE TABLE IF NOT EXISTS tool_scc_files (
    run_id UUID NOT NULL,
    repo_id UUID NOT NULL,
    file_id VARCHAR NOT NULL,
    language VARCHAR NOT NULL,
    lines INTEGER NOT NULL,
    code INTEGER NOT NULL,
    comments INTEGER NOT NULL,
    blanks INTEGER NOT NULL,
    complexity INTEGER,
    bytes BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, file_id)
);

CREATE TABLE IF NOT EXISTS tool_scc_summary (
    run_id UUID NOT NULL,
    repo_id UUID NOT NULL,
    language VARCHAR NOT NULL,
    file_count INTEGER NOT NULL,
    total_lines INTEGER NOT NULL,
    total_code INTEGER NOT NULL,
    total_comments INTEGER NOT NULL,
    total_blanks INTEGER NOT NULL,
    avg_complexity DOUBLE,
    PRIMARY KEY (run_id, language)
);

-- Index for efficient joins with layout
CREATE INDEX IF NOT EXISTS idx_tool_scc_files_file_id
ON tool_scc_files(file_id);
```

---

## Appendix B: dbt Model Examples

### B.1 Staging Model

```sql
-- models/staging/stg_scc_files.sql

WITH source AS (
    SELECT * FROM {{ source('landing', 'tool_scc_files') }}
    WHERE run_id = '{{ var("run_id") }}'
),

renamed AS (
    SELECT
        run_id,
        repo_id,
        file_id,
        language,
        lines AS total_lines,
        code AS code_lines,
        comments AS comment_lines,
        blanks AS blank_lines,
        complexity,
        created_at
    FROM source
)

SELECT * FROM renamed
```

### B.2 Mart Model

```sql
-- models/marts/file_metrics.sql

WITH scc AS (
    SELECT * FROM {{ ref('stg_scc_files') }}
),

lizard AS (
    SELECT * FROM {{ ref('stg_lizard_functions') }}
),

layout AS (
    SELECT * FROM {{ ref('stg_layout_files') }}
),

merged AS (
    SELECT
        l.run_id,
        l.repo_id,
        l.file_id,
        l.relative_path,
        l.language,
        l.category,
        -- LOC metrics (prefer scc)
        COALESCE(s.total_lines, lz.nloc) AS loc,
        s.code_lines AS sloc,
        s.comment_lines,
        s.blank_lines,
        -- Complexity (prefer lizard)
        COALESCE(lz.max_ccn, s.complexity) AS max_complexity,
        lz.avg_ccn AS avg_complexity,
        lz.function_count,
        -- Source tracking
        CASE WHEN s.file_id IS NOT NULL THEN 'scc' ELSE 'lizard' END AS loc_source,
        CASE WHEN lz.file_id IS NOT NULL THEN 'lizard' ELSE 'scc' END AS complexity_source
    FROM layout l
    LEFT JOIN scc s ON l.file_id = s.file_id AND l.run_id = s.run_id
    LEFT JOIN lizard lz ON l.file_id = lz.file_id AND l.run_id = lz.run_id
    WHERE l.category = 'source'
)

SELECT * FROM merged
```

---

## Appendix C: Compliance Checklist

### Tool Compliance Checklist

- [ ] **Structure**
  - [ ] Makefile with setup, analyze, evaluate, clean targets
  - [ ] README.md with usage documentation
  - [ ] schemas/output.schema.json
  - [ ] schemas/config.schema.json (versioned input config schema)
  - [ ] collector persistence spec for tool + schema_version
  - [ ] scripts/analyze.py
  - [ ] scripts/evaluate.py
  - [ ] tests/ directory with unit tests

- [ ] **Input Contract**
  - [ ] Accepts --config (path to config JSON file)
  - [ ] Accepts --repo-path (required unless --config provided)
  - [ ] Accepts --branch (default: main)
  - [ ] Accepts --commit (default: HEAD, resolved to SHA)
  - [ ] Accepts --run-id (required unless --config provided)
  - [ ] Accepts --output-path (required unless --config provided)
  - [ ] Accepts --db-path (required)

- [ ] **Configuration Contract**
  - [ ] Validates config against schemas/config.schema.json
  - [ ] Checks schema_version compatibility (MAJOR version match)
  - [ ] Logs validation errors with clear messages
  - [ ] CLI arguments override config file values
  - [ ] Ignores unknown fields with warning (forward compatibility)

- [ ] **Output Contract**
  - [ ] Produces JSON conforming to envelope schema
  - [ ] Produces JSON conforming to tool schema
  - [ ] Emits repo-relative paths following normalization rules
  - [ ] Includes metadata (tool_name, version, run_id, branch, commit, etc.)
  - [ ] Commit is full SHA (never HEAD)
  - [ ] No direct DuckDB writes (SoT engine handles persistence)

- [ ] **Quality**
  - [ ] Handles errors gracefully with partial results
  - [ ] Includes execution duration
  - [ ] Logs errors in errors array
  - [ ] Unit test coverage > 50%

---

## Appendix D: SQL Query Catalog

This appendix documents key SQL query patterns from the collector's repository layer. These queries inform the design of the Source of Truth engine and demonstrate common data access patterns across the unified schema.

### D.1 File-Level Insight Queries

These queries combine metrics from multiple tools to surface file-level insights.

#### Coverage Gap Analysis

Identifies files with low test coverage AND high complexity—prime refactoring candidates.

```sql
-- Files with coverage gaps: low coverage + high complexity = risk
SELECT
    fm.file_path,
    fm.line_coverage_pct,
    fm.max_ccn,
    fm.loc,
    CASE
        WHEN fm.line_coverage_pct < 50 AND fm.max_ccn > 15 THEN 'critical'
        WHEN fm.line_coverage_pct < 70 AND fm.max_ccn > 10 THEN 'high'
        WHEN fm.line_coverage_pct < 80 THEN 'medium'
        ELSE 'low'
    END AS risk_level
FROM file_metrics fm
WHERE fm.run_id = ?
  AND fm.line_coverage_pct IS NOT NULL
  AND fm.max_ccn IS NOT NULL
ORDER BY
    CASE
        WHEN fm.line_coverage_pct < 50 AND fm.max_ccn > 15 THEN 1
        WHEN fm.line_coverage_pct < 70 AND fm.max_ccn > 10 THEN 2
        WHEN fm.line_coverage_pct < 80 THEN 3
        ELSE 4
    END,
    fm.max_ccn DESC;
```

**Pattern:** CASE expression for risk categorization and custom ordering.

#### Maintenance Burden Query

Identifies files that are both complex and frequently changed—high maintenance burden.

```sql
-- High maintenance burden: complex + volatile files
SELECT
    fm.file_path,
    fm.max_ccn,
    fm.churn_count,
    fm.unique_authors,
    (fm.max_ccn * fm.churn_count) AS burden_score
FROM file_metrics fm
WHERE fm.run_id = ?
  AND fm.max_ccn > 10
  AND fm.churn_count > 5
ORDER BY burden_score DESC
LIMIT 50;
```

**Pattern:** Computed column for composite scoring.

#### File Metrics with Registry Enrichment

Joins file metrics with layout scanner data for complete file context.

```sql
-- Enriched file metrics with layout context
SELECT
    fr.file_id,
    fr.relative_path,
    fr.language,
    fr.category,
    fm.loc,
    fm.sloc,
    fm.max_ccn,
    fm.function_count,
    fm.line_coverage_pct,
    dr.directory_id,
    dr.relative_path AS directory_path
FROM file_registry fr
JOIN file_metrics fm ON fr.file_id = fm.file_id AND fr.run_id = fm.run_id
JOIN directory_registry dr ON fr.directory_id = dr.directory_id AND fr.run_id = dr.run_id
WHERE fr.run_id = ?
  AND fr.category = 'source'
ORDER BY fm.max_ccn DESC;
```

**Pattern:** Multi-table JOIN using file_id as canonical identifier.

### D.2 Security Aggregation Queries

These queries aggregate and score security findings across tools.

#### Security Debt Scoring

Computes a weighted security debt score per file, prioritizing critical issues.

```sql
-- Security debt scoring: weighted sum of security issues
WITH file_vulns AS (
    SELECT
        file_path,
        COUNT(*) FILTER (WHERE severity = 'critical') AS critical_vulns,
        COUNT(*) FILTER (WHERE severity = 'high') AS high_vulns,
        COUNT(*) FILTER (WHERE severity = 'medium') AS medium_vulns,
        COUNT(*) AS total_vulns
    FROM vulnerabilities
    WHERE run_id = ?
    GROUP BY file_path
),
file_secrets AS (
    SELECT
        file_path,
        COUNT(*) AS secret_count,
        COUNT(*) FILTER (WHERE entropy > 4.5) AS high_entropy_secrets
    FROM secrets
    WHERE run_id = ?
    GROUP BY file_path
)
SELECT
    COALESCE(v.file_path, s.file_path) AS file_path,
    COALESCE(v.critical_vulns, 0) AS critical_vulns,
    COALESCE(v.high_vulns, 0) AS high_vulns,
    COALESCE(s.secret_count, 0) AS secret_count,
    COALESCE(s.high_entropy_secrets, 0) AS high_entropy_secrets,
    -- Weighted security debt score
    (COALESCE(v.critical_vulns, 0) * 5 +
     COALESCE(v.high_vulns, 0) * 2 +
     COALESCE(v.medium_vulns, 0) * 1 +
     COALESCE(s.high_entropy_secrets, 0) * 3 +
     COALESCE(s.secret_count, 0) * 1) AS security_debt_score
FROM file_vulns v
FULL OUTER JOIN file_secrets s ON v.file_path = s.file_path
ORDER BY security_debt_score DESC;
```

**Pattern:** FILTER clause for conditional counting, FULL OUTER JOIN for complete coverage, weighted scoring with domain-specific multipliers.

#### Vulnerability Severity Summary

Aggregates vulnerabilities by severity with proper ordering.

```sql
-- Vulnerability summary by severity
SELECT
    severity,
    COUNT(*) AS issue_count,
    COUNT(DISTINCT file_path) AS affected_files,
    COUNT(DISTINCT cve_id) AS unique_cves
FROM vulnerabilities
WHERE run_id = ?
GROUP BY severity
ORDER BY CASE severity
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
    ELSE 5
END;
```

**Pattern:** CASE expression for custom severity ordering (critical → high → medium → low).

### D.3 Cross-Tool Composite Queries

These queries combine data from multiple tools to compute unified risk scores.

#### Composite Risk Scoring

The most important query pattern—normalizes metrics across different scales and applies weighted scoring.

```sql
-- Composite risk scoring: normalize and weight multiple metrics
WITH vuln_counts AS (
    SELECT file_path, COUNT(*) as vuln_count
    FROM vulnerabilities
    WHERE run_id = ?
    GROUP BY file_path
),
file_risk AS (
    SELECT
        fm.file_path,
        fm.max_ccn,
        fm.total_fan_in,
        -- Normalize each metric to 0-1 scale using window functions
        COALESCE(fm.max_ccn, 0)::DOUBLE / NULLIF(MAX(fm.max_ccn) OVER(), 0) AS ccn_norm,
        COALESCE(fm.total_fan_in, 0)::DOUBLE / NULLIF(MAX(fm.total_fan_in) OVER(), 0) AS fan_in_norm,
        COALESCE(vc.vuln_count, 0)::DOUBLE / NULLIF(MAX(vc.vuln_count) OVER(), 0) AS vuln_norm,
        -- Coverage gap (inverted: 100% coverage = 0 gap)
        (100 - COALESCE(fm.line_coverage_pct, 100)) / 100.0 AS coverage_gap
    FROM file_metrics fm
    LEFT JOIN vuln_counts vc ON fm.file_path = vc.file_path
    WHERE fm.run_id = ?
)
SELECT
    file_path,
    max_ccn,
    total_fan_in,
    -- Weighted composite: complexity 30%, coupling 25%, vulns 30%, coverage 15%
    ROUND(
        ccn_norm * 0.30 +
        fan_in_norm * 0.25 +
        vuln_norm * 0.30 +
        coverage_gap * 0.15,
        4
    ) AS composite_risk
FROM file_risk
WHERE ccn_norm > 0 OR fan_in_norm > 0 OR vuln_norm > 0
ORDER BY composite_risk DESC
LIMIT 100;
```

**Pattern:** Window functions for normalization (metric/MAX(metric)), weighted sum for composite score, NULLIF to prevent division by zero.

#### Dead Code Detection

Finds symbols with no incoming calls (fan-in = 0)—potential dead code.

```sql
-- Dead code candidates: exported symbols with no callers
SELECT
    cs.symbol_name,
    cs.symbol_type,
    cs.file_path,
    cs.line_number,
    COALESCE(caller_count, 0) AS caller_count
FROM code_symbols cs
LEFT JOIN (
    SELECT callee_name, COUNT(DISTINCT caller_name) AS caller_count
    FROM symbol_calls
    WHERE run_id = ?
    GROUP BY callee_name
) sc ON cs.symbol_name = sc.callee_name
WHERE cs.run_id = ?
  AND cs.is_exported = true
  AND COALESCE(caller_count, 0) = 0
  AND cs.symbol_type IN ('function', 'class', 'method')
ORDER BY cs.file_path, cs.line_number;
```

**Pattern:** LEFT JOIN with aggregation for optional relationship detection.

#### File ID Coverage Report

Data quality check—ensures all tools reference valid file IDs from layout scanner.

```sql
-- File ID coverage: which tools have data for which files
SELECT
    fr.file_id,
    fr.relative_path,
    CASE WHEN fm.file_id IS NOT NULL THEN 1 ELSE 0 END AS has_metrics,
    CASE WHEN cs.file_id IS NOT NULL THEN 1 ELSE 0 END AS has_symbols,
    CASE WHEN v.file_id IS NOT NULL THEN 1 ELSE 0 END AS has_vulns,
    CASE WHEN cd.file_id IS NOT NULL THEN 1 ELSE 0 END AS has_coverage
FROM file_registry fr
LEFT JOIN (SELECT DISTINCT run_id, file_id FROM file_metrics) fm
    ON fr.run_id = fm.run_id AND fr.file_id = fm.file_id
LEFT JOIN (SELECT DISTINCT run_id, file_id FROM code_symbols) cs
    ON fr.run_id = cs.run_id AND fr.file_id = cs.file_id
LEFT JOIN (SELECT DISTINCT run_id, file_id FROM vulnerabilities) v
    ON fr.run_id = v.run_id AND fr.file_id = v.file_id
LEFT JOIN (SELECT DISTINCT run_id, file_id FROM coverage_details) cd
    ON fr.run_id = cd.run_id AND fr.file_id = cd.file_id
WHERE fr.run_id = ?
ORDER BY fr.relative_path;
```

**Pattern:** Multiple LEFT JOINs with CASE expressions for presence checking, useful for data quality dashboards.

### D.4 Call Graph Traversal Queries

These queries traverse the call graph to compute blast radius and dependency metrics.

#### Blast Radius (Transitive Callers)

Uses recursive CTE to find all transitive callers of a symbol—measures impact of changes.

```sql
-- Blast radius: all transitive callers of a symbol
WITH RECURSIVE call_chain AS (
    -- Base case: direct callers
    SELECT
        caller_name,
        callee_name,
        file_path,
        1 AS depth
    FROM symbol_calls
    WHERE run_id = ?
      AND callee_name = ?  -- Target symbol

    UNION ALL

    -- Recursive case: callers of callers
    SELECT
        sc.caller_name,
        sc.callee_name,
        sc.file_path,
        cc.depth + 1
    FROM symbol_calls sc
    JOIN call_chain cc ON sc.callee_name = cc.caller_name
    WHERE cc.depth < ?  -- Max depth limit (e.g., 5)
      AND sc.run_id = ?
)
SELECT
    caller_name,
    file_path,
    MIN(depth) AS min_depth,
    COUNT(*) AS path_count
FROM call_chain
GROUP BY caller_name, file_path
ORDER BY min_depth, caller_name;
```

**Pattern:** Recursive CTE for transitive closure, depth limiting to prevent infinite loops, MIN(depth) to find shortest path.

#### Fan-In/Fan-Out Aggregation

Computes coupling metrics per symbol.

```sql
-- Symbol coupling metrics: fan-in and fan-out
SELECT
    cs.symbol_name,
    cs.symbol_type,
    cs.file_path,
    COALESCE(fan_out.count, 0) AS fan_out,
    COALESCE(fan_in.count, 0) AS fan_in,
    -- Instability metric: fan_out / (fan_in + fan_out)
    CASE
        WHEN COALESCE(fan_out.count, 0) + COALESCE(fan_in.count, 0) = 0 THEN 0
        ELSE ROUND(
            COALESCE(fan_out.count, 0)::DOUBLE /
            (COALESCE(fan_out.count, 0) + COALESCE(fan_in.count, 0)),
            3
        )
    END AS instability
FROM code_symbols cs
LEFT JOIN (
    SELECT caller_name, COUNT(DISTINCT callee_name) AS count
    FROM symbol_calls WHERE run_id = ?
    GROUP BY caller_name
) fan_out ON cs.symbol_name = fan_out.caller_name
LEFT JOIN (
    SELECT callee_name, COUNT(DISTINCT caller_name) AS count
    FROM symbol_calls WHERE run_id = ?
    GROUP BY callee_name
) fan_in ON cs.symbol_name = fan_in.callee_name
WHERE cs.run_id = ?
ORDER BY (COALESCE(fan_in.count, 0) + COALESCE(fan_out.count, 0)) DESC;
```

**Pattern:** Separate aggregations for different relationship directions, instability metric calculation.

#### Directory Symbol Rollups

Aggregates symbol metrics to directory level for architectural analysis.

```sql
-- Directory-level symbol rollups
SELECT
    dr.directory_id,
    dr.relative_path,
    COUNT(DISTINCT cs.symbol_name) AS symbol_count,
    SUM(COALESCE(cs.fan_in, 0)) AS total_fan_in,
    SUM(COALESCE(cs.fan_out, 0)) AS total_fan_out,
    AVG(COALESCE(cs.ccn, 0)) AS avg_complexity,
    MAX(COALESCE(cs.ccn, 0)) AS max_complexity
FROM directory_registry dr
JOIN file_registry fr ON dr.directory_id = fr.directory_id AND dr.run_id = fr.run_id
JOIN code_symbols cs ON fr.file_id = cs.file_id AND fr.run_id = cs.run_id
WHERE dr.run_id = ?
GROUP BY dr.directory_id, dr.relative_path
ORDER BY total_fan_in + total_fan_out DESC;
```

**Pattern:** Hierarchical aggregation through JOINs, multiple aggregate functions.

#### Directory Metric Rollups (Direct vs Recursive)

Directory metric rollups are materialized in DuckDB via dbt as two variants:

- `rollup_*_directory_recursive_distributions`: includes files from the full subtree of each directory.
- `rollup_*_directory_direct_distributions`: includes only files directly in the directory (no descendants).

Each rollup distribution includes:
- counts and basic stats: `value_count`, `min_value`, `max_value`, `avg_value`, `stddev_value`
- quantiles: `p25_value`, `p50_value` (also `median_value`), `p75_value`, `p90_value`, `p95_value`, `p99_value`
- shape/dispersion: `skewness_value`, `kurtosis_value`, `cv_value`, `iqr_value`
- inequality/concentration: `gini_value`, `theil_value`, `hoover_value`, `palma_value`
- share metrics: `top_10_pct_share`, `top_20_pct_share`, `bottom_50_pct_share`

dbt tests enforce:
- distribution values are in valid ranges
- recursive rollups never report fewer files than direct rollups for the same run/directory/metric

### D.5 Run Management Queries

These queries support the orchestration layer for managing analysis runs.

#### Latest Run for Repository

Finds the most recent completed run for a repository.

```sql
-- Get latest completed run for a repository
SELECT
    run_id,
    repo_id,
    branch,
    commit,
    started_at,
    completed_at,
    status,
    tools_succeeded,
    tools_failed
FROM collection_runs
WHERE repo_id = ?
  AND status = 'completed'
ORDER BY completed_at DESC
LIMIT 1;
```

**Pattern:** Simple filtering with ORDER BY for "most recent" queries.

#### Incremental Analysis Baseline Lookup

Finds the baseline run for incremental analysis based on commit ancestry.

```sql
-- Find baseline for incremental analysis
SELECT
    cr.run_id,
    cr.commit,
    cr.completed_at
FROM collection_runs cr
WHERE cr.repo_id = ?
  AND cr.status = 'completed'
  AND cr.branch = ?
  AND cr.completed_at < ?
ORDER BY cr.completed_at DESC
LIMIT 1;
```

**Pattern:** Temporal ordering for finding previous runs on same branch.

#### Copy Unchanged Metrics (Incremental)

Copies metrics from previous run for files that haven't changed.

```sql
-- Copy unchanged file metrics from previous run
INSERT INTO file_metrics (
    run_id, repo_id, file_id, file_path, loc, sloc, max_ccn,
    function_count, line_coverage_pct, source_tool, created_at
)
SELECT
    ?::UUID AS run_id,  -- New run_id
    fm.repo_id,
    fm.file_id,
    fm.file_path,
    fm.loc,
    fm.sloc,
    fm.max_ccn,
    fm.function_count,
    fm.line_coverage_pct,
    fm.source_tool,
    CURRENT_TIMESTAMP
FROM file_metrics fm
WHERE fm.run_id = ?  -- Previous run_id
  AND fm.file_id NOT IN (
      SELECT file_id FROM changed_files WHERE run_id = ?
  );
```

**Pattern:** INSERT...SELECT for bulk copy with exclusion subquery.

### D.6 Query Pattern Summary

| Pattern | Use Case | Example |
|---------|----------|---------|
| **CASE ordering** | Custom sort orders (severity, risk) | `ORDER BY CASE severity WHEN 'critical' THEN 1...` |
| **Window normalization** | Scale metrics 0-1 | `metric / NULLIF(MAX(metric) OVER(), 0)` |
| **Weighted scoring** | Composite risk | `m1 * 0.30 + m2 * 0.25 + m3 * 0.30 + m4 * 0.15` |
| **Recursive CTE** | Transitive relationships | `WITH RECURSIVE call_chain AS (... UNION ALL ...)` |
| **FILTER clause** | Conditional counting | `COUNT(*) FILTER (WHERE severity = 'critical')` |
| **FULL OUTER JOIN** | Complete coverage | Combining vulns + secrets |
| **LEFT JOIN + COALESCE** | Optional relationships | Metrics with/without coverage |
| **Hierarchical rollup** | Directory aggregations | `JOIN directory → file → symbol` |

### D.7 Source of Truth Design Implications

These query patterns inform the Source of Truth engine design:

1. **Normalization layer needed**: Queries frequently normalize metrics to 0-1 scale. The Source of Truth should pre-compute normalized values.

2. **Composite scores as first-class metrics**: Risk scores combining multiple dimensions should be materialized, not computed on every query.

3. **Recursive CTE support required**: DuckDB handles this well, but blast radius queries may need caching for performance.

4. **Cross-tool JOINs are common**: The file_id correlation strategy is validated—every query uses it.

5. **Temporal queries matter**: Incremental analysis requires efficient "latest before X" queries.

6. **Directory rollups should be materialized**: Computing them on every query is expensive; dbt can maintain them.

---

## Appendix E: Success Patterns Catalog

This appendix documents proven patterns from Project Vulcan's development. These patterns have been validated through production use and should be followed when building new components.

### E.1 Evaluation Framework Pattern

The evaluation framework follows a three-layer architecture that balances speed, cost, and accuracy.

#### Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    INPUT: Tool Output JSON                          │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                 LAYER 1: PROGRAMMATIC CHECKS                        │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Schema Check │  │ Required     │  │ Range        │              │
│  │              │  │ Fields Check │  │ Validation   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  Output: List[CheckResult]                                          │
│  Speed: < 100ms                                                     │
│  Cost: $0                                                           │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼ (if all checks pass)
┌────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: LLM JUDGES                              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Accuracy     │  │ Completeness │  │ Actionability│              │
│  │ Judge        │  │ Judge        │  │ Judge        │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  Output: List[JudgeResult]                                          │
│  Speed: 2-5 seconds each                                            │
│  Cost: ~$0.01 per judge                                             │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                 LAYER 3: SCORECARD AGGREGATION                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Weighted Score = Σ (dimension_weight × dimension_score)      │   │
│  │                                                               │   │
│  │ Critical dimensions: 25-35% weight                           │   │
│  │ Important dimensions: 15-25% weight                          │   │
│  │ Supporting dimensions: 10-15% weight                         │   │
│  │                                                               │   │
│  │ Decision: score >= 3.0 → PASS, else FAIL                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Output: EvaluationResult (score, decision, breakdown)              │
└────────────────────────────────────────────────────────────────────┘
```

#### Implementation Example

```python
# From src/shared/evaluation/scorecard.py

@dataclass
class DimensionScore:
    name: str
    weight: float           # 0.0 to 1.0
    score: float            # 0 to 5
    source: str             # "check" or "judge"
    details: Optional[str]

@dataclass
class EvaluationResult:
    overall_score: float    # 0 to 5
    decision: str           # "PASS" or "FAIL"
    dimensions: List[DimensionScore]
    threshold: float        # Decision threshold (default: 3.0)

    @property
    def weighted_score(self) -> float:
        return sum(d.weight * d.score for d in self.dimensions)

def evaluate_tool_output(output: dict, ground_truth: Optional[dict] = None) -> EvaluationResult:
    """Three-layer evaluation pattern."""

    # Layer 1: Programmatic checks (fast, deterministic)
    check_results = run_programmatic_checks(output)
    if any(c.severity == "critical" for c in check_results):
        return EvaluationResult(
            overall_score=0.0,
            decision="FAIL",
            dimensions=[DimensionScore("schema_validity", 0.3, 0.0, "check", "Critical check failed")]
        )

    # Layer 2: LLM judges (slower, nuanced)
    judge_results = run_llm_judges(output, ground_truth)

    # Layer 3: Scorecard aggregation
    return aggregate_to_scorecard(check_results, judge_results)
```

#### When to Use Each Layer

| Situation | Layer | Rationale |
|-----------|-------|-----------|
| Schema violations | Programmatic | Deterministic, fast |
| Missing required fields | Programmatic | Deterministic, fast |
| Value out of range | Programmatic | Deterministic, fast |
| Accuracy assessment | LLM Judge | Requires context understanding |
| Actionability evaluation | LLM Judge | Subjective quality |
| Completeness checking | Hybrid | Count programmatic, quality LLM |

### E.2 Tool Integration Pattern

This pattern describes how to integrate a new analysis tool into the Vulcan pipeline.

#### Standard Tool Directory Structure

```
src/tools/{tool-name}/
├── Makefile                    # Standard targets: setup, analyze, evaluate, clean
├── README.md                   # Tool documentation
├── pyproject.toml              # Python packaging (if applicable)
├── requirements.txt            # Dependencies
│
├── scripts/
│   ├── analyze.py              # Main entry point
│   ├── export.py               # JSON output generation
│   └── evaluate.py             # Evaluation runner
│
├── schemas/
│   └── output.schema.json      # JSON Schema for tool output
│
├── evaluation/
│   ├── ground-truth/           # Per-repo ground truth files
│   │   ├── repo-a.json
│   │   └── repo-b.json
│   ├── checks/                 # Programmatic check implementations
│   │   ├── __init__.py
│   │   ├── accuracy.py
│   │   └── completeness.py
│   └── llm/
│       └── judges/             # LLM judge implementations
│           ├── __init__.py
│           └── actionability.py
│
├── eval-repos/
│   └── synthetic/              # Test repositories for evaluation
│       ├── happy-path/
│       └── edge-case/
│
└── tests/
    ├── conftest.py
    ├── test_analyze.py
    └── test_evaluation.py
```

#### Makefile Interface

```makefile
# Standard Makefile template for Vulcan tools

.PHONY: setup analyze evaluate clean

# Required variables
REPO_PATH ?=
REPO_NAME ?=
OUTPUT_DIR ?= output

# Setup: Install dependencies and prepare environment
setup:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Analyze: Run the tool against a repository
analyze: setup
	@if [ -z "$(REPO_PATH)" ]; then echo "REPO_PATH required"; exit 1; fi
	@if [ -z "$(REPO_NAME)" ]; then echo "REPO_NAME required"; exit 1; fi
	.venv/bin/python scripts/analyze.py \
		--repo-path "$(REPO_PATH)" \
		--repo-name "$(REPO_NAME)" \
		--output-dir "$(OUTPUT_DIR)"

# Evaluate: Run evaluation against ground truth
evaluate: setup
	.venv/bin/python scripts/evaluate.py \
		--output-dir "$(OUTPUT_DIR)" \
		--ground-truth evaluation/ground-truth/

# Clean: Remove generated files
clean:
	rm -rf .venv output/ .pytest_cache/
```

#### Tool Registry Integration

```python
# In collector's tool_registry.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ToolMetadata:
    name: str
    display_name: str
    phase: int                              # 0=foundation, 1=independent, 2+=dependent
    languages: List[str]                    # Supported languages, ["*"] for all
    timeout_seconds: int
    parallel_safe: bool
    depends_on: List[str]                   # Tools that must run first
    produces: List[str]                     # Table names this tool populates
    requires_layout: bool = True            # Whether layout-scanner data is needed
    incremental_capable: bool = False       # Supports incremental analysis

# Example registration
TOOL_REGISTRY = {
    "scc": ToolMetadata(
        name="scc",
        display_name="SCC (Lines of Code)",
        phase=1,
        languages=["*"],
        timeout_seconds=60,
        parallel_safe=True,
        depends_on=["layout-scanner"],
        produces=["file_metrics"],
        incremental_capable=True
    ),
    # ... more tools
}
```

### E.3 LLM Judge Pattern

LLM judges evaluate qualitative aspects of tool output that programmatic checks cannot assess.

#### JudgeResult Dataclass

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class JudgeResult:
    """Standardized output from LLM judges."""

    # Required fields
    dimension: str              # What's being evaluated (e.g., "actionability")
    score: float                # 0-5 scale
    confidence: float           # 0-1 confidence in the score
    reasoning: str              # Why this score was given

    # Optional fields
    recommendations: List[str] = field(default_factory=list)  # Improvement suggestions
    evidence: List[str] = field(default_factory=list)         # Supporting evidence

    def to_dimension_score(self, weight: float) -> DimensionScore:
        """Convert to scorecard dimension."""
        return DimensionScore(
            name=self.dimension,
            weight=weight,
            score=self.score,
            source="judge",
            details=self.reasoning
        )
```

#### Judge Base Class

```python
from abc import ABC, abstractmethod

class BaseJudge(ABC):
    """Base class for all LLM judges."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self.client = anthropic.Anthropic()

    @property
    @abstractmethod
    def dimension(self) -> str:
        """The dimension this judge evaluates."""
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> str:
        """The prompt template for this judge."""
        pass

    def evaluate(self, tool_output: dict, ground_truth: Optional[dict] = None) -> JudgeResult:
        """Run evaluation and return structured result."""

        # Collect evidence first (pattern: pre-structure data for LLM)
        evidence = self.collect_evidence(tool_output, ground_truth)

        # Build prompt with evidence
        prompt = self.prompt_template.format(
            evidence=json.dumps(evidence, indent=2),
            dimension=self.dimension
        )

        # Call LLM
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse structured response
        return self.parse_response(response.content[0].text)

    @abstractmethod
    def collect_evidence(self, tool_output: dict, ground_truth: Optional[dict]) -> dict:
        """Collect evidence for the LLM to evaluate."""
        pass

    def parse_response(self, response_text: str) -> JudgeResult:
        """Parse LLM response into JudgeResult."""
        # Implementation parses JSON from response
        ...
```

#### Example Judge Implementation

```python
class ActionabilityJudge(BaseJudge):
    """Evaluates whether findings are actionable."""

    @property
    def dimension(self) -> str:
        return "actionability"

    @property
    def prompt_template(self) -> str:
        return """
You are evaluating the actionability of code analysis findings.

## Evidence
{evidence}

## Scoring Rubric
- 5: Every finding has clear, specific remediation steps
- 4: Most findings have remediation guidance
- 3: Some findings have guidance, others are vague
- 2: Few findings have actionable guidance
- 1: Findings identify issues but provide no remediation
- 0: Findings are unclear or not actionable

## Output Format
Respond with JSON:
{{
    "score": <0-5>,
    "confidence": <0-1>,
    "reasoning": "<explanation>",
    "recommendations": ["<suggestion1>", "<suggestion2>"],
    "evidence": ["<example1>", "<example2>"]
}}
"""

    def collect_evidence(self, tool_output: dict, ground_truth: Optional[dict]) -> dict:
        findings = tool_output.get("findings", [])
        return {
            "sample_findings": findings[:10],  # Sample for token efficiency
            "total_findings": len(findings),
            "findings_with_remediation": sum(1 for f in findings if f.get("remediation")),
            "findings_with_references": sum(1 for f in findings if f.get("references"))
        }
```

### E.4 Context Pack Pattern

The guidance-engine creates LLM-ready context packs that summarize repository analysis for AI agents.

#### Context Pack Variants

| Variant | Size Target | Use Case | Content Focus |
|---------|-------------|----------|---------------|
| **concise** | ~50KB | Quick overview | Top 10 hotspots, critical issues only |
| **descriptive** | ~150KB | Technical review | All zones, top 50 hotspots, dependency issues |
| **actionable** | ~400KB | Implementation work | Full details, code snippets, refactoring suggestions |

#### Context Pack Structure

```python
@dataclass
class ContextPack:
    """LLM-ready repository context."""

    # Metadata
    repo_name: str
    generated_at: datetime
    variant: str  # "concise", "descriptive", "actionable"

    # Repository Overview
    summary: RepositorySummary

    # Complexity Analysis
    zones: List[ComplexityZone]
    hotspots: List[Hotspot]

    # Dependency Analysis
    import_cycles: List[ImportCycle]
    external_dependencies: List[Dependency]

    # Risk Assessment
    security_issues: List[SecurityFinding]
    knowledge_concentration: KnowledgeAnalysis

    # Actionable Guidance (actionable variant only)
    refactoring_suggestions: Optional[List[RefactoringSuggestion]]
    priority_order: Optional[List[str]]  # Ordered list of hotspot IDs

@dataclass
class ComplexityZone:
    """A cluster of related complexity hotspots."""
    zone_id: str
    zone_type: str  # "volatile_complexity", "concentration", etc.
    directory: str
    density: float      # Hotspots per 1000 LOC
    mass: float         # Total complexity in zone
    hotspot_count: int
    primary_concern: str  # Human-readable summary

@dataclass
class Hotspot:
    """A high-risk file requiring attention."""
    file_id: str
    file_path: str

    # Metrics
    complexity_score: float
    volatility_score: float
    combined_score: float

    # Details
    max_ccn: int
    churn_count: int
    unique_authors: int

    # Graph metrics
    fan_in: int
    fan_out: int
    blast_radius: int

    # Flags
    is_volatile: bool
    is_concentrated: bool  # Knowledge silo
```

#### Context Pack Generation

```python
def generate_context_pack(
    repo_id: str,
    variant: str = "descriptive"
) -> ContextPack:
    """Generate an LLM-ready context pack."""

    # Size limits by variant
    limits = {
        "concise": {"hotspots": 10, "zones": 5, "cycles": 3},
        "descriptive": {"hotspots": 50, "zones": 20, "cycles": 10},
        "actionable": {"hotspots": 100, "zones": 50, "cycles": 25}
    }

    limit = limits[variant]

    # Query hotspots (ordered by combined score)
    hotspots = query_hotspots(
        repo_id,
        lens="volatile_complexity",
        limit=limit["hotspots"]
    )

    # Query zones
    zones = query_zones(repo_id, limit=limit["zones"])

    # Query cycles
    cycles = query_import_cycles(repo_id, limit=limit["cycles"])

    # Build pack
    pack = ContextPack(
        repo_name=get_repo_name(repo_id),
        generated_at=datetime.utcnow(),
        variant=variant,
        summary=build_summary(repo_id),
        zones=zones,
        hotspots=hotspots,
        import_cycles=cycles,
        # ... other fields
    )

    # Add actionable guidance for actionable variant
    if variant == "actionable":
        pack.refactoring_suggestions = generate_refactoring_suggestions(hotspots)
        pack.priority_order = prioritize_hotspots(hotspots)

    return pack
```

#### MCP Integration

The guidance-engine exposes context packs via MCP (Model Context Protocol) for AI agent consumption:

```python
# MCP tool definitions
MCP_TOOLS = [
    {
        "name": "get_hotspots",
        "description": "Get complexity hotspots for a repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_id": {"type": "string"},
                "lens": {"type": "string", "enum": ["complexity", "volatility", "volatile_complexity"]},
                "limit": {"type": "integer", "default": 20}
            },
            "required": ["repo_id"]
        }
    },
    {
        "name": "get_context_pack",
        "description": "Get LLM-ready context pack for a repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_id": {"type": "string"},
                "variant": {"type": "string", "enum": ["concise", "descriptive", "actionable"]}
            },
            "required": ["repo_id"]
        }
    },
    {
        "name": "get_blast_radius",
        "description": "Get transitive callers of a symbol (impact analysis)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_id": {"type": "string"},
                "symbol_name": {"type": "string"},
                "max_depth": {"type": "integer", "default": 5}
            },
            "required": ["repo_id", "symbol_name"]
        }
    }
]
```

### E.5 Adapter Pattern for Tool Output Parsing

The adapter pattern standardizes how tool-specific output is parsed into unified schema.

#### Base Adapter Infrastructure

```python
# From src/shared/adapters/base.py (proposed location)

@dataclass
class PathMatchStats:
    """Track file path matching accuracy."""
    total_paths: int = 0
    matched_paths: int = 0
    unmatched_paths: List[str] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        if self.total_paths == 0:
            return 1.0
        return self.matched_paths / self.total_paths

    def record_match(self, path: str, matched: bool):
        self.total_paths += 1
        if matched:
            self.matched_paths += 1
        else:
            self.unmatched_paths.append(path)

class SeverityMapper:
    """Normalize severity levels across tools."""

    SEVERITY_MAP = {
        # Tool-specific → Unified
        "CRITICAL": "critical",
        "BLOCKER": "critical",
        "HIGH": "high",
        "MAJOR": "high",
        "MEDIUM": "medium",
        "MINOR": "medium",
        "LOW": "low",
        "INFO": "info",
        "HINT": "info"
    }

    @classmethod
    def normalize(cls, severity: str) -> str:
        return cls.SEVERITY_MAP.get(severity.upper(), "unknown")

def normalize_path(path: str, repo_root: str) -> str:
    """Convert absolute/relative path to canonical relative path."""
    # Remove repo root prefix
    if path.startswith(repo_root):
        path = path[len(repo_root):]

    # Normalize separators
    path = path.replace("\\", "/")

    # Remove leading slash
    path = path.lstrip("/")

    return path
```

#### Tool-Specific Adapter Example

```python
class SonarQubeAdapter(BaseAdapter):
    """Parse SonarQube output into unified schema."""

    def __init__(self, layout_api: LayoutAPI):
        self.layout_api = layout_api
        self.path_stats = PathMatchStats()
        self.severity_mapper = SeverityMapper()

    def parse_issues(self, sonar_output: dict) -> List[UnifiedIssue]:
        """Convert SonarQube issues to unified format."""
        issues = []

        for item in sonar_output.get("issues", []):
            # Normalize path
            raw_path = item.get("component", "")
            normalized = normalize_path(raw_path, self.repo_root)

            # Look up file_id
            file_id = self.layout_api.get_file_id(normalized)
            self.path_stats.record_match(normalized, file_id is not None)

            # Map severity
            severity = self.severity_mapper.normalize(item.get("severity", "INFO"))

            issues.append(UnifiedIssue(
                file_id=file_id,
                file_path=normalized,
                line=item.get("line"),
                severity=severity,
                rule_id=item.get("rule"),
                message=item.get("message"),
                source_tool="sonarqube"
            ))

        return issues

    def get_path_match_report(self) -> dict:
        """Return path matching statistics for evaluation."""
        return {
            "total_paths": self.path_stats.total_paths,
            "matched_paths": self.path_stats.matched_paths,
            "match_rate": self.path_stats.match_rate,
            "unmatched_sample": self.path_stats.unmatched_paths[:10]
        }
```

---

## Appendix F: Minimal Schemas (V1.1)

This appendix provides schema sketches for new structures introduced by the Architecture V2 Amendments.

### F.1 Evaluation Result Envelope Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Evaluation Result Envelope",
  "type": "object",
  "required": ["run_id", "repo_id", "commit", "timestamp", "judge_name", "judge_version", "model_id", "dimension", "score"],
  "properties": {
    "run_id": { "type": "string", "format": "uuid" },
    "repo_id": { "type": "string", "format": "uuid" },
    "commit": { "type": "string", "pattern": "^[a-f0-9]{40}$" },
    "timestamp": { "type": "string", "format": "date-time" },
    "judge_name": { "type": "string" },
    "judge_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "model_id": { "type": "string" },
    "prompt_template_id": { "type": "string" },
    "prompt_resolved": { "type": "string" },
    "inputs_digest": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "output_schema_version": { "type": "string" },
    "dimension": { "type": "string" },
    "score": { "type": "number", "minimum": 0, "maximum": 5 },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "reasoning": { "type": "string" },
    "recommendations": { "type": "array", "items": { "type": "string" } },
    "evidence_refs": { "type": "array", "items": { "type": "string" } }
  }
}
```

### F.2 Decision Flag Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Decision Flag",
  "type": "object",
  "required": ["flag_code", "severity", "description", "triggered_by"],
  "properties": {
    "flag_code": {
      "type": "string",
      "enum": [
        "INCOMPLETE_LAYOUT",
        "INCOMPLETE_TOOL_SET",
        "LOW_FILE_COVERAGE",
        "METRIC_DISAGREEMENT_LOC",
        "METRIC_DISAGREEMENT_COMPLEXITY",
        "VULN_DEDUPLICATION_CONFLICT",
        "TREND_CONFIDENCE_LOW"
      ]
    },
    "severity": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low", "info"]
    },
    "description": { "type": "string" },
    "triggered_by": {
      "type": "string",
      "description": "Source: tool name, SoT transformation, or evaluation judge"
    },
    "evidence_refs": {
      "type": "array",
      "items": { "type": "string" }
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "threshold_value": {
      "type": "number",
      "description": "The threshold that was exceeded"
    },
    "actual_value": {
      "type": "number",
      "description": "The actual value that triggered the flag"
    }
  }
}
```

### F.3 Epistemic Claim Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Epistemic Claim",
  "type": "object",
  "required": ["claim_type", "evidence_refs", "as_of"],
  "properties": {
    "claim_type": {
      "type": "string",
      "enum": ["FACT", "DERIVED", "EVALUATION"],
      "description": "FACT=observed, DERIVED=computed, EVALUATION=LLM-judged"
    },
    "evidence_refs": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Pointers to source evidence (file_id, tool, SoT row)"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Confidence score (required for DERIVED/EVALUATION)"
    },
    "confidence_explanation": {
      "type": "string",
      "description": "Human-readable explanation of confidence"
    },
    "as_of": {
      "type": "object",
      "required": ["run_id", "commit"],
      "properties": {
        "run_id": { "type": "string", "format": "uuid" },
        "commit": { "type": "string" },
        "tool_versions": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      }
    }
  }
}
```

---

*Document Version: 1.4 Draft*
*Last Updated: 2026-01-24*
*Changes: Added Architecture V2 Amendments (v1.0) - Primary Product Persona, Decision Semantics, Stable File Identity, Trend Analysis, Run Lifecycle, Canonical Ingestion Rule, LLM Guardrails, vulcan-core Package, CI Gates, V1 Non-Goals, Change Log, Appendix F*
