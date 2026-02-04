/**
 * TypeScript file with light duplication - small duplicated blocks.
 */

interface UserData {
    id?: number;
    name?: string;
    email?: string;
    active?: boolean;
    createdAt?: string;
    permissions?: string[];
}

function processUserData(user: UserData): UserData {
    return {
        id: user.id || 0,
        name: (user.name || "").trim(),
        email: (user.email || "").toLowerCase().trim(),
        active: user.active !== false,
        createdAt: user.createdAt || "",
    };
}

function processAdminData(admin: UserData): UserData {
    return {
        id: admin.id || 0,
        name: (admin.name || "").trim(),
        email: (admin.email || "").toLowerCase().trim(),
        active: admin.active !== false,
        createdAt: admin.createdAt || "",
        permissions: admin.permissions || [],
    };
}

function validateEmail(email: string): boolean {
    if (!email) return false;
    if (!email.includes("@")) return false;
    const parts = email.split("@");
    if (parts.length !== 2) return false;
    if (!parts[0] || !parts[1]) return false;
    if (!parts[1].includes(".")) return false;
    return true;
}

function formatCurrency(amount: number, currency: string = "USD"): string {
    const symbols: Record<string, string> = { USD: "$", EUR: "E", GBP: "P" };
    const symbol = symbols[currency] || currency;
    if (amount < 0) {
        return `-${symbol}${Math.abs(amount).toFixed(2)}`;
    }
    return `${symbol}${amount.toFixed(2)}`;
}

function calculateDiscount(price: number, discountPct: number): number {
    if (discountPct < 0 || discountPct > 100) {
        throw new Error("Discount must be between 0 and 100");
    }
    return price * (1 - discountPct / 100);
}

export { UserData, processUserData, processAdminData, validateEmail, formatCurrency, calculateDiscount };
