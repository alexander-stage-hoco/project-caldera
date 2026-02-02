# Shared Utilities

Common infrastructure used across Project Caldera tools.

## Modules

### evaluation/

LLM judge infrastructure with observability integration.

**Key exports:**

```python
from shared.evaluation import (
    # Core classes
    BaseJudge,      # Abstract base class for LLM judges
    JudgeResult,    # Evaluation result dataclass

    # Observability enforcement
    require_observability,       # Raise if observability disabled
    verify_interactions_logged,  # Check interactions were logged
    get_observability_summary,   # Get trace summary
    get_recent_interactions,     # Query recent interactions
    is_observability_enabled,    # Check if enabled
    ObservabilityDisabledError,  # Exception type
)
```

**Usage:**

```python
from shared.evaluation import BaseJudge, JudgeResult

class MyJudge(BaseJudge):
    @property
    def dimension_name(self) -> str:
        return "my_dimension"

    @property
    def weight(self) -> float:
        return 0.25

    def collect_evidence(self) -> dict:
        return {"key": "value"}

    def get_default_prompt(self) -> str:
        return "Evaluate {{ evidence }}"
```

See `docs/SHARED_EVALUATION.md` for complete documentation.

## Adding New Shared Modules

When adding new shared infrastructure:

1. Create a subdirectory under `src/shared/`
2. Add `__init__.py` with public exports
3. Document in this README
4. Create dedicated documentation in `docs/`
