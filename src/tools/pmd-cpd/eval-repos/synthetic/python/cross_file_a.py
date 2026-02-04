"""Python file A for cross-file duplication detection."""


def calculate_order_total(items: list[dict]) -> float:
    """Calculate total price of all items in an order."""
    total = 0.0
    for item in items:
        price = item.get("price", 0.0)
        quantity = item.get("quantity", 1)
        discount = item.get("discount", 0.0)
        item_total = price * quantity * (1 - discount / 100)
        total += item_total
    return round(total, 2)


def apply_shipping_cost(subtotal: float, country: str) -> float:
    """Apply shipping cost based on country."""
    shipping_rates = {
        "US": 5.99,
        "CA": 8.99,
        "UK": 12.99,
        "DE": 14.99,
        "FR": 14.99,
        "AU": 19.99,
    }
    base_rate = shipping_rates.get(country, 24.99)
    if subtotal > 100:
        return subtotal  # Free shipping over $100
    return subtotal + base_rate


def apply_tax(subtotal: float, state: str) -> float:
    """Apply tax based on state."""
    tax_rates = {
        "CA": 0.0725,
        "NY": 0.08,
        "TX": 0.0625,
        "FL": 0.06,
        "WA": 0.065,
    }
    rate = tax_rates.get(state, 0.0)
    tax = subtotal * rate
    return round(subtotal + tax, 2)


def format_order_summary(order: dict) -> str:
    """Format order summary for display."""
    lines = []
    lines.append("=" * 50)
    lines.append("ORDER SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Order ID: {order.get('id', 'N/A')}")
    lines.append(f"Customer: {order.get('customer_name', 'Unknown')}")
    lines.append(f"Date: {order.get('date', 'Unknown')}")
    lines.append("-" * 50)
    for item in order.get("items", []):
        lines.append(f"  {item.get('name')}: ${item.get('price', 0):.2f}")
    lines.append("-" * 50)
    lines.append(f"Subtotal: ${order.get('subtotal', 0):.2f}")
    lines.append(f"Shipping: ${order.get('shipping', 0):.2f}")
    lines.append(f"Tax: ${order.get('tax', 0):.2f}")
    lines.append(f"Total: ${order.get('total', 0):.2f}")
    lines.append("=" * 50)
    return "\n".join(lines)
