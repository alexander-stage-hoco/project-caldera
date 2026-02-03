"""Modern Python syntax test repo - Python 3.10+ features."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


# Structural pattern matching (Python 3.10+)
def process_command(command: dict[str, Any]) -> str:
    """Process command using match statement."""
    match command:
        case {"action": "create", "name": str(name)}:
            return f"Creating {name}"
        case {"action": "delete", "id": int(id_)}:
            return f"Deleting {id_}"
        case {"action": "update", "id": int(id_), "data": dict(data)}:
            return f"Updating {id_} with {len(data)} fields"
        case {"action": str(action)}:
            return f"Unknown action: {action}"
        case _:
            return "Invalid command"


# Match with guards
def categorize_number(n: int | float) -> str:
    """Categorize number using match with guards."""
    match n:
        case int(x) if x < 0:
            return "negative integer"
        case int(x) if x == 0:
            return "zero"
        case int(x) if x > 0:
            return "positive integer"
        case float(x) if x < 0:
            return "negative float"
        case float(x) if x >= 0:
            return "non-negative float"
        case _:
            return "unknown"


# Match with class patterns
@dataclass
class Point:
    """Point dataclass for pattern matching."""

    x: float
    y: float


@dataclass
class Circle:
    """Circle dataclass for pattern matching."""

    center: Point
    radius: float


@dataclass
class Rectangle:
    """Rectangle dataclass for pattern matching."""

    top_left: Point
    width: float
    height: float


def describe_shape(shape: Point | Circle | Rectangle) -> str:
    """Describe shape using class patterns."""
    match shape:
        case Point(x=0, y=0):
            return "origin"
        case Point(x=x, y=y) if x == y:
            return f"diagonal point at {x}"
        case Point(x=x, y=y):
            return f"point at ({x}, {y})"
        case Circle(center=Point(x=0, y=0), radius=r):
            return f"circle at origin with radius {r}"
        case Circle(center=c, radius=r):
            return f"circle at ({c.x}, {c.y}) with radius {r}"
        case Rectangle(top_left=tl, width=w, height=h):
            return f"rectangle at ({tl.x}, {tl.y}) size {w}x{h}"
        case _:
            return "unknown shape"


# Match with sequence patterns
def process_sequence(seq: list[Any]) -> str:
    """Process sequence using match."""
    match seq:
        case []:
            return "empty"
        case [x]:
            return f"single: {x}"
        case [x, y]:
            return f"pair: {x}, {y}"
        case [x, y, *rest]:
            return f"starts with {x}, {y} and {len(rest)} more"
        case _:
            return "other"


# Walrus operator (Python 3.8+) in various contexts
def find_first_long_word(words: list[str], min_length: int = 5) -> str | None:
    """Find first word longer than min_length using walrus."""
    for word in words:
        if (n := len(word)) >= min_length:
            print(f"Found word of length {n}")
            return word
    return None


def process_with_walrus(data: list[int]) -> list[int]:
    """Process data using walrus in comprehension."""
    return [y for x in data if (y := x * 2) > 10]


# Positional-only parameters (Python 3.8+)
def positional_only(x: int, y: int, /) -> int:
    """Function with positional-only parameters."""
    return x + y


def mixed_parameters(pos_only: int, /, standard: int, *, kw_only: int) -> int:
    """Function with positional-only, standard, and keyword-only."""
    return pos_only + standard + kw_only


# Union types with | (Python 3.10+)
def process_value(value: int | str | None) -> str:
    """Process value with union type."""
    if value is None:
        return "none"
    return str(value)


def get_item(container: list[int] | dict[str, int], key: int | str) -> int | None:
    """Get item from list or dict."""
    match container:
        case list():
            return container[int(key)] if isinstance(key, int) and 0 <= key < len(container) else None
        case dict():
            return container.get(str(key))
        case _:
            return None


# Enum with match
class Status(Enum):
    """Status enum for matching."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


def handle_status(status: Status) -> str:
    """Handle status with match."""
    match status:
        case Status.PENDING:
            return "Waiting..."
        case Status.ACTIVE:
            return "In progress"
        case Status.COMPLETED:
            return "Done!"
        case Status.FAILED:
            return "Error occurred"


# Type alias (Python 3.12+)
type Vector = list[float]
type Matrix = list[Vector]


def multiply_matrix(m: Matrix, v: Vector) -> Vector:
    """Multiply matrix by vector."""
    return [sum(row[i] * v[i] for i in range(len(v))) for row in m]


# Exception groups (Python 3.11+)
def validate_all(items: list[dict]) -> None:
    """Validate all items, collecting all errors."""
    errors = []
    for i, item in enumerate(items):
        if "name" not in item:
            errors.append(ValueError(f"Item {i} missing name"))
        if "value" not in item:
            errors.append(ValueError(f"Item {i} missing value"))
    if errors:
        raise ExceptionGroup("Validation failed", errors)


# Self type hint (Python 3.11+)
class Builder:
    """Builder pattern with Self type."""

    def __init__(self) -> None:
        """Initialize builder."""
        self.parts: list[str] = []

    def add(self, part: str) -> "Builder":
        """Add part and return self for chaining."""
        self.parts.append(part)
        return self

    def build(self) -> str:
        """Build final result."""
        return "".join(self.parts)
