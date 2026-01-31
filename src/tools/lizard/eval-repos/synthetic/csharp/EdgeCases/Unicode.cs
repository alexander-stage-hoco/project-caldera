namespace Synthetic.EdgeCases;

/// <summary>
/// Unicode content test file.
/// </summary>
public class UnicodeTest
{
    // Unicode in strings
    public string Greeting => "Hello, 世界! 🌍";
    public string EmojiMath => "1️⃣ + 2️⃣ = 3️⃣";

    // Various Unicode characters
    private readonly Dictionary<string, string> _translations = new()
    {
        ["hello"] = "你好",
        ["world"] = "мир",
        ["welcome"] = "مرحبا",
        ["goodbye"] = "さようなら",
        ["thanks"] = "धन्यवाद"
    };

    public string? GetTranslation(string key) =>
        _translations.TryGetValue(key, out var value) ? value : null;

    // Unicode in XML docs
    /// <summary>
    /// Größenberechnung - Size calculation
    /// </summary>
    public double CalculateGröße(double länge, double breite) =>
        länge * breite;

    // Emoji method
    public string GetStatus(bool success) =>
        success ? "✅ Erfolgreich" : "❌ Fehlgeschlagen";
}
