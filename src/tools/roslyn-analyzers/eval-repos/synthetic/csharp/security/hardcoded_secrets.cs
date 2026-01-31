using System;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// Hardcoded secrets examples for Roslyn Analyzer testing.
    /// Expected violations: CA5390 (6) + SCS0015 (6) = 6 unique patterns
    /// Safe patterns: 2
    /// Note: CA5390 is deprecated by Microsoft. SCS0015 from SecurityCodeScan
    /// provides better pattern-based detection for hardcoded passwords.
    /// </summary>
    public class HardcodedSecretsExamples
    {
        // CA5390: Hardcoded password (line 14)
        private const string DatabasePassword = "SuperSecret123!";

        // CA5390: Hardcoded API key (line 17)
        private static readonly string ApiKey = "sk-1234567890abcdef";

        // CA5390: Hardcoded connection string with password (line 20)
        private const string ConnectionString = "Server=db.example.com;Database=prod;User=admin;Password=admin123";

        // CA5390: Hardcoded JWT secret (line 23)
        private readonly byte[] JwtSecret = System.Text.Encoding.UTF8.GetBytes("my-super-secret-jwt-key-12345");

        // CA5390: Hardcoded encryption key (line 26)
        private static readonly string EncryptionKey = "AES256-KEY-0123456789ABCDEF";

        // CA5390: Hardcoded OAuth client secret (line 29)
        public string GetClientSecret() => "oauth-client-secret-xyz789";

        // SCS0015: Hardcoded password in variable assignment
        public void ConnectToDatabase()
        {
            string password = "hardcoded_db_password";  // SCS0015
            string dbPassword = "secret123";            // SCS0015
            string userPassword = "admin";              // SCS0015
            Console.WriteLine($"Connecting with password length: {password.Length}");
        }

        // SCS0015: Hardcoded password in method parameter
        public void AuthenticateUser()
        {
            var pwd = "userPassword123";                // SCS0015
            string adminPwd = "admin_secret";           // SCS0015
            string rootPassword = "root123";            // SCS0015
            Login("admin", adminPwd);
        }

        private void Login(string user, string pass) => Console.WriteLine($"User: {user}");

        public void UseHardcodedCredentials()
        {
            // These use the hardcoded values above
            var password = DatabasePassword;
            var key = ApiKey;
            Console.WriteLine($"Using password: {password.Length} chars");
        }

        // SAFE: Reading from environment (no violation expected)
        public string GetSecureApiKey()
        {
            return Environment.GetEnvironmentVariable("API_KEY") ?? throw new InvalidOperationException("API_KEY not set");
        }

        // SAFE: Reading from configuration (no violation expected)
        public string GetSecureConnectionString(Microsoft.Extensions.Configuration.IConfiguration config)
        {
            return config.GetConnectionString("DefaultConnection");
        }
    }
}

// Fake namespace for compilation
namespace Microsoft.Extensions.Configuration
{
    public interface IConfiguration
    {
        string GetConnectionString(string name);
    }
}
