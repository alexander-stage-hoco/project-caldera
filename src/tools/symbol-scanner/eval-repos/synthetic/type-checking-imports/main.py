"""Tests for TYPE_CHECKING conditional imports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar, Generic

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path
    from typing import Any

# Type variable for generic types
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class DataProcessor(Protocol[T_co]):
    """Protocol for data processors (TYPE_CHECKING only types)."""

    def process(self, data: T_co) -> T_co:
        """Process the data."""
        ...

    def get_path(self) -> Path:
        """Get the path."""
        ...


class Repository(Generic[T]):
    """Generic repository class using TYPE_CHECKING imports."""

    def __init__(self, items: list[T] | None = None):
        self._items: list[T] = items or []
        self._callbacks: list[Callable[[T], None]] = []

    def add(self, item: T) -> None:
        """Add an item to the repository."""
        self._items.append(item)
        for callback in self._callbacks:
            callback(item)

    def get_all(self) -> list[T]:
        """Get all items."""
        return self._items.copy()

    def register_callback(self, callback: Callable[[T], None]) -> None:
        """Register a callback for item additions."""
        self._callbacks.append(callback)

    def iterate(self) -> Iterator[T]:
        """Iterate over items."""
        return iter(self._items)


def process_with_any(data: Any) -> Any:
    """Process data with Any type (from TYPE_CHECKING)."""
    if isinstance(data, dict):
        return {k: process_with_any(v) for k, v in data.items()}
    return data


def load_from_path(path: Path) -> str:
    """Load content from a path (Path from TYPE_CHECKING)."""
    return path.read_text()


class _InternalHelper:
    """Internal helper class (private)."""

    @staticmethod
    def _transform(value: str) -> str:
        return value.upper()


if __name__ == "__main__":
    repo: Repository[str] = Repository()
    repo.add("test")
    print(repo.get_all())
