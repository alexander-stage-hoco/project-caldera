"""LLM-as-a-Judge evaluation system for scc PoC.

This package provides qualitative evaluation of scc outputs using Claude Code
in headless mode with specialized judge agents.
"""

from .orchestrator import LLMEvaluator, EvaluationResult, DimensionResult

__all__ = ["LLMEvaluator", "EvaluationResult", "DimensionResult"]
