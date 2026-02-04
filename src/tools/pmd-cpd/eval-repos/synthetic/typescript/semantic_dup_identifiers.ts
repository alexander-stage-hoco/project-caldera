/**
 * TypeScript file with semantic duplicates - same logic with different variable names.
 */

interface ProfileData {
    age?: number;
    activityCount?: number;
    purchaseCount?: number;
    referralCount?: number;
    id?: number;
    name?: string;
    email?: string;
    active?: boolean;
    createdAt?: string;
    lastSeen?: string;
}

function calculateUserScore(userData: ProfileData): number {
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

function calculateCustomerRating(customerInfo: ProfileData): number {
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

interface ProcessedRecord {
    identifier?: number;
    fullName?: string;
    emailAddress?: string;
    isActive?: boolean;
    registrationDate?: string;
    lastLogin?: string;
    memberId?: number;
    displayName?: string;
    contactEmail?: string;
    accountStatus?: boolean;
    signupDate?: string;
    recentActivity?: string;
}

function processUserRecord(record: ProfileData): ProcessedRecord {
    return {
        identifier: record.id || 0,
        fullName: (record.name || "").trim(),
        emailAddress: (record.email || "").toLowerCase().trim(),
        isActive: record.active !== false,
        registrationDate: record.createdAt || "",
        lastLogin: record.lastSeen || "",
    };
}

function processMemberEntry(entry: ProfileData): ProcessedRecord {
    return {
        memberId: entry.id || 0,
        displayName: (entry.name || "").trim(),
        contactEmail: (entry.email || "").toLowerCase().trim(),
        accountStatus: entry.active !== false,
        signupDate: entry.createdAt || "",
        recentActivity: entry.lastSeen || "",
    };
}

export { ProfileData, ProcessedRecord, calculateUserScore, calculateCustomerRating, processUserRecord, processMemberEntry };
