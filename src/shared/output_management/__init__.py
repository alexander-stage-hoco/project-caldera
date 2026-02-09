"""Output management utilities for tool analysis results.

This module provides shared utilities for handling tool output envelopes
and loading analysis results, reducing duplication across tool judges.

Usage:
    from shared.output_management import unwrap_envelope, load_analysis_results
"""

from __future__ import annotations

from .envelope import unwrap_envelope, wrap_envelope
from .loader import load_analysis_results, load_ground_truth, load_all_outputs

__all__ = [
    "unwrap_envelope",
    "wrap_envelope",
    "load_analysis_results",
    "load_ground_truth",
    "load_all_outputs",
]
