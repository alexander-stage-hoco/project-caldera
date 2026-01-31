"""
Model classes with code quality issues.
For SonarQube testing of Python analysis.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime


# Code smell: Class with too many fields
@dataclass
class Customer:
    """Customer model with too many fields."""

    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    postal_code: str
    country: str
    date_of_birth: Optional[str]
    gender: Optional[str]
    membership_level: str
    loyalty_points: int
    preferred_language: str
    timezone: str
    created_at: str
    updated_at: str
    last_login: Optional[str]
    is_active: bool
    is_verified: bool
    marketing_opt_in: bool
    notes: Optional[str]


# Code smell: Empty class
class EmptyService:
    """Service class that does nothing."""

    pass


# Code smell: Class with only one method that could be a function
class SingleMethodClass:
    """Class with single method - could be a function."""

    def calculate(self, x: int, y: int) -> int:
        return x + y


# Bug: __eq__ without __hash__
class Product:
    """Product with __eq__ but no __hash__."""

    def __init__(self, id: int, name: str, price: float):
        self.id = id
        self.name = name
        self.price = price

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Product):
            return False
        return self.id == other.id


# Code smell: Inheritance depth too deep
class BaseEntity:
    """Base entity."""

    def __init__(self):
        self.id = None


class NamedEntity(BaseEntity):
    """Named entity."""

    def __init__(self):
        super().__init__()
        self.name = None


class TimestampedEntity(NamedEntity):
    """Timestamped entity."""

    def __init__(self):
        super().__init__()
        self.created_at = None
        self.updated_at = None


class AuditableEntity(TimestampedEntity):
    """Auditable entity."""

    def __init__(self):
        super().__init__()
        self.created_by = None
        self.updated_by = None


class VersionedEntity(AuditableEntity):
    """Versioned entity."""

    def __init__(self):
        super().__init__()
        self.version = 0


class SoftDeleteEntity(VersionedEntity):
    """Soft delete entity - deep inheritance."""

    def __init__(self):
        super().__init__()
        self.deleted_at = None
        self.deleted_by = None


# Code smell: Unused import at class level (typing.Any already imported at top)
class OrderItem:
    """Order item model."""

    def __init__(self, product_id: int, quantity: int, price: float):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
        self.subtotal = quantity * price


# Code smell: Property returning wrong type hint
class Order:
    """Order model with type hint issues."""

    def __init__(self):
        self.items: List[OrderItem] = []
        self.status = "pending"

    @property
    def total(self) -> str:  # Bug: Returns float but type hint says str
        return sum(item.subtotal for item in self.items)

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    # Code smell: Method could be static
    def format_currency(self, amount: float) -> str:
        return f"${amount:.2f}"


# Bug: Shadowing built-in
class Report:
    """Report model that shadows built-ins."""

    def __init__(self):
        self.id = None
        self.type = None  # Shadows built-in 'type'
        self.format = None  # Shadows built-in 'format'
        self.list = []  # Shadows built-in 'list'

    def generate(self, format: str = "pdf") -> bytes:  # Parameter shadows built-in
        """Generate report."""
        return b""


# Code smell: Too many return statements
def classify_customer(
    orders: int, total_spent: float, days_since_last_order: int
) -> str:
    """Classify customer with too many return statements."""
    if orders == 0:
        return "new"

    if orders < 3:
        if total_spent < 100:
            return "casual"
        else:
            return "promising"

    if orders < 10:
        if total_spent < 500:
            return "regular"
        elif total_spent < 1000:
            return "loyal"
        else:
            return "vip"

    if days_since_last_order > 365:
        return "lapsed"

    if days_since_last_order > 180:
        return "at_risk"

    if total_spent > 5000:
        return "champion"

    return "active"
