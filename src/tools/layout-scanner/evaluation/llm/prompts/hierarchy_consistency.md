# Hierarchy Consistency Evaluation

You are evaluating the Layout Scanner's file/directory hierarchy consistency.

## Evaluation Dimension: Hierarchy Consistency (Weight: 25%)

This dimension assesses the correctness and consistency of parent-child relationships in the output.

### Sub-Dimensions

| Sub-Dimension | Weight | Focus |
|---------------|--------|-------|
| Parent-Child Relationships | 35% | Are IDs correctly linked? |
| Depth Calculations | 25% | Are depth values correct? |
| Count Consistency | 25% | Do direct/recursive counts match? |
| Path Coherence | 15% | Do paths match hierarchy position? |

---

## What to Evaluate

### 1. Parent-Child Relationships (35%)

**Verification Points:**
- Every file must have a valid `parent_directory_id`
- `parent_directory_id` must exist in the directories object
- Root directory should be identifiable (depth=0 or no parent)

**Example Valid Relationship:**
```json
// File
{
  "path": "src/main.py",
  "parent_directory_id": "d-abc123"
}

// Directory
{
  "id": "d-abc123",
  "path": "src"
}
```

### 2. Depth Calculations (25%)

**Rules:**
- Root directory: depth = 0
- Files/dirs in root: depth = 0 (for root-level files) or 1 (in subdir)
- `depth` should equal `path.count("/")`

**Examples:**
| Path | Expected Depth |
|------|----------------|
| `README.md` | 0 |
| `src/main.py` | 1 |
| `src/utils/helpers.py` | 2 |
| `tests/unit/test_main.py` | 2 |

### 3. Count Consistency (25%)

**Rules:**
- `recursive_file_count` >= `direct_file_count`
- `recursive_size_bytes` >= `direct_size_bytes`
- `recursive_directory_count` >= `direct_directory_count`
- Parent directory recursive counts should include child counts

### 4. Path Coherence (15%)

**Verification:**
- File path should start with parent directory path
- Path segments should match directory names
- No orphaned paths (paths without valid parents)

---

## Evidence

### Hierarchy Sample
{{ hierarchy_sample }}

### Statistics
{{ statistics }}

### Parent-Child Relationships
{{ relationships }}

---

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 5 | All relationships valid, depths correct, counts consistent, paths coherent |
| 4 | 99%+ relationships valid, minor depth or count discrepancies |
| 3 | 95%+ relationships valid, some inconsistencies in counts |
| 2 | 90-95% relationships valid, multiple hierarchy issues |
| 1 | <90% valid relationships, hierarchy unreliable |

---

## Required Output

Analyze the evidence and return a JSON object with this exact structure:

```json
{
    "dimension": "hierarchy_consistency",
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation of your assessment>",
    "sub_scores": {
        "parent_child_relationships": <1-5>,
        "depth_calculations": <1-5>,
        "count_consistency": <1-5>,
        "path_coherence": <1-5>
    },
    "evidence_cited": [
        "<quote specific hierarchy relationships>",
        "<note any inconsistencies found>"
    ],
    "recommendations": [
        "<specific improvements if score < 5>"
    ]
}
```

**Important:**
- Verify parent IDs actually exist
- Check depth calculations match path structure
- Confirm recursive counts >= direct counts
- Look for orphaned files or broken references
