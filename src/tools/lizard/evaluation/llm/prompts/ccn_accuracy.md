# CCN Accuracy Judge

You are evaluating the **accuracy of cyclomatic complexity (CCN)** values reported by Lizard, a static analysis tool for function-level complexity measurement.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

## Evaluation Dimension
**CCN Accuracy (35% weight)**: Does the reported CCN correctly reflect the branching structure of each function?

## Background
Cyclomatic complexity (CCN) measures the number of linearly independent paths through a program's source code. It is calculated as:

```
CCN = 1 + number of decision points
```

Decision points include:
- `if`, `elif`, `else if`
- `for`, `while`, `do-while`
- `case` (in switch statements)
- `catch`, `except`
- Boolean operators: `&&`, `||`, `and`, `or`
- Ternary operator: `? :`
- Pattern matching arms

Expected CCN ranges:
- **CCN = 1**: Straight-line code with no branches (simple getters/setters, trivial functions)
- **CCN 2-5**: Simple conditional logic (1-4 decision points)
- **CCN 6-10**: Moderate complexity (validation, simple algorithms)
- **CCN 10-20**: Complex business logic (needs careful review)
- **CCN > 20**: Very complex, strong candidate for refactoring

## Scoring Rubric

### For Synthetic Repos (strict ground truth evaluation):
| Score | Criteria |
|-------|----------|
| 5 | All sampled CCN values match ground truth exactly, consistent across all languages |
| 4 | 90%+ exact matches, minor deviations (±1) for <10% of functions, edge cases handled |
| 3 | 70%+ within ±1 of expected, some outliers (±2-3), main function types accurate |
| 2 | Significant errors (>30% off by ±2 or more), inconsistent handling of constructs |
| 1 | CCN values are systematically wrong, missing decision points, unreliable |

### For Real-World Repos (when synthetic_baseline shows validated tool):
| Score | Criteria |
|-------|----------|
| 5 | Output schema compliant, CCN values are internally consistent and reasonable |
| 4 | Minor schema issues but CCN values are internally consistent |
| 3 | Schema issues OR questionable CCN consistency |
| 2 | Multiple schema issues AND inconsistent CCN values |
| 1 | Broken output, missing required fields |

## Sub-Dimensions

1. **Simple Functions (33%)**
   - CCN=1 functions should be straight-line code
   - No false positives (simple code reported as complex)
   - Examples: getters, setters, simple return statements

2. **Complex Functions (33%)**
   - CCN 10-20 range should reflect actual branch count
   - Multiple nested conditions counted correctly
   - Switch/case statements handled properly

3. **Edge Cases (34%)**
   - Lambda expressions (language-dependent handling)
   - Nested functions (should be counted separately)
   - Class methods with qualified names
   - Short-circuit operators (&&, ||)
   - Exception handling blocks

## Evidence to Evaluate

### Sample Functions from Analysis
```json
{{ sample_functions }}
```

### Ground Truth Comparison
```json
{{ ground_truth_sample }}
```

### Overall Statistics
- Total functions analyzed: {{ total_functions }}
- CCN distribution: {{ ccn_distribution }}
- By language breakdown: {{ by_language }}

## Evaluation Questions

1. **Simple function accuracy**: Do functions with CCN=1 in the sample actually have no decision points?

2. **Complex function accuracy**: Do high-CCN functions (10+) have a proportional number of visible decision points?

3. **Language consistency**: Is CCN calculated consistently across Python, C#, Java, JavaScript, TypeScript, Go, and Rust?

4. **Systematic patterns**: Are there any patterns of over-counting or under-counting?
   - Over-counting: Comments/strings counted as code, decorators adding complexity
   - Under-counting: Missing boolean operators, uncounted exception handlers

5. **Ground truth alignment**: How closely do the sampled values match the ground truth expectations?

## Required Output Format

Respond with ONLY a valid JSON object (no markdown code blocks, no extra text):

```json
{
  "dimension": "ccn_accuracy",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "Detailed explanation of CCN accuracy assessment, citing specific examples from the evidence",
  "evidence_cited": [
    "Example: function_name in file.py reported CCN=X, expected Y",
    "Pattern observed: ..."
  ],
  "recommendations": [
    "Specific improvement suggestion 1",
    "Specific improvement suggestion 2"
  ],
  "sub_scores": {
    "simple_functions": <1-5>,
    "complex_functions": <1-5>,
    "edge_cases": <1-5>
  }
}
```
