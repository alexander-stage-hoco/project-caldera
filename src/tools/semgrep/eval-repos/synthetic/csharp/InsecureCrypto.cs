/**
 * Test file for Insecure Cryptography detection.
 * Contains weak/deprecated cryptographic algorithm usage for C#.
 */

using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace SmellTests.Security
{
    public class InsecureCryptoExamples
    {
        // INSECURE_CRYPTO: Using MD5 for hashing
        public string HashWithMD5(string input)
        {
            // BAD: MD5 is cryptographically broken
            using var md5 = MD5.Create();
            byte[] inputBytes = Encoding.UTF8.GetBytes(input);
            byte[] hashBytes = md5.ComputeHash(inputBytes);
            return Convert.ToBase64String(hashBytes);
        }

        // INSECURE_CRYPTO: Using SHA1 for security purposes
        public string HashWithSHA1(string input)
        {
            // BAD: SHA1 is deprecated for security
            using var sha1 = SHA1.Create();
            byte[] inputBytes = Encoding.UTF8.GetBytes(input);
            byte[] hashBytes = sha1.ComputeHash(inputBytes);
            return Convert.ToBase64String(hashBytes);
        }

        // INSECURE_CRYPTO: Using DES encryption
        public byte[] EncryptWithDES(byte[] data, byte[] key)
        {
            // BAD: DES is weak (56-bit key)
            using var des = DES.Create();
            des.Key = key;
            des.GenerateIV();
            using var encryptor = des.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // INSECURE_CRYPTO: Using TripleDES (also deprecated)
        public byte[] EncryptWithTripleDES(byte[] data, byte[] key)
        {
            // BAD: TripleDES is deprecated
            using var tdes = TripleDES.Create();
            tdes.Key = key;
            tdes.GenerateIV();
            using var encryptor = tdes.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // INSECURE_CRYPTO: Using RC2 encryption
        public byte[] EncryptWithRC2(byte[] data, byte[] key)
        {
            // BAD: RC2 is weak
            using var rc2 = RC2.Create();
            rc2.Key = key;
            rc2.GenerateIV();
            using var encryptor = rc2.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // INSECURE_CRYPTO: Weak RSA key size
        public RSA CreateWeakRsaKey()
        {
            // BAD: 1024-bit RSA is too weak
            return RSA.Create(1024);
        }

        // INSECURE_CRYPTO: Using Random instead of cryptographic RNG
        public string GenerateToken()
        {
            // BAD: System.Random is predictable
            var random = new Random();
            var bytes = new byte[32];
            random.NextBytes(bytes);
            return Convert.ToBase64String(bytes);
        }

        // INSECURE_CRYPTO: ECB mode (patterns can be detected)
        public byte[] EncryptECB(byte[] data, byte[] key)
        {
            using var aes = Aes.Create();
            aes.Key = key;
            // BAD: ECB mode reveals patterns
            aes.Mode = CipherMode.ECB;
            using var encryptor = aes.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // INSECURE_CRYPTO: No padding (can cause issues)
        public byte[] EncryptNoPadding(byte[] data, byte[] key, byte[] iv)
        {
            using var aes = Aes.Create();
            aes.Key = key;
            aes.IV = iv;
            // BAD: No padding can cause issues
            aes.Padding = PaddingMode.None;
            using var encryptor = aes.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // INSECURE_CRYPTO: Using DSA with weak key
        public DSA CreateWeakDsaKey()
        {
            // BAD: Small DSA key
            return DSA.Create(1024);
        }

        // CORRECT: Using SHA256 for hashing
        public string HashWithSHA256(string input)
        {
            // GOOD: SHA256 is secure
            using var sha256 = SHA256.Create();
            byte[] inputBytes = Encoding.UTF8.GetBytes(input);
            byte[] hashBytes = sha256.ComputeHash(inputBytes);
            return Convert.ToBase64String(hashBytes);
        }

        // CORRECT: Using AES with proper configuration
        public byte[] EncryptWithAES(byte[] data, byte[] key, byte[] iv)
        {
            using var aes = Aes.Create();
            aes.Key = key;
            aes.IV = iv;
            // GOOD: CBC mode with PKCS7 padding
            aes.Mode = CipherMode.CBC;
            aes.Padding = PaddingMode.PKCS7;
            using var encryptor = aes.CreateEncryptor();
            return encryptor.TransformFinalBlock(data, 0, data.Length);
        }

        // CORRECT: Using cryptographic RNG
        public string GenerateSecureToken()
        {
            // GOOD: Cryptographic random number generator
            using var rng = RandomNumberGenerator.Create();
            var bytes = new byte[32];
            rng.GetBytes(bytes);
            return Convert.ToBase64String(bytes);
        }

        // CORRECT: Strong RSA key size
        public RSA CreateStrongRsaKey()
        {
            // GOOD: 2048-bit or higher
            return RSA.Create(2048);
        }
    }
}
