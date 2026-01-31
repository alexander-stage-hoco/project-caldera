"""
Test file for DD smell A2_HIGH_CYCLOMATIC detection.
Contains methods with high cyclomatic complexity.
"""


def calculate_shipping_cost(
    weight: float,
    distance: float,
    shipping_type: str,
    is_fragile: bool,
    is_hazardous: bool,
    priority: str,
    customer_tier: str,
    destination_country: str,
) -> float:
    """
    A2_HIGH_CYCLOMATIC: Method with excessive branching.
    Cyclomatic complexity > 15.
    """
    base_cost = 0.0

    # Many nested conditions create high complexity
    if shipping_type == "standard":
        if weight < 1:
            base_cost = 5.0
        elif weight < 5:
            base_cost = 10.0
        elif weight < 10:
            base_cost = 15.0
        else:
            base_cost = 20.0

        if distance < 100:
            base_cost *= 1.0
        elif distance < 500:
            base_cost *= 1.5
        elif distance < 1000:
            base_cost *= 2.0
        else:
            base_cost *= 3.0

    elif shipping_type == "express":
        if weight < 1:
            base_cost = 15.0
        elif weight < 5:
            base_cost = 25.0
        else:
            base_cost = 40.0

        base_cost *= 1.5 if distance < 500 else 2.5

    elif shipping_type == "overnight":
        base_cost = 50.0 + (weight * 5)

    # More branches
    if is_fragile:
        if shipping_type == "standard":
            base_cost *= 1.25
        elif shipping_type == "express":
            base_cost *= 1.35
        else:
            base_cost *= 1.5

    if is_hazardous:
        if destination_country == "US":
            base_cost += 25.0
        elif destination_country in ["UK", "CA", "AU"]:
            base_cost += 35.0
        else:
            base_cost += 50.0

    # Customer tier discounts
    if customer_tier == "gold":
        base_cost *= 0.8
    elif customer_tier == "silver":
        base_cost *= 0.9
    elif customer_tier == "bronze":
        base_cost *= 0.95

    # Priority handling
    if priority == "high":
        base_cost += 10.0
    elif priority == "critical":
        base_cost += 25.0

    return round(base_cost, 2)


def validate_form_data(data: dict) -> tuple[bool, list]:
    """
    A3_DEEP_NESTING: Method with deep nesting.
    """
    errors = []

    if data:
        if "user" in data:
            if data["user"]:
                if "email" in data["user"]:
                    if data["user"]["email"]:
                        if "@" not in data["user"]["email"]:
                            errors.append("Invalid email")
                        else:
                            if len(data["user"]["email"]) > 100:
                                errors.append("Email too long")
                    else:
                        errors.append("Empty email")
                else:
                    errors.append("Missing email")
            else:
                errors.append("Empty user object")
        else:
            errors.append("Missing user field")
    else:
        errors.append("No data provided")

    return len(errors) == 0, errors


def process_transaction(
    amount: float,
    currency: str,
    payment_method: str,
    card_type: str = None,
    bank_code: str = None,
    is_recurring: bool = False,
    retry_count: int = 0,
) -> dict:
    """
    A2_HIGH_CYCLOMATIC: Another high complexity method.
    """
    result = {"status": "pending", "message": ""}

    if amount <= 0:
        result["status"] = "error"
        result["message"] = "Invalid amount"
        return result

    if currency not in ["USD", "EUR", "GBP", "JPY"]:
        result["status"] = "error"
        result["message"] = "Unsupported currency"
        return result

    if payment_method == "card":
        if card_type == "visa":
            if amount > 10000:
                if not is_recurring:
                    result["status"] = "pending_review"
                else:
                    result["status"] = "approved"
            else:
                result["status"] = "approved"
        elif card_type == "mastercard":
            if amount > 5000:
                result["status"] = "pending_review"
            else:
                result["status"] = "approved"
        elif card_type == "amex":
            result["status"] = "approved" if amount < 15000 else "pending_review"
        else:
            result["status"] = "error"
            result["message"] = "Unknown card type"

    elif payment_method == "bank_transfer":
        if bank_code:
            if bank_code.startswith("US"):
                result["status"] = "approved"
            elif bank_code.startswith("EU"):
                if amount < 50000:
                    result["status"] = "approved"
                else:
                    result["status"] = "pending_review"
            else:
                result["status"] = "manual_review"
        else:
            result["status"] = "error"
            result["message"] = "Bank code required"

    elif payment_method == "crypto":
        if currency == "USD":
            result["status"] = "approved"
        else:
            result["status"] = "error"
            result["message"] = "Crypto only accepts USD"

    else:
        result["status"] = "error"
        result["message"] = "Unknown payment method"

    # Retry logic adds more complexity
    if result["status"] == "error" and retry_count < 3:
        result["can_retry"] = True
    else:
        result["can_retry"] = False

    return result
