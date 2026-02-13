"""LLM Evaluation Orchestrator for PMD CPD.

This module provides the orchestrator interface for the LLM evaluation framework.
It wraps the existing llm_evaluate.py functionality to provide a consistent
interface with other tools in the Project Vulcan ecosystem.
"""

from __future__ import annotations

import sys
from pathlib import Path

from shared.evaluation import require_observability

# Add scripts directory to path for imports
_scripts_dir = Path(__file__).parent.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from llm_evaluate import run_llm_evaluation, print_report, main

__all__ = ["run_llm_evaluation", "print_report", "main"]

if __name__ == "__main__":
    require_observability()
    main()
