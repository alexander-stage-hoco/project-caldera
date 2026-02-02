"""
Insights - Consolidated reporting component for Project Vulcan.

Generates HTML and Markdown reports from sot-engine dbt marts.
"""

from pathlib import Path

from .generator import InsightsGenerator
from .data_fetcher import DataFetcher

__all__ = [
    "InsightsGenerator",
    "DataFetcher",
]

__version__ = "0.1.0"
