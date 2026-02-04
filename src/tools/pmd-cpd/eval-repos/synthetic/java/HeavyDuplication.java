/**
 * Java file with heavy duplication - multiple large duplicated blocks.
 */
package synthetic;

import java.util.*;

public class HeavyDuplication {

    public static String generateUserReport(List<Map<String, Object>> users) {
        List<String> lines = new ArrayList<>();
        lines.add("=".repeat(60));
        lines.add("USER REPORT");
        lines.add("=".repeat(60));
        lines.add("");

        for (Map<String, Object> item : users) {
            lines.add("ID: " + item.getOrDefault("id", "N/A"));
            lines.add("Name: " + item.getOrDefault("name", "Unknown"));
            lines.add("Email: " + item.getOrDefault("email", "N/A"));
            lines.add("Status: " + item.getOrDefault("status", "active"));
            lines.add("Created: " + item.getOrDefault("createdAt", "Unknown"));
            lines.add("-".repeat(40));
        }

        lines.add("");
        lines.add("Total records: " + users.size());
        lines.add("=".repeat(60));
        return String.join("\n", lines);
    }

    public static String generateAdminReport(List<Map<String, Object>> admins) {
        List<String> lines = new ArrayList<>();
        lines.add("=".repeat(60));
        lines.add("ADMIN REPORT");
        lines.add("=".repeat(60));
        lines.add("");

        for (Map<String, Object> item : admins) {
            lines.add("ID: " + item.getOrDefault("id", "N/A"));
            lines.add("Name: " + item.getOrDefault("name", "Unknown"));
            lines.add("Email: " + item.getOrDefault("email", "N/A"));
            lines.add("Status: " + item.getOrDefault("status", "active"));
            lines.add("Created: " + item.getOrDefault("createdAt", "Unknown"));
            lines.add("-".repeat(40));
        }

        lines.add("");
        lines.add("Total records: " + admins.size());
        lines.add("=".repeat(60));
        return String.join("\n", lines);
    }

    public static String generateGuestReport(List<Map<String, Object>> guests) {
        List<String> lines = new ArrayList<>();
        lines.add("=".repeat(60));
        lines.add("GUEST REPORT");
        lines.add("=".repeat(60));
        lines.add("");

        for (Map<String, Object> item : guests) {
            lines.add("ID: " + item.getOrDefault("id", "N/A"));
            lines.add("Name: " + item.getOrDefault("name", "Unknown"));
            lines.add("Email: " + item.getOrDefault("email", "N/A"));
            lines.add("Status: " + item.getOrDefault("status", "active"));
            lines.add("Created: " + item.getOrDefault("createdAt", "Unknown"));
            lines.add("-".repeat(40));
        }

        lines.add("");
        lines.add("Total records: " + guests.size());
        lines.add("=".repeat(60));
        return String.join("\n", lines);
    }

    public static List<String> validateUserInput(Map<String, Object> data) {
        List<String> errors = new ArrayList<>();
        if (data.get("name") == null) errors.add("Name is required");
        if (data.get("email") == null) errors.add("Email is required");
        String email = (String) data.getOrDefault("email", "");
        if (!email.contains("@")) errors.add("Invalid email format");
        if (data.get("password") == null) errors.add("Password is required");
        String password = (String) data.getOrDefault("password", "");
        if (password.length() < 8) errors.add("Password must be at least 8 characters");
        if (data.get("age") == null) errors.add("Age is required");
        Integer age = (Integer) data.getOrDefault("age", 0);
        if (age < 18) errors.add("Must be at least 18 years old");
        return errors;
    }

    public static List<String> validateAdminInput(Map<String, Object> data) {
        List<String> errors = new ArrayList<>();
        if (data.get("name") == null) errors.add("Name is required");
        if (data.get("email") == null) errors.add("Email is required");
        String email = (String) data.getOrDefault("email", "");
        if (!email.contains("@")) errors.add("Invalid email format");
        if (data.get("password") == null) errors.add("Password is required");
        String password = (String) data.getOrDefault("password", "");
        if (password.length() < 8) errors.add("Password must be at least 8 characters");
        if (data.get("age") == null) errors.add("Age is required");
        Integer age = (Integer) data.getOrDefault("age", 0);
        if (age < 18) errors.add("Must be at least 18 years old");
        return errors;
    }
}
