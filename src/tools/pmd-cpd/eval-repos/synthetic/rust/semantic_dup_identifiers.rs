//! Rust file with semantic duplicates - same logic with different variable names.

/// Profile data representation.
pub struct ProfileData {
    pub age: u32,
    pub activity_count: u32,
    pub purchase_count: u32,
    pub referral_count: u32,
    pub id: u32,
    pub name: String,
    pub email: String,
    pub active: bool,
    pub created_at: String,
    pub last_seen: String,
}

/// Calculate score for a user based on profile data.
pub fn calculate_user_score(user_data: &ProfileData) -> f64 {
    let mut base_value = 100.0;
    let user_age = user_data.age;
    let user_activity = user_data.activity_count;
    let user_purchases = user_data.purchase_count;
    let user_referrals = user_data.referral_count;

    if user_age > 18 {
        base_value += 10.0;
    }
    if user_age > 30 {
        base_value += 5.0;
    }
    if user_activity > 50 {
        base_value += 20.0;
    }
    if user_purchases > 10 {
        base_value += 15.0;
    }
    if user_referrals > 5 {
        base_value += 25.0;
    }

    base_value.min(200.0)
}

/// Calculate rating for a customer - semantic duplicate with renamed vars.
pub fn calculate_customer_rating(customer_info: &ProfileData) -> f64 {
    let mut starting_score = 100.0;
    let customer_years = customer_info.age;
    let customer_interactions = customer_info.activity_count;
    let customer_orders = customer_info.purchase_count;
    let customer_invites = customer_info.referral_count;

    if customer_years > 18 {
        starting_score += 10.0;
    }
    if customer_years > 30 {
        starting_score += 5.0;
    }
    if customer_interactions > 50 {
        starting_score += 20.0;
    }
    if customer_orders > 10 {
        starting_score += 15.0;
    }
    if customer_invites > 5 {
        starting_score += 25.0;
    }

    starting_score.min(200.0)
}

/// Processed user record.
pub struct ProcessedRecord {
    pub identifier: u32,
    pub full_name: String,
    pub email_address: String,
    pub is_active: bool,
    pub registration_date: String,
    pub last_login: String,
}

/// Processed member entry.
pub struct ProcessedMember {
    pub member_id: u32,
    pub display_name: String,
    pub contact_email: String,
    pub account_status: bool,
    pub signup_date: String,
    pub recent_activity: String,
}

/// Process a user record with transformations.
pub fn process_user_record(record: &ProfileData) -> ProcessedRecord {
    ProcessedRecord {
        identifier: record.id,
        full_name: record.name.trim().to_string(),
        email_address: record.email.to_lowercase().trim().to_string(),
        is_active: record.active,
        registration_date: record.created_at.clone(),
        last_login: record.last_seen.clone(),
    }
}

/// Process a member entry - semantic duplicate with renamed vars.
pub fn process_member_entry(entry: &ProfileData) -> ProcessedMember {
    ProcessedMember {
        member_id: entry.id,
        display_name: entry.name.trim().to_string(),
        contact_email: entry.email.to_lowercase().trim().to_string(),
        account_status: entry.active,
        signup_date: entry.created_at.clone(),
        recent_activity: entry.last_seen.clone(),
    }
}
