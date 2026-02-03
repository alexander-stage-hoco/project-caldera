"""Large file test repo - 500+ lines, 50+ functions, 10+ classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# ============================================================================
# Base Classes
# ============================================================================


class BaseEntity(ABC):
    """Abstract base for all entities."""

    @abstractmethod
    def get_id(self) -> str:
        """Return entity ID."""
        ...

    @abstractmethod
    def validate(self) -> bool:
        """Validate entity."""
        ...


@dataclass
class Metadata:
    """Metadata for entities."""

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    version: int = 1
    tags: list[str] = field(default_factory=list)

    def bump_version(self) -> None:
        """Increment version."""
        self.version += 1
        self.updated_at = datetime.now()


# ============================================================================
# User Domain
# ============================================================================


@dataclass
class Address:
    """User address."""

    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"

    def format_full(self) -> str:
        """Format full address."""
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}, {self.country}"

    def format_short(self) -> str:
        """Format short address."""
        return f"{self.city}, {self.state}"


class User(BaseEntity):
    """User entity."""

    def __init__(self, user_id: str, name: str, email: str):
        """Initialize user."""
        self.user_id = user_id
        self.name = name
        self.email = email
        self.metadata = Metadata()
        self.addresses: list[Address] = []
        self.preferences: dict[str, Any] = {}

    def get_id(self) -> str:
        """Return user ID."""
        return self.user_id

    def validate(self) -> bool:
        """Validate user."""
        return bool(self.name and "@" in self.email)

    def add_address(self, address: Address) -> None:
        """Add address to user."""
        self.addresses.append(address)

    def get_primary_address(self) -> Address | None:
        """Get primary address."""
        return self.addresses[0] if self.addresses else None

    def set_preference(self, key: str, value: Any) -> None:
        """Set preference."""
        self.preferences[key] = value
        self.metadata.bump_version()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get preference."""
        return self.preferences.get(key, default)


class Admin(User):
    """Admin user."""

    def __init__(self, user_id: str, name: str, email: str, permissions: list[str]):
        """Initialize admin."""
        super().__init__(user_id, name, email)
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """Check if admin has permission."""
        return permission in self.permissions or "*" in self.permissions

    def grant_permission(self, permission: str) -> None:
        """Grant permission."""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def revoke_permission(self, permission: str) -> None:
        """Revoke permission."""
        if permission in self.permissions:
            self.permissions.remove(permission)


# ============================================================================
# Product Domain
# ============================================================================


@dataclass
class ProductSpec:
    """Product specifications."""

    weight: float
    dimensions: tuple[float, float, float]
    color: str
    material: str

    def get_volume(self) -> float:
        """Calculate volume."""
        return self.dimensions[0] * self.dimensions[1] * self.dimensions[2]


class Product(BaseEntity):
    """Product entity."""

    def __init__(self, product_id: str, name: str, price: float):
        """Initialize product."""
        self.product_id = product_id
        self.name = name
        self.price = price
        self.metadata = Metadata()
        self.spec: ProductSpec | None = None
        self.categories: list[str] = []

    def get_id(self) -> str:
        """Return product ID."""
        return self.product_id

    def validate(self) -> bool:
        """Validate product."""
        return bool(self.name and self.price > 0)

    def set_spec(self, spec: ProductSpec) -> None:
        """Set product spec."""
        self.spec = spec
        self.metadata.bump_version()

    def add_category(self, category: str) -> None:
        """Add category."""
        if category not in self.categories:
            self.categories.append(category)

    def apply_discount(self, percent: float) -> float:
        """Apply discount and return new price."""
        discount = self.price * (percent / 100)
        return self.price - discount

    def clone(self) -> "Product":
        """Clone product."""
        cloned = Product(f"{self.product_id}_copy", self.name, self.price)
        cloned.spec = self.spec
        cloned.categories = self.categories.copy()
        return cloned


# ============================================================================
# Order Domain
# ============================================================================


@dataclass
class OrderItem:
    """Order line item."""

    product: Product
    quantity: int
    unit_price: float

    def get_total(self) -> float:
        """Get item total."""
        return self.quantity * self.unit_price


class Order(BaseEntity):
    """Order entity."""

    def __init__(self, order_id: str, user: User):
        """Initialize order."""
        self.order_id = order_id
        self.user = user
        self.items: list[OrderItem] = []
        self.status: str = "pending"
        self.metadata = Metadata()
        self.shipping_address: Address | None = None

    def get_id(self) -> str:
        """Return order ID."""
        return self.order_id

    def validate(self) -> bool:
        """Validate order."""
        return bool(self.items and self.user and self.shipping_address)

    def add_item(self, product: Product, quantity: int) -> None:
        """Add item to order."""
        item = OrderItem(product, quantity, product.price)
        self.items.append(item)
        self.metadata.bump_version()

    def remove_item(self, product_id: str) -> bool:
        """Remove item from order."""
        for i, item in enumerate(self.items):
            if item.product.product_id == product_id:
                self.items.pop(i)
                self.metadata.bump_version()
                return True
        return False

    def get_subtotal(self) -> float:
        """Get order subtotal."""
        return sum(item.get_total() for item in self.items)

    def get_tax(self, rate: float = 0.08) -> float:
        """Calculate tax."""
        return self.get_subtotal() * rate

    def get_total(self) -> float:
        """Get order total."""
        return self.get_subtotal() + self.get_tax()

    def set_shipping_address(self, address: Address) -> None:
        """Set shipping address."""
        self.shipping_address = address
        self.metadata.bump_version()

    def submit(self) -> bool:
        """Submit order."""
        if self.validate():
            self.status = "submitted"
            self.metadata.bump_version()
            return True
        return False

    def cancel(self) -> bool:
        """Cancel order."""
        if self.status in ("pending", "submitted"):
            self.status = "cancelled"
            self.metadata.bump_version()
            return True
        return False


# ============================================================================
# Generic Repository
# ============================================================================


class Repository(Generic[T]):
    """Generic repository."""

    def __init__(self) -> None:
        """Initialize repository."""
        self._items: dict[str, T] = {}

    def add(self, item: T) -> None:
        """Add item."""
        if hasattr(item, "get_id"):
            self._items[item.get_id()] = item

    def get(self, item_id: str) -> T | None:
        """Get item by ID."""
        return self._items.get(item_id)

    def remove(self, item_id: str) -> bool:
        """Remove item."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def list_all(self) -> list[T]:
        """List all items."""
        return list(self._items.values())

    def count(self) -> int:
        """Count items."""
        return len(self._items)

    def clear(self) -> None:
        """Clear all items."""
        self._items.clear()

    def find_by(self, predicate: Callable[[T], bool]) -> list[T]:
        """Find items matching predicate."""
        return [item for item in self._items.values() if predicate(item)]


# ============================================================================
# Service Classes
# ============================================================================


class UserService:
    """User service."""

    def __init__(self, repo: Repository[User]):
        """Initialize service."""
        self.repo = repo

    def create_user(self, name: str, email: str) -> User:
        """Create user."""
        user_id = f"user_{datetime.now().timestamp()}"
        user = User(user_id, name, email)
        self.repo.add(user)
        return user

    def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        return self.repo.get(user_id)

    def update_email(self, user_id: str, email: str) -> bool:
        """Update user email."""
        user = self.repo.get(user_id)
        if user:
            user.email = email
            user.metadata.bump_version()
            return True
        return False

    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        return self.repo.remove(user_id)

    def search_by_email(self, email_part: str) -> list[User]:
        """Search users by email."""
        return self.repo.find_by(lambda u: email_part in u.email)


class ProductService:
    """Product service."""

    def __init__(self, repo: Repository[Product]):
        """Initialize service."""
        self.repo = repo

    def create_product(self, name: str, price: float) -> Product:
        """Create product."""
        product_id = f"prod_{datetime.now().timestamp()}"
        product = Product(product_id, name, price)
        self.repo.add(product)
        return product

    def get_product(self, product_id: str) -> Product | None:
        """Get product by ID."""
        return self.repo.get(product_id)

    def update_price(self, product_id: str, price: float) -> bool:
        """Update product price."""
        product = self.repo.get(product_id)
        if product:
            product.price = price
            product.metadata.bump_version()
            return True
        return False

    def get_by_category(self, category: str) -> list[Product]:
        """Get products by category."""
        return self.repo.find_by(lambda p: category in p.categories)

    def apply_bulk_discount(self, percent: float, category: str | None = None) -> int:
        """Apply discount to products."""
        count = 0
        for product in self.repo.list_all():
            if category is None or category in product.categories:
                product.price = product.apply_discount(percent)
                count += 1
        return count


class OrderService:
    """Order service."""

    def __init__(self, order_repo: Repository[Order], user_service: UserService):
        """Initialize service."""
        self.order_repo = order_repo
        self.user_service = user_service

    def create_order(self, user_id: str) -> Order | None:
        """Create order for user."""
        user = self.user_service.get_user(user_id)
        if not user:
            return None
        order_id = f"order_{datetime.now().timestamp()}"
        order = Order(order_id, user)
        self.order_repo.add(order)
        return order

    def get_order(self, order_id: str) -> Order | None:
        """Get order by ID."""
        return self.order_repo.get(order_id)

    def get_user_orders(self, user_id: str) -> list[Order]:
        """Get all orders for user."""
        return self.order_repo.find_by(lambda o: o.user.user_id == user_id)

    def submit_order(self, order_id: str) -> bool:
        """Submit order."""
        order = self.order_repo.get(order_id)
        return order.submit() if order else False

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order."""
        order = self.order_repo.get(order_id)
        return order.cancel() if order else False


# ============================================================================
# Utility Functions
# ============================================================================


def validate_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email and "." in email.split("@")[1]


def validate_zip_code(zip_code: str) -> bool:
    """Validate US zip code."""
    return len(zip_code) == 5 and zip_code.isdigit()


def format_currency(amount: float) -> str:
    """Format as currency."""
    return f"${amount:,.2f}"


def format_date(dt: datetime) -> str:
    """Format datetime."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def calculate_shipping(weight: float, distance: int) -> float:
    """Calculate shipping cost."""
    base_rate = 5.0
    weight_rate = 0.5
    distance_rate = 0.01
    return base_rate + (weight * weight_rate) + (distance * distance_rate)


def generate_tracking_number() -> str:
    """Generate tracking number."""
    import random
    import string
    prefix = "TRK"
    suffix = "".join(random.choices(string.digits, k=10))
    return f"{prefix}{suffix}"


def parse_address(address_str: str) -> Address | None:
    """Parse address string."""
    parts = address_str.split(", ")
    if len(parts) >= 4:
        return Address(
            street=parts[0],
            city=parts[1],
            state=parts[2].split()[0],
            zip_code=parts[2].split()[1] if len(parts[2].split()) > 1 else "",
            country=parts[3] if len(parts) > 3 else "USA",
        )
    return None


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Merge two dictionaries."""
    result = dict1.copy()
    result.update(dict2)
    return result


def flatten_list(nested: list[list[T]]) -> list[T]:
    """Flatten nested list."""
    return [item for sublist in nested for item in sublist]


def chunk_list(items: list[T], chunk_size: int) -> list[list[T]]:
    """Chunk list into smaller lists."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def deduplicate(items: list[T]) -> list[T]:
    """Remove duplicates preserving order."""
    seen = set()
    result = []
    for item in items:
        item_hash = hash(str(item))
        if item_hash not in seen:
            seen.add(item_hash)
            result.append(item)
    return result


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely get nested dict value."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def retry(func: Callable, max_attempts: int = 3, delay: float = 1.0) -> Any:
    """Retry function on failure."""
    import time
    last_error = None
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(delay)
    raise last_error


def memoize(func: Callable) -> Callable:
    """Memoization decorator."""
    cache: dict = {}

    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return wrapper


def compose(*funcs: Callable) -> Callable:
    """Compose multiple functions."""
    def composed(x):
        result = x
        for func in reversed(funcs):
            result = func(result)
        return result
    return composed


def pipe(value: Any, *funcs: Callable) -> Any:
    """Pipe value through functions."""
    result = value
    for func in funcs:
        result = func(result)
    return result


# ============================================================================
# Factory Functions
# ============================================================================


def create_test_user(index: int = 0) -> User:
    """Create test user."""
    return User(f"test_user_{index}", f"Test User {index}", f"test{index}@example.com")


def create_test_product(index: int = 0) -> Product:
    """Create test product."""
    return Product(f"test_prod_{index}", f"Test Product {index}", 9.99 + index)


def create_test_order(user: User) -> Order:
    """Create test order."""
    order = Order(f"test_order_{datetime.now().timestamp()}", user)
    order.set_shipping_address(user.get_primary_address() or Address("123 Test St", "Test City", "TS", "12345"))
    return order


def build_sample_data() -> dict[str, Any]:
    """Build sample data for testing."""
    users = [create_test_user(i) for i in range(5)]
    products = [create_test_product(i) for i in range(10)]
    orders = [create_test_order(users[i % len(users)]) for i in range(3)]

    return {
        "users": users,
        "products": products,
        "orders": orders,
    }
