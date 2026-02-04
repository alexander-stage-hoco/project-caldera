//! Rust file with light duplication - small duplicated blocks.

/// User data representation.
#[derive(Clone, Default)]
pub struct UserData {
    pub id: u32,
    pub name: String,
    pub email: String,
    pub active: bool,
    pub created_at: String,
    pub permissions: Vec<String>,
}

/// Process user data with validation.
pub fn process_user_data(user: &UserData) -> UserData {
    UserData {
        id: user.id,
        name: user.name.trim().to_string(),
        email: user.email.to_lowercase().trim().to_string(),
        active: user.active,
        created_at: user.created_at.clone(),
        permissions: Vec::new(),
    }
}

/// Process admin data with validation - light duplication.
pub fn process_admin_data(admin: &UserData) -> UserData {
    UserData {
        id: admin.id,
        name: admin.name.trim().to_string(),
        email: admin.email.to_lowercase().trim().to_string(),
        active: admin.active,
        created_at: admin.created_at.clone(),
        permissions: admin.permissions.clone(),
    }
}

/// Validate email format.
pub fn validate_email(email: &str) -> bool {
    if email.is_empty() {
        return false;
    }
    if !email.contains('@') {
        return false;
    }
    let parts: Vec<&str> = email.split('@').collect();
    if parts.len() != 2 {
        return false;
    }
    if parts[0].is_empty() || parts[1].is_empty() {
        return false;
    }
    if !parts[1].contains('.') {
        return false;
    }
    true
}

/// Format a number as currency.
pub fn format_currency(amount: f64, currency: &str) -> String {
    let symbol = match currency {
        "USD" => "$",
        "EUR" => "E",
        "GBP" => "P",
        _ => currency,
    };
    if amount < 0.0 {
        format!("-{}{:.2}", symbol, amount.abs())
    } else {
        format!("{}{:.2}", symbol, amount)
    }
}

/// Calculate discounted price.
pub fn calculate_discount(price: f64, discount_pct: f64) -> Result<f64, &'static str> {
    if discount_pct < 0.0 || discount_pct > 100.0 {
        return Err("Discount must be between 0 and 100");
    }
    Ok(price * (1.0 - discount_pct / 100.0))
}
