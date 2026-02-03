"""Generator and comprehension patterns test repo."""

from typing import Generator, Iterator, Iterable


# Simple generator function
def count_up(n: int) -> Generator[int, None, None]:
    """Generate numbers from 0 to n-1."""
    i = 0
    while i < n:
        yield i
        i += 1


# Generator with send support
def accumulator() -> Generator[int, int | None, int]:
    """Accumulator generator that accepts values via send()."""
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value
    return total


# Generator that delegates with yield from
def flatten(nested: Iterable[Iterable[int]]) -> Generator[int, None, None]:
    """Flatten nested iterables using yield from."""
    for inner in nested:
        yield from inner


# Generator with exception handling
def safe_divide(numbers: list[int], divisor: int) -> Generator[float | None, None, None]:
    """Divide numbers, yielding None on error."""
    for n in numbers:
        try:
            yield n / divisor
        except ZeroDivisionError:
            yield None


# Infinite generator
def fibonacci() -> Generator[int, None, None]:
    """Generate infinite Fibonacci sequence."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


# Class with generator method
class DataProcessor:
    """Processes data using generators."""

    def __init__(self, data: list[int]):
        """Initialize with data."""
        self.data = data

    def process_items(self) -> Generator[str, None, None]:
        """Process items yielding strings."""
        for item in self.data:
            yield f"Processed: {item}"

    def filter_positive(self) -> Generator[int, None, None]:
        """Filter positive numbers."""
        for item in self.data:
            if item > 0:
                yield item


# Functions using comprehensions
def square_list(numbers: list[int]) -> list[int]:
    """Create list of squares using list comprehension."""
    return [x * x for x in numbers]


def filter_even(numbers: list[int]) -> list[int]:
    """Filter even numbers with list comprehension."""
    return [x for x in numbers if x % 2 == 0]


def nested_comprehension(matrix: list[list[int]]) -> list[int]:
    """Flatten matrix with nested comprehension."""
    return [x for row in matrix for x in row]


def conditional_comprehension(numbers: list[int]) -> list[str]:
    """Comprehension with conditional expression."""
    return ["even" if x % 2 == 0 else "odd" for x in numbers]


# Dict comprehension
def create_lookup(items: list[str]) -> dict[str, int]:
    """Create lookup dict using dict comprehension."""
    return {item: len(item) for item in items}


def invert_dict(d: dict[str, int]) -> dict[int, str]:
    """Invert dict using comprehension."""
    return {v: k for k, v in d.items()}


# Set comprehension
def unique_lengths(words: list[str]) -> set[int]:
    """Get unique word lengths using set comprehension."""
    return {len(w) for w in words}


# Generator expression
def sum_squares(numbers: list[int]) -> int:
    """Sum of squares using generator expression."""
    return sum(x * x for x in numbers)


def any_positive(numbers: list[int]) -> bool:
    """Check if any number is positive using generator expression."""
    return any(x > 0 for x in numbers)


def first_match(items: list[str], prefix: str) -> str | None:
    """Find first item matching prefix using generator expression."""
    return next((item for item in items if item.startswith(prefix)), None)


# Complex nested comprehensions
def matrix_transpose(matrix: list[list[int]]) -> list[list[int]]:
    """Transpose matrix using nested comprehension."""
    if not matrix:
        return []
    return [[row[i] for row in matrix] for i in range(len(matrix[0]))]


# Walrus operator in comprehension (Python 3.8+)
def filter_and_transform(numbers: list[int]) -> list[int]:
    """Filter and transform using walrus operator."""
    return [y for x in numbers if (y := x * 2) > 10]


# Generator that uses comprehensions internally
def processed_chunks(data: list[int], chunk_size: int) -> Generator[list[int], None, None]:
    """Yield processed chunks using comprehension."""
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        yield [x * 2 for x in chunk]
