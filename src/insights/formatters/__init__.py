"""
Output formatters for insights reports.
"""

from .base import BaseFormatter
from .html import HtmlFormatter
from .markdown import MarkdownFormatter

__all__ = [
    "BaseFormatter",
    "HtmlFormatter",
    "MarkdownFormatter",
]
