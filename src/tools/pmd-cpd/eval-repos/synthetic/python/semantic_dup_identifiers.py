"""Python file with semantic duplicates - same logic with different variable names.

These should NOT be detected in standard mode but SHOULD be detected
with --ignore-identifiers flag (semantic mode).
"""


def calculate_user_score(user_data: dict) -> float:
    """Calculate score for a user based on profile data."""
    base_value = 100.0
    user_age = user_data.get("age", 0)
    user_activity = user_data.get("activity_count", 0)
    user_purchases = user_data.get("purchase_count", 0)
    user_referrals = user_data.get("referral_count", 0)

    if user_age > 18:
        base_value += 10.0
    if user_age > 30:
        base_value += 5.0
    if user_activity > 50:
        base_value += 20.0
    if user_purchases > 10:
        base_value += 15.0
    if user_referrals > 5:
        base_value += 25.0

    return min(base_value, 200.0)


def calculate_customer_rating(customer_info: dict) -> float:
    """Calculate rating for a customer - semantic duplicate with renamed vars."""
    starting_score = 100.0
    customer_years = customer_info.get("age", 0)
    customer_interactions = customer_info.get("activity_count", 0)
    customer_orders = customer_info.get("purchase_count", 0)
    customer_invites = customer_info.get("referral_count", 0)

    if customer_years > 18:
        starting_score += 10.0
    if customer_years > 30:
        starting_score += 5.0
    if customer_interactions > 50:
        starting_score += 20.0
    if customer_orders > 10:
        starting_score += 15.0
    if customer_invites > 5:
        starting_score += 25.0

    return min(starting_score, 200.0)


def process_user_record(record: dict) -> dict:
    """Process a user record with transformations."""
    result = {}
    result["identifier"] = record.get("id", 0)
    result["full_name"] = record.get("name", "").strip().title()
    result["email_address"] = record.get("email", "").lower().strip()
    result["is_active"] = record.get("active", True)
    result["registration_date"] = record.get("created_at", "")
    result["last_login"] = record.get("last_seen", "")
    return result


def process_member_entry(entry: dict) -> dict:
    """Process a member entry - semantic duplicate with renamed vars."""
    output = {}
    output["member_id"] = entry.get("id", 0)
    output["display_name"] = entry.get("name", "").strip().title()
    output["contact_email"] = entry.get("email", "").lower().strip()
    output["account_status"] = entry.get("active", True)
    output["signup_date"] = entry.get("created_at", "")
    output["recent_activity"] = entry.get("last_seen", "")
    return output
