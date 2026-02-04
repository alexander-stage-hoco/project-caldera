// Authentication header handling test cases for DevSkim evaluation
// Expected: DevSkim should detect insecure auth patterns

using System;
using System.Net.Http;
using System.Net.Http.Headers;

namespace ApiSecurity
{
    public class AuthHeaders
    {
        // VULNERABLE: Hardcoded API key in header (DS173237)
        public HttpClient CreateClientWithHardcodedKey()
        {
            var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-API-Key", "sk-prod-1234567890abcdef");
            client.DefaultRequestHeaders.Add("Authorization", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test");
            return client;
        }

        // VULNERABLE: Basic auth with hardcoded credentials
        public HttpClient CreateClientWithBasicAuth()
        {
            var client = new HttpClient();
            var credentials = Convert.ToBase64String(
                System.Text.Encoding.ASCII.GetBytes("admin:password123")
            );
            client.DefaultRequestHeaders.Authorization =
                new AuthenticationHeaderValue("Basic", credentials);
            return client;
        }

        // VULNERABLE: Sending auth over HTTP (not HTTPS)
        public void SendAuthOverHttp()
        {
            var client = new HttpClient();
            client.BaseAddress = new Uri("http://api.example.com");  // HTTP not HTTPS
            client.DefaultRequestHeaders.Add("Authorization", "Bearer token");
            // DevSkim should warn about insecure transport
        }

        // VULNERABLE: Logging authorization header
        public void LogAuthHeader(HttpRequestMessage request)
        {
            var authHeader = request.Headers.Authorization;
            Console.WriteLine($"Auth header: {authHeader}");  // Logging sensitive data
            System.Diagnostics.Debug.WriteLine($"Token: {authHeader?.Parameter}");
        }

        // SAFE: Reading auth from environment (no finding expected)
        public HttpClient CreateClientWithEnvAuth()
        {
            var client = new HttpClient();
            var apiKey = Environment.GetEnvironmentVariable("API_KEY");
            if (!string.IsNullOrEmpty(apiKey))
            {
                client.DefaultRequestHeaders.Add("X-API-Key", apiKey);
            }
            return client;
            // This should NOT be flagged - using environment variables
        }

        // SAFE: Using HTTPS with auth
        public void SendAuthOverHttps()
        {
            var client = new HttpClient();
            client.BaseAddress = new Uri("https://api.example.com");
            // This should NOT be flagged
        }
    }
}
