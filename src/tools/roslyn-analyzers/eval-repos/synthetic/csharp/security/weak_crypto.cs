using System;
using System.Security.Cryptography;
using System.Text;

namespace SyntheticSmells.Security
{
    /// <summary>
    /// Weak cryptography examples for Roslyn Analyzer testing.
    /// Expected violations: CA5350 (2), CA5351 (2) = 4 total
    /// Safe patterns: 2
    /// </summary>
    public class WeakCryptoExamples
    {
        // CA5350: Weak algorithm - DES (line 16)
        public byte[] EncryptWithDes(byte[] data, byte[] key)
        {
            using var des = DES.Create();
            des.Key = key;
            des.GenerateIV();
            using var encryptor = des.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // CA5350: Weak algorithm - TripleDES (line 27)
        public byte[] EncryptWithTripleDes(byte[] data, byte[] key)
        {
            using var tdes = TripleDES.Create();
            tdes.Key = key;
            tdes.GenerateIV();
            using var encryptor = tdes.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // CA5351: Broken algorithm - MD5 hash (line 38)
        public string HashWithMd5(string input)
        {
            using var md5 = MD5.Create();
            var hash = md5.ComputeHash(Encoding.UTF8.GetBytes(input));
            return BitConverter.ToString(hash).Replace("-", "").ToLower();
        }

        // CA5351: Broken algorithm - MD5 for password (line 47)
        public byte[] HashPasswordMd5(string password)
        {
            using var md5 = MD5.Create();
            return md5.ComputeHash(Encoding.UTF8.GetBytes(password));
        }

        // SAFE: Using AES (no violation expected)
        public byte[] SecureEncryptWithAes(byte[] data, byte[] key)
        {
            using var aes = Aes.Create();
            aes.Key = key;
            aes.GenerateIV();
            using var encryptor = aes.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // SAFE: Using SHA256 (no violation expected)
        public string SecureHashWithSha256(string input)
        {
            using var sha256 = SHA256.Create();
            var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
            return BitConverter.ToString(hash).Replace("-", "").ToLower();
        }
    }
}
