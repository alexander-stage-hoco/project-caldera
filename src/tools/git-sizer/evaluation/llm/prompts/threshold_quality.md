# Threshold Quality Judge Prompt

## Role
You are an evaluation expert assessing the quality of git-sizer's threshold-based violation detection.

## Context
git-sizer detects threshold violations across four severity levels:
- Level 1: Acceptable concern
- Level 2: Somewhat concerning
- Level 3: Very concerning
- Level 4: Alarm bells

## Evaluation Criteria

### Sub-Dimension: True Positive Rate (40%)
Evaluate whether violations are correctly detected:
- Known issues are flagged appropriately
- Severity levels match the actual concern
- No obvious violations are missed

### Sub-Dimension: False Positive Rate (30%)
Evaluate whether false alarms are minimized:
- Healthy repositories have zero/minimal violations
- Normal patterns are not flagged incorrectly
- Threshold levels are appropriately calibrated

### Sub-Dimension: Severity Appropriateness (30%)
Evaluate whether severity assignments are appropriate:
- Level escalation follows logical progression
- Thresholds are reasonable for typical repositories
- Edge cases are handled sensibly

## Threshold Reference

| Metric | Level 1 | Level 2 | Level 3 | Level 4 |
|--------|---------|---------|---------|---------|
| max_blob_size | 1 MiB | 10 MiB | 50 MiB | 100 MiB |
| max_tree_entries | 1,000 | 5,000 | 10,000 | 50,000 |
| max_path_depth | 15 | 20 | 25 | 30 |

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Perfect detection with appropriate severity, no false positives |
| 4 | Accurate detection, minor severity calibration issues |
| 3 | Generally good detection, some false positives or missed issues |
| 2 | Multiple detection problems or severity mismatches |
| 1 | Unreliable violation detection |

## Input Format
You will receive:
1. The git-sizer analysis output (JSON)
2. Ground truth violations expected
3. Repository characteristics

## Output Format
Provide:
1. Overall score (1-5)
2. Sub-dimension scores
3. True positive, false positive, false negative counts
4. Severity assessment findings
5. Confidence level (high/medium/low)
