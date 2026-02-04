/**
 * Java file A for cross-file duplication detection.
 */
package synthetic;

import java.util.*;

public class CrossFileA {

    public static double calculateOrderTotal(List<Map<String, Object>> items) {
        double total = 0.0;
        for (Map<String, Object> item : items) {
            double price = ((Number) item.getOrDefault("price", 0.0)).doubleValue();
            int quantity = ((Number) item.getOrDefault("quantity", 1)).intValue();
            double discount = ((Number) item.getOrDefault("discount", 0.0)).doubleValue();
            double itemTotal = price * quantity * (1 - discount / 100);
            total += itemTotal;
        }
        return Math.round(total * 100.0) / 100.0;
    }

    private static final Map<String, Double> SHIPPING_RATES = Map.of(
        "US", 5.99,
        "CA", 8.99,
        "UK", 12.99,
        "DE", 14.99,
        "FR", 14.99,
        "AU", 19.99
    );

    public static double applyShippingCost(double subtotal, String country) {
        double baseRate = SHIPPING_RATES.getOrDefault(country, 24.99);
        if (subtotal > 100) return subtotal;
        return subtotal + baseRate;
    }

    private static final Map<String, Double> TAX_RATES = Map.of(
        "CA", 0.0725,
        "NY", 0.08,
        "TX", 0.0625,
        "FL", 0.06,
        "WA", 0.065
    );

    public static double applyTax(double subtotal, String state) {
        double rate = TAX_RATES.getOrDefault(state, 0.0);
        double tax = subtotal * rate;
        return Math.round((subtotal + tax) * 100.0) / 100.0;
    }

    public static String formatOrderSummary(Map<String, Object> order) {
        List<String> lines = new ArrayList<>();
        lines.add("=".repeat(50));
        lines.add("ORDER SUMMARY");
        lines.add("=".repeat(50));
        lines.add("Order ID: " + order.getOrDefault("id", "N/A"));
        lines.add("Customer: " + order.getOrDefault("customerName", "Unknown"));
        lines.add("Date: " + order.getOrDefault("date", "Unknown"));
        lines.add("-".repeat(50));
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) order.getOrDefault("items", Collections.emptyList());
        for (Map<String, Object> item : items) {
            double price = ((Number) item.getOrDefault("price", 0.0)).doubleValue();
            lines.add(String.format("  %s: $%.2f", item.get("name"), price));
        }
        lines.add("-".repeat(50));
        lines.add(String.format("Subtotal: $%.2f", ((Number) order.getOrDefault("subtotal", 0.0)).doubleValue()));
        lines.add(String.format("Shipping: $%.2f", ((Number) order.getOrDefault("shipping", 0.0)).doubleValue()));
        lines.add(String.format("Tax: $%.2f", ((Number) order.getOrDefault("tax", 0.0)).doubleValue()));
        lines.add(String.format("Total: $%.2f", ((Number) order.getOrDefault("total", 0.0)).doubleValue()));
        lines.add("=".repeat(50));
        return String.join("\n", lines);
    }
}
