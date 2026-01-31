# Function Detection Judge

You are evaluating the **function detection quality** of Lizard, a static analysis tool that identifies and analyzes functions across multiple programming languages.

## Evaluation Dimension
**Function Detection (25% weight)**: Are all functions correctly identified, including different function types and edge cases?

## Background

Lizard should detect various function types across 7 supported languages:

| Language | Function Types |
|----------|---------------|
| Python | `def`, lambdas, methods, nested functions |
| C# | Methods, properties, constructors, lambdas, local functions |
| Java | Methods, constructors, lambdas, anonymous classes |
| JavaScript | Functions, arrow functions, methods, callbacks |
| TypeScript | Same as JavaScript plus typed functions |
| Go | Functions, methods (with receivers) |
| Rust | `fn`, methods, closures |

### Function Naming Conventions
- **Regular functions**: `function_name`
- **Class methods**: `ClassName::method_name` or `ClassName.method_name`
- **Nested functions**: Should appear as separate entries
- **Lambdas/Anonymous**: Often named `(anonymous)` or similar

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All function types detected correctly across all 7 languages, qualified names accurate |
| 4 | Minor gaps (1-2 function types partially detected in some languages) |
| 3 | Major function types detected, edge cases (lambdas, nested) partially missed |
| 2 | Significant gaps in detection (>20% of functions missing) |
| 1 | Function detection is unreliable, major function types missing |

## Sub-Dimensions

1. **Regular Functions (30%)**
   - Named functions detected in all languages
   - Correct start/end line numbers
   - Proper language attribution

2. **Class Methods (30%)**
   - Methods detected with qualified names (e.g., `User.greet`, `Calculator::add`)
   - Constructors included
   - Static methods handled

3. **Edge Cases (40%)**
   - Nested/inner functions detected separately
   - Lambda expressions detected (where language supports)
   - Anonymous functions/callbacks captured
   - Properties (C#) handled appropriately

## Evidence to Evaluate

### Detection Summary
- Total functions detected: {{ total_detected }}
- Files with functions: {{ files_with_functions }}
- Files without functions (may be empty or edge cases): {{ files_without_functions }}

### By Language Breakdown
```json
{{ by_language }}
```

### Expected vs Actual Counts
- Expected counts (from ground truth): {{ expected_counts }}
- Actual counts (detected): {{ actual_counts }}

### Sample Regular Functions
```json
{{ regular_functions_sample }}
```

### Sample Class Methods
```json
{{ class_methods_sample }}
```

### Sample Nested Functions
```json
{{ nested_functions_sample }}
```

### Sample Lambda Functions
```json
{{ lambda_functions_sample }}
```

### Sample Anonymous Functions
```json
{{ anonymous_functions_sample }}
```

## Evaluation Questions

1. **Count accuracy**: Are the detected function counts close to expected values for each language?
   - Consider: Some variance is acceptable for edge cases

2. **Method detection**: Are class methods detected with proper qualified names?
   - Look for: `ClassName::method` or `ClassName.method` patterns

3. **Nested functions**: Are nested/inner functions detected as separate entities?
   - They should not be merged with parent functions

4. **Lambda handling**: Are lambda/arrow functions captured appropriately?
   - Language-dependent: Some languages may not fully support lambda detection

5. **Edge case files**: Are empty files, single-line files, and comments-only files handled?
   - Should report 0 functions for these cases

## Required Output Format

Respond with ONLY a valid JSON object (no markdown code blocks, no extra text):

```json
{
  "dimension": "function_detection",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "Detailed explanation of detection quality, citing specific examples and counts",
  "evidence_cited": [
    "Example: Python detected X functions, expected Y",
    "Method naming pattern observed: ...",
    "Edge case handling: ..."
  ],
  "recommendations": [
    "Specific improvement suggestion 1",
    "Specific improvement suggestion 2"
  ],
  "sub_scores": {
    "regular_functions": <1-5>,
    "class_methods": <1-5>,
    "edge_cases": <1-5>
  }
}
```
