"""Modern Python patterns - dataclasses, protocols, TypedDict, NamedTuple."""

from dataclasses import dataclass, field, asdict, replace
from typing import Protocol, TypedDict, NamedTuple, runtime_checkable, Any, ClassVar


# ============================================================================
# Protocols (Structural Subtyping)
# ============================================================================


@runtime_checkable
class Comparable(Protocol):
    """Protocol for comparable objects."""

    def __lt__(self, other: Any) -> bool:
        """Less than comparison."""
        ...

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        ...


class Hashable(Protocol):
    """Protocol for hashable objects."""

    def __hash__(self) -> int:
        """Return hash value."""
        ...


class Serializable(Protocol):
    """Protocol for serializable objects."""

    def to_json(self) -> str:
        """Serialize to JSON string."""
        ...

    @classmethod
    def from_json(cls, data: str) -> "Serializable":
        """Deserialize from JSON string."""
        ...


class Repository(Protocol[Any]):
    """Generic repository protocol."""

    def add(self, item: Any) -> None:
        """Add item."""
        ...

    def get(self, id: str) -> Any | None:
        """Get item by ID."""
        ...

    def delete(self, id: str) -> bool:
        """Delete item."""
        ...


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass
class Point:
    """Simple 2D point."""

    x: float
    y: float

    def distance_from_origin(self) -> float:
        """Calculate distance from origin."""
        return (self.x ** 2 + self.y ** 2) ** 0.5


@dataclass(frozen=True)
class ImmutablePoint:
    """Immutable 2D point."""

    x: float
    y: float

    def translate(self, dx: float, dy: float) -> "ImmutablePoint":
        """Return new translated point."""
        return ImmutablePoint(self.x + dx, self.y + dy)


@dataclass
class Person:
    """Person with default factory."""

    name: str
    age: int
    email: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate after initialization."""
        if self.age < 0:
            raise ValueError("Age cannot be negative")

    def add_tag(self, tag: str) -> None:
        """Add a tag."""
        if tag not in self.tags:
            self.tags.append(tag)


@dataclass(order=True)
class SortablePerson:
    """Person that can be sorted."""

    sort_key: str = field(init=False, repr=False)
    name: str
    age: int

    def __post_init__(self) -> None:
        """Set sort key."""
        self.sort_key = self.name.lower()


@dataclass
class Config:
    """Configuration with class variables."""

    name: str
    debug: bool = False
    max_connections: int = 100

    # Class variables (not instance fields)
    VERSION: ClassVar[str] = "1.0.0"
    DEFAULT_TIMEOUT: ClassVar[int] = 30

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def with_debug(self, debug: bool) -> "Config":
        """Return copy with different debug setting."""
        return replace(self, debug=debug)


@dataclass
class Address:
    """Nested dataclass for addresses."""

    street: str
    city: str
    country: str
    postal_code: str = ""


@dataclass
class Company:
    """Company with nested dataclass."""

    name: str
    address: Address
    employees: list[Person] = field(default_factory=list)

    def add_employee(self, person: Person) -> None:
        """Add employee."""
        self.employees.append(person)

    def get_employee_count(self) -> int:
        """Get employee count."""
        return len(self.employees)


# ============================================================================
# TypedDict
# ============================================================================


class UserDict(TypedDict):
    """TypedDict for user data."""

    id: str
    name: str
    email: str


class UserDictOptional(TypedDict, total=False):
    """TypedDict with optional fields."""

    id: str
    name: str
    email: str
    phone: str
    address: str


class NestedDict(TypedDict):
    """TypedDict with nested structure."""

    user: UserDict
    metadata: dict[str, Any]


# ============================================================================
# NamedTuple
# ============================================================================


class Coordinate(NamedTuple):
    """Coordinate as NamedTuple."""

    x: float
    y: float
    z: float = 0.0

    def magnitude(self) -> float:
        """Calculate magnitude."""
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5


class HTTPResponse(NamedTuple):
    """HTTP response tuple."""

    status_code: int
    body: str
    headers: dict[str, str] = {}

    def is_success(self) -> bool:
        """Check if response is successful."""
        return 200 <= self.status_code < 300


class DatabaseRecord(NamedTuple):
    """Database record tuple."""

    id: int
    data: dict[str, Any]
    created_at: str
    updated_at: str | None = None


# ============================================================================
# Functions using these types
# ============================================================================


def process_comparable(items: list[Comparable]) -> list[Comparable]:
    """Sort comparable items."""
    return sorted(items)


def validate_serializable(obj: Serializable) -> bool:
    """Validate serializable object."""
    try:
        json_str = obj.to_json()
        return bool(json_str)
    except Exception:
        return False


def create_user_dict(id: str, name: str, email: str) -> UserDict:
    """Create user dict."""
    return {"id": id, "name": name, "email": email}


def transform_coordinate(coord: Coordinate, scale: float) -> Coordinate:
    """Scale a coordinate."""
    return Coordinate(coord.x * scale, coord.y * scale, coord.z * scale)


def merge_configs(base: Config, override: Config) -> Config:
    """Merge two configs, override takes precedence."""
    return Config(
        name=override.name or base.name,
        debug=override.debug,
        max_connections=override.max_connections,
    )
