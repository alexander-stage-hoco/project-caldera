"""Processor module that calls utils functions."""

from utils import validate, sanitize


def process_input(raw_input: str) -> str | None:
    """Process raw input with validation and sanitization."""
    if not validate(raw_input):
        return None
    return sanitize(raw_input)


def batch_process(items: list[str]) -> list[str]:
    """Process multiple items."""
    results = []
    for item in items:
        processed = process_input(item)
        if processed:
            results.append(processed)
    return results
