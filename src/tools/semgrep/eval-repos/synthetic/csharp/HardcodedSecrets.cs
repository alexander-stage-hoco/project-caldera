/**
 * Test file for Hardcoded Secrets/Credentials detection.
 * Contains multiple hardcoded credential patterns for C#.
 */

using System;
using System.Net;
using System.Data.SqlClient;
using System.Security.Cryptography;
using System.Text;

namespace SmellTests.Security
{
    public class HardcodedSecretsExamples
    {
        // HARDCODED_SECRET: Hardcoded password in string
        private const string AdminPassword = "SuperSecretPassword123!";

        // HARDCODED_SECRET: Hardcoded API key
        private static readonly string ApiKey = "sk-1234567890abcdef1234567890abcdef";

        // HARDCODED_SECRET: Hardcoded connection string with password
        private readonly string _connectionString =
            "Server=prod.db.com;Database=Users;User Id=admin;Password=Pr0dP@ssw0rd!";

        // HARDCODED_SECRET: Hardcoded secret key
        private static byte[] SecretKey = Encoding.UTF8.GetBytes("MySecretKey12345");

        // HARDCODED_SECRET: Hardcoded token in field
        private string _authToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U";

        // HARDCODED_SECRET: Password in method parameter default
        public void Connect(string password = "DefaultPassword123")
        {
            // Using default hardcoded password
            Console.WriteLine($"Connecting with password: {password}");
        }

        // HARDCODED_SECRET: Hardcoded credentials in NetworkCredential
        public WebClient CreateAuthenticatedClient()
        {
            // BAD: Hardcoded username/password
            var client = new WebClient();
            client.Credentials = new NetworkCredential("admin", "AdminP@ss123!");
            return client;
        }

        // HARDCODED_SECRET: AWS credentials
        public void ConfigureAws()
        {
            // BAD: Hardcoded AWS credentials
            string accessKey = "AKIAIOSFODNN7EXAMPLE";
            string secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";
            Console.WriteLine($"Using AWS: {accessKey}");
        }

        // HARDCODED_SECRET: Private key in string
        private const string PrivateKey = @"-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7MiU5ByUU
-----END RSA PRIVATE KEY-----";

        // HARDCODED_SECRET: Encryption key in variable
        public byte[] EncryptData(byte[] data)
        {
            // BAD: Hardcoded encryption key
            byte[] key = new byte[] { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                                      0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10 };
            using var aes = Aes.Create();
            aes.Key = key;
            return aes.CreateEncryptor().TransformFinalBlock(data, 0, data.Length);
        }

        // HARDCODED_SECRET: Database password in connection string builder
        public string BuildConnectionString()
        {
            var builder = new SqlConnectionStringBuilder
            {
                DataSource = "server.database.windows.net",
                InitialCatalog = "MyDatabase",
                UserID = "sa",
                Password = "VerySecurePassword123!"  // BAD: Hardcoded
            };
            return builder.ConnectionString;
        }

        // HARDCODED_SECRET: OAuth client secret
        private static class OAuthConfig
        {
            public const string ClientId = "my-client-id";
            public const string ClientSecret = "c0nf1d3nt14l_s3cr3t_k3y";  // BAD
        }

        // CORRECT: Using environment variable
        public string GetApiKey()
        {
            // GOOD: Reading from environment
            return Environment.GetEnvironmentVariable("API_KEY") ?? throw new InvalidOperationException("API_KEY not set");
        }

        // CORRECT: Using configuration
        public string GetConnectionString(IConfiguration config)
        {
            // GOOD: Reading from configuration
            return config.GetConnectionString("DefaultConnection");
        }
    }

    // Stub interface for compilation
    public interface IConfiguration
    {
        string GetConnectionString(string name);
    }
}
