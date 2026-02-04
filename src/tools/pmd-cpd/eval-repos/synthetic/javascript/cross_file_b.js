/**
 * JavaScript file B for cross-file duplication - contains duplicate code from file A.
 */

function calculateInvoiceTotal(items) {
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

function applyDeliveryCost(subtotal, country) {
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

function applyVat(subtotal, state) {
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

function formatInvoiceSummary(invoice) {
    const lines = [];
    lines.push("=".repeat(50));
    lines.push("INVOICE SUMMARY");
    lines.push("=".repeat(50));
    lines.push(`Invoice ID: ${invoice.id || "N/A"}`);
    lines.push(`Customer: ${invoice.customerName || "Unknown"}`);
    lines.push(`Date: ${invoice.date || "Unknown"}`);
    lines.push("-".repeat(50));
    for (const item of invoice.items || []) {
        lines.push(`  ${item.name}: $${(item.price || 0).toFixed(2)}`);
    }
    lines.push("-".repeat(50));
    lines.push(`Subtotal: $${(invoice.subtotal || 0).toFixed(2)}`);
    lines.push(`Shipping: $${(invoice.shipping || 0).toFixed(2)}`);
    lines.push(`Tax: $${(invoice.tax || 0).toFixed(2)}`);
    lines.push(`Total: $${(invoice.total || 0).toFixed(2)}`);
    lines.push("=".repeat(50));
    return lines.join("\n");
}

module.exports = { calculateInvoiceTotal, applyDeliveryCost, applyVat, formatInvoiceSummary };
