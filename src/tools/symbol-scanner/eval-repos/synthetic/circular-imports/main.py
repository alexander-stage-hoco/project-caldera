"""Main entry point demonstrating circular import handling."""

from __future__ import annotations

from module_a import ClassA, create_a
from module_b import ClassB


def main():
    """Demonstrate the circular import pattern."""
    a = create_a("test")
    b = ClassB(42)

    # Cross-module calls
    result1 = a.call_b(b)
    result2 = a.use_helper()
    result3 = b.create_and_link_a("linked")

    print(f"Results: {result1}, {result2}, {result3.get_name()}")


if __name__ == "__main__":
    main()
