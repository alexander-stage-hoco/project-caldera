/**
 * Java file with light duplication - small duplicated blocks.
 */
package synthetic;

import java.util.*;

public class LightDuplication {

    public static Map<String, Object> processUserData(Map<String, Object> user) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", user.getOrDefault("id", 0));
        result.put("name", ((String) user.getOrDefault("name", "")).trim());
        result.put("email", ((String) user.getOrDefault("email", "")).toLowerCase().trim());
        result.put("active", user.getOrDefault("active", true));
        result.put("createdAt", user.getOrDefault("createdAt", ""));
        return result;
    }

    public static Map<String, Object> processAdminData(Map<String, Object> admin) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", admin.getOrDefault("id", 0));
        result.put("name", ((String) admin.getOrDefault("name", "")).trim());
        result.put("email", ((String) admin.getOrDefault("email", "")).toLowerCase().trim());
        result.put("active", admin.getOrDefault("active", true));
        result.put("createdAt", admin.getOrDefault("createdAt", ""));
        result.put("permissions", admin.getOrDefault("permissions", Collections.emptyList()));
        return result;
    }

    public static boolean validateEmail(String email) {
        if (email == null || email.isEmpty()) return false;
        if (!email.contains("@")) return false;
        String[] parts = email.split("@");
        if (parts.length != 2) return false;
        if (parts[0].isEmpty() || parts[1].isEmpty()) return false;
        if (!parts[1].contains(".")) return false;
        return true;
    }

    public static String formatCurrency(double amount, String currency) {
        Map<String, String> symbols = Map.of("USD", "$", "EUR", "E", "GBP", "P");
        String symbol = symbols.getOrDefault(currency, currency);
        if (amount < 0) {
            return String.format("-%s%.2f", symbol, Math.abs(amount));
        }
        return String.format("%s%.2f", symbol, amount);
    }

    public static double calculateDiscount(double price, double discountPct) {
        if (discountPct < 0 || discountPct > 100) {
            throw new IllegalArgumentException("Discount must be between 0 and 100");
        }
        return price * (1 - discountPct / 100);
    }
}
