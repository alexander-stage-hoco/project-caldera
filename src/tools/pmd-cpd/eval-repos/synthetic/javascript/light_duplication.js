/**
 * JavaScript file with light duplication - small duplicated blocks.
 */

function processUserData(user) {
    const result = {};
    result.id = user.id || 0;
    result.name = (user.name || "").trim();
    result.email = (user.email || "").toLowerCase().trim();
    result.active = user.active !== false;
    result.createdAt = user.createdAt || "";
    return result;
}

function processAdminData(admin) {
    const result = {};
    result.id = admin.id || 0;
    result.name = (admin.name || "").trim();
    result.email = (admin.email || "").toLowerCase().trim();
    result.active = admin.active !== false;
    result.createdAt = admin.createdAt || "";
    result.permissions = admin.permissions || [];
    return result;
}

function validateEmail(email) {
    if (!email) return false;
    if (!email.includes("@")) return false;
    const parts = email.split("@");
    if (parts.length !== 2) return false;
    if (!parts[0] || !parts[1]) return false;
    if (!parts[1].includes(".")) return false;
    return true;
}

function formatCurrency(amount, currency = "USD") {
    const symbols = { USD: "$", EUR: "E", GBP: "P" };
    const symbol = symbols[currency] || currency;
    if (amount < 0) {
        return `-${symbol}${Math.abs(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `${symbol}${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function calculateDiscount(price, discountPct) {
    if (discountPct < 0 || discountPct > 100) {
        throw new Error("Discount must be between 0 and 100");
    }
    return price * (1 - discountPct / 100);
}

module.exports = { processUserData, processAdminData, validateEmail, formatCurrency, calculateDiscount };
