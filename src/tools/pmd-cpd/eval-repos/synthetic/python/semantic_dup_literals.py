"""Python file with semantic duplicates - same logic with different literal values.

These should NOT be detected in standard mode but SHOULD be detected
with --ignore-literals flag (semantic mode).
"""


def calculate_bronze_tier_discount(price: float) -> float:
    """Calculate discount for bronze tier customers."""
    base_discount = 5.0
    max_discount = 15.0
    threshold = 100.0

    if price < threshold:
        return price * (1 - base_discount / 100)

    additional = (price - threshold) * 0.02
    total_discount = min(base_discount + additional, max_discount)
    return price * (1 - total_discount / 100)


def calculate_silver_tier_discount(price: float) -> float:
    """Calculate discount for silver tier - semantic duplicate with different literals."""
    base_discount = 10.0
    max_discount = 25.0
    threshold = 150.0

    if price < threshold:
        return price * (1 - base_discount / 100)

    additional = (price - threshold) * 0.02
    total_discount = min(base_discount + additional, max_discount)
    return price * (1 - total_discount / 100)


def calculate_gold_tier_discount(price: float) -> float:
    """Calculate discount for gold tier - semantic duplicate with different literals."""
    base_discount = 15.0
    max_discount = 35.0
    threshold = 200.0

    if price < threshold:
        return price * (1 - base_discount / 100)

    additional = (price - threshold) * 0.02
    total_discount = min(base_discount + additional, max_discount)
    return price * (1 - total_discount / 100)


def validate_us_address(address: dict) -> list[str]:
    """Validate US address format."""
    errors = []
    required_fields = ["street", "city", "state", "zip"]
    state_pattern = r"^[A-Z]{2}$"
    zip_pattern = r"^\d{5}(-\d{4})?$"

    for field in required_fields:
        if not address.get(field):
            errors.append(f"{field.title()} is required")

    import re
    if address.get("state") and not re.match(state_pattern, address["state"]):
        errors.append("State must be 2 letter code")
    if address.get("zip") and not re.match(zip_pattern, address["zip"]):
        errors.append("ZIP must be 5 digits")

    return errors


def validate_ca_address(address: dict) -> list[str]:
    """Validate Canadian address - semantic duplicate with different literals."""
    errors = []
    required_fields = ["street", "city", "province", "postal_code"]
    province_pattern = r"^[A-Z]{2}$"
    postal_pattern = r"^[A-Z]\d[A-Z] ?\d[A-Z]\d$"

    for field in required_fields:
        if not address.get(field):
            errors.append(f"{field.title()} is required")

    import re
    if address.get("province") and not re.match(province_pattern, address["province"]):
        errors.append("Province must be 2 letter code")
    if address.get("postal_code") and not re.match(postal_pattern, address["postal_code"]):
        errors.append("Postal code must be A1A 1A1 format")

    return errors
