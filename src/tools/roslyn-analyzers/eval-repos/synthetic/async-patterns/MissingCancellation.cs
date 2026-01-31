using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace AsyncPatterns.Cancellation
{
    /// <summary>
    /// Missing CancellationToken violations.
    /// Expected violations: CA2016 (Forward CancellationToken to methods that take one)
    /// </summary>
    public class MissingCancellationExamples
    {
        private readonly HttpClient _client = new();

        // CA2016: Forward CancellationToken to async methods
        public async Task ProcessWithCancellation(CancellationToken cancellationToken)
        {
            // Missing cancellation token forwarding
            await Task.Delay(1000);  // CA2016: Should pass cancellationToken
        }

        // CA2016: Multiple missing forwards
        public async Task MultipleOperations(CancellationToken token)
        {
            await Task.Delay(100);   // CA2016
            await Task.Delay(200);   // CA2016
            await Task.Delay(300);   // CA2016
        }

        // CA2016: HttpClient without cancellation
        public async Task FetchDataAsync(string url, CancellationToken cancellationToken)
        {
            // Missing cancellation token
            var response = await _client.GetAsync(url);  // CA2016
            var content = await response.Content.ReadAsStringAsync();  // CA2016
            Console.WriteLine(content);
        }

        // CA2016: In try block
        public async Task OperationWithRetry(CancellationToken token)
        {
            for (int i = 0; i < 3; i++)
            {
                try
                {
                    await Task.Delay(1000);  // CA2016
                    break;
                }
                catch (Exception)
                {
                    await Task.Delay(500);  // CA2016
                }
            }
        }
    }

    /// <summary>
    /// Methods that should accept but don't have CancellationToken parameter.
    /// </summary>
    public class MissingCancellationParameter
    {
        private readonly HttpClient _client = new();

        // Should have CancellationToken parameter
        public async Task<string> FetchDataAsync(string url)
        {
            var response = await _client.GetAsync(url);
            return await response.Content.ReadAsStringAsync();
        }

        // Should have CancellationToken parameter for long operations
        public async Task ProcessLargeDataAsync(byte[] data)
        {
            foreach (var chunk in ChunkData(data, 1024))
            {
                await Task.Delay(10);  // No way to cancel
            }
        }

        private byte[][] ChunkData(byte[] data, int size)
        {
            return new[] { data };  // Simplified
        }
    }

    /// <summary>
    /// Clean cancellation patterns
    /// </summary>
    public class SafeCancellationExamples
    {
        private readonly HttpClient _client = new();

        // OK: Properly forwarding cancellation token
        public async Task ProcessWithCancellation(CancellationToken cancellationToken)
        {
            await Task.Delay(1000, cancellationToken);
        }

        // OK: HttpClient with cancellation
        public async Task<string> FetchDataAsync(string url, CancellationToken cancellationToken)
        {
            var response = await _client.GetAsync(url, cancellationToken);
            return await response.Content.ReadAsStringAsync(cancellationToken);
        }

        // OK: Checking cancellation in loops
        public async Task ProcessItemsAsync(string[] items, CancellationToken cancellationToken)
        {
            foreach (var item in items)
            {
                cancellationToken.ThrowIfCancellationRequested();
                await Task.Delay(100, cancellationToken);
            }
        }
    }
}
