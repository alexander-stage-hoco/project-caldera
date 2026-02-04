/**
 * JavaScript file A for cross-file duplication detection.
 */

function calculateOrderTotal(items) {
    let total = 0.0;
    for (const item of items) {
        const price = item.price || 0.0;
        const quantity = item.quantity || 1;
        const discount = item.discount || 0.0;
        const itemTotal = price * quantity * (1 - discount / 100);
        total += itemTotal;
    }
    return Math.round(total * 100) / 100;
}

function applyShippingCost(subtotal, country) {
    const shippingRates = {
        US: 5.99,
        CA: 8.99,
        UK: 12.99,
        DE: 14.99,
        FR: 14.99,
        AU: 19.99,
    };
    const baseRate = shippingRates[country] || 24.99;
    if (subtotal > 100) return subtotal;
    return subtotal + baseRate;
}

function applyTax(subtotal, state) {
    const taxRates = {
        CA: 0.0725,
        NY: 0.08,
        TX: 0.0625,
        FL: 0.06,
        WA: 0.065,
    };
    const rate = taxRates[state] || 0.0;
    const tax = subtotal * rate;
    return Math.round((subtotal + tax) * 100) / 100;
}

function formatOrderSummary(order) {
    const lines = [];
    lines.push("=".repeat(50));
    lines.push("ORDER SUMMARY");
    lines.push("=".repeat(50));
    lines.push(`Order ID: ${order.id || "N/A"}`);
    lines.push(`Customer: ${order.customerName || "Unknown"}`);
    lines.push(`Date: ${order.date || "Unknown"}`);
    lines.push("-".repeat(50));
    for (const item of order.items || []) {
        lines.push(`  ${item.name}: $${(item.price || 0).toFixed(2)}`);
    }
    lines.push("-".repeat(50));
    lines.push(`Subtotal: $${(order.subtotal || 0).toFixed(2)}`);
    lines.push(`Shipping: $${(order.shipping || 0).toFixed(2)}`);
    lines.push(`Tax: $${(order.tax || 0).toFixed(2)}`);
    lines.push(`Total: $${(order.total || 0).toFixed(2)}`);
    lines.push("=".repeat(50));
    return lines.join("\n");
}

module.exports = { calculateOrderTotal, applyShippingCost, applyTax, formatOrderSummary };
