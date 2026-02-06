# Graph Quality Evaluation

You are an expert graph theory analyst evaluating DependenSee's dependency graph construction.

## Evaluation Context

{{ interpretation_guidance }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Judge graph structure quality: Are nodes and edges properly typed?
- Focus on internal consistency, not absolute counts
- A well-formed graph with few nodes is still high quality

## Task

Evaluate the quality and consistency of the generated dependency graph structure.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

### 1. Structural Completeness (35%)
Does the graph contain all expected nodes and edges?
- **5**: All projects and packages represented as nodes with correct edges
- **4**: Minor missing elements (<5%)
- **3**: Some elements missing (5-15%)
- **2**: Significant gaps (15-30%)
- **1**: Graph is incomplete (>30% missing)

### 2. Internal Consistency (35%)
Is the graph internally consistent?
- **5**: No dangling references, all edge targets exist as nodes
- **4**: Rare inconsistencies (<2%)
- **3**: Some inconsistencies (2-10%)
- **2**: Many inconsistencies (10-20%)
- **1**: Severely inconsistent (>20% dangling refs)

### 3. Connectivity (30%)
Are all nodes appropriately connected?
- **5**: No orphan nodes (all nodes have at least one edge)
- **4**: Few orphan nodes (<5%)
- **3**: Some orphan nodes (5-15%)
- **2**: Many orphan nodes (15-30%)
- **1**: Most nodes are orphans (>30%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation of your evaluation>",
  "evidence_cited": [
    "<specific evidence from the graph structure>",
    "<node/edge counts and consistency metrics>"
  ],
  "recommendations": [
    "<suggestions for improving graph quality>",
    "<edge types to add or fix>"
  ],
  "sub_scores": {
    "structural_completeness": <1-5>,
    "internal_consistency": <1-5>,
    "connectivity": <1-5>
  }
}
