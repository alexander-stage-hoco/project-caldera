// Insecure URL test cases for DevSkim evaluation
// Expected: DevSkim should detect insecure transport (HTTP instead of HTTPS)

using System;
using System.Net.Http;
using System.Xml;

namespace SecurityTests
{
    public class InsecureUrls
    {
        // VULNERABLE: HTTP URLs for API calls (DS137138)
        public void MakeInsecureApiCall()
        {
            var client = new HttpClient();
            client.BaseAddress = new Uri("http://api.example.com");  // HTTP not HTTPS
            // DevSkim should flag this as insecure URL
        }

        // VULNERABLE: HTTP in configuration
        public string ApiEndpoint => "http://backend.internal.com/api";

        // VULNERABLE: FTP URL (insecure protocol)
        public void DownloadFile()
        {
            var ftpUrl = "ftp://files.example.com/data.zip";  // FTP is insecure
            // DevSkim should flag insecure protocol
        }

        // VULNERABLE: Telnet URL
        public string TelnetConnection => "telnet://server.example.com:23";

        // VULNERABLE: HTTP URL in XML configuration
        public void LoadXmlConfig()
        {
            var doc = new XmlDocument();
            // External entity with HTTP
            doc.Load("http://config.example.com/settings.xml");
        }

        // VULNERABLE: Multiple HTTP URLs
        public string[] GetEndpoints()
        {
            return new[]
            {
                "http://service1.example.com",
                "http://service2.example.com",
                "http://service3.example.com"
            };
        }

        // SAFE: HTTPS URL (no finding expected)
        public void MakeSecureApiCall()
        {
            var client = new HttpClient();
            client.BaseAddress = new Uri("https://api.example.com");
            // This should NOT be flagged - uses HTTPS
        }

        // SAFE: Local development URLs (may or may not flag)
        public void LocalDevelopment()
        {
            // Local development is typically acceptable
            var devUrl = "https://localhost:5001";
        }

        // SAFE: Configuration from environment
        public string GetApiUrl()
        {
            return Environment.GetEnvironmentVariable("API_URL") ?? "https://default.example.com";
        }
    }
}
