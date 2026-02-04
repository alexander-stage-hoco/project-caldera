//! Rust file with semantic duplicates - same logic with different literal values.

use regex::Regex;

/// Calculate discount for bronze tier customers.
pub fn calculate_bronze_tier_discount(price: f64) -> f64 {
    let base_discount = 5.0;
    let max_discount = 15.0;
    let threshold = 100.0;

    if price < threshold {
        return price * (1.0 - base_discount / 100.0);
    }

    let additional = (price - threshold) * 0.02;
    let total_discount = (base_discount + additional).min(max_discount);
    price * (1.0 - total_discount / 100.0)
}

/// Calculate discount for silver tier - semantic duplicate with different literals.
pub fn calculate_silver_tier_discount(price: f64) -> f64 {
    let base_discount = 10.0;
    let max_discount = 25.0;
    let threshold = 150.0;

    if price < threshold {
        return price * (1.0 - base_discount / 100.0);
    }

    let additional = (price - threshold) * 0.02;
    let total_discount = (base_discount + additional).min(max_discount);
    price * (1.0 - total_discount / 100.0)
}

/// Calculate discount for gold tier - semantic duplicate with different literals.
pub fn calculate_gold_tier_discount(price: f64) -> f64 {
    let base_discount = 15.0;
    let max_discount = 35.0;
    let threshold = 200.0;

    if price < threshold {
        return price * (1.0 - base_discount / 100.0);
    }

    let additional = (price - threshold) * 0.02;
    let total_discount = (base_discount + additional).min(max_discount);
    price * (1.0 - total_discount / 100.0)
}

/// Address representation.
pub struct Address {
    pub street: String,
    pub city: String,
    pub state: String,
    pub zip: String,
    pub province: String,
    pub postal_code: String,
}

/// Validate US address format.
pub fn validate_us_address(address: &Address) -> Vec<String> {
    let mut errors = Vec::new();
    let required_fields = ["street", "city", "state", "zip"];
    let state_pattern = Regex::new(r"^[A-Z]{2}$").unwrap();
    let zip_pattern = Regex::new(r"^\d{5}(-\d{4})?$").unwrap();

    for field in &required_fields {
        let value = match *field {
            "street" => &address.street,
            "city" => &address.city,
            "state" => &address.state,
            "zip" => &address.zip,
            _ => continue,
        };
        if value.is_empty() {
            let capitalized = field.chars().next().unwrap().to_uppercase().to_string() + &field[1..];
            errors.push(format!("{} is required", capitalized));
        }
    }

    if !address.state.is_empty() && !state_pattern.is_match(&address.state) {
        errors.push("State must be 2 letter code".to_string());
    }
    if !address.zip.is_empty() && !zip_pattern.is_match(&address.zip) {
        errors.push("ZIP must be 5 digits".to_string());
    }

    errors
}

/// Validate Canadian address - semantic duplicate with different literals.
pub fn validate_ca_address(address: &Address) -> Vec<String> {
    let mut errors = Vec::new();
    let required_fields = ["street", "city", "province", "postal_code"];
    let province_pattern = Regex::new(r"^[A-Z]{2}$").unwrap();
    let postal_pattern = Regex::new(r"^[A-Z]\d[A-Z] ?\d[A-Z]\d$").unwrap();

    for field in &required_fields {
        let value = match *field {
            "street" => &address.street,
            "city" => &address.city,
            "province" => &address.province,
            "postal_code" => &address.postal_code,
            _ => continue,
        };
        if value.is_empty() {
            let capitalized = field.chars().next().unwrap().to_uppercase().to_string() + &field[1..];
            errors.push(format!("{} is required", capitalized));
        }
    }

    if !address.province.is_empty() && !province_pattern.is_match(&address.province) {
        errors.push("Province must be 2 letter code".to_string());
    }
    if !address.postal_code.is_empty() && !postal_pattern.is_match(&address.postal_code) {
        errors.push("Postal code must be A1A 1A1 format".to_string());
    }

    errors
}
