"""Module B - imports from module_a (circular dependency)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_a import ClassA

from module_a import create_a


class ClassB:
    """Class that references ClassA."""

    def __init__(self, value: int):
        self.value = value
        self._a_instance: ClassA | None = None

    def get_value(self) -> int:
        """Return the value."""
        return self.value

    def process(self, text: str) -> str:
        """Process text with value."""
        return f"{text}_{self.value}"

    def create_and_link_a(self, name: str) -> ClassA:
        """Create a ClassA instance and link it."""
        a = create_a(name)
        self._a_instance = a
        return a


def helper_b(text: str) -> str:
    """Helper function used by module_a."""
    return f"helper_{text}"
