/**
 * JavaScript file with semantic duplicates - same logic with different variable names.
 * These should NOT be detected in standard mode but SHOULD be detected
 * with --ignore-identifiers flag.
 */

function calculateUserScore(userData) {
    let baseValue = 100.0;
    const userAge = userData.age || 0;
    const userActivity = userData.activityCount || 0;
    const userPurchases = userData.purchaseCount || 0;
    const userReferrals = userData.referralCount || 0;

    if (userAge > 18) baseValue += 10.0;
    if (userAge > 30) baseValue += 5.0;
    if (userActivity > 50) baseValue += 20.0;
    if (userPurchases > 10) baseValue += 15.0;
    if (userReferrals > 5) baseValue += 25.0;

    return Math.min(baseValue, 200.0);
}

function calculateCustomerRating(customerInfo) {
    let startingScore = 100.0;
    const customerYears = customerInfo.age || 0;
    const customerInteractions = customerInfo.activityCount || 0;
    const customerOrders = customerInfo.purchaseCount || 0;
    const customerInvites = customerInfo.referralCount || 0;

    if (customerYears > 18) startingScore += 10.0;
    if (customerYears > 30) startingScore += 5.0;
    if (customerInteractions > 50) startingScore += 20.0;
    if (customerOrders > 10) startingScore += 15.0;
    if (customerInvites > 5) startingScore += 25.0;

    return Math.min(startingScore, 200.0);
}

function processUserRecord(record) {
    return {
        identifier: record.id || 0,
        fullName: (record.name || "").trim(),
        emailAddress: (record.email || "").toLowerCase().trim(),
        isActive: record.active !== false,
        registrationDate: record.createdAt || "",
        lastLogin: record.lastSeen || "",
    };
}

function processMemberEntry(entry) {
    return {
        memberId: entry.id || 0,
        displayName: (entry.name || "").trim(),
        contactEmail: (entry.email || "").toLowerCase().trim(),
        accountStatus: entry.active !== false,
        signupDate: entry.createdAt || "",
        recentActivity: entry.lastSeen || "",
    };
}

module.exports = { calculateUserScore, calculateCustomerRating, processUserRecord, processMemberEntry };
