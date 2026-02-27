"""Identifier validation for filesystem-safe identifiers."""
from __future__ import annotations

import re

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_safe_identifier(value: str, field_name: str) -> None:
    """Raise ValueError if value contains path separators, .., or unsafe chars.

    Identifiers must start with an alphanumeric character and contain only
    alphanumeric characters, dots, underscores, and hyphens.  The substring
    ``..`` is rejected to prevent path traversal.
    """
    if not value or not _SAFE_ID_RE.match(value) or ".." in value:
        raise ValueError(
            f"Unsafe {field_name}: {value!r}. "
            f"Must match [A-Za-z0-9][A-Za-z0-9._-]* and not contain '..'."
        )
