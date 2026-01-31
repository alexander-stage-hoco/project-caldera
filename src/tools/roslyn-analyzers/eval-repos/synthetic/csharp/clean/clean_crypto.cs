using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace SyntheticSmells.Clean
{
    /// <summary>
    /// Clean cryptography implementation using modern algorithms.
    /// Expected violations: 0
    /// Demonstrates secure crypto practices (AES, SHA256, proper key handling).
    /// </summary>
    public sealed class CleanCryptoService : IDisposable
    {
        private readonly Aes _aes;
        private bool _disposed;

        public CleanCryptoService()
        {
            _aes = Aes.Create();
            _aes.KeySize = 256;  // Strong key size
            _aes.Mode = CipherMode.CBC;
            _aes.Padding = PaddingMode.PKCS7;
        }

        /// <summary>
        /// Encrypts data using AES-256 (secure algorithm).
        /// </summary>
        public EncryptedData Encrypt(byte[] plaintext, byte[] key)
        {
            ThrowIfDisposed();

            if (plaintext == null || plaintext.Length == 0)
                throw new ArgumentException("Plaintext cannot be null or empty", nameof(plaintext));

            if (key == null || key.Length != 32)  // 256 bits
                throw new ArgumentException("Key must be 256 bits (32 bytes)", nameof(key));

            _aes.Key = key;
            _aes.GenerateIV();

            using var encryptor = _aes.CreateEncryptor();
            using var ms = new MemoryStream();
            using var cs = new CryptoStream(ms, encryptor, CryptoStreamMode.Write);

            cs.Write(plaintext, 0, plaintext.Length);
            cs.FlushFinalBlock();

            return new EncryptedData
            {
                Ciphertext = ms.ToArray(),
                IV = _aes.IV
            };
        }

        /// <summary>
        /// Decrypts data using AES-256.
        /// </summary>
        public byte[] Decrypt(EncryptedData encrypted, byte[] key)
        {
            ThrowIfDisposed();

            if (encrypted == null)
                throw new ArgumentNullException(nameof(encrypted));

            if (key == null || key.Length != 32)
                throw new ArgumentException("Key must be 256 bits (32 bytes)", nameof(key));

            _aes.Key = key;
            _aes.IV = encrypted.IV;

            using var decryptor = _aes.CreateDecryptor();
            using var ms = new MemoryStream(encrypted.Ciphertext);
            using var cs = new CryptoStream(ms, decryptor, CryptoStreamMode.Read);
            using var output = new MemoryStream();

            cs.CopyTo(output);
            return output.ToArray();
        }

        /// <summary>
        /// Computes SHA-256 hash (secure algorithm).
        /// </summary>
        public static string ComputeHash(string input)
        {
            if (string.IsNullOrEmpty(input))
                throw new ArgumentException("Input cannot be null or empty", nameof(input));

            using var sha256 = SHA256.Create();
            var bytes = Encoding.UTF8.GetBytes(input);
            var hash = sha256.ComputeHash(bytes);
            return Convert.ToBase64String(hash);
        }

        /// <summary>
        /// Generates a cryptographically secure random key.
        /// </summary>
        public static byte[] GenerateSecureKey(int sizeInBytes = 32)
        {
            var key = new byte[sizeInBytes];
            using var rng = RandomNumberGenerator.Create();
            rng.GetBytes(key);
            return key;
        }

        /// <summary>
        /// Computes HMAC-SHA256 for message authentication.
        /// </summary>
        public static byte[] ComputeHmac(byte[] data, byte[] key)
        {
            if (data == null || data.Length == 0)
                throw new ArgumentException("Data cannot be null or empty", nameof(data));

            if (key == null || key.Length == 0)
                throw new ArgumentException("Key cannot be null or empty", nameof(key));

            using var hmac = new HMACSHA256(key);
            return hmac.ComputeHash(data);
        }

        private void ThrowIfDisposed()
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(CleanCryptoService));
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                _aes?.Dispose();
                _disposed = true;
            }
        }
    }

    public class EncryptedData
    {
        public byte[] Ciphertext { get; set; }
        public byte[] IV { get; set; }
    }
}
