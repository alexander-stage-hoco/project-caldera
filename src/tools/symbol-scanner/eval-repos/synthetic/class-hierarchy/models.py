"""Class hierarchy test repo - classes, methods, and inheritance."""

from abc import ABC, abstractmethod


class BaseModel(ABC):
    """Abstract base class for models."""

    def __init__(self, name: str):
        """Initialize the model."""
        self.name = name

    @abstractmethod
    def validate(self) -> bool:
        """Validate the model."""
        ...

    def display(self) -> str:
        """Return display string."""
        return f"Model: {self.name}"


class User(BaseModel):
    """User model."""

    def __init__(self, name: str, email: str):
        """Initialize user."""
        super().__init__(name)
        self.email = email

    def validate(self) -> bool:
        """Validate user data."""
        return "@" in self.email

    def send_notification(self, message: str) -> None:
        """Send a notification to the user."""
        print(f"Sending to {self.email}: {message}")


class Admin(User):
    """Admin user model."""

    def __init__(self, name: str, email: str, permissions: list[str]):
        """Initialize admin."""
        super().__init__(name, email)
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """Check if admin has permission."""
        return permission in self.permissions


def create_user(name: str, email: str) -> User:
    """Factory function to create a user."""
    user = User(name, email)
    if user.validate():
        return user
    raise ValueError("Invalid user data")
