"""Tool requirements checks for Caldera."""

from __future__ import annotations

import pytest
from pathlib import Path

pytest.skip(
    "Tool compliance checks moved to src/tool-compliance/tool_compliance.py",
    allow_module_level=True,
)
