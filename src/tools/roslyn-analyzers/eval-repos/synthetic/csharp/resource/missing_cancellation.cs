using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace SyntheticSmells.Resource
{
    /// <summary>
    /// Missing CancellationToken examples for Roslyn Analyzer testing.
    /// Expected violations: CA2016 (5) = 5 total
    /// </summary>
    public class MissingCancellationExamples
    {
        private readonly HttpClient _client = new();

        // CA2016: Missing CancellationToken forwarding (line 18)
        public async Task<string> FetchDataAsync()
        {
            // Should accept CancellationToken parameter
            return await _client.GetStringAsync("https://api.example.com/data");
        }

        // CA2016: CancellationToken available but not passed (line 26)
        public async Task ProcessAsync(CancellationToken cancellationToken)
        {
            // Token available but not forwarded!
            var data = await _client.GetStringAsync("https://api.example.com/data");
            await ProcessDataAsync(data);
        }

        // CA2016: Task.Delay without cancellation (line 35)
        public async Task WaitAsync(int milliseconds)
        {
            await Task.Delay(milliseconds);
            // Should be: await Task.Delay(milliseconds, cancellationToken);
        }

        // CA2016: Multiple async calls without cancellation (line 43)
        public async Task<byte[]> DownloadAsync(string url)
        {
            var response = await _client.GetAsync(url);
            return await response.Content.ReadAsByteArrayAsync();
            // Both calls should accept CancellationToken
        }

        // CA2016: Nested async without cancellation propagation (line 52)
        public async Task RunOperationAsync(CancellationToken cancellationToken)
        {
            // Token available but not used in inner call
            await PerformWorkAsync();
        }

        private async Task ProcessDataAsync(string data)
        {
            await Task.Delay(100);
        }

        private async Task PerformWorkAsync()
        {
            await Task.Delay(1000);
        }

        // OK: Proper CancellationToken usage (no violation)
        public async Task<string> FetchDataWithCancellationAsync(CancellationToken cancellationToken)
        {
            return await _client.GetStringAsync("https://api.example.com/data", cancellationToken);
        }

        // OK: Proper Task.Delay with cancellation (no violation)
        public async Task WaitWithCancellationAsync(int milliseconds, CancellationToken cancellationToken)
        {
            await Task.Delay(milliseconds, cancellationToken);
        }
    }
}
