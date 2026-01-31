/**
 * Test file for DD smell A2_HIGH_CYCLOMATIC detection.
 * Contains functions with high cyclomatic complexity.
 */

function calculateShippingCost(weight, distance, shippingType, isFragile, isHazardous, priority, customerTier, destination) {
    /**
     * A2_HIGH_CYCLOMATIC: Function with excessive branching.
     * Cyclomatic complexity > 15.
     */
    let baseCost = 0;

    if (shippingType === 'standard') {
        if (weight < 1) {
            baseCost = 5.0;
        } else if (weight < 5) {
            baseCost = 10.0;
        } else if (weight < 10) {
            baseCost = 15.0;
        } else {
            baseCost = 20.0;
        }

        if (distance < 100) {
            baseCost *= 1.0;
        } else if (distance < 500) {
            baseCost *= 1.5;
        } else if (distance < 1000) {
            baseCost *= 2.0;
        } else {
            baseCost *= 3.0;
        }
    } else if (shippingType === 'express') {
        if (weight < 1) {
            baseCost = 15.0;
        } else if (weight < 5) {
            baseCost = 25.0;
        } else {
            baseCost = 40.0;
        }
        baseCost *= distance < 500 ? 1.5 : 2.5;
    } else if (shippingType === 'overnight') {
        baseCost = 50.0 + (weight * 5);
    }

    if (isFragile) {
        if (shippingType === 'standard') {
            baseCost *= 1.25;
        } else if (shippingType === 'express') {
            baseCost *= 1.35;
        } else {
            baseCost *= 1.5;
        }
    }

    if (isHazardous) {
        if (destination === 'US') {
            baseCost += 25.0;
        } else if (['UK', 'CA', 'AU'].includes(destination)) {
            baseCost += 35.0;
        } else {
            baseCost += 50.0;
        }
    }

    if (customerTier === 'gold') {
        baseCost *= 0.8;
    } else if (customerTier === 'silver') {
        baseCost *= 0.9;
    } else if (customerTier === 'bronze') {
        baseCost *= 0.95;
    }

    if (priority === 'high') {
        baseCost += 10.0;
    } else if (priority === 'critical') {
        baseCost += 25.0;
    }

    return Math.round(baseCost * 100) / 100;
}


function validateFormData(data) {
    /**
     * A3_DEEP_NESTING: Function with deep nesting.
     */
    const errors = [];

    if (data) {
        if (data.user) {
            if (data.user.email) {
                if (data.user.email.length > 0) {
                    if (!data.user.email.includes('@')) {
                        errors.push('Invalid email');
                    } else {
                        if (data.user.email.length > 100) {
                            errors.push('Email too long');
                        }
                    }
                } else {
                    errors.push('Empty email');
                }
            } else {
                errors.push('Missing email');
            }
        } else {
            errors.push('Empty user object');
        }
    } else {
        errors.push('No data provided');
    }

    return { valid: errors.length === 0, errors };
}


function processTransaction(amount, currency, paymentMethod, cardType, bankCode, isRecurring, retryCount) {
    /**
     * A2_HIGH_CYCLOMATIC: Another high complexity function.
     */
    const result = { status: 'pending', message: '' };

    if (amount <= 0) {
        result.status = 'error';
        result.message = 'Invalid amount';
        return result;
    }

    if (!['USD', 'EUR', 'GBP', 'JPY'].includes(currency)) {
        result.status = 'error';
        result.message = 'Unsupported currency';
        return result;
    }

    if (paymentMethod === 'card') {
        if (cardType === 'visa') {
            if (amount > 10000) {
                result.status = isRecurring ? 'approved' : 'pending_review';
            } else {
                result.status = 'approved';
            }
        } else if (cardType === 'mastercard') {
            result.status = amount > 5000 ? 'pending_review' : 'approved';
        } else if (cardType === 'amex') {
            result.status = amount < 15000 ? 'approved' : 'pending_review';
        } else {
            result.status = 'error';
            result.message = 'Unknown card type';
        }
    } else if (paymentMethod === 'bank_transfer') {
        if (bankCode) {
            if (bankCode.startsWith('US')) {
                result.status = 'approved';
            } else if (bankCode.startsWith('EU')) {
                result.status = amount < 50000 ? 'approved' : 'pending_review';
            } else {
                result.status = 'manual_review';
            }
        } else {
            result.status = 'error';
            result.message = 'Bank code required';
        }
    } else if (paymentMethod === 'crypto') {
        if (currency === 'USD') {
            result.status = 'approved';
        } else {
            result.status = 'error';
            result.message = 'Crypto only accepts USD';
        }
    } else {
        result.status = 'error';
        result.message = 'Unknown payment method';
    }

    result.canRetry = result.status === 'error' && retryCount < 3;

    return result;
}

module.exports = {
    calculateShippingCost,
    validateFormData,
    processTransaction,
};
