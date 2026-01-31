"""LLM-as-a-Judge evaluation framework for Layout Scanner.

This module provides LLM-based qualitative evaluation of layout scanner outputs,
complementing the programmatic checks with semantic understanding.
"""

from .orchestrator import LLMEvaluator

__all__ = ["LLMEvaluator"]
