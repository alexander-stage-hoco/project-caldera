namespace CoverageDemo;

public class StringUtils
{
    // This method will be tested
    public string Reverse(string input)
    {
        if (string.IsNullOrEmpty(input)) return input;
        return new string(input.Reverse().ToArray());
    }

    // This method will NOT be tested (partial coverage)
    public string Truncate(string input, int maxLength)
    {
        if (string.IsNullOrEmpty(input)) return input;
        return input.Length <= maxLength ? input : input[..maxLength] + "...";
    }

    // This branch will not be fully covered
    public bool IsValidEmail(string email)
    {
        if (string.IsNullOrWhiteSpace(email)) return false;
        if (!email.Contains('@')) return false;
        if (email.EndsWith(".")) return false;  // Uncovered branch
        return true;
    }
}
