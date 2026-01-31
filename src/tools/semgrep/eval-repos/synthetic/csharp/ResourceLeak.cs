/**
 * Test file for DD smell F3_HTTPCLIENT_NEW detection.
 * Contains HttpClient instantiation anti-patterns.
 */

using System;
using System.Net.Http;
using System.Threading.Tasks;

namespace SmellTests.Resources
{
    public class ResourceLeakExamples
    {
        // F3_HTTPCLIENT_NEW: Creating HttpClient per request causes socket exhaustion
        public async Task<string> FetchDataAsync(string url)
        {
            using var client = new HttpClient();  // BAD: new HttpClient per call
            return await client.GetStringAsync(url);
        }

        // F3_HTTPCLIENT_NEW: Another HttpClient instantiation
        public async Task<byte[]> DownloadFileAsync(string url)
        {
            var client = new HttpClient();  // BAD: not even disposed
            return await client.GetByteArrayAsync(url);
        }

        // F3_HTTPCLIENT_NEW: HttpClient in loop (very bad)
        public async Task ProcessUrlsAsync(string[] urls)
        {
            foreach (var url in urls)
            {
                using var httpClient = new HttpClient();  // BAD: new client per iteration
                var response = await httpClient.GetAsync(url);
                Console.WriteLine(response.StatusCode);
            }
        }

        // F3_HTTPCLIENT_NEW: HttpClient created conditionally
        public async Task<string?> ConditionalFetchAsync(string url, bool useProxy)
        {
            if (useProxy)
            {
                var handler = new HttpClientHandler { UseProxy = true };
                using var client = new HttpClient(handler);  // BAD
                return await client.GetStringAsync(url);
            }
            else
            {
                using var client = new HttpClient();  // BAD
                return await client.GetStringAsync(url);
            }
        }

        // CORRECT: Injected HttpClient
        private readonly HttpClient _httpClient;

        public ResourceLeakExamples(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        // CORRECT: Uses injected client
        public async Task<string> FetchDataCorrectlyAsync(string url)
        {
            return await _httpClient.GetStringAsync(url);
        }
    }

    // F3_HTTPCLIENT_NEW: Static HttpClient in method (still bad pattern)
    public class AnotherBadExample
    {
        public async Task<string> GetDataAsync(string url)
        {
            // Creating new HttpClient even with using
            using HttpClient http = new HttpClient();
            return await http.GetStringAsync(url);
        }
    }
}
