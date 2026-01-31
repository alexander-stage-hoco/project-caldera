// Package edge_cases provides Unicode content tests.
package edge_cases

// Unicode in strings
var greeting = "Hello, 世界! 🌍"
var emojiMath = "1️⃣ + 2️⃣ = 3️⃣"

// Translations with various Unicode
var translations = map[string]string{
	"hello":   "你好",
	"world":   "мир",
	"welcome": "مرحبا",
	"goodbye": "さようなら",
	"thanks":  "धन्यवाद",
}

// GetTranslation returns a translation.
func GetTranslation(key string) string {
	if val, ok := translations[key]; ok {
		return val
	}
	return ""
}

// FormatGreeting creates a multilingual greeting.
func FormatGreeting(name string) string {
	return "Привет, " + name + "! 👋 Welcome to 日本!"
}

// GetStatus returns a status with emoji.
func GetStatus(success bool) string {
	if success {
		return "✅ Success"
	}
	return "❌ Failed"
}
