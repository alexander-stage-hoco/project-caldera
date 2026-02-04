//! Rust file B for cross-file duplication - contains duplicate code from file A.

use std::collections::HashMap;

/// Invoice item representation.
pub struct InvoiceItem {
    pub price: f64,
    pub quantity: u32,
    pub discount: f64,
    pub name: String,
}

/// Invoice representation.
pub struct Invoice {
    pub id: Option<String>,
    pub customer_name: Option<String>,
    pub date: Option<String>,
    pub items: Vec<InvoiceItem>,
    pub subtotal: f64,
    pub shipping: f64,
    pub tax: f64,
    pub total: f64,
}

/// Calculate the total price of items - duplicate of order total.
pub fn calculate_invoice_total(items: &[InvoiceItem]) -> f64 {
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
    static ref DELIVERY_RATES: HashMap<&'static str, f64> = {
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

/// Apply delivery cost based on country - duplicate of shipping cost.
pub fn apply_delivery_cost(subtotal: f64, country: &str) -> f64 {
    let base_rate = DELIVERY_RATES.get(country).copied().unwrap_or(24.99);
    if subtotal > 100.0 {
        return subtotal;
    }
    subtotal + base_rate
}

lazy_static::lazy_static! {
    static ref VAT_RATES: HashMap<&'static str, f64> = {
        let mut m = HashMap::new();
        m.insert("CA", 0.0725);
        m.insert("NY", 0.08);
        m.insert("TX", 0.0625);
        m.insert("FL", 0.06);
        m.insert("WA", 0.065);
        m
    };
}

/// Apply VAT based on state - duplicate of tax.
pub fn apply_vat(subtotal: f64, state: &str) -> f64 {
    let rate = VAT_RATES.get(state).copied().unwrap_or(0.0);
    let tax = subtotal * rate;
    ((subtotal + tax) * 100.0).round() / 100.0
}

/// Format the invoice summary for display - duplicate of order summary.
pub fn format_invoice_summary(invoice: &Invoice) -> String {
    let mut lines = Vec::new();
    lines.push("=".repeat(50));
    lines.push("INVOICE SUMMARY".to_string());
    lines.push("=".repeat(50));
    let id = invoice.id.as_deref().unwrap_or("N/A");
    let customer_name = invoice.customer_name.as_deref().unwrap_or("Unknown");
    let date = invoice.date.as_deref().unwrap_or("Unknown");
    lines.push(format!("Invoice ID: {}", id));
    lines.push(format!("Customer: {}", customer_name));
    lines.push(format!("Date: {}", date));
    lines.push("-".repeat(50));
    for item in &invoice.items {
        lines.push(format!("  {}: ${:.2}", item.name, item.price));
    }
    lines.push("-".repeat(50));
    lines.push(format!("Subtotal: ${:.2}", invoice.subtotal));
    lines.push(format!("Shipping: ${:.2}", invoice.shipping));
    lines.push(format!("Tax: ${:.2}", invoice.tax));
    lines.push(format!("Total: ${:.2}", invoice.total));
    lines.push("=".repeat(50));
    lines.join("\n")
}
