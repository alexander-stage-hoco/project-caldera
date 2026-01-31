//! Unicode content test file.

/// Unicode in strings
pub const GREETING: &str = "Hello, 世界! 🌍";
pub const EMOJI_MATH: &str = "1️⃣ + 2️⃣ = 3️⃣";

use std::collections::HashMap;

/// Get translations map.
pub fn translations() -> HashMap<&'static str, &'static str> {
    let mut map = HashMap::new();
    map.insert("hello", "你好");
    map.insert("world", "мир");
    map.insert("welcome", "مرحبا");
    map.insert("goodbye", "さようなら");
    map.insert("thanks", "धन्यवाद");
    map
}

/// Get a translation.
pub fn get_translation(key: &str) -> Option<&'static str> {
    translations().get(key).copied()
}

/// Format a greeting with Unicode.
pub fn format_greeting(name: &str) -> String {
    format!("Привет, {}! 👋 Welcome to 日本!", name)
}

/// Get status with emoji.
pub fn get_status(success: bool) -> &'static str {
    if success {
        "✅ Success"
    } else {
        "❌ Failed"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_greeting() {
        assert!(GREETING.contains("世界"));
    }
}
