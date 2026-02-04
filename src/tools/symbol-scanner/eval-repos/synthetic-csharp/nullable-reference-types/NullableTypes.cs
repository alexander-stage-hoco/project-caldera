#nullable enable
namespace NullableReferenceTypes;

public class NullableExample
{
    private string? _name;
    public string? NullableProp { get; set; }
    public string NonNullable { get; set; } = "";

    public string GetOrDefault(string? input) => input ?? "default";
    public int? ParseNumber(string? text) =>
        int.TryParse(text, out var n) ? n : null;
}

public class NullableContainer<T> where T : class?
{
    public T? Value { get; set; }
    public bool HasValue => Value != null;
}
