"""Python file with heavy duplication - multiple large duplicated blocks."""


def generate_user_report(users: list[dict]) -> str:
    """Generate a formatted report for users."""
    lines = []
    lines.append("=" * 60)
    lines.append("USER REPORT")
    lines.append("=" * 60)
    lines.append("")

    for item in users:
        lines.append(f"ID: {item.get('id', 'N/A')}")
        lines.append(f"Name: {item.get('name', 'Unknown')}")
        lines.append(f"Email: {item.get('email', 'N/A')}")
        lines.append(f"Status: {item.get('status', 'active')}")
        lines.append(f"Created: {item.get('created_at', 'Unknown')}")
        lines.append("-" * 40)

    lines.append("")
    lines.append(f"Total records: {len(users)}")
    lines.append("=" * 60)
    return "\n".join(lines)


def generate_admin_report(admins: list[dict]) -> str:
    """Generate a formatted report for admins - duplicated structure."""
    lines = []
    lines.append("=" * 60)
    lines.append("ADMIN REPORT")
    lines.append("=" * 60)
    lines.append("")

    for item in admins:
        lines.append(f"ID: {item.get('id', 'N/A')}")
        lines.append(f"Name: {item.get('name', 'Unknown')}")
        lines.append(f"Email: {item.get('email', 'N/A')}")
        lines.append(f"Status: {item.get('status', 'active')}")
        lines.append(f"Created: {item.get('created_at', 'Unknown')}")
        lines.append("-" * 40)

    lines.append("")
    lines.append(f"Total records: {len(admins)}")
    lines.append("=" * 60)
    return "\n".join(lines)


def generate_guest_report(guests: list[dict]) -> str:
    """Generate a formatted report for guests - duplicated structure."""
    lines = []
    lines.append("=" * 60)
    lines.append("GUEST REPORT")
    lines.append("=" * 60)
    lines.append("")

    for item in guests:
        lines.append(f"ID: {item.get('id', 'N/A')}")
        lines.append(f"Name: {item.get('name', 'Unknown')}")
        lines.append(f"Email: {item.get('email', 'N/A')}")
        lines.append(f"Status: {item.get('status', 'active')}")
        lines.append(f"Created: {item.get('created_at', 'Unknown')}")
        lines.append("-" * 40)

    lines.append("")
    lines.append(f"Total records: {len(guests)}")
    lines.append("=" * 60)
    return "\n".join(lines)


def validate_user_input(data: dict) -> list[str]:
    """Validate user input data."""
    errors = []
    if not data.get("name"):
        errors.append("Name is required")
    if not data.get("email"):
        errors.append("Email is required")
    if "@" not in data.get("email", ""):
        errors.append("Invalid email format")
    if not data.get("password"):
        errors.append("Password is required")
    if len(data.get("password", "")) < 8:
        errors.append("Password must be at least 8 characters")
    if not data.get("age"):
        errors.append("Age is required")
    if data.get("age", 0) < 18:
        errors.append("Must be at least 18 years old")
    return errors


def validate_admin_input(data: dict) -> list[str]:
    """Validate admin input data - duplicated validation."""
    errors = []
    if not data.get("name"):
        errors.append("Name is required")
    if not data.get("email"):
        errors.append("Email is required")
    if "@" not in data.get("email", ""):
        errors.append("Invalid email format")
    if not data.get("password"):
        errors.append("Password is required")
    if len(data.get("password", "")) < 8:
        errors.append("Password must be at least 8 characters")
    if not data.get("age"):
        errors.append("Age is required")
    if data.get("age", 0) < 18:
        errors.append("Must be at least 18 years old")
    return errors
