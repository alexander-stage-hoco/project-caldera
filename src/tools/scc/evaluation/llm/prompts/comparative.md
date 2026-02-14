# Comparative Judge

You are evaluating scc **against alternative tools** (cloc, tokei, loc).

## Evaluation Dimension

**Comparative Analysis (8% weight)**: How does scc compare to alternatives?

## Comparison Criteria

| Aspect | Weight |
|--------|--------|
| Speed | 25% |
| Accuracy | 25% |
| Output richness | 20% |
| Language support | 15% |
| Maintenance/community | 15% |

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | Best in class: Superior to all alternatives in key areas |
| 4 | Above average: Better than most alternatives |
| 3 | Competitive: On par with alternatives |
| 2 | Below average: Alternatives are generally better |
| 1 | Inferior: Significant disadvantages vs alternatives |

## Evidence to Evaluate

{{ evidence }}

### scc Performance
```json
{{ scc_results }}
```

### Alternative Tool Results (if available)
{{ alternative_results }}

### Known Comparisons
- scc: Written in Go, parallel processing, complexity calculation
- cloc: Perl, mature, wide language support
- tokei: Rust, fast, accurate
- loc: Rust, minimal, very fast

## Evaluation Questions

1. How does scc's speed compare on the test repositories?
2. Is complexity calculation a significant advantage?
3. Does scc support all languages needed for DD Platform?
4. How active is the project (stars, recent commits)?
5. What unique features does scc provide?

## Evaluation Approach

Score based on the known comparison data and scc results provided. scc's key differentiators are: Go-based parallelism, complexity calculation, and 200+ language support. Provide your JSON response directly.

## Required Output Format

```json
{
  "dimension": "comparative",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed comparison>",
  "evidence_cited": ["<specific benchmarks or features>"],
  "recommendations": ["<areas where alternatives excel>"]
}
```
