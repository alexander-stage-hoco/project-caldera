// Hardcoded Secrets test cases for DevSkim evaluation
// Expected: DevSkim should detect hardcoded credentials and API keys

using System;

namespace SecurityTests
{
    public class HardcodedSecrets
    {
        // VULNERABLE: Hardcoded password (DS134411)
        private const string Password = "SuperSecretPassword123!";

        // VULNERABLE: Hardcoded API key (DS114352)
        private const string ApiKey = "sk-1234567890abcdef1234567890abcdef";

        // VULNERABLE: Hardcoded connection string with password
        private const string ConnectionString = "Server=myserver;Database=mydb;User Id=admin;Password=MyP@ssw0rd!;";

        // VULNERABLE: AWS Access Key pattern (DS160340)
        private const string AwsAccessKey = "AKIAIOSFODNN7EXAMPLE";

        // VULNERABLE: Private key embedded
        private const string PrivateKey = @"-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcpo3q3K8e7ijV6twYt5f5UswDnQzMw8Kz
-----END RSA PRIVATE KEY-----";

        public void AuthenticateUser(string username)
        {
            // VULNERABLE: Hardcoded password in code
            string password = "admin123";

            if (username == "admin" && password == "admin123")
            {
                // Allow access
            }
        }

        public void ConnectToService()
        {
            // VULNERABLE: Hardcoded bearer token
            string token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c";
            // DevSkim should flag this JWT token
        }

        // SAFE: Password from environment
        public void SafeConnection()
        {
            string password = Environment.GetEnvironmentVariable("DB_PASSWORD");
            // This should NOT be flagged
        }

        // SAFE: Configuration-based
        public void SafeApiKey()
        {
            // Getting API key from secure configuration
            string apiKey = GetFromSecureVault("api-key");
            // This should NOT be flagged
        }

        private string GetFromSecureVault(string key) => "";
    }
}
