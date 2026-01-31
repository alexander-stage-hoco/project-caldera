# Shared Evaluation Framework

This module provides a standardized `BaseJudge` implementation for LLM-as-a-Judge evaluation across all Project Caldera analysis tools. Each tool's LLM judges should inherit from this class to ensure consistent evaluation patterns.

## Overview

The shared evaluation framework provides:

- **JudgeResult**: A standardized dataclass for evaluation results
- **BaseJudge**: An abstract base class for building LLM judges
- **Dual invocation modes**: Anthropic SDK (preferred) or Claude CLI (fallback)
- **Dual evaluation modes**: LLM-based or heuristic-only evaluation
- **Evidence collection patterns**: Standardized methods for loading analysis results and ground truth

## Installation

```python
# From tool-specific judges
from shared.evaluation import BaseJudge, JudgeResult

# Or import directly
from shared.evaluation.base_judge import BaseJudge, JudgeResult
```

## JudgeResult Dataclass

`JudgeResult` is the standardized output format for all judge evaluations.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `dimension` | `str` | Name of the evaluation dimension (e.g., "accuracy", "coverage") |
| `score` | `int` | Numeric score from 1-5 (1=poor, 5=excellent) |
| `confidence` | `float` | Confidence level from 0.0-1.0 |
| `reasoning` | `str` | Explanation of the score |
| `evidence_cited` | `list[str]` | List of evidence points used in evaluation (default: []) |
| `recommendations` | `list[str]` | List of improvement recommendations (default: []) |
| `sub_scores` | `dict[str, int]` | Dictionary of sub-dimension scores (default: {}) |
| `raw_response` | `str` | The raw LLM response text (default: "") |

### Methods

#### `to_dict() -> dict[str, Any]`

Convert the result to a dictionary for JSON serialization.

```python
result = JudgeResult(
    dimension="accuracy",
    score=4,
    confidence=0.85,
    reasoning="Good detection rate"
)
data = result.to_dict()
# {'dimension': 'accuracy', 'score': 4, 'confidence': 0.85, ...}
```

#### `from_dict(data: dict) -> JudgeResult`

Create a JudgeResult from a dictionary. Handles missing fields gracefully.

```python
data = {"score": 4, "reasoning": "Good"}
result = JudgeResult.from_dict(data)
# result.dimension == "unknown" (default for missing field)
```

#### `is_passing(threshold: int = 3) -> bool`

Check if the score meets the passing threshold.

```python
result = JudgeResult(dimension="test", score=4, confidence=0.8, reasoning="")
result.is_passing()           # True (default threshold=3)
result.is_passing(threshold=5)  # False
```

### Usage Example

```python
from shared.evaluation import JudgeResult
import json

# Create a result
result = JudgeResult(
    dimension="vulnerability_accuracy",
    score=4,
    confidence=0.85,
    reasoning="Detected 8/10 known CVEs with accurate severity classification",
    evidence_cited=["CVE-2023-1234 detected", "CVE-2023-5678 detected"],
    recommendations=["Improve detection for low-severity CVEs"],
    sub_scores={"cve_detection": 4, "severity_accuracy": 5},
)

# Serialize to JSON
json_str = json.dumps(result.to_dict(), indent=2)

# Deserialize from JSON
restored = JudgeResult.from_dict(json.loads(json_str))
```

## BaseJudge Abstract Class

`BaseJudge` is the foundation for all LLM judges in the evaluation framework.

### Abstract Methods (Must Implement)

#### `dimension_name` (property)

Returns the name of the evaluation dimension.

```python
@property
def dimension_name(self) -> str:
    return "vulnerability_accuracy"
```

#### `weight` (property)

Returns the weight of this dimension in overall scoring (0.0-1.0).

```python
@property
def weight(self) -> float:
    return 0.35  # 35% of overall score
```

#### `collect_evidence() -> dict[str, Any]`

Gather evidence files and data for evaluation. The returned dictionary is JSON-serialized and injected into the prompt template.

```python
def collect_evidence(self) -> dict[str, Any]:
    results = self.load_analysis_results()
    ground_truth = self.load_ground_truth()
    return {
        "analysis": results,
        "expected": ground_truth,
        "statistics": {...},
    }
```

### Optional Override Methods

#### `get_default_prompt() -> str`

Return a default prompt template if no prompt file exists. The template should include `{{ evidence }}` placeholder.

```python
def get_default_prompt(self) -> str:
    return """# Vulnerability Accuracy Evaluation

Evaluate the following evidence for CVE detection accuracy.

## Evidence
{{ evidence }}

## Response Format
Respond with ONLY a JSON object:
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>",
  "evidence_cited": ["<evidence points>"],
  "recommendations": ["<improvements>"],
  "sub_scores": {}
}
"""
```

#### `run_heuristic_evaluation(evidence: dict) -> JudgeResult`

Provide heuristic-based evaluation without LLM. Used when `use_llm=False`.

```python
def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
    detection_rate = evidence["summary"]["detection_rate"]
    if detection_rate >= 90:
        score = 5
    elif detection_rate >= 70:
        score = 4
    elif detection_rate >= 50:
        score = 3
    else:
        score = 2

    return JudgeResult(
        dimension=self.dimension_name,
        score=score,
        confidence=0.9,
        reasoning=f"Detection rate: {detection_rate}%",
    )
```

#### `run_ground_truth_assertions() -> tuple[bool, list[str]]`

Run pre-evaluation validation checks against ground truth.

```python
def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
    failures = []
    evidence = self.collect_evidence()

    if evidence["summary"]["detection_rate"] < 50:
        failures.append("Detection rate below 50%")

    return len(failures) == 0, failures
```

### Concrete Methods (Provided by BaseJudge)

| Method | Description |
|--------|-------------|
| `validate_claude_cli()` | Check if Claude CLI is available and executable |
| `load_prompt_template()` | Load prompt from file or use default |
| `load_analysis_results()` | Load all JSON files from output_dir |
| `load_ground_truth()` | Load all ground truth files |
| `extract_files(analysis)` | Extract files list (handles both formats) |
| `extract_summary(analysis)` | Extract summary dict (handles both formats) |
| `build_prompt(evidence)` | Build complete prompt with evidence |
| `parse_response(response)` | Parse LLM response into JudgeResult |
| `invoke_claude(prompt)` | Invoke Claude (SDK preferred, CLI fallback) |
| `evaluate()` | Run the full evaluation pipeline |
| `get_prompt(data)` | Legacy interface (deprecated, use build_prompt) |

### Constructor Parameters

```python
judge = MyJudge(
    model="sonnet",           # Model name or API ID
    timeout=120,              # Timeout in seconds for LLM invocation
    working_dir=Path.cwd(),   # Working directory
    output_dir=None,          # Directory containing analysis output files
    ground_truth_dir=None,    # Directory containing ground truth files
    use_llm=True,             # Whether to use LLM (False for heuristic-only)
)
```

### Model Mapping

The `model` parameter accepts short names that map to API model IDs:

| Short Name | API Model ID |
|------------|--------------|
| `sonnet` | `claude-sonnet-4-20250514` |
| `opus` | `claude-opus-4-20250514` |
| `haiku` | `claude-haiku-4-20250514` |

You can also pass the full API model ID directly.

## Creating a New Judge

### Step-by-Step Guide

1. **Create the judge file** in your tool's `evaluation/llm/judges/` directory
2. **Import the base class** from shared evaluation
3. **Define the class** inheriting from BaseJudge
4. **Implement required abstract methods**
5. **Optionally override** heuristic evaluation and ground truth assertions
6. **Create a prompt template** (optional, can use default)

### Complete Example

```python
"""Vulnerability accuracy judge for Trivy evaluation."""

from pathlib import Path
from typing import Any

from shared.evaluation import BaseJudge, JudgeResult


class VulnerabilityAccuracyJudge(BaseJudge):
    """Judge for evaluating vulnerability identification accuracy."""

    @property
    def dimension_name(self) -> str:
        return "vulnerability_accuracy"

    @property
    def weight(self) -> float:
        return 0.35  # 35% of overall score

    @property
    def prompt_file(self) -> Path:
        """Custom prompt location."""
        return Path(__file__).parent.parent / "prompts" / "vulnerability_accuracy.md"

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence about vulnerability accuracy."""
        results = self.load_analysis_results()
        ground_truth = self.load_ground_truth()

        evidence = {
            "summary": {
                "repos_analyzed": len(results),
                "total_expected_cves": 0,
                "total_detected_cves": 0,
            },
            "per_repo_accuracy": [],
            "missed_cves": [],
        }

        for repo_name, data in results.items():
            vulns = data.get("vulnerabilities", [])
            detected_cve_ids = {v.get("id", "") for v in vulns}

            gt = ground_truth.get(repo_name)
            if not gt:
                continue

            known_cves = gt.get("known_cves", [])
            for cve_id in known_cves:
                evidence["summary"]["total_expected_cves"] += 1
                if cve_id in detected_cve_ids:
                    evidence["summary"]["total_detected_cves"] += 1
                else:
                    evidence["missed_cves"].append({
                        "repo": repo_name,
                        "cve_id": cve_id,
                    })

        return evidence

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Heuristic evaluation without LLM."""
        total_expected = evidence["summary"]["total_expected_cves"]
        total_detected = evidence["summary"]["total_detected_cves"]

        if total_expected == 0:
            score = 3
            detection_rate = 100.0
        else:
            detection_rate = total_detected / total_expected * 100
            if detection_rate >= 90:
                score = 5
            elif detection_rate >= 70:
                score = 4
            elif detection_rate >= 50:
                score = 3
            else:
                score = 2

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.9,
            reasoning=f"CVE detection rate: {detection_rate:.1f}%",
            evidence_cited=[f"Detected {total_detected}/{total_expected} CVEs"],
        )

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Pre-evaluation validation."""
        failures = []
        evidence = self.collect_evidence()

        total = evidence["summary"]["total_expected_cves"]
        detected = evidence["summary"]["total_detected_cves"]

        if total > 0 and (detected / total) < 0.5:
            failures.append(f"Detection rate below 50%: {detected}/{total}")

        return len(failures) == 0, failures
```

## SDK vs CLI Invocation Modes

The framework supports two methods for invoking Claude:

### Anthropic SDK (Preferred)

When the `anthropic` package is installed and `ANTHROPIC_API_KEY` is set:

```python
# Automatic SDK usage
judge = MyJudge(model="sonnet")
result = judge.evaluate()  # Uses SDK internally
```

The SDK method (`_invoke_via_sdk`) is preferred because:
- Direct API access with better error handling
- No subprocess overhead
- Cleaner authentication via environment variable

### Claude CLI (Fallback)

If SDK is unavailable, falls back to Claude Code CLI:

```bash
claude -p "<prompt>" --model sonnet --output-format text --allowedTools "" --max-turns 5
```

The CLI method (`_invoke_via_cli`) is used when:
- `anthropic` package is not installed
- `ANTHROPIC_API_KEY` environment variable is not set

### Checking CLI Availability

```python
is_valid, message = BaseJudge.validate_claude_cli()
if is_valid:
    print(f"Claude CLI found at: {message}")
else:
    print(f"CLI unavailable: {message}")
```

## Heuristic vs LLM Evaluation Modes

### LLM Evaluation (Default)

```python
judge = MyJudge(use_llm=True)  # Default
result = judge.evaluate()
# Collects evidence -> Builds prompt -> Invokes Claude -> Parses response
```

### Heuristic-Only Evaluation

```python
judge = MyJudge(use_llm=False)
result = judge.evaluate()
# Collects evidence -> Calls run_heuristic_evaluation() -> Returns result
```

Heuristic mode is useful for:
- Fast iteration during development
- CI/CD pipelines without LLM access
- Baseline comparisons
- Cost reduction in high-volume scenarios

## Evidence Collection Patterns

### Loading Analysis Results

```python
def collect_evidence(self) -> dict[str, Any]:
    # Load all JSON files from output_dir
    results = self.load_analysis_results()
    # Returns: {"repo_name": {analysis_data}, ...}

    for repo_name, data in results.items():
        # Handle both envelope formats
        files = self.extract_files(data)      # data["results"]["files"] or data["files"]
        summary = self.extract_summary(data)  # data["results"]["summary"] or data["summary"]
```

### Loading Ground Truth

```python
def collect_evidence(self) -> dict[str, Any]:
    # Load all JSON files from ground_truth_dir
    ground_truth = self.load_ground_truth()
    # Returns: {"repo_name": {ground_truth_data}, ...}
    # Keys from "id" field in JSON if present, otherwise filename stem
```

### Standard Evidence Structure

```python
evidence = {
    "summary": {
        "repos_analyzed": 5,
        "total_findings": 42,
        "detection_rate": 85.0,
    },
    "per_repo_details": [...],
    "matches": [...],
    "misses": [...],
    "ground_truth_assertions": {
        "passed": True,
        "failures": [],
    },
}
```

## Response Parsing

The `parse_response()` method handles various LLM response formats:

### JSON Response (Preferred)

```
Here is my evaluation:
{
    "score": 4,
    "confidence": 0.85,
    "reasoning": "Good coverage",
    "evidence_cited": ["File A"],
    "recommendations": ["Add tests"]
}
```

The method extracts JSON from anywhere in the response text.

### Text Fallback

If JSON parsing fails, the method searches for score patterns:

```
Based on my analysis, I give a score: 4 for this dimension.
```

Extracts `score: N` or `score:N` patterns. Defaults to score=3 if no pattern found.

### Handling Malformed Responses

```python
response = ""  # Empty response
result = judge.parse_response(response)
# result.score = 3 (default)
# result.reasoning = "No response received"
# result.confidence = 0.5 (low confidence fallback)
```

## Integration with Tool-Specific Evaluation Pipelines

### Directory Structure

```
src/tools/trivy/
    evaluation/
        llm/
            judges/
                __init__.py
                base.py           # Re-exports from shared
                vulnerability_accuracy.py
                severity_accuracy.py
            prompts/
                vulnerability_accuracy.md
                severity_accuracy.md
            results/
        ground-truth/
            vulnerable-npm.json
            iac-terraform.json
```

### Tool-Specific Base Module

Create a `base.py` that re-exports from shared for cleaner imports:

```python
# src/tools/trivy/evaluation/llm/judges/base.py
"""Re-export shared base classes for local imports."""
from shared.evaluation import BaseJudge, JudgeResult

__all__ = ["BaseJudge", "JudgeResult"]
```

### Evaluation Script Integration

```python
# src/tools/trivy/scripts/llm_evaluate.py
from pathlib import Path
from evaluation.llm.judges.vulnerability_accuracy import VulnerabilityAccuracyJudge
from evaluation.llm.judges.severity_accuracy import SeverityAccuracyJudge

JUDGES = [
    VulnerabilityAccuracyJudge,
    SeverityAccuracyJudge,
]

def run_evaluation(
    output_dir: Path,
    ground_truth_dir: Path,
    model: str = "sonnet",
    use_llm: bool = True,
) -> dict:
    results = []
    weighted_score = 0.0
    total_weight = 0.0

    for JudgeClass in JUDGES:
        judge = JudgeClass(
            model=model,
            output_dir=output_dir,
            ground_truth_dir=ground_truth_dir,
            use_llm=use_llm,
        )
        result = judge.evaluate()
        results.append(result.to_dict())
        weighted_score += result.score * judge.weight
        total_weight += judge.weight

    return {
        "overall_score": round(weighted_score / total_weight, 2) if total_weight > 0 else 0,
        "dimensions": results,
    }
```

### Running Evaluations

```bash
# With LLM evaluation
python scripts/llm_evaluate.py --model sonnet

# Heuristic only (fast, no LLM)
python scripts/llm_evaluate.py --heuristic

# Custom directories
python scripts/llm_evaluate.py \
    --output-dir ./output/runs \
    --ground-truth-dir ./evaluation/ground-truth
```

## Testing Judges

See `/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/shared/evaluation/tests/test_base_judge.py` for comprehensive test examples covering:

- JudgeResult serialization and deserialization
- CLI validation
- Prompt building and loading
- Response parsing (JSON, text fallback, malformed)
- Claude invocation (SDK and CLI, mocked)
- Heuristic evaluation fallback
- Data loading (analysis results, ground truth)
- Full evaluation pipeline

### Running Tests

```bash
cd src/shared/evaluation
pytest tests/ -v
```

## Best Practices

1. **Always define meaningful weights** that sum to 1.0 across all judges for a tool
2. **Collect comprehensive evidence** including both positive and negative signals
3. **Implement heuristic evaluation** for fast iteration and CI/CD
4. **Use ground truth assertions** to catch obvious failures before LLM invocation
5. **Cap scores on assertion failures** to prevent false positives
6. **Include raw_response** for debugging and audit trails
7. **Test with mocked LLM responses** to ensure robust parsing
