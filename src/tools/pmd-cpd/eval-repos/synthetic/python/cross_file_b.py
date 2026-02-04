"""Python file B for cross-file duplication detection - contains duplicate code from file A."""


def calculate_invoice_total(items: list[dict]) -> float:
    """Calculate total price of all items in an invoice - duplicate of order total."""
    total = 0.0
    for item in items:
        price = item.get("price", 0.0)
        quantity = item.get("quantity", 1)
        discount = item.get("discount", 0.0)
        item_total = price * quantity * (1 - discount / 100)
        total += item_total
    return round(total, 2)


def apply_delivery_cost(subtotal: float, country: str) -> float:
    """Apply delivery cost based on country - duplicate of shipping cost."""
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


def apply_vat(subtotal: float, state: str) -> float:
    """Apply VAT based on state - duplicate of tax."""
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


def format_invoice_summary(invoice: dict) -> str:
    """Format invoice summary for display - duplicate of order summary."""
    lines = []
    lines.append("=" * 50)
    lines.append("INVOICE SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Invoice ID: {invoice.get('id', 'N/A')}")
    lines.append(f"Customer: {invoice.get('customer_name', 'Unknown')}")
    lines.append(f"Date: {invoice.get('date', 'Unknown')}")
    lines.append("-" * 50)
    for item in invoice.get("items", []):
        lines.append(f"  {item.get('name')}: ${item.get('price', 0):.2f}")
    lines.append("-" * 50)
    lines.append(f"Subtotal: ${invoice.get('subtotal', 0):.2f}")
    lines.append(f"Shipping: ${invoice.get('shipping', 0):.2f}")
    lines.append(f"Tax: ${invoice.get('tax', 0):.2f}")
    lines.append(f"Total: ${invoice.get('total', 0):.2f}")
    lines.append("=" * 50)
    return "\n".join(lines)
