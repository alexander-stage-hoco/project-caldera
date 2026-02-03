"""File with mix of valid and invalid Python - tests error recovery."""

# Valid function at start
def valid_function_one(x: int) -> int:
    """First valid function."""
    return x * 2


# Another valid function
def valid_function_two(a: str, b: str) -> str:
    """Concatenate strings."""
    return a + b


# Valid class
class ValidClass:
    """A valid class."""

    def __init__(self, name: str):
        """Initialize."""
        self.name = name

    def greet(self) -> str:
        """Return greeting."""
        return f"Hello, {self.name}"


# SYNTAX ERROR: Missing colon
def broken_function_one(x)
    return x + 1


# This function after the error should still be extractable by tree-sitter
def valid_after_error(value: int) -> int:
    """Valid function after syntax error."""
    return value * 3


# SYNTAX ERROR: Unclosed parenthesis
def broken_function_two(a, b:
    return a + b


# Valid class after errors
class AnotherValidClass:
    """Valid class after syntax errors."""

    def method_one(self) -> int:
        """Return one."""
        return 1

    def method_two(self, x: int) -> int:
        """Double input."""
        return x * 2


# SYNTAX ERROR: Invalid indentation
def broken_indentation():
"""Bad docstring indent."""
    return 42


# Valid function at end
def final_valid_function(items: list) -> int:
    """Count items."""
    return len(items)


# Valid nested function
def outer_valid():
    """Outer function."""
    def inner_valid():
        """Inner function."""
        return "nested"
    return inner_valid()


# SYNTAX ERROR: Missing closing bracket
data = [1, 2, 3, 4


# Final valid function
def very_last_function() -> str:
    """The very last function."""
    return "end"
