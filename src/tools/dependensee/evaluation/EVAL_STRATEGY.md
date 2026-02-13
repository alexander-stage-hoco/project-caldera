# Evaluation Strategy: DependenSee

This document describes the evaluation methodology for the DependenSee .NET dependency visualization and analysis tool.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation to provide both objective rigor and semantic understanding:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- verifies structural correctness, data accuracy, and envelope compliance |
| LLM Judges | 40% | Semantic understanding -- evaluates nuanced quality dimensions like graph coherence, detection completeness, and circular dependency reasoning |

This hybrid approach is motivated by the nature of dependency analysis output. Programmatic checks can deterministically validate that project counts, reference lists, and graph node/edge relationships match known ground truth. However, aspects such as whether the dependency graph is "useful" or whether circular dependency paths are "complete and informative" require semantic judgment that LLM judges are better suited to assess.

The programmatic layer runs first and provides a fast feedback loop. If programmatic checks fail (any check returns `fail` or `error`), the overall programmatic decision is `FAIL` regardless of individual scores. The LLM layer then provides a deeper qualitative assessment. When both are available, they are combined using a 60/40 weighted formula to produce a single decision.

### Key Design Principles

1. **Ground truth drives accuracy checks.** Every accuracy check compares tool output against hand-verified expected values from synthetic .NET solutions.
2. **Binary pass/fail for programmatic checks.** Each check returns `pass`, `fail`, `warn`, or `error`. There are no ambiguous 1-5 scores at the programmatic level.
3. **LLM judges are grounded in evidence.** Judges collect structured evidence from the analysis output before invoking the LLM, and ground truth assertions can cap LLM scores if hard constraints are violated.
4. **Evaluation modes support both synthetic and real-world repos.** Synthetic mode validates against exact expected values; real-world mode evaluates output quality without fixed expectations.

---

## Dimension Summary

### Programmatic Dimensions

Programmatic checks are organized into four categories. There are no explicit per-category weights in the programmatic evaluator; instead, the overall programmatic score is computed as the ratio of passing checks to total checks.

| Category | Check Count | Purpose |
|----------|-------------|---------|
| Accuracy | 6 | Validates project counts, paths, references, packages, frameworks, and circular dependencies against ground truth |
| Coverage | 4 | Ensures all projects are analyzed, graph is populated, summary is present, and all projects have valid paths |
| Output Quality | 5 | Validates envelope format, metadata completeness, tool name, path normalization, and graph internal consistency |
| Performance | 1 | Verifies output size is proportional to project count |

**Total programmatic checks: 16**

### LLM Judge Dimensions

| Judge | Weight | Focus Area |
|-------|--------|------------|
| Project Detection | 30% | Completeness and accuracy of .NET project file discovery |
| Dependency Accuracy | 30% | Correctness of project and package reference detection |
| Graph Quality | 20% | Structural completeness, internal consistency, and connectivity of the dependency graph |
| Circular Detection | 20% | Accuracy of circular dependency identification and path reporting |

### Combined Scoring

```
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_weighted_score)
```

Where:
- `programmatic_normalized` = programmatic score (0.0-1.0) scaled to 0.0-5.0
- `llm_weighted_score` = sum of (judge_score * judge_weight) / sum of judge_weights, on a 1-5 scale

---

## Programmatic Check Catalog

### Accuracy Checks (6 Checks)

These checks compare tool output against ground truth files. When no ground truth is available, checks return `pass` with a "skipped" message.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| `accuracy.project_count` | Project count matches | `summary.project_count` equals `expected.project_count` from ground truth | Actual vs expected count |
| `accuracy.project_paths` | All expected projects found | Set of actual project paths equals set of expected project paths; no missing, no extra | Missing paths, extra paths |
| `accuracy.project_references` | Project references correct | For each project, the set of `project_references` matches expected; no missing, no extra | Per-project mismatches (first 3) |
| `accuracy.package_references` | Package references correct | For each project, the set of package names in `package_references` matches expected | Per-project mismatches (first 3) |
| `accuracy.target_frameworks` | Target frameworks correct | For each project, `target_framework` matches expected value exactly | Per-project framework mismatches (first 3) |
| `accuracy.circular_dependencies` | Circular dependency count correct | `len(data.circular_dependencies)` equals `expected.circular_dependency_count` | Actual vs expected count |

#### Implementation Details

All accuracy checks follow the same pattern:

```python
def check_<aspect>(output: dict, ground_truth: dict | None) -> dict:
    # 1. If no ground truth, return pass (skipped)
    # 2. Extract actual values from output.data
    # 3. Extract expected values from ground_truth.expected
    # 4. Compare and return pass/fail with descriptive message
```

The `check_project_references` and `check_package_references` checks perform set comparison per project path, identifying both missing and extra references. The message includes up to 3 mismatches to keep output manageable.

### Coverage Checks (4 Checks)

Coverage checks verify that the tool produces complete output, independent of ground truth.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| `coverage.projects_analyzed` | Projects were analyzed | `data.projects` is non-empty (returns `warn` if empty, not `fail`) | Number of projects analyzed |
| `coverage.graph_populated` | Dependency graph has content | `data.dependency_graph.nodes` is non-empty (returns `warn` if empty) | Node and edge counts |
| `coverage.summary_present` | Summary statistics present | All required fields exist in `data.summary`: `project_count`, `package_count`, `reference_count`, `circular_dependency_count` | List of missing fields |
| `coverage.project_paths_present` | All projects have valid paths | Every project in `data.projects` has a non-empty `path` field | List of projects missing paths (first 5) |

#### Note on Warn vs Fail

The `projects_analyzed` and `graph_populated` checks return `warn` rather than `fail` when no data is found. This is intentional: an empty repository is a valid edge case (covered by the `empty.json` ground truth scenario). The warn status does not count toward the failure total in the summary computation.

### Output Quality Checks (5 Checks)

Output quality checks validate envelope format compliance and data integrity.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| `output_quality.envelope_present` | Envelope structure valid | Both `metadata` and `data` keys exist at root level | Which section is missing |
| `output_quality.metadata_complete` | Metadata has all required fields | All 8 required fields present: `tool_name`, `tool_version`, `run_id`, `repo_id`, `branch`, `commit`, `timestamp`, `schema_version` | List of missing fields |
| `output_quality.tool_name_correct` | Tool name is correct | `metadata.tool_name` equals `"dependensee"` exactly | Actual tool name |
| `output_quality.paths_repo_relative` | All paths are repo-relative | No project path or project reference starts with `/` or `./` | List of non-relative paths (first 3) |
| `output_quality.graph_consistency` | Dependency graph internally consistent | All edge sources reference existing node IDs; all `project_reference` edge targets reference existing node IDs (package reference targets may reference external packages not in the node list) | List of invalid references (first 3) |

#### Path Normalization Rule

Per Project Caldera conventions, all file paths must be repo-relative:
- No leading `/`, `./`, or `..`
- POSIX separators only (`/` not `\`)

The `paths_repo_relative` check validates both `project.path` and entries in `project.project_references`.

### Performance Checks (1 Check)

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| `performance.output_size_reasonable` | Output size proportional to input | Number of graph nodes >= number of projects (returns `warn` if violated) | Project count, node count, edge count |

This is a sanity check ensuring the dependency graph contains at least as many nodes as there are projects. A graph with fewer nodes than projects would indicate that some projects were not represented in the graph structure.

---

## Scoring

### Programmatic Score Computation

The programmatic evaluator (`scripts/evaluate.py`) uses a simple ratio-based scoring model:

```python
def compute_summary(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") == "fail")
    warned = sum(1 for r in results if r.get("status") == "warn")
    errored = sum(1 for r in results if r.get("status") == "error")

    score = passed / total if total > 0 else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "errored": errored,
        "score": round(score, 4),
        "decision": "PASS" if failed == 0 and errored == 0 else "FAIL",
    }
```

Key properties of this scoring:
- **Score** is the fraction of checks that passed (`passed / total`), yielding a value between 0.0 and 1.0.
- **Decision** is `PASS` only if there are zero failures AND zero errors. Any single failure or error triggers `FAIL`.
- **Warns** do not count as failures. They reduce the score slightly (since they are not counted as passed) but do not trigger a FAIL decision.

### LLM Score Computation

Each LLM judge produces a score on a 1-5 scale. The overall LLM score is a weighted average:

```python
total_score = sum(judge_score * judge_weight for each judge) / sum(judge_weights)
```

With the current judge weights:
- Project Detection: 0.30
- Dependency Accuracy: 0.30
- Graph Quality: 0.20
- Circular Detection: 0.20
- Total weight: 1.00

### Combined Score Formula

When both programmatic and LLM results are available, the orchestrator computes a combined score:

```python
# In the orchestrator (evaluation/llm/orchestrator.py):
prog_score = programmatic_score * 5.0  # Convert 0-1 to 0-5 scale

# In the shared base (shared/evaluation/orchestrator.py):
PROGRAMMATIC_WEIGHT = 0.60
LLM_WEIGHT = 0.40

combined = (programmatic_score_on_5_scale * PROGRAMMATIC_WEIGHT) + (llm_total_score * LLM_WEIGHT)
```

Example: If programmatic score is 0.9375 (15/16 checks pass) and LLM score is 4.2:
```
programmatic_normalized = 0.9375 * 5.0 = 4.6875
combined = (4.6875 * 0.60) + (4.2 * 0.40) = 2.8125 + 1.68 = 4.4925
```

### Ground Truth Score Capping

If a judge's ground truth assertions fail, the LLM score for that judge is capped at 2 (out of 5):

```python
# In shared/evaluation/orchestrator.py:
if not gt_passed:
    result.score = min(result.score, 2)  # Cap at 2 if assertions fail
```

This prevents the LLM from awarding a high score when verifiable facts are wrong. For example, if the `ProjectDetectionJudge` ground truth assertion finds that the project count does not match, the LLM score for that dimension cannot exceed 2 regardless of how positively the LLM evaluates other aspects.

---

## Decision Thresholds

Decisions are determined from the combined score (or LLM-only score if no programmatic results are available) using these thresholds:

| Decision | Combined Score | Interpretation |
|----------|----------------|----------------|
| STRONG_PASS | >= 4.0 | Excellent quality, production-ready output |
| PASS | >= 3.5 | Good quality, minor improvements possible |
| WEAK_PASS | >= 3.0 | Acceptable with caveats, should investigate warnings |
| FAIL | < 3.0 | Significant issues, requires remediation |

These thresholds are defined in `src/shared/evaluation/orchestrator.py`:

```python
class LLMEvaluatorBase(ABC):
    STRONG_PASS_THRESHOLD = 4.0
    PASS_THRESHOLD = 3.5
    WEAK_PASS_THRESHOLD = 3.0
```

Note: The programmatic evaluator uses a separate binary PASS/FAIL decision (any failure = FAIL). The combined decision uses the threshold-based system above.

---

## LLM Judge Details

### Judge 1: Project Detection (30%)

**Class:** `ProjectDetectionJudge` in `evaluation/llm/judges/project_detection.py`

**Purpose:** Evaluates completeness and accuracy of .NET project file discovery, including `.csproj`, `.fsproj`, and `.vbproj` files.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Completeness | 40% | 5: All project files found. 4: >90% found. 3: 70-90%. 2: 50-70%. 1: <50% found. |
| Path Quality | 30% | 5: All paths repo-relative, no `..` or absolute. 4: <5% issues. 3: 5-15% issues. 2: 15-30% issues. 1: Mostly absolute or `..` paths. |
| Framework Detection | 30% | 5: All projects have target framework. 4: >90%. 3: 70-90%. 2: 50-70%. 1: <50%. |

**Evidence collected:**
- `repos_analyzed`: List of repository names processed
- `total_projects`: Count of all projects found across repos
- `projects_with_framework`: Count of projects with target framework detected
- `projects_with_path`: Count of projects with a valid path field
- `path_quality`: Breakdown of absolute paths, `..` paths, and relative paths
- `project_types`: Counts by extension (`.csproj`, `.fsproj`, `.vbproj`)
- `sample_projects`: First 5 projects for inspection
- `ground_truth_comparison`: Per-repo expected vs actual project counts (when ground truth available)

**Ground truth assertions:** Checks that the project count for each repo matches the expected count from ground truth. Failure caps the LLM score at 2.

**Prompt template:** `evaluation/llm/prompts/project_detection.md`

### Judge 2: Dependency Accuracy (30%)

**Class:** `DependencyAccuracyJudge` in `evaluation/llm/judges/dependency_accuracy.py`

**Purpose:** Evaluates correctness of project reference and NuGet package reference detection.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Project Reference Accuracy | 40% | 5: All project references captured with correct paths. 4: >90% correct. 3: 70-90%. 2: 50-70%. 1: <50% correct. |
| Package Reference Accuracy | 35% | 5: All packages with correct names and versions. 4: >90%. 3: 70-90%. 2: 50-70% or missing versions. 1: <50% correct. |
| Internal Consistency | 25% | 5: No orphan references, all targets exist. 4: <5% inconsistencies. 3: 5-15%. 2: 15-30%. 1: >30% data integrity issues. |

**Evidence collected:**
- `total_projects`, `total_project_references`, `total_package_references`: Aggregate counts
- `packages_with_version`: Count of packages that include version information
- `version_coverage_pct`: Percentage of packages with versions
- `unique_packages`, `duplicate_package_count`: Package uniqueness analysis
- `sample_packages`: Up to 10 sample packages with name, version, project, and repo
- `sample_project_refs`: Up to 10 sample project references with from, to, and repo
- `ground_truth_comparison`: Per-repo expected vs actual reference and package counts

**Ground truth assertions:** Checks that both `reference_count` and `package_count` match expected values per repo. Failure caps the LLM score at 2.

**Prompt template:** `evaluation/llm/prompts/dependency_accuracy.md`

### Judge 3: Graph Quality (20%)

**Class:** `GraphQualityJudge` in `evaluation/llm/judges/graph_quality.py`

**Purpose:** Evaluates structural completeness, internal consistency, and connectivity of the dependency graph.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Structural Completeness | 35% | 5: All projects and packages represented as nodes with correct edges. 4: <5% missing. 3: 5-15% missing. 2: 15-30% missing. 1: >30% missing. |
| Internal Consistency | 35% | 5: No dangling references, all edge targets exist as nodes. 4: <2% inconsistencies. 3: 2-10%. 2: 10-20%. 1: >20% dangling refs. |
| Connectivity | 30% | 5: No orphan nodes. 4: <5% orphans. 3: 5-15%. 2: 15-30%. 1: >30% orphans. |

**Evidence collected:**
- `graphs_analyzed`: Per-repo node and edge counts
- `total_nodes`, `total_edges`: Aggregate totals
- `node_breakdown`: Counts of project nodes vs package nodes
- `edge_breakdown`: Counts of project reference edges vs package reference edges
- `quality_metrics`: Computed metrics including `dangling_references`, `orphan_nodes`, `consistency_pct`, and `connectivity_pct`
- `ground_truth_comparison`: Per-repo expected vs actual graph node/edge counts

**Quality metric formulas (computed in evidence collection):**
```python
consistency_score = 1.0 - (dangling_refs / max(total_edges, 1))
connectivity_score = 1.0 - (orphan_nodes / max(total_nodes, 1))
```

**Ground truth assertions:** Checks that `graph_node_count` and `graph_edge_count` match expected values per repo. Failure caps the LLM score at 2.

**Prompt template:** `evaluation/llm/prompts/graph_quality.md`

### Judge 4: Circular Detection (20%)

**Class:** `CircularDetectionJudge` in `evaluation/llm/judges/circular_detection.py`

**Purpose:** Evaluates accuracy of circular dependency identification, path completeness, and internal consistency.

**Sub-dimensions:**

| Sub-dimension | Weight | Scoring Rubric |
|---------------|--------|----------------|
| Detection Accuracy | 40% | 5: All cycles detected with no false positives. 4: >90% detected, minimal FP. 3: 70-90%, some FP. 2: 50-70% or many FP. 1: <50% or unreliable. |
| Path Completeness | 30% | 5: All cycles include complete path (A -> B -> C -> A). 4: >90% complete. 3: 70-90%. 2: 50-70%. 1: <50% complete. |
| Internal Consistency | 30% | 5: Summary counts match actual cycle counts exactly. 4: <5% discrepancy. 3: 5-15%. 2: 15-30%. 1: >30% inconsistencies. |

**Special case handling:** When no circular dependencies are found AND ground truth confirms zero cycles expected, the judge is instructed to score 5 if the output is well-formed and consistent. This prevents penalizing correct behavior on clean codebases.

**Evidence collected:**
- `total_cycles`: Total number of cycles found across all repos
- `repos_with_cycles`, `repos_without_cycles`: Categorization of repos
- `cycles`: Up to 10 sample cycles with repo name, cycle path, and cycle length
- `summary_counts`: Per-repo circular dependency counts from the summary section
- `consistency_issues`: Repos where summary count differs from actual cycle count
- `is_consistent`: Boolean flag for overall consistency
- `ground_truth_comparison`: Per-repo expected vs actual cycle counts

**Ground truth assertions:** Checks that `circular_dependency_count` matches the expected value per repo. Failure caps the LLM score at 2.

**Prompt template:** `evaluation/llm/prompts/circular_detection.md`

---

## LLM Judge Infrastructure

### Base Judge Architecture

All DependenSee judges extend `evaluation/llm/judges/base.py:BaseJudge`, which in turn extends `shared.evaluation.BaseJudge` (from `src/shared/evaluation/base_judge.py`).

The DependenSee-specific base provides:
- `load_all_analysis_results()`: Loads JSON analysis files from `output_dir`, falling back to a single `analysis_path` file for backwards compatibility.
- `extract_projects(data)`: Extracts the `projects` list from analysis data, handling envelope unwrapping via `shared.output_management.unwrap_envelope`.
- `extract_dependency_graph(data)`: Extracts the `dependency_graph` dict, defaulting to `{"nodes": [], "edges": []}`.
- `prompt_file` property: Resolves to `evaluation/llm/prompts/<dimension_name>.md`.

### Prompt Template System

Each judge has a corresponding prompt template in `evaluation/llm/prompts/`. Templates use `{{ placeholder }}` syntax for variable substitution:

| Placeholder | Source |
|-------------|--------|
| `{{ evidence }}` | JSON-serialized evidence dict from `collect_evidence()` |
| `{{ interpretation_guidance }}` | Context-dependent guidance string |
| `{{ synthetic_baseline }}` | Synthetic evaluation baseline results (for real-world mode) |
| `{{ evaluation_mode }}` | Either `"synthetic"` or `"real_world"` |

All prompts share a common structure:
1. Role assignment (expert .NET architect or graph theory analyst)
2. Evaluation context with mode-specific instructions
3. Evidence section with the `{{ evidence }}` placeholder
4. Evaluation criteria with sub-dimension rubrics
5. JSON response format specification

### Response Format

All judges expect the LLM to return a JSON object:

```json
{
  "score": 4,
  "confidence": 0.85,
  "reasoning": "Detailed explanation of the evaluation...",
  "evidence_cited": ["Specific evidence points referenced..."],
  "recommendations": ["Improvement suggestions..."],
  "sub_scores": {
    "sub_dimension_1": 5,
    "sub_dimension_2": 4,
    "sub_dimension_3": 3
  }
}
```

### Evaluation Modes

The judges support two evaluation modes:

| Mode | When Used | Behavior |
|------|-----------|----------|
| `synthetic` | Evaluating against synthetic test repos with known ground truth | Strict validation against expected values; ground truth assertions enforced |
| `real_world` | Evaluating against real repositories without predefined expectations | Focus on output quality, consistency, and correctness of what is detected; low counts are acceptable |

When in `real_world` mode, prompts include additional guidance:
- Low project/dependency counts may be valid for small repositories
- Focus on accuracy of what IS detected, not raw counts
- Zero cycles found is a VALID result for clean codebases

### Confidence Levels

Each LLM judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review recommended |

---

## Ground Truth

### Methodology

Ground truth files define the exact expected output for each synthetic test scenario. They are hand-authored based on carefully constructed .NET solutions where every project, reference, and package is known in advance.

### Synthetic Repository Scenarios

Five ground truth scenarios are maintained in `evaluation/ground-truth/`:

| File | Scenario | Projects | Packages | Refs | Cycles | Purpose |
|------|----------|----------|----------|------|--------|---------|
| `synthetic.json` | Standard .NET solution | 4 | 9 | 6 | 0 | Baseline: typical multi-project solution with layered dependencies |
| `circular.json` | Circular dependency chain | 3 | 3 | 3 | 1 | Validates cycle detection: A -> B -> C -> A |
| `empty.json` | Empty repository | 0 | 0 | 0 | 0 | Edge case: no .NET projects at all |
| `multi-framework.json` | Multi-framework projects | 3 | 6 | 2 | 0 | Validates handling of mixed target frameworks (net6.0, net7.0, net8.0) |
| `transitive.json` | Transitive dependency chain | 4 | 5 | 3 | 0 | Validates linear chain detection: Presentation -> Application -> Domain -> Infrastructure |

### Ground Truth Schema

Each ground truth file follows this structure:

```json
{
  "id": "<scenario-id>",
  "description": "Human-readable description of the scenario",
  "repo_path": "eval-repos/<scenario-id>",
  "expected": {
    "project_count": <int>,
    "projects": [
      {
        "name": "<project-name>",
        "path": "<repo-relative-path-to-csproj>",
        "target_framework": "<e.g. net8.0>",
        "project_references": ["<repo-relative paths>"],
        "package_references": [
          {"name": "<package-name>", "version": "<version>"}
        ]
      }
    ],
    "package_count": <int>,
    "reference_count": <int>,
    "circular_dependency_count": <int>,
    "circular_dependencies": [["A", "B", "C", "A"]],
    "graph_node_count": <int>,
    "graph_edge_count": <int>
  }
}
```

### Scenario-Specific Expected Values

#### Synthetic (baseline)

4 projects: MyApp, MyApp.Core, MyApp.Data, MyApp.Tests. All target `net8.0`. 9 unique NuGet packages (Microsoft.Extensions.Hosting, Serilog, Newtonsoft.Json, Dapper, Microsoft.Data.SqlClient, xunit, xunit.runner.visualstudio, Moq, FluentAssertions). 6 project references forming a layered architecture. 13 graph nodes (4 projects + 9 packages), 15 graph edges (6 project refs + 9 package refs).

#### Circular

3 projects: ServiceA, ServiceB, ServiceC. Each references the next in a cycle (A -> B -> C -> A). 1 circular dependency detected. 3 NuGet packages, 3 project references. 6 graph nodes, 6 graph edges.

#### Empty

Zero across all metrics. Validates graceful handling of repositories with no .NET content.

#### Multi-Framework

3 projects spanning net6.0, net7.0, and net8.0: LegacyService (net6.0), ModernApi (net7.0 referencing LegacyService), LatestWorker (net8.0 referencing ModernApi). 6 packages, 2 project references. 9 graph nodes, 8 graph edges.

#### Transitive

4 projects forming a linear chain: App.Presentation -> App.Application -> App.Domain -> App.Infrastructure. Tests that the tool correctly represents transitive dependency chains without falsely reporting circular dependencies. 5 packages, 3 project references. 9 graph nodes, 8 graph edges.

### Scenario Selection at Runtime

The evaluator (`scripts/evaluate.py`) dynamically selects the ground truth file based on the `repo_path` field in the analysis output metadata:

```python
metadata = output.get("metadata", {})
repo_path = metadata.get("repo_path", "")

# Extract scenario name from path
if "/" in repo_path:
    scenario = repo_path.split("/")[-1]
else:
    scenario = repo_path or "synthetic"

# Load matching ground truth
gt_path = args.ground_truth_dir / f"{scenario}.json"
```

For example, if the analysis was run against `eval-repos/circular`, the evaluator loads `circular.json` as ground truth.

---

## Additional Prompt Templates

Two additional prompt templates exist for supplementary evaluation:

| File | Purpose |
|------|---------|
| `evaluation/llm/prompts/accuracy.md` | Generic accuracy evaluation prompt (simplified, 1-5 scale with PASS/FAIL verdict) |
| `evaluation/llm/prompts/actionability.md` | Evaluates whether the output is actionable for developers (simplified, 1-5 scale with PASS/FAIL verdict) |

These are not currently wired into the 4-judge orchestrator but are available for ad-hoc or future evaluation use.

---

## Running Evaluations

### Prerequisites

1. Run analysis first to produce output:
   ```bash
   cd src/tools/dependensee
   make analyze REPO_PATH=eval-repos/synthetic
   ```

2. Ensure the virtual environment is set up:
   ```bash
   make setup
   ```

### Programmatic Evaluation

```bash
# Run programmatic evaluation against the most recent analysis output
make evaluate

# The evaluator will:
# 1. Find the latest output directory (outputs/*/)
# 2. Load output.json from that directory
# 3. Detect the scenario from metadata.repo_path
# 4. Load matching ground truth from evaluation/ground-truth/
# 5. Run all 16 checks
# 6. Write results to evaluation/results/evaluation_report.json
```

### LLM Evaluation

```bash
# Full LLM evaluation (4 judges, opus-4.5 model)
make evaluate-llm

# With a different model
make evaluate-llm LLM_MODEL=sonnet

# Focused evaluation (2 judges: project_detection + dependency_accuracy)
# Via direct invocation:
.venv/bin/python -m evaluation.llm.orchestrator outputs/ \
    --output evaluation/results/llm_evaluation.json \
    --model opus-4.5 \
    --focused

# With markdown report generation
.venv/bin/python -m evaluation.llm.orchestrator outputs/ \
    --output evaluation/results/llm_evaluation.json \
    --model opus-4.5 \
    --markdown
```

### Combined Evaluation

The LLM orchestrator automatically looks for programmatic results at `evaluation/results/evaluation_report.json`. If found, it computes the combined score:

```bash
# Run programmatic first, then LLM (which picks up programmatic results)
make evaluate
make evaluate-llm
```

Alternatively, specify the programmatic results path explicitly:

```bash
.venv/bin/python -m evaluation.llm.orchestrator outputs/ \
    --output evaluation/results/llm_evaluation.json \
    --programmatic-results evaluation/results/evaluation_report.json
```

### Evaluation Across Multiple Scenarios

To evaluate against all ground truth scenarios, run analysis and evaluation for each:

```bash
for scenario in synthetic circular empty multi-framework transitive; do
    make analyze REPO_PATH=eval-repos/$scenario REPO_NAME=$scenario
    make evaluate
done
```

---

## Evaluation Output Format

### Programmatic Report (`evaluation_report.json`)

```json
{
  "timestamp": "2026-02-13T10:00:00+00:00",
  "decision": "PASS",
  "score": 1.0,
  "summary": {
    "total": 16,
    "passed": 16,
    "failed": 0,
    "warned": 0,
    "errored": 0,
    "score": 1.0,
    "decision": "PASS"
  },
  "checks": [
    {
      "check_id": "accuracy.project_count",
      "status": "pass",
      "message": "Project count matches: 4"
    }
  ]
}
```

### LLM Evaluation Report (`llm_evaluation.json`)

```json
{
  "run_id": "llm-eval-20260213-100000",
  "timestamp": "2026-02-13T10:00:00+00:00",
  "model": "opus-4.5",
  "dimensions": [
    {
      "name": "project_detection",
      "score": 4.5,
      "weight": 0.30,
      "weighted_score": 1.35,
      "confidence": 0.90,
      "reasoning": "...",
      "sub_scores": {
        "completeness": 5,
        "path_quality": 4,
        "framework_detection": 5
      },
      "ground_truth_passed": true,
      "ground_truth_failures": []
    }
  ],
  "total_score": 4.35,
  "average_confidence": 0.88,
  "combined_score": 4.52,
  "decision": "STRONG_PASS"
}
```

---

## Extending the Evaluation

### Adding a New Programmatic Check

1. Choose the appropriate category module in `scripts/checks/` (accuracy, coverage, output_quality, or performance).
2. Add a function following the naming convention `check_<name>(output, ground_truth) -> dict`.
3. Return a dict with at minimum `check_id` (format: `<module>.<check_name>`) and `status` (`pass`, `fail`, `warn`, or `error`).
4. The evaluator auto-discovers all `check_*` functions via `importlib`.
5. Update ground truth files if the check requires new expected values.
6. Run `make evaluate` to verify the new check.

### Adding a New LLM Judge

1. Create a new judge class in `evaluation/llm/judges/`, extending `BaseJudge`.
2. Implement required properties: `dimension_name`, `weight`.
3. Implement `collect_evidence()` to gather structured data from analysis output.
4. Implement `get_default_prompt()` as a fallback prompt template.
5. Implement `run_ground_truth_assertions()` for hard constraint checking.
6. Create a corresponding prompt template in `evaluation/llm/prompts/<dimension_name>.md`.
7. Register the new judge in `evaluation/llm/judges/__init__.py` (add to `JUDGES` list and `__all__`).
8. Register the judge in `evaluation/llm/orchestrator.py` in `register_all_judges()`.
9. Adjust existing judge weights to maintain a total weight of 1.0.

### Adding a New Ground Truth Scenario

1. Create the synthetic .NET solution in `eval-repos/<scenario-name>/`.
2. Create the ground truth file at `evaluation/ground-truth/<scenario-name>.json` following the established schema.
3. Populate all expected fields: project_count, projects (with full reference details), package_count, reference_count, circular_dependency_count, graph_node_count, graph_edge_count.
4. Run analysis and evaluation against the new scenario to verify accuracy.

---

## References

- [DependenSee GitHub](https://github.com/AdrianWilczynski/DependenSee) -- .NET dependency visualization tool
- [Project Caldera Evaluation Docs](../../../docs/EVALUATION.md) -- Shared LLM judge infrastructure
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685) -- Foundation for LLM evaluation methodology
- [Shared Evaluation Base](../../../src/shared/evaluation/) -- `BaseJudge`, `LLMEvaluatorBase`, `JudgeResult`
