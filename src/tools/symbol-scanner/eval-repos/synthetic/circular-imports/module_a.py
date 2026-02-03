"""Module A - imports from module_b (circular dependency)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import ClassB

from module_b import helper_b


class ClassA:
    """Class that references ClassB."""

    def __init__(self, name: str):
        self.name = name
        self._b_instance: ClassB | None = None

    def get_name(self) -> str:
        """Return the name."""
        return self.name

    def call_b(self, b_instance: ClassB) -> str:
        """Call a method on ClassB instance."""
        self._b_instance = b_instance
        return b_instance.process(self.name)

    def use_helper(self) -> str:
        """Use the helper from module_b."""
        return helper_b(self.name)


def create_a(name: str) -> ClassA:
    """Factory function for ClassA."""
    return ClassA(name)
