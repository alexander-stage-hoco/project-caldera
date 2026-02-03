"""Advanced decorator patterns test repo."""

from functools import wraps
from typing import Callable, TypeVar

T = TypeVar("T")


# Simple decorator (no arguments)
def simple_decorator(func: Callable) -> Callable:
    """Simple decorator without arguments."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("Before")
        result = func(*args, **kwargs)
        print("After")
        return result
    return wrapper


# Decorator with arguments
def repeat(times: int):
    """Decorator that repeats function execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results
        return wrapper
    return decorator


# Decorator that modifies return value
def add_prefix(prefix: str):
    """Decorator that adds prefix to string return value."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return f"{prefix}{result}"
        return wrapper
    return decorator


# Class with various decorator types
class Service:
    """Service class demonstrating method decorators."""

    _cache: dict = {}

    def __init__(self, name: str):
        """Initialize service."""
        self.name = name

    @staticmethod
    def create_id() -> str:
        """Static method to create ID."""
        import uuid
        return str(uuid.uuid4())

    @classmethod
    def from_config(cls, config: dict) -> "Service":
        """Class method to create from config."""
        return cls(config.get("name", "default"))

    @property
    def display_name(self) -> str:
        """Property to get display name."""
        return f"Service: {self.name}"

    @property
    def status(self) -> str:
        """Another property."""
        return "active"

    @simple_decorator
    def process(self, data: str) -> str:
        """Method with simple decorator."""
        return data.upper()

    @repeat(3)
    def fetch(self, url: str) -> str:
        """Method with parameterized decorator."""
        return f"Fetched: {url}"


# Stacked decorators
@simple_decorator
@add_prefix("[LOG] ")
def log_message(msg: str) -> str:
    """Function with stacked decorators."""
    return msg


# Function with multiple stacked decorators
@simple_decorator
@repeat(2)
@add_prefix(">> ")
def process_item(item: str) -> str:
    """Function with three stacked decorators."""
    return item.strip()


# Using decorated function
@simple_decorator
def greet(name: str) -> str:
    """Simple decorated function."""
    return f"Hello, {name}!"


# Custom context manager decorator
class context_decorator:
    """Class-based decorator."""

    def __init__(self, func: Callable):
        """Initialize with function."""
        self.func = func
        wraps(func)(self)

    def __call__(self, *args, **kwargs):
        """Call the decorated function."""
        print("Entering context")
        try:
            return self.func(*args, **kwargs)
        finally:
            print("Exiting context")


@context_decorator
def risky_operation(value: int) -> int:
    """Function with class-based decorator."""
    return value * 2
