"""Utility functions for cross-module calls test."""


def validate(data: str) -> bool:
    """Validate input data."""
    return bool(data and data.strip())


def sanitize(text: str) -> str:
    """Sanitize text input."""
    return text.strip().lower()


def format_output(result: dict) -> str:
    """Format output dictionary."""
    return str(result)
