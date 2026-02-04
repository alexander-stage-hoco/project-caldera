namespace ExtensionMethods;

public static class StringExtensions
{
    public static string Truncate(this string str, int max) =>
        str?.Length > max ? str[..max] + "..." : str;

    public static bool IsNullOrEmpty(this string str) =>
        string.IsNullOrEmpty(str);
}

public static class CollectionExtensions
{
    public static bool IsEmpty<T>(this IEnumerable<T> col) => !col.Any();
    public static T SecondOrDefault<T>(this IEnumerable<T> col) =>
        col.Skip(1).FirstOrDefault();
}

public class Usage
{
    public void Demo()
    {
        var text = "Hello".Truncate(3);
        var list = new[] { 1, 2, 3 };
        var empty = list.IsEmpty();
    }
}
