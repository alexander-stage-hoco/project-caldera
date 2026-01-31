namespace CleanCode;

/// <summary>
/// Utility class for string operations.
/// </summary>
public static class StringUtils
{
    /// <summary>
    /// Checks if a string is null or empty.
    /// </summary>
    public static bool IsNullOrEmpty(string? value)
    {
        return string.IsNullOrEmpty(value);
    }

    /// <summary>
    /// Reverses a string.
    /// </summary>
    public static string Reverse(string input)
    {
        ArgumentNullException.ThrowIfNull(input);

        var chars = input.ToCharArray();
        Array.Reverse(chars);
        return new string(chars);
    }

    /// <summary>
    /// Capitalizes the first letter of a string.
    /// </summary>
    public static string Capitalize(string input)
    {
        if (string.IsNullOrEmpty(input))
        {
            return input;
        }

        return char.ToUpper(input[0]) + input[1..];
    }

    /// <summary>
    /// Counts the number of words in a string.
    /// </summary>
    public static int CountWords(string input)
    {
        if (string.IsNullOrWhiteSpace(input))
        {
            return 0;
        }

        return input.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length;
    }
}
