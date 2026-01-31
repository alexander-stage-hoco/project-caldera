using System;
using System.Net.Http;
using System.Threading.Tasks;

namespace SyntheticTests
{
    /// <summary>
    /// C# file with sync-over-async anti-patterns for testing E1_SYNC_OVER_ASYNC detection.
    /// </summary>
    public class SyncOverAsyncExamples
    {
        private readonly HttpClient _client = new HttpClient();

        // E1_SYNC_OVER_ASYNC: Using .Result blocks the thread
        public string BlockingGetWithResult(string url)
        {
            var task = _client.GetStringAsync(url);
            return task.Result;  // BAD: Deadlock risk
        }

        // E1_SYNC_OVER_ASYNC: Using .Wait() blocks the thread
        public void BlockingWait(string url)
        {
            var task = _client.GetAsync(url);
            task.Wait();  // BAD: Deadlock risk
        }

        // E1_SYNC_OVER_ASYNC: Using GetAwaiter().GetResult() blocks the thread
        public string BlockingGetAwaiter(string url)
        {
            var task = _client.GetStringAsync(url);
            return task.GetAwaiter().GetResult();  // BAD: Still blocking
        }

        // Multiple violations in one method
        public void MultipleBlockingCalls(string url1, string url2)
        {
            var t1 = _client.GetStringAsync(url1);
            var t2 = _client.GetStringAsync(url2);

            var r1 = t1.Result;  // E1_SYNC_OVER_ASYNC
            t2.Wait();           // E1_SYNC_OVER_ASYNC
        }

        // GOOD: Proper async pattern
        public async Task<string> ProperAsyncMethod(string url)
        {
            return await _client.GetStringAsync(url);
        }

        // GOOD: Async all the way
        public async Task ProcessDataAsync(string url)
        {
            var data = await _client.GetStringAsync(url);
            Console.WriteLine(data);
        }
    }
}
