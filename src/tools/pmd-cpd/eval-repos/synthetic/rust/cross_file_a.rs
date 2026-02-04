//! Rust file A for cross-file duplication detection.

use std::collections::HashMap;

/// Order item representation.
pub struct OrderItem {
    pub price: f64,
    pub quantity: u32,
    pub discount: f64,
    pub name: String,
}

/// Order representation.
pub struct Order {
    pub id: Option<String>,
    pub customer_name: Option<String>,
    pub date: Option<String>,
    pub items: Vec<OrderItem>,
    pub subtotal: f64,
    pub shipping: f64,
    pub tax: f64,
    pub total: f64,
}

/// Calculate the total price of items.
pub fn calculate_order_total(items: &[OrderItem]) -> f64 {
    let mut total = 0.0;
    for item in items {
        let price = item.price;
        let quantity = if item.quantity == 0 { 1 } else { item.quantity };
        let discount = item.discount;
        let item_total = price * quantity as f64 * (1.0 - discount / 100.0);
        total += item_total;
    }
    (total * 100.0).round() / 100.0
}

lazy_static::lazy_static! {
    static ref SHIPPING_RATES: HashMap<&'static str, f64> = {
        let mut m = HashMap::new();
        m.insert("US", 5.99);
        m.insert("CA", 8.99);
        m.insert("UK", 12.99);
        m.insert("DE", 14.99);
        m.insert("FR", 14.99);
        m.insert("AU", 19.99);
        m
    };
}

/// Apply shipping cost based on country.
pub fn apply_shipping_cost(subtotal: f64, country: &str) -> f64 {
    let base_rate = SHIPPING_RATES.get(country).copied().unwrap_or(24.99);
    if subtotal > 100.0 {
        return subtotal;
    }
    subtotal + base_rate
}

lazy_static::lazy_static! {
    static ref TAX_RATES: HashMap<&'static str, f64> = {
        let mut m = HashMap::new();
        m.insert("CA", 0.0725);
        m.insert("NY", 0.08);
        m.insert("TX", 0.0625);
        m.insert("FL", 0.06);
        m.insert("WA", 0.065);
        m
    };
}

/// Apply tax based on state.
pub fn apply_tax(subtotal: f64, state: &str) -> f64 {
    let rate = TAX_RATES.get(state).copied().unwrap_or(0.0);
    let tax = subtotal * rate;
    ((subtotal + tax) * 100.0).round() / 100.0
}

/// Format the order summary for display.
pub fn format_order_summary(order: &Order) -> String {
    let mut lines = Vec::new();
    lines.push("=".repeat(50));
    lines.push("ORDER SUMMARY".to_string());
    lines.push("=".repeat(50));
    let id = order.id.as_deref().unwrap_or("N/A");
    let customer_name = order.customer_name.as_deref().unwrap_or("Unknown");
    let date = order.date.as_deref().unwrap_or("Unknown");
    lines.push(format!("Order ID: {}", id));
    lines.push(format!("Customer: {}", customer_name));
    lines.push(format!("Date: {}", date));
    lines.push("-".repeat(50));
    for item in &order.items {
        lines.push(format!("  {}: ${:.2}", item.name, item.price));
    }
    lines.push("-".repeat(50));
    lines.push(format!("Subtotal: ${:.2}", order.subtotal));
    lines.push(format!("Shipping: ${:.2}", order.shipping));
    lines.push(format!("Tax: ${:.2}", order.tax));
    lines.push(format!("Total: ${:.2}", order.total));
    lines.push("=".repeat(50));
    lines.join("\n")
}
