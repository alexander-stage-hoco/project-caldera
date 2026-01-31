"""
Utility module with code smells and maintainability issues.
For SonarQube testing of Python code quality analysis.
"""

import re
from typing import Any, Dict, List, Optional, Union


# Code smell: God class with too many responsibilities
class UtilityManager:
    """A class that does too many things - violates Single Responsibility."""

    def __init__(self):
        self.string_cache = {}
        self.number_cache = {}
        self.object_cache = {}
        self.config = {}
        self.logger = None
        self.metrics = {}

    # String utilities
    def format_string(self, template: str, **kwargs) -> str:
        return template.format(**kwargs)

    def truncate_string(self, s: str, max_length: int) -> str:
        if len(s) > max_length:
            return s[: max_length - 3] + "..."
        return s

    def slugify(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[-\s]+", "-", s)
        return s.strip("-")

    def capitalize_words(self, s: str) -> str:
        return " ".join(word.capitalize() for word in s.split())

    # Number utilities
    def round_to(self, n: float, decimals: int) -> float:
        return round(n, decimals)

    def clamp(self, n: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(n, max_val))

    def percentage(self, part: float, whole: float) -> float:
        if whole == 0:
            return 0.0
        return (part / whole) * 100

    def average(self, numbers: List[float]) -> float:
        if not numbers:
            return 0.0
        return sum(numbers) / len(numbers)

    # Date utilities (simplified)
    def format_date(self, date_str: str, format: str) -> str:
        # Simplified - just returns the input
        return date_str

    def parse_date(self, date_str: str) -> Optional[str]:
        # Simplified
        return date_str if date_str else None

    # Config utilities
    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        self.config[key] = value

    # Cache utilities
    def cache_get(self, cache_type: str, key: str) -> Optional[Any]:
        cache = getattr(self, f"{cache_type}_cache", {})
        return cache.get(key)

    def cache_set(self, cache_type: str, key: str, value: Any) -> None:
        cache = getattr(self, f"{cache_type}_cache", {})
        cache[key] = value

    def cache_clear(self, cache_type: str) -> None:
        cache = getattr(self, f"{cache_type}_cache", {})
        cache.clear()

    # Logging utilities
    def log_info(self, message: str) -> None:
        if self.logger:
            self.logger.info(message)

    def log_error(self, message: str) -> None:
        if self.logger:
            self.logger.error(message)

    # Metrics utilities
    def record_metric(self, name: str, value: float) -> None:
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_metric_average(self, name: str) -> float:
        values = self.metrics.get(name, [])
        return self.average(values)


# Code smell: Duplicate function implementations
def validate_email_v1(email: str) -> bool:
    """Validate email - version 1."""
    if not email:
        return False
    if "@" not in email:
        return False
    if "." not in email:
        return False
    if len(email) < 5:
        return False
    if len(email) > 254:
        return False
    return True


def validate_email_v2(email: str) -> bool:
    """Validate email - version 2 (duplicate logic)."""
    if not email:
        return False
    if "@" not in email:
        return False
    if "." not in email:
        return False
    if len(email) < 5:
        return False
    if len(email) > 254:
        return False
    return True


# Code smell: Magic numbers
def calculate_shipping(weight: float, distance: float) -> float:
    """Calculate shipping cost with magic numbers."""
    base_cost = 5.99  # Magic number
    weight_factor = 0.5  # Magic number
    distance_factor = 0.1  # Magic number
    tax_rate = 0.08  # Magic number

    subtotal = base_cost + (weight * weight_factor) + (distance * distance_factor)
    return subtotal * (1 + tax_rate)


# Code smell: Long parameter list
def create_order(
    customer_id: int,
    customer_name: str,
    customer_email: str,
    shipping_address: str,
    billing_address: str,
    items: List[Dict],
    discount_code: Optional[str],
    payment_method: str,
    currency: str,
    notes: str,
) -> Dict:
    """Create order with too many parameters."""
    return {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "shipping_address": shipping_address,
        "billing_address": billing_address,
        "items": items,
        "discount_code": discount_code,
        "payment_method": payment_method,
        "currency": currency,
        "notes": notes,
    }


# Code smell: Commented out code
def process_payment(amount: float, method: str) -> bool:
    """Process payment with commented out code."""
    # Old implementation:
    # if method == "credit":
    #     return process_credit_card(amount)
    # elif method == "debit":
    #     return process_debit_card(amount)
    # elif method == "paypal":
    #     return process_paypal(amount)

    # New simplified implementation:
    return True


# Bug: Comparison with None using ==
def check_value(value: Optional[str]) -> str:
    """Check value - uses == None instead of is None."""
    if value == None:  # Bug: should use 'is None'
        return "empty"
    return value


# Bug: Mutable default argument
def append_item(item: str, items: List[str] = []) -> List[str]:
    """Append item with mutable default argument bug."""
    items.append(item)
    return items
