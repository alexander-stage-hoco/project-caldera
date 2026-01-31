using System;
using System.IO;
using System.Net.Http;

namespace SyntheticSmells.Resource
{
    /// <summary>
    /// Disposal pattern examples for IDISP014/IDISP017 testing.
    /// Expected violations: IDISP014 (3), IDISP017 (3) = 6 total
    /// Safe patterns: 3
    /// </summary>
    public class DisposalPatternExamples
    {
        // IDISP014: Creating new HttpClient instances (should use singleton)
        public string FetchData1(string url)
        {
            var client = new HttpClient();  // IDISP014: Use single instance
            return client.GetStringAsync(url).Result;
        }

        // IDISP014: Another HttpClient in method
        public string FetchData2(string url)
        {
            using var client = new HttpClient();  // IDISP014: Still flagged
            return client.GetStringAsync(url).Result;
        }

        // IDISP014: HttpClient in constructor
        private readonly HttpClient _client = new HttpClient();  // IDISP014: Should inject

        // IDISP017: Prefer using over try-finally
        public void ProcessFile1(string path)
        {
            FileStream stream = null;
            try
            {
                stream = File.OpenRead(path);  // IDISP017: Prefer using
                // Process stream
            }
            finally
            {
                stream?.Dispose();
            }
        }

        // IDISP017: Another try-finally pattern
        public void ProcessFile2(string path)
        {
            StreamReader reader = null;
            try
            {
                reader = new StreamReader(path);  // IDISP017: Prefer using
                var content = reader.ReadToEnd();
            }
            finally
            {
                if (reader != null)
                    reader.Dispose();
            }
        }

        // IDISP017: Try-finally with multiple resources
        public void ProcessMultiple(string path1, string path2)
        {
            FileStream fs1 = null;
            FileStream fs2 = null;
            try
            {
                fs1 = File.OpenRead(path1);  // IDISP017
                fs2 = File.OpenRead(path2);
            }
            finally
            {
                fs1?.Dispose();
                fs2?.Dispose();
            }
        }

        // SAFE: Using statement (no violation expected)
        public void SafeUsingPattern(string path)
        {
            using var stream = File.OpenRead(path);
            // Process stream
        }

        // SAFE: Using block (no violation expected)
        public void SafeUsingBlock(string path)
        {
            using (var reader = new StreamReader(path))
            {
                var content = reader.ReadToEnd();
            }
        }

        // SAFE: Injected HttpClient (no violation expected)
        public class SafeHttpService
        {
            private readonly HttpClient _httpClient;

            public SafeHttpService(HttpClient httpClient)
            {
                _httpClient = httpClient;  // Injected, not created
            }

            public string Fetch(string url)
            {
                return _httpClient.GetStringAsync(url).Result;
            }
        }
    }
}
