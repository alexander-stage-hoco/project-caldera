"""Pytest fixtures for symbol-scanner tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def simple_function_code():
    """Simple Python code with functions."""
    return '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def main():
    print(hello("World"))
    result = add(1, 2)
    print(result)
'''


@pytest.fixture
def class_code():
    """Python code with classes and methods."""
    return '''
class Calculator:
    """A simple calculator class."""

    def __init__(self):
        """Initialize calculator."""
        self.result = 0

    def add(self, x: int, y: int) -> int:
        """Add two numbers."""
        self.result = x + y
        return self.result

    def _internal(self):
        """Internal method."""
        pass


class AdvancedCalculator(Calculator):
    """Advanced calculator with more operations."""

    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        self.result = x * y
        return self.result
'''


@pytest.fixture
def import_code():
    """Python code with various import styles."""
    return '''
import os
import sys

from pathlib import Path
from typing import Optional, List

import json as json_lib

from collections import *


def use_imports():
    path = Path(".")
    data = json_lib.loads("{}")
    return os.getcwd()
'''


@pytest.fixture
def cross_module_repo(temp_dir):
    """Create a multi-file test repo."""
    # utils.py
    (temp_dir / "utils.py").write_text('''
def validate(data):
    return bool(data)

def sanitize(text):
    return text.strip()
''')

    # main.py
    (temp_dir / "main.py").write_text('''
from utils import validate, sanitize

def process(data):
    if validate(data):
        return sanitize(data)
    return None
''')

    return temp_dir
