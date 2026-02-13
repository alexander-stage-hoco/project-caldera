#!/usr/bin/env python3
"""
LLM Evaluation Script for Roslyn Analyzers PoC.

This script wraps the LLM evaluation orchestrator for CLI usage.

Usage:
    python scripts/llm_evaluate.py \
        --analysis output/runs/roslyn_analysis.json \
        --output output/runs/llm_evaluation.json \
        --model opus-4.5
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path so that evaluation.llm imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.llm.orchestrator import main

if __name__ == "__main__":
    main()
