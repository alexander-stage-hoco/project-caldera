using System;
using System.Threading;
using System.Threading.Tasks;

namespace AsyncPatterns;

/// <summary>
/// Demonstrates async/await patterns.
/// </summary>
public class AsyncService
{
    /// <summary>
    /// Fetches data asynchronously.
    /// </summary>
    public async Task<string> FetchDataAsync(string url)
    {
        await Task.Delay(100); // Simulate network delay
        return $"Data from {url}";
    }

    /// <summary>
    /// Fetches data with cancellation support.
    /// </summary>
    public async Task<string> FetchDataAsync(string url, CancellationToken cancellationToken)
    {
        await Task.Delay(100, cancellationToken);
        return $"Data from {url}";
    }

    /// <summary>
    /// Processes multiple items concurrently.
    /// </summary>
    public async Task<int> ProcessAllAsync(string[] items)
    {
        var tasks = new Task<int>[items.Length];
        for (int i = 0; i < items.Length; i++)
        {
            tasks[i] = ProcessItemAsync(items[i]);
        }

        var results = await Task.WhenAll(tasks);
        return SumResults(results);
    }

    /// <summary>
    /// Processes a single item.
    /// </summary>
    private async Task<int> ProcessItemAsync(string item)
    {
        await Task.Delay(10);
        return item.Length;
    }

    private int SumResults(int[] results)
    {
        int sum = 0;
        foreach (var r in results) sum += r;
        return sum;
    }
}

/// <summary>
/// Async stream producer.
/// </summary>
public class AsyncStreamService
{
    /// <summary>
    /// Produces items asynchronously.
    /// </summary>
    public async IAsyncEnumerable<int> GenerateNumbersAsync(int count)
    {
        for (int i = 0; i < count; i++)
        {
            await Task.Delay(10);
            yield return i;
        }
    }

    /// <summary>
    /// Consumes async stream.
    /// </summary>
    public async Task<int> ConsumeAsync(IAsyncEnumerable<int> source)
    {
        int total = 0;
        await foreach (var item in source)
        {
            total += item;
        }
        return total;
    }
}
