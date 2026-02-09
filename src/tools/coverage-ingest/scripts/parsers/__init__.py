"""Coverage report parsers for multiple formats."""
from __future__ import annotations

from .base import BaseCoverageParser, FileCoverage
from .lcov import LcovParser
from .cobertura import CoberturaParser
from .jacoco import JacocoParser
from .istanbul import IstanbulParser

__all__ = [
    "BaseCoverageParser",
    "FileCoverage",
    "LcovParser",
    "CoberturaParser",
    "JacocoParser",
    "IstanbulParser",
]
