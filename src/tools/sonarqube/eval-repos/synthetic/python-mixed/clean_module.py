"""
Clean module with no issues.
This module follows Python best practices and should have minimal SonarQube findings.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class User:
    """User model using dataclass for clean implementation."""

    id: int
    username: str
    email: str
    is_active: bool = True


class UserService:
    """User service with clean, well-structured code."""

    def __init__(self, repository):
        """Initialize with dependency injection."""
        self._repository = repository

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID."""
        if user_id <= 0:
            return None
        return self._repository.find(user_id)

    def find_active_users(self) -> List[User]:
        """Find all active users."""
        users = self._repository.find_all()
        return [user for user in users if user.is_active]

    def create_user(self, username: str, email: str) -> User:
        """Create a new user with validation."""
        self._validate_username(username)
        self._validate_email(email)

        user = User(
            id=0,  # Will be set by repository
            username=username,
            email=email,
        )
        return self._repository.save(user)

    def _validate_username(self, username: str) -> None:
        """Validate username."""
        if not username:
            raise ValueError("Username is required")
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(username) > 50:
            raise ValueError("Username must be at most 50 characters")

    def _validate_email(self, email: str) -> None:
        """Validate email address."""
        if not email:
            raise ValueError("Email is required")
        if "@" not in email:
            raise ValueError("Invalid email format")


def calculate_discount(base_price: float, discount_percent: float) -> float:
    """
    Calculate discounted price.

    Args:
        base_price: Original price
        discount_percent: Discount percentage (0-100)

    Returns:
        Discounted price

    Raises:
        ValueError: If inputs are invalid
    """
    if base_price < 0:
        raise ValueError("Base price cannot be negative")
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")

    discount_amount = base_price * (discount_percent / 100)
    return base_price - discount_amount


def chunk_list(items: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks of specified size.

    Args:
        items: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
