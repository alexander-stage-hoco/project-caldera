"""Python file with light duplication - small duplicated blocks."""


def process_user_data(user: dict) -> dict:
    """Process user data with validation."""
    result = {}
    result["id"] = user.get("id", 0)
    result["name"] = user.get("name", "").strip()
    result["email"] = user.get("email", "").lower().strip()
    result["active"] = user.get("active", True)
    result["created_at"] = user.get("created_at", "")
    return result


def process_admin_data(admin: dict) -> dict:
    """Process admin data with validation - light duplication."""
    result = {}
    result["id"] = admin.get("id", 0)
    result["name"] = admin.get("name", "").strip()
    result["email"] = admin.get("email", "").lower().strip()
    result["active"] = admin.get("active", True)
    result["created_at"] = admin.get("created_at", "")
    result["permissions"] = admin.get("permissions", [])
    return result


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    if not parts[0] or not parts[1]:
        return False
    if "." not in parts[1]:
        return False
    return True


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a number as currency."""
    symbols = {"USD": "$", "EUR": "E", "GBP": "P"}
    symbol = symbols.get(currency, currency)
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"


def calculate_discount(price: float, discount_pct: float) -> float:
    """Calculate discounted price."""
    if discount_pct < 0 or discount_pct > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_pct / 100)
