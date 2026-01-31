"""
ID Generator for Layout Scanner.

Generates stable, deterministic IDs for files and directories using SHA-256 hashing.
IDs are prefixed with 'f-' for files and 'd-' for directories.
"""

import hashlib
from typing import Literal


def generate_id(path: str, kind: Literal["file", "directory"]) -> str:
    """
    Generate a stable ID for a file or directory.

    The ID is computed as SHA-256 hash of the normalized path, truncated to 12 hex chars.
    This ensures:
    - Same path always produces same ID (deterministic)
    - Different paths produce different IDs (collision-resistant for practical purposes)
    - IDs are short enough to be readable

    Args:
        path: Normalized relative path from repository root
        kind: Either "file" or "directory"

    Returns:
        ID string like "f-a3b2c1d4e5f6" for files or "d-123456789abc" for directories
    """
    prefix = "f-" if kind == "file" else "d-"

    # Hash the path
    hash_bytes = hashlib.sha256(path.encode("utf-8")).digest()

    # Take first 6 bytes (12 hex chars) for a compact but collision-resistant ID
    hash_hex = hash_bytes[:6].hex()

    return f"{prefix}{hash_hex}"


def generate_root_id() -> str:
    """
    Generate the root directory ID.

    The root directory always has a special ID for easy identification.
    """
    return "d-000000000000"


def is_file_id(id_str: str) -> bool:
    """Check if an ID represents a file."""
    return id_str.startswith("f-")


def is_directory_id(id_str: str) -> bool:
    """Check if an ID represents a directory."""
    return id_str.startswith("d-")


def extract_hash(id_str: str) -> str:
    """Extract the hash portion from an ID."""
    return id_str[2:]  # Skip prefix
