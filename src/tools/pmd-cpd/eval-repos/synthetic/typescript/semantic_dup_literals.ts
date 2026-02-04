/**
 * TypeScript file with semantic duplicates - same logic with different literal values.
 */

function calculateBronzeTierDiscount(price: number): number {
    const baseDiscount = 5.0;
    const maxDiscount = 15.0;
    const threshold = 100.0;

    if (price < threshold) {
        return price * (1 - baseDiscount / 100);
    }

    const additional = (price - threshold) * 0.02;
    const totalDiscount = Math.min(baseDiscount + additional, maxDiscount);
    return price * (1 - totalDiscount / 100);
}

function calculateSilverTierDiscount(price: number): number {
    const baseDiscount = 10.0;
    const maxDiscount = 25.0;
    const threshold = 150.0;

    if (price < threshold) {
        return price * (1 - baseDiscount / 100);
    }

    const additional = (price - threshold) * 0.02;
    const totalDiscount = Math.min(baseDiscount + additional, maxDiscount);
    return price * (1 - totalDiscount / 100);
}

function calculateGoldTierDiscount(price: number): number {
    const baseDiscount = 15.0;
    const maxDiscount = 35.0;
    const threshold = 200.0;

    if (price < threshold) {
        return price * (1 - baseDiscount / 100);
    }

    const additional = (price - threshold) * 0.02;
    const totalDiscount = Math.min(baseDiscount + additional, maxDiscount);
    return price * (1 - totalDiscount / 100);
}

interface Address {
    street?: string;
    city?: string;
    state?: string;
    zip?: string;
    province?: string;
    postalCode?: string;
}

function validateUsAddress(address: Address): string[] {
    const errors: string[] = [];
    const requiredFields = ["street", "city", "state", "zip"];
    const statePattern = /^[A-Z]{2}$/;
    const zipPattern = /^\d{5}(-\d{4})?$/;

    for (const field of requiredFields) {
        if (!address[field as keyof Address]) {
            errors.push(`${field.charAt(0).toUpperCase() + field.slice(1)} is required`);
        }
    }

    if (address.state && !statePattern.test(address.state)) {
        errors.push("State must be 2 letter code");
    }
    if (address.zip && !zipPattern.test(address.zip)) {
        errors.push("ZIP must be 5 digits");
    }

    return errors;
}

function validateCaAddress(address: Address): string[] {
    const errors: string[] = [];
    const requiredFields = ["street", "city", "province", "postalCode"];
    const provincePattern = /^[A-Z]{2}$/;
    const postalPattern = /^[A-Z]\d[A-Z] ?\d[A-Z]\d$/;

    for (const field of requiredFields) {
        if (!address[field as keyof Address]) {
            errors.push(`${field.charAt(0).toUpperCase() + field.slice(1)} is required`);
        }
    }

    if (address.province && !provincePattern.test(address.province)) {
        errors.push("Province must be 2 letter code");
    }
    if (address.postalCode && !postalPattern.test(address.postalCode)) {
        errors.push("Postal code must be A1A 1A1 format");
    }

    return errors;
}

export { Address, calculateBronzeTierDiscount, calculateSilverTierDiscount, calculateGoldTierDiscount, validateUsAddress, validateCaAddress };
