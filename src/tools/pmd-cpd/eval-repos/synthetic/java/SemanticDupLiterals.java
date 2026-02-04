/**
 * Java file with semantic duplicates - same logic with different literal values.
 */
package synthetic;

import java.util.*;
import java.util.regex.*;

public class SemanticDupLiterals {

    public static double calculateBronzeTierDiscount(double price) {
        double baseDiscount = 5.0;
        double maxDiscount = 15.0;
        double threshold = 100.0;

        if (price < threshold) {
            return price * (1 - baseDiscount / 100);
        }

        double additional = (price - threshold) * 0.02;
        double totalDiscount = Math.min(baseDiscount + additional, maxDiscount);
        return price * (1 - totalDiscount / 100);
    }

    public static double calculateSilverTierDiscount(double price) {
        double baseDiscount = 10.0;
        double maxDiscount = 25.0;
        double threshold = 150.0;

        if (price < threshold) {
            return price * (1 - baseDiscount / 100);
        }

        double additional = (price - threshold) * 0.02;
        double totalDiscount = Math.min(baseDiscount + additional, maxDiscount);
        return price * (1 - totalDiscount / 100);
    }

    public static double calculateGoldTierDiscount(double price) {
        double baseDiscount = 15.0;
        double maxDiscount = 35.0;
        double threshold = 200.0;

        if (price < threshold) {
            return price * (1 - baseDiscount / 100);
        }

        double additional = (price - threshold) * 0.02;
        double totalDiscount = Math.min(baseDiscount + additional, maxDiscount);
        return price * (1 - totalDiscount / 100);
    }

    public static List<String> validateUsAddress(Map<String, String> address) {
        List<String> errors = new ArrayList<>();
        List<String> requiredFields = List.of("street", "city", "state", "zip");
        Pattern statePattern = Pattern.compile("^[A-Z]{2}$");
        Pattern zipPattern = Pattern.compile("^\\d{5}(-\\d{4})?$");

        for (String field : requiredFields) {
            String value = address.get(field);
            if (value == null || value.isEmpty()) {
                errors.add(Character.toUpperCase(field.charAt(0)) + field.substring(1) + " is required");
            }
        }

        String state = address.get("state");
        if (state != null && !statePattern.matcher(state).matches()) {
            errors.add("State must be 2 letter code");
        }
        String zip = address.get("zip");
        if (zip != null && !zipPattern.matcher(zip).matches()) {
            errors.add("ZIP must be 5 digits");
        }

        return errors;
    }

    public static List<String> validateCaAddress(Map<String, String> address) {
        List<String> errors = new ArrayList<>();
        List<String> requiredFields = List.of("street", "city", "province", "postalCode");
        Pattern provincePattern = Pattern.compile("^[A-Z]{2}$");
        Pattern postalPattern = Pattern.compile("^[A-Z]\\d[A-Z] ?\\d[A-Z]\\d$");

        for (String field : requiredFields) {
            String value = address.get(field);
            if (value == null || value.isEmpty()) {
                errors.add(Character.toUpperCase(field.charAt(0)) + field.substring(1) + " is required");
            }
        }

        String province = address.get("province");
        if (province != null && !provincePattern.matcher(province).matches()) {
            errors.add("Province must be 2 letter code");
        }
        String postalCode = address.get("postalCode");
        if (postalCode != null && !postalPattern.matcher(postalCode).matches()) {
            errors.add("Postal code must be A1A 1A1 format");
        }

        return errors;
    }
}
