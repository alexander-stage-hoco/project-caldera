# LLM Evaluation Infrastructure

This document describes the shared LLM evaluation infrastructure in Project Caldera, including the BaseJudge class and observability system.

---

## Overview

The shared evaluation module (`src/shared/evaluation/`) provides:

- **BaseJudge**: Abstract base class for all LLM judges
- **JudgeResult**: Standardized evaluation result dataclass
- **Observability**: Automatic logging of all LLM interactions
- **SDK/CLI usage**: Claude Code CLI by default; Anthropic SDK only with `USE_ANTHROPIC_SDK=1`

### Why Shared Infrastructure?

1. **Consistency**: All judges behave the same way (response parsing, error handling)
2. **Observability**: Automatic logging without per-tool implementation
3. **Maintainability**: Bug fixes and improvements apply to all tools
4. **Compliance**: CI checks enforce shared module usage

---

## Module Exports

```python
from shared.evaluation import (
    # Core classes
    BaseJudge,
    JudgeResult,

    # Observability enforcement
    ObservabilityDisabledError,
    is_observability_enabled,
    require_observability,
    verify_interactions_logged,
    get_observability_summary,
    get_recent_interactions,

    # Feature flag
    HAS_OBSERVABILITY,
)
```

---

## BaseJudge Interface

### Abstract Properties (Required)

| Property | Type | Description |
|----------|------|-------------|
| `dimension_name` | `str` | Name of evaluation dimension (e.g., "accuracy") |
| `weight` | `float` | Weight in overall score (0.0-1.0) |

### Abstract Methods (Required)

| Method | Signature | Description |
|--------|-----------|-------------|
| `collect_evidence()` | `() -> dict[str, Any]` | Gather evidence for evaluation |
| `get_default_prompt()` | `() -> str` | Return default prompt if file doesn't exist |

### Constructor Parameters

```python
BaseJudge(
    model: str = "opus-4.5",              # "opus-4.5", "sonnet", "opus", "haiku", or full API ID
    timeout: int = 120,                  # Timeout in seconds
    working_dir: Path | None = None,     # Working directory (default: cwd)
    output_dir: Path | None = None,      # Analysis output directory
    ground_truth_dir: Path | None = None,# Ground truth files directory
    use_llm: bool = True,                # False for heuristic-only evaluation
    trace_id: str | None = None,         # Correlation ID for observability
    enable_observability: bool = True,   # Log LLM interactions
)
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `evaluate()` | Run full evaluation pipeline |
| `invoke_claude(prompt)` | Invoke Claude with automatic observability |
| `build_prompt(evidence)` | Build prompt from template with evidence |
| `parse_response(response)` | Parse LLM response into JudgeResult |
| `load_prompt_template()` | Load prompt from file or get_default_prompt() |
| `load_analysis_results()` | Load all JSON files from output_dir |
| `load_ground_truth()` | Load all JSON files from ground_truth_dir |
| `run_heuristic_evaluation(evidence)` | Override for non-LLM evaluation |

---

## JudgeResult Dataclass

```python
@dataclass
class JudgeResult:
    dimension: str           # Evaluation dimension name
    score: int               # Score from 1-5 (1=poor, 5=excellent)
    confidence: float        # Confidence level (0.0-1.0)
    reasoning: str           # Explanation of the score
    evidence_cited: list[str]    # Evidence points used
    recommendations: list[str]   # Improvement suggestions
    sub_scores: dict[str, int]   # Sub-dimension scores
    raw_response: str        # Raw LLM response text
```

### Methods

```python
result.to_dict()              # Convert to dictionary for JSON
result.is_passing(threshold)  # Check if score >= threshold (default: 3)

JudgeResult.from_dict(data)   # Create from dictionary
```

---

## Creating Tool Judges

### Step 1: Create Tool-Specific Base Class

Most tools create a local `base.py` that extends the shared BaseJudge:

```python
# src/tools/my-tool/evaluation/llm/judges/base.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult


class BaseJudge(SharedBaseJudge):
    """Tool-specific extensions for my-tool judges."""

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        ground_truth_dir: Path | None = None,
        use_llm: bool = True,
        trace_id: str | None = None,
        enable_observability: bool = True,
    ):
        # Set tool-specific defaults
        working_dir = working_dir or Path(__file__).resolve().parents[4]
        output_dir = output_dir or working_dir / "output" / "runs"
        ground_truth_dir = ground_truth_dir or working_dir / "evaluation" / "ground-truth"

        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            ground_truth_dir=ground_truth_dir,
            use_llm=use_llm,
            trace_id=trace_id,
            enable_observability=enable_observability,
        )

    @property
    def prompt_file(self) -> Path:
        """Override prompt file location for this tool."""
        return self.working_dir / "evaluation" / "llm" / "prompts" / f"{self.dimension_name}.md"
```

### Step 2: Create Dimension Judge

```python
# src/tools/my-tool/evaluation/llm/judges/accuracy.py
from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class AccuracyJudge(BaseJudge):
    """Evaluate accuracy of my-tool output against ground truth."""

    @property
    def dimension_name(self) -> str:
        return "accuracy"

    @property
    def weight(self) -> float:
        return 0.35

    def collect_evidence(self) -> dict[str, Any]:
        """Gather evidence for accuracy evaluation."""
        analysis_results = self.load_analysis_results()
        ground_truth = self.load_ground_truth()

        evidence = {
            "analysis_results": {},
            "ground_truth": {},
            "comparisons": [],
        }

        for repo_name, analysis in analysis_results.items():
            if repo_name in ground_truth:
                gt = ground_truth[repo_name]
                evidence["analysis_results"][repo_name] = analysis
                evidence["ground_truth"][repo_name] = gt
                evidence["comparisons"].append({
                    "repo": repo_name,
                    "expected_count": gt.get("expected_count", 0),
                    "actual_count": len(self.extract_files(analysis)),
                })

        return evidence

    def get_default_prompt(self) -> str:
        return """# Accuracy Evaluation

Evaluate the accuracy of my-tool output against the ground truth.

## Evidence

{{ evidence }}

## Scoring Rubric

- **5 (Excellent)**: 95%+ accuracy, all critical items detected
- **4 (Good)**: 85-94% accuracy, most items detected
- **3 (Acceptable)**: 70-84% accuracy, key items detected
- **2 (Poor)**: 50-69% accuracy, significant gaps
- **1 (Failing)**: <50% accuracy, major issues missed

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

### Step 3: Create Orchestrator

```python
# src/tools/my-tool/evaluation/llm/orchestrator.py
from __future__ import annotations

import uuid
from pathlib import Path

from shared.evaluation import require_observability

from .judges.accuracy import AccuracyJudge
from .judges.actionability import ActionabilityJudge
from .judges.false_positive_rate import FalsePositiveRateJudge
from .judges.integration_fit import IntegrationFitJudge


def run_llm_evaluation(
    output_path: Path,
    ground_truth_dir: Path,
    model: str = "opus-4.5",
) -> dict:
    """Run LLM evaluation for my-tool."""
    # IMPORTANT: Enforce observability at the start
    require_observability()

    # Generate shared trace ID for all judges
    trace_id = str(uuid.uuid4())

    # Initialize judges with shared trace
    judges = [
        AccuracyJudge(
            output_dir=output_path.parent,
            ground_truth_dir=ground_truth_dir,
            model=model,
            trace_id=trace_id,
        ),
        ActionabilityJudge(...),
        FalsePositiveRateJudge(...),
        IntegrationFitJudge(...),
    ]

    results = {}
    for judge in judges:
        result = judge.evaluate()
        results[result.dimension] = result.to_dict()

    # Calculate overall score
    total_weight = sum(j.weight for j in judges)
    weighted_score = sum(
        results[j.dimension_name]["score"] * j.weight
        for j in judges
    ) / total_weight

    return {
        "trace_id": trace_id,
        "overall_score": round(weighted_score, 2),
        "dimensions": results,
    }
```

---

## Required LLM Judges (4 minimum)

All tools must have at least 4 LLM judges:

| Judge | Purpose |
|-------|---------|
| `accuracy.py` or equivalent | Validates findings match expected |
| `actionability.py` | Assesses if findings are useful |
| `false_positive_rate.py` or equivalent | Evaluates false positive assessment |
| `integration_fit.py` | Validates SoT schema compatibility |

---

## Prompt Templates

Prompts are loaded from files with `{{ evidence }}` placeholder:

```markdown
# Accuracy Evaluation

Evaluate the accuracy of the analysis output.

## Evidence

{{ evidence }}

## Scoring Rubric

- **5 (Excellent)**: 95%+ accuracy
- **4 (Good)**: 85-94% accuracy
- **3 (Acceptable)**: 70-84% accuracy
- **2 (Poor)**: 50-69% accuracy
- **1 (Failing)**: <50% accuracy

## Response Format

Respond with ONLY a JSON object:
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>",
  "evidence_cited": ["<points>"],
  "recommendations": ["<improvements>"],
  "sub_scores": {}
}
```

### Prompt File Location

Default: `{working_dir}/evaluation/llm/prompts/{dimension_name}.md`

Override by implementing the `prompt_file` property in your base class.

If the prompt file doesn't exist, `get_default_prompt()` is called.

---

## Heuristic Evaluation

For testing or fallback, judges can provide heuristic evaluation without LLM:

```python
class AccuracyJudge(BaseJudge):
    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Compute accuracy without LLM."""
        comparisons = evidence.get("comparisons", [])

        if not comparisons:
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.8,
                reasoning="No data to evaluate",
            )

        # Calculate accuracy percentage
        total_expected = sum(c["expected_count"] for c in comparisons)
        total_actual = sum(c["actual_count"] for c in comparisons)

        if total_expected == 0:
            accuracy = 1.0 if total_actual == 0 else 0.0
        else:
            accuracy = min(total_actual / total_expected, 1.0)

        # Map to score
        score = int(accuracy * 4) + 1  # 1-5 scale

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.9,
            reasoning=f"Heuristic accuracy: {accuracy:.1%}",
        )

# Usage
judge = AccuracyJudge(use_llm=False)
result = judge.evaluate()  # Uses heuristic
```

---

## Model Selection

The BaseJudge supports three model shortcuts:

| Shortcut | API Model ID |
|----------|-------------|
| `sonnet` | `claude-sonnet-4-20250514` |
| `opus` | `claude-opus-4-20250514` |
| `opus-4.5` | `claude-opus-4-5-20250514` |
| `haiku` | `claude-haiku-4-20250514` |

Or pass the full API model ID directly:

```python
judge = AccuracyJudge(model="claude-opus-4-5-20250514")
```

---

## Observability

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Tool Judges                           │
│  AccuracyJudge │ CoverageJudge │ ActionabilityJudge │ ...   │
└────────────────────────────────┬────────────────────────────┘
                                 │ inherit from
┌────────────────────────────────▼────────────────────────────┐
│                shared.evaluation.BaseJudge                   │
│  - invoke_claude() wraps all LLM calls                      │
│  - Automatic observability logging                          │
└────────────────────────────────┬────────────────────────────┘
                                 │ logs to
┌────────────────────────────────▼────────────────────────────┐
│           insights.evaluation.llm.observability              │
│  LLMLogger (singleton) → FileStore (JSONL)                  │
└─────────────────────────────────────────────────────────────┘
```

### What's Captured

- Full prompts and responses
- Timing information (latency, duration)
- Status (success, error, timeout)
- Trace correlation across related judges
- Parsed results (scores, reasoning)

### Configuration

All configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_OBSERVABILITY_ENABLED` | `true` | Master switch |
| `LLM_OBSERVABILITY_LOG_DIR` | `output/llm_logs` | Log directory |
| `LLM_OBSERVABILITY_CONSOLE` | `false` | Also log to console |
| `LLM_OBSERVABILITY_INCLUDE_PROMPTS` | `true` | Include full prompts |
| `LLM_OBSERVABILITY_INCLUDE_RESPONSES` | `true` | Include full responses |
| `LLM_OBSERVABILITY_RETENTION_DAYS` | `30` | Auto-cleanup (0 = no cleanup) |

### Disabling for Local Testing

```bash
export LLM_OBSERVABILITY_ENABLED=false
```

Or programmatically:
```python
from insights.evaluation.llm.observability import set_config, ObservabilityConfig
set_config(ObservabilityConfig(enabled=False))
```

### Trace Correlation

Each evaluation run generates a unique `trace_id` linking all judge interactions:

```python
trace_id = str(uuid.uuid4())

accuracy_judge = AccuracyJudge(trace_id=trace_id)
coverage_judge = CoverageJudge(trace_id=trace_id)

# Later, query all interactions for this evaluation
from insights.evaluation.llm.observability import FileStore
store = FileStore()
interactions = store.query_by_trace(trace_id)
```

### Storage Format

Interactions stored in JSON-Lines files organized by date:

```
output/llm_logs/
├── 2025-01-30/
│   └── interactions.jsonl
├── 2025-01-31/
│   └── interactions.jsonl
└── ...
```

Each line is a complete JSON object:

```json
{
  "interaction_id": "uuid",
  "trace_id": "uuid",
  "timestamp_start": "2025-01-30T10:00:00.000Z",
  "timestamp_end": "2025-01-30T10:00:05.123Z",
  "duration_ms": 5123,
  "provider_name": "anthropic_sdk",
  "judge_name": "accuracy",
  "model": "claude-opus-4-5-20250514",
  "user_prompt": "...",
  "response_content": "...",
  "status": "success",
  "parsed_score": 4,
  "parsed_reasoning": "..."
}
```

### Query API

```python
from insights.evaluation.llm.observability import FileStore
from datetime import datetime

store = FileStore()

# Read all interactions for today
interactions = store.read_date()

# Read for specific date
interactions = store.read_date(datetime(2025, 1, 30))

# Query by trace ID
interactions = store.query_by_trace("trace-uuid")

# Query by judge name
accuracy_interactions = store.query_by_judge("accuracy")

# Query by status
errors = store.query_by_status("error")

# Get statistics
stats = store.get_stats()
# Returns: {"total_count": 10, "success_count": 9, "error_count": 1, ...}

# Build evaluation span from trace
span = store.get_evaluation_span("trace-uuid")
```

### Enforcement

The `require_observability()` function enforces that observability is enabled:

```python
from shared.evaluation import require_observability

def run_llm_evaluation(output_path: Path, ...) -> dict:
    require_observability()  # Raises ObservabilityDisabledError if disabled
    # ... rest of evaluation logic ...
```

If disabled, raises:
```
ObservabilityDisabledError: LLM observability is required but disabled.
Set LLM_OBSERVABILITY_ENABLED=true or remove the environment variable.
```

### Validation Functions

```python
from shared.evaluation import (
    is_observability_enabled,
    verify_interactions_logged,
    get_observability_summary,
    get_recent_interactions,
)

# Check if enabled
if is_observability_enabled():
    print("Observability is active")

# Verify interactions were logged for a trace
if verify_interactions_logged(trace_id, min_count=4):
    print("All 4 judges logged successfully")

# Get summary for a trace
summary = get_observability_summary(trace_id)
# Returns: {"interaction_count": 4, "success_count": 4, ...}

# Get recent interactions (for debugging)
recent = get_recent_interactions(hours=24, judge_name="accuracy")
```

---

## CI Compliance Script

The `scripts/check_observability_compliance.py` script verifies proper usage:

```bash
python scripts/check_observability_compliance.py
python scripts/check_observability_compliance.py --verbose
```

### Checks Performed

1. **Direct Anthropic SDK calls**: No `messages.create()` outside shared module
2. **Direct Claude CLI calls**: No `subprocess.run(["claude"...])` outside shared module
3. **Tool base.py imports**: All judges import from `shared.evaluation`
4. **Orchestrator enforcement**: All orchestrators call `require_observability()`

### Exit Codes

- `0` = All checks pass
- `1` = Violations found

---

## References

- [TOOL_INTEGRATION_CHECKLIST.md](./TOOL_INTEGRATION_CHECKLIST.md) - Tool creation and integration
- [COMPLIANCE.md](./COMPLIANCE.md) - Compliance requirements
- `src/shared/evaluation/` - Shared module source
- `src/shared/README.md` - Module overview
- `src/insights/evaluation/llm/observability/` - Observability module
