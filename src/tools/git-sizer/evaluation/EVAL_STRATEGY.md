# Evaluation Strategy: Git-Sizer

This document describes the evaluation methodology for the git-sizer repository health analysis tool. Git-sizer measures Git object sizes (blobs, trees, commits), detects threshold violations, assigns health grades, and identifies LFS candidates.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation in a hybrid approach:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- validates size measurements, metric coverage, edge case handling, and performance |
| LLM Judges | 40% | Semantic understanding -- evaluates threshold quality, actionability, accuracy nuance, and integration fit |

### Why Hybrid?

Programmatic checks excel at verifying concrete facts: "Did the bloated repo report a max blob size above 5 MiB?" LLM judges add a layer of semantic reasoning that programmatic checks cannot: "Are the threshold severity levels calibrated correctly across the spectrum of repository health?" Together, they provide both precision and nuance.

### What "Correct" Means for Git-Sizer

Correctness for git-sizer is defined along four axes:

1. **Size Accuracy** -- Blob, tree, commit, and path measurements match ground truth within specified tolerances. A 10 MiB blob must be detected as approximately 10 MiB, not 1 MiB or 100 MiB.
2. **Threshold Quality** -- Healthy repositories receive no violations and high grades; problematic repositories (bloated binaries, wide trees, deep history) are correctly flagged with appropriate severity levels.
3. **Actionability** -- Reports include specific LFS candidate paths, violation metrics with current values, and health grades that enable quick triage.
4. **Integration Fit** -- Output conforms to Caldera envelope format, maps cleanly to DuckDB landing zone tables, and does not duplicate metrics already provided by other tools.

---

## Dimension Summary

### Programmatic Dimensions

Programmatic evaluation runs 28 checks across 4 categories. Each category contributes equally to the programmatic score (25% per category).

| Dimension | Checks | Weight (of Programmatic) | Method | Focus |
|-----------|--------|--------------------------|--------|-------|
| Accuracy | AC-1 to AC-8 | 25% | Ground truth comparison | Blob/tree/commit size correctness |
| Coverage | CV-1 to CV-8 | 25% | Schema inspection | Metric presence across all repos |
| Edge Cases | EC-1 to EC-8 | 25% | Boundary validation | Minimal repos, deep paths, output structure |
| Performance | PF-1 to PF-4 | 25% | Timing / output size | Speed thresholds and memory efficiency |

### LLM Judge Dimensions

| Judge | Weight (of LLM) | Sub-Dimensions | Focus |
|-------|------------------|----------------|-------|
| Size Accuracy | 35% | Blob (40%), Tree (30%), Commit (30%) | Measurement correctness |
| Threshold Quality | 25% | True Positives (40%), False Positives (30%), Severity Calibration (30%) | Violation detection quality |
| Actionability | 20% | LFS Recommendations (40%), Violation Clarity (30%), Prioritization (30%) | Report usefulness |
| Integration Fit | 20% | Gap Coverage (40%), Schema Compatibility (30%), Performance (30%) | Caldera platform fit |

### Combined Score Calculation

```python
# Programmatic score is 0.0 to 1.0 (average of all 28 check scores)
# Normalize to 1-5 scale
programmatic_normalized = programmatic_score * 5.0

# LLM score is already 1-5 (weighted average of 4 judges)
llm_score = (
    size_accuracy_score * 0.35 +
    threshold_quality_score * 0.25 +
    actionability_score * 0.20 +
    integration_fit_score * 0.20
)

# Final combined score
combined_score = (0.60 * programmatic_normalized) + (0.40 * llm_score)
```

---

## Check Catalog (28 Programmatic Checks)

### Accuracy Checks (AC-1 to AC-8)

Located in `scripts/checks/accuracy.py`. These checks compare git-sizer output against ground truth from synthetic repositories.

| ID | Name | Severity | Pass Criteria | Evidence Collected |
|----|------|----------|---------------|-------------------|
| AC-1 | Large blob detection | Critical | Bloated repo: max_blob_size >= 5 MiB | `max_blob_bytes`, `expected_min_bytes` |
| AC-2 | Total blob size accuracy | Critical | Bloated repo: blob_total_size >= 15 MiB | `total_blob_bytes`, `expected_min_bytes` |
| AC-3 | Commit count accuracy | High | Deep-history repo: commit_count within 490-510 (expected ~501) | `commit_count`, `expected` |
| AC-4 | Tree entries detection | High | Wide-tree repo: max_tree_entries >= 900 (expected ~1000) | `max_tree_entries`, `expected` |
| AC-5 | Path depth detection | High | Wide-tree repo: max_path_depth >= 15 (expected ~20) | `max_path_depth`, `expected` |
| AC-6 | Health grade accuracy | Medium | Healthy repo grade in A/B; bloated and wide-tree grades in C/D/F; at least 50% correct | `correct`, `total` |
| AC-7 | LFS candidate identification | Medium | Bloated repo has at least 1 LFS candidate | `lfs_candidates` |
| AC-8 | Threshold violation detection | Medium | Violation counts match expectations per repo (bloated >= 1, wide-tree >= 2, healthy = 0) | `correct`, `total` |

#### AC-1 Scoring Formula

```python
ac1_score = min(1.0, max_blob / (10 * 1024 * 1024))
ac1_passed = max_blob >= 5 * 1024 * 1024
```

The score scales linearly from 0 to 1 based on the detected max blob size relative to the 10 MiB expected value. The pass threshold is set at 5 MiB (50% of expected) to allow for synthetic repo variation.

#### AC-3 Scoring Formula

```python
ac3_passed = 490 <= commit_count <= 510
ac3_score = 1.0 if ac3_passed else max(0, 1.0 - abs(commit_count - 501) / 501)
```

Uses a range-based pass with graceful degradation: scores decrease linearly as the detected count diverges from the expected 501.

#### AC-6 Scoring Formula

```python
ac6_score = grade_correct / grade_total if grade_total > 0 else 0.0
ac6_passed = ac6_score >= 0.5
```

Checks each synthetic repo against expected grade bands. Healthy should receive A or B; bloated and wide-tree should receive C, D, or F.

#### AC-8 Scoring Formula

```python
# Per repo: at least half of expected violations detected
if actual_count >= expected_count * 0.5:
    violations_correct += 1
ac8_score = violations_correct / violations_total
ac8_passed = ac8_score >= 0.5
```

### Coverage Checks (CV-1 to CV-8)

Located in `scripts/checks/coverage.py`. These checks verify that git-sizer populates all expected metric fields across all analyzed repositories.

| ID | Name | Severity | Pass Criteria | Expected Metrics | Evidence Collected |
|----|------|----------|---------------|------------------|-------------------|
| CV-1 | Blob metrics coverage | High | >= 80% of repos have all blob metrics | `blob_count`, `blob_total_size`, `max_blob_size` | `metrics`, `coverage` |
| CV-2 | Tree metrics coverage | High | >= 80% of repos have all tree metrics | `tree_count`, `tree_total_size`, `tree_total_entries`, `max_tree_entries` | `metrics`, `coverage` |
| CV-3 | Commit metrics coverage | High | >= 80% of repos have all commit metrics | `commit_count`, `commit_total_size`, `max_commit_size`, `max_history_depth` | `metrics`, `coverage` |
| CV-4 | Reference metrics coverage | Medium | >= 80% of repos have all reference metrics | `reference_count`, `branch_count`, `tag_count` | `metrics`, `coverage` |
| CV-5 | Path metrics coverage | Medium | >= 80% of repos have all path metrics | `max_path_depth`, `max_path_length` | `metrics`, `coverage` |
| CV-6 | Expanded checkout metrics | Medium | >= 80% of repos have expanded metrics | `expanded_tree_count`, `expanded_blob_count`, `expanded_blob_size` | `metrics`, `coverage` |
| CV-7 | Health grade coverage | Critical | >= 80% of repos have a health grade assigned | (boolean presence) | `coverage`, `total` |
| CV-8 | Violation detail coverage | Medium | >= 80% of violations have required fields (`metric`, `level`) | (field completeness) | `complete`, `total` |

#### Coverage Scoring Formula

All coverage checks use the same pattern:

```python
coverage_score = fields_present / (num_repos * num_expected_fields)
passed = coverage_score >= 0.8
```

For CV-8, if there are no violations to check, the score defaults to 1.0 (pass by default).

### Edge Case Checks (EC-1 to EC-8)

Located in `scripts/checks/edge_cases.py`. These checks validate behavior at boundary conditions.

| ID | Name | Severity | Pass Criteria | Evidence Collected |
|----|------|----------|---------------|-------------------|
| EC-1 | Minimal repo handling | High | Healthy repo analyzed with commit_count > 0 | `repo`, `analyzed` |
| EC-2 | Large history handling | High | Deep-history repo analyzed with commit_count > 400 | `repo`, `analyzed` |
| EC-3 | Wide tree handling | High | Wide-tree repo analyzed with max_tree_entries > 500 | `repo`, `analyzed` |
| EC-4 | Deep path handling | Medium | Wide-tree repo detected max_path_depth > 10 | `max_depth` |
| EC-5 | No violations case | Medium | Healthy repo has exactly 0 violations | `violations` |
| EC-6 | Multiple violations case | Medium | Wide-tree repo has >= 2 violations | `violations` |
| EC-7 | JSON output validity | High | >= 75% of repos have required fields (`tool`, `health_grade`, `metrics`) | `required`, `valid`, `total` |
| EC-8 | Raw output preservation | Low | >= 80% of repos preserve raw git-sizer output | `preserved`, `total` |

#### Edge Case Scoring

Edge case checks are binary (0.0 or 1.0) except for EC-7 and EC-8 which use proportional scoring:

```python
# EC-7: Proportional based on field completeness
ec7_score = fields_valid / total_checks
ec7_passed = ec7_score >= 0.75

# EC-8: Proportional based on raw output preservation
ec8_score = raw_preserved / len(repos)
ec8_passed = ec8_score >= 0.8
```

### Performance Checks (PF-1 to PF-4)

Located in `scripts/checks/performance.py`. These checks validate speed and resource usage.

| ID | Name | Severity | Threshold | Pass Criteria | Evidence Collected |
|----|------|----------|-----------|---------------|-------------------|
| PF-1 | Total analysis speed | High | < 5,000 ms | All synthetic repos analyzed under 5 seconds total | `duration_ms`, `threshold_ms` |
| PF-2 | Per-repo analysis speed | Medium | < 2,000 ms | >= 75% of repos analyzed under 2 seconds each | `fast_repos`, `slow_repos`, `threshold_ms` |
| PF-3 | Large repo handling | Medium | < 30,000 ms | Deep-history repo (500+ commits) under 30 seconds | `duration_ms`, `threshold_ms` |
| PF-4 | Output size efficiency | Low | < 100 KB | Total raw output under 100 KB across all repos | `raw_size_bytes`, `threshold_bytes` |

#### Performance Scoring Formula

```python
# PF-1: Inverse ratio (faster = higher score, capped at 1.0)
pf1_score = min(1.0, threshold / max(duration, 1))

# PF-2: Proportion of repos under threshold
pf2_score = fast_repos / len(repos)
pf2_passed = pf2_score >= 0.75

# PF-3: Same inverse ratio as PF-1
pf3_score = min(1.0, threshold / max(duration, 1))

# PF-4: Same inverse ratio
pf4_score = min(1.0, threshold / max(total_raw_size, 1))
```

---

## Scoring System

### Overall Programmatic Score

The overall programmatic score is computed as the simple mean of all 28 check scores:

```python
class EvaluationReport:
    @property
    def score(self) -> float:
        """Overall score (0.0 to 1.0)."""
        if not self.checks:
            return 0.0
        return sum(c.score for c in self.checks) / len(self.checks)
```

Category-level scores use the same averaging within each category:

```python
@property
def score_by_category(self) -> dict[str, float]:
    categories: dict[str, list[float]] = {}
    for check in self.checks:
        cat = check.category.value
        categories.setdefault(cat, []).append(check.score)
    return {
        cat: sum(scores) / len(scores)
        for cat, scores in categories.items()
    }
```

### Normalized Score (1-5 Scale)

For scorecard display, the 0-1 programmatic score is normalized to a 1-5 scale:

```python
normalized_score = report.score * 5.0
```

### Category Dimension Weights in Scorecard

Each category receives equal weight in the scorecard:

```python
weight = 1.0 / len(report.score_by_category)  # 0.25 for 4 categories
weighted_score = score * 5.0 / len(report.score_by_category)
```

### LLM Combined Score

The LLM evaluation produces a weighted average across 4 judges:

```python
JUDGES = {
    "size_accuracy": (SizeAccuracyJudge, 0.35),
    "threshold_quality": (ThresholdQualityJudge, 0.25),
    "actionability": (ActionabilityJudge, 0.20),
    "integration_fit": (IntegrationFitJudge, 0.20),
}

llm_score = sum(judge_score * weight for judge_score, weight in judge_results)
```

---

## Decision Thresholds

### Overall Decision

The decision is derived from the programmatic score (0-1) multiplied by 5.0 to produce a normalized score:

```python
def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on score (0-1)."""
    normalized = score * 5.0
    if normalized >= 4.0:
        return "STRONG_PASS"
    elif normalized >= 3.5:
        return "PASS"
    elif normalized >= 3.0:
        return "WEAK_PASS"
    return "FAIL"
```

| Decision | Normalized Score | Raw Score (0-1) | Interpretation |
|----------|-----------------|-----------------|----------------|
| STRONG_PASS | >= 4.0 | >= 0.80 | Excellent, production-ready |
| PASS | >= 3.5 | >= 0.70 | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 | >= 0.60 | Acceptable with caveats |
| FAIL | < 3.0 | < 0.60 | Significant issues |

### Category-Level Pass Criteria

In the console report, individual categories are evaluated at the 75% threshold:

```python
pct = passed / total * 100 if total > 0 else 0
status = "PASS" if pct >= 75 else "FAIL"
```

### Exit Code

The process exits 0 if the overall score >= 0.75, otherwise exits 1:

```python
sys.exit(0 if report.score >= 0.75 else 1)
```

---

## LLM Judge Details

### Size Accuracy Judge (35% of LLM Score)

**Class:** `SizeAccuracyJudge` in `evaluation/llm/judges/size_accuracy.py`
**Prompt Template:** `evaluation/llm/prompts/size_accuracy.md`

Evaluates correctness of blob, tree, commit, and path measurements.

#### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Blob Accuracy | 40% | Blob sizes correctly measured (max_blob_size, blob_total_size) |
| Tree Accuracy | 30% | Tree entry counts correct (max_tree_entries, tree_count) |
| Commit Accuracy | 30% | Commit counts and history depth correct |

#### Scoring Rubric

**Synthetic Repos (strict ground truth):**

| Score | Criteria |
|-------|----------|
| 5 | All measurements within 5% of expected values |
| 4 | Most measurements accurate, minor variations |
| 3 | Generally accurate, some significant variations |
| 2 | Several measurements significantly off |
| 1 | Measurements unreliable or missing |

**Real-World Repos (when synthetic baseline validated):**

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, measurements present and consistent |
| 4 | Minor schema issues but measurements internally consistent |
| 3 | Schema issues OR questionable measurement consistency |
| 2 | Multiple schema issues AND inconsistent measurements |
| 1 | Broken output, missing required fields |

#### Evidence Collected

- `repo_metrics`: Per-repo metrics summary (blob count, sizes in MB, tree count, entries, commit count, path depth/length)
- `accuracy_results`: Pass/fail for each ground truth comparison (bloated_max_blob, bloated_total_blob, deep_history_commits, wide_tree_entries, wide_tree_depth)
- `passed_tests`, `total_tests`, `pass_rate`: Aggregate accuracy stats
- `expected_values`: Ground truth expectations per synthetic repo
- `evaluation_mode`: "synthetic" or "real_world"
- `synthetic_baseline`: Synthetic validation context for real-world evaluation
- `interpretation_guidance`: Evaluation strategy context string

#### Ground Truth Assertions

If ground truth assertions fail, the LLM judge score is capped. Assertions check:
- All repos have non-empty metrics
- Required fields present: `blob_count`, `commit_count`, `tree_count`

---

### Threshold Quality Judge (25% of LLM Score)

**Class:** `ThresholdQualityJudge` in `evaluation/llm/judges/threshold_quality.py`
**Prompt Template:** `evaluation/llm/prompts/threshold_quality.md`

Evaluates appropriateness of threshold-based violation detection and health grading.

#### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| True Positive Rate | 40% | Problematic repos correctly flagged |
| False Positive Rate | 30% | Healthy repos not incorrectly flagged |
| Severity Calibration | 30% | Threshold levels match actual severity |

#### Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Perfect threshold accuracy, no false positives/negatives |
| 4 | Excellent thresholds, rare edge case misses |
| 3 | Good thresholds, some calibration issues |
| 2 | Thresholds too aggressive or too lenient |
| 1 | Thresholds unreliable, many misclassifications |

#### Threshold Levels

Git-sizer uses severity levels to indicate concern:

| Level | Symbol | Meaning |
|-------|--------|---------|
| 1 | `*` | Acceptable (minor concern) |
| 2 | `**` | Somewhat concerning |
| 3 | `***` | Very concerning |
| 4 | `!!!!` | Alarm bells |

#### Evidence Collected

- `violation_summary`: Per-repo violations with metric, value, level, and raw_value
- `grade_distribution`: Count of repos per grade letter (A, B, C, D, F)
- `expected_outcomes`: Expected violation counts and grade ranges per synthetic repo
- `quality_results`: Per-repo pass/fail for violations and grade accuracy
- `passed_tests`, `total_tests`, `pass_rate`: Aggregate quality stats
- `level_distribution`: Distribution of violation severity levels across all repos

#### Expected Outcomes for Synthetic Repos

| Repository | Expected Violations | Expected Grade | Description |
|------------|-------------------|----------------|-------------|
| healthy | 0 | A, A+ | Clean repo, no size issues |
| bloated | >= 1 | B, C, C+, D | Large binary files trigger blob size violations |
| wide-tree | >= 2 | C, C+, D, D+, F | Wide tree + deep paths trigger violations |
| deep-history | 0 | A, A+, B | Many commits but within normal range |

#### Ground Truth Assertions

- Healthy repo must have 0 violations
- Bloated repo must have >= 1 violation
- All repos must have health grades assigned

---

### Actionability Judge (20% of LLM Score)

**Class:** `ActionabilityJudge` in `evaluation/llm/judges/actionability.py`
**Prompt Template:** `evaluation/llm/prompts/actionability.md`

Evaluates whether developers can easily understand and act on git-sizer findings.

#### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| LFS Recommendations | 40% | Clear identification of LFS candidates with file names/paths |
| Violation Clarity | 30% | Messages explain issues clearly with metric names and values |
| Prioritization Support | 30% | Grades enable quick assessment and triage |

#### Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Clear LFS recommendations, detailed violations, actionable grades |
| 4 | Good recommendations, clear messages, useful grades |
| 3 | Adequate information, some gaps in clarity |
| 2 | Vague messages, limited actionable information |
| 1 | Unclear findings, no actionable recommendations |

#### Evidence Collected

- `lfs_candidates_summary`: Per-repo LFS candidate lists (up to 10 per repo)
- `total_lfs_candidates`: Count of LFS candidates across all repos
- `violation_messages`: Per-violation detail including metric, value, level, raw_value, object_ref, and boolean flags (has_metric, has_value, has_object_ref)
- `message_quality`: Counts of violations with object_ref, metric, and value fields
- `grade_coverage`: Per-repo health grade presence and violation/LFS counts
- `grade_coverage_pct`: Percentage of repos with assigned grades
- `actionable_info`: Boolean flags for LFS recommendations, threshold warnings, and all repos graded

#### Ground Truth Assertions

- All repos must have health grades
- All violations must have `metric` and `level` fields
- Bloated repo must have LFS candidates identified

---

### Integration Fit Judge (20% of LLM Score)

**Class:** `IntegrationFitJudge` in `evaluation/llm/judges/integration_fit.py`
**Prompt Template:** `evaluation/llm/prompts/integration_fit.md`

Evaluates how well git-sizer output maps to Caldera Platform storage and pipeline requirements.

#### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Gap Coverage | 40% | Fills gaps in existing Caldera capabilities (not duplicating scc, lizard, semgrep, etc.) |
| Schema Compatibility | 30% | Output maps to Caldera landing zone tables |
| Performance | 30% | Fast enough for pipeline integration |

#### Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Perfect fit -- fills clear gap, compatible schema, fast performance |
| 4 | Good fit -- minor schema adjustments needed, performs well |
| 3 | Acceptable fit -- some gaps remain, moderate adjustments needed |
| 2 | Poor fit -- significant overlap or incompatibilities |
| 1 | Does not fit -- major conflicts with existing architecture |

#### Evidence Collected

- `schema_check`: Field presence at top-level (`timestamp`, `target_path`, `repositories`, `summary`), repo-level (`repository`, `health_grade`, `metrics`, `violations`), and metric-level coverage percentage
- `dd_mapping`: Caldera Platform table mapping (`lz_git_sizer_metrics`, `lz_git_sizer_lfs_candidates`, `lz_git_sizer_violations`), gap analysis with addressed gaps and overlaps
- `performance`: Total duration, average per-repo duration, pipeline threshold compliance
- `output_format`: JSON validity, raw output preservation, nested structure presence
- `existing_dd_tools`: List of existing Caldera tools (scc, lizard, semgrep, trivy, sonarqube)
- `git_sizer_adds`: Unique capabilities git-sizer provides (health grade, LFS candidates, threshold violations, blob/tree/path analysis)

#### Caldera Platform Mapping

| git-sizer Field | Landing Zone Target |
|-----------------|-------------------|
| health_grade | `lz_git_sizer_metrics.health_grade` |
| blob_total_size | `lz_git_sizer_metrics.blob_total_size` |
| max_blob_size | `lz_git_sizer_metrics.max_blob_size` |
| commit_count | `lz_git_sizer_metrics.commit_count` |
| lfs_candidates | `lz_git_sizer_lfs_candidates[]` |
| violations | `lz_git_sizer_violations[]` |

#### Ground Truth Assertions

- Required top-level fields present: `timestamp`, `target_path`, `repositories`, `summary`
- All repos have `repository`, `health_grade`, `metrics` fields
- Total duration under 60 seconds

---

## Evidence Collection

Every check (programmatic and LLM) collects structured evidence for transparency and debugging. Evidence is stored in the `evidence` field of each `CheckResult`.

### CheckResult Schema

```python
@dataclass
class CheckResult:
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "Large blob detection"
    category: CheckCategory # ACCURACY, COVERAGE, EDGE_CASES, PERFORMANCE
    passed: bool
    score: float            # 0.0 to 1.0
    message: str            # Human-readable result description
    evidence: dict[str, Any] = field(default_factory=dict)
```

### Evidence Types by Category

| Category | Evidence Fields | Example |
|----------|----------------|---------|
| Accuracy | Expected values, actual values, thresholds, repo names | `{"max_blob_bytes": 10485760, "expected_min_bytes": 5242880}` |
| Coverage | Metric names, coverage counts, per-repo presence | `{"metrics": ["blob_count", ...], "coverage": 15}` |
| Edge Cases | Repo names, boundary values, field presence | `{"repo": "healthy", "violations": 0}` |
| Performance | Duration in ms, thresholds in ms, slow repo names, output sizes | `{"duration_ms": 3200, "threshold_ms": 5000}` |

### LLM Judge Evidence

LLM judges collect richer evidence via the `collect_evidence()` method. Each judge returns a dict of evidence keys that are injected into the prompt template via `{{ placeholder }}` substitution. The base judge also builds a `programmatic_summary` string from any available programmatic evaluation results to provide cross-signal context to the LLM.

---

## Ground Truth Methodology

### Synthetic Repository Design

Ground truth is defined across 5 synthetic repositories, each targeting a specific dimension of git-sizer analysis. Ground truth files are located in `evaluation/ground-truth/`.

| Repository | File | Purpose | Key Characteristics |
|------------|------|---------|-------------------|
| healthy | `healthy.json` | Baseline -- no issues | Small files, shallow tree, few commits, expected grade A/A+ |
| bloated | `bloated.json` | Large binary detection | 5-15 MiB max blob, 20-50 MiB total, LFS candidates expected, grade C/D |
| deep-history | `deep-history.json` | History depth analysis | ~501 commits, 10-50 branches, 15-100 tags, grade B/C |
| wide-tree | `wide-tree.json` | Tree width and path depth | 500-2000 files in one directory, grade C/D |
| multi-branch | `multi-branch.json` | Branching complexity | 7 branches, 3 tags, merge commits, grade A/B |

### Ground Truth Schema (v1.0)

Each ground truth file follows this schema:

```json
{
  "schema_version": "1.0",
  "scenario": "<scenario-name>",
  "description": "<description of what this repo tests>",
  "repo_path": "eval-repos/synthetic/<repo-name>",
  "expected": {
    "health_grade": {
      "acceptable": ["<grade>", ...],
      "description": "<why this grade range>"
    },
    "metrics": {
      "<metric_name>": {
        "min": <number>,
        "max": <number>,
        "description": "<metric explanation>"
      }
    },
    "lfs_candidates": {
      "min_count": <number>,
      "max_count": <number>,
      "expected_patterns": ["*.png", "*.bin", ...],
      "description": "<expectation>"
    },
    "threshold_violations": {
      "min_count": <number>,
      "max_count": <number>,
      "expected_violations": [
        {
          "metric": "<metric_name>",
          "min_level": <1-4>,
          "max_level": <1-4>,
          "description": "<violation explanation>"
        }
      ]
    }
  },
  "thresholds": {
    "max_analysis_time_ms": <number>,
    "description": "<performance expectation>"
  }
}
```

### Expected Metric Ranges by Repository

#### healthy (baseline)

| Metric | Max | Description |
|--------|-----|-------------|
| max_blob_size | 100 KB | No file larger than 100 KB |
| blob_total_size | 1 MB | Total under 1 MB |
| blob_count | 5-50 | Small file count |
| max_tree_entries | 50 | No wide directories |
| max_path_depth | 5 | Shallow structure |
| commit_count | 3-100 | Small history |
| branch_count | 1-5 | Few branches |
| tag_count | 0-10 | Few tags |
| Violations | 0 | None expected |
| LFS candidates | 0 | None expected |
| Analysis time | < 5,000 ms | Quick |

#### bloated (large binaries)

| Metric | Range | Description |
|--------|-------|-------------|
| max_blob_size | 5-15 MB | Large blob present |
| blob_total_size | 20-50 MB | Inflated by binaries |
| blob_count | 10-100 | Moderate files |
| max_tree_entries | < 100 | Normal width |
| max_path_depth | < 8 | Moderate depth |
| commit_count | 5-200 | Normal history |
| Violations | 1-4 | Blob size violations |
| LFS candidates | 2-5 | Patterns: *.png, *.jpg, *.bin, *.dat, *.zip |
| Analysis time | < 10,000 ms | Slightly longer |

#### deep-history (many commits)

| Metric | Range | Description |
|--------|-------|-------------|
| max_blob_size | < 512 KB | Small files |
| commit_count | 400-600 | ~501 commits |
| max_history_depth | 300-600 | Deep lineage |
| branch_count | 10-50 | Many branches |
| tag_count | 15-100 | Many release tags |
| reference_count | 30-200 | Combined refs |
| max_parent_count | 2-10 | Merge commits |
| Violations | 0-2 | Possible commit/ref count warnings |
| LFS candidates | 0 | No large files |
| Analysis time | < 15,000 ms | History traversal |

#### wide-tree (many files per directory)

| Metric | Range | Description |
|--------|-------|-------------|
| max_blob_size | < 256 KB | Small individual files |
| blob_count | 500-2000 | Large file count |
| max_tree_entries | 500-2000 | At least one wide directory |
| tree_total_entries | 500-5000 | Many total entries |
| max_path_depth | < 6 | Shallow but wide |
| Violations | 1-3 | Tree width violations |
| LFS candidates | 0-5 | Few if any |
| Analysis time | < 10,000 ms | Tree traversal |

#### multi-branch (branching complexity)

| Metric | Range | Description |
|--------|-------|-------------|
| max_blob_size | < 100 KB | Small source files |
| commit_count | 12-25 | Moderate with merges |
| branch_count | 6-10 | 7 named branches |
| tag_count | 2-5 | 3 version tags |
| reference_count | 8-15 | Combined refs |
| max_parent_count | 2 | Merge commits |
| Violations | 0 | None expected |
| LFS candidates | 0 | None expected |
| Analysis time | < 5,000 ms | Quick |

### Ground Truth Generation Process

1. **Create synthetic repos** with known characteristics (e.g., add a 10 MiB binary for bloated)
2. **Run git-sizer** to get baseline measurements
3. **Define expected ranges** with appropriate tolerances (not exact values, since Git objects may have overhead)
4. **Cross-reference** with `git count-objects -v` and `git rev-list --count HEAD` for validation
5. **Document edge cases** (e.g., shallow clones may affect commit counts)

---

## Evaluation Workflow

### Running Programmatic Evaluation

```bash
# Full evaluation against synthetic repos
make evaluate

# Analyze all synthetic repos first, then evaluate
make analyze-synthetic
make evaluate

# JSON-only output (for CI)
cd src/tools/git-sizer
$(PYTHON_VENV) -m scripts.evaluate \
    --results-dir evaluation/results \
    --ground-truth-dir evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json \
    --json

# Skip long-running checks
$(PYTHON_VENV) -m scripts.evaluate \
    --results-dir evaluation/results \
    --ground-truth-dir evaluation/ground-truth \
    --skip-long-checks
```

### Running LLM Evaluation

```bash
# Full LLM evaluation (4 judges, default model)
make evaluate-llm

# Custom model and timeout
make evaluate-llm LLM_MODEL=opus LLM_TIMEOUT=300

# Direct invocation
$(PYTHON_VENV) -m evaluation.llm.orchestrator \
    evaluation/results \
    --output evaluation/results/llm_evaluation.json \
    --model sonnet \
    --timeout 120 \
    --programmatic-results evaluation/results/evaluation_report.json
```

### Full Pipeline

```bash
# End-to-end: setup, analyze synthetic repos, run programmatic evaluation
make all

# Or step by step:
make setup
make analyze-synthetic
make evaluate
make evaluate-llm
```

### Evaluation Outputs

Evaluation artifacts are written to the `evaluation/results/` directory:

```
evaluation/results/
  <repo-name>/
    output.json                  # Per-repo analysis output (Caldera envelope)
  evaluation_report.json         # Programmatic evaluation report
  checks.json                    # Detailed check results
  scorecard.json                 # Structured scorecard data
  scorecard.md                   # Markdown scorecard for compliance
  llm_evaluation.json            # LLM judge results (if evaluate-llm run)
```

### Example Programmatic Output

```json
{
  "timestamp": "2026-02-13T10:00:00",
  "analysis_path": "evaluation/results",
  "ground_truth_dir": "evaluation/ground-truth",
  "summary": {
    "passed": 26,
    "failed": 2,
    "total": 28,
    "score": 0.9286,
    "score_by_category": {
      "accuracy": 0.9125,
      "coverage": 0.9500,
      "edge_cases": 0.9375,
      "performance": 0.9150
    },
    "passed_by_category": {
      "accuracy": [7, 8],
      "coverage": [8, 8],
      "edge_cases": [7, 8],
      "performance": [4, 4]
    }
  },
  "checks": [
    {
      "check_id": "AC-1",
      "name": "Large blob detection",
      "category": "accuracy",
      "passed": true,
      "score": 1.0,
      "message": "Detected max blob size: 10.2 MiB",
      "evidence": {"max_blob_bytes": 10695475, "expected_min_bytes": 5242880}
    }
  ]
}
```

---

## Confidence Requirements

### LLM Judge Confidence

Each LLM judge reports a confidence level (0.0-1.0) alongside its score:

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review needed |

### Ground Truth Assertion Capping

Each LLM judge runs `run_ground_truth_assertions()` before the LLM invocation. If assertions fail, the judge can cap the LLM score to prevent inflated ratings. The base judge supports this pattern:

```python
def evaluate(self):
    gt_passed, gt_failures = self.run_ground_truth_assertions()
    # If ground truth fails, cap score
    if not gt_passed:
        score = min(llm_score, 2)  # Max score of 2 if GT fails
```

### Error Handling

The git-sizer base judge handles error responses gracefully. If the LLM returns an empty response or an error, the judge returns a score of 1 with confidence 0.0:

```python
if not response.strip():
    return JudgeResult(
        dimension=self.dimension_name,
        score=1,
        confidence=0.0,
        reasoning="Empty response from Claude.",
        ...
    )

if response.strip().startswith("Error:"):
    return JudgeResult(
        dimension=self.dimension_name,
        score=1,
        confidence=0.0,
        reasoning=response.strip(),
        ...
    )
```

---

## Extending the Evaluation

### Adding a Programmatic Check

1. Add the check function to the appropriate module in `scripts/checks/` (e.g., `accuracy.py`)
2. Return a `CheckResult` with the correct `CheckCategory`, a unique `check_id`, and supporting `evidence`
3. Include the new check in the module's `run_*_checks()` function
4. Update ground truth files if the check requires new expected values
5. Run `make evaluate` to verify
6. Update this document

### Adding an LLM Judge

1. Create a new judge class in `evaluation/llm/judges/<dimension>.py` extending `BaseJudge`
2. Implement `dimension_name`, `weight`, `collect_evidence()`, `run_ground_truth_assertions()`, and optionally `get_default_prompt()`
3. Create a prompt template in `evaluation/llm/prompts/<dimension>.md` with `{{ placeholder }}` variables matching evidence keys
4. Register the judge in `evaluation/llm/judges/__init__.py` with its weight in the `JUDGES` dict
5. Run `make evaluate-llm` to verify
6. Update this document

### Adding Ground Truth for a New Synthetic Repo

1. Create the synthetic repository in `eval-repos/synthetic/<repo-name>/`
2. Initialize git and commit files with known characteristics
3. Create `evaluation/ground-truth/<repo-name>.json` following the v1.0 schema
4. Define expected metric ranges with appropriate tolerances
5. Add the repo to accuracy checks in `scripts/checks/accuracy.py` if needed
6. Add expected outcomes to the Threshold Quality judge evidence
7. Run `make analyze-synthetic && make evaluate` to verify

### Updating Thresholds

Thresholds are defined directly in check functions:

```python
# In performance.py
pf1_threshold = 5000   # 5 seconds total
pf2_threshold = 2000   # 2 seconds per repo
pf3_threshold = 30000  # 30 seconds for large repo
pf4_threshold = 100000 # 100 KB total raw output

# In accuracy.py
ac1_min = 5 * 1024 * 1024   # 5 MiB min detected blob
ac3_range = (490, 510)       # Commit count range
ac4_min = 900                # Min detected tree entries
ac5_min = 15                 # Min detected path depth
```

---

## Rollup Validation

Git-sizer operates at the repository level rather than the file level, so it does not produce directory-level rollups via dbt. The relevant dbt models are:

- `stg_git_sizer_metrics`: Staging model for repository-level metrics
- `stg_git_sizer_violations`: Staging model for threshold violations
- `stg_git_sizer_lfs_candidates`: Staging model for LFS candidate files

No `recursive >= direct` invariant applies since git-sizer does not produce per-directory distributions.

---

## References

- [git-sizer GitHub](https://github.com/github/git-sizer) -- upstream tool
- [Git LFS](https://git-lfs.com/) -- Git Large File Storage
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685) -- methodology reference
- [Caldera CLAUDE.md](../../../CLAUDE.md) -- project conventions
- [Evaluation Documentation](../../../docs/EVALUATION.md) -- shared LLM judge infrastructure
