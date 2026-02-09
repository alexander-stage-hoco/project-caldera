"""Pytest configuration and fixtures for coverage-ingest tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_lcov_content() -> str:
    """Sample LCOV format coverage data."""
    return """TN:test
SF:src/main.py
FN:1,main
FNDA:5,main
FNF:1
FNH:1
DA:1,5
DA:2,5
DA:3,0
DA:4,5
LF:4
LH:3
BRF:2
BRH:1
end_of_record
SF:src/utils.py
DA:1,10
DA:2,10
LF:2
LH:2
end_of_record
"""


@pytest.fixture
def sample_cobertura_content() -> str:
    """Sample Cobertura XML format coverage data."""
    return """<?xml version="1.0" ?>
<coverage line-rate="0.75" branch-rate="0.5" version="5.5">
    <packages>
        <package name="src">
            <classes>
                <class name="main.py" filename="src/main.py" line-rate="0.75" branch-rate="0.5">
                    <lines>
                        <line number="1" hits="5"/>
                        <line number="2" hits="5"/>
                        <line number="3" hits="0"/>
                        <line number="4" hits="5"/>
                    </lines>
                </class>
                <class name="utils.py" filename="src/utils.py" line-rate="1.0">
                    <lines>
                        <line number="1" hits="10"/>
                        <line number="2" hits="10"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>
"""


@pytest.fixture
def sample_jacoco_content() -> str:
    """Sample JaCoCo XML format coverage data."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<report name="MyProject">
    <package name="com/example">
        <sourcefile name="Main.java">
            <counter type="INSTRUCTION" missed="10" covered="90"/>
            <counter type="LINE" missed="2" covered="8"/>
            <counter type="BRANCH" missed="1" covered="3"/>
        </sourcefile>
        <sourcefile name="Utils.java">
            <counter type="INSTRUCTION" missed="0" covered="50"/>
            <counter type="LINE" missed="0" covered="5"/>
        </sourcefile>
    </package>
</report>
"""


@pytest.fixture
def sample_istanbul_content() -> str:
    """Sample Istanbul JSON format coverage data."""
    return """{
  "src/main.js": {
    "path": "src/main.js",
    "statementMap": {
      "0": {"start": {"line": 1}, "end": {"line": 1}},
      "1": {"start": {"line": 2}, "end": {"line": 2}},
      "2": {"start": {"line": 3}, "end": {"line": 3}},
      "3": {"start": {"line": 4}, "end": {"line": 4}}
    },
    "s": {"0": 5, "1": 5, "2": 0, "3": 5},
    "branchMap": {
      "0": {"type": "if", "locations": [{"start": {"line": 2}}, {"start": {"line": 2}}]}
    },
    "b": {"0": [3, 2]}
  },
  "src/utils.js": {
    "path": "src/utils.js",
    "statementMap": {
      "0": {"start": {"line": 1}, "end": {"line": 1}},
      "1": {"start": {"line": 2}, "end": {"line": 2}}
    },
    "s": {"0": 10, "1": 10},
    "b": {}
  }
}
"""
