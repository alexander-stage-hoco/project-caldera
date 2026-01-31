"""
Test file with NO code smells.
Used to validate Semgrep doesn't report false positives.
"""

import logging
from dataclasses import dataclass
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class User:
    """A simple user data class."""
    id: int
    name: str
    email: str


class UserService:
    """Clean service class with proper exception handling."""

    def __init__(self, repository):
        self._repository = repository

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID with proper error handling."""
        try:
            return self._repository.find_by_id(user_id)
        except ConnectionError as e:
            logger.error(f"Database connection failed: {e}")
            raise
        except ValueError as e:
            logger.warning(f"Invalid user ID {user_id}: {e}")
            return None

    def create_user(self, name: str, email: str) -> User:
        """Create a new user with validation."""
        if not name or not email:
            raise ValueError("Name and email are required")

        if "@" not in email:
            raise ValueError("Invalid email format")

        user = User(id=0, name=name, email=email)
        return self._repository.save(user)


def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price."""
    if price < 0:
        raise ValueError("Price cannot be negative")

    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")

    discount_amount = price * (discount_percent / 100)
    return round(price - discount_amount, 2)


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"
