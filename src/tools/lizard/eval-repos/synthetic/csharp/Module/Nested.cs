namespace Synthetic.Module;

/// <summary>
/// Nested module demonstrating namespace and import patterns.
/// </summary>
public class NestedService
{
    private readonly List<string> _items = new();

    public void Add(string item)
    {
        if (!string.IsNullOrEmpty(item))
        {
            _items.Add(item);
        }
    }

    public IEnumerable<string> GetAll() => _items.AsReadOnly();

    public string? Find(Func<string, bool> predicate) =>
        _items.FirstOrDefault(predicate);
}

public record NestedRecord(int Id, string Name, DateTime Created);

public interface INestedProcessor
{
    Task<bool> ProcessAsync(NestedRecord record, CancellationToken ct = default);
}

public class NestedProcessor : INestedProcessor
{
    public async Task<bool> ProcessAsync(NestedRecord record, CancellationToken ct = default)
    {
        await Task.Delay(10, ct);
        return record.Id > 0;
    }
}
