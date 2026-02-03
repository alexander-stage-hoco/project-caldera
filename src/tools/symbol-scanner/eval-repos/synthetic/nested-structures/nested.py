"""Nested structures test repo - deeply nested code patterns."""

from typing import Callable


# Nested classes
class Outer:
    """Outer class containing nested classes."""

    class_var: str = "outer"

    def __init__(self, value: int):
        """Initialize outer."""
        self.value = value

    class Inner:
        """Nested inner class."""

        inner_var: str = "inner"

        def __init__(self, name: str):
            """Initialize inner."""
            self.name = name

        def display(self) -> str:
            """Display inner."""
            return f"Inner: {self.name}"

        class DeepNested:
            """Deeply nested class."""

            def __init__(self, data: dict):
                """Initialize deep nested."""
                self.data = data

            def process(self) -> dict:
                """Process deep nested data."""
                return {k: v * 2 for k, v in self.data.items()}

    def create_inner(self, name: str) -> "Outer.Inner":
        """Create an inner instance."""
        return Outer.Inner(name)


# Nested functions (closures)
def outer_function(multiplier: int) -> Callable[[int], int]:
    """Create a multiplier function using closure."""

    def inner_multiply(value: int) -> int:
        """Inner function that uses outer scope."""
        return value * multiplier

    return inner_multiply


def counter_factory(start: int = 0) -> tuple[Callable[[], int], Callable[[], int]]:
    """Factory creating increment/decrement closures."""
    count = start

    def increment() -> int:
        """Increment and return count."""
        nonlocal count
        count += 1
        return count

    def decrement() -> int:
        """Decrement and return count."""
        nonlocal count
        count -= 1
        return count

    return increment, decrement


def deeply_nested() -> Callable[[], Callable[[], Callable[[], int]]]:
    """Create deeply nested function chain."""

    def level1() -> Callable[[], Callable[[], int]]:
        """First level."""
        x = 1

        def level2() -> Callable[[], int]:
            """Second level."""
            y = 2

            def level3() -> int:
                """Third level using outer scopes."""
                return x + y

            return level3

        return level2

    return level1


# Lambda assignments
square = lambda x: x * x
add = lambda a, b: a + b
identity = lambda x: x


# Lambdas in more complex expressions
apply_twice = lambda f, x: f(f(x))
compose = lambda f, g: lambda x: f(g(x))


# Class with methods containing nested functions
class Processor:
    """Processor with complex nested structures."""

    def __init__(self, data: list[int]):
        """Initialize processor."""
        self.data = data

    def process_with_callback(self, callback: Callable[[int], int]) -> list[int]:
        """Process data with callback."""

        def apply_and_validate(item: int) -> int:
            """Apply callback and validate result."""
            result = callback(item)
            return result if result >= 0 else 0

        return [apply_and_validate(item) for item in self.data]

    def create_transformer(self, factor: int) -> Callable[[int], int]:
        """Create transformer function."""
        offset = 10

        def transform(value: int) -> int:
            """Transform using outer scope values."""
            return value * factor + offset

        return transform


# Function with multiple nested levels
def create_validator(
    min_val: int, max_val: int
) -> Callable[[int], tuple[bool, str]]:
    """Create a validator with nested helper functions."""

    def validate(value: int) -> tuple[bool, str]:
        """Validate a value."""

        def check_range() -> bool:
            """Check if value is in range."""
            return min_val <= value <= max_val

        def get_message() -> str:
            """Get validation message."""
            if check_range():
                return "valid"
            return f"out of range [{min_val}, {max_val}]"

        return check_range(), get_message()

    return validate


# Nested class inside function
def create_handler() -> type:
    """Create a handler class dynamically."""

    class DynamicHandler:
        """Handler created inside function."""

        def __init__(self):
            """Initialize handler."""
            self.handlers: dict = {}

        def register(self, name: str, func: Callable) -> None:
            """Register a handler."""
            self.handlers[name] = func

        def call(self, name: str, *args) -> any:
            """Call a registered handler."""
            return self.handlers[name](*args)

    return DynamicHandler


# Complex closure with class inside
def make_counter_class() -> type:
    """Create counter class with closure state."""
    count = 0

    class Counter:
        """Counter using closure state."""

        def increment(self) -> int:
            """Increment shared counter."""
            nonlocal count
            count += 1
            return count

        def get_count(self) -> int:
            """Get current count."""
            return count

    return Counter
