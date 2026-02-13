# Evaluation Strategy: Gitleaks PoC

This document describes the evaluation methodology for the Gitleaks secret detection tool within Project Caldera. It covers the full evaluation pipeline: programmatic checks, LLM-as-a-Judge dimensions, ground truth methodology, scoring formulas, and decision thresholds.

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation to assess both objective correctness and semantic quality of secret detection output:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, deterministic verification of counts, schema, invariants |
| LLM Judges | 40% | Semantic understanding of detection quality, false positive reasoning, coverage gaps |

This hybrid approach provides both precision and nuance. Programmatic checks verify that counts match, schemas validate, rollup invariants hold, and performance stays within bounds. LLM judges assess whether detected secrets are plausible, severity classifications are reasonable, and coverage is comprehensive -- aspects that resist simple equality checks.

**Key design decisions:**

1. **Binary pass/fail for programmatic checks.** Each check either passes or fails. There are no partial scores within a single check. The programmatic dimension score is derived from the pass rate across all checks.
2. **1-5 rubric scoring for LLM judges.** Each judge produces a score on a 1-5 scale with sub-dimension breakdowns and confidence levels, enabling nuanced quality assessment.
3. **Multi-scenario evaluation.** Ground truth spans 9 synthetic scenarios covering different secret types, history patterns, and edge cases. Each programmatic run evaluates one scenario; the aggregate pass rate forms the programmatic score.
4. **Dual evaluation modes.** Synthetic mode compares strictly against ground truth. Real-world mode uses the synthetic baseline to contextualize findings from production repositories where ground truth is unavailable.

---

## Dimension Summary

### Programmatic Dimensions

Programmatic checks are organized into 8 categories. All categories carry equal weight in the aggregate pass rate calculation (no per-category weighting -- each individual check contributes equally to the overall pass rate).

| Category | Check IDs | Count | Focus |
|----------|-----------|-------|-------|
| Accuracy | SA-1 to SA-11 | 11 | Secret count, rule, file, finding, and severity matching |
| Detection | SD-1 to SD-6 | 6 | False negatives, false positives, entropy, masking |
| Coverage | SC-1 to SC-8 | 8 | Schema completeness, metadata, finding field coverage |
| Performance | SP-1 to SP-4 | 4 | Scan time, per-commit time, per-finding time, memory |
| Output Quality | OQ-1 | 1 | Caldera envelope schema validation |
| Integration Fit | IF-1 | 1 | Repo-relative file path enforcement |
| Edge Cases | EC-1 to EC-4 | 4 | Empty repos, unicode, large files, binary files |
| Rollup Validation | RV-1 to RV-4 | 4 | Directory aggregation invariants |
| **Total** | | **39** | |

### LLM Judge Dimensions

| Judge | Weight | Dimension | Sub-dimensions |
|-------|--------|-----------|----------------|
| Detection Accuracy | 35% | `detection_accuracy` | True positive rate (40%), Location accuracy (30%), Rule matching (30%) |
| False Positive Rate | 25% | `false_positive` | False positive count (40%), Pattern quality (30%), Noise level (30%) |
| Secret Coverage | 20% | `secret_coverage` | Type breadth (40%), Format handling (30%), Historical coverage (30%) |
| Severity Classification | 20% | `severity_classification` | Classification accuracy (40%), Risk assessment (30%), Context awareness (30%) |
| **Total** | **100%** | | |

---

## Programmatic Check Catalog

### Accuracy Checks (SA-1 to SA-11)

**Module:** `scripts/checks/accuracy.py`
**Category:** `Accuracy`
**Purpose:** Verify that detected secrets match ground truth expectations in count, identity, location, and severity.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| SA-1 | Total secret count | `actual.total_secrets == expected.total_secrets` | Expected count, actual count |
| SA-2 | Unique secret count | `actual.unique_secrets == expected.unique_secrets` | Expected count, actual count |
| SA-3 | Secrets in HEAD | `actual.secrets_in_head == expected.secrets_in_head` | Expected count, actual count |
| SA-4 | Secrets in history | `actual.secrets_in_history == expected.secrets_in_history` | Expected count, actual count |
| SA-5 | Files with secrets count | `actual.files_with_secrets == expected.files_with_secrets` | Expected count, actual count |
| SA-6 | Commits with secrets count | `actual.commits_with_secrets == expected.commits_with_secrets` | Expected count, actual count |
| SA-7 | Expected rule IDs detected | All `expected.rule_ids` present in `actual.secrets_by_rule` keys | Expected rule list, actual rule list |
| SA-8 | Expected files with secrets | All `expected.files_with_secrets_list` present in actual files | Expected file list, actual file list |
| SA-9 | Rule counts match | For each rule, `expected.secrets_by_rule[rule] == actual.secrets_by_rule[rule]` | Per-rule expected vs actual counts |
| SA-10 | Expected findings detected | All expected `file:rule:line` fingerprints found in actual findings | Expected fingerprints, actual fingerprints |
| SA-11 | Severity assignments correct | For findings with `expected_severity`, actual severity matches | Expected severities, actual severities, mismatches |

**SA-8 special behavior:** If `expected.files_with_secrets_list` is empty, the check auto-passes with message "No specific files expected".

**SA-10 special behavior:** If `expected.findings` is empty, the check auto-passes with message "No specific findings expected".

**SA-11 special behavior:** Only validated when findings have an `expected_severity` field. Skips findings without severity expectations.

### Detection Checks (SD-1 to SD-6)

**Module:** `scripts/checks/detection.py`
**Category:** `Detection`
**Purpose:** Verify detection quality -- no false negatives for known secrets, no unexpected rule types, entropy sanity, and secret masking.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| SD-1 | No false negatives | `actual.total_secrets >= expected.total_secrets` | Expected minimum count, actual count |
| SD-2 | No unexpected rule IDs | `actual_rules - expected_rules == empty set` (only when expected rules defined) | Expected rule set, actual rule set, unexpected rules |
| SD-3 | Historical secrets detected | `actual.secrets_in_history == expected.secrets_in_history` | Expected historical count, actual historical count |
| SD-4 | Clean repos have zero secrets | When `expected.total_secrets == 0`: `actual.total_secrets == 0` | Boolean match |
| SD-5 | Entropy values reasonable | All findings have `0 <= entropy <= 8` (bits) | Invalid entropy entries (first 3) |
| SD-6 | All secrets have masked preview | All `secret_preview` fields contain `*` or are <= 8 chars | Unmasked file paths (first 3) |

**SD-2 special behavior:** If no expected rules are defined in ground truth, the check auto-passes to avoid false failures on scenarios without rule expectations.

**SD-4 special behavior:** When `expected.total_secrets > 0`, the check auto-passes with "N/A - repo expected to have secrets".

### Coverage Checks (SC-1 to SC-8)

**Module:** `scripts/checks/coverage.py`
**Category:** `Coverage`
**Purpose:** Verify output completeness -- all required fields, metadata, and structural elements are present in the analysis output.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| SC-1 | Schema version present | `results.schema_version is not None` | Actual schema version |
| SC-2 | Tool version present | `results.tool_version` is non-empty string | Actual tool version |
| SC-3 | Timestamp present | `results.timestamp is not None` | Actual timestamp |
| SC-4 | Summary metrics present | All of `total_secrets`, `unique_secrets`, `secrets_in_head`, `secrets_in_history`, `files_with_secrets`, `commits_with_secrets` exist | Present fields, missing fields |
| SC-5 | Findings list present | `findings` key exists in results | Present/missing |
| SC-6 | Files summary present | `files` key exists in results | Present/missing |
| SC-7 | Directory metrics present | `directories` key exists in results | Present/missing |
| SC-8 | All findings have required fields | Every finding contains `file_path`, `line_number`, `rule_id`, `secret_type`, `commit_hash`, `fingerprint` | Invalid findings (first 3), required field list |

### Performance Checks (SP-1 to SP-4)

**Module:** `scripts/checks/performance.py`
**Category:** `Performance`
**Purpose:** Verify that scan performance is within acceptable bounds. Thresholds are configurable via the `thresholds` section in ground truth files.

| Check ID | Name | Pass Criteria | Default Threshold | Evidence Collected |
|----------|------|---------------|-------------------|-------------------|
| SP-1 | Total scan time | `actual.scan_time_ms <= max_scan_time_ms` | 10,000 ms | Actual time, threshold |
| SP-2 | Time per commit | `scan_time_ms / commits_with_secrets <= max_ms_per_commit` | 1,000 ms | Time per commit, threshold |
| SP-3 | Time per finding | `scan_time_ms / total_secrets <= max_ms_per_finding` | 500 ms | Time per finding, threshold |
| SP-4 | Findings count reasonable | `len(findings) <= max_findings_for_test` | 100 | Findings count, threshold |

**SP-2 special behavior:** When `commits_with_secrets == 0`, auto-passes with "N/A - no commits with secrets".

**SP-3 special behavior:** When `total_secrets == 0`, auto-passes with "N/A - no secrets found".

**Threshold sources (in priority order):**
1. `expected.thresholds` within the ground truth file
2. Top-level `thresholds` in the ground truth file (backwards compatibility)
3. Hardcoded defaults in the check code

### Output Quality Checks (OQ-1)

**Module:** `scripts/checks/output_quality.py`
**Category:** `Output Quality`
**Purpose:** Validate that analysis output conforms to the Caldera envelope format specification.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| OQ-1 | Caldera envelope schema | Zero validation errors from `_validate_caldera_envelope()` | Validation errors (first 5) |

**Envelope validation covers two accepted formats:**

1. **Caldera envelope format** (`metadata` + `data`):
   - Required metadata fields: `tool_name`, `tool_version`, `run_id`, `repo_id`, `branch`, `commit`, `timestamp`, `schema_version`
   - `metadata.tool_name` must equal `"gitleaks"`
   - Required data fields: `tool`, `tool_version`, `total_secrets`, `findings`
   - `data.tool` must equal `"gitleaks"`
   - `data.total_secrets` must be an integer
   - `data.findings` must be a list

2. **Legacy format** (`results` wrapper):
   - Required root fields: `schema_version`, `generated_at`, `repo_name`, `repo_path`, `results`
   - Required results fields: `tool`, `tool_version`, `total_secrets`, `findings`
   - Same type constraints as Caldera format

### Integration Fit Checks (IF-1)

**Module:** `scripts/checks/integration_fit.py`
**Category:** `Integration Fit`
**Purpose:** Verify that all file paths in findings are repo-relative, as required by the Caldera path normalization standard.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| IF-1 | All paths are repo-relative | Zero findings with absolute file paths (`os.path.isabs()` returns False for all) | Count of absolute paths, total findings |

### Edge Case Checks (EC-1 to EC-4)

**Module:** `scripts/checks/edge_cases.py`
**Category:** `Edge Cases`
**Purpose:** Validate graceful handling of edge conditions -- empty repositories, unicode paths, large files, and binary files.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| EC-1 | Empty repo handling | When `is_empty_repo == True`: output has `total_secrets == 0` and `findings` is a list | total_secrets, has_findings_list |
| EC-2 | Unicode file paths | All finding `file_path` values are valid UTF-8 strings (not bytes) | Unicode issues (first 3) |
| EC-3 | Large file handling | When `has_large_files == True`: `0 < scan_time_ms < max_expected_time` | Actual scan time, threshold |
| EC-4 | Binary file handling | When `has_binary_files == True`: no findings from binary file extensions (`.exe`, `.dll`, `.so`, `.dylib`, `.bin`, `.png`, `.jpg`, `.gif`, `.pdf`, `.zip`, `.tar`, `.gz`) | Binary file findings (first 3) |

**Conditional execution:** EC-1, EC-3, and EC-4 evaluate only when the corresponding flag (`is_empty_repo`, `has_large_files`, `has_binary_files`) is set in the ground truth `expected` section. Otherwise they auto-pass with "N/A" messages.

### Rollup Validation Checks (RV-1 to RV-4)

**Module:** `scripts/checks/rollup.py`
**Category:** `Rollup Validation`
**Purpose:** Validate directory aggregation invariants, ensuring recursive/direct count relationships hold and root totals are consistent.

| Check ID | Name | Pass Criteria | Evidence Collected |
|----------|------|---------------|-------------------|
| RV-1 | Recursive >= Direct (secrets) | For all directories: `recursive_secret_count >= direct_secret_count` | Violating directories (first 3) |
| RV-2 | Recursive >= Direct (files) | For all directories: `recursive_file_count >= direct_file_count` | Violating directories (first 3) |
| RV-3 | All counts non-negative | For all directories: `direct_secret_count`, `recursive_secret_count`, `direct_file_count`, `recursive_file_count` are all >= 0 | Negative count entries (first 3) |
| RV-4 | Root recursive equals total | Root directory `recursive_secret_count == total_secrets` | Root recursive count, total_secrets |

**Root directory resolution:** Looks for `"."` first, then falls back to the shortest path key in the directories dict.

**Missing directories behavior:** When `results.directories` is empty or absent, all four checks auto-pass with "N/A - no directory metrics present".

---

## Scoring

### Programmatic Score Calculation

The programmatic evaluation runs all 39 checks across all evaluated scenarios. Each check produces a binary pass/fail result. The programmatic score is the aggregate pass rate:

```python
# From evaluate.py
overall_score = total_passed / total_checks  # Range: 0.0 to 1.0
```

For the scorecard, this is normalized to a 1-5 scale:

```python
normalized_score = overall_score * 5.0  # Range: 0.0 to 5.0
```

Per-dimension scores are calculated the same way within each category:

```python
dim_score = (data["passed"] / data["total"]) * 5.0
```

Dimensions are weighted equally (uniform weight = `1.0 / number_of_dimensions`).

### LLM Score Calculation

Each LLM judge produces a 1-5 score with sub-dimension breakdown. The LLM composite score is the weighted sum:

```
llm_score = (detection_accuracy.score * 0.35)
          + (false_positive.score * 0.25)
          + (secret_coverage.score * 0.20)
          + (severity_classification.score * 0.20)
```

### Combined Score

The final combined score merges programmatic and LLM scores:

```python
combined_score = (programmatic_score * 0.60) + (llm_score * 0.40)
```

Where `programmatic_score` is the normalized 1-5 value (`pass_rate * 5.0`).

---

## Decision Thresholds

Decisions are made on the normalized combined score (1-5 scale):

| Decision | Score Range | Interpretation |
|----------|-------------|----------------|
| STRONG_PASS | >= 4.0 (80%+ pass rate) | Excellent, production-ready secret detection |
| PASS | >= 3.5 (70%+ pass rate) | Good, minor improvements needed |
| WEAK_PASS | >= 3.0 (60%+ pass rate) | Acceptable with caveats, some detection gaps |
| FAIL | < 3.0 (below 60% pass rate) | Significant issues, unreliable detection |

The decision function in `evaluate.py`:

```python
def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on pass rate (0-1)."""
    normalized = score * 5.0
    if normalized >= 4.0:
        return "STRONG_PASS"
    elif normalized >= 3.5:
        return "PASS"
    elif normalized >= 3.0:
        return "WEAK_PASS"
    return "FAIL"
```

Note: The input `score` is the raw pass rate (0-1), which is multiplied by 5.0 internally for threshold comparison.

---

## LLM Judge Details

### Detection Accuracy Judge (35%)

**Class:** `DetectionAccuracyJudge`
**File:** `evaluation/llm/judges/detection_accuracy.py`
**Prompt:** `evaluation/llm/prompts/detection_accuracy.md`

**Sub-dimensions:**

| Sub-dimension | Weight | Rubric |
|---------------|--------|--------|
| True Positive Rate | 40% | Were all expected secrets detected? Were secret types correctly identified? |
| Location Accuracy | 30% | Are file paths correct and normalized? Are line numbers accurate? |
| Rule Matching | 30% | Were appropriate detection rules triggered? Is match quality good? |

**Scoring rubric (synthetic repos):**

| Score | Criteria |
|-------|----------|
| 5 | All secrets detected with correct types and locations |
| 4 | >90% secrets detected, minor location inaccuracies |
| 3 | 70-90% secrets detected, some misidentifications |
| 2 | 50-70% secrets detected, significant issues |
| 1 | <50% secrets detected, unreliable detection |

**Scoring rubric (real-world repos with validated synthetic baseline):**

| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, any findings are accurate, metadata complete |
| 4 | Minor schema issues but findings accurate, good metadata |
| 3 | Schema issues OR questionable finding accuracy |
| 2 | Multiple schema issues AND questionable findings |
| 1 | Broken output, missing required fields, obvious false positives |

**Evidence collection:** Loads all analysis results and ground truth, builds per-scenario comparison summaries (expected vs actual totals, rule IDs, files). In real-world mode, injects synthetic baseline context and interpretation guidance.

### False Positive Judge (25%)

**Class:** `FalsePositiveJudge`
**File:** `evaluation/llm/judges/false_positive.py`
**Prompt:** `evaluation/llm/prompts/false_positive.md`

**Sub-dimensions:**

| Sub-dimension | Weight | Rubric |
|---------------|--------|--------|
| False Positive Count | 40% | How many false positives? What percentage of total findings? |
| Pattern Quality | 30% | Are FPs from overly broad patterns? Are test/example secrets handled? |
| Noise Level | 30% | Is signal-to-noise ratio acceptable? Are findings actionable? |

**Scoring rubric:**

| Score | Criteria |
|-------|----------|
| 5 | No false positives, all findings are true secrets |
| 4 | < 5% false positive rate, minimal noise |
| 3 | 5-15% false positive rate, manageable noise |
| 2 | 15-30% false positive rate, significant noise |
| 1 | > 30% false positive rate, overwhelming noise |

**Evidence collection:** Loads all results and ground truth. For each scenario, computes `potential_false_positives = max(0, actual_count - expected_count)`. Flags clean repos (`expected_count == 0`) and whether they passed (zero actual findings).

### Secret Coverage Judge (20%)

**Class:** `SecretCoverageJudge`
**File:** `evaluation/llm/judges/secret_coverage.py`
**Prompt:** `evaluation/llm/prompts/secret_coverage.md`

**Sub-dimensions:**

| Sub-dimension | Weight | Rubric |
|---------------|--------|--------|
| Type Breadth | 40% | Common types (API keys, tokens, passwords, private keys), platform-specific (AWS, GCP, GitHub, Slack) |
| Format Handling | 30% | Encoding handling (base64, hex, URL-encoded), file formats (JSON, YAML, .env, config) |
| Historical Coverage | 30% | Git history scanning, deleted-but-committed secret detection |

**Scoring rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Comprehensive coverage of all expected secret types |
| 4 | Good coverage with minor gaps in less common types |
| 3 | Basic coverage of common types only |
| 2 | Limited coverage, many important types missed |
| 1 | Poor coverage, most secrets not detected |

**Secret types expected to be covered:**
- AWS access keys and secret keys
- GitHub/GitLab tokens
- Slack tokens and webhooks
- Private keys (RSA, DSA, EC)
- Database passwords
- API keys (generic and platform-specific)
- JWT tokens
- OAuth tokens

**Evidence collection:** Aggregates `rule_types_detected` and `expected_rule_types` across all scenarios. Identifies scenarios with historical secrets and compares expected vs actual historical detection counts.

### Severity Classification Judge (20%)

**Class:** `SeverityClassificationJudge`
**File:** `evaluation/llm/judges/severity_classification.py`
**Prompt:** `evaluation/llm/prompts/severity_classification.md`

**Sub-dimensions:**

| Sub-dimension | Weight | Rubric |
|---------------|--------|--------|
| Classification Accuracy | 40% | Critical secrets marked critical? Test secrets de-prioritized? |
| Risk Assessment | 30% | Secret type risk considered? High-value targets prioritized? |
| Context Awareness | 30% | File location considered? Commit recency factored? Environment indicators used? |

**Expected severity levels:**

| Severity | Examples |
|----------|----------|
| CRITICAL | Production credentials, root/admin keys, active database passwords |
| HIGH | Service account keys, CI/CD tokens, encryption keys, private keys |
| MEDIUM | Development keys, staging credentials, internal tokens |
| LOW | Test data, example keys, clearly marked placeholders |

**Scoring rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Perfect severity classification matching risk profile |
| 4 | Minor severity misclassifications (within one level) |
| 3 | Some important misclassifications affecting triage order |
| 2 | Significant misclassifications, critical items not prioritized |
| 1 | Severity classification unreliable, cannot be used for triage |

**Evidence collection:** Aggregates severity distribution (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) across all analysis results. Extracts expected severities from ground truth findings that have `expected_severity` fields. Reports severity mismatches.

---

## LLM Judge Infrastructure

### Base Class Hierarchy

All judges inherit from `BaseJudge` (gitleaks-specific) which extends `SharedBaseJudge` (from `src/shared/evaluation/base_judge.py`):

```
SharedBaseJudge (src/shared/evaluation/base_judge.py)
  --> BaseJudge (evaluation/llm/judges/base.py)
    --> DetectionAccuracyJudge
    --> FalsePositiveJudge
    --> SecretCoverageJudge
    --> SeverityClassificationJudge
```

### Judge Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model` | `"opus-4.5"` | LLM model for evaluation |
| `timeout` | `120` seconds | LLM invocation timeout |
| `working_dir` | Tool root (`src/tools/gitleaks`) | Working directory |
| `output_dir` | `outputs/runs` | Analysis output directory |
| `ground_truth_dir` | `evaluation/ground-truth` | Ground truth directory |
| `use_llm` | `True` | Enable LLM evaluation (False for heuristic-only) |
| `trace_id` | `None` | Correlation ID for linking judges in one run |
| `enable_observability` | `True` | Log LLM interactions for tracing |
| `evaluation_mode` | `None` (auto) | `"synthetic"`, `"real_world"`, or auto-detect |

### Prompt Template System

Each judge has a prompt template in `evaluation/llm/prompts/<dimension_name>.md`. Templates use `{{ placeholder }}` syntax for evidence injection:

| Placeholder | Content |
|-------------|---------|
| `{{ evidence }}` | Serialized evidence dictionary from `collect_evidence()` |
| `{{ evaluation_mode }}` | Current evaluation mode (synthetic/real_world) |
| `{{ interpretation_guidance }}` | Mode-specific scoring guidance |
| `{{ synthetic_baseline }}` | Synthetic validation results (real-world mode only) |

### Judge Response Format

All judges return structured JSON with the same schema:

```json
{
    "score": 4,
    "confidence": 0.85,
    "reasoning": "Detailed explanation of scoring rationale",
    "evidence_cited": ["Specific findings referenced"],
    "recommendations": ["Actionable improvements"],
    "sub_scores": {
        "<sub_dimension_1>": 4,
        "<sub_dimension_2>": 5,
        "<sub_dimension_3>": 3
    }
}
```

---

## Confidence Requirements

### LLM Judge Confidence

Each judge reports a confidence level (0.0-1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review recommended |

Low-confidence scores should be flagged in evaluation reports and potentially excluded from aggregate calculations or capped.

### Ground Truth Confidence

The ground truth anchors programmatic evaluation. If programmatic checks fail on synthetic scenarios where ground truth is established, it signals a real regression, not a judgment ambiguity. LLM scores can be capped when ground truth assertions fail:

```python
# If ground truth checks fail, cap LLM score
if not gt_passed:
    score = min(llm_score, 2)  # Max score of 2 if GT fails
```

---

## Ground Truth

### Methodology

Ground truth files define expected detection outcomes for synthetic repositories. Each ground truth file specifies exact expected values for secret counts, rule IDs, file locations, line numbers, and (optionally) severity classifications.

### Generation Process

1. **Create synthetic repository**: Seed known secrets of specific types into files
2. **Run Gitleaks**: Execute detection to establish baseline findings
3. **Manual verification**: Confirm each finding is a true positive with correct metadata
4. **Document expected values**: Record counts, rules, files, line numbers, and severities
5. **Set performance thresholds**: Define acceptable scan time bounds per scenario

### Ground Truth Schema

Each ground truth file follows this structure:

```json
{
    "schema_version": "1.0",
    "scenario": "<scenario-name>",
    "description": "<human-readable description>",
    "generated_at": "<ISO 8601 timestamp>",
    "repo_path": "eval-repos/synthetic/<scenario-name>",
    "expected": {
        "total_secrets": 2,
        "unique_secrets": 2,
        "secrets_in_head": 2,
        "secrets_in_history": 0,
        "files_with_secrets": 2,
        "commits_with_secrets": 1,
        "rule_ids": ["aws-access-token", "github-pat"],
        "files_with_secrets_list": [".env", "config/api.py"],
        "secrets_by_rule": {"aws-access-token": 1, "github-pat": 1},
        "secrets_by_severity": {"CRITICAL": 1, "HIGH": 1},
        "findings": [
            {
                "file_path": ".env",
                "rule_id": "aws-access-token",
                "line_number": 2,
                "expected_severity": "CRITICAL"
            }
        ],
        "repository": "<scenario-name>",
        "thresholds": {
            "max_scan_time_ms": 5000,
            "max_ms_per_commit": 1000,
            "max_ms_per_finding": 500,
            "max_findings_for_test": 100
        }
    }
}
```

**Optional fields in expected:** `secrets_by_severity`, `expected_severity` on findings, `is_empty_repo`, `has_large_files`, `has_binary_files`.

### Synthetic Scenarios (9 Total)

| Scenario | File | Secrets | History | Rule Types | Purpose |
|----------|------|---------|---------|------------|---------|
| api-keys | `api-keys.json` | 2 | 0 | github-pat, stripe-access-token | API key detection across file types |
| aws-credentials | `aws-credentials.json` | 2 | 0 | aws-access-token | AWS credential detection (.aws/credentials, Python config) |
| historical-secrets | `historical-secrets.json` | 1 | 1 | aws-access-token | Deleted secrets in git history |
| mixed-secrets | `mixed-secrets.json` | 2 | 0 | generic-api-key, stripe-access-token | Multi-type detection in production-like files |
| no-secrets | `no-secrets.json` | 0 | 0 | (none) | Clean codebase baseline -- should produce zero findings |
| private-keys | `private-keys.json` | 2 | 0 | private-key | RSA/SSH private key detection with severity expectations |
| database-creds | `database-creds.json` | 1 | 0 | private-key | Database SSL certificate/key detection |
| cloud-mixed | `cloud-mixed.json` | 7 | 0 | aws-access-token, github-pat, slack-bot-token, generic-api-key, private-key | Multi-provider cloud credentials with severity expectations (CRITICAL, HIGH, MEDIUM) |
| synthetic | `synthetic.json` | 0 | 0 | (none) | Combined synthetic repo baseline |

**Secret types covered across scenarios:**
- AWS access tokens (aws-credentials, historical-secrets, cloud-mixed)
- GitHub personal access tokens (api-keys, cloud-mixed)
- Stripe access tokens (api-keys, mixed-secrets)
- Generic API keys (mixed-secrets, cloud-mixed)
- Private keys -- RSA/SSH (private-keys, database-creds, cloud-mixed)
- Slack bot tokens (cloud-mixed)

**Severity expectations defined in:**
- `private-keys.json`: 2 HIGH findings
- `database-creds.json`: 1 HIGH finding
- `cloud-mixed.json`: 4 CRITICAL, 2 HIGH, 1 MEDIUM findings

### Expected Value Summary

| Metric | Total Across All Scenarios |
|--------|---------------------------|
| Total secrets | 17 |
| Scenarios with history | 1 (historical-secrets) |
| Scenarios with severity expectations | 3 (private-keys, database-creds, cloud-mixed) |
| Clean repo scenarios | 2 (no-secrets, synthetic) |
| Distinct rule IDs | 6 (aws-access-token, github-pat, stripe-access-token, generic-api-key, private-key, slack-bot-token) |

---

## Evidence Collection

### Programmatic Evidence

Each `CheckResult` captures:

```python
@dataclass
class CheckResult:
    check_id: str       # e.g., "SA-1"
    category: str       # e.g., "Accuracy"
    passed: bool        # Binary pass/fail
    message: str        # Human-readable description
    expected: Any       # Expected value or constraint
    actual: Any         # Actual observed value
```

### Check Helper Functions

The `scripts/checks/__init__.py` module provides reusable check primitives:

| Helper | Signature | Purpose |
|--------|-----------|---------|
| `check_equal` | `(check_id, category, name, expected, actual, tolerance=0)` | Exact or tolerance-based equality |
| `check_at_least` | `(check_id, category, name, minimum, actual)` | Lower bound check |
| `check_at_most` | `(check_id, category, name, maximum, actual)` | Upper bound check |
| `check_contains` | `(check_id, category, name, expected_items, actual_set)` | Set membership check |
| `check_not_contains` | `(check_id, category, name, forbidden_items, actual_set)` | Exclusion check |
| `check_boolean` | `(check_id, category, name, expected, actual)` | Boolean equality |

### LLM Judge Evidence

Each judge's `collect_evidence()` method builds a structured evidence dictionary. Common patterns:

1. **Load all analysis results** via `load_all_analysis_results()` -- returns dict keyed by scenario name
2. **Load all ground truth** via `load_all_ground_truth()` -- returns dict keyed by scenario name
3. **Build comparison summaries** -- per-scenario expected-vs-actual breakdowns
4. **Inject evaluation mode context** -- synthetic vs real-world interpretation guidance

---

## Evaluation Workflow

### Running Programmatic Evaluation

```bash
# Full programmatic evaluation against all scenarios
cd src/tools/gitleaks
make evaluate

# Direct invocation with custom paths
.venv/bin/python -m scripts.evaluate \
    --analysis-dir outputs/runs \
    --ground-truth-dir evaluation/ground-truth \
    --output evaluation/results
```

### Running LLM Evaluation

```bash
# LLM evaluation with default model (opus-4.5)
make evaluate-llm

# Direct invocation with custom model
.venv/bin/python -m evaluation.llm.orchestrator \
    --working-dir . \
    --programmatic-results evaluation/results/evaluation_report.json \
    --model opus-4.5 \
    --evaluation-mode synthetic
```

### Running Tests

```bash
# All tests
make test

# Quick tests (stop on first failure)
make test-quick
```

### Building Synthetic Repos

```bash
# Recreate synthetic test repositories
make build-repos
```

### Evaluation Outputs

```
evaluation/
├── ground-truth/                    # Ground truth files (9 scenarios)
│   ├── api-keys.json
│   ├── aws-credentials.json
│   ├── cloud-mixed.json
│   ├── database-creds.json
│   ├── historical-secrets.json
│   ├── mixed-secrets.json
│   ├── no-secrets.json
│   ├── private-keys.json
│   └── synthetic.json
├── results/
│   ├── evaluation_report.json       # Programmatic evaluation report
│   └── <scenario>_eval.json         # Per-scenario evaluation reports
├── scorecard.json                   # Structured scorecard with dimensions
├── scorecard.md                     # Markdown scorecard for human review
└── llm/
    ├── judges/                      # Judge implementations
    ├── prompts/                     # Prompt templates
    └── orchestrator.py              # LLM evaluation orchestrator
```

---

## Extending the Evaluation

### Adding a New Programmatic Check

1. Identify the appropriate module in `scripts/checks/` (accuracy, detection, coverage, performance, output_quality, integration_fit, edge_cases, rollup)
2. Add the check function using the helper primitives from `scripts/checks/__init__.py`
3. Assign a sequential check ID following the module prefix (e.g., SA-12, SD-7, SC-9)
4. Add the check to the module's `run_*_checks()` function
5. If needed, update ground truth files with new expected values
6. Run `make evaluate` to verify the new check
7. Update this document with the new check entry

### Adding a New Ground Truth Scenario

1. Create a synthetic repository with known secrets under `eval-repos/synthetic/<name>/`
2. Run Gitleaks analysis and verify findings manually
3. Create `evaluation/ground-truth/<name>.json` following the schema above
4. Run programmatic evaluation to confirm all checks pass
5. Update the scenario table in this document

### Adding a New LLM Judge

1. Create a new judge class in `evaluation/llm/judges/` extending `BaseJudge`
2. Define `dimension_name`, `weight`, `get_default_prompt()`, and `collect_evidence()`
3. Create a prompt template in `evaluation/llm/prompts/<dimension_name>.md`
4. Register the judge in `evaluation/llm/judges/__init__.py`
5. Add the judge to the orchestrator's judge list
6. Ensure all judge weights sum to 1.0 after adding the new judge
7. Update the dimension summary tables in this document

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-14 | Initial version |
| 2.0 | 2026-02-13 | Complete rewrite: added full check catalog (39 checks), LLM judge details with sub-dimensions and rubrics, ground truth methodology with 9 scenarios, scoring formulas, evidence collection details, extension guide |
