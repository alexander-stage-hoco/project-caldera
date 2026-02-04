namespace PatternMatching;

public class Matcher
{
    public string Describe(object obj) => obj switch
    {
        null => "null",
        string s => $"string({s.Length})",
        int i when i > 0 => "positive",
        _ => "other"
    };

    public string Classify(int temp) => temp switch
    {
        < 0 => "Freezing",
        >= 0 and < 20 => "Cold",
        >= 20 => "Warm"
    };
}

public class Order
{
    public decimal Weight { get; set; }
    public bool IsPriority { get; set; }
}
