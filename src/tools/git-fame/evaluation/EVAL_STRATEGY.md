# Evaluation Strategy: git-fame Authorship Attribution

This document describes the evaluation methodology for the git-fame tool, which provides line-level authorship attribution via git blame, producing author ownership metrics, bus factor calculations, and concentration indices (HHI, Gini).

---

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation to assess git-fame output across correctness, completeness, reliability, and integration readiness.

| Component | Purpose |
|-----------|---------|
| Programmatic | Objective, reproducible, fast -- validates structure, accuracy against ground truth, performance, and integration schema compliance |
| LLM Judges | Semantic understanding -- evaluates nuanced quality of authorship attribution, bus factor reasoning, concentration metric consistency, and evidence completeness |

### Why Hybrid?

Programmatic checks efficiently validate deterministic properties (JSON validity, field presence, numeric accuracy within tolerances) but cannot judge whether an authorship distribution "makes sense" given the repository context. LLM judges complement this by reasoning over the full analysis output, detecting subtle inconsistencies, and assessing whether concentration metrics correctly reflect the underlying ownership pattern. Together, the two tiers provide both precision and nuance.

### Design Principles

1. **Ground truth as anchor** -- Synthetic repositories with controlled author distributions provide deterministic expected values for all key metrics (author count, LOC, HHI, bus factor, ownership percentages).
2. **Binary where possible** -- Programmatic checks produce pass/fail results. LLM judges use a 1-5 rubric but each rubric level maps to concrete, observable criteria.
3. **Evidence-driven** -- Every check and judge collects structured evidence (actual values, expected values, deltas) so failures are immediately diagnosable.
4. **Envelope-aware** -- Checks support both the new Caldera envelope format (`metadata`/`data` structure) and the legacy format (`schema_version`/`results`), ensuring backward compatibility.

---

## Dimension Summary

### Programmatic Dimensions (evaluate.py)

| ID | Dimension | Weight | Checks | Focus |
|----|-----------|--------|--------|-------|
| D1 | Output Quality | 20% | 6 | Schema, timestamps, field presence, JSON validity |
| D2 | Authorship Accuracy | 20% | 8 | LOC, author count, ownership %, bus factor, HHI vs ground truth |
| D3 | Reliability | 15% | 4 | Determinism, empty repo handling, single-author, renames |
| D4 | Performance | 15% | 4 | Execution speed, memory usage, incremental performance |
| D5 | Integration Fit | 15% | 4 | Path normalization, metric compatibility, collector schema |
| D6 | Installation | 15% | 2 | pip install verification, CLI help validation |
| | **Total** | **100%** | **28** | |

### LLM Judge Dimensions (judges/__init__.py JUDGES registry)

| Dimension | Weight | Judge Class | Focus |
|-----------|--------|-------------|-------|
| Authorship Quality | 25% | `AuthorshipQualityJudge` | Author identification accuracy, ownership percentages, metric completeness |
| Bus Factor Accuracy | 20% | `BusFactorAccuracyJudge` | Calculation correctness, distribution consistency, risk assessment |
| Concentration Metrics | 20% | `ConcentrationMetricsJudge` | HHI accuracy, top-N percentages, internal consistency |
| Evidence Quality | 15% | `EvidenceQualityJudge` | Required/optional field coverage, provenance tracking |
| Integration Readiness | 10% | `IntegrationReadinessJudge` | Caldera envelope compliance, type correctness, format consistency |
| Output Completeness | 10% | `OutputCompletenessJudge` | Section presence, author data quality, summary data, error rate |
| | **100%** | **6 judges** | |

---

## Programmatic Check Catalog

### D1: Output Quality (20% weight, 6 checks)

These checks verify the structure and format of git-fame output files.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| OQ-1 | Schema Version Present | `schema_version` field exists in all analysis outputs (supports both `metadata.schema_version` envelope and top-level legacy) | List of analyses checked, repos with missing field |
| OQ-2 | Valid ISO8601 Timestamp | Timestamp matches `YYYY-MM-DDTHH:MM:SS` pattern with optional fractional seconds and timezone (supports `metadata.timestamp` and `generated_at`) | Invalid timestamp values per repo |
| OQ-3 | Required Summary Fields | All 5 required summary fields present: `author_count`, `total_loc`, `hhi_index`, `bus_factor`, `top_author_pct` | Missing fields per repo |
| OQ-4 | Author Record Fields | All author records contain: `name`, `surviving_loc`, `ownership_pct` | Total author count, missing field paths |
| OQ-5 | File Record Fields | If file-level data is present, all records contain: `path`, `author`, `loc`. Passes if only author-level data is present. | Total file count, missing field paths |
| OQ-6 | JSON Validity | All `*.json` files in the output directory parse as valid JSON | File names and parse error details for invalid files |

### D2: Authorship Accuracy (20% weight, 8 checks)

These checks compare analysis output against ground truth from `evaluation/ground-truth/synthetic.json`.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| AA-1 | Total LOC Matches | `total_loc` in summary exactly matches `expected_total_loc` from ground truth | Expected vs actual LOC per repo |
| AA-2 | Author Count Matches | `author_count` in summary exactly matches `expected_author_count` | Expected vs actual count per repo |
| AA-3 | Top Author LOC >= 90% | Top author's `surviving_loc` is at least 90% of `expected_top_author_loc` | Threshold, actual LOC, expected minimum |
| AA-4 | Ownership % Within 5% | Each author's `ownership_pct` is within 5.0 percentage points of `expected_authors` ground truth | Per-author expected vs actual, tolerance |
| AA-5 | Bus Factor Matches | `bus_factor` in summary exactly matches `expected_bus_factor` | Expected vs actual per repo |
| AA-6 | HHI Index Within 0.1 | `hhi_index` in summary is within 0.1 of `expected_hhi` | Expected vs actual HHI, delta |
| AA-7 | Top Two % Within 5% | `top_two_pct` in summary is within 5.0 percentage points of `expected_top_two_pct` | Expected vs actual, delta |
| AA-8 | File Attribution | All files have a non-empty `author` field. If only author-level data exists, checks for non-empty authors list. | Total files/authors checked, missing attributions |

**Ground truth loading**: The `AuthorshipAccuracyChecks` class loads ground truth via `load_ground_truth()` which handles both flat `{repo_name: {values}}` and nested `{repos: {repo_name: {expected: {values}}}}` structures. Repos whose names start with `_` are skipped. Checks that find no corresponding ground truth key are marked as passed (skipped).

### D3: Reliability (15% weight, 4 checks)

These checks verify git-fame produces consistent and correct results under various conditions, using live execution against synthetic repositories in `eval-repos/`.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| RL-1 | Determinism | Two consecutive runs on the same repo produce byte-identical JSON output (compared via MD5 of sorted JSON) | Hash values from both runs, test repo path |
| RL-2 | Empty Repo Handling | Running git-fame on an empty repository (no commits or LOC=0) exits without crashing. Accepts exit code 0 or informative stderr. | Return code, stderr content, repo path |
| RL-3 | Single Author Handling | Single-author repository produces exactly 1 author in output. If ground truth is available, validates bus_factor=1 and HHI=1.0. | Author count, bus factor, HHI values |
| RL-4 | Rename Handling | Authorship is tracked through file renames (git-fame relies on git blame which inherently tracks renames). If no rename-test repo exists, passes as git-fame delegates rename tracking to git. | Number of authors tracked, repo path |

### D4: Performance (15% weight, 4 checks)

These checks measure execution speed and resource usage by running git-fame against test repositories.

| Check ID | Name | Threshold | Pass Criteria | Evidence Collected |
|----------|------|-----------|---------------|-------------------|
| PF-1 | Small Repo Speed | 5.0 seconds | git-fame completes analysis of a small repo (<100 files) within threshold | Elapsed time, threshold, repo path |
| PF-2 | Medium Repo Speed | 30.0 seconds | git-fame completes analysis of a medium repo (100-500 files) within threshold | Elapsed time, threshold, repo path |
| PF-3 | Memory Usage | 500 MB | Peak memory usage (via `resource.getrusage(RUSAGE_CHILDREN)`) stays under threshold. Handles macOS (bytes) vs Linux (KB) `maxrss` units. | Memory MB, threshold, platform |
| PF-4 | Incremental Speed | 150% of first run | Second consecutive run is not more than 50% slower than the first (and >2s total), allowing for OS-level file caching benefit | First run time, second run time, ratio |

### D5: Integration Fit (15% weight, 4 checks)

These checks verify compatibility with the Caldera SoT Engine and DD Platform.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| IF-1 | Path Normalization | All file paths in output are repo-relative: no leading `/`, `\`, `./`; no backslashes; no Windows drive letters; no `..` components | Invalid paths per repo |
| IF-2 | Metric Compatibility | All 4 required metrics present in summary for L5/L8/L9 lens mapping: `author_count` (L8), `total_loc` (L5), `hhi_index` (L9), `bus_factor` (L9) | Found vs missing metrics, lens mapping |
| IF-3 | Directory Rollups | If directory-level data is present, validates it. Otherwise passes (git-fame is an author-level tool; directory rollups are not applicable). | Directory count if present |
| IF-4 | Collector Integration | Output matches collector schema: either Caldera envelope format (metadata: `tool_name`, `tool_version`, `run_id`, `schema_version`, `timestamp`; data: `tool`, `summary`, `authors`) or legacy format (`schema_version`, `generated_at`, `repo_name`, `results`). Also validates `authors` is a list and `summary` is a dict. | Missing fields, type errors per repo |

### D6: Installation (15% weight, 2 checks)

These checks verify git-fame is properly installed and accessible.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| IN-1 | pip Install | `import gitfame; print(gitfame.__version__)` succeeds, or `python -m gitfame --version` returns exit code 0 | Installed version string |
| IN-2 | CLI Help | `python -m gitfame --help` returns exit code 0 with output containing "usage" or "gitfame" or known flag names (`--format`, `--branch`) | Help text presence, output length |

---

## Scoring

### Programmatic Dimension Score

Each dimension score is computed from its individual check results on a 0-5 scale:

```python
def calculate_dimension_score(results: list[dict]) -> float:
    """Calculate score for a dimension (0-5 scale)."""
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.get("passed", False))
    return round(passed / len(results) * 5.0, 2)
```

For example, if a dimension has 6 checks and 5 pass: `5/6 * 5.0 = 4.17`.

### Programmatic Overall Score (Weighted)

The overall programmatic score is a weighted sum of all dimension scores:

```python
weights = {
    "output_quality":       0.20,
    "authorship_accuracy":  0.20,
    "reliability":          0.15,
    "performance":          0.15,
    "integration_fit":      0.15,
    "installation":         0.15,
}

weighted_score = (
    oq_score  * weights["output_quality"]
    + aa_score * weights["authorship_accuracy"]
    + rel_score * weights["reliability"]
    + perf_score * weights["performance"]
    + int_score * weights["integration_fit"]
    + inst_score * weights["installation"]
)
weighted_score = round(weighted_score, 2)
```

The result is a value on the 0-5 scale.

### LLM Judge Score

Each LLM judge returns a score on a 1-5 scale. The overall LLM score is computed as a weighted sum using the judge registry weights:

```python
# From judges/__init__.py JUDGES registry
JUDGES = {
    "authorship_quality":    (AuthorshipQualityJudge,    0.25),
    "bus_factor_accuracy":   (BusFactorAccuracyJudge,    0.20),
    "concentration_metrics": (ConcentrationMetricsJudge, 0.20),
    "evidence_quality":      (EvidenceQualityJudge,      0.15),
    "integration_readiness": (IntegrationReadinessJudge, 0.10),
    "output_completeness":   (OutputCompletenessJudge,   0.10),
}

llm_overall = sum(judge_score * weight for (_, weight), judge_score in ...)
```

### Scorecard Normalization

The `generate_scorecard_json` function normalizes the overall 0-5 score to a 0-1 scale and percentage:

```python
"score": round(overall_score / 5.0, 4),
"score_percent": round(overall_score / 5.0 * 100, 2),
```

---

## Decision Thresholds

Two threshold systems exist in the codebase. The primary system used by `determine_decision()` (for scorecard generation) is:

| Decision | Score Range | Interpretation |
|----------|-------------|----------------|
| STRONG_PASS | >= 4.0 (80%+) | Excellent, production-ready |
| PASS | >= 3.5 (70%+) | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 (60%+) | Acceptable with caveats |
| FAIL | < 3.0 (below 60%) | Significant issues, not ready |

A secondary classification in `classify_score()` uses slightly different breakpoints for the evaluation report:

| Classification | Score Range |
|----------------|-------------|
| STRONG_PASS | >= 4.5 |
| PASS | >= 4.0 |
| MARGINAL_PASS | >= 3.5 |
| MARGINAL_FAIL | >= 3.0 |
| FAIL | < 3.0 |

The scorecard dimension-level status uses a simplified mapping: PASS if score >= 4.0, MARGINAL if score >= 3.0, FAIL otherwise.

---

## LLM Judge Details

### Architecture

All LLM judges inherit from a git-fame-specific `BaseJudge` class (`evaluation/llm/judges/base.py`) which in turn extends the shared `SharedBaseJudge` from `src/shared/evaluation/base_judge.py`. The git-fame base class adds:

- **Caldera envelope handling** via `unwrap_envelope()` for extracting results from either envelope or legacy format
- **Author metrics extraction** (`extract_authors()`, `extract_summary()`)
- **Concentration index calculations** (`calculate_bus_factor()`, `calculate_hhi()`)
- **Per-key placeholder replacement** in prompt templates (supports both `{{ key }}` and `{{ evidence }}` patterns)
- **Empty/error response handling** in `parse_response()` -- returns score=1, confidence=0.0 for malformed LLM output

Default model: `opus-4.5` with 120-second timeout.

### Judge 1: Authorship Quality (25%)

**Class**: `AuthorshipQualityJudge`
**Prompt**: `evaluation/llm/prompts/authorship_quality.md`

**Sub-dimensions**:

| Sub-dimension | Weight | 5 (Best) | 3 (Acceptable) | 1 (Worst) |
|---------------|--------|----------|-----------------|-----------|
| Author Identification | 40% | All authors captured, no duplicates | 85-95% correct, some duplicates | <70% correct, many missing |
| Ownership Accuracy | 35% | Percentages sum to 100%, values reasonable | 1-5% total deviation | >10% deviation, data integrity issues |
| Metric Completeness | 25% | LOC, commits, files all present for all authors | 5-15% of data missing | >30% critical data missing |

**Evidence collected**:
- Aggregated authorship data from all repos (total authors, total LOC)
- Top 15 authors across all repos (sorted by ownership %)
- Per-repo summaries (author count, total LOC, top author %, ownership validation)
- Ownership percentage validation (sum-to-100% check)
- Ground truth comparison (accuracy, matches, mismatches, missing) when available
- Synthetic baseline context and interpretation guidance

**Ground truth assertions**: Before LLM evaluation, validates ownership sums to 100% and author count matches expected. Failures are reported alongside the LLM score.

### Judge 2: Bus Factor Accuracy (20%)

**Class**: `BusFactorAccuracyJudge`
**Prompt**: `evaluation/llm/prompts/bus_factor_accuracy.md`

**Sub-dimensions**:

| Sub-dimension | Weight | 5 (Best) | 3 (Acceptable) | 1 (Worst) |
|---------------|--------|----------|-----------------|-----------|
| Calculation Accuracy | 50% | All bus factors match recalculated values | >80% correct | <50% correct, systematic errors |
| Distribution Consistency | 30% | Bus factor perfectly reflects cumulative ownership | Some inconsistencies | Bus factor contradicts ownership data |
| Risk Assessment Validity | 20% | Risk levels accurately reflect implications | Some questionable assessments | Risk assessment unreliable |

**Evidence collected**:
- Per-repo bus factor analysis: reported vs independently calculated bus factor, match status
- Cumulative ownership coverage for top 10 authors (rank, name, ownership %, cumulative %)
- Risk level classification: critical (bf=1), high (bf<=2), moderate (bf<=4), low (bf>4)
- Ground truth comparison when available
- Overall accuracy percentage across all repos

**Ground truth assertions**: Validates that bus factor matches expected value from ground truth for each repo.

### Judge 3: Concentration Metrics (20%)

**Class**: `ConcentrationMetricsJudge`
**Prompt**: `evaluation/llm/prompts/concentration_metrics.md`

**Sub-dimensions**:

| Sub-dimension | Weight | 5 (Best) | 3 (Acceptable) | 1 (Worst) |
|---------------|--------|----------|-----------------|-----------|
| HHI Accuracy | 40% | All HHI values within 1% of recalculated | >80% correct | <50% correct, systematic errors |
| Top-N Accuracy | 35% | All top-N values match exactly | Some values off by >1pp | Top-N calculations unreliable |
| Internal Consistency | 25% | All metrics mutually consistent | Some inconsistencies | Metrics contradict each other |

**Evidence collected**:
- Per-repo concentration analysis: reported HHI, top_author_pct, top_two_pct vs independently calculated values
- Validation deltas: HHI difference (tolerance 0.01), top-1 difference (tolerance 1.0pp)
- Concentration level classification: highly_concentrated (HHI >= 0.50), moderately_concentrated (>= 0.25), unconcentrated (>= 0.15), highly_distributed (< 0.15)
- Independent recalculation of Gini coefficient, top-3 %, and top-5 %
- Overall HHI accuracy and top-author accuracy percentages

**Ground truth assertions**: Validates HHI within 0.02 and top_author_pct within 2.0pp of expected values.

### Judge 4: Evidence Quality (15%)

**Class**: `EvidenceQualityJudge`
**Prompt**: `evaluation/llm/prompts/evidence_quality.md`

**Sub-dimensions**:

| Sub-dimension | Weight | 5 (Best) | 3 (Acceptable) | 1 (Worst) |
|---------------|--------|----------|-----------------|-----------|
| Required Field Coverage | 40% | 100% of authors have all required fields | 85-95% coverage | <70% coverage |
| Optional Field Coverage | 30% | >90% of authors have all optional fields | 50-70% coverage | <30% coverage |
| Provenance Quality | 30% | All repos have complete provenance | 70-90% repos have provenance | <50% have provenance |

**Required author fields**: `name`, `surviving_loc`, `commit_count`, `ownership_pct`
**Optional author fields**: `insertions_total`, `deletions_total`, `files_touched`
**Required summary fields**: `author_count`, `total_loc`, `bus_factor`, `hhi_index`

**Evidence collected**:
- Per-repo field coverage percentages (required and optional)
- Per-field coverage rates across all authors
- Provenance presence (tool name, commands)
- Summary field completeness

**Ground truth assertions**: Validates all authors have all 4 required fields.

### Judge 5: Integration Readiness (10%)

**Class**: `IntegrationReadinessJudge`
**Prompt**: `evaluation/llm/prompts/integration_readiness.md`

**Sub-dimensions**:

| Sub-dimension | Weight | 5 (Best) | 3 (Acceptable) | 1 (Worst) |
|---------------|--------|----------|-----------------|-----------|
| Schema Completeness | 40% | 100% of required fields present | 85-95% coverage | <70% coverage |
| Type Correctness | 30% | No type issues | 5-15% repos with issues | >30% repos with issues |
| Format Consistency | 30% | Identical structure across repos | Some structural inconsistencies | Highly inconsistent |

**Required metadata fields**: `tool_name`, `tool_version`, `run_id`, `repo_id`, `branch`, `commit`, `timestamp`, `schema_version`
**Required data fields**: `tool`, `tool_version`, `repo_name`, `summary`, `authors`
**Required summary fields**: `author_count`, `total_loc`, `hhi_index`, `bus_factor`, `top_author_pct`

**Evidence collected**:
- Per-repo metadata/data/summary field presence and coverage percentages
- Type validation: schema_version is semver, timestamp is ISO 8601, `author_count`/`total_loc`/`bus_factor` are integers
- Overall integration score and type issue rate

**Ground truth assertions**: Validates `metadata` section contains `tool_name`, `schema_version`, `timestamp`, and `data` section contains `summary` and `authors`.

### Judge 6: Output Completeness (10%)

**Class**: `OutputCompletenessJudge`
**Prompt**: `evaluation/llm/prompts/output_completeness.md`

**Sub-dimensions**:

| Sub-dimension | Weight | 5 (Best) | 3 (Acceptable) | 1 (Worst) |
|---------------|--------|----------|-----------------|-----------|
| Section Presence | 25% | All sections present in all repos | 5-15% of repos missing sections | >30% missing critical sections |
| Author Data Quality | 40% | All authors have all required fields | 85-95% complete | <70% complete |
| Summary Data Quality | 25% | All summary metrics present and valid | 85-95% present | <70% present |
| Error Rate | 10% | No errors in any repo | 5-15% repos with errors | >30% repos with errors |

**Evidence collected**:
- Per-repo section presence (summary, authors, provenance)
- Author quality flags: has_names, has_loc, has_ownership, has_commits
- Summary quality flags: has_author_count, has_total_loc, has_hhi, has_bus_factor, has_top_author_pct
- Error condition detection
- Weighted completeness score per repo: section_score * 0.2 + author_score * 0.5 + summary_score * 0.3

**Ground truth assertions**: Validates no error conditions, authors list non-empty, and summary present for each repo.

### Additional Prompt Templates

Two supplementary prompt templates exist but are not wired to dedicated judge classes:

| Prompt File | Purpose |
|-------------|---------|
| `prompts/accuracy.md` | Generic accuracy evaluation (1-5 scale with PASS/FAIL verdict) |
| `prompts/actionability.md` | Generic actionability evaluation (1-5 scale with PASS/FAIL verdict) |

These use a simpler response format (`score`, `verdict`, `reasoning`) compared to the full judge prompts.

---

## Ground Truth

### Methodology

Ground truth is generated from **synthetic repositories** created by `scripts/build_repos.py` with known, controlled author distributions. Each repository has a specific ownership pattern designed to test different aspects of authorship analysis.

### Synthetic Repository Scenarios

6 ground truth files in `evaluation/ground-truth/`:

| File | Scenario | Authors | Key Properties |
|------|----------|---------|----------------|
| `synthetic.json` | Master index | 5 repos | Combined reference with HHI/bus_factor ranges per repo |
| `single-author.json` | Maximum concentration | 1 (Alice) | HHI=1.0, bus_factor=1, top_author_pct=100%, 4 files ~350 LOC |
| `multi-author.json` | 50/30/20 split | 3 (Alice/Bob/Carol) | HHI~0.38, bus_factor=1, 6 files ~350 LOC |
| `bus-factor-1.json` | Dominant author (90%) | 3 (Alice 90%, Bob 5%, Carol 5%) | HHI~0.815, bus_factor=1, high_bus_factor_risk=true |
| `balanced.json` | Equal contributions (25% each) | 4 (Alice/Bob/Carol/Dave) | HHI=0.25, bus_factor=2, gini~0.0 |
| `multi-branch.json` | Multiple branches | 4 (varying across branches) | 5 branches, merge history, HHI 0.20-0.35 |

### Ground Truth Schema (V1.0)

Each scenario file follows this structure:

```json
{
  "schema_version": "1.0",
  "scenario": "<scenario-name>",
  "description": "<what this scenario tests>",
  "repo_path": "eval-repos/synthetic/<name>",
  "expected": {
    "summary": {
      "author_count": <int>,
      "file_count": {"min": <int>, "max": <int>},
      "total_loc": {"min": <int>, "max": <int>}
    },
    "concentration_metrics": {
      "bus_factor": <int or {"min": <int>, "max": <int>}>,
      "hhi_index": {"min": <float>, "max": <float>},
      "gini_coefficient": {"min": <float>, "max": <float>},
      "top_author_pct": {"min": <float>, "max": <float>}
    },
    "authors": [
      {
        "name": "<author name>",
        "email": "<email>",
        "loc_pct": {"min": <float>, "max": <float>},
        "file_count": <int or {"min": <int>, "max": <int>}>,
        "commit_count": {"min": <int>, "max": <int>}
      }
    ]
  },
  "risk_indicators": {
    "high_bus_factor_risk": <boolean>
  },
  "thresholds": {
    "max_analysis_time_ms": <int>
  }
}
```

**Range format**: Numeric expected values use `{"min": X, "max": Y}` to accommodate natural variance in LOC counting, merge handling, and rounding. Exact values (e.g., `author_count`, single-value `bus_factor`) are specified as plain integers.

### Master Index (synthetic.json)

The `synthetic.json` file serves as a compact reference used by the `AuthorshipAccuracyChecks` class. It uses a nested structure:

```json
{
  "repos": {
    "<repo-name>": {
      "description": "...",
      "expected": {
        "author_count": <int>,
        "bus_factor": <int>,
        "hhi_index": {"min": <float>, "max": <float>},
        "top_author_pct": {"min": <float>, "max": <float>}
      }
    }
  }
}
```

### Expected Value Formats

| Metric | Type | Tolerance | Example |
|--------|------|-----------|---------|
| `author_count` | Exact integer | 0 | `3` |
| `bus_factor` | Exact integer or range | 0 (exact) or min/max | `1` or `{"min": 1, "max": 2}` |
| `hhi_index` | Float range | 0.1 (AA-6 check) | `{"min": 0.35, "max": 0.42}` |
| `top_author_pct` | Float range | 5.0pp (AA-7 check) | `{"min": 48.0, "max": 53.0}` |
| `gini_coefficient` | Float range | N/A (LLM only) | `{"min": 0.15, "max": 0.25}` |
| `total_loc` | Integer range | 0 (AA-1 exact match) | `{"min": 300, "max": 400}` |
| `loc_pct` | Float range | 5.0pp (AA-4 check) | `{"min": 48.0, "max": 53.0}` |

### Scenario Coverage

| Property | Single-Author | Multi-Author | Bus-Factor-1 | Balanced | Multi-Branch |
|----------|:------------:|:------------:|:------------:|:--------:|:------------:|
| 1 author | X | | | | |
| 3 authors | | X | X | | |
| 4 authors | | | | X | X |
| HHI = 1.0 | X | | | | |
| HHI moderate | | X | | | X |
| HHI high | | | X | | |
| HHI low | | | | X | |
| Bus factor = 1 | X | X | X | | |
| Bus factor = 2 | | | | X | |
| Bus factor variable | | | | | X |
| Branching | | | | | X |
| High risk | | | X | | |
| Low risk | | | | X | X |

---

## Evidence Collection

### Programmatic Evidence

Every programmatic check produces a standardized result via the `check_result()` utility:

```python
def check_result(check: str, passed: bool, message: str) -> dict:
    return {
        "check": check,     # e.g., "OQ-1", "AA-3", "PF-2"
        "passed": passed,    # True or False
        "message": message,  # Human-readable explanation with specifics
    }
```

Messages include concrete values (e.g., "Completed in 0.83s (threshold: 5.0s)", "LOC mismatches: multi-author: expected 350, got 352").

### LLM Judge Evidence

Each judge collects a structured evidence dictionary via its `collect_evidence()` method. Common evidence patterns:

- **`total_repos`**: Number of repositories analyzed
- **`evaluation_mode`**: "synthetic" or "real_world"
- **`ground_truth_comparison`**: Per-repo accuracy/match data when ground truth is available
- **`synthetic_baseline`**: Results from synthetic evaluation for calibration
- **`interpretation_guidance`**: Context-specific guidance for the LLM

Evidence is serialized to JSON and injected into prompt templates via `{{ evidence }}` and `{{ key }}` placeholders. The `build_prompt()` method raises `ValueError` if any placeholders remain unresolved.

### LLM Judge Response Format

All judges expect a JSON response from the LLM:

```json
{
  "score": 4,
  "confidence": 0.85,
  "reasoning": "Detailed explanation of the evaluation...",
  "evidence_cited": ["specific data points referenced"],
  "recommendations": ["improvement suggestions"],
  "sub_scores": {
    "<sub_dimension_1>": 4,
    "<sub_dimension_2>": 5,
    "<sub_dimension_3>": 3
  }
}
```

### LLM Judge Confidence

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review recommended |

---

## Utility Functions

### Analysis Loading (checks/utils.py)

| Function | Purpose |
|----------|---------|
| `load_analysis_bundle(output_dir, repo_name)` | Load analysis JSON from multiple possible locations (latest/, runs/, direct) |
| `load_ground_truth(ground_truth_file)` | Load ground truth, handles both flat and nested `{repos: ...}` structure |
| `find_repo_analyses(output_dir)` | Discover all repo analyses: checks `combined_analysis.json`, individual JSONs, and runs directory |
| `check_result(check, passed, message)` | Create standardized check result dictionary |

### LLM Judge Utilities (judges/utils.py)

| Function | Purpose |
|----------|---------|
| `load_analysis_bundle(output_dir)` | Load all JSON analyses, aggregate author/LOC/commit totals |
| `load_ground_truth(ground_truth_dir)` | Load all ground truth JSON files from directory |
| `compare_authors(actual, expected, tolerance)` | Compare author lists: matches, mismatches, missing, extra authors. Default 5% tolerance. |
| `validate_ownership_percentages(authors)` | Validate percentages are non-negative, <=100%, and sum within 1% of 100% |
| `calculate_concentration_metrics(authors)` | Independently calculate HHI, Gini, bus factor, and top-N% from author ownership |

---

## Running Evaluations

### Programmatic Evaluation

```bash
# From the git-fame tool directory
make evaluate

# Or directly
.venv/bin/python scripts/evaluate.py --output evaluation/results/evaluation_report.json
```

**Prerequisites**: Run `make build-repos` to create synthetic repositories, then `make analyze` to generate output.

**Outputs**:
- `evaluation/results/evaluation_report.json` -- Full evaluation results with all check details
- `evaluation/scorecard.md` -- Markdown scorecard with dimension table and per-check results
- `evaluation/scorecard.json` -- Structured scorecard with dimension IDs (D1-D6) and check arrays

### LLM Evaluation

```bash
# From the git-fame tool directory
make evaluate-llm

# Or directly with model selection
.venv/bin/python -m evaluation.llm.orchestrator --model opus-4.5 --output evaluation/results/llm_evaluation.json
```

**Outputs**:
- `evaluation/results/llm_evaluation.json` -- Per-judge scores, confidence, reasoning, sub-scores

### Evaluation Output Structure

```
evaluation/
├── EVAL_STRATEGY.md                    # This document
├── scorecard.md                        # Programmatic scorecard (generated)
├── scorecard.json                      # Structured scorecard (generated)
├── ground-truth/
│   ├── synthetic.json                  # Master ground truth index
│   ├── single-author.json             # Single-author scenario
│   ├── multi-author.json              # Multi-author (50/30/20) scenario
│   ├── bus-factor-1.json              # Dominant author (90%) scenario
│   ├── balanced.json                  # Equal contributions scenario
│   └── multi-branch.json             # Multi-branch scenario
├── results/
│   ├── evaluation_report.json         # Programmatic results (generated)
│   └── llm_evaluation.json           # LLM judge results (generated)
└── llm/
    ├── judges/
    │   ├── __init__.py                # Judge registry with weights
    │   ├── base.py                    # Git-fame-specific BaseJudge
    │   ├── utils.py                   # Comparison and calculation utilities
    │   ├── authorship_quality.py      # 25% weight
    │   ├── bus_factor_accuracy.py     # 20% weight
    │   ├── concentration_metrics.py   # 20% weight
    │   ├── evidence_quality.py        # 15% weight
    │   ├── integration_readiness.py   # 10% weight
    │   └── output_completeness.py     # 10% weight
    └── prompts/
        ├── authorship_quality.md      # Author attribution prompt
        ├── bus_factor_accuracy.md     # Bus factor prompt
        ├── concentration_metrics.md   # HHI/Gini prompt
        ├── evidence_quality.md        # Data completeness prompt
        ├── integration_readiness.md   # SoT Engine compliance prompt
        ├── output_completeness.md     # Output structure prompt
        ├── accuracy.md                # Generic accuracy prompt (unused)
        └── actionability.md           # Generic actionability prompt (unused)
```

---

## Extending the Evaluation

### Adding a New Programmatic Check

1. Add the check method to the appropriate `*Checks` class (e.g., `_check_new_thing()` in `authorship_accuracy.py`)
2. Add the method call to the class's `run_all()` list
3. Use the `check_result()` utility to return standardized results
4. Update this document's Check Catalog with the new check ID, criteria, and evidence

### Adding a New LLM Judge

1. Create a new judge class in `evaluation/llm/judges/` inheriting from `BaseJudge`
2. Implement `dimension_name`, `weight`, `collect_evidence()`, `get_default_prompt()`, and `run_ground_truth_assertions()`
3. Create a prompt template in `evaluation/llm/prompts/<dimension_name>.md` with `{{ evidence }}` placeholder
4. Register the judge in `evaluation/llm/judges/__init__.py` by adding to `JUDGES` dict and `__all__`
5. Ensure weights in `JUDGES` still sum to 1.0

### Adding a New Ground Truth Scenario

1. Create a new JSON file in `evaluation/ground-truth/` following the V1.0 schema
2. Add the scenario's `build_*()` function to `scripts/build_repos.py`
3. Add the repo entry to `synthetic.json` master index
4. Run `make build-repos && make analyze && make evaluate` to validate

### Updating Thresholds

Performance thresholds are defined in check methods:

```python
# In performance.py
threshold_seconds = 5.0   # PF-1: small repo speed
threshold_seconds = 30.0  # PF-2: medium repo speed
threshold_mb = 500.0      # PF-3: memory usage

# In authorship_accuracy.py
tolerance = 5.0           # AA-4: ownership percentage tolerance (pp)
tolerance = 0.1           # AA-6: HHI tolerance
tolerance = 5.0           # AA-7: top-two percentage tolerance (pp)
```

---

## References

- [git-fame (gitfame)](https://github.com/casperdcl/git-fame) -- Line-of-code attribution tool
- [Herfindahl-Hirschman Index](https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_index) -- Concentration metric
- [Bus Factor](https://en.wikipedia.org/wiki/Bus_factor) -- Key-person risk metric
- [Gini Coefficient](https://en.wikipedia.org/wiki/Gini_coefficient) -- Inequality measure
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685) -- Evaluation methodology
- [Caldera CLAUDE.md](../../CLAUDE.md) -- Project conventions and architecture
