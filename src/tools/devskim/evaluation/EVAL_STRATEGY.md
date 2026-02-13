# Evaluation Strategy: DevSkim Security Linter

This document describes the evaluation methodology for the DevSkim security linting tool within Project Caldera. DevSkim is a pattern-based security analyzer from Microsoft that detects specific vulnerability patterns in source code, with particular strength in insecure cryptography, unsafe deserialization, XXE, and security misconfiguration detection.

---

## Evaluation Philosophy

The evaluation combines **programmatic checks** with **LLM-as-a-Judge** evaluation to validate DevSkim's security detection capabilities:

| Component | Weight | Purpose |
|-----------|--------|---------|
| Programmatic | 60% | Objective, reproducible, fast -- validates detection counts, coverage, schema conformance |
| LLM Judges | 40% | Semantic understanding -- assesses detection quality, severity calibration, security focus |

This hybrid approach is essential for a security tool because:

1. **Programmatic checks** verify that known vulnerabilities are detected (true positives), safe code is not flagged (false positives), and output conforms to the Caldera envelope schema. These checks run in seconds and produce deterministic results.

2. **LLM judges** assess qualitative dimensions that resist simple counting: whether severity ratings are appropriately calibrated for a pattern-matching tool, whether findings are actionable for developers, and whether the tool stays focused on security rather than drifting into code quality lint.

3. **DevSkim-specific context matters.** DevSkim is a specialized pattern-based linter, not a comprehensive SAST scanner. It detects insecure cryptography, unsafe deserialization, XXE, LDAP injection patterns, and security misconfigurations. It does NOT detect SQL injection, XSS, path traversal, or hardcoded secrets (those require data-flow or semantic analysis). The evaluation framework respects this scope boundary -- zero detections in out-of-scope categories are expected and correct, not failures.

### What "Correct" Means for DevSkim

- **True positive**: A known insecure pattern (e.g., `MD5.Create()`, `BinaryFormatter.Deserialize()`) is flagged with the correct rule ID, appropriate severity, and accurate file/line location.
- **True negative**: Safe code patterns (e.g., `SHA256.Create()`, `RNGCryptoServiceProvider`) produce zero findings.
- **False positive**: A safe pattern is incorrectly flagged. The evaluation tolerates a small false positive rate (up to 20% of total findings) because pattern-matching tools inherently lack runtime context.
- **False negative (in-scope)**: A pattern within DevSkim's rule set is missed. This is a genuine failure.
- **False negative (out-of-scope)**: A vulnerability type outside DevSkim's rule set (e.g., SQL injection) is not detected. This is expected and correct.

---

## Dimension Summary

### Programmatic Dimensions

The programmatic evaluation runs checks across 6 categories. Each category's score is the mean of its constituent check scores (0.0 to 1.0). The overall programmatic score is the unweighted mean across all checks.

| ID | Dimension | Checks | Purpose |
|----|-----------|--------|---------|
| D1 | Accuracy | AC-1 to AC-8 | Security detection correctness per vulnerability category |
| D2 | Coverage | CV-1 to CV-8 | Language and security category coverage |
| D3 | Edge Cases | EC-1 to EC-8 | Handling of empty files, large files, comments, minified code |
| D4 | Performance | PF-1 to PF-4 | Analysis speed, throughput, and result completeness |
| D5 | Output Quality | OQ-1 | Schema validation against Caldera envelope format |
| D6 | Integration Fit | IF-1 | File path normalization (repo-relative paths) |

### LLM Judge Dimensions

| Judge | Weight | Sub-dimensions |
|-------|--------|----------------|
| Detection Accuracy | 40% | True positive rate, False positive rate, Vulnerability classification |
| Rule Coverage | 25% | Rule breadth, Category coverage, Ground truth alignment |
| Severity Calibration | 20% | Severity appropriateness, Consistency, Industry alignment |
| Security Focus | 15% | Security relevance, Signal quality, Appropriate scope |

### Combined Score Calculation

```python
# Programmatic score: mean of all check scores (0.0 to 1.0)
programmatic_score = sum(check.score for check in all_checks) / len(all_checks)

# Normalize to 1-5 scale for decision thresholds
normalized_score = programmatic_score * 5.0

# LLM combined score: weighted mean of 4 judges (1-5 scale)
llm_score = (
    detection_accuracy.score * 0.40 +
    rule_coverage.score * 0.25 +
    severity_calibration.score * 0.20 +
    security_focus.score * 0.15
)

# Final combined score (when both components run)
combined_score = (0.60 * normalized_score) + (0.40 * llm_score)
```

---

## Check Catalog

### Accuracy Checks (AC-1 to AC-8)

Located in `scripts/checks/accuracy.py`. These checks compare DevSkim findings against ground truth expectations for specific vulnerability categories.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| AC-1 | SQL injection detection | Accuracy | Found count >= min_expected from ground truth | count, expected min/max, ground truth source |
| AC-2 | Hardcoded secrets detection | Accuracy | Found count >= min_expected from ground truth | count, expected min/max, ground truth source |
| AC-3 | Insecure crypto detection | Accuracy | Found count >= min_expected from ground truth | count, expected min/max, ground truth source |
| AC-4 | Path traversal detection | Accuracy | Found count >= min_expected from ground truth | count, expected min/max, ground truth source |
| AC-5 | XSS detection | Accuracy | Found count >= min_expected from ground truth | count, expected min/max, ground truth source |
| AC-6 | Deserialization detection | Accuracy | Found count >= min_expected from ground truth | count, expected min/max, ground truth source |
| AC-7 | False positive rate | Accuracy | Score >= 0.7 (false positives < 20% of total) | false_positives, total_findings, safe_files_checked |
| AC-8 | Overall precision/recall | Accuracy | F1 score >= 0.6 | precision, recall, f1, true_positives, total_found, total_expected |

**Detection Score Formula (AC-1 through AC-6):**

```python
def _compute_detection_score(found: int, expected: dict | None) -> float:
    if expected is None:
        return 0.7 if found > 0 else 0.5  # No ground truth: partial credit

    min_expected = expected.get("min_expected", 0)
    if min_expected == 0:
        return 1.0 if found >= 0 else 0.5

    if found >= min_expected:
        return 1.0                                    # Full detection
    elif found > 0:
        return 0.5 + (found / min_expected) * 0.5     # Partial detection
    else:
        return 0.0                                     # No detection
```

**False Positive Score Formula (AC-7):**

```python
score = max(0.0, 1.0 - (false_positives / total_findings))
# Passed when score >= 0.7 (i.e., false positives <= 30% of total)
```

**Precision/Recall Formula (AC-8):**

```python
precision = true_positives / total_found if total_found > 0 else 1.0
recall = true_positives / total_expected if total_expected > 0 else 1.0
f1 = 2 * precision * recall / (precision + recall)
# Passed when f1 >= 0.6
```

**Skipped checks**: When ground truth does not contain expectations for a given category (e.g., SQL injection is not in DevSkim's scope), the check is skipped and treated as `passed=True, score=1.0`. This prevents penalizing DevSkim for known out-of-scope limitations.

### Coverage Checks (CV-1 to CV-8)

Located in `scripts/checks/coverage.py`. These checks verify that DevSkim analyzes files across expected languages and covers expected security categories.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| CV-1 | C# coverage | Coverage | C# files were analyzed (files > 0) | files_analyzed, issues_detected, categories_covered |
| CV-2 | Python coverage | Coverage | Python files were analyzed | files_analyzed, issues_detected, categories_covered |
| CV-3 | JavaScript coverage | Coverage | JavaScript files were analyzed | files_analyzed, issues_detected, categories_covered |
| CV-4 | Java coverage | Coverage | Java files were analyzed | files_analyzed, issues_detected, categories_covered |
| CV-5 | Go coverage | Coverage | Go files were analyzed | files_analyzed, issues_detected, categories_covered |
| CV-6 | C/C++ coverage | Coverage | C/C++ files were analyzed | files_analyzed, issues_detected, categories_covered |
| CV-7 | Multi-language support | Coverage | All expected languages analyzed | languages list, count |
| CV-8 | DD security category coverage | Coverage | At least one security category detected | total_categories, categories_detected, coverage_percentage, high_priority_covered |

**Per-Language Score Formula (CV-1 through CV-6):**

```python
score = 0.0
if files > 0:
    score += 0.4       # Language files were analyzed
if issues > 0:
    score += 0.3       # At least one issue detected
if len(categories) > 0:
    score += 0.3 * min(len(categories) / 3, 1.0)  # Multiple categories covered
```

**Category Coverage Score (CV-8):**

```python
# High-priority categories weighted at 60%
high_priority = ["sql_injection", "hardcoded_secret", "insecure_crypto", "xss", "command_injection"]
priority_score = (priority_covered / len(high_priority)) * 0.6

# Remaining categories weighted at 40%
other_score = (other_covered / other_denominator) * 0.4

category_score = min(priority_score + other_score, 1.0)
```

**Skipped checks**: Language checks are skipped (passed, score 1.0) when the corresponding language is not present in the ground truth.

### Edge Case Checks (EC-1 to EC-8)

Located in `scripts/checks/edge_cases.py`. These checks validate that DevSkim handles non-standard input gracefully.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| EC-1 | Empty files handling | Edge Cases | No issues reported for 0-line files | empty_file_count, empty_files list |
| EC-2 | Large files handling | Edge Cases | Files >1000 lines analyzed without crash | large_file_count, large_files (path + lines) |
| EC-3 | Mixed content files | Edge Cases | Files with multiple issue types processed | mixed_file_count, examples (path + categories) |
| EC-4 | Nested code handling | Edge Cases | Deeply nested structures analyzed | total_files_analyzed |
| EC-5 | Comment handling | Edge Cases | < 3 false positives in commented code | potential_comment_fps (count) |
| EC-6 | String literal handling | Edge Cases | < 3 false positives in string literals | potential_string_fps (count) |
| EC-7 | Minified code handling | Edge Cases | Minified files handled without crash | minified_candidates, total_files |
| EC-8 | Non-UTF8 encoding handling | Edge Cases | Encoding variations handled gracefully | note |

**Comment False Positive Detection (EC-5):**

```python
# Counts findings where code_snippet starts with comment markers
for issue in file_info.get("issues", []):
    snippet = issue.get("code_snippet", "").strip()
    if snippet.startswith("//") or snippet.startswith("#") or snippet.startswith("/*"):
        fps += 1
# score = 1.0 if fps == 0 else max(0.5, 1.0 - (fps * 0.1))
```

**String Literal False Positive Detection (EC-6):**

```python
# Checks for documentation/example patterns in findings
doc_patterns = ["example", "documentation", "sample", "demo", "test"]
# Counts findings where message or snippet contains doc patterns
```

### Performance Checks (PF-1 to PF-4)

Located in `scripts/checks/performance.py`. These checks measure DevSkim's execution speed and output completeness.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| PF-1 | Analysis duration | Performance | Within target time for repo size | duration_ms, duration_seconds, target_seconds, total_files |
| PF-2 | Files per second throughput | Performance | >= 5 files/second | files_per_second, total_files, duration_seconds |
| PF-3 | Lines per second throughput | Performance | Waived (always passes) | lines_per_second, total_lines, duration_seconds (waived=true) |
| PF-4 | Result completeness | Performance | >= 80% of expected sections present | has_metadata, has_summary, has_files, has_directories, has_statistics |

**Duration Targets (PF-1):**

| Repo Size | File Count | Target |
|-----------|------------|--------|
| Small | < 50 files | < 30 seconds |
| Medium | 50-500 files | < 120 seconds |
| Large | > 500 files | < 300 seconds |

**Duration Score Tiers:**

```python
if duration_seconds <= target * 0.5:
    score = 1.0
elif duration_seconds <= target:
    score = 0.8
elif duration_seconds <= target * 2:
    score = 0.6
else:
    score = 0.4
```

**Throughput Score Tiers (PF-2):**

| Files/Second | Score |
|-------------|-------|
| >= 20 | 1.0 |
| >= 10 | 0.9 |
| >= 5 | 0.7 |
| >= 1 | 0.5 |
| < 1 | 0.3 |

**Lines/Second Score Tiers (PF-3):**

| Lines/Second | Score |
|-------------|-------|
| >= 5000 | 1.0 |
| >= 2000 | 0.8 |
| >= 1000 | 0.6 |
| >= 500 | 0.5 |
| < 500 | 0.3 |

Note: PF-3 is waived (`passed=True` always) since line throughput depends heavily on file content density.

### Output Quality Checks (OQ-1)

Located in `scripts/checks/output_quality.py`. Validates the output against the Caldera envelope schema.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| OQ-1 | Schema validation | Output Quality | Zero validation errors | errors list (up to 5) |

**Validation Rules:**

For Caldera envelope format (`metadata` + `data`):
- Required metadata fields: `run_id`, `repo_id`, `branch`, `timestamp`
- Required data fields: `tool`, `summary`, `files`
- `data.tool` must equal `"devskim"`

For older envelope format (`schema_version` + `results`):
- Required root fields: `schema_version`, `generated_at`, `repo_name`, `repo_path`, `results`
- Required results fields: `tool`, `tool_version`, `metadata`, `summary`
- `results.tool` must equal `"devskim"`

### Integration Fit Checks (IF-1)

Located in `scripts/checks/integration_fit.py`. Validates that file paths conform to Caldera conventions.

| Check ID | Name | Category | Pass Criteria | Evidence Collected |
|----------|------|----------|---------------|-------------------|
| IF-1 | Relative file paths | Integration Fit | All file paths are relative (no absolute paths) | absolute_paths count |

**Score Formula:**

```python
score = 1.0 if total_files == 0 else max(0.0, 1.0 - (absolute_paths / total_files))
# Passed when absolute_paths == 0
```

---

## Scoring

### Programmatic Scoring

The overall programmatic score is the **unweighted arithmetic mean** of all check scores:

```python
@property
def score(self) -> float:
    if not self.checks:
        return 0.0
    return sum(c.score for c in self.checks) / len(self.checks)
```

Category-level scores are computed similarly as the mean of scores within each category:

```python
@property
def score_by_category(self) -> dict[str, float]:
    categories: dict[str, list[float]] = {}
    for check in self.checks:
        cat = check.category.value
        categories.setdefault(cat, []).append(check.score)
    return {cat: sum(scores) / len(scores) for cat, scores in categories.items()}
```

### Normalized Score

The raw score (0.0 to 1.0) is normalized to a 1-5 scale for decision thresholds and scorecard display:

```python
normalized_score = score * 5.0
```

### Scorecard Generation

The scorecard computes per-dimension weighted scores. Each dimension's weight is `1.0 / number_of_dimensions` (equal weighting):

```python
"weight": 1.0 / len(report.score_by_category)
"score": round(score * 5.0, 2)
"weighted_score": round(score * 5.0 / len(report.score_by_category), 2)
```

### LLM Judge Scoring

Each LLM judge produces a score on a 1-5 scale with sub-dimension scores. The combined LLM score uses the judge weights:

```
llm_combined = (
    detection_accuracy * 0.40 +
    rule_coverage * 0.25 +
    severity_calibration * 0.20 +
    security_focus * 0.15
)
```

Ground truth assertions can cap LLM scores. If assertions fail, the maximum score is capped at 2:

```python
gt_passed, gt_failures = self.run_ground_truth_assertions()
if not gt_passed:
    score = min(llm_score, 2)  # Cap at 2 if ground truth assertions fail
```

---

## Decision Thresholds

Decisions are based on the **normalized score** (0-5 scale, derived from the 0-1 raw score via `score * 5.0`):

| Decision | Normalized Score | Raw Score Equivalent | Interpretation |
|----------|-----------------|---------------------|----------------|
| STRONG_PASS | >= 4.0 | >= 80% | Excellent, production-ready security detection |
| PASS | >= 3.5 | >= 70% | Good, minor improvements possible |
| WEAK_PASS | >= 3.0 | >= 60% | Acceptable with caveats, review edge cases |
| FAIL | < 3.0 | < 60% | Significant issues in detection accuracy or coverage |

The `determine_decision()` function in `evaluate.py`:

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

The `EvaluationReport.decision` property uses a slightly different mapping (based on the 0-1 score directly) for console display:

```python
@property
def decision(self) -> str:
    if self.score >= 0.8:
        return "STRONG_PASS"
    elif self.score >= 0.6:
        return "PASS"
    elif self.score >= 0.5:
        return "WEAK_PASS"
    else:
        return "FAIL"
```

The process exits with code 0 if `score >= 0.5` and code 1 otherwise.

---

## LLM Judges

### Detection Accuracy Judge (40%)

Located in `evaluation/llm/judges/detection_accuracy.py`, prompt at `evaluation/llm/prompts/detection_accuracy.md`.

**Purpose**: Evaluates whether DevSkim correctly identifies security vulnerabilities within its specialized scope (insecure cryptography, unsafe deserialization, XXE, LDAP injection, information disclosure).

**Sub-dimensions:**

| Sub-dimension | Weight | Criteria |
|---------------|--------|----------|
| True Positive Rate | 40% | Are expected security issues within DevSkim's specialization detected? |
| False Positive Rate | 30% | Are there spurious findings? Is noise acceptable? |
| Vulnerability Classification | 30% | Are categories correctly identified? Are severity levels appropriate? |

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | >95% detection in specialized areas (crypto, deserialization), appropriate zero findings in out-of-scope categories |
| 4 | 85-95% in specialized areas, clear tool limitations acknowledged |
| 3 | 70-85% in specialized areas, reasonable gap handling |
| 2 | <70% even in core specializations (crypto, deserialization) |
| 1 | Fundamental issues in DevSkim's own specialty areas |

**Evidence collected:**
- `total_files_analyzed`, `total_findings`
- `security_categories` (counts by category: sql_injection, xss, path_traversal, secrets, crypto, deserialization, ldap_injection, information_disclosure, other)
- `findings_by_severity` (critical, important, moderate, low)
- `sample_findings` (up to 10 findings with rule, severity, message, file)
- `ground_truth` (files with expectations, required categories, min total issues)
- `evaluation_mode`, `synthetic_baseline`, `interpretation_guidance`

**Ground truth assertions:**
- Total findings must be >= `min_total_issues` from `csharp.json` ground truth
- If assertion fails, LLM score is capped at 2

**Severity mapping** (DevSkim to evaluation names):
```python
SEVERITY_MAP = {
    "critical": "critical",
    "high": "important",
    "medium": "moderate",
    "low": "low",
}
```

### Rule Coverage Judge (25%)

Located in `evaluation/llm/judges/rule_coverage.py`, prompt at `evaluation/llm/prompts/rule_coverage.md`.

**Purpose**: Evaluates breadth and depth of DevSkim's activated rule set.

**Sub-dimensions:**

| Sub-dimension | Weight | Criteria |
|---------------|--------|----------|
| Rule Breadth | 35% | How many unique security rules are triggered? Is the rule set comprehensive? |
| Category Coverage | 35% | Are all major security categories represented? Is distribution reasonable? |
| Ground Truth Alignment | 30% | Are expected security patterns being detected? Are required categories covered? |

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | >10 rules, all major categories, >90% ground truth alignment |
| 4 | 7-10 rules, most categories, 70-90% alignment |
| 3 | 5-7 rules, key categories present, 50-70% alignment |
| 2 | 3-5 rules, missing important categories, 30-50% alignment |
| 1 | <3 rules or major gaps, <30% alignment |

**Evidence collected:**
- `unique_rules_triggered` (count)
- `rules_by_frequency` (top 20 rules with counts)
- `rule_categories` (category-to-count mapping using `dd_category`)
- `ground_truth_comparison` (expected categories, covered categories, coverage rate)
- `security_domains` (OWASP Top 10 coverage assessment)

**Ground truth assertions:**
- At least 2 unique rules must be triggered across all analysis results
- If assertion fails, LLM score is capped at 2

### Severity Calibration Judge (20%)

Located in `evaluation/llm/judges/severity_calibration.py`, prompt at `evaluation/llm/prompts/severity_calibration.md`.

**Purpose**: Assesses whether DevSkim assigns appropriate severity levels to different vulnerability types.

**Sub-dimensions:**

| Sub-dimension | Weight | Criteria |
|---------------|--------|----------|
| Severity Appropriateness | 40% | Are critical findings truly critical (RCE, auth bypass)? Are low-severity findings appropriately downgraded? |
| Consistency | 35% | Is the same vulnerability type assigned consistent severity? Is the distribution reasonable? |
| Industry Alignment | 25% | Does severity align with CVSS-like principles? Would a security team trust these ratings? |

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | Severity consistent within categories, reasonable for pattern-matching tool |
| 4 | Minor inconsistencies, overall calibration appropriate for static analysis |
| 3 | Some unexpected ratings, but defensible given tool limitations |
| 2 | Inconsistent ratings within the same category |
| 1 | Severity inversions (low-risk marked critical, high-risk marked low) |

**DevSkim-specific calibration expectations:**
- Crypto findings at CRITICAL is acceptable (DevSkim cannot distinguish security-use vs. checksum-use)
- Deserialization at MEDIUM is acceptable (DevSkim cannot determine data source trust level)
- Absence of LOW severity is expected (DevSkim focuses on high-signal security issues)

**Evidence collected:**
- `severity_distribution` (critical, important, moderate, low counts)
- `severity_by_category` (per-category severity breakdown)
- `severity_samples` (up to 15 samples with rule, severity, category, message)
- `severity_guidelines` (expected severity by category)

**Ground truth assertions:**
- No single security category should have findings spanning more than 2 severity levels
- If assertion fails, LLM score is capped at 2

### Security Focus Judge (15%)

Located in `evaluation/llm/judges/security_focus.py`, prompt at `evaluation/llm/prompts/security_focus.md`.

**Purpose**: Verifies that DevSkim maintains focus on security-relevant findings rather than general code quality issues.

**Sub-dimensions:**

| Sub-dimension | Weight | Criteria |
|---------------|--------|----------|
| Security Relevance | 50% | Are findings primarily security-related? Are issues mapped to known weaknesses? |
| Signal Quality | 30% | Are security findings actionable? Is noise from non-security issues minimal? |
| Appropriate Scope | 20% | Does DevSkim avoid non-security lint issues? |

**Scoring Rubric:**

| Score | Criteria |
|-------|----------|
| 5 | >90% security focus, all findings actionable, minimal noise |
| 4 | 80-90% security focus, low noise |
| 3 | 60-80% security focus, some irrelevant findings |
| 2 | 40-60% security focus, significant noise |
| 1 | <40% security focus, tool is not security-focused |

**Security keyword detection**: Findings are classified as security-related if they contain any of these keywords in rule_id, message, or dd_category:

```python
security_keywords = {
    "inject", "sql", "xss", "script", "secret", "password", "credential",
    "crypto", "encrypt", "hash", "auth", "session", "token", "csrf",
    "deserial", "traversal", "path", "redirect", "ssrf", "xxe", "ldap",
    "random", "rng", "prng", "entropy",
}
```

**Evidence collected:**
- `security_findings` (count), `quality_findings` (count), `security_ratio`
- `security_samples` (up to 8 samples), `quality_samples` (up to 5 samples)
- `focus_assessment` (expected behavior, threshold, keywords checked)

**Ground truth assertions:**
- If total findings > 10, security ratio must be >= 50%
- If assertion fails, LLM score is capped at 2

### Additional Prompt Templates

Two additional prompt templates exist in `evaluation/llm/prompts/` for future or alternative use:

| Prompt File | Purpose |
|-------------|---------|
| `accuracy.md` | Simplified detection accuracy prompt (no DevSkim-specific context) |
| `actionability.md` | Finding actionability evaluation (clarity, location precision, fix guidance) |

The `actionability.md` prompt evaluates three sub-dimensions:
- **Finding Clarity** (35%): Are findings clearly explained? Is security impact obvious?
- **Location Precision** (30%): Are file paths and line numbers accurate? Are code snippets useful?
- **Fix Guidance** (35%): Does the finding suggest remediation? Are DD categories meaningful?

---

## Ground Truth

### Methodology

Ground truth files are located in `evaluation/ground-truth/` and define expected DevSkim behavior against synthetic test repositories.

**Generation process:**
1. Create synthetic C# source files with known vulnerability patterns (insecure crypto, unsafe deserialization, XXE, security misconfigurations)
2. Run DevSkim with CALDERA custom rules against the synthetic repository
3. Manually verify each finding against the known vulnerability patterns
4. Document expected detection counts, rule IDs, and line numbers
5. Identify out-of-scope patterns (SQL injection, XSS, path traversal) and document expected zero detections

### Ground Truth Files

| File | Scenario | Language | Expected Issues | Key Patterns |
|------|----------|----------|-----------------|--------------|
| `csharp.json` | Primary C# security | C# | >= 25 total | insecure_crypto, insecure_random, xxe, command_injection, security_misconfiguration, deserialization, ldap_injection, information_disclosure |
| `api-security.json` | API security | C# | >= 2 total | ldap_injection, deserialization, security_misconfiguration |
| `clean.json` | Negative test (safe code) | C# | 0 expected | Validates zero false positives on safe patterns |
| `deserialization.json` | Deserialization focus | C# | >= 2 total | BinaryFormatter, TypeNameHandling.All |
| `xxe.json` | XXE focus | C# | >= 4 total | XmlResolver, DtdProcessing, XmlTextReader |

### Ground Truth Schema

Each ground truth file follows this structure:

```json
{
  "schema_version": "1.0",
  "scenario": "<scenario-name>",
  "language": "<language>",
  "description": "...",
  "generated_at": "2026-02-06T12:00:00Z",
  "repo_path": "eval-repos/synthetic/<path>",
  "expected": {
    "language": "<language>",
    "version": "<gt-version>",
    "aggregate_expectations": {
      "min_total_issues": <int>,
      "max_false_positives": <int>,
      "required_categories": ["<category1>", "<category2>"],
      "notes": "..."
    }
  },
  "files": {
    "<FileName.cs>": {
      "expected_categories": ["<category>"],
      "expected_issues": [
        {
          "category": "<dd_category>",
          "count": <int>,
          "lines": [<line_numbers>],
          "notes": "..."
        },
        {
          "rule_id": "<DevSkim-rule-id>",
          "count": <int>,
          "description": "..."
        }
      ],
      "total_expected": <int>,
      "false_positives_allowed": <int>,
      "notes": "..."
    }
  }
}
```

### Expected Values by Source File

#### csharp.json (Primary Scenario)

| Source File | Expected Categories | Total Expected | Key Rules | Notes |
|-------------|--------------------|--------------:|-----------|-------|
| InsecureCrypto.cs | insecure_crypto, insecure_random | 11 | DS126858 (x8), DS106863, DS187371, CALDERA001 | MD5, SHA1, DES, ECB mode, System.Random |
| InsecureUrls.cs | ldap_injection | 6 | DS137138 (x6) | HTTP URLs flagged as insecure transport |
| SecurityMisconfigurations.cs | security_misconfiguration, command_injection | 6 | CALDERA006, CALDERA007 (x2), CALDERA008, CALDERA009 (x2) | Cookies, CORS, cmd.exe |
| XxeVulnerability.cs | xxe | 5 | CALDERA002 (x2), CALDERA003, CALDERA004 (x2) | XmlResolver, DtdProcessing, XmlTextReader |
| InsecureRandom.cs | insecure_random | 5 | CALDERA001 (x5) | System.Random usage |
| Deserialization.cs | deserialization | 2 | DS425040 (x2) | BinaryFormatter, TypeNameHandling |
| SqlInjection.cs | information_disclosure | 1 | DS162092 | Debug code (NOT SQL injection detection) |
| HardcodedSecrets.cs | (none) | 0 | -- | Not detected by DevSkim |
| PathTraversal.cs | (none) | 0 | -- | Not detected by DevSkim |
| XssVulnerability.cs | (none) | 0 | -- | Not detected by DevSkim |
| SafeCode.cs | (none) | 0 | -- | Negative test case |

#### clean.json (Negative Test)

| Source File | Expected Categories | Total Expected | Notes |
|-------------|--------------------|--------------:|-------|
| SafeCode.cs | (none) | 0 | Uses SHA256, RNGCryptoServiceProvider, AES-CBC, parameterized SQL, safe JsonConvert. Up to 2 false positives tolerated. |

#### deserialization.json (Focused Scenario)

| Source File | Expected Categories | Total Expected | Key Rules |
|-------------|--------------------|--------------:|-----------|
| Deserialization.cs | deserialization | 2 | DS425040 (x2) -- BinaryFormatter.Deserialize and TypeNameHandling.All |

#### xxe.json (Focused Scenario)

| Source File | Expected Categories | Total Expected | Key Rules |
|-------------|--------------------|--------------:|-----------|
| XxeVulnerability.cs | xxe | 5 | CALDERA002 (x2), CALDERA003, CALDERA004 (x2) |

#### api-security.json (API Scenario)

| Source File | Expected Categories | Total Expected | Key Rules |
|-------------|--------------------|--------------:|-----------|
| CorsConfig.cs | security_misconfiguration | 1 | CALDERA009 |
| AuthHeaders.cs | ldap_injection | 1 | DS137138 |
| InputValidation.cs | deserialization | 1 | DS425040 |
| ApiEndpoints.cs | (none) | 0 | -- |
| SafeApiCode.cs | (none) | 0 | -- |

### DevSkim Rule Reference

Rules referenced in ground truth:

| Rule ID | Source | Description | Category |
|---------|--------|-------------|----------|
| DS126858 | Built-in | Weak/Broken Hash Algorithm (MD5, SHA1) | insecure_crypto |
| DS106863 | Built-in | DES block cipher | insecure_crypto |
| DS187371 | Built-in | Weak cipher mode (ECB) | insecure_crypto |
| DS425040 | Built-in | Do not deserialize untrusted data | deserialization |
| DS137138 | Built-in | Insecure URL (HTTP instead of HTTPS) | ldap_injection |
| DS162092 | Built-in | Debug code in production | information_disclosure |
| CALDERA001 | Custom | Insecure Random Number Generator (System.Random) | insecure_random |
| CALDERA002 | Custom | XML External Entity (XXE) via XmlResolver | xxe |
| CALDERA003 | Custom | XML External Entity (XXE) via DTD Processing | xxe |
| CALDERA004 | Custom | Insecure XmlTextReader Usage | xxe |
| CALDERA006 | Custom | Shell Command Execution (cmd.exe) | command_injection |
| CALDERA007 | Custom | Insecure Cookie - HttpOnly Disabled | security_misconfiguration |
| CALDERA008 | Custom | Insecure Cookie - Secure Flag Disabled | security_misconfiguration |
| CALDERA009 | Custom | Disabled CORS Validation | security_misconfiguration |

### Security Categories

The evaluation recognizes 15 DD security categories as defined in `scripts/checks/__init__.py`:

```
sql_injection, hardcoded_secret, insecure_crypto, path_traversal, xss,
deserialization, xxe, command_injection, ldap_injection, open_redirect,
ssrf, csrf, information_disclosure, broken_access_control, security_misconfiguration
```

DevSkim (with CALDERA custom rules) reliably detects issues in: `insecure_crypto`, `insecure_random`, `xxe`, `command_injection`, `security_misconfiguration`, `deserialization`, `ldap_injection` (insecure URLs), and `information_disclosure`.

DevSkim does NOT detect (by design): `sql_injection`, `hardcoded_secret`, `path_traversal`, `xss`, `open_redirect`, `ssrf`, `csrf`, `broken_access_control`.

---

## Evidence Collection

Each check collects structured evidence for transparency and debugging:

```python
@dataclass
class CheckResult:
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "SQL injection detection"
    category: CheckCategory # ACCURACY, COVERAGE, EDGE_CASES, PERFORMANCE, OUTPUT_QUALITY, INTEGRATION_FIT
    passed: bool
    score: float            # 0.0 to 1.0
    message: str            # Human-readable result description
    evidence: dict[str, Any]  # Supporting data for audit trail
```

### Evidence Types by Check Category

| Category | Evidence Fields |
|----------|----------------|
| Accuracy (AC-1 to AC-6) | `count` (found), `expected` (min_expected, max_false_positives) |
| Accuracy (AC-7) | `false_positives`, `total_findings`, `safe_files_checked` |
| Accuracy (AC-8) | `precision`, `recall`, `f1`, `true_positives`, `total_found`, `total_expected` |
| Coverage (CV-1 to CV-6) | `files_analyzed`, `issues_detected`, `categories_covered` |
| Coverage (CV-7) | `languages` list, `count` |
| Coverage (CV-8) | `total_categories`, `categories_detected`, `coverage_percentage`, `high_priority_covered`, `by_category` |
| Edge Cases (EC-1) | `empty_file_count`, `empty_files` |
| Edge Cases (EC-2) | `large_file_count`, `large_files` (path + lines) |
| Edge Cases (EC-5/EC-6) | `potential_comment_fps` / `potential_string_fps` |
| Performance (PF-1) | `duration_ms`, `duration_seconds`, `target_seconds`, `total_files` |
| Performance (PF-2/PF-3) | `files_per_second` / `lines_per_second`, `total_files`/`total_lines`, `duration_seconds` |
| Performance (PF-4) | `has_metadata`, `has_summary`, `has_files`, `has_directories`, `has_statistics` |
| Output Quality (OQ-1) | `errors` list (up to 5 validation errors) |
| Integration Fit (IF-1) | `absolute_paths` count |

---

## LLM Judge Confidence

Each LLM judge reports a confidence level (0.0 to 1.0):

| Confidence | Interpretation |
|------------|----------------|
| >= 0.9 | High confidence, reliable score |
| 0.7-0.9 | Moderate confidence, some uncertainty |
| < 0.7 | Low confidence, manual review recommended |

Ground truth assertions can cap LLM scores: if assertions fail, the maximum judge score is capped at 2 regardless of the LLM's evaluation.

---

## Running the Evaluation

### Programmatic Evaluation

```bash
# Full evaluation with verbose console output
cd src/tools/devskim
make evaluate

# Quick evaluation (skips performance checks)
.venv/bin/python scripts/evaluate.py --quick

# JSON-only output (no console report)
.venv/bin/python scripts/evaluate.py --json

# Custom analysis path and ground truth
.venv/bin/python scripts/evaluate.py \
    --analysis outputs/<run-id>/output.json \
    --ground-truth evaluation/ground-truth \
    --output evaluation/results/evaluation_report.json

# Disable colored output
.venv/bin/python scripts/evaluate.py --no-color
```

### LLM Evaluation

```bash
# Run LLM evaluation (requires analysis output)
make evaluate-llm

# Specify model
make evaluate-llm LLM_MODEL=opus
```

### Full Pipeline

```bash
# End-to-end: setup, analyze, evaluate
make all

# Step by step
make setup
make analyze                  # Analyze synthetic repos
make evaluate                 # Programmatic evaluation
make evaluate-llm             # LLM evaluation
```

### Evaluation Outputs

Evaluation artifacts are written to fixed locations:

```
evaluation/
  results/
    evaluation_report.json   # Programmatic evaluation report
  scorecard.json             # Structured scorecard (JSON)
  scorecard.md               # Human-readable scorecard (Markdown)
  llm/
    results/                 # LLM judge results
```

### Evaluation Report Structure

```json
{
  "timestamp": "2026-02-13T09:00:00Z",
  "analysis_path": "outputs/<run-id>/output.json",
  "ground_truth_dir": "evaluation/ground-truth",
  "decision": "STRONG_PASS",
  "score": 0.95,
  "summary": {
    "passed": 28,
    "failed": 0,
    "total": 28,
    "score": 0.95,
    "decision": "STRONG_PASS",
    "score_by_category": {
      "accuracy": 0.95,
      "coverage": 0.90,
      "edge_cases": 0.88,
      "performance": 0.85,
      "output_quality": 1.0,
      "integration_fit": 1.0
    },
    "passed_by_category": {
      "accuracy": [8, 8],
      "coverage": [8, 8],
      "edge_cases": [8, 8],
      "performance": [4, 4],
      "output_quality": [1, 1],
      "integration_fit": [1, 1]
    }
  },
  "checks": [
    {
      "check_id": "AC-1",
      "name": "SQL injection detection",
      "category": "accuracy",
      "passed": true,
      "score": 1.0,
      "message": "Skipped: No SQL injection expectations in ground truth",
      "evidence": {"skipped": true, "reason": "..."}
    }
  ]
}
```

---

## Extending the Evaluation

### Adding a Programmatic Check

1. Add the check function to the appropriate module in `scripts/checks/`:
   ```python
   # In scripts/checks/accuracy.py (or new module)
   results.append(CheckResult(
       check_id="AC-9",
       name="New check name",
       category=CheckCategory.ACCURACY,
       passed=condition,
       score=computed_score,
       message="Description of result",
       evidence={"key": "value"},
   ))
   ```

2. If creating a new module, register it in `scripts/checks/__init__.py`:
   ```python
   from .new_module import run_new_checks
   ```

3. Add the runner call to `scripts/evaluate.py`:
   ```python
   new_checks = run_new_checks(analysis, ground_truth_dir)
   all_checks.extend(new_checks)
   ```

4. Update ground truth files if the check requires new expected values.

5. Run `make evaluate` to verify the check works correctly.

### Adding an LLM Judge

1. Create the judge class in `evaluation/llm/judges/<dimension>.py`:
   - Extend `BaseJudge` from `evaluation/llm/judges/base.py`
   - Implement `dimension_name`, `weight`, `collect_evidence()`, `get_default_prompt()`, `run_ground_truth_assertions()`

2. Create the prompt template in `evaluation/llm/prompts/<dimension>.md`:
   - Include `{{ evidence }}` placeholder
   - Define evaluation criteria with weights
   - Provide a scoring rubric (1-5 scale)
   - Specify required JSON output format with `score`, `confidence`, `reasoning`, `evidence_cited`, `recommendations`, `sub_scores`

3. Register the judge in `evaluation/llm/judges/__init__.py`:
   ```python
   from .new_judge import NewJudge
   ```

4. Update this document.

### Adding Ground Truth

1. Create a synthetic test repository in `eval-repos/synthetic/<scenario>/`
2. Add source files with known vulnerability patterns
3. Run DevSkim against the repository and verify findings
4. Create `evaluation/ground-truth/<scenario>.json` following the schema above
5. Document expected detections and known out-of-scope patterns

### Updating Thresholds

Threshold values are defined within check functions:

```python
# In performance.py
duration_target = 30    # PF-1: seconds for small repo
fps_threshold = 5       # PF-2: files per second

# In accuracy.py
fp_pass_threshold = 0.7 # AC-7: false positive score threshold
f1_pass_threshold = 0.6 # AC-8: F1 score threshold

# In edge_cases.py
comment_fp_max = 3      # EC-5: max comment false positives
string_fp_max = 3       # EC-6: max string literal false positives
```

---

## References

- [DevSkim GitHub](https://github.com/microsoft/DevSkim)
- [DevSkim Rules Documentation](https://github.com/microsoft/DevSkim/tree/main/rules)
- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [LLM-as-a-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685)
- [Project Caldera EVALUATION.md](../../../docs/EVALUATION.md)
