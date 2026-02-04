// Safe Code - No security issues expected
// This file should have zero findings from DevSkim

using System;
using System.Data.SqlClient;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.IO;
using System.Web;

namespace SecurityTests
{
    /// <summary>
    /// Examples of secure coding practices.
    /// DevSkim should NOT flag any issues in this file.
    /// </summary>
    public class SafeCode
    {
        // SAFE: Parameterized SQL query
        public void SafeSqlQuery(SqlConnection connection, string userId)
        {
            using (var cmd = new SqlCommand("SELECT * FROM Users WHERE Id = @id", connection))
            {
                cmd.Parameters.AddWithValue("@id", userId);
                using (var reader = cmd.ExecuteReader())
                {
                    // Process results
                }
            }
        }

        // SAFE: Strong cryptographic hash
        public byte[] SecureHash(byte[] data)
        {
            using (var sha256 = SHA256.Create())
            {
                return sha256.ComputeHash(data);
            }
        }

        // SAFE: Cryptographically secure random
        public byte[] SecureRandom(int length)
        {
            byte[] bytes = new byte[length];
            using (var rng = RandomNumberGenerator.Create())
            {
                rng.GetBytes(bytes);
            }
            return bytes;
        }

        // SAFE: AES encryption with secure settings
        public byte[] SecureEncrypt(byte[] data, byte[] key)
        {
            using (var aes = Aes.Create())
            {
                aes.Mode = CipherMode.CBC;
                aes.Padding = PaddingMode.PKCS7;
                aes.Key = key;
                aes.GenerateIV();

                using (var encryptor = aes.CreateEncryptor())
                {
                    return encryptor.TransformFinalBlock(data, 0, data.Length);
                }
            }
        }

        // SAFE: Type-safe JSON deserialization
        public UserDto ParseUserJson(string json)
        {
            return JsonSerializer.Deserialize<UserDto>(json);
        }

        // SAFE: HTML encoding before output
        public string RenderSafeHtml(string userInput)
        {
            return HttpUtility.HtmlEncode(userInput);
        }

        // SAFE: Path validation
        public string ReadSafeFile(string basePath, string filename)
        {
            // Only use the filename portion
            string safeFilename = Path.GetFileName(filename);
            string fullPath = Path.Combine(basePath, safeFilename);

            // Validate the path is still within base directory
            if (!Path.GetFullPath(fullPath).StartsWith(Path.GetFullPath(basePath)))
            {
                throw new UnauthorizedAccessException("Invalid path");
            }

            return File.ReadAllText(fullPath);
        }

        // SAFE: Environment variable for secrets
        public string GetApiKey()
        {
            return Environment.GetEnvironmentVariable("API_KEY")
                ?? throw new InvalidOperationException("API_KEY not configured");
        }
    }

    public class UserDto
    {
        public string Name { get; set; }
        public string Email { get; set; }
    }
}
