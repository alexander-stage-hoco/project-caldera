"""Import patterns test repo - various import styles."""

# Standard module import
import os
import sys

# From import with multiple symbols
from pathlib import Path, PurePath

# Aliased import
import json as json_lib

# Relative import (simulated)
# from .utils import helper  # Would need package structure

# Star import (generally discouraged)
from collections import *


def get_cwd() -> Path:
    """Get current working directory using pathlib."""
    return Path.cwd()


def read_json(filepath: str) -> dict:
    """Read JSON file."""
    with open(filepath) as f:
        return json_lib.load(f)


def list_files(directory: str) -> list[str]:
    """List files in directory."""
    return os.listdir(directory)


def get_python_path() -> list[str]:
    """Get Python path."""
    return sys.path.copy()
