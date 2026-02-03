"""Metaprogramming patterns - metaclasses, descriptors, __init_subclass__."""

from typing import Any, Callable, TypeVar, Generic


T = TypeVar("T")


# ============================================================================
# Descriptors
# ============================================================================


class Descriptor:
    """Simple data descriptor."""

    def __set_name__(self, owner: type, name: str) -> None:
        """Store attribute name."""
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        """Get attribute value."""
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj: Any, value: Any) -> None:
        """Set attribute value."""
        setattr(obj, self.private_name, value)


class TypedDescriptor(Generic[T]):
    """Type-checked descriptor."""

    def __init__(self, expected_type: type[T]) -> None:
        """Initialize with expected type."""
        self.expected_type = expected_type
        self.name = ""
        self.private_name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        """Store attribute name."""
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj: Any, objtype: type | None = None) -> T | None:
        """Get attribute value."""
        if obj is None:
            return self  # type: ignore
        return getattr(obj, self.private_name, None)

    def __set__(self, obj: Any, value: T) -> None:
        """Set attribute value with type check."""
        if not isinstance(value, self.expected_type):
            raise TypeError(f"{self.name} must be {self.expected_type.__name__}")
        setattr(obj, self.private_name, value)


class CachedProperty:
    """Cached property descriptor (like functools.cached_property)."""

    def __init__(self, func: Callable[[Any], T]) -> None:
        """Initialize with getter function."""
        self.func = func
        self.name = ""

    def __set_name__(self, owner: type, name: str) -> None:
        """Store attribute name."""
        self.name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> T:
        """Get cached value or compute it."""
        if obj is None:
            return self  # type: ignore
        if self.name not in obj.__dict__:
            obj.__dict__[self.name] = self.func(obj)
        return obj.__dict__[self.name]


# ============================================================================
# Metaclasses
# ============================================================================


class SingletonMeta(type):
    """Metaclass for singleton pattern."""

    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Return existing instance or create new one."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class RegistryMeta(type):
    """Metaclass that registers all subclasses."""

    _registry: dict[str, type] = {}

    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> type:
        """Create class and register it."""
        cls = super().__new__(mcs, name, bases, namespace)
        mcs._registry[name] = cls
        return cls

    @classmethod
    def get_class(mcs, name: str) -> type | None:
        """Get class by name."""
        return mcs._registry.get(name)


class ValidatingMeta(type):
    """Metaclass that validates class attributes."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> type:
        """Create class with validation."""
        # Check for required methods
        required_methods = namespace.get("_required_methods", [])
        for method in required_methods:
            if method not in namespace:
                raise TypeError(f"Class {name} must implement {method}")
        return super().__new__(mcs, name, bases, namespace)


# ============================================================================
# __init_subclass__ Pattern
# ============================================================================


class Plugin:
    """Base class using __init_subclass__ for plugin registration."""

    _plugins: dict[str, type] = {}

    def __init_subclass__(cls, plugin_name: str = "", **kwargs: Any) -> None:
        """Register plugin subclass."""
        super().__init_subclass__(**kwargs)
        name = plugin_name or cls.__name__
        Plugin._plugins[name] = cls

    @classmethod
    def get_plugin(cls, name: str) -> type | None:
        """Get plugin by name."""
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls) -> list[str]:
        """List all plugin names."""
        return list(cls._plugins.keys())


class Validator:
    """Base class for validators using __init_subclass__."""

    _validators: list[type] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register validator subclass."""
        super().__init_subclass__(**kwargs)
        Validator._validators.append(cls)

    def validate(self, value: Any) -> bool:
        """Validate value (to be overridden)."""
        return True

    @classmethod
    def validate_all(cls, value: Any) -> list[str]:
        """Run all validators."""
        errors = []
        for validator_cls in cls._validators:
            validator = validator_cls()
            if not validator.validate(value):
                errors.append(f"{validator_cls.__name__} failed")
        return errors


# ============================================================================
# __class_getitem__ Pattern
# ============================================================================


class Container:
    """Generic container using __class_getitem__."""

    _type_cache: dict[type, type] = {}

    def __class_getitem__(cls, item_type: type) -> type:
        """Return specialized container type."""
        if item_type not in cls._type_cache:
            # Create specialized class
            new_cls = type(
                f"{cls.__name__}[{item_type.__name__}]",
                (cls,),
                {"_item_type": item_type},
            )
            cls._type_cache[item_type] = new_cls
        return cls._type_cache[item_type]

    def __init__(self) -> None:
        """Initialize container."""
        self.items: list[Any] = []
        self._item_type: type = object

    def add(self, item: Any) -> None:
        """Add item with type checking."""
        if not isinstance(item, self._item_type):
            raise TypeError(f"Expected {self._item_type.__name__}")
        self.items.append(item)


# ============================================================================
# Dynamic Class Creation
# ============================================================================


def create_class(name: str, attrs: dict[str, Any], bases: tuple = ()) -> type:
    """Dynamically create a class."""
    return type(name, bases, attrs)


def create_dataclass_like(name: str, fields: dict[str, type]) -> type:
    """Create a simple dataclass-like class."""

    def __init__(self: Any, **kwargs: Any) -> None:
        for field_name, field_type in fields.items():
            value = kwargs.get(field_name)
            if value is not None and not isinstance(value, field_type):
                raise TypeError(f"{field_name} must be {field_type.__name__}")
            setattr(self, field_name, value)

    def __repr__(self: Any) -> str:
        values = ", ".join(f"{k}={getattr(self, k)!r}" for k in fields)
        return f"{name}({values})"

    namespace = {
        "__init__": __init__,
        "__repr__": __repr__,
        "_fields": fields,
    }
    return type(name, (), namespace)


def add_method(cls: type, name: str, func: Callable) -> None:
    """Add method to existing class."""
    setattr(cls, name, func)


def wrap_class(cls: type) -> type:
    """Class decorator that adds functionality."""
    original_init = cls.__init__

    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        print(f"Creating {cls.__name__}")
        original_init(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls


# ============================================================================
# Property Factories
# ============================================================================


def make_property(attr_name: str) -> property:
    """Create a property for an attribute."""

    def getter(self: Any) -> Any:
        return getattr(self, f"_{attr_name}", None)

    def setter(self: Any, value: Any) -> None:
        setattr(self, f"_{attr_name}", value)

    return property(getter, setter)


def make_read_only_property(attr_name: str) -> property:
    """Create a read-only property."""

    def getter(self: Any) -> Any:
        return getattr(self, f"_{attr_name}", None)

    return property(getter)


# ============================================================================
# Example Classes Using Meta Patterns
# ============================================================================


class DatabaseSingleton(metaclass=SingletonMeta):
    """Database connection singleton."""

    def __init__(self, dsn: str = ""):
        """Initialize connection."""
        self.dsn = dsn
        self.connected = False

    def connect(self) -> None:
        """Connect to database."""
        self.connected = True


class JSONPlugin(Plugin, plugin_name="json"):
    """JSON serialization plugin."""

    def serialize(self, data: Any) -> str:
        """Serialize to JSON."""
        import json
        return json.dumps(data)


class XMLPlugin(Plugin, plugin_name="xml"):
    """XML serialization plugin."""

    def serialize(self, data: Any) -> str:
        """Serialize to XML."""
        return f"<data>{data}</data>"


class Person:
    """Person using descriptors."""

    name = TypedDescriptor(str)
    age = TypedDescriptor(int)

    def __init__(self, name: str, age: int):
        """Initialize person."""
        self.name = name
        self.age = age
