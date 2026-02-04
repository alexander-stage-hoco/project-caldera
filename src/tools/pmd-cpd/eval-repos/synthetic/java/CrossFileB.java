/**
 * Java file B for cross-file duplication - contains duplicate code from file A.
 */
package synthetic;

import java.util.*;

public class CrossFileB {

    public static double calculateInvoiceTotal(List<Map<String, Object>> items) {
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

    public static double applyDeliveryCost(double subtotal, String country) {
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

    public static double applyVat(double subtotal, String state) {
        double rate = TAX_RATES.getOrDefault(state, 0.0);
        double tax = subtotal * rate;
        return Math.round((subtotal + tax) * 100.0) / 100.0;
    }

    public static String formatInvoiceSummary(Map<String, Object> invoice) {
        List<String> lines = new ArrayList<>();
        lines.add("=".repeat(50));
        lines.add("INVOICE SUMMARY");
        lines.add("=".repeat(50));
        lines.add("Invoice ID: " + invoice.getOrDefault("id", "N/A"));
        lines.add("Customer: " + invoice.getOrDefault("customerName", "Unknown"));
        lines.add("Date: " + invoice.getOrDefault("date", "Unknown"));
        lines.add("-".repeat(50));
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items = (List<Map<String, Object>>) invoice.getOrDefault("items", Collections.emptyList());
        for (Map<String, Object> item : items) {
            double price = ((Number) item.getOrDefault("price", 0.0)).doubleValue();
            lines.add(String.format("  %s: $%.2f", item.get("name"), price));
        }
        lines.add("-".repeat(50));
        lines.add(String.format("Subtotal: $%.2f", ((Number) invoice.getOrDefault("subtotal", 0.0)).doubleValue()));
        lines.add(String.format("Shipping: $%.2f", ((Number) invoice.getOrDefault("shipping", 0.0)).doubleValue()));
        lines.add(String.format("Tax: $%.2f", ((Number) invoice.getOrDefault("tax", 0.0)).doubleValue()));
        lines.add(String.format("Total: $%.2f", ((Number) invoice.getOrDefault("total", 0.0)).doubleValue()));
        lines.add("=".repeat(50));
        return String.join("\n", lines);
    }
}
