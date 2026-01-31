package synthetic.edge_cases;

import java.util.HashMap;
import java.util.Map;

/**
 * Unicode content test file.
 */
public class Unicode {

    // Unicode in strings
    public static final String GREETING = "Hello, 世界! 🌍";
    public static final String EMOJI_MATH = "1️⃣ + 2️⃣ = 3️⃣";

    // Various Unicode characters
    private static final Map<String, String> TRANSLATIONS = new HashMap<>();

    static {
        TRANSLATIONS.put("hello", "你好");
        TRANSLATIONS.put("world", "мир");
        TRANSLATIONS.put("welcome", "مرحبا");
        TRANSLATIONS.put("goodbye", "さようなら");
        TRANSLATIONS.put("thanks", "धन्यवाद");
    }

    public static String getTranslation(String key) {
        return TRANSLATIONS.getOrDefault(key, null);
    }

    public static String formatGreeting(String name) {
        return "Привет, " + name + "! 👋 Welcome to 日本!";
    }

    public static String getStatus(boolean success) {
        return success ? "✅ Success" : "❌ Failed";
    }

    public static int countEmojis(String text) {
        int count = 0;
        for (int i = 0; i < text.length(); ) {
            int codePoint = text.codePointAt(i);
            if (codePoint >= 0x1F300 && codePoint <= 0x1F9FF) {
                count++;
            }
            i += Character.charCount(codePoint);
        }
        return count;
    }
}
