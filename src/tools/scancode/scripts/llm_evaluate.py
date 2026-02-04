#!/usr/bin/env python3
"""CLI wrapper for running scancode LLM evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.llm import orchestrator


if __name__ == "__main__":
    orchestrator.main()
