/**
 * Java file with semantic duplicates - same logic with different variable names.
 */
package synthetic;

import java.util.*;

public class SemanticDupIdentifiers {

    public static double calculateUserScore(Map<String, Object> userData) {
        double baseValue = 100.0;
        int userAge = ((Number) userData.getOrDefault("age", 0)).intValue();
        int userActivity = ((Number) userData.getOrDefault("activityCount", 0)).intValue();
        int userPurchases = ((Number) userData.getOrDefault("purchaseCount", 0)).intValue();
        int userReferrals = ((Number) userData.getOrDefault("referralCount", 0)).intValue();

        if (userAge > 18) baseValue += 10.0;
        if (userAge > 30) baseValue += 5.0;
        if (userActivity > 50) baseValue += 20.0;
        if (userPurchases > 10) baseValue += 15.0;
        if (userReferrals > 5) baseValue += 25.0;

        return Math.min(baseValue, 200.0);
    }

    public static double calculateCustomerRating(Map<String, Object> customerInfo) {
        double startingScore = 100.0;
        int customerYears = ((Number) customerInfo.getOrDefault("age", 0)).intValue();
        int customerInteractions = ((Number) customerInfo.getOrDefault("activityCount", 0)).intValue();
        int customerOrders = ((Number) customerInfo.getOrDefault("purchaseCount", 0)).intValue();
        int customerInvites = ((Number) customerInfo.getOrDefault("referralCount", 0)).intValue();

        if (customerYears > 18) startingScore += 10.0;
        if (customerYears > 30) startingScore += 5.0;
        if (customerInteractions > 50) startingScore += 20.0;
        if (customerOrders > 10) startingScore += 15.0;
        if (customerInvites > 5) startingScore += 25.0;

        return Math.min(startingScore, 200.0);
    }

    public static Map<String, Object> processUserRecord(Map<String, Object> record) {
        Map<String, Object> result = new HashMap<>();
        result.put("identifier", record.getOrDefault("id", 0));
        result.put("fullName", ((String) record.getOrDefault("name", "")).trim());
        result.put("emailAddress", ((String) record.getOrDefault("email", "")).toLowerCase().trim());
        result.put("isActive", record.getOrDefault("active", true));
        result.put("registrationDate", record.getOrDefault("createdAt", ""));
        result.put("lastLogin", record.getOrDefault("lastSeen", ""));
        return result;
    }

    public static Map<String, Object> processMemberEntry(Map<String, Object> entry) {
        Map<String, Object> output = new HashMap<>();
        output.put("memberId", entry.getOrDefault("id", 0));
        output.put("displayName", ((String) entry.getOrDefault("name", "")).trim());
        output.put("contactEmail", ((String) entry.getOrDefault("email", "")).toLowerCase().trim());
        output.put("accountStatus", entry.getOrDefault("active", true));
        output.put("signupDate", entry.getOrDefault("createdAt", ""));
        output.put("recentActivity", entry.getOrDefault("lastSeen", ""));
        return output;
    }
}
